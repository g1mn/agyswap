"""agyswap.modules.tui.watch — live quota-only monitor screen."""
from __future__ import annotations

from textual.binding import Binding
from textual.widgets import ListView

from . import actions
from .dashboard import AccountListScreen
from .widgets import AccountItem


class WatchScreen(AccountListScreen):
    """Live-monitor-only view. 's' toggles select mode; Enter confirms a switch
    only while selecting, so a stray keypress while just watching quota can't
    accidentally switch accounts."""

    BINDINGS = AccountListScreen.BINDINGS + [
        Binding("s", "toggle_select", "Select", show=False),
        Binding("enter", "confirm", "Confirm", priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._selecting = False

    def action_toggle_select(self) -> None:
        self._selecting = not self._selecting
        self.sub_title = "SELECT (enter to switch)" if self._selecting else ""

    def action_confirm(self) -> None:
        if not self._selecting:
            return
        listview = self.query_one("#accounts", ListView)
        if listview.index is None or not listview.children:
            return
        item = listview.children[listview.index]
        if not isinstance(item, AccountItem):
            return
        try:
            acc = actions.switch_account(str(item.slot))
            self.app.notify(f"Switched to #{item.slot} ({item.row.get('email')}).")
            if acc.get("is_soon"):
                self.app.notify(f"Token expiring soon ({acc.get('expiry_rel')}).", severity="warning")
            self.app.trigger_refresh(True)
        except Exception as e:
            self.app.notify(str(e), severity="warning")
        self._selecting = False
        self.sub_title = ""
