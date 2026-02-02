#!/bin/bash
# Setup opticode integrations with popular AI coding tools

set -e

OPTICODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPERS_DIR="$OPTICODE_DIR/wrappers"

echo "======================================================================"
echo "                    OPTICODE INTEGRATION SETUP"
echo "======================================================================"
echo ""

# Check shell
echo "1. Detecting shell..."
SHELL_NAME=$(basename "$SHELL")
echo "   Shell: $SHELL_NAME"

# Determine config file
case "$SHELL_NAME" in
    bash)
        CONFIG_FILE="$HOME/.bashrc"
        ;;
    zsh)
        CONFIG_FILE="$HOME/.zshrc"
        ;;
    fish)
        CONFIG_FILE="$HOME/.config/fish/config.fish"
        ;;
    *)
        echo "   Unknown shell. Please manually add to your shell config."
        CONFIG_FILE=""
        ;;
esac

# Setup method choice
echo ""
echo "2. Setting up opticode integration..."
echo ""
echo "   CHOOSE SETUP METHOD:"
echo ""
echo "   [1] Shell aliases (RECOMMENDED)"
echo "       - Aliases: codex, claude automatically use opticode"
echo "       - Safe: No PATH manipulation, can't break your tools"
echo ""
echo "   [2] PATH wrappers (ADVANCED)"
echo "       - Wrappers intercept codex/claude commands"
echo "       - Risky: Can break if not set up correctly"
echo ""
read -p "   Choose [1/2] (default: 1): " -n 1 -r
echo

SETUP_METHOD="${REPLY:-1}"

if [[ "$SETUP_METHOD" == "2" ]]; then
    echo ""
    echo "   ⚠️  WARNING: PATH wrappers can break your tools if not configured correctly."
    read -p "   Continue with PATH wrappers? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        SETUP_METHOD="1"
    fi
fi

if [[ "$SETUP_METHOD" == "2" ]]; then
    # PATH wrapper setup (old method)
    if [[ -n "$CONFIG_FILE" ]]; then
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d)"
        echo "   ✓ Backed up $CONFIG_FILE"
        
        if ! grep -q "opticode/wrappers" "$CONFIG_FILE" 2>/dev/null; then
            echo "" >> "$CONFIG_FILE"
            echo "# opticode transparent wrappers" >> "$CONFIG_FILE"
            echo "export PATH=\"$WRAPPERS_DIR:\$PATH\"" >> "$CONFIG_FILE"
            echo "   ✓ Added wrappers to PATH in $CONFIG_FILE"
        fi
        
        echo ""
        echo "   ⚠️  IMPORTANT: If codex/claude stop working, check:"
        echo "      which codex   # Should not point to $WRAPPERS_DIR"
        echo ""
        echo "   To use immediately: source $CONFIG_FILE"
    fi
else
    # Alias setup (recommended)
    echo ""
    echo "   Setting up shell aliases..."
    
    if [[ -n "$CONFIG_FILE" ]]; then
        # Backup config
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d)" 2>/dev/null || true
        
        # Add aliases
        if ! grep -q "opticode alias" "$CONFIG_FILE" 2>/dev/null; then
            echo "" >> "$CONFIG_FILE"
            echo "# opticode aliases" >> "$CONFIG_FILE"
            echo "alias codex='opticode run --tool codex'" >> "$CONFIG_FILE"
            echo "alias claude='opticode run --tool claude'" >> "$CONFIG_FILE"
            echo "alias opt='opticode optimize'" >> "$CONFIG_FILE"
            echo "   ✓ Added aliases to $CONFIG_FILE"
        else
            echo "   ✓ Aliases already present"
        fi
        
        echo ""
        echo "   To use immediately: source $CONFIG_FILE"
        echo ""
        echo "   Usage after setup:"
        echo "     codex 'your request'   # Automatically optimized"
        echo "     claude                 # Runs through opticode"
        echo "     opt 'your request'     # Just optimize, don't run"
    fi
fi

# Create convenience aliases file (either way)
ALIAS_FILE="$HOME/.opticode_aliases"
cat > "$ALIAS_FILE" << 'EOF'
# opticode aliases (source this file or add to shell config)

# Main aliases - optimize and run
alias codex='opticode run --tool codex'
alias claude='opticode run --tool claude'

# Optimize-only (don't run through tool)
alias opt='opticode optimize'

# Quick status check
alias opt-status='opticode status'

# Optimize and copy to clipboard (macOS)
alias opt-copy='opticode optimize | pbcopy'

# Optimize and save to file
alias opt-save='opticode optimize > /tmp/opticode_prompt.txt && echo "Saved to /tmp/opticode_prompt.txt"'
EOF
echo ""
echo "   ✓ Created aliases file: $ALIAS_FILE"

# Check for tools
echo ""
echo "4. Checking for AI tools..."

TOOLS_FOUND=()

if command -v codex &> /dev/null; then
    echo "   ✓ Codex CLI found"
    TOOLS_FOUND+=("codex")
else
    echo "   ✗ Codex CLI not found (npm install -g @openai/codex)"
fi

if command -v claude &> /dev/null; then
    echo "   ✓ Claude Code found"
    TOOLS_FOUND+=("claude")
else
    echo "   ✗ Claude Code not found (npm install -g @anthropic-ai/claude-code)"
fi

# Cursor check
cursor_paths=(
    "/Applications/Cursor.app/Contents/MacOS/Cursor"
    "/usr/bin/cursor"
    "$HOME/.local/bin/cursor"
)
CURSOR_FOUND=false
for path in "${cursor_paths[@]}"; do
    if [[ -f "$path" ]]; then
        echo "   ✓ Cursor found at $path"
        CURSOR_FOUND=true
        break
    fi
done
if [[ "$CURSOR_FOUND" == false ]]; then
    echo "   ✗ Cursor not found (download from cursor.com)"
fi

# Configure opticode
echo ""
echo "5. Configuring opticode..."

mkdir -p .opticode
if [[ ! -f ".opticode/config.json" ]]; then
    cat > .opticode/config.json << EOF
{
  "codex_cmd": "codex exec --skip-git-repo-check {prompt}",
  "claude_cmd": "claude"
}
EOF
    echo "   ✓ Created .opticode/config.json"
else
    echo "   ✓ Config already exists"
fi

# Summary
echo ""
echo "======================================================================"
echo "                    SETUP COMPLETE"
echo "======================================================================"
echo ""

if [[ ${#TOOLS_FOUND[@]} -gt 0 ]]; then
    echo "Tools with opticode integration:"
    for tool in "${TOOLS_FOUND[@]}"; do
        echo "  • $tool"
    done
    echo ""
    echo "Usage:"
    echo "  $ codex 'Add error handling'       # Automatically optimized"
    echo "  $ claude 'Refactor the cache'       # Automatically optimized"
    echo ""
else
    echo "No AI CLI tools detected. Install one:"
    echo "  npm install -g @openai/codex        # For Codex CLI"
    echo "  npm install -g @anthropic-ai/claude-code  # For Claude Code"
    echo ""
fi

echo "Other useful commands:"
echo "  opt 'Add error handling'            # Just optimize, don't run"
echo "  opt-status                          # Check opticode status"
echo "  opt-copy                            # Optimize & copy to clipboard"
echo ""
echo "Manual integration (for Cursor, etc.):"
echo "  opticode optimize 'your request' | pbcopy  # Copy, then paste"
echo ""
echo "See INTEGRATION_GUIDE.md for more options."
echo ""
