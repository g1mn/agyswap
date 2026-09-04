import unittest
import unittest.mock
import tempfile
import json
import time
import argparse
import io
import contextlib
from pathlib import Path

import agyswap
import modules.quota as quota


class AgyswapTestCase(unittest.TestCase):
    """Monkeypatches all storage paths to a tempdir — never touches the real
    ~/.agyswap or ~/.agy-swap directories."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        tmp_home = Path(self._tmpdir.name)

        self._orig = {name: getattr(agyswap, name) for name in
                      ("BASE_DIR", "CONFIG_FILE", "SLOTS_DIR", "BACKUP_DIR", "LOCK_FILE", "LEGACY_BASE_DIR")}
        self._orig_quota = {name: getattr(quota, name) for name in ("BASE_DIR", "QUOTA_CACHE_FILE")}

        agyswap.BASE_DIR = tmp_home / "agyswap-new"
        agyswap.CONFIG_FILE = agyswap.BASE_DIR / "config.json"
        agyswap.SLOTS_DIR = agyswap.BASE_DIR / "slots"
        agyswap.BACKUP_DIR = agyswap.BASE_DIR / "backup"
        agyswap.LOCK_FILE = agyswap.BASE_DIR / ".agyswap.lock"
        agyswap.LEGACY_BASE_DIR = tmp_home / "agy-swap-legacy"

        quota.BASE_DIR = agyswap.BASE_DIR
        quota.QUOTA_CACHE_FILE = agyswap.BASE_DIR / "quota_cache.json"

    def tearDown(self):
        for name, value in self._orig.items():
            setattr(agyswap, name, value)
        for name, value in self._orig_quota.items():
            setattr(quota, name, value)
        self._tmpdir.cleanup()


class TestNextEnabledAccount(AgyswapTestCase):
    def test_skips_disabled_and_wraps(self):
        accounts = [
            {"slot": 1, "disabled": False},
            {"slot": 2, "disabled": True},
            {"slot": 3, "disabled": False},
        ]
        self.assertEqual(agyswap._next_enabled_account(accounts, active_slot=1)["slot"], 3)
        self.assertEqual(agyswap._next_enabled_account(accounts, active_slot=3)["slot"], 1)

    def test_active_slot_disabled_falls_back_to_first_enabled(self):
        accounts = [{"slot": 1, "disabled": True}, {"slot": 2, "disabled": False}]
        self.assertEqual(agyswap._next_enabled_account(accounts, active_slot=1)["slot"], 2)

    def test_all_disabled_returns_none(self):
        self.assertIsNone(agyswap._next_enabled_account([{"slot": 1, "disabled": True}], active_slot=1))

    def test_no_active_slot_returns_first_by_slot_order(self):
        accounts = [{"slot": 5, "disabled": False}, {"slot": 2, "disabled": False}]
        self.assertEqual(agyswap._next_enabled_account(accounts, active_slot=None)["slot"], 2)


class TestMigrateLegacyDataDir(AgyswapTestCase):
    def test_moves_only_owned_files_leaves_siblings_tool_data_untouched(self):
        legacy = agyswap.LEGACY_BASE_DIR
        legacy.mkdir(parents=True)
        (legacy / "config.json").write_text(json.dumps({"active_slot": 1, "accounts": []}))
        (legacy / "slots").mkdir()
        (legacy / "slots" / "slot-1.json").write_text("{}")

        # Simulated files belonging to the unrelated pr656d/agy-swap tool sharing this dir.
        (legacy / "sequence.json").write_text("{}")
        (legacy / "credentials").mkdir()
        (legacy / "credentials" / "foo.enc").write_text("x")

        agyswap.migrate_legacy_data_dir()

        self.assertTrue(agyswap.CONFIG_FILE.exists())
        self.assertTrue((agyswap.SLOTS_DIR / "slot-1.json").exists())
        self.assertFalse((legacy / "config.json").exists())
        self.assertTrue((legacy / "sequence.json").exists())
        self.assertTrue((legacy / "credentials" / "foo.enc").exists())

    def test_idempotent_second_call_is_a_noop(self):
        legacy = agyswap.LEGACY_BASE_DIR
        legacy.mkdir(parents=True)
        (legacy / "config.json").write_text("{}")
        agyswap.migrate_legacy_data_dir()
        self.assertTrue(agyswap.CONFIG_FILE.exists())
        agyswap.migrate_legacy_data_dir()  # legacy config.json is gone now; must not raise
        self.assertTrue(agyswap.CONFIG_FILE.exists())

    def test_no_legacy_dir_is_a_noop(self):
        agyswap.migrate_legacy_data_dir()
        self.assertFalse(agyswap.CONFIG_FILE.exists())

    def test_interrupted_migration_recovers_on_next_call(self):
        """config.json moves LAST specifically so an interruption between moves
        (crash, disk full) is recoverable — simulate slots/backup already moved
        but config.json still in the legacy dir, and verify a second call finishes
        the job instead of getting permanently stuck."""
        legacy = agyswap.LEGACY_BASE_DIR
        legacy.mkdir(parents=True)
        (legacy / "config.json").write_text(json.dumps({"active_slot": 1, "accounts": [{"slot": 1}]}))
        (legacy / "slots").mkdir()
        (legacy / "slots" / "slot-1.json").write_text("{}")

        # Simulate: process died after moving slots/, before moving config.json.
        agyswap.BASE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        (legacy / "slots").rename(agyswap.SLOTS_DIR)

        self.assertFalse(agyswap.CONFIG_FILE.exists())
        agyswap.migrate_legacy_data_dir()

        self.assertTrue(agyswap.CONFIG_FILE.exists())
        self.assertTrue((agyswap.SLOTS_DIR / "slot-1.json").exists())
        # A once-loaded account's slot file must actually be reachable now.
        agyswap.StorageManager.load_slot(1)  # raises FileNotFoundError if still stranded


class TestQuotaCache(AgyswapTestCase):
    def test_fetch_all_merges_not_clobbers(self):
        quota._atomic_write_json(quota.QUOTA_CACHE_FILE, {
            "a@x.com": {"fetched_at": int(time.time()), "stale": False,
                        "models": {"gemini-pro": {"remaining_pct": 50.0, "used_pct": 50.0, "resets_at": ""}}},
        })

        def fake_fetch_raw(token):
            return {"buckets": [{"modelId": "gemini-pro", "remainingFraction": 0.9, "resetTime": "later"}]}

        orig = quota._fetch_raw
        quota._fetch_raw = fake_fetch_raw
        try:
            result = quota.fetch_all([("b@x.com", "tok-b")], force=True)
        finally:
            quota._fetch_raw = orig

        self.assertEqual(result["a@x.com"]["models"]["gemini-pro"]["remaining_pct"], 50.0)
        self.assertEqual(result["b@x.com"]["models"]["gemini-pro"]["remaining_pct"], 90.0)

    def test_transient_failure_preserves_last_known_good_as_stale(self):
        quota._atomic_write_json(quota.QUOTA_CACHE_FILE, {
            "c@x.com": {"fetched_at": int(time.time()) - 1000, "stale": False,
                        "models": {"gemini-pro": {"remaining_pct": 40.0, "used_pct": 60.0, "resets_at": "t"}}},
        })

        def fake_fetch_raw(token):
            raise quota.QuotaFetchError("network down", kind="transient")

        orig = quota._fetch_raw
        quota._fetch_raw = fake_fetch_raw
        try:
            result = quota.fetch_all([("c@x.com", "tok-c")], force=True)
        finally:
            quota._fetch_raw = orig

        self.assertTrue(result["c@x.com"]["stale"])
        self.assertEqual(result["c@x.com"]["models"]["gemini-pro"]["remaining_pct"], 40.0)

    def test_fresh_entry_skips_live_fetch_when_not_forced(self):
        quota._atomic_write_json(quota.QUOTA_CACHE_FILE, {
            "d@x.com": {"fetched_at": int(time.time()), "stale": False,
                        "models": {"gemini-pro": {"remaining_pct": 77.0, "used_pct": 23.0, "resets_at": ""}}},
        })

        calls = []
        orig = quota._fetch_raw
        quota._fetch_raw = lambda token: calls.append(token) or {"buckets": []}
        try:
            entry = quota.fetch_for_account("d@x.com", "tok-d", force=False)
        finally:
            quota._fetch_raw = orig

        self.assertEqual(calls, [])  # never hit the network — TTL gate short-circuited
        self.assertEqual(entry["models"]["gemini-pro"]["remaining_pct"], 77.0)

    def test_failure_with_no_prior_entry_degrades_instead_of_raising_and_sets_ttl(self):
        """A permanently-failing account (e.g. revoked token) must not retry on
        every single call — fetched_at has to advance even on failure."""
        def fake_fetch_raw(token):
            raise quota.QuotaFetchError("401", kind="auth")

        orig = quota._fetch_raw
        quota._fetch_raw = fake_fetch_raw
        try:
            entry = quota.fetch_for_account("e@x.com", "tok-e", force=False)
            self.assertTrue(entry["stale"])
            self.assertEqual(entry["models"], {})

            calls = []
            quota._fetch_raw = lambda token: calls.append(token)
            entry2 = quota.fetch_for_account("e@x.com", "tok-e", force=False)
            self.assertEqual(calls, [])  # within TTL of the failed attempt — no retry
            self.assertTrue(entry2["stale"])
        finally:
            quota._fetch_raw = orig

    def test_malformed_response_degrades_gracefully_instead_of_crashing(self):
        quota._fetch_raw_orig = quota._fetch_raw
        quota._fetch_raw = lambda token: {"buckets": [None]}  # triggers AttributeError in _map_buckets
        try:
            entry = quota.fetch_for_account("f@x.com", "tok-f", force=False)
        finally:
            quota._fetch_raw = quota._fetch_raw_orig
            del quota._fetch_raw_orig

        self.assertTrue(entry["stale"])
        self.assertIn("last_error", entry)


class TestAliasEnableDisable(AgyswapTestCase):
    def _seed(self, accounts):
        agyswap.StorageManager.save_config({"active_slot": accounts[0]["slot"], "accounts": accounts})

    def test_cmd_alias_set_and_unset_roundtrip(self):
        self._seed([{"slot": 1, "email": "a@x.com", "alias": "", "disabled": False}])

        agyswap.cmd_alias(argparse.Namespace(target="1", name="main", unset=False))
        self.assertEqual(agyswap.StorageManager.load_config()["accounts"][0]["alias"], "main")

        agyswap.cmd_alias(argparse.Namespace(target="1", name=None, unset=True))
        self.assertEqual(agyswap.StorageManager.load_config()["accounts"][0]["alias"], "")

    def test_cmd_alias_duplicate_raises(self):
        self._seed([
            {"slot": 1, "email": "a@x.com", "alias": "work", "disabled": False},
            {"slot": 2, "email": "b@x.com", "alias": "", "disabled": False},
        ])
        with self.assertRaises(SystemExit):
            agyswap.cmd_alias(argparse.Namespace(target="2", name="work", unset=False))

    def test_cmd_disable_and_enable(self):
        self._seed([{"slot": 1, "email": "a@x.com", "alias": "", "disabled": False}])

        agyswap.cmd_disable(argparse.Namespace(target="1"))
        self.assertTrue(agyswap.StorageManager.load_config()["accounts"][0]["disabled"])

        agyswap.cmd_enable(argparse.Namespace(target="1"))
        self.assertFalse(agyswap.StorageManager.load_config()["accounts"][0]["disabled"])

    def test_cmd_rename_rejects_empty_alias(self):
        self._seed([{"slot": 1, "email": "a@x.com", "alias": "main", "disabled": False}])
        with self.assertRaises(SystemExit):
            agyswap.cmd_rename(argparse.Namespace(target="1", new_alias=""))
        # Rejected — original alias must be untouched.
        self.assertEqual(agyswap.StorageManager.load_config()["accounts"][0]["alias"], "main")


class TestCmdQuota(AgyswapTestCase):
    def test_json_output_scoped_to_requested_target_not_whole_cache(self):
        agyswap.StorageManager.save_config({
            "active_slot": 1,
            "accounts": [
                {"slot": 1, "email": "work@x.com", "alias": "", "disabled": False},
                {"slot": 2, "email": "personal@x.com", "alias": "", "disabled": False},
            ],
        })
        # No slot files exist, so cmd_quota can't fetch — it falls back to
        # read_cache(), which is exactly the path that used to leak the whole file.
        quota._atomic_write_json(quota.QUOTA_CACHE_FILE, {
            "work@x.com": {"fetched_at": int(time.time()), "stale": False, "models": {}},
            "personal@x.com": {"fetched_at": int(time.time()), "stale": False, "models": {}},
        })

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            agyswap.cmd_quota(argparse.Namespace(target="1", refresh=False, json=True))
        output = json.loads(buf.getvalue())

        self.assertIn("work@x.com", output)
        self.assertNotIn("personal@x.com", output)


class TestCmdSwitch(AgyswapTestCase):
    """Tests for cmd_switch active_slot persistence and related side effects."""

    def _setup_two_slots(self):
        """Helper: create a config with two enabled slots and their slot files."""
        agyswap.StorageManager.init_storage()
        cfg = {
            "active_slot": 1,
            "accounts": [
                {"slot": 1, "email": "a@x.com", "alias": "a", "disabled": False,
                 "added_at": "2026-01-01T00:00:00+00:00", "last_used_at": "2026-01-01T00:00:00+00:00"},
                {"slot": 2, "email": "b@x.com", "alias": "b", "disabled": False,
                 "added_at": "2026-01-01T00:00:00+00:00", "last_used_at": "2026-01-01T00:00:00+00:00"},
            ]
        }
        agyswap.StorageManager.save_config(cfg)
        token = {"access_token": "tok", "expiry": "2099-12-31T23:59:59Z"}
        for s in (1, 2):
            agyswap.StorageManager.save_slot(s, {
                "slot": s, "email": cfg["accounts"][s - 1]["email"],
                "auth_method": "consumer", "token": token
            })
        return cfg

    @unittest.mock.patch.object(agyswap.KeychainManager, "set_payload")
    def test_switch_updates_active_slot(self, mock_kc):
        """After switching to slot 2, config.json active_slot must be 2."""
        self._setup_two_slots()
        args = argparse.Namespace(target="2", dry_run=False, force=False,
                                  resume=False, new_session=False,
                                  dangerously_skip_permissions=False)
        agyswap.cmd_switch(args)
        cfg = agyswap.StorageManager.load_config()
        self.assertEqual(cfg["active_slot"], 2)

    @unittest.mock.patch.object(agyswap.KeychainManager, "set_payload")
    def test_switch_updates_last_used_at(self, mock_kc):
        """After switching, last_used_at must be updated to a recent timestamp."""
        self._setup_two_slots()
        args = argparse.Namespace(target="2", dry_run=False, force=False,
                                  resume=False, new_session=False,
                                  dangerously_skip_permissions=False)
        agyswap.cmd_switch(args)
        cfg = agyswap.StorageManager.load_config()
        acc2 = next(a for a in cfg["accounts"] if a["slot"] == 2)
        self.assertNotEqual(acc2["last_used_at"], "2026-01-01T00:00:00+00:00")

    @unittest.mock.patch.object(agyswap.KeychainManager, "set_payload")
    def test_blind_rotation_after_switch(self, mock_kc):
        """Blind rotation after switching to 2 should pick slot 1 (wrap-around)."""
        self._setup_two_slots()
        # First switch to slot 2
        agyswap.cmd_switch(argparse.Namespace(
            target="2", dry_run=False, force=False,
            resume=False, new_session=False, dangerously_skip_permissions=False))
        # Now blind rotation (no target) should pick slot 1
        agyswap.cmd_switch(argparse.Namespace(
            target=None, dry_run=False, force=False,
            resume=False, new_session=False, dangerously_skip_permissions=False))
        cfg = agyswap.StorageManager.load_config()
        self.assertEqual(cfg["active_slot"], 1)

    @unittest.mock.patch.object(agyswap.KeychainManager, "set_payload")
    def test_switch_dry_run_no_side_effects(self, mock_kc):
        """--dry-run must not modify config or call KeychainManager."""
        self._setup_two_slots()
        args = argparse.Namespace(target="2", dry_run=True, force=False,
                                  resume=False, new_session=False,
                                  dangerously_skip_permissions=False)
        agyswap.cmd_switch(args)
        cfg = agyswap.StorageManager.load_config()
        self.assertEqual(cfg["active_slot"], 1)  # unchanged
        mock_kc.assert_not_called()

    def test_set_payload_no_argv_leak(self):
        """set_payload must not pass the raw password as a subprocess argument."""
        with unittest.mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = unittest.mock.Mock(returncode=0, stderr="")
            try:
                agyswap.KeychainManager.set_payload({"test": "data"})
            except Exception:
                pass  # May fail due to mock, but we only care about argv
            if mock_run.call_count >= 2:
                # Second call is add-generic-password
                add_call = mock_run.call_args_list[-1]
                cmd_args = add_call[0][0] if add_call[0] else add_call[1].get("args", [])
                # The raw password string must NOT appear in the command argv
                for arg in cmd_args:
                    self.assertFalse(
                        arg.startswith(agyswap.KEYRING_PREFIX),
                        f"Secret leaked in subprocess argv: {arg[:20]}..."
                    )
                # Verify password was passed via stdin (input= kwarg)
                input_val = add_call[1].get("input", "")
                self.assertTrue(
                    input_val.startswith(agyswap.KEYRING_PREFIX),
                    "Password must be passed via stdin input, not argv"
                )


class TestAgyGuard(AgyswapTestCase):
    """Tests for agyswap guard auto-rotating rate-limit protector."""

    def test_rate_limit_patterns_matching(self):
        """Validates that various Google/Gemini 429 quota exhaustion strings match."""
        import modules.guard as guard

        samples = [
            "Error: RPC failed with status RESOURCE_EXHAUSTED",
            "HTTP status: 429 Too Many Requests",
            "GoogleGenerativeAIError: Quota exceeded for model",
            "Error: Rate limit reached, try again in 5 minutes",
            "Resource has been exhausted (e.g. check quota)",
        ]
        for sample in samples:
            matched = any(p.search(sample) for p in guard.RATE_LIMIT_PATTERNS)
            self.assertTrue(matched, f"Pattern should match: {sample}")

    def test_inspect_log_tail_detects_quota_error(self):
        """inspect_log_tail_for_quota_error must detect error lines in recent logs."""
        import modules.guard as guard

        tmp_log = Path(self._tmpdir.name) / "test_cli.log"
        tmp_log.write_text("Normal line 1\nNormal line 2\nERROR: RESOURCE_EXHAUSTED: quota limit reached\n")

        # Inspect since time in past
        detected, snippet = guard.inspect_log_tail_for_quota_error(tmp_log, since_mtime=time.time() - 10)
        self.assertTrue(detected)
        self.assertIn("RESOURCE_EXHAUSTED", snippet)

    def test_inspect_log_tail_ignores_clean_log(self):
        """inspect_log_tail_for_quota_error returns False when no error present."""
        import modules.guard as guard

        tmp_log = Path(self._tmpdir.name) / "clean_cli.log"
        tmp_log.write_text("Normal session line 1\nNormal session line 2\n")

        detected, snippet = guard.inspect_log_tail_for_quota_error(tmp_log, since_mtime=time.time() - 10)
        self.assertFalse(detected)
        self.assertEqual(snippet, "")

    @unittest.mock.patch("shutil.which", return_value="/mock/bin/agy")
    @unittest.mock.patch("pathlib.Path.exists", return_value=True)
    def test_guard_normal_exit_terminates_loop(self, mock_exists, mock_which):
        """When agy exits with 0 and no quota error, guard terminates with exit code 0."""
        import modules.guard as guard

        agyswap.StorageManager.init_storage()
        cfg = {
            "active_slot": 1,
            "accounts": [
                {"slot": 1, "email": "a@x.com", "disabled": False},
            ]
        }
        agyswap.StorageManager.save_config(cfg)

        with unittest.mock.patch("subprocess.run") as mock_sub:
            mock_sub.return_value = unittest.mock.Mock(returncode=0)
            with unittest.mock.patch("time.time", side_effect=[100.0, 105.0]):  # session duration 5s
                with unittest.mock.patch("modules.guard.inspect_log_tail_for_quota_error", return_value=(False, "")):
                    g = guard.AgyGuard(resume=True, dangerously_skip_permissions=False)
                    code = g.run()
                    self.assertEqual(code, 0)
                    self.assertEqual(mock_sub.call_count, 1)


class TestStatelessMcpServer(AgyswapTestCase):
    """Tests for 2026 Stateless Model Context Protocol (MCP) server implementation."""

    def test_mcp_initialize_compatibility(self):
        """Optional initialize request returns protocol info with stateless capability."""
        from modules.mcp_server import dispatch_mcp_request, PROTOCOL_VERSION

        req = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "initialize",
            "params": {"protocolVersion": "2026-07-28"},
        }
        res = dispatch_mcp_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["id"], 10)
        self.assertEqual(res["result"]["protocolVersion"], PROTOCOL_VERSION)
        self.assertTrue(res["result"]["capabilities"]["stateless"])

    def test_mcp_stateless_tools_list_without_handshake(self):
        """tools/list must succeed without any prior initialize call (Stateless Spec)."""
        from modules.mcp_server import dispatch_mcp_request

        req = {"jsonrpc": "2.0", "id": 11, "method": "tools/list"}
        res = dispatch_mcp_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["id"], 11)
        tool_names = [t["name"] for t in res["result"]["tools"]]
        self.assertIn("agyswap_list_accounts", tool_names)
        self.assertIn("agyswap_get_quota", tool_names)
        self.assertIn("agyswap_switch_account", tool_names)
        self.assertIn("agyswap_rotate_token", tool_names)
        self.assertIn("agyswap_compact_context", tool_names)

    def test_mcp_stateless_tools_call_execution(self):
        """tools/call on agyswap_list_accounts executes and returns JSON content."""
        from modules.mcp_server import dispatch_mcp_request

        agyswap.StorageManager.init_storage()
        cfg = {
            "active_slot": 1,
            "accounts": [
                {"slot": 1, "email": "test@mcp.org", "disabled": False},
            ],
        }
        agyswap.StorageManager.save_config(cfg)

        req = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "agyswap_list_accounts", "arguments": {}},
        }
        res = dispatch_mcp_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["id"], 12)
        content_text = res["result"]["content"][0]["text"]
        payload = json.loads(content_text)
        self.assertEqual(payload["active_slot"], 1)
        self.assertEqual(payload["accounts"][0]["email"], "test@mcp.org")

    def test_mcp_unknown_tool_returns_error(self):
        """Calling nonexistent tool returns standard JSON-RPC -32601 code."""
        from modules.mcp_server import dispatch_mcp_request

        req = {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        }
        res = dispatch_mcp_request(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["error"]["code"], -32601)


class TestCmdPrompt(AgyswapTestCase):
    """Tests for agyswap prompt fast shell integration."""

    def test_prompt_default_and_plain_output(self):
        agyswap.StorageManager.init_storage()
        cfg = {
            "active_slot": 1,
            "accounts": [{"slot": 1, "email": "a@x.com", "alias": "work", "disabled": False}],
        }
        agyswap.StorageManager.save_config(cfg)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            agyswap.cmd_prompt(argparse.Namespace(plain=False, json=False))
        self.assertEqual(buf.getvalue().strip(), "[agy:work]")

        buf_plain = io.StringIO()
        with contextlib.redirect_stdout(buf_plain):
            agyswap.cmd_prompt(argparse.Namespace(plain=True, json=False))
        self.assertEqual(buf_plain.getvalue().strip(), "work")

    def test_prompt_json_output(self):
        agyswap.StorageManager.init_storage()
        cfg = {
            "active_slot": 1,
            "accounts": [{"slot": 1, "email": "a@x.com", "alias": "work", "disabled": False}],
        }
        agyswap.StorageManager.save_config(cfg)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            agyswap.cmd_prompt(argparse.Namespace(plain=False, json=True))
        data = json.loads(buf.getvalue())
        self.assertTrue(data["active"])
        self.assertEqual(data["name"], "work")
        self.assertEqual(data["slot"], 1)

    def test_prompt_no_active_slot(self):
        agyswap.StorageManager.init_storage()
        agyswap.StorageManager.save_config({"active_slot": None, "accounts": []})

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            agyswap.cmd_prompt(argparse.Namespace(plain=False, json=False))
        self.assertEqual(buf.getvalue().strip(), "")


if __name__ == "__main__":
    unittest.main()



