"""
StateManager: Extracts and synchronizes lightweight working state snapshots (.agents/memory/STATE.md).
Captures git branch, modified files, diff summary, and high-level goals.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from datetime import datetime, timezone

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

            # Status short
            res = subprocess.run(["git", "status", "--porcelain"], cwd=self.root_dir, capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if len(line) < 4:
                        continue
                    xy = line[:2]
                    filename = line[3:].strip()
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
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.memory_dir.chmod(0o700)
        except Exception:
            pass

        state_file = self.memory_dir / "STATE.md"
        content = self.snapshot(goal)
        state_file.write_text(content, encoding="utf-8")
        try:
            state_file.chmod(0o600)
        except Exception:
            pass
        return state_file
