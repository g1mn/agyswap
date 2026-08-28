"""agyswap.modules.tui.actions — TUI-safe account mutation layer.

Reuses agyswap's storage/keychain primitives directly, but never print()s,
sys.exit()s, or execs a subprocess like the cmd_* CLI entry points do — those
would kill the whole TUI process on a validation failure. Raises ActionError
instead so a Textual worker/action can catch it and show a notification.
"""
from __future__ import annotations

from datetime import datetime, timezone

from agyswap import (
    KeychainManager,
    StorageManager,
    fetch_google_userinfo,
    find_account,
    format_expiry_detail,
)


class ActionError(Exception):
    pass


def _load_config() -> dict:
    try:
        return StorageManager.load_config()
    except Exception as e:
        raise ActionError(f"Failed to load account data: {e}") from e


def _save_config(cfg: dict) -> None:
    try:
        StorageManager.save_config(cfg)
    except Exception as e:
        raise ActionError(f"Failed to save account data: {e}") from e


def _save_slot(slot_num, data: dict) -> None:
    try:
        StorageManager.save_slot(slot_num, data)
    except Exception as e:
        raise ActionError(f"Failed to save slot data: {e}") from e


def _remove_slot_file(slot_num) -> None:
    try:
        StorageManager.remove_slot_file(slot_num)
    except Exception as e:
        raise ActionError(f"Failed to remove slot file: {e}") from e


def switch_account(target: str, *, force: bool = False) -> dict:
    cfg = _load_config()
    accounts = cfg.get("accounts", [])
    selected = find_account(accounts, target)
    if not selected:
        raise ActionError(f"Slot '{target}' not found.")

    slot_num = selected.get("slot")
    email = selected.get("email")
    try:
        slot_data = StorageManager.load_slot(slot_num)
    except Exception as e:
        raise ActionError(f"Failed to load slot file: {e}") from e

    token_dict = slot_data.get("token", {})
    _, exp_rel, is_expired, is_soon = format_expiry_detail(token_dict.get("expiry", ""))
    if is_expired and not force:
        raise ActionError(f"Slot #{slot_num} ({email}) token has expired ({exp_rel}). Refresh with 'agyswap rotate {slot_num}'.")

    try:
        KeychainManager.set_payload({"auth_method": slot_data.get("auth_method", "consumer"), "token": token_dict})
    except Exception as e:
        raise ActionError(f"Failed to update Keychain: {e}") from e

    result = dict(selected)
    result["is_soon"] = is_soon
    result["expiry_rel"] = exp_rel
    return result


def add_current_account() -> dict:
    try:
        payload = KeychainManager.get_current_payload()
    except Exception as e:
        raise ActionError(f"No Keychain login found: {e}") from e

    token_dict = payload.get("token", {})
    access_token = token_dict.get("access_token", "")
    if not access_token:
        raise ActionError("No valid access token found in Keychain.")

    user_info = fetch_google_userinfo(access_token)
    email = user_info.get("email")
    if not email:
        raise ActionError("Could not resolve account email. Run 'agyswap add <email>' in a terminal instead.")

    cfg = _load_config()
    accounts = cfg.get("accounts", [])
    existing = next((a for a in accounts if a.get("email", "").lower() == email.lower()), None)

    if existing:
        slot_num = existing.get("slot")
    else:
        existing_slots = [a.get("slot", 0) for a in accounts]
        slot_num = min(set(range(1, max(existing_slots, default=0) + 2)) - set(existing_slots))

    now_iso = datetime.now(timezone.utc).isoformat()
    acc_entry = {
        "slot": slot_num,
        "email": email,
        "name": user_info.get("name") or (existing.get("name") if existing else ""),
        "alias": existing.get("alias", "") if existing else "",
        "auth_method": payload.get("auth_method", "consumer"),
        "disabled": (existing.get("disabled", False) if existing else False),
        "added_at": existing.get("added_at", now_iso) if existing else now_iso,
        "last_used_at": now_iso,
    }
    slot_payload = {
        "slot": slot_num,
        "email": email,
        "name": acc_entry["name"],
        "auth_method": acc_entry["auth_method"],
        "token": token_dict,
        "updated_at": now_iso,
    }
    _save_slot(slot_num, slot_payload)

    if existing:
        accounts[accounts.index(existing)] = acc_entry
    else:
        accounts.append(acc_entry)
    cfg["accounts"] = accounts
    cfg["active_slot"] = slot_num
    _save_config(cfg)
    return acc_entry


def remove_account(target: str) -> dict:
    cfg = _load_config()
    accounts = cfg.get("accounts", [])
    selected = find_account(accounts, target)
    if not selected:
        raise ActionError(f"Slot '{target}' not found.")

    slot_num = selected.get("slot")
    _remove_slot_file(slot_num)
    accounts.remove(selected)

    if cfg.get("active_slot") == slot_num:
        cfg["active_slot"] = min((a.get("slot", 0) for a in accounts), default=None)

    cfg["accounts"] = accounts
    _save_config(cfg)
    return selected


def set_disabled(target: str, disabled: bool) -> dict:
    cfg = _load_config()
    accounts = cfg.get("accounts", [])
    selected = find_account(accounts, target)
    if not selected:
        raise ActionError(f"Slot '{target}' not found.")
    selected["disabled"] = disabled
    cfg["accounts"] = accounts
    _save_config(cfg)
    return selected
