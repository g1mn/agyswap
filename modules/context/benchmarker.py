"""
ContextBenchmarker: Analyzes codebase token footprint and measures compression efficiency.
Zero external dependencies.
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List
from modules.context.repomap import RepoMapper
from modules.context.budgeter import TokenBudgeter

BOX_WIDTH = 61  # interior column width of the report boxes, between the │ borders


def _visible_width(text: str) -> int:
    """Terminal column width of text, counting wide/emoji glyphs as 2 columns (len() undercounts them as 1)."""
    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ("W", "F") or 0x1F300 <= ord(ch) <= 0x1FAFF or 0x2600 <= ord(ch) <= 0x27BF:
            width += 2
        else:
            width += 1
    return width


def _box_line(content: str, width: int = BOX_WIDTH) -> str:
    """Pads content to an exact visible width and wraps it with box-drawing borders."""
    pad = max(0, width - _visible_width(content))
    return f"│{content}{' ' * pad}│"


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
            "_raw_map": raw_map,
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

        border = "─" * BOX_WIDTH
        lines = [
            f"┌{border}┐",
            _box_line(" 📊 agyswap Context Compression Benchmark"),
            f"├{border}┤",
            _box_line(f"  Indexed Files      : {stats['raw_files']}"),
            _box_line(f"  Raw Codebase Lines : {raw_lines_str}"),
            _box_line(f"  Raw Token Footprint: {raw_tokens_str}"),
            f"├{border}┤",
            _box_line(f"  Repo-Map Lines     : {map_lines_str}"),
            _box_line(f"  Repo-Map Tokens    : {map_tokens_str}"),
            _box_line(f"  Saved Tokens / Run : {savings_str}"),
            f"├{border}┤",
            _box_line(f"  Compression Rate   : [{bar}] {red_pct:>5.1f}%"),
            f"└{border}┘",
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
        public_stats = {k: v for k, v in stats.items() if not k.startswith("_")}
        return json.dumps(public_stats, indent=2)

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

    @classmethod
    def run_golden_benchmark(cls, fixture_dir: str | Path | None = None, budget: int = 2000) -> Dict[str, Any]:
        """Runs benchmark against fixed multi-language Golden Repo and measures symbol recall."""
        import json
        import time

        if fixture_dir is None:
            # Look relative to project root
            base_dir = Path(__file__).resolve().parent.parent.parent
            fixture_path = base_dir / "tests" / "fixtures" / "golden_repo"
        else:
            fixture_path = Path(fixture_dir).resolve()

        if not fixture_path.exists():
            raise FileNotFoundError(f"Golden fixture directory not found at: {fixture_path}")

        meta_file = fixture_path / "metadata.json"
        expected_symbols = []
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                expected_symbols = meta.get("expected_symbols", [])
            except Exception:
                pass

        bench = cls(root_dir=fixture_path)
        start_time = time.perf_counter()
        stats = bench.run_benchmark(budget=budget)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        repo_map = stats.pop("_raw_map", "")

        matched = []
        missing = []
        for sym in expected_symbols:
            # A symbol ending mid-identifier (e.g. "class ApiClient") must not match a
            # renamed "class ApiClientV2" that merely starts with it, so require a
            # non-word boundary right after it. Symbols intentionally truncated at a
            # non-word char (e.g. "func NewRouter(") are fine as plain substrings.
            if sym and re.match(r"\w", sym[-1]):
                found = re.search(re.escape(sym) + r"(?!\w)", repo_map) is not None
            else:
                found = sym in repo_map
            if found:
                matched.append(sym)
            else:
                missing.append(sym)

        total_exp = len(expected_symbols)
        recall_pct = (len(matched) / total_exp * 100.0) if total_exp > 0 else 100.0
        map_tokens = stats["map_tokens"]
        info_density = (len(matched) / (map_tokens / 1000.0)) if map_tokens > 0 else 0.0

        stats.update({
            "is_golden": True,
            "latency_ms": round(latency_ms, 2),
            "expected_symbols_count": total_exp,
            "matched_symbols_count": len(matched),
            "missing_symbols": missing,
            "recall_pct": round(recall_pct, 1),
            "info_density": round(info_density, 1),
        })
        return stats

    @staticmethod
    def render_golden_report(stats: Dict[str, Any]) -> str:
        """Renders an ASCII visualization card for the Golden Benchmark."""
        rec_pct = stats.get("recall_pct", 100.0)
        red_pct = stats["reduction_pct"]
        latency = stats.get("latency_ms", 0.0)
        density = stats.get("info_density", 0.0)
        matched = stats.get("matched_symbols_count", 0)
        total = stats.get("expected_symbols_count", 0)

        border = "─" * BOX_WIDTH
        lines = [
            f"┌{border}┐",
            _box_line(" 🏆 agyswap Golden Quality & Context Benchmark Monitor"),
            f"├{border}┤",
            _box_line(f"  Standard Fixtures  : {stats['raw_files']} files ({stats['raw_lines']:,} lines)"),
            _box_line(f"  Raw Code Footprint : ~{stats['raw_tokens']:,} tokens"),
            _box_line(f"  Repo-Map Size      : ~{stats['map_tokens']:,} tokens"),
            f"├{border}┤",
            _box_line(f"  Token Compression  : {red_pct:>5.1f}% 🟢"),
            _box_line(f"  Symbol Recall      : {rec_pct:>5.1f}% ({matched}/{total} symbols) 🟢"),
            _box_line(f"  Information Density: {density:>5.1f} symbols / 1k Tokens 🟢"),
            _box_line(f"  AST Parsing Latency: {latency:>5.2f} ms ⚡"),
            f"└{border}┘",
        ]

        missing = stats.get("missing_symbols", [])
        if missing:
            lines.append("\n⚠️ Missing Expected Symbols:")
            for m in missing:
                lines.append(f"  • {m}")

        return "\n".join(lines)
