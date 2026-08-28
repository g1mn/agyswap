"""agyswap.modules.tui.widgets — quota bar rendering + list/panel widgets."""
from __future__ import annotations

import time

from rich.text import Text
from textual.widgets import Label, ListItem, Static

from .theme import DIM, severity_color

STALE_OK_S = 180
BAR_WIDTH = 16
FILLED = "━"
EMPTY = "─"


def bar_cells(used_pct: float, width: int = BAR_WIDTH) -> str:
    used_pct = max(0.0, min(100.0, used_pct))
    filled = round(width * used_pct / 100)
    return FILLED * filled + EMPTY * (width - filled)


def usage_line(model_id: str, m: dict, *, fresh: bool) -> Text:
    used = m.get("used_pct", 0.0)
    style = severity_color(used) if fresh else f"{DIM} dim"
    line = Text()
    line.append(f"  {model_id:<22}", style="bold" if fresh else DIM)
    line.append(bar_cells(used), style=style)
    line.append(f" {used:>5.1f}%", style=style)
    resets = m.get("resets_at")
    if resets:
        line.append(f"  resets {resets}", style=DIM)
    return line


def account_summary(row: dict, now: float) -> Text:
    """Multi-line block for one account: header + one usage_line per real model
    (no fabricated 5h/7d split — quota.py only ever gives us real per-model data)."""
    text = Text()
    slot = row.get("slot")
    email = row.get("email", "?")
    alias = row.get("alias") or ""
    label = f" [{alias}]" if alias else ""
    disabled = " (disabled)" if row.get("disabled") else ""
    active = " ●" if row.get("active") else ""
    text.append(f"#{slot} {email}{label}{disabled}{active}\n", style="bold" if row.get("active") else "")

    quota = row.get("quota")
    if not quota:
        text.append("  (no quota data yet)\n", style=DIM)
        return text

    fresh = (now - quota.get("fetched_at", 0)) < STALE_OK_S and not quota.get("stale")
    models = quota.get("models") or {}
    if not models:
        text.append("  (no model quota reported)\n", style=DIM)
    for model_id in sorted(models):
        text.append(usage_line(model_id, models[model_id], fresh=fresh))
        text.append("\n")
    return text


def mini_account_text(row: dict) -> Text:
    """Compact one-line summary for list rows (switch/watch screens)."""
    slot = row.get("slot")
    email = row.get("email", "?")
    alias = row.get("alias") or ""
    label = f" [{alias}]" if alias else ""
    disabled = " (disabled)" if row.get("disabled") else ""
    active = " ●" if row.get("active") else ""

    text = Text(f"#{slot} {email}{label}{disabled}{active}", style="bold" if row.get("active") else "")

    models = ((row.get("quota") or {}).get("models")) or {}
    if models:
        worst_id = min(models, key=lambda k: models[k].get("remaining_pct", 100.0))
        worst = models[worst_id]
        used = worst.get("used_pct", 0.0)
        text.append(f"   {worst_id}: {used:.0f}%", style=severity_color(used))
        if len(models) > 1:
            text.append(f" (+{len(models) - 1} more)", style=DIM)
    return text


class AccountsPanel(Static):
    """Always-visible quota monitor on the dashboard."""

    def update_rows(self, rows: list) -> None:
        if not rows:
            self.update("No registered slots. Press 'a' to add the current agy login.")
            return
        now = time.time()
        text = Text()
        for row in rows:
            text.append(account_summary(row, now))
            text.append("\n")
        self.update(text)


class AccountItem(ListItem):
    """One row in a switch/watch account list."""

    def __init__(self, row: dict) -> None:
        self.slot = row.get("slot")
        self.row = row
        super().__init__(Label(mini_account_text(row)))


class MenuItem(ListItem):
    """One row in the dashboard's drill-down menu."""

    def __init__(self, action_id: str, label: str) -> None:
        self.action_id = action_id
        super().__init__(Label(label))
