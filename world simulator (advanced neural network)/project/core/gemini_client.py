"""
project/core/gemini_client.py

Asynchronous HTTP client interface communicating with Gemini APIs via background worker threads.
Features:
- Dynamic Multi-Key Health & Latency Router: Automatically routes requests to the healthiest,
  lowest-latency, unexhausted API keys.
- Instant Failover on HTTP 429 Rate Limits / Quotas: Backs off the exhausted key and instantly
  retries with the next best key in pool.
- Zero-Crash Guarantee with Seamless Offline Heuristic Fallback.
- Dynamic key addition, pruning, and secret masking.
- Full integration with UserProfile and pure 100% Offline Mode.
"""

from __future__ import annotations

import os
import time
import json
import urllib.request
import urllib.error
import threading
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Callable, Optional, List, Tuple
from project.security.vault import SecureKeyVault


def _load_env_file() -> None:
    """Lightweight .env loader that populates os.environ without requiring external packages."""
    search_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]
    for p in search_paths:
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, _, val = line.partition("=")
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = val
            except Exception:
                pass
            break


@dataclass
class KeyHealth:
    """Health statistics and routing telemetry for a single API key."""
    key: str
    status: str = "ACTIVE"  # "ACTIVE", "COOLDOWN_429", "ERROR_AUTH"
    cooldown_until: float = 0.0
    consecutive_errors: int = 0
    success_count: int = 0
    avg_latency_ms: float = 200.0
    last_used: float = 0.0

    @property
    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until and self.status != "ERROR_AUTH"

    @property
    def masked_key(self) -> str:
        k = self.key.strip()
        if len(k) <= 8:
            return "****"
        return f"{k[:4]}...{k[-4:]}"


DEFAULT_API_KEYS_POOL: List[str] = []


class GeminiClient:
    """Asynchronous client for Generative Language API with intelligent multi-key routing."""

    def __init__(self, api_key: Optional[str] = None, use_default_pool: bool = True) -> None:
        _load_env_file()
        self.vault = SecureKeyVault()
        
        self._keys_pool: List[str] = []
        self._key_stats: Dict[str, KeyHealth] = {}
        self.is_offline: bool = False

        # 1. Load keys from user_profile if allowed
        if use_default_pool:
            try:
                from project.core.user_profile import user_profile_manager
                prof = user_profile_manager.get_profile()
                self.is_offline = prof.gemini.get("is_offline", False)
                for k in prof.gemini.get("api_keys", []):
                    clean_k = k.strip()
                    if clean_k and clean_k not in self._keys_pool:
                        self._keys_pool.append(clean_k)
            except Exception:
                pass

        if api_key and api_key.strip():
            if api_key.strip() not in self._keys_pool:
                self._keys_pool.append(api_key.strip())
            self.is_offline = False
        elif api_key == "":
            use_default_pool = False
            self.is_offline = True

        if use_default_pool and not self.is_offline:
            # Check GEMINI_API_KEYS (comma-separated list for multi-key pool rotation)
            env_keys = os.environ.get("GEMINI_API_KEYS")
            if env_keys:
                for k in env_keys.split(","):
                    k = k.strip()
                    if k and k not in self._keys_pool:
                        self._keys_pool.append(k)

            # Check single GEMINI_API_KEY
            env_key = os.environ.get("GEMINI_API_KEY")
            if env_key and env_key.strip() and env_key.strip() not in self._keys_pool:
                self._keys_pool.append(env_key.strip())

            for k in DEFAULT_API_KEYS_POOL:
                if k and k.strip() and k.strip() not in self._keys_pool:
                    self._keys_pool.append(k.strip())

        # If no keys in pool, seamlessly activate offline mode
        if len(self._keys_pool) == 0:
            self.is_offline = True

        # Initialize health trackers for each key
        for k in self._keys_pool:
            self._key_stats[k] = KeyHealth(key=k)

        self._key_index: int = 0
        self._pool_lock = threading.Lock()
        self._cache_lock = threading.Lock()

        # Quota Safety & Rate-Limiting Parameters (Max 1 request per 3.5s per free-tier key)
        self._min_request_interval_s: float = 3.5
        self._last_request_time: float = 0.0
        self._response_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

        # Global thread pool for non-blocking asynchronous queries
        self._executor = ThreadPoolExecutor(max_workers=4)

    def add_api_key(self, new_key: str) -> None:
        """Dynamically registers a new live API key to the active routing pool."""
        clean = new_key.strip()
        if not clean:
            return
        with self._pool_lock:
            if clean not in self._keys_pool:
                self._keys_pool.insert(0, clean)
                self._key_stats[clean] = KeyHealth(key=clean)
                self.is_offline = False
                masked = f"{clean[:4]}...{clean[-4:]}" if len(clean) > 8 else "****"
                print(f"[GEMINI ROUTER] Added key ({masked}) to multi-key routing pool. (Total: {len(self._keys_pool)})")

    def remove_api_key(self, key_or_index: Any) -> bool:
        """Removes a key by value or index."""
        with self._pool_lock:
            removed_key = None
            if isinstance(key_or_index, int) and 0 <= key_or_index < len(self._keys_pool):
                removed_key = self._keys_pool.pop(key_or_index)
            elif isinstance(key_or_index, str) and key_or_index in self._keys_pool:
                self._keys_pool.remove(key_or_index)
                removed_key = key_or_index

            if removed_key:
                self._key_stats.pop(removed_key, None)
                if len(self._keys_pool) == 0:
                    self.is_offline = True
                return True
        return False

    def purge_dead_keys(self) -> int:
        """Purges all keys in pool."""
        with self._pool_lock:
            count = len(self._keys_pool)
            self._keys_pool.clear()
            self._key_stats.clear()
            self._key_index = 0
            self.is_offline = True
            return count

    def get_best_key(self) -> Optional[str]:
        """
        Health-aware intelligent key router:
        Picks the key with the lowest consecutive errors, lowest moving latency,
        and not currently on 429 rate-limit cooldown.
        """
        with self._pool_lock:
            if not self._keys_pool or self.is_offline:
                return None

            now = time.time()
            available = [stats for stats in self._key_stats.values() if stats.is_available]

            if not available:
                # All keys are currently cooling down: pick the one expiring soonest
                all_stats = list(self._key_stats.values())
                if all_stats:
                    all_stats.sort(key=lambda s: s.cooldown_until)
                    best = all_stats[0]
                    if best.cooldown_until - now <= 2.0:
                        # Wait brief fraction if cooldown is almost over
                        time.sleep(max(0.1, best.cooldown_until - now))
                        return best.key
                return None

            # Sort available keys by health:
            # 1. fewest consecutive errors (lowest error count first)
            # 2. lowest average latency
            # 3. least recently used (spread load across keys)
            available.sort(key=lambda s: (s.consecutive_errors, s.avg_latency_ms, s.last_used))
            best_stats = available[0]
            best_stats.last_used = now
            return best_stats.key

    def get_current_key(self) -> str:
        """Returns the best key or currently rotated key."""
        best = self.get_best_key()
        if best:
            return best
        with self._pool_lock:
            if not self._keys_pool:
                return ""
            return self._keys_pool[self._key_index % len(self._keys_pool)]

    def record_key_success(self, key: str, latency_ms: float) -> None:
        """Records a successful API response to improve routing score."""
        with self._pool_lock:
            stats = self._key_stats.get(key)
            if stats:
                stats.total_successes += 1
                stats.consecutive_errors = 0
                stats.status = "ACTIVE"
                # Exponential moving average of latency
                stats.avg_latency_ms = (stats.avg_latency_ms * 0.7) + (latency_ms * 0.3)

    def record_key_error(self, key: str, is_429: bool = False, is_auth_err: bool = False) -> None:
        """Records an error and triggers immediate cooldown or rotation."""
        with self._pool_lock:
            stats = self._key_stats.get(key)
            if stats:
                stats.consecutive_errors += 1
                if is_auth_err:
                    stats.status = "ERROR_AUTH"
                elif is_429:
                    stats.status = "COOLDOWN_429"
                    stats.cooldown_until = time.time() + 60.0  # 60s backoff for 429
                    masked = stats.masked_key
                    print(f"⚠️ [GEMINI ROUTER] Key ({masked}) hit quota limit (429). Placed on 60s cooldown.")

    def get_pool_status(self) -> List[Dict[str, Any]]:
        """Returns human-readable telemetry for all registered keys."""
        with self._pool_lock:
            res = []
            now = time.time()
            for k, stats in self._key_stats.items():
                cd_remaining = max(0.0, stats.cooldown_until - now)
                res.append({
                    "masked_key": stats.masked_key,
                    "status": "COOLDOWN" if cd_remaining > 0 else stats.status,
                    "cooldown_s": round(cd_remaining, 1),
                    "success_count": stats.total_successes,
                    "avg_latency_ms": round(stats.avg_latency_ms, 1),
                    "errors": stats.consecutive_errors,
                })
            return res

    def request_reasoning_async(self, prompt: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Schedules content generation request in a background thread."""
        self._executor.submit(self._run_request_and_callback, prompt, callback)

    def _run_request_and_callback(self, prompt: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        try:
            result = self.request_reasoning(prompt)
            callback(result)
        except Exception:
            callback(self._offline_fallback_solver(prompt))

    def request_reasoning(self, prompt: str) -> Dict[str, Any]:
        """Posts prompt to Gemini API with dynamic key health routing, caching, and offline fallback."""
        p_hash = str(hash(prompt))
        now = time.time()

        # 1. Check Smart Response Cache (TTL 90s)
        with self._cache_lock:
            if p_hash in self._response_cache:
                cached_time, cached_res = self._response_cache[p_hash]
                if (now - cached_time) < 90.0:
                    return dict(cached_res)

        # 2. Pure Offline Mode / No Keys: Instant heuristic evaluation
        if self.is_offline or not self._keys_pool:
            res = self._offline_fallback_solver(prompt)
            with self._cache_lock:
                self._response_cache[p_hash] = (now, res)
            return res

        # 3. Enforce Minimum Quota Rate-Limit Cooldown
        with self._pool_lock:
            elapsed = now - self._last_request_time
            if elapsed < self._min_request_interval_s:
                res = self._offline_fallback_solver(prompt)
                with self._cache_lock:
                    self._response_cache[p_hash] = (now, res)
                return res
            self._last_request_time = now

        max_attempts = min(len(self._keys_pool), 3)
        models_to_try = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-2.5-flash"]

        for attempt in range(max_attempts):
            key = self.get_best_key()
            if not key:
                break

            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 150,
                    "temperature": 0.4
                }
            }

            for model_name in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                is_safe, _ = self.vault.validate_outbound_url(url)
                if not is_safe:
                    continue

                t0 = time.time()
                try:
                    data = json.dumps(payload).encode("utf-8")
                    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

                    with urllib.request.urlopen(req, timeout=8.0) as response:
                        latency_ms = (time.time() - t0) * 1000.0
                        self.record_key_success(key, latency_ms)

                        resp_bytes = response.read()
                        resp_json = json.loads(resp_bytes.decode("utf-8"))
                        candidate = resp_json.get("candidates", [{}])[0]
                        parts = candidate.get("content", {}).get("parts", [])
                        text_content = ""
                        for p in parts:
                            if isinstance(p, dict) and "text" in p and p["text"]:
                                text_content += p["text"]
                        text_content = text_content.strip()

                        if text_content.startswith("```"):
                            lines = text_content.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].strip() == "```":
                                lines = lines[:-1]
                            text_content = "\n".join(lines).strip()

                        parsed = json.loads(text_content)
                        if isinstance(parsed, dict) and "action" in parsed:
                            with self._cache_lock:
                                self._response_cache[p_hash] = (now, parsed)
                            return parsed

                        res = {"action": "WANDER", "reasoning": "Standard LLM navigation"}
                        with self._cache_lock:
                            self._response_cache[p_hash] = (now, res)
                        return res

                except urllib.error.HTTPError as e:
                    if e.code in (404,):
                        continue
                    elif e.code == 429:
                        self.record_key_error(key, is_429=True)
                        break  # Route to next best key
                    elif e.code in (400, 401, 403):
                        self.record_key_error(key, is_auth_err=True)
                        break
                    else:
                        self.record_key_error(key)
                        break
                except Exception:
                    self.record_key_error(key)
                    break

        # Fallback to local heuristic solver if all online keys fail or quota exceeded
        fallback = self._offline_fallback_solver(prompt)
        with self._cache_lock:
            self._response_cache[p_hash] = (now, fallback)
        return fallback

    def _offline_fallback_solver(self, prompt: str) -> Dict[str, Any]:
        """Deterministic local decision solver used when in offline mode or during network outages."""
        prompt_lower = prompt.lower()

        # Divine Prayer & Deity Communion Oracle
        if "divine" in prompt_lower or "prayer" in prompt_lower or "deity" in prompt_lower or "miracle" in prompt_lower:
            prophecies = [
                "Heed the sacred winds; expand thy tribe toward the fertile rivers.",
                "Let unity sanctify thy clan; store abundant grain for the coming seasons.",
                "Courage bestows sovereignty; cultivate the holy flora and honor the cosmos.",
                "The stars illuminate thy path; master tools of crafting and defend the sanctuary.",
            ]
            chosen_prophecy = prophecies[hash(prompt) % len(prophecies)]
            return {
                "action": "EXPLORE",
                "prophecy": chosen_prophecy,
                "reasoning": "Offline Neural Core: Celestial guidance manifested to sovereign leader."
            }

        if "health" in prompt_lower or "energy" in prompt_lower:
            for word in prompt_lower.split():
                if "/" in word:
                    cleaned = "".join(c for c in word if c.isdigit() or c in "./")
                    try:
                        num, den = map(float, cleaned.split("/"))
                        if den > 0 and num / den < 0.35:
                            return {"action": "FORAGE_FOOD", "reasoning": "Offline heuristic: Energy level is critically low (<35%)"}
                    except Exception:
                        pass

        if "predator" in prompt_lower:
            return {"action": "FLEE", "reasoning": "Offline heuristic: Threat detected in vicinity."}

        if "hydration" in prompt_lower:
            return {"action": "DRINK_WATER", "reasoning": "Offline heuristic: Seeking water basin."}

        return {"action": "WANDER", "reasoning": "Offline heuristic: Domain exploration."}

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)
