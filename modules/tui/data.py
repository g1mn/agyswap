"""agyswap.modules.tui.data — pure, side-effect-free snapshot builder for the TUI.

Mirrors cmd_list's active-account detection logic without any print()s, so it's
safe to call from a background worker thread.
"""
from __future__ import annotations

from agyswap import KeychainManager, StorageManager, token_fingerprint
from modules.quota import get_cached_quota


def build_snapshot() -> list:
    cfg = StorageManager.load_config()
    accounts = cfg.get("accounts", [])
    active_slot = cfg.get("active_slot")

    curr_token_hash = ""
    try:
        curr_payload = KeychainManager.get_current_payload()
        curr_token_hash = token_fingerprint(curr_payload.get("token", {}).get("access_token", ""))
    except Exception:
        pass

    rows = []
    for acc in sorted(accounts, key=lambda x: x.get("slot", 0)):
        slot = acc.get("slot")
        slot_token_hash = ""
        try:
            slot_token_hash = token_fingerprint(StorageManager.load_slot(slot).get("token", {}).get("access_token", ""))
        except Exception:
            pass

        is_active = (slot_token_hash == curr_token_hash) if curr_token_hash else (slot == active_slot)

        rows.append({
            "slot": slot,
            "email": acc.get("email", "?"),
            "name": acc.get("name", ""),
            "alias": acc.get("alias", ""),
            "auth_method": acc.get("auth_method", "consumer"),
            "disabled": acc.get("disabled", False),
            "active": is_active,
            "added_at": acc.get("added_at", ""),
            "last_used_at": acc.get("last_used_at", ""),
            "quota": get_cached_quota(acc.get("email", "")),
        })
    return rows
