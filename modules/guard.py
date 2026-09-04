"""agyswap.modules.guard — Auto-Rotating Rate-Limit Protector for agy CLI.

Monitors active agy CLI sessions. When a 429 Too Many Requests or
RESOURCE_EXHAUSTED error occurs, automatically switches to the next healthy
account and resumes the conversation context seamlessly via `agy -c`.
"""
from __future__ import annotations

import os
import re
import sys
import time
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

AGY_LOG_DIR = Path.home() / ".gemini" / "antigravity-cli" / "log"
AGY_CLI_LOG = Path.home() / ".gemini" / "antigravity-cli" / "cli.log"

# Regex patterns indicating rate limits or quota exhaustion
RATE_LIMIT_PATTERNS = [
    re.compile(r"RESOURCE_EXHAUSTED", re.IGNORECASE),
    re.compile(r"status[:\s=]+429\b", re.IGNORECASE),
    re.compile(r"quota\s*(exceeded|limit|exhausted)", re.IGNORECASE),
    re.compile(r"rate\s*limit\s*(reached|exceeded)", re.IGNORECASE),
    re.compile(r"too\s*many\s*requests", re.IGNORECASE),
    re.compile(r"Resource\s*has\s*been\s*exhausted", re.IGNORECASE),
]


def get_latest_log_file() -> Optional[Path]:
    """Finds the most recently modified agy log file."""
    if AGY_CLI_LOG.exists():
        try:
            return AGY_CLI_LOG.resolve()
        except Exception:
            pass
    if AGY_LOG_DIR.exists():
        logs = list(AGY_LOG_DIR.glob("*.log"))
        if logs:
            return max(logs, key=lambda p: p.stat().st_mtime)
    return None


def inspect_log_tail_for_quota_error(log_path: Optional[Path], since_mtime: float, max_lines: int = 150) -> Tuple[bool, str]:
    """Inspects recent log entries created/modified after `since_mtime` for quota errors."""
    if not log_path or not log_path.exists():
        return False, ""

    try:
        if log_path.stat().st_mtime < since_mtime - 5.0:
            return False, ""

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            tail_lines = lines[-max_lines:] if len(lines) > max_lines else lines

        for line in reversed(tail_lines):
            for pat in RATE_LIMIT_PATTERNS:
                if pat.search(line):
                    return True, line.strip()
    except Exception:
        pass
    return False, ""


class AgyGuard:
    def __init__(
        self,
        resume: bool = True,
        dangerously_skip_permissions: bool = False,
        auto_ctx: bool = False,
        max_switches: int = 10,
        extra_args: Optional[List[str]] = None,
    ):
        self.resume = resume
        self.skip_perms = dangerously_skip_permissions
        self.auto_ctx = auto_ctx
        self.max_switches = max_switches
        self.extra_args = extra_args or []

    def run(self, initial_target: Optional[str] = None) -> int:
        """Runs the guard supervision loop."""
        import agyswap

        agy_bin = shutil.which("agy") or "/opt/homebrew/bin/agy"
        if not Path(agy_bin).exists():
            print(agyswap.red(f"✗ 'agy' binary not found at '{agy_bin}'. Please install Antigravity CLI first."))
            return 1

        cfg = agyswap.StorageManager.load_config()
        accounts = cfg.get("accounts", [])
        if not accounts:
            print(agyswap.red("✗ No registered accounts. Run 'agyswap add' to register accounts first."))
            return 1

        # If an initial target is specified, switch to it first
        if initial_target:
            print(agyswap.cyan(f"🛡️  [agyswap guard] Switching to initial account: {initial_target}"))
            agyswap.cmd_switch(
                agyswap.argparse.Namespace(
                    target=initial_target,
                    dry_run=False,
                    force=False,
                    resume=False,
                    new_session=False,
                    dangerously_skip_permissions=False,
                )
            )

        switch_count = 0
        consecutive_errors = 0
        max_consecutive_errors = len([a for a in accounts if not a.get("disabled", False)]) or 3

        print(agyswap.cyan("🛡️  agyswap guard started. Rate-limit protection is ACTIVE."))
        print(agyswap.gray("   • Auto-rotate on 429/Quota Limit: ON"))
        print(agyswap.gray(f"   • Context auto-compaction (--ctx): {'ON' if self.auto_ctx else 'OFF'}"))
        print(agyswap.gray(f"   • Auto-approve permissions (-y): {'ON' if self.skip_perms else 'OFF'}\n"))

        while True:
            cfg = agyswap.StorageManager.load_config()
            active_slot = cfg.get("active_slot")
            current_acc = next((a for a in cfg.get("accounts", []) if a.get("slot") == active_slot), None)
            active_email = current_acc.get("email", "?") if current_acc else "?"

            cmd = [agy_bin]
            if self.resume or switch_count > 0:
                cmd.append("-c")
            if self.skip_perms:
                cmd.append("--dangerously-skip-permissions")
            if self.extra_args:
                cmd.extend(self.extra_args)

            session_start_time = time.time()
            log_target = get_latest_log_file()
            log_start_mtime = log_target.stat().st_mtime if log_target and log_target.exists() else session_start_time

            print(agyswap.bold(agyswap.green(f"▶ Launching agy session [Slot #{active_slot} · {active_email}]...")))
            print(agyswap.gray("─" * 60))

            # Run interactive process sharing stdin/stdout/stderr
            try:
                proc = subprocess.run(cmd)
                exit_code = proc.returncode
            except KeyboardInterrupt:
                print(agyswap.yellow("\n🛑 agyswap guard interrupted by user (Ctrl+C). Exiting."))
                return 130
            except Exception as e:
                print(agyswap.red(f"\n✗ Error launching agy: {e}"))
                return 1

            session_duration = time.time() - session_start_time
            print(agyswap.gray("─" * 60))

            # Inspect logs for rate limit / quota error
            current_log = get_latest_log_file()
            is_quota_err, err_snippet = inspect_log_tail_for_quota_error(current_log, log_start_mtime)

            # Normal voluntary exit (e.g. exit_code == 0 and session lasted > 3 seconds with no quota error)
            if exit_code == 0 and not is_quota_err:
                print(agyswap.green(f"✓ agy session finished normally (duration: {int(session_duration)}s). Exiting guard."))
                return 0

            # If session was super brief and had no error, assume user quit immediately
            if session_duration < 3.0 and exit_code == 0:
                print(agyswap.gray("✓ agy exited immediately without errors. Exiting guard."))
                return 0

            # If quota exhaustion detected OR non-zero exit with quota signs
            if is_quota_err or exit_code != 0:
                if is_quota_err:
                    print(agyswap.red(f"\n⚡ [agyswap guard] Quota limit / 429 detected on Slot #{active_slot} ({active_email})!"))
                    if err_snippet:
                        print(agyswap.gray(f"   Log snippet: {err_snippet[:100]}..."))
                else:
                    print(agyswap.yellow(f"\n⚠️  [agyswap guard] agy exited with code {exit_code}."))

                switch_count += 1
                consecutive_errors += 1

                if switch_count > self.max_switches:
                    print(agyswap.red(f"✗ Maximum switch limit ({self.max_switches}) reached. Stopping guard."))
                    return 1

                if consecutive_errors >= max_consecutive_errors:
                    print(agyswap.red(f"✗ All {consecutive_errors} available accounts appear to be exhausted or failing."))
                    print(agyswap.yellow("💡 Tip: Try 'agyswap quota' to check limits or wait for quota reset."))
                    return 1

                # If auto_ctx is enabled, run context compaction before switching
                if self.auto_ctx:
                    print(agyswap.cyan("🧠 Compacting repository context and saving state before switch..."))
                    try:
                        agyswap.cmd_context(
                            agyswap.argparse.Namespace(
                                ctx_action="clean",
                                dir=".",
                                budget=2000,
                                goal="Auto-recovery session continuation via guard",
                            )
                        )
                    except Exception as ce:
                        print(agyswap.yellow(f"  (Context compaction skipped: {ce})"))

                # Rotate to next enabled account
                print(agyswap.cyan("🔄 Rotating to next available account profile..."))
                next_acc = agyswap._next_enabled_account(cfg.get("accounts", []), active_slot)
                if not next_acc:
                    print(agyswap.red("✗ No enabled accounts available for rotation."))
                    return 1

                next_slot = next_acc.get("slot")
                next_email = next_acc.get("email")

                # Pre-emptively refresh token if expired
                try:
                    sdata = agyswap.StorageManager.load_slot(next_slot)
                    exp_raw = sdata.get("token", {}).get("expiry", "")
                    _, _, is_expired, _ = agyswap.format_expiry_detail(exp_raw)
                    if is_expired:
                        print(agyswap.yellow(f"⚡ Token for #{next_slot} ({next_email}) is expired. Refreshing..."))
                        agyswap.rotate_single_slot(next_slot, is_active=False)
                except Exception:
                    pass

                # Execute switch
                agyswap.cmd_switch(
                    agyswap.argparse.Namespace(
                        target=str(next_slot),
                        dry_run=False,
                        force=False,
                        resume=False,
                        new_session=False,
                        dangerously_skip_permissions=False,
                    )
                )

                print(agyswap.green(f"🚀 Re-launching session with #{next_slot} ({next_email}) preserving context (`agy -c`)...\n"))
                time.sleep(0.5)
                continue
            else:
                return exit_code
