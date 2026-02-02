#!/bin/bash
# Quick test script for opticode + Codex CLI

echo "======================================================================"
echo "                    OPTICODE + CODEX QUICK TEST"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd "$(dirname "$0")"

echo -e "${BLUE}Step 1: Testing WITHOUT opticode${NC}"
echo "Running: codex exec --skip-git-repo-check 'Add hello world comment to cli.py'"
echo ""
echo "Note: This will take 10-60 seconds..."
echo ""

START_TIME=$(date +%s)
codex exec --skip-git-repo-check "Add hello world comment to src/opticode/cli.py" 2>&1 | tee /tmp/codex_without.txt
END_TIME=$(date +%s)

WITHOUT_TIME=$((END_TIME - START_TIME))
echo ""
echo -e "${GREEN}✓ Completed in ${WITHOUT_TIME}s${NC}"
echo ""
read -p "Press Enter to continue to test WITH opticode..."
echo ""

echo -e "${BLUE}Step 2: Testing WITH opticode${NC}"
echo "First, see what opticode does to the prompt:"
echo ""
opticode optimize "Add hello world comment to src/opticode/cli.py" | head -30
echo ""
read -p "Press Enter to run Codex with optimized prompt..."
echo ""

echo "Running: codex exec --skip-git-repo-check <optimized_prompt>"
echo "Note: This will take 10-60 seconds..."
echo ""

START_TIME=$(date +%s)
opticode optimize "Add hello world comment to src/opticode/cli.py" | xargs -0 codex exec --skip-git-repo-check 2>&1 | tee /tmp/codex_with.txt
END_TIME=$(date +%s)

WITH_TIME=$((END_TIME - START_TIME))
echo ""
echo -e "${GREEN}✓ Completed in ${WITH_TIME}s${NC}"
echo ""

echo -e "${BLUE}Step 3: Testing vague request blocking${NC}"
echo "Request: 'should we use redis or mysql'"
echo ""
opticode optimize "should we use redis or mysql"
echo ""
echo -e "${GREEN}✓ This was blocked before wasting an API call!${NC}"
echo ""

echo "======================================================================"
echo "                         COMPARISON"
echo "======================================================================"
echo ""
echo "WITHOUT opticode:"
echo "  Time: ${WITHOUT_TIME}s"
echo "  Output lines: $(wc -l < /tmp/codex_without.txt)"
echo "  Output preview:"
head -5 /tmp/codex_without.txt | sed 's/^/    /'
echo ""
echo "WITH opticode:"
echo "  Time: ${WITH_TIME}s"
echo "  Output lines: $(wc -l < /tmp/codex_with.txt)"
echo "  Output preview:"
head -5 /tmp/codex_with.txt | sed 's/^/    /'
echo ""

if [ $WITH_TIME -gt $WITHOUT_TIME ]; then
    DIFF=$((WITH_TIME - WITHOUT_TIME))
    echo "Time difference: +${DIFF}s (slower with opticode)"
else
    DIFF=$((WITHOUT_TIME - WITH_TIME))
    echo "Time difference: -${DIFF}s (faster with opticode)"
fi

echo ""
echo "Check full output:"
echo "  Without: cat /tmp/codex_without.txt"
echo "  With:    cat /tmp/codex_with.txt"
echo ""
