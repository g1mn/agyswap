"""
TokenBudgeter: Estimates and trims prompt/context content to strictly fit within token limits.
Uses a fast character/word heuristic (1 token ~ 3.8 chars) for zero-dependency execution.
"""

from __future__ import annotations

class TokenBudgeter:
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Fast token estimator across languages and code."""
        if not text:
            return 0
        # Average heuristic for code and multilingual text
        return max(1, int(len(text) / 3.6))

    @classmethod
    def trim_to_budget(cls, text: str, max_tokens: int) -> str:
        """Trims text to fit within max_tokens, preserving head and critical structure."""
        current_tokens = cls.estimate_tokens(text)
        if current_tokens <= max_tokens:
            return text

        lines = text.splitlines()
        max_chars = max(0, int(max_tokens * 3.6))

        def banner(remaining: int) -> str:
            full = f"\n... [Truncated {remaining} lines to fit {max_tokens} token budget] ..."
            if len(full) <= max_chars:
                return full
            short = "\n...[truncated]..."
            return short if len(short) <= max_chars else ""

        # Reserve the banner's worst-case width up front (using the full line count as an
        # upper bound on "remaining", since remaining can only have fewer digits) so the
        # banner actually appended below never pushes the result past max_chars.
        content_budget = max(0, max_chars - len(banner(len(lines))))

        truncated_lines = []
        accumulated_chars = 0
        for line in lines:
            if accumulated_chars + len(line) + 1 > content_budget:
                trailer = banner(len(lines) - len(truncated_lines))
                if trailer:
                    truncated_lines.append(trailer)
                break
            truncated_lines.append(line)
            accumulated_chars += len(line) + 1

        return "\n".join(truncated_lines)
