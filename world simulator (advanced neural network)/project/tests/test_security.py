"""
tests/test_security.py

Comprehensive Test Suite for the Advanced Local and Public Network Security System.
"""

import os
import time
import unittest
from project.security.firewall import DualZoneFirewall, NetworkZone
from project.security.rate_limiter import MultiTierRateLimiter, ZoneRatePolicy
from project.security.ids import IntrusionDetectionSystem, ThreatLevel
from project.security.auth import (
    AuthManager,
    Role,
    Permission,
    SecurityToken,
)
from project.security.crypto import CryptoEngine
from project.security.vault import SecureKeyVault
from project.security.sanitizer import PayloadSanitizer
from project.security.audit import SecurityAuditLogger, SecuritySeverity
from project.systems.security_system import SecuritySystem
from project.core.scheduler import UpdateContext


class TestSecuritySubsystem(unittest.TestCase):

    def setUp(self) -> None:
        self.audit_test_path = "test_security_audit.jsonl"

    def tearDown(self) -> None:
        if os.path.exists(self.audit_test_path):
            os.remove(self.audit_test_path)

    # -------------------------------------------------------------------------
    # 1. Dual-Zone Firewall Tests
    # -------------------------------------------------------------------------
    def test_firewall_zone_classification(self) -> None:
        fw = DualZoneFirewall()

        # Local private subnets & loopback
        self.assertEqual(fw.classify_zone("127.0.0.1"), NetworkZone.LOCAL)
        self.assertEqual(fw.classify_zone("10.10.5.2"), NetworkZone.LOCAL)
        self.assertEqual(fw.classify_zone("192.168.1.1"), NetworkZone.LOCAL)
        self.assertEqual(fw.classify_zone("172.16.0.25"), NetworkZone.LOCAL)
        self.assertEqual(fw.classify_zone("::1"), NetworkZone.LOCAL)

        # Public routable WAN IPs
        self.assertEqual(fw.classify_zone("8.8.8.8"), NetworkZone.PUBLIC)
        self.assertEqual(fw.classify_zone("1.1.1.1"), NetworkZone.PUBLIC)
        self.assertEqual(fw.classify_zone("93.184.216.34"), NetworkZone.PUBLIC)

        # Bogon / Invalid IPs
        self.assertEqual(fw.classify_zone("192.0.2.1"), NetworkZone.BLOCKED)
        self.assertEqual(fw.classify_zone("240.0.0.1"), NetworkZone.BLOCKED)
        self.assertEqual(fw.classify_zone("not_an_ip"), NetworkZone.BLOCKED)

    def test_firewall_rules_and_dynamic_bans(self) -> None:
        fw = DualZoneFirewall()
        ip = "198.51.200.10"

        # Allowed initially
        allowed, zone, _ = fw.is_allowed(ip)
        self.assertTrue(allowed)
        self.assertEqual(zone, NetworkZone.PUBLIC)

        # Apply temporary ban (0.2 seconds)
        fw.add_ban(ip, duration_sec=0.2, reason="Test ban")
        self.assertTrue(fw.is_banned(ip))
        allowed, zone, _ = fw.is_allowed(ip)
        self.assertFalse(allowed)
        self.assertEqual(zone, NetworkZone.BLOCKED)

        # Wait for ban to expire
        time.sleep(0.25)
        self.assertFalse(fw.is_banned(ip))
        pruned = fw.clean_expired_bans()
        self.assertEqual(pruned, 0)  # already cleaned on is_banned check

        # Blacklist CIDR
        fw.add_blacklist("203.0.120.0/24")
        allowed, _, reason = fw.is_allowed("203.0.120.45")
        self.assertFalse(allowed)
        self.assertIn("blacklist", reason.lower())

    # -------------------------------------------------------------------------
    # 2. Rate Limiter Tests
    # -------------------------------------------------------------------------
    def test_rate_limiter_dual_tier(self) -> None:
        limiter = MultiTierRateLimiter(
            local_policy=ZoneRatePolicy(capacity=5.0, refill_rate=1.0),
            public_policy=ZoneRatePolicy(capacity=2.0, refill_rate=0.5, max_violations_before_penalty=2, penalty_duration_sec=0.3),
        )

        local_ip = "192.168.1.50"
        public_ip = "8.8.8.8"

        # Local has 5 tokens
        for _ in range(5):
            ok, _, _ = limiter.allow_request(local_ip, zone=NetworkZone.LOCAL)
            self.assertTrue(ok)
        
        # 6th request throttled
        ok, wait_sec, _ = limiter.allow_request(local_ip, zone=NetworkZone.LOCAL)
        self.assertFalse(ok)
        self.assertGreater(wait_sec, 0.0)

        # Public has only 2 tokens
        ok1, _, _ = limiter.allow_request(public_ip, zone=NetworkZone.PUBLIC)
        ok2, _, _ = limiter.allow_request(public_ip, zone=NetworkZone.PUBLIC)
        ok3, wait, meta = limiter.allow_request(public_ip, zone=NetworkZone.PUBLIC)
        
        self.assertTrue(ok1)
        self.assertTrue(ok2)
        self.assertFalse(ok3)

    # -------------------------------------------------------------------------
    # 3. IDS / IPS Tests
    # -------------------------------------------------------------------------
    def test_ids_signature_inspection_and_threat_scoring(self) -> None:
        fw = DualZoneFirewall()
        ids = IntrusionDetectionSystem(firewall=fw, temp_ban_threshold=50.0)
        attacker_ip = "198.51.100.99"

        # Safe payload
        safe_ok, threats, score = ids.inspect_payload(attacker_ip, '{"action": "GET_TELEMETRY", "tick": 100}')
        self.assertTrue(safe_ok)
        self.assertEqual(len(threats), 0)

        # SQL & Command injection attempt
        malicious_payload = "'; DROP TABLE users; whoami; /etc/passwd"
        bad_ok, threats, score = ids.inspect_payload(attacker_ip, malicious_payload)
        
        self.assertFalse(bad_ok)
        self.assertGreater(len(threats), 0)
        self.assertGreater(score, 0.0)

        # Verify automatic firewall ban triggered
        self.assertTrue(fw.is_banned(attacker_ip))

    # -------------------------------------------------------------------------
    # 4. RBAC & Auth Token Tests
    # -------------------------------------------------------------------------
    def test_auth_manager_tokens_and_permissions(self) -> None:
        auth = AuthManager(secret_key="unit_test_secret_key_1234567890")

        # Authenticate admin
        role = auth.authenticate_credentials("admin", "admin_alife_secure")
        self.assertEqual(role, Role.ADMIN)

        # Create token bound to IP
        token_str = auth.create_token(
            user_id="admin",
            role=Role.ADMIN,
            duration_sec=10.0,
            bound_ip="127.0.0.1",
        )

        # Valid verification
        valid, token_obj, _ = auth.verify_token(
            token_str=token_str,
            client_ip="127.0.0.1",
            required_permission=Permission.MUTATE_WORLD,
        )
        self.assertTrue(valid)
        self.assertIsNotNone(token_obj)
        self.assertEqual(token_obj.role, Role.ADMIN)

        # IP mismatch rejection
        valid_ip_mismatch, _, reason = auth.verify_token(token_str=token_str, client_ip="192.168.1.100")
        self.assertFalse(valid_ip_mismatch)
        self.assertIn("IP mismatch", reason)

        # Revocation
        auth.revoke_token(token_obj.token_id)
        valid_revoked, _, rev_reason = auth.verify_token(token_str=token_str, client_ip="127.0.0.1")
        self.assertFalse(valid_revoked)
        self.assertIn("revoked", rev_reason.lower())

    # -------------------------------------------------------------------------
    # 5. Cryptography & Anti-Replay Tests
    # -------------------------------------------------------------------------
    def test_crypto_engine_signing_and_anti_replay(self) -> None:
        crypto = CryptoEngine(default_shared_key="test_shared_secret_key_alife_00")
        payload = {"sim_tick": 450, "command": "SPAWN_PLANT", "x": 10.0, "y": 20.0}

        # Sign packet
        packet = crypto.sign_payload(payload, sender_id="client_1")
        self.assertIn("signature", packet)
        self.assertIn("nonce", packet)

        # 1st Verification: Success
        ok, unpacked, _ = crypto.verify_and_unpack(packet)
        self.assertTrue(ok)
        self.assertEqual(unpacked["sim_tick"], 450)

        # 2nd Verification: Replay Attack Rejection
        replay_ok, _, replay_reason = crypto.verify_and_unpack(packet)
        self.assertFalse(replay_ok)
        self.assertIn("Replay attack", replay_reason)

        # Tampered signature check
        tampered_packet = crypto.sign_payload({"data": "original"}, sender_id="client_1")
        tampered_packet["payload"]["data"] = "hacked"
        tamper_ok, _, tamper_reason = crypto.verify_and_unpack(tampered_packet)
        self.assertFalse(tamper_ok)
        self.assertIn("mismatch", tamper_reason)

    def test_crypto_authenticated_encryption(self) -> None:
        crypto = CryptoEngine()
        secret_data = b"CONFIDENTIAL_GENETIC_TRAIT_PAYLOAD_12345"

        enc_dict = crypto.encrypt_bytes(secret_data)
        self.assertIn("ciphertext", enc_dict)
        self.assertIn("tag", enc_dict)

        decrypted = crypto.decrypt_bytes(enc_dict)
        self.assertEqual(decrypted, secret_data)

        # Tamper tag
        enc_dict["tag"] = "QUFB"  # invalid base64 tag
        self.assertIsNone(crypto.decrypt_bytes(enc_dict))

    # -------------------------------------------------------------------------
    # 6. Vault & SSRF Guard Tests
    # -------------------------------------------------------------------------
    def test_vault_masking_and_ssrf(self) -> None:
        vault = SecureKeyVault()
        raw_key = "AQ.TestSecretKey123456789"
        vault.set_secret("TEST_KEY", raw_key)

        # Unmasked retrieve
        self.assertEqual(vault.get_secret("TEST_KEY"), raw_key)

        # Masked string
        masked_disp = vault.mask_string(raw_key)
        self.assertTrue(masked_disp.startswith("AQ.TestS"))
        self.assertTrue(masked_disp.endswith("********"))

        # SSRF checks
        ok_google, _ = vault.validate_outbound_url("https://generativelanguage.googleapis.com/v1beta/models")
        self.assertTrue(ok_google)

        bad_insecure, _ = vault.validate_outbound_url("http://generativelanguage.googleapis.com/test")
        self.assertFalse(bad_insecure)  # HTTP not HTTPS

        bad_aws_meta, _ = vault.validate_outbound_url("https://169.254.169.254/latest/meta-data")
        self.assertFalse(bad_aws_meta)  # Cloud metadata blocked

        bad_internal, _ = vault.validate_outbound_url("https://127.0.0.1:8080/admin")
        self.assertFalse(bad_internal)  # Loopback SSRF blocked

    # -------------------------------------------------------------------------
    # 7. Payload Sanitizer Tests
    # -------------------------------------------------------------------------
    def test_payload_sanitizer(self) -> None:
        # Null bytes & control character stripping
        raw_text = "Hello\x00World\x1FTest"
        clean_text = PayloadSanitizer.sanitize_text(raw_text)
        self.assertEqual(clean_text, "HelloWorldTest")

        # JSON Depth Bomb rejection
        nested = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
        import json
        nested_json = json.dumps(nested)

        # Passes with depth 10
        ok_deep, _, _ = PayloadSanitizer.parse_and_sanitize_json(nested_json, max_depth=10)
        self.assertTrue(ok_deep)

        # Fails with depth limit 3
        fail_deep, _, reason = PayloadSanitizer.parse_and_sanitize_json(nested_json, max_depth=3)
        self.assertFalse(fail_deep)
        self.assertIn("Recursion depth exceeded", reason)

    # -------------------------------------------------------------------------
    # 8. Security Audit Logger Tests
    # -------------------------------------------------------------------------
    def test_audit_logger(self) -> None:
        logger = SecurityAuditLogger()
        logger.log_event(SecuritySeverity.INFO, "USER_LOGIN", client_ip="127.0.0.1", details="Admin login")
        logger.log_event(SecuritySeverity.CRITICAL_ATTACK, "INJECTION_ATTACK", client_ip="198.51.100.5", details="SQL injection")

        events = logger.get_events(min_severity=SecuritySeverity.SECURITY_ALERT)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "INJECTION_ATTACK")

        # Flush to JSONL
        count = logger.flush_to_jsonl(self.audit_test_path)
        self.assertEqual(count, 2)
        self.assertTrue(os.path.exists(self.audit_test_path))

    # -------------------------------------------------------------------------
    # 9. Security System End-to-End Pipeline Tests
    # -------------------------------------------------------------------------
    def test_security_system_pipeline(self) -> None:
        sec_sys = SecuritySystem(audit_log_path=self.audit_test_path)
        
        context = UpdateContext(
            tick=60,
            delta_time=0.1,
            simulation_time=1.0,
            random_seed=42,
            world_reference=None,
            is_paused=False,
            active_thread_count=1,
        )

        sec_sys.initialize(context)
        sec_sys.update(context)

        # 1. Valid local request without token
        ok, data, _ = sec_sys.process_inbound_request("127.0.0.1", '{"query": "status"}')
        self.assertTrue(ok)
        self.assertEqual(data["query"], "status")

        # 2. Blocked attack with malicious injection signature
        bad_ok, _, reason = sec_sys.process_inbound_request("93.184.216.34", '{"command": "eval(__import__(\'os\').system(\'calc\'))"}')
        self.assertFalse(bad_ok)
        self.assertIn("Malicious signature", reason)

        # 3. Authenticated command with valid admin token
        admin_token = sec_sys.auth_mgr.create_token("admin", Role.ADMIN, bound_ip="192.168.1.50")
        auth_ok, _, _ = sec_sys.process_inbound_request(
            ip_str="192.168.1.50",
            raw_payload='{"action": "TRIGGER_DISASTER", "type": "METEOR"}',
            token_str=admin_token,
            required_perm=Permission.TRIGGER_DISASTER,
        )
        self.assertTrue(auth_ok)

        sec_sys.shutdown()


if __name__ == "__main__":
    unittest.main()
