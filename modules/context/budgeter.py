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
        truncated_lines = []
        accumulated_chars = 0
        max_chars = int(max_tokens * 3.6)

        for line in lines:
            if accumulated_chars + len(line) + 1 > max_chars:
                truncated_lines.append(f"\n... [Truncated {len(lines) - len(truncated_lines)} lines to fit {max_tokens} token budget] ...")
                break
            truncated_lines.append(line)
            accumulated_chars += len(line) + 1

        return "\n".join(truncated_lines)
