<p align="center">
  <a href="https://github.com/g1mn/agyswap">
    <img src="https://raw.githubusercontent.com/g1mn/agyswap/main/assets/banner.svg" alt="agyswap Banner" width="100%">
  </a>
</p>

<p align="center">
  <a href="https://github.com/g1mn/agyswap/actions/workflows/ci.yml"><img src="https://github.com/g1mn/agyswap/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/g1mn/agyswap/releases"><img src="https://img.shields.io/github/v/release/g1mn/agyswap?color=blue&label=release" alt="Release"></a>
  <a href="https://g1mn.github.io/agyswap/"><img src="https://img.shields.io/badge/Token_Savings-94.2%25-brightgreen.svg" alt="Token Savings: 94.2%"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="#-requirements"><img src="https://img.shields.io/badge/Platform-macOS-lightgrey.svg" alt="Platform: macOS"></a>
  <a href="#-installation"><img src="https://img.shields.io/badge/Python-3.9+-green.svg" alt="Python: 3.9+"></a>
  <a href="#-key-features"><img src="https://img.shields.io/badge/Dependencies-rich%20%2B%20textual-brightgreen.svg" alt="Dependencies: rich + textual"></a>
</p>

<p align="center">
  <b>Seamless Multi-Account &amp; Session Manager for Google Antigravity (<code>agy</code>) CLI</b><br>
  Run different accounts per terminal window simultaneously. Switch, rotate tokens, and resume sessions in one command — no browser, no popups, no lost context.
</p>

---

## 🏛️ Architecture Overview

`agyswap` acts as a zero-overhead local credential coordinator between your shell, macOS Keychain, and isolated local storage:

<p align="center">
  <img src="assets/architecture.svg" alt="agyswap Architecture Topology" width="100%">
</p>

### 🌐 Interactive Architecture Dashboard & Token Playground
For a live, interactive visualization of account slots, switching sequences, and a **real-time token compression playground**:
- **1-Click CLI Open**: Run `agyswap viz --open` to view your local account status in your default browser (saved in isolated `~/.agyswap/dashboard.html` with Mode `0600`, completely git-clean).
- **Live TUI Dashboard**: Run `agyswap tui` for a keyboard-driven terminal dashboard with live per-account Gemini quota bars, or `agyswap watch` to jump straight into the live monitor.
- **Online Demo & Token Playground**: Hosted on GitHub Pages at [https://g1mn.github.io/agyswap](https://g1mn.github.io/agyswap) (Includes Interactive Token ROI Calculator & a 9-language AST Split Viewer — Python, TypeScript, Go, Rust, Java, C, C++, Header, Shell).

---

## ✨ Key Features

- ⚡ **Instant Switching**: Switch active credentials in ~0.1s (`agyswap 2` or `agyswap switch work`).
- 🪟 **Per-Session Account Isolation**: Existing `agy` sessions keep their own account in memory; only new sessions inherit the switched profile — enabling true parallel multi-account workflows.
- 🚀 **One-Command Session Resume (`-r`)**: `agyswap 2 -r` switches account and immediately relaunches `agy -c` preserving 100% conversation history and context.
- ⚡ **Zero-Interaction Token Rotation**: `agyswap rotate --all` refreshes all OAuth tokens in the background — no browser required.
- 🔐 **Native OS Security (CWE-214 Mitigation)**: Direct binding to macOS `Security.framework` C API prevents OAuth secrets from appearing in process arguments (`argv` / `ps aux`).
- 🔒 **Atomic Concurrency & Strict Permissions**: Protected by `fcntl.flock` exclusive process locks, umask-safe creation (`0600`), and owner-only directories (`0700`).
- 🚨 **Expired Token Guard**: Prevents accidental switches to expired tokens unless explicitly forced with `--force`.
- ⚠️ **30-Minute Expiry Warnings**: Proactively highlights expiring credentials with `⚠️ Soon`.
- 🔍 **`health` Dashboard**: Instant summary of token validities, relative expiration times, and slot mappings.
- 🛡️ **`audit` Command**: Verifies and auto-corrects filesystem permissions across all credential stores.
- 🧠 **Context & AST Repo-Map (`ctx`)**: **94.2% Token Compression (~32k tokens saved/session)** via pure AST skeletons and lightweight state persistence.
- 📊 **Real-time Token Benchmarking (`ctx bench`)**: Built-in visual terminal cards, Markdown tables (`-md`), and JSON metrics for tracking token efficiency.
- 🏆 **Golden Quality Benchmark (`ctx bench --golden`)**: Multi-language oracle regression suite (Python, TypeScript/TSX, Go, Rust, Java, C, C++, Shell) — enforces 100% symbol-recall on every release.
- 🏷️ **Account Aliases**: Assign meaningful aliases (`main`, `work`, `dev`) via `agyswap add`/`rename`, or manage them directly with the standalone `agyswap alias` command.
- 🔀 **Enable/Disable Slots**: `agyswap disable <slot>` holds an account out of blind rotation (`agyswap switch` with no target) without removing its credentials — `agyswap switch <slot>` still works explicitly.
- 📊 **Gemini API Quota Tracking (`quota`)**: Per-account, per-model usage and reset times, TTL-cached and merge-safe (`agyswap quota`, `--refresh`, `--json`).
- 📦 **Backup & Migration (`export`/`import`)**: Migrate slot configurations across machines (live secrets excluded).
- 🎯 **`--dry-run` Previews**: Non-destructive preview mode for `switch`, `remove`, and `sync`.
- 🔔 **Active Session Detection**: Scans and warns about running `agy` sessions and their working directories.
- ⌨️ **Shell Auto-Completion**: Tab completion scripts for `bash`, `zsh`, and `fish`.
- 📦 **Minimal Dependencies**: Just `rich` + `textual`, used solely for the optional `agyswap tui`/`watch` live dashboard — everything else is standard library.

---

## 🧠 Intelligent Context Optimization & Token Benchmarks

`agyswap` includes a built-in AST code mapping and context management engine (`agyswap ctx`) designed to drastically reduce token waste and prevent context bloat in agentic coding workflows.

### 📊 Real-Time Benchmark (`agyswap ctx bench`)

```text
┌─────────────────────────────────────────────────────────────┐
│ 📊 agyswap Context Compression Benchmark                    │
├─────────────────────────────────────────────────────────────┤
│  Indexed Files      : 20                                    │
│  Raw Codebase Lines : 3,101 lines (123,082 chars)           │
│  Raw Token Footprint: ~34,189 tokens                        │
├─────────────────────────────────────────────────────────────┤
│  Repo-Map Lines     : 135 lines                             │
│  Repo-Map Tokens    : ~1,995 / 2,000 tokens                 │
│  Saved Tokens / Run : ~32,194 tokens                        │
├─────────────────────────────────────────────────────────────┤
│  Compression Rate   : [██████████████████░░]  94.2%         │
└─────────────────────────────────────────────────────────────┘
```

| Scenario | Naive Exploration | `agyswap ctx` (AST Map + Firewall) | Net Savings |
| :--- | :---: | :---: | :---: |
| **Codebase Discovery** | Full files read (`~34.2k tokens`) | `REPO_MAP.md` single load (`~2.0k tokens`) | **🔥 94.2% Saved** |
| **Session Reset Recovery** | Re-read raw files (`~34.2k tokens`) | `STATE.md` snapshot load (`< 300 tokens`) | **⚡ 99.6% Saved** |
| **10 Iteration Sessions** | ~342,000 tokens ($1.03+) | ~20,000 tokens ($0.06) | **17x Cost & Rate-Limit Savings** |

### 🏆 Golden Quality Benchmark (`agyswap ctx bench --golden`)

An oracle regression suite bundled in `tests/fixtures/golden_repo/` — a fixed, multi-language fixture set with a `metadata.json` checklist of expected symbols. Every release must extract **100% of them** to pass, guarding against silent AST/regex regressions across languages:

```text
┌─────────────────────────────────────────────────────────────┐
│ 🏆 agyswap Golden Quality & Context Benchmark Monitor       │
├─────────────────────────────────────────────────────────────┤
│  Standard Fixtures  : 11 files (323 lines)                  │
│  Raw Code Footprint : ~2,136 tokens                         │
│  Repo-Map Size      : ~704 tokens                           │
├─────────────────────────────────────────────────────────────┤
│  Token Compression  :  67.0% 🟢                             │
│  Symbol Recall      : 100.0% (36/36 symbols) 🟢             │
│  Information Density:  51.1 symbols / 1k Tokens 🟢          │
│  AST Parsing Latency:  1.90 ms ⚡                           │
└─────────────────────────────────────────────────────────────┘
```

Covers **10 file extensions across 8 languages** — Python, TypeScript (+ TSX), Go, Rust, Java, C, C++, and Shell — using native `ast` parsing for Python and hardened regex extractors (with control-flow/keyword guards) for the rest.

### 🚀 Context Management Workflow

```bash
# 1. Measure real-time token compression
agyswap ctx bench              # Visual ASCII report
agyswap ctx bench -md          # Markdown table format (for PRs / docs)
agyswap ctx bench --json       # JSON format for CI/CD pipelines
agyswap ctx bench --golden     # Multi-language oracle regression (100% recall gate)

# 2. Inspect compact AST skeleton of the codebase
agyswap ctx map --budget 2000

# 3. Snapshot working state (branch, staged/modified/untracked files, diff stat)
agyswap ctx state

# 4. Synchronize Repo-Map & Working State before resetting an agy chat
agyswap ctx clean
/clear                         # Run in agy: resume instantly with zero context loss!
```

---

## 🔄 How agyswap Differs from cswap

If you've used `cswap` for Claude Code, `agyswap` works differently due to how `agy` manages OAuth tokens — and this is actually a **feature**, not a limitation:

| | cswap (Claude Code) | agyswap (Antigravity) |
|:---|:---|:---|
| **Auth model** | Stateless (reads file on each request) | Stateful (token loaded into process memory at launch) |
| **Switch scope** | All sessions switch immediately | **Existing sessions keep their account; only new sessions use the switched profile** ✨ |
| **Parallel accounts** | One account at a time | **Run different accounts per terminal window simultaneously** ✨ |
| **Context on switch** | Session continues | Use `-r` to resume with 100% conversation history preserved |
| **Token refresh** | N/A | `rotate --all` → background OAuth refresh, no browser needed |

> 💡 **Pro tip**: Because each `agy` session independently holds its token in process memory, you can have Terminal A running `work@company.com` and Terminal B running `personal@gmail.com` **at the same time**, completely independently.

---

## 💡 Parallel Account Workflow

```bash
# Terminal A — work project
agyswap switch work    # switch Keychain to work@company.com
agy                    # → starts as work@company.com

# Terminal B — simultaneously, independent account
agyswap 1 -n           # switch Keychain to personal@gmail.com + auto-launch fresh agy session
                       # Terminal A is unaffected — still running as work@company.com ✨
```

---

## 🚀 Installation

### Option 1: Homebrew (Recommended on macOS)
```bash
brew install g1mn/tap/agyswap
# or
brew tap g1mn/tap && brew install agyswap
```
*Shell completions for `zsh`, `bash`, and `fish` are automatically configured by Homebrew.*

### Option 2: One-Line Curl Installer
```bash
curl -fsSL https://raw.githubusercontent.com/g1mn/agyswap/main/install.sh | bash
```

### Option 3: Pip / Pipx (from source)
```bash
git clone https://github.com/g1mn/agyswap.git
cd agyswap
pip install .
# or
pipx install .
```
*Not published on PyPI — the unhyphenated name collides with an unrelated existing `agy-swap` project.*

### Option 4: Clone and Install
```bash
git clone https://github.com/g1mn/agyswap.git
cd agyswap
./install.sh
```

### Shell Auto-Completion (Optional)
```bash
# zsh (~/.zshrc)
echo 'eval "$(agyswap completion zsh)"' >> ~/.zshrc && source ~/.zshrc

# bash (~/.bashrc)
echo 'eval "$(agyswap completion bash)"' >> ~/.bashrc && source ~/.bashrc

# fish
agyswap completion fish > ~/.config/fish/completions/agyswap.fish
```

---

## 📖 Command Reference

### 1. Register Accounts
Log in via `agy` in your terminal, then register the active profile:
```bash
agy                   # Log in with first Google account in browser
agyswap add personal  # Save as slot #1 with alias 'personal'

agy                   # Log in with second Google account
agyswap add work      # Save as slot #2 with alias 'work'
```

### 2. List Profiles (`list` / default)
```bash
agyswap
# or
agyswap list
```
```text
Accounts:
  1: personal@example.com [personal] (active)
     ├ Token:  Valid   expires 15:30   in 5h 45m
     ├ Method: consumer
     └ Status: Active · just now · synced just now

  2: work@company.com [work]
     ├ Token:  Valid   expires 18:00   in 8h 15m
     ├ Method: consumer
     └ Status: Ready · 1h ago · synced 1h ago

Running instances:
  ● CLI   ~/projects/backend  (1 session)
```

### 3. Switch Profile (`switch` / slot shortcut)
```bash
agyswap 2                  # Quick switch (next agy launch uses slot #2)
agyswap 2 -r               # Switch + immediately resume last session (agy -c)
agyswap 2 -n               # Switch + launch a fresh agy session
agyswap 2 -r -y            # Switch + resume + auto-approve all tool permissions
agyswap 2 -n -y            # Switch + new session + auto-approve all tool permissions
agyswap switch work        # Switch by alias
agyswap switch user@gmail  # Switch by email
agyswap switch 1 --force   # Force switch with expired token
agyswap switch 2 --dry-run # Preview switch without applying
agyswap switch work --resume --dangerously-skip-permissions  # Long form
```

> **`-y` / `--dangerously-skip-permissions`**: Passes `--dangerously-skip-permissions` to `agy` when combined with `-r` or `-n`. Enables fully automated no-prompt workflows where `agy` auto-approves all tool permission requests.

### 4. Inspect Active Status (`status` / `whoami`)
```bash
agyswap status   # Show active slot and Keychain token info
agyswap whoami   # Query Google UserInfo API in real time
```

### 5. Token Health & Rotation (`health` / `rotate`)
```bash
agyswap health             # Token expiry dashboard for all slots
agyswap rotate --all       # Refresh all OAuth tokens (no browser, ~1s)
agyswap rotate 2           # Refresh specific slot
```
```text
🔍 agyswap health check

  ✅ Valid    #1  [personal] personal@example.com   ◀ active
             expires 15:30  (in 5h 45m)

  ❌ Expired  #2  [work]     work@company.com
             expired 2h ago
    → Run 'agyswap rotate 2' or re-login with agy
```

### 6. Security Audit (`audit`)
```bash
agyswap audit
```
```text
🛡️  agyswap Security Audit

  ✓ ~/.agyswap        : Permission 0700 (Secure)
  ✓ ~/.agyswap/slots  : Permission 0700 (Secure)
  ✓ config.json       : Permission 0600 (Secure)
  ✓ macOS Keychain Interface : Connected (Native C API)

🎉 Security Audit Passed: All credential stores are isolated.
```

### 7. Backup & Migration (`export` / `import`)
```bash
# Export metadata (secrets excluded)
agyswap export ~/Desktop/agyswap-backup.json

# Restore on a new machine
agyswap import ~/Desktop/agyswap-backup.json
# Then log into each account once via 'agy' and run 'agyswap sync'
```

### 8. Aliases & Rotation Control (`alias` / `enable` / `disable`)
```bash
agyswap alias 2 work        # Set alias 'work' on slot #2
agyswap alias 2 --unset     # Remove the alias
agyswap alias               # List all aliased slots

agyswap disable 2           # Hold slot #2 out of blind rotation (credentials kept)
agyswap switch              # Rotates to the next *enabled* slot, skipping disabled ones
agyswap switch 2            # Explicit switch still works even if slot #2 is disabled
agyswap enable 2            # Re-include it in rotation
```

### 9. Gemini Quota (`quota`)
```bash
agyswap quota                # Per-model quota for all enabled accounts (TTL-cached, ~45s)
agyswap quota work --refresh # Force a live re-fetch for one account, bypassing the cache
agyswap quota --json         # Machine-readable output
```

### 10. Live Dashboard (`tui` / `watch`)
```bash
agyswap tui     # Full-screen dashboard: account list, live quota bars, switch/add/remove
agyswap watch   # Jump straight into the live quota-watch view
```
Keys: `s` switch · `w` watch · `j`/`k` move · `q` quit.

---

## 🔒 Security Model

| Security Layer | Implementation | Threat Mitigated |
| :--- | :--- | :--- |
| **Keychain Binding** | macOS `Security.framework` Native C API (`ctypes`) | Process argument sniffing (`ps aux`, CWE-214) |
| **Keychain ACL Reset** | Delete + re-create with `-A`/`-T` flags on every switch | macOS `securityd` password/certificate popup dialogs |
| **Storage Isolation** | Files `0600`, Directories `0700` (`opener=secure_opener`) | Cross-user / local process snooping & Umask race conditions |
| **Concurrency Control** | `fcntl.flock` exclusive file locking | Lost updates during simultaneous terminal operations |
| **Data Integrity** | Atomic replacement (`tmp -> replace`) + `backup/` history | File corruption on crash or abrupt power cut |
| **Web Dashboard** | `safe_json_for_script` Unicode escaping | Stored XSS inside HTML `<script>` tags |

---

## 📂 Storage Layout

```text
~/.agyswap/                      # Mode 0700 (Owner rwx only)
├── config.json                  # Mode 0600 (Metadata & active slot mapping)
├── .agyswap.lock                # Mode 0600 (flock concurrency barrier)
├── quota_cache.json             # Mode 0600 (TTL-cached Gemini quota, merge-safe)
├── dashboard.html                # Mode 0600 (generated by 'agyswap viz')
├── slots/                       # Mode 0700 (Directory)
│   ├── slot-1.json              # Mode 0600 (Token credential payload)
│   └── slot-2.json              # Mode 0600
└── backup/                      # Mode 0700 (Directory)
    └── config-YYYYMMDD.json     # Mode 0600 (Rolling automated backups)
```

> **Migrating from an older install?** `agyswap` used to store its data at `~/.agy-swap/` (note the hyphen) — a path that happens to collide with an unrelated, similarly-named third-party tool. From v0.5.0 onward, `agyswap` automatically moves just its own files (`config.json`, `slots/`, `backup/`, `dashboard.html`) to `~/.agyswap/` the first time you run any command; anything else left in the old directory is never touched.

---

## ⚠️ Disclaimer

`agyswap` is an independent open-source developer tool and is **not** affiliated with, endorsed by, sponsored by, or supported by Google LLC. "Antigravity", "Gemini", and "Google" are trademarks or registered trademarks of Google LLC. This utility is intended strictly for managing multiple legitimately owned developer profiles.

## ⭐ Support & Community

If `agyswap` saves you time and makes your Antigravity CLI workflow smoother, please consider giving it a **Star (⭐)** on GitHub! It helps more developers discover the project and accelerates promotion to Homebrew core.

- 🐛 **Found a bug?** [Open an issue](https://github.com/g1mn/agyswap/issues)
- 💡 **Have a feature request?** [Submit a PR or Feature Request](https://github.com/g1mn/agyswap/issues/new)
- 📢 **Share with peers:** Share `agyswap` with fellow developers using Antigravity!

---

## 📄 License

MIT License © 2026 [g1mn](https://github.com/g1mn)
