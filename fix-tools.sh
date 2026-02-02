#!/bin/bash
# Fix broken codex/claude after wrapper installation

echo "=== Restoring codex and claude ==="
echo ""

# Find where tools are actually installed
echo "1. Finding real tool locations..."

# Claude
REAL_CLAUDE=""
for path in "$HOME/.local/share/claude/versions/"*; do
    if [[ -x "$path" ]]; then
        REAL_CLAUDE="$path"
        echo "   Found claude at: $REAL_CLAUDE"
        break
    fi
done

# Codex via npm
REAL_CODEX=""
NPM_PREFIX=$(npm config get prefix 2>/dev/null)
if [[ -n "$NPM_PREFIX" ]] && [[ -x "$NPM_PREFIX/bin/codex" ]]; then
    REAL_CODEX="$NPM_PREFIX/bin/codex"
    echo "   Found codex at: $REAL_CODEX"
fi

echo ""
echo "2. Checking ~/.local/bin for wrappers..."

if [[ -f "$HOME/.local/bin/claude" ]]; then
    if head -1 "$HOME/.local/bin/claude" | grep -q "bin/bash"; then
        echo "   ⚠️  Found wrapper at ~/.local/bin/claude (needs fixing)"
        
        if [[ -n "$REAL_CLAUDE" ]]; then
            echo "   → Backing up wrapper to ~/.local/bin/claude.wrapper.backup"
            mv "$HOME/.local/bin/claude" "$HOME/.local/bin/claude.wrapper.backup"
            
            echo "   → Creating symlink to real claude"
            ln -s "$REAL_CLAUDE" "$HOME/.local/bin/claude"
            echo "   ✓ Fixed claude"
        fi
    else
        echo "   ✓ ~/.local/bin/claude is already the real binary"
    fi
fi

if [[ -f "$HOME/.local/bin/codex" ]]; then
    if head -1 "$HOME/.local/bin/codex" | grep -q "bin/bash"; then
        echo "   ⚠️  Found wrapper at ~/.local/bin/codex (needs fixing)"
        
        if [[ -n "$REAL_CODEX" ]]; then
            echo "   → Backing up wrapper to ~/.local/bin/codex.wrapper.backup"
            mv "$HOME/.local/bin/codex" "$HOME/.local/bin/codex.wrapper.backup"
            
            echo "   → Creating symlink to real codex"
            ln -s "$REAL_CODEX" "$HOME/.local/bin/codex"
            echo "   ✓ Fixed codex"
        fi
    else
        echo "   ✓ ~/.local/bin/codex is already the real binary"
    fi
fi

echo ""
echo "3. Setting up aliases instead of wrappers..."

SHELL_CONFIG=""
if [[ -f "$HOME/.zshrc" ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    SHELL_CONFIG="$HOME/.bashrc"
fi

if [[ -n "$SHELL_CONFIG" ]]; then
    if ! grep -q "opticode alias" "$SHELL_CONFIG" 2>/dev/null; then
        echo "" >> "$SHELL_CONFIG"
        echo "# opticode aliases (safe alternative to PATH wrappers)" >> "$SHELL_CONFIG"
        echo "alias codex='opticode run --tool codex'" >> "$SHELL_CONFIG"
        echo "alias claude='opticode run --tool claude'" >> "$SHELL_CONFIG"
        echo "   ✓ Added aliases to $SHELL_CONFIG"
    else
        echo "   ✓ Aliases already present"
    fi
    echo ""
    echo "   Run: source $SHELL_CONFIG"
fi

echo ""
echo "=== Done ==="
echo ""
echo "Test your tools:"
echo "  claude --version    # Should work now"
echo "  codex --help        # Should work now"
echo ""
echo "Usage with opticode (via aliases):"
echo "  codex 'add login'   # Goes through opticode"
echo "  claude              # Goes through opticode"
