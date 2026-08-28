"""agyswap.modules.tui.dashboard — main dashboard screen, account-list base, switch picker."""
from __future__ import annotations

from functools import partial

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListView

from . import actions
from .widgets import AccountItem, AccountsPanel, MenuItem, mini_account_text

FLASH_S = 1.5


class DashboardScreen(Screen):
    BINDINGS = [
        ("s", "open_switch", "Switch"),
        ("w", "app.open_watch", "Watch"),
        Binding("a", "open_add", "Add", show=False),
        Binding("f", "app.refresh_full", "Refresh", show=False),
        Binding("j,down", "cursor_down", "Down", show=False),
        Binding("k,up", "cursor_up", "Up", show=False),
        Binding("escape,left", "menu_back", "Back", show=False),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._menu_stack = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield AccountsPanel(id="accounts-panel")
        yield ListView(id="menu")
        yield Footer()

    def on_mount(self) -> None:
        self._push_root_menu()
        self._on_snapshot(self.app.snapshot)
        self.watch(self.app, "snapshot", self._on_snapshot)

    def _on_snapshot(self, snapshot) -> None:
        if snapshot is None:
            return
        self.query_one("#accounts-panel", AccountsPanel).update_rows(snapshot)

    def _root_entries(self):
        return [
            ("switch", "Switch account"),
            ("watch", "Watch (live quota)"),
            ("add", "Add current agy login"),
            ("disable", "Disable an account"),
            ("enable", "Enable an account"),
            ("remove", "Remove an account"),
            ("refresh", "Refresh now"),
            ("quit", "Quit"),
        ]

    def _push_root_menu(self) -> None:
        self._render_menu(self._root_entries())

    def _render_menu(self, entries) -> None:
        menu = self.query_one("#menu", ListView)
        menu.clear()
        for action_id, label in entries:
            menu.append(MenuItem(action_id, label))

    def action_cursor_down(self) -> None:
        lv = self.query_one("#menu", ListView)
        if lv.index is not None and lv.children:
            lv.index = min(lv.index + 1, len(lv.children) - 1)

    def action_cursor_up(self) -> None:
        lv = self.query_one("#menu", ListView)
        if lv.index is not None and lv.children:
            lv.index = max(lv.index - 1, 0)

    def action_open_switch(self) -> None:
        self.app.push_screen(SwitchScreen())

    def action_open_add(self) -> None:
        self.app.run_worker(self._add_current_worker, thread=True, exit_on_error=False, name="add-current")

    def _add_current_worker(self) -> None:
        try:
            acc = actions.add_current_account()
            self.app.call_from_thread(self.app.notify, f"Added #{acc.get('slot')} ({acc.get('email')})")
        except Exception as e:
            self.app.call_from_thread(self.app.notify, str(e), severity="warning")
        self.app.call_from_thread(self.app.trigger_refresh, True)

    def action_menu_back(self) -> None:
        if self._menu_stack:
            self._render_menu(self._menu_stack.pop())
        else:
            self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, MenuItem):
            return
        self._dispatch(item.action_id)

    def _dispatch(self, action_id: str) -> None:
        rows = self.app.snapshot or []
        if action_id == "switch":
            self.action_open_switch()
        elif action_id == "watch":
            self.app.action_open_watch()
        elif action_id == "add":
            self.action_open_add()
        elif action_id == "refresh":
            self.app.trigger_refresh(True)
        elif action_id == "quit":
            self.app.exit()
        elif action_id == "disable":
            self._menu_stack.append(self._root_entries())
            self._render_menu([(f"disable:{r['slot']}", f"#{r['slot']} {r['email']}") for r in rows if not r.get("disabled")])
        elif action_id == "enable":
            self._menu_stack.append(self._root_entries())
            self._render_menu([(f"enable:{r['slot']}", f"#{r['slot']} {r['email']}") for r in rows if r.get("disabled")])
        elif action_id == "remove":
            self._menu_stack.append(self._root_entries())
            self._render_menu([(f"remove:{r['slot']}", f"#{r['slot']} {r['email']}") for r in rows])
        elif action_id.startswith("disable:"):
            self._do_toggle(action_id.split(":", 1)[1], True)
        elif action_id.startswith("enable:"):
            self._do_toggle(action_id.split(":", 1)[1], False)
        elif action_id.startswith("remove:"):
            self._do_remove(action_id.split(":", 1)[1])

    def _return_to_root(self) -> None:
        # Reset the stack, not just re-render — otherwise the frame pushed when
        # entering this submenu is left orphaned, and the next Escape press just
        # redraws the (already-showing) root menu instead of leaving the screen.
        self._menu_stack = []
        self._push_root_menu()

    def _do_toggle(self, slot: str, disabled: bool) -> None:
        # save_config() acquires a blocking file lock — run it off the UI thread,
        # same as action_open_add, so lock contention can't freeze the whole TUI.
        self.app.run_worker(partial(self._toggle_worker, slot, disabled), thread=True, exit_on_error=False, name="toggle-disabled")
        self._return_to_root()

    def _toggle_worker(self, slot: str, disabled: bool) -> None:
        try:
            actions.set_disabled(slot, disabled)
            self.app.call_from_thread(self.app.notify, f"Slot #{slot} {'disabled' if disabled else 'enabled'}.")
        except Exception as e:
            self.app.call_from_thread(self.app.notify, str(e), severity="warning")
        self.app.call_from_thread(self.app.trigger_refresh, True)

    def _do_remove(self, slot: str) -> None:
        self.app.run_worker(partial(self._remove_worker, slot), thread=True, exit_on_error=False, name="remove-account")
        self._return_to_root()

    def _remove_worker(self, slot: str) -> None:
        try:
            actions.remove_account(slot)
            self.app.call_from_thread(self.app.notify, f"Slot #{slot} removed.")
        except Exception as e:
            self.app.call_from_thread(self.app.notify, str(e), severity="warning")
        self.app.call_from_thread(self.app.trigger_refresh, True)


class AccountListScreen(Screen):
    """Shared base for SwitchScreen/WatchScreen: only rebuilds the list (which would
    lose cursor position) when the set of account slots actually changes; otherwise
    updates rows in place and flashes ones whose quota just refreshed."""

    BINDINGS = [
        Binding("j,down", "cursor_down", "Down", show=False),
        Binding("k,up", "cursor_up", "Up", show=False),
        ("escape,q", "back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._known_slots = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(id="accounts")
        yield Footer()

    def on_mount(self) -> None:
        self._rebuild(self.app.snapshot or [])
        self.watch(self.app, "snapshot", self._on_snapshot)

    def _on_snapshot(self, snapshot) -> None:
        if snapshot is None:
            return
        self._rebuild(snapshot)

    def _include(self, row: dict) -> bool:
        return True

    def _rebuild(self, rows) -> None:
        rows = [r for r in rows if self._include(r)]
        slots = {r.get("slot") for r in rows}
        listview = self.query_one("#accounts", ListView)

        if slots != self._known_slots:
            selected_slot = self._current_slot()
            listview.clear()
            for row in rows:
                listview.append(AccountItem(row))
            self._known_slots = slots
            if selected_slot is not None:
                for i, row in enumerate(rows):
                    if row.get("slot") == selected_slot:
                        listview.index = i
                        break
        else:
            for item in listview.children:
                if not isinstance(item, AccountItem):
                    continue
                new_row = next((r for r in rows if r.get("slot") == item.slot), None)
                if new_row is None:
                    continue
                old_fetched = (item.row.get("quota") or {}).get("fetched_at")
                new_fetched = (new_row.get("quota") or {}).get("fetched_at")
                item.row = new_row
                item.query_one(Label).update(mini_account_text(new_row))
                if new_fetched and new_fetched != old_fetched:
                    item.add_class("flash")
                    self.set_timer(FLASH_S, lambda it=item: it.remove_class("flash"))

    def _current_slot(self):
        listview = self.query_one("#accounts", ListView)
        if listview.index is None or not listview.children:
            return None
        return getattr(listview.children[listview.index], "slot", None)

    def action_cursor_down(self) -> None:
        lv = self.query_one("#accounts", ListView)
        if lv.index is not None and lv.children:
            lv.index = min(lv.index + 1, len(lv.children) - 1)

    def action_cursor_up(self) -> None:
        lv = self.query_one("#accounts", ListView)
        if lv.index is not None and lv.children:
            lv.index = max(lv.index - 1, 0)

    def action_back(self) -> None:
        self.app.pop_screen()


class SwitchScreen(AccountListScreen):
    BINDINGS = AccountListScreen.BINDINGS + [Binding("enter", "select", "Switch", priority=True)]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._switch_to(event.item)

    def action_select(self) -> None:
        listview = self.query_one("#accounts", ListView)
        if listview.index is not None and listview.children:
            self._switch_to(listview.children[listview.index])

    def _switch_to(self, item) -> None:
        if not isinstance(item, AccountItem):
            return
        try:
            acc = actions.switch_account(str(item.slot))
            self.app.notify(f"Switched to #{item.slot} ({item.row.get('email')}).")
            if acc.get("is_soon"):
                self.app.notify(f"Token expiring soon ({acc.get('expiry_rel')}).", severity="warning")
            self.app.trigger_refresh(True)
            self.app.pop_screen()
        except Exception as e:
            self.app.notify(str(e), severity="warning")
