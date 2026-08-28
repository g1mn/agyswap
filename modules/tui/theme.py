"""agyswap.modules.tui.theme — colors and severity thresholds for the TUI."""
from __future__ import annotations

from textual.theme import Theme

OK = "#4caf50"
WARN = "#e8a33d"
CRIT = "#e64553"
DIM = "#6c7086"
ACCENT = "#89b4fa"

WARN_THRESHOLD = 70.0
CRIT_THRESHOLD = 90.0


def severity_color(used_pct: float) -> str:
    if used_pct >= CRIT_THRESHOLD:
        return CRIT
    if used_pct >= WARN_THRESHOLD:
        return WARN
    return OK


AGYSWAP_DARK = Theme(
    name="agyswap-dark",
    primary=ACCENT,
    secondary=DIM,
    accent=ACCENT,
    success=OK,
    warning=WARN,
    error=CRIT,
    dark=True,
)
