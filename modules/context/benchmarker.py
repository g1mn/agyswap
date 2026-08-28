"""
ContextBenchmarker: Analyzes codebase token footprint and measures compression efficiency.
Zero external dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, List
from modules.context.repomap import RepoMapper
from modules.context.budgeter import TokenBudgeter


class ContextBenchmarker:
    def __init__(self, root_dir: str | Path = "."):
        self.root_dir = Path(root_dir).resolve()

    def run_benchmark(self, budget: int = 2000) -> Dict[str, Any]:
        """Calculates raw codebase metrics vs. compressed Repo-Map metrics."""
        mapper = RepoMapper(root_dir=self.root_dir, max_tokens=budget)
        
        raw_files = 0
        raw_chars = 0
        raw_lines = 0
        lang_stats: Dict[str, Dict[str, int]] = {}

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in mapper.ignored_dirs and not d.startswith(".")]
            for file in sorted(files):
                ext = Path(file).suffix.lower()
                if ext in mapper.supported_extensions:
                    full_path = Path(root) / file
                    try:
                        rel_path = full_path.relative_to(self.root_dir)
                    except ValueError:
                        rel_path = full_path

                    if any(part.startswith(".") for part in rel_path.parts):
                        continue

                    try:
                        content = full_path.read_text(encoding="utf-8", errors="ignore")
                        lines = content.splitlines()
                        raw_files += 1
                        raw_chars += len(content)
                        raw_lines += len(lines)

                        ext_key = ext if ext else "(no ext)"
                        if ext_key not in lang_stats:
                            lang_stats[ext_key] = {"files": 0, "lines": 0, "chars": 0}
                        lang_stats[ext_key]["files"] += 1
                        lang_stats[ext_key]["lines"] += len(lines)
                        lang_stats[ext_key]["chars"] += len(content)
                    except Exception:
                        continue

        raw_tokens = max(1, int(raw_chars / 3.6)) if raw_chars > 0 else 0

        # Generate Map
        raw_map = mapper.generate_map()
        trimmed_map = TokenBudgeter.trim_to_budget(raw_map, max_tokens=budget)
        map_chars = len(trimmed_map)
        map_lines = len(trimmed_map.splitlines())
        map_tokens = TokenBudgeter.estimate_tokens(trimmed_map)

        savings_tokens = max(0, raw_tokens - map_tokens)
        reduction_pct = ((raw_tokens - map_tokens) / raw_tokens * 100) if raw_tokens > 0 else 0.0

        return {
            "raw_files": raw_files,
            "raw_lines": raw_lines,
            "raw_chars": raw_chars,
            "raw_tokens": raw_tokens,
            "map_lines": map_lines,
            "map_chars": map_chars,
            "map_tokens": map_tokens,
            "budget": budget,
            "savings_tokens": savings_tokens,
            "reduction_pct": round(reduction_pct, 1),
            "lang_stats": lang_stats,
        }

    @staticmethod
    def render_cli_report(stats: Dict[str, Any]) -> str:
        """Renders an ASCII visualization report of token efficiency."""
        red_pct = stats["reduction_pct"]
        bar_len = 20
        filled = int(bar_len * (red_pct / 100.0))
        bar = "█" * filled + "░" * (bar_len - filled)

        raw_lines_str = f"{stats['raw_lines']:,} lines ({stats['raw_chars']:,} chars)"
        raw_tokens_str = f"~{stats['raw_tokens']:,} tokens"
        map_lines_str = f"{stats['map_lines']:,} lines"
        map_tokens_str = f"~{stats['map_tokens']:,} / {stats['budget']:,} tokens"
        savings_str = f"~{stats['savings_tokens']:,} tokens"

        lines = [
            "┌─────────────────────────────────────────────────────────────┐",
            "│ 📊 agyswap Context Compression Benchmark                     │",
            "├─────────────────────────────────────────────────────────────┤",
            f"│  Indexed Files      : {stats['raw_files']:<38}│",
            f"│  Raw Codebase Lines : {raw_lines_str:<38}│",
            f"│  Raw Token Footprint: {raw_tokens_str:<38}│",
            "├─────────────────────────────────────────────────────────────┤",
            f"│  Repo-Map Lines     : {map_lines_str:<38}│",
            f"│  Repo-Map Tokens    : {map_tokens_str:<38}│",
            f"│  Saved Tokens / Run : {savings_str:<38}│",
            "├─────────────────────────────────────────────────────────────┤",
            f"│  Compression Rate   : [{bar}] {red_pct:>5.1f}% │",
            "└─────────────────────────────────────────────────────────────┘",
        ]

        if stats["lang_stats"]:
            lines.append("\n📁 Language Breakdown:")
            for ext, data in sorted(stats["lang_stats"].items(), key=lambda x: x[1]["lines"], reverse=True):
                tokens_est = int(data["chars"] / 3.6)
                lines.append(f"  • {ext:<8}: {data['files']:>2} files | {data['lines']:>5,} lines | ~{tokens_est:>6,} tokens")

        return "\n".join(lines)

    @staticmethod
    def render_json(stats: Dict[str, Any]) -> str:
        """Renders benchmark statistics in JSON format for CI/CD pipelines."""
        import json
        return json.dumps(stats, indent=2)

    @staticmethod
    def render_markdown(stats: Dict[str, Any]) -> str:
        """Renders benchmark statistics as GitHub-flavored markdown with table and badges."""
        red_pct = stats["reduction_pct"]
        lines = [
            f"### 📊 agyswap Context Compression Benchmark",
            "",
            f"[![Token Savings](https://img.shields.io/badge/Token_Savings-{red_pct}%25-brightgreen.svg)](https://g1mn.github.io/agyswap/) ",
            f"[![Saved Tokens](https://img.shields.io/badge/Saved_per_Session-~{stats['savings_tokens']:,}_Tokens-blue.svg)](https://g1mn.github.io/agyswap/)",
            "",
            "| Metric | Raw Codebase | Repo-Map Compressed | Net Savings |",
            "| :--- | :---: | :---: | :---: |",
            f"| **Files** | `{stats['raw_files']}` | `{stats['raw_files']}` | - |",
            f"| **Lines** | `{stats['raw_lines']:,}` | `{stats['map_lines']:,}` | **{stats['raw_lines'] - stats['map_lines']:,} lines** |",
            f"| **Estimated Tokens** | `~{stats['raw_tokens']:,}` | `~{stats['map_tokens']:,}` | **🔥 ~{stats['savings_tokens']:,} tokens ({red_pct}%)** |",
            "",
        ]

        if stats["lang_stats"]:
            lines.append("#### 📁 Language Breakdown")
            lines.append("| Language | Files | Lines | Raw Tokens |")
            lines.append("| :--- | :---: | :---: | :---: |")
            for ext, data in sorted(stats["lang_stats"].items(), key=lambda x: x[1]["lines"], reverse=True):
                tokens_est = int(data["chars"] / 3.6)
                lines.append(f"| `{ext}` | {data['files']} | {data['lines']:,} | ~{tokens_est:,} |")

        return "\n".join(lines)
