# 🔄 agyswap

**Fast Multi-Account Switcher & Session Manager for Google Antigravity (`agy`) CLI**  
Manage and swap multiple Google Antigravity profiles on macOS Keychain with 0.1s switching, native OS credential security, and POSIX file isolation.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: macOS](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)]()
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)]()
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-0-brightgreen.svg)]()

---

## 🏛️ Architecture Overview

`agyswap` acts as a zero-overhead local credential coordinator between your shell, macOS Keychain, and isolated local storage:

<p align="center">
  <img src="assets/architecture.svg" alt="agyswap Architecture Topology" width="100%">
</p>

### 🌐 Interactive Architecture Dashboard
For a live, interactive visualization of account slots, switching sequences, and storage layouts:
- **1-Click CLI Open**: Run `agyswap viz --open` to view your local status in your default browser.
- **Local File**: Open [`docs/index.html`](docs/index.html) (`open docs/index.html`).
- **Live Demo**: Hosted on GitHub Pages at [https://g1mn.github.io/agyswap](https://g1mn.github.io/agyswap).

---

## ✨ Key Features

- ⚡ **Instant Switching**: Switch active credentials in ~0.1s (`agyswap 2` or `agyswap switch work`).
- 🔐 **Native OS Security (CWE-214 Mitigation)**: Direct binding to macOS `Security.framework` C API prevents OAuth secrets from appearing in process arguments (`argv` / `ps aux`).
- 🔒 **Atomic Concurrency & Strict Permissions**: Protected by `fcntl.flock` exclusive process locks, umask-safe creation (`0600`), and owner-only directories (`0700`).
- 🚨 **Expired Token Guard**: Prevents accidental switches to expired tokens unless explicitly forced with `--force`.
- ⚠️ **30-Minute Expiry Warnings**: Proactively highlights expiring credentials with `⚠️ Soon`.
- 🔍 **`health` Dashboard**: Instant summary of token validities, relative expiration times, and slot mappings.
- 🛡️ **`audit` Command**: Verifies and auto-corrects filesystem permissions across all credential stores.
- 🔄 **`rotate` Token Refresh**: Initiates OAuth refresh token renewal for expired profiles.
- 🏷️ **Account Aliases**: Assign meaningful aliases (`main`, `work`, `dev`) for fast switching.
- 📦 **Backup & Migration (`export`/`import`)**: Migrate slot configurations across machines (live secrets excluded).
- 🎯 **`--dry-run` Previews**: Non-destructive preview mode for `switch`, `remove`, and `sync`.
- 🔔 **Active Session Detection**: Scans and warns about running `agy` sessions and their working directories.
- ⌨️ **Shell Auto-Completion**: Tab completion scripts for `bash`, `zsh`, and `fish`.
- 📦 **Zero External Dependencies**: Powered entirely by the Python 3 standard library.

---

## 🚀 Quick Installation

### Option 1: One-Line Installer
```bash
curl -fsSL https://raw.githubusercontent.com/g1mn/agyswap/main/install.sh | bash
```

### Option 2: Clone and Link
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
agyswap 2                  # Quick switch to slot #2
agyswap switch work        # Switch by alias
agyswap switch user@gmail  # Switch by email
agyswap switch 1 --force   # Force switch with expired token
agyswap switch 2 --dry-run # Preview switch without applying
```

### 4. Inspect Active Status (`status` / `whoami`)
```bash
agyswap status   # Show active slot and Keychain token info
agyswap whoami   # Query Google UserInfo API in real time
```

### 5. Token Health Dashboard (`health`)
```bash
agyswap health
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

  ✓ ~/.agy-swap       : Permission 0700 (Secure)
  ✓ ~/.agy-swap/slots : Permission 0700 (Secure)
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

---

## 🔒 Security Model

| Security Layer | Implementation | Threat Mitigated |
| :--- | :--- | :--- |
| **Keychain Binding** | macOS `Security.framework` Native C API (`ctypes`) | Process argument sniffing (`ps aux`, CWE-214) |
| **Storage Isolation** | Files `0600`, Directories `0700` (`opener=secure_opener`) | Cross-user / local process snooping & Umask race conditions |
| **Concurrency Control** | `fcntl.flock` exclusive file locking | Lost updates during simultaneous terminal operations |
| **Data Integrity** | Atomic replacement (`tmp -> replace`) + `backup/` history | File corruption on crash or abrupt power cut |
| **Web Dashboard** | `safe_json_for_script` Unicode escaping | Stored XSS inside HTML `<script>` tags |

---

## 📂 Storage Layout

```text
~/.agy-swap/                     # Mode 0700 (Owner rwx only)
├── config.json                  # Mode 0600 (Metadata & active slot mapping)
├── .agyswap.lock                # Mode 0600 (flock concurrency barrier)
├── slots/                       # Mode 0700 (Directory)
│   ├── slot-1.json              # Mode 0600 (Token credential payload)
│   └── slot-2.json              # Mode 0600
└── backup/                      # Mode 0700 (Directory)
    └── config-YYYYMMDD.json     # Mode 0600 (Rolling automated backups)
```

---

## ⚠️ Disclaimer

`agyswap` is an independent open-source developer tool and is **not** affiliated with, endorsed by, sponsored by, or supported by Google LLC. "Antigravity", "Gemini", and "Google" are trademarks or registered trademarks of Google LLC. This utility is intended strictly for managing multiple legitimately owned developer profiles.

---

## 📄 License

MIT License © 2026 [g1mn](https://github.com/g1mn)
