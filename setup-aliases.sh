#!/bin/bash
# Setup opticode using shell aliases (safer than PATH manipulation)

echo "Add these to your ~/.zshrc or ~/.bashrc:"
echo ""
echo "# opticode aliases"
echo "alias codex='opticode run --tool codex'"
echo "alias claude='opticode run --tool claude'"
echo ""
echo "Then run: source ~/.zshrc (or ~/.bashrc)"
echo ""
echo "To remove the old PATH-based wrappers, check:"
echo "  echo \$PATH"
echo ""
echo "And remove the texen/wrappers directory from PATH if present."
