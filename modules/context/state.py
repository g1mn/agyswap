"""
StateManager: Extracts and synchronizes lightweight working state snapshots (.agents/memory/STATE.md).
Captures git branch, modified files, diff summary, and high-level goals.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def secure_mkdir(path: Path, mode: int = 0o700) -> None:
    """Creates a directory (and parents) that only the owner can access, with no world/group-readable window."""
    path.mkdir(parents=True, exist_ok=True, mode=mode)


def secure_write(path: Path, content: str, mode: int = 0o600) -> None:
    """Writes content to path with restrictive permissions from the moment of creation (no chmod-after race)."""
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)


class StateManager:
    def __init__(self, root_dir: str | Path = "."):
        self.root_dir = Path(root_dir).resolve()
        self.memory_dir = self.root_dir / ".agents" / "memory"

    def get_git_status(self) -> dict:
        """Extracts git status summary without heavy diff outputs."""
        status = {
            "branch": "unknown",
            "modified": [],
            "staged": [],
            "untracked": [],
            "diff_summary": ""
        }
        try:
            # Branch name
            res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.root_dir, capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                status["branch"] = res.stdout.strip()

            # Status short. Use -z (NUL-delimited, unquoted paths) so filenames with spaces
            # and rename records ("new\0old\0") parse correctly instead of naive line-splitting.
            res = subprocess.run(["git", "status", "--porcelain", "-z"], cwd=self.root_dir, capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                tokens = res.stdout.split("\0")
                i = 0
                while i < len(tokens):
                    entry = tokens[i]
                    i += 1
                    if len(entry) < 4:
                        continue
                    xy = entry[:2]
                    filename = entry[3:]
                    if xy[0] in ("R", "C"):
                        old_path = tokens[i] if i < len(tokens) else ""
                        i += 1
                        if old_path:
                            filename = f"{old_path} -> {filename}"
                    if xy == "??":
                        status["untracked"].append(filename)
                    elif xy[0] in "AMRD":
                        status["staged"].append(f"{xy[0]} {filename}")
                    elif xy[1] in "MD":
                        status["modified"].append(filename)

            # Diff stat
            res = subprocess.run(["git", "diff", "--stat"], cwd=self.root_dir, capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                status["diff_summary"] = res.stdout.strip()
        except Exception:
            pass
        return status

    def snapshot(self, goal: str = "Active Development") -> str:
        """Generates a super-compact working state snapshot (< 300 tokens)."""
        git_info = self.get_git_status()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# 🧠 Working State Snapshot",
            f"- **Timestamp**: {now}",
            f"- **Branch**: `{git_info['branch']}`",
            f"- **Current Goal**: {goal}",
            "",
            "## 📝 Changed Files",
        ]

        if git_info["staged"]:
            lines.append("### Staged")
            for f in git_info["staged"][:10]:
                lines.append(f"- `{f}`")

        if git_info["modified"]:
            lines.append("### Unstaged Modifications")
            for f in git_info["modified"][:10]:
                lines.append(f"- `M` {f}")
        elif not git_info["staged"]:
            lines.append("- (No uncommitted modifications)")

        if git_info["untracked"]:
            lines.append("### Untracked Files")
            for f in git_info["untracked"][:5]:
                lines.append(f"- `?` {f}")

        if git_info["diff_summary"]:
            lines.extend([
                "",
                "## 📊 Diff Summary",
                "```text",
                git_info["diff_summary"],
                "```"
            ])

        return "\n".join(lines)

    def save_snapshot(self, goal: str = "Active Development") -> Path:
        """Saves working state to .agents/memory/STATE.md with secure permissions."""
        secure_mkdir(self.memory_dir)
        state_file = self.memory_dir / "STATE.md"
        secure_write(state_file, self.snapshot(goal))
        return state_file
