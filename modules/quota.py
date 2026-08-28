"""agyswap.modules.quota — Gemini API quota tracking (per-account, per-model).

Fetches usage from Google's Cloud Code Assist API using each account's stored
OAuth access token. Unlike a naive port of this idea, this module:
  - merges into the existing cache instead of clobbering it every write,
  - TTL-gates re-fetches per account instead of hitting the API unconditionally,
  - exposes real per-model quota instead of fabricating a 5h/7d split the API
    doesn't actually provide.
"""
from __future__ import annotations

import fcntl
import json
import os
import time
import urllib.request
import urllib.error
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path.home() / ".agyswap"
QUOTA_CACHE_FILE = BASE_DIR / "quota_cache.json"
QUOTA_LOCK_FILE = BASE_DIR / ".quota.lock"
QUOTA_API_URL = "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota"
DEFAULT_TTL_SECONDS = 45


@contextmanager
def _cache_lock():
    """Exclusive lock around quota_cache.json's read-modify-write cycle — without
    this, the TUI's background poller and a concurrent `agyswap quota` CLI call
    can each read a pre-update snapshot and clobber each other's writes."""
    BASE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(str(QUOTA_LOCK_FILE), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except Exception:
            pass


class QuotaFetchError(Exception):
    def __init__(self, message: str, kind: str):
        super().__init__(message)
        self.kind = kind  # "auth" | "transient"


def _secure_opener(path, flags):
    return os.open(path, flags | os.O_CREAT | os.O_TRUNC, 0o600)


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    with open(tmp, "w", encoding="utf-8", opener=_secure_opener) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def read_cache() -> dict:
    if not QUOTA_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(QUOTA_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _fetch_raw(access_token: str) -> dict:
    req = urllib.request.Request(
        QUOTA_API_URL,
        data=b"{}",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise QuotaFetchError(f"HTTP {e.code}", kind=("auth" if e.code in (401, 403) else "transient")) from e
    except Exception as e:
        raise QuotaFetchError(str(e), kind="transient") from e


def _map_buckets(resp: dict) -> dict:
    """Honest per-model exposure — no fabricated 5h/7d split."""
    models = {}
    for b in resp.get("buckets", []):
        remaining = b.get("remainingFraction", 1.0)
        models[b.get("modelId", "unknown")] = {
            "remaining_pct": round(remaining * 100, 1),
            "used_pct": round((1 - remaining) * 100, 1),
            "resets_at": b.get("resetTime", ""),
        }
    return models


def fetch_for_account(email: str, access_token: str, *, force: bool = False) -> dict:
    """Fetches quota for one account, TTL-gated. On any failure — network error,
    auth error, or a malformed API response — degrades to a stale cache entry
    (empty models if there was no prior successful fetch) rather than raising,
    and always advances fetched_at so a permanently-failing account is retried
    at most once per TTL window instead of on every single call."""
    with _cache_lock():
        cache = read_cache()
        entry = cache.get(email)
        if not force and entry and (time.time() - entry.get("fetched_at", 0)) < DEFAULT_TTL_SECONDS:
            return entry
        try:
            models = _map_buckets(_fetch_raw(access_token))
        except QuotaFetchError as e:
            error = e
        except Exception as e:
            error = QuotaFetchError(f"malformed API response: {e}", kind="transient")
        else:
            new_entry = {"fetched_at": int(time.time()), "models": models, "stale": False}
            cache[email] = new_entry
            _atomic_write_json(QUOTA_CACHE_FILE, cache)
            return new_entry

        stale_entry = dict(entry) if entry else {"models": {}}
        stale_entry["fetched_at"] = int(time.time())
        stale_entry["stale"] = True
        stale_entry["last_error"] = str(error)
        cache[email] = stale_entry
        _atomic_write_json(QUOTA_CACHE_FILE, cache)
        return stale_entry


def fetch_all(accounts_with_tokens: list, *, force: bool = False) -> dict:
    """accounts_with_tokens: list[(email, access_token)]. Re-reads the full cache
    first, so accounts not present in this batch are never dropped (merge, not
    clobber). Per-account failures don't abort the batch."""
    cache = read_cache()
    for email, token in accounts_with_tokens:
        try:
            cache[email] = fetch_for_account(email, token, force=force)
        except QuotaFetchError:
            continue
    return cache


def get_cached_quota(email: str) -> dict | None:
    """Non-blocking cache read for a single account. Returns
    {"fetched_at": int, "models": {...}, "stale": bool} or None."""
    return read_cache().get(email)
