# Changelog

All notable changes to agyswap are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

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
