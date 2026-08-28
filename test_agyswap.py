import unittest
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


if __name__ == "__main__":
    unittest.main()
