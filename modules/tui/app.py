"""agyswap.modules.tui.app — AgySwapTuiApp: polling/threading orchestration.

Quota fetches are blocking urllib calls, so the refresh tick runs in a real OS
thread (not asyncio) and marshals the result back to the UI thread via
call_from_thread. A single reactive `snapshot` field fans out to every mounted
screen/widget via `self.watch(app, "snapshot", callback)`.
"""
from __future__ import annotations

from textual.app import App
from textual.reactive import reactive
from textual.worker import WorkerState

from .dashboard import DashboardScreen
from .theme import AGYSWAP_DARK
from .watch import WatchScreen

POLL_INTERVAL_S = 3.0


class AgySwapTuiApp(App):
    TITLE = "agyswap"
    CSS_PATH = "tui.tcss"
    ENABLE_COMMAND_PALETTE = False

    snapshot: reactive = reactive(None)

    def __init__(self, start_watch: bool = False) -> None:
        super().__init__()
        self._start_watch = start_watch
        self._refreshing = False

    def on_mount(self) -> None:
        self.register_theme(AGYSWAP_DARK)
        self.theme = "agyswap-dark"
        self.push_screen(DashboardScreen())
        if self._start_watch:
            self.push_screen(WatchScreen())
        self.set_interval(POLL_INTERVAL_S, self._tick)
        self._tick()

    def _tick(self) -> None:
        self.trigger_refresh()

    def trigger_refresh(self, force: bool = False) -> None:
        if self._refreshing and not force:
            return
        self._refreshing = True
        # exclusive=True cancels any already-running "refresh" worker instead of
        # letting force=True spawn a second, fully concurrent one that could race
        # to apply a stale snapshot after the newer one already landed.
        self.run_worker(self._refresh_blocking, thread=True, group="refresh", exclusive=True, exit_on_error=False, name="snapshot-refresh")

    def action_open_watch(self) -> None:
        self.push_screen(WatchScreen())

    def action_refresh_full(self) -> None:
        self.trigger_refresh(True)

    def _refresh_blocking(self) -> None:
        # No blanket try/except here: an unexpected exception should propagate so
        # the Worker enters WorkerState.ERROR, which on_worker_state_changed below
        # already handles (resets _refreshing and notifies the user) — swallowing
        # it silently would hide real bugs and leave the dashboard stuck stale
        # with zero indication anything went wrong.
        from agyswap import StorageManager
        from modules.quota import fetch_all

        from .data import build_snapshot

        accounts = StorageManager.load_config().get("accounts", [])
        accounts_with_tokens = []
        for acc in accounts:
            if acc.get("disabled"):
                continue
            try:
                token = StorageManager.load_slot(acc.get("slot")).get("token", {}).get("access_token", "")
                if token:
                    accounts_with_tokens.append((acc.get("email"), token))
            except Exception:
                continue
        if accounts_with_tokens:
            fetch_all(accounts_with_tokens)
        snap = build_snapshot()
        self.call_from_thread(self._apply_snapshot, snap)

    def _apply_snapshot(self, snap) -> None:
        self.snapshot = snap
        self._refresh_done()

    def _refresh_done(self) -> None:
        self._refreshing = False

    def on_worker_state_changed(self, event) -> None:
        if getattr(event.worker, "name", "") == "snapshot-refresh" and event.state == WorkerState.ERROR:
            self._refreshing = False
            self.notify("Quota refresh failed — will retry.", severity="warning")


def run_tui(start_watch: bool = False) -> None:
    AgySwapTuiApp(start_watch=start_watch).run()
