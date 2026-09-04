<p align="center">
  <a href="https://github.com/g1mn/agyswap">
    <img src="https://raw.githubusercontent.com/g1mn/agyswap/main/assets/banner.svg" alt="agyswap Banner" width="100%">
  </a>
</p>

<p align="center">
  <a href="https://github.com/g1mn/agyswap/actions/workflows/ci.yml"><img src="https://github.com/g1mn/agyswap/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/g1mn/agyswap/releases"><img src="https://img.shields.io/github/v/release/g1mn/agyswap?color=blue&label=release" alt="Release"></a>
  <a href="https://g1mn.github.io/agyswap/"><img src="https://img.shields.io/badge/Token_Savings-96.1%25-brightgreen.svg" alt="Token Savings: 96.1%"></a>
  <a href="https://g1mn.github.io/agyswap/"><img src="https://img.shields.io/badge/MCP-2026_Stateless-blue.svg" alt="MCP: 2026 Stateless"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="#-installation"><img src="https://img.shields.io/badge/Platform-macOS-lightgrey.svg" alt="Platform: macOS"></a>
</p>

<p align="center">
  <b>The Uninterrupted Multi-Account &amp; Intelligent Context Engine for Google Antigravity (<code>agy</code>) CLI</b><br>
  Instant switching in 0.1s · Zero-interruption 429 rate-limit guard · 96% context token compression · 2026 Stateless MCP server.
</p>

---

### 🎮 [👉 Launch Interactive Live Playground & Documentation](https://g1mn.github.io/agyswap/)
> Explore the **Live Rate-Limit Guard Simulator**, **Interactive Token ROI Calculator**, **9-Language AST Split Viewer**, and **Stateless MCP Sandbox** directly in your browser.

---

## ⚡ Quick Start (30 Seconds)

```bash
# 1. Register current logged-in account
agyswap add personal

# 2. Switch to account #2 and resume conversation immediately with full auto-approval
agyswap 2 -r -y

# 3. 🛡️ Never hit rate limits again: Launch agy under auto-rotating guard protection
agyswap guard -y --ctx

# 4. Interactive Live TUI Dashboard
agyswap tui
```

---

## ✨ Why agyswap?

| Feature | Without agyswap | With agyswap |
| :--- | :--- | :--- |
| **Account Switching** | Log out in browser, re-authenticate (~60s) | **`agyswap 2` (~0.1s instant switch)** |
| **Session Context** | Context lost on browser re-login | **`-r` keeps 100% conversation history (`agy -c`)** |
| **Rate Limits (429)** | Work stops; manual terminal intervention | **`agyswap guard` auto-rotates & resumes seamlessly** |
| **Token Consumption** | Full codebase loaded on resets (~50k tokens) | **`agyswap ctx` 96.1% AST compression (~1.9k tokens)** |
| **AI Agent Autonomy** | Agents cannot manage their own quotas | **2026 Stateless MCP Server (`agyswap mcp`)** |
| **Parallel Sessions** | Only one account system-wide | **Independent accounts per terminal window simultaneously** |

---

## 🚀 Installation

### Option 1: Homebrew (Recommended on macOS)
```bash
brew install g1mn/tap/agyswap
```

### Option 2: One-Line Curl Installer
```bash
curl -fsSL https://raw.githubusercontent.com/g1mn/agyswap/main/install.sh | bash
```

---

## 🤖 2026 Stateless MCP Server

Connect `agyswap` to **Antigravity**, **Cursor**, or **Claude Code** so your AI coding agents can check their own Gemini quotas and rotate credentials autonomously without human intervention:

```json
{
  "mcpServers": {
    "agyswap": {
      "command": "agyswap",
      "args": ["mcp"]
    }
  }
}
```
*Zero dependencies. Conforms to the latest 2026 Stateless MCP specification with zero mandatory handshakes.*

---

## 📖 Essential Commands

```bash
agyswap                     # List all registered accounts with token health & quota
agyswap 2 -r -y             # Switch to slot 2 + resume (agy -c) + auto-approve tools
agyswap guard -y --ctx      # 🛡️ Auto-rotate on 429 + 96% context compaction
agyswap rotate --all        # Refresh all OAuth tokens in background (no browser)
agyswap ctx bench           # Measure real-time codebase token footprint & savings
agyswap tui                 # Keyboard-driven terminal dashboard (rich/textual)
agyswap prompt              # Fast prompt string for Starship / zsh (`[agy:work 85%]`)
```

> 📚 For comprehensive documentation, architecture diagrams, storage specs, and security audits:  
> **👉 Visit the [Interactive Documentation & Architecture Dashboard](https://g1mn.github.io/agyswap/)**

---

## 📄 License

MIT License © 2026 [g1mn](https://github.com/g1mn)
