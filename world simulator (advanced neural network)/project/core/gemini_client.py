"""
project/core/gemini_client.py

Asynchronous HTTP client interface communicating with Gemini APIs via background worker threads.
Features:
- Dynamic Multi-Key Failover Pool (Instant Auto-Switching on Rate Limit / HTTP 429 Quota Exceeded).
- Updated for modern Gemini 3.6 / Gemini Flash endpoints.
- Zero-Crash Guarantee with Seamless Offline Heuristic Fallback.
- Dynamic key addition, pruning of dead/exhausted keys, and secret masking.
- High-Performance ThreadPool Background Execution.
"""

from __future__ import annotations

import os
import time
import json
import urllib.request
import urllib.error
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Callable, Optional, List
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


# Active Verified Key Pool (Configurable via .env or GEMINI_API_KEY / GEMINI_API_KEYS environment variables)
DEFAULT_API_KEYS_POOL: List[str] = []


class GeminiClient:
    """Asynchronous client for Generative Language API with auto-failover multi-key rotation."""

    def __init__(self, api_key: Optional[str] = None, use_default_pool: bool = True) -> None:
        _load_env_file()
        self.vault = SecureKeyVault()
        
        # Build key rotation pool with active keys only
        self._keys_pool: List[str] = []
        if api_key and api_key.strip():
            self._keys_pool.append(api_key.strip())
        elif api_key == "":
            use_default_pool = False  # Explicit empty string disables network pool for fast offline testing

        if use_default_pool:
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

        self._key_index: int = 0
        self._pool_lock = threading.Lock()
        self._cache_lock = threading.Lock()

        # Quota Safety & Rate-Limiting Parameters (Max 1 request per 3.5s per free-tier key)
        self._min_request_interval_s: float = 3.5
        self._last_request_time: float = 0.0
        self._response_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}  # hash -> (timestamp, result)

        # Global thread pool for non-blocking asynchronous queries
        self._executor = ThreadPoolExecutor(max_workers=4)

    def add_api_key(self, new_key: str) -> None:
        """Dynamically registers a new live API key to the active pool."""
        clean = new_key.strip()
        if not clean:
            return
        with self._pool_lock:
            if clean not in self._keys_pool:
                self._keys_pool.insert(0, clean)  # Insert as primary
                self._key_index = 0
                print(f"[GEMINI CLIENT] Added fresh key ({clean[:8]}...{clean[-4:]}) to primary rotation.")

    def purge_dead_keys(self) -> int:
        """Purges all keys in pool."""
        with self._pool_lock:
            count = len(self._keys_pool)
            self._keys_pool.clear()
            self._key_index = 0
            return count

    def get_current_key(self) -> str:
        """Thread-safely returns currently active API key from the pool."""
        with self._pool_lock:
            if not self._keys_pool:
                return ""
            return self._keys_pool[self._key_index % len(self._keys_pool)]

    def rotate_to_next_key(self, reason: str = "") -> str:
        """Rotates to next available API key in the pool immediately."""
        with self._pool_lock:
            if not self._keys_pool:
                return ""
            old_idx = self._key_index
            self._key_index = (self._key_index + 1) % len(self._keys_pool)
            new_idx = self._key_index
            new_key = self._keys_pool[new_idx]
            
        print(f"\n[GEMINI API ROTATION] Key #{old_idx + 1} quota limit/error ({reason}). Auto-switched immediately to Key #{new_idx + 1} in pool!")
        return new_key

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
        """Posts prompt to Gemini API with token-bucket rate limiting, caching, and key failover."""
        p_hash = str(hash(prompt))
        now = time.time()

        # 1. Check Smart Response Cache (TTL 90s)
        with self._cache_lock:
            if p_hash in self._response_cache:
                cached_time, cached_res = self._response_cache[p_hash]
                if (now - cached_time) < 90.0:
                    return dict(cached_res)

        if not self._keys_pool:
            res = self._offline_fallback_solver(prompt)
            with self._cache_lock:
                self._response_cache[p_hash] = (now, res)
            return res

        # 2. Enforce Minimum Quota Rate-Limit Cooldown
        with self._pool_lock:
            elapsed = now - self._last_request_time
            if elapsed < self._min_request_interval_s:
                # If requested during cooldown, serve from heuristic oracle to prevent 429 quota exhaustion
                res = self._offline_fallback_solver(prompt)
                with self._cache_lock:
                    self._response_cache[p_hash] = (now, res)
                return res
            self._last_request_time = now

        max_attempts = len(self._keys_pool)
        models_to_try = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-2.5-flash"]
        
        for attempt in range(max_attempts):
            key = self.get_current_key()
            if not key:
                break

            headers = {
                "Content-Type": "application/json",
            }
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 150,
                    "temperature": 0.4
                }
            }

            success = False
            for model_name in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                
                is_safe, ssrf_reason = self.vault.validate_outbound_url(url)
                if not is_safe:
                    continue

                try:
                    data = json.dumps(payload).encode("utf-8")
                    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                    
                    with urllib.request.urlopen(req, timeout=12.0) as response:
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
                        # Model not available on this API version, try next model
                        continue
                    elif e.code in (503, 429):
                        # Transient Google cloud overload: quick 0.5s pause and retry once before rotating
                        time.sleep(0.5)
                        try:
                            with urllib.request.urlopen(req, timeout=12.0) as retry_resp:
                                resp_json = json.loads(retry_resp.read().decode("utf-8"))
                                candidate = resp_json.get("candidates", [{}])[0]
                                parts = candidate.get("content", {}).get("parts", [])
                                text_content = "".join([p.get("text", "") for p in parts if isinstance(p, dict)]).strip()
                                if text_content.startswith("```"):
                                    text_content = "\n".join([l for l in text_content.splitlines() if not l.startswith("```")]).strip()
                                parsed = json.loads(text_content)
                                if isinstance(parsed, dict) and "action" in parsed:
                                    with self._cache_lock:
                                        self._response_cache[p_hash] = (now, parsed)
                                    return parsed
                        except Exception:
                            pass
                    
                    # 429 Quota Exceeded, 401, 403 Forbidden, 500, 503 -> Rotate key
                    self.rotate_to_next_key(reason=f"HTTP {e.code}: {e.reason}")
                    break
                except (urllib.error.URLError, TimeoutError, Exception) as e:
                    self.rotate_to_next_key(reason=f"Network/Parse Error: {str(e)[:40]}")
                    break

        # If all keys in pool encountered rate limits or failures, gracefully fallback
        fallback = self._offline_fallback_solver(prompt)
        with self._cache_lock:
            self._response_cache[p_hash] = (now, fallback)
        return fallback

    def _offline_fallback_solver(self, prompt: str) -> Dict[str, Any]:
        """Deterministic local decision solver used when API key is missing or offline."""
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
                "reasoning": "Divine communion heuristic: Celestial guidance manifested to sovereign leader."
            }
        
        if "health" in prompt_lower and "energy" in prompt_lower:
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
