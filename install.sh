#!/usr/bin/env bash
# ==============================================================================
# agyswap Installer
# Antigravity (agy) CLI Multi-Account Switcher & Session Manager
# ==============================================================================
set -euo pipefail

INSTALL_DIR="${AGYSWAP_INSTALL_DIR:-$HOME/.local/bin}"
REPO="g1mn/agyswap"
RAW_URL="https://raw.githubusercontent.com/${REPO}/main/bin/agyswap"

mkdir -p "$INSTALL_DIR"

echo "📦 Installing agyswap..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/bin/agyswap" ]; then
    echo "  • Installing from local repository: $SCRIPT_DIR/bin/agyswap"
    ln -sf "$SCRIPT_DIR/bin/agyswap" "$INSTALL_DIR/agyswap"
    chmod +x "$SCRIPT_DIR/bin/agyswap"
elif [ -f "$SCRIPT_DIR/agyswap" ]; then
    echo "  • Installing from local file: $SCRIPT_DIR/agyswap"
    ln -sf "$SCRIPT_DIR/agyswap" "$INSTALL_DIR/agyswap"
    chmod +x "$SCRIPT_DIR/agyswap"
else
    echo "  • Fetching latest release from GitHub..."
    curl -fsSL "$RAW_URL" -o "$INSTALL_DIR/agyswap"
    chmod +x "$INSTALL_DIR/agyswap"
fi

echo "  ✓ Executable installed to: $INSTALL_DIR/agyswap"

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  Note: $INSTALL_DIR is not in your PATH."
    echo "   Add it to your shell configuration:"
    echo ""
    if [ -n "${ZSH_VERSION:-}" ] || [ -f "$HOME/.zshrc" ]; then
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
    else
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
    fi
    echo ""
fi

echo ""
echo "🎉 agyswap installed successfully!"
if command -v agyswap &>/dev/null; then
    agyswap --version
elif [ -x "$INSTALL_DIR/agyswap" ]; then
    "$INSTALL_DIR/agyswap" --version
fi

echo ""
echo "💡 Quick Start:"
echo "  1. Log in via agy:   agy"
echo "  2. Register slot:    agyswap add personal"
echo "  3. Check status:     agyswap list"
echo "  4. Switch account:   agyswap switch <slot|alias>"
echo "  5. Security audit:   agyswap audit"
echo ""
echo "  Shell completion (optional):"
echo "    echo 'eval \"\$(agyswap completion zsh)\"' >> ~/.zshrc"
