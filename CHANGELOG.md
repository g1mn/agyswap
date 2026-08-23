# Changelog

All notable changes to agyswap are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

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
