# Fix for Broken codex/claude Commands

## Problem
Your shell is running the opticode wrapper directly instead of using aliases.
When you type `codex` or `claude`, it's calling opticode with no arguments, 
which returns "What is the specific task you want performed?"

## Root Cause
- You're using **bash** (not zsh)
- The PATH still includes the broken wrappers
- Aliases were added to `.zshrc` but you're in bash

## Fix (Run these commands)

```bash
# 1. Clear the broken PATH entry
export PATH="/opt/anaconda3/bin:/opt/anaconda3/condabin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/Users/usman/.local/bin"

# 2. Set up aliases in your CURRENT shell
alias codex='opticode run --tool codex'
alias claude='opticode run --tool claude'

# 3. Test - should work now
codex --version
claude --version
```

## Permanent Fix (for new shells)

Since your `.bash_profile` is owned by root, add aliases to `.bashrc` instead:

```bash
# Add to ~/.bashrc
cat >> ~/.bashrc << 'EOF'

# opticode aliases
alias codex='opticode run --tool codex'
alias claude='opticode run --tool claude'
EOF

# Then source it
source ~/.bashrc
```

## Alternative: Just use explicit opticode commands

Instead of fixing aliases, just use:
```bash
# Instead of: codex "add login"
opticode run --tool codex "add login"

# Instead of: claude "refactor auth"
opticode run --tool claude "refactor auth"
```

## Verify it works

```bash
# Should show: codex-cli X.XX.X
codex --version

# Should show: X.X.X (Claude Code)
claude --version

# Should optimize and show structured prompt (not run codex)
opticode optimize "add dashboard"
```
