# Changelog

All notable changes to agyswap are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [0.5.0] — 2026-08-29

### Added
- `agyswap alias`: standalone alias management (`agyswap alias`, `agyswap alias <slot> <name>`, `agyswap alias <slot> --unset`)
- `agyswap enable` / `agyswap disable`: hold a slot out of blind rotation (`agyswap switch` with no target) without removing its credentials; explicit `agyswap switch <slot>` still works on a disabled slot
- `agyswap quota`: per-account, per-model Gemini API quota tracking (`--refresh`, `--json`), TTL-cached (45s) and merge-safe — never clobbers other accounts' cached data on write
- `agyswap tui` / `agyswap watch`: live, keyboard-driven terminal dashboard with real-time per-model quota bars (`rich` + `textual`)

### Changed
- Data directory moved from `~/.agy-swap/` to `~/.agyswap/` — automatically migrated in place on first run; the old path collided with an unrelated third-party tool of a similar name
- `requires-python` raised to `>=3.9` (matches `rich`/`textual`'s actual floor; CI already only tested 3.9+)
- `rich` and `textual` are now required dependencies (used only by `tui`/`watch`) — `agyswap` is no longer zero-dependency
- Fixed a packaging bug where the wheel only ever included `agyswap.py` and silently dropped `modules/` (meaning `agyswap ctx ...` was likely already broken for `pip`/`pipx` installs); `[tool.hatch.build.targets.wheel]` now explicitly includes `modules/**/*.py` and `modules/**/*.tcss`
- Fixed the same `modules/` gap for Homebrew (`Formula/agyswap.rb` now installs `modules/` alongside the binary) and the curl installer (`install.sh` now fetches `modules/` from the repo tarball); `agyswap.py` now resolves its own real install location (following symlinks) to find `modules/` regardless of install method
- `docs/index.html` (GitHub Pages): updated for the above — new Command Reference cards for `alias`/`enable`/`disable`/`quota`/`tui`/`watch`, corrected "zero dependencies" claims, updated storage layout + a migration note, `rich`/`textual` install caveats on the Homebrew/curl tabs, 3 new FAQ entries, and fixed a pre-existing duplicate section-letter bug (two sections were both labeled "G")
- `docs/index.html`'s Interactive Architecture Topology (section A): added a "Live TUI Dashboard" node and a new "Live TUI Dashboard Path" preset, added a 5th Engine Core bullet for the quota cache + TUI safety layer, and extended the Google endpoints node to show the quota API — verified visually in a real browser (no overlap/clipping, presets highlight correctly)
- `assets/architecture.svg` / `docs/assets/architecture.svg` (README's Architecture Overview image, two files kept byte-identical per `RELEASING.md`): same Live TUI Dashboard node + quota cache bullet + quota API line as above, fixed a stray `~/.agy-swap/` (legacy path) it still showed, fixed the "Zero Dependencies" footer, and fixed its header badge which was still stuck at "V0.1.0" despite the Engine Core box already saying v0.4.0 — verified visually
- `assets/banner.svg` / `docs/assets/banner.svg`: fixed the "DEPENDENCIES: 0 External Deps" feature pill to say "rich+textual (TUI)" — verified visually. `logo.svg`/`logo-icon.svg` checked, no stale claims found

### Fixed (cross-review pass)
- `migrate_legacy_data_dir()`: `config.json` now moves last, not first — an interrupted migration (crash, disk full) used to permanently strand `slots/`/`backup/` in the legacy directory since the "already migrated" guard only checked for the new `config.json`
- `agyswap quota --json` (with a target/slot given) no longer dumps every cached account — it's now scoped to the requested account(s), matching the human-readable output
- `modules/quota.py`'s `quota_cache.json` read-modify-write is now protected by a file lock — concurrent writers (the TUI's background poller and a CLI `agyswap quota` call) could previously clobber each other's just-written updates
- A permanently-failing account (e.g. revoked token) is now retried at most once per TTL window instead of on every single call/poll tick
- A malformed/unexpected API response shape no longer crashes `agyswap quota` or the TUI's refresh worker with a raw traceback — it degrades to stale cached data like any other transient failure
- `modules/tui/actions.py`'s mutation functions now wrap every `StorageManager` call and re-raise as `ActionError`, so a corrupted-config or disk-full error can no longer escape past the TUI's error-handling layer and crash the whole dashboard
- The TUI no longer runs blocking, lock-acquiring account mutations (disable/enable/remove) directly on the UI thread — they now run in a background worker like switch/add already did
- Switching accounts from the TUI now shows the same "token expiring soon" warning the CLI already shows
- Fixed a `_menu_stack` leak in the TUI dashboard that made "Back" require an extra Escape press after every completed disable/enable/remove action
- Fixed a race where a forced TUI refresh (after an account action) could run concurrently with an in-flight periodic refresh instead of replacing it
- `agyswap.py`'s bundled-package bootstrap now requires a marker file (`modules/quota.py`) instead of a bare directory check, so it can't be fooled into loading an unrelated `modules/` folder
- `install.sh`'s `modules/` fetch now stages the new copy before removing the old one, so a failed download can't leave an existing install with no `modules/` at all
- `agyswap rename` now rejects an empty alias (previously silently cleared it, inconsistent with `agyswap alias`'s explicit `--unset`)
- `StorageManager.load_config()`'s corrupted-config recovery no longer calls `print()` directly — it could garble the TUI's rendered screen since this runs on background worker threads too

---

## [0.4.0] — 2026-08-28

### Added
- `agyswap ctx` subsystem: AST-based Repo Map (`ctx map`), lightweight working-state snapshots (`ctx state`), and real-time compression benchmarking (`ctx bench [--json|-md]`)
- `agyswap ctx bench --golden`: multi-language oracle regression suite (Python, TypeScript/TSX, Go, Rust, Java, C, C++, Shell) enforcing 100% symbol recall on every release
- Java, C, C++, and header-file (`.h`) support in the AST Repo Mapper (regex extractors with control-flow keyword guards)
- Interactive Context Playground & ROI Calculator on the GitHub Pages docs, with a 9-language full-source-vs-repo-map split viewer

### Fixed
- `ctx bench --json` no longer leaks the full untrimmed repo map into its output
- `TokenBudgeter.trim_to_budget` no longer overshoots the requested token budget when appending its truncation banner
- AST signature extraction now includes positional-only, keyword-only, `*args`, and `**kwargs` parameters (previously silently dropped)
- Decorator extraction is no longer limited to a hardcoded allowlist — `@x.setter`, `@app.route(...)`, and other real-world decorators are now preserved
- Tuple-unpacking constant assignments (e.g. `A, B = 1, 2`) are now extracted
- `ctx bench --golden` now honors `--dir` / `--budget` instead of silently ignoring them
- `.agents/memory/*` files and directories are now created with secure permissions atomically, removing a brief world-readable TOCTOU window
- Git status parsing now correctly handles quoted/spaced filenames and renames (`git status --porcelain -z`)
- `--budget` rejects zero/negative values with a clear usage error instead of silently producing broken output
- Golden benchmark symbol-recall check no longer reports false positives when a symbol is renamed to something that merely starts with the old name
- ASCII benchmark report box borders now render aligned regardless of emoji width or digit count

---

## [0.3.0] — 2026-08-23

### Added
- `agyswap switch -r` / `--resume`: Switch account + immediately resume last agy session (`agy -c`) with 100% conversation history preserved
- `agyswap switch -n` / `--new`: Switch account + launch a fresh agy session
- `agyswap switch -y` / `--dangerously-skip-permissions`: Pass `--dangerously-skip-permissions` to agy when combined with `-r` or `-n`, enabling fully automated no-prompt workflows (e.g. `agyswap 2 -r -y`)
- `agyswap rotate --all` / `-a`: Background OAuth token rotation for all slots simultaneously — no browser required
- Keychain ACL reset on every switch: eliminates macOS password/certificate popup dialogs permanently
- `RELEASING.md`: permanent release checklist to ensure all 9 files are updated on every release

### Fixed
- Keychain access prompt (macOS security password dialog) appearing on agyswap execution
- Multiple `(active)` markers shown in list view when config slot and Keychain token fingerprints diverged

---

## [0.2.0] — 2026-08-23

### Added
- Zero-interaction OAuth token rotation (`agyswap rotate --all`)
- Official Homebrew Tap distribution (`brew install g1mn/tap/agyswap`)
- Interactive local dashboard (`agyswap viz --open`)
- Visual identity system (SVG logo, banner, architecture diagram)
- GitHub Actions CI/CD with automated release and Telegram notification workflows

---

## [0.1.0] — 2026-08-22

### Added
- Initial release: multi-account Keychain switching for `agy` (Antigravity) CLI
- Slot management: `add`, `switch`, `remove`, `rename`, `list`
- Token health dashboard: `health`, `audit`, `status`, `whoami`
- Backup & restore: `export`, `import`
- Shell completions: `bash`, `zsh`, `fish`
- Interactive architecture dashboard: `agyswap viz`
- Zero external dependencies (Python 3 standard library only)
