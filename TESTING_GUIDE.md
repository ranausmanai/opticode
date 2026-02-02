# Testing opticode with Codex CLI - Quick Start

## Step 1: Setup (One-time)

```bash
# 1. Go to the opticode directory
cd /Users/usman/Documents/Vibed/texen

# 2. Install opticode
pip install -e .

# 3. Verify installation
opticode --help
```

## Step 2: Test WITHOUT opticode (Baseline)

```bash
# Simple test - see what Codex does with raw request
codex exec --skip-git-repo-check "Add a hello world comment to src/opticode/cli.py"

# Time it
 time codex exec --skip-git-repo-check "Add error handling to cache.py"
```

**What to observe:**
- How long does it take?
- What format is the output? (text or git diff?)
- Does it ask clarifying questions?
- Does it guess the right files?

## Step 3: Test WITH opticode

### Option A: See the optimized prompt first

```bash
# Just optimize, don't send to Codex
opticode optimize "Add error handling to cache.py"

# You'll see the structured prompt with:
# - TASK section
# - CONTEXT (repo info, file snippets)
# - DO/DONT constraints
# - OUTPUT format
```

### Option B: Run through opticode

```bash
# Single command - optimize then run
codex exec --skip-git-repo-check "$(opticode optimize 'Add error handling to cache.py')"

# Or step by step:
OPTIMIZED=$(opticode optimize "Add error handling to cache.py")
codex exec --skip-git-repo-check "$OPTIMIZED"
```

### Option C: Use the wrapper (cleanest)

```bash
# Setup wrapper
./setup-integrations.sh
source ~/.bashrc

# Now just use 'codex' normally - it auto-optimizes
codex "Add error handling to cache.py"
```

## Step 4: Compare Test Scenarios

### Test 1: Simple Clear Request

```bash
# WITHOUT
time codex exec --skip-git-repo-check "Add fibonacci function to src/opticode/utils.py"

# WITH
time codex exec --skip-git-repo-check "$(opticode optimize 'Add fibonacci function to src/opticode/utils.py')"
```

**Compare:** Time, output format, specificity

---

### Test 2: Vague Request

```bash
# WITHOUT - see what happens
codex exec --skip-git-repo-check "Improve the code"

# WITH - should be blocked
opticode optimize "Improve the code"
```

**Expected with opticode:** Clarification question instead of API call

---

### Test 3: Comparison Request

```bash
# WITHOUT - likely confused response
codex exec --skip-git-repo-check "should we use redis or mysql"

# WITH - blocked with guidance
opticode optimize "should we use redis or mysql"
```

**Expected with opticode:** "This looks like a comparison..."

---

### Test 4: Complex Multi-file Request

```bash
# WITHOUT - may guess wrong files or timeout
time codex exec --skip-git-repo-check "Update error handling in executor to match cache.py pattern"

# WITH - has context of both files
time codex exec --skip-git-repo-check "$(opticode optimize 'Update error handling in executor to match cache.py pattern')"
```

**Expected with opticode:** Includes snippets from both files

---

### Test 5: Request with Filler Words

```bash
# WITHOUT
codex exec --skip-git-repo-check "umm maybe fix the bug or something"

# WITH - should clean up
opticode optimize "umm maybe fix the bug or something"
```

**Expected with opticode:** Filler words removed, clearer prompt

## Step 5: What to Measure

| Metric | How to measure |
|--------|----------------|
| **Time** | `time codex exec ...` |
| **Output format** | Text vs git diff |
| **Clarifications needed** | Did Codex ask "which file?" |
| **Success** | Did it complete or timeout/error? |
| **Precision** | Exact changes vs vague description |

## Step 6: Quick Commands Reference

```bash
# Check opticode status
opticode status

# Just optimize (preview)
opticode optimize "your request"

# Optimize and run
opticode run --tool codex "your request"

# Optimize and copy (for Cursor)
opticode optimize "your request" | pbcopy

# See what context opticode adds
opticode optimize --quality "your request"
```

## Example Session

```bash
$ cd /Users/usman/Documents/Vibed/texen

$ # Test 1: WITHOUT opticode
$ time codex exec --skip-git-repo-check "Add comment to cli.py"
[wait...]
[see output]

$ # Test 2: WITH opticode  
$ time codex exec --skip-git-repo-check "$(opticode optimize 'Add comment to cli.py')"
[wait...]
[see output - should have more context]

$ # Test 3: Vague request
$ opticode optimize "should we use redis or mysql"
This looks like a comparison. Specify: (1) 'Implement X' to build one, or (2) ask for analysis only.
[blocked before API call!]
```

## Troubleshooting

**"codex: command not found"**
```bash
# Make sure codex is installed
npm install -g @openai/codex
```

**"Not inside a trusted directory"**
```bash
# Always use --skip-git-repo-check
codex exec --skip-git-repo-check "your prompt"
```

**opticode optimize shows nothing**
```bash
# Check you're in the right directory
cd /Users/usman/Documents/Vibed/texen
opticode status
```

## What You Should See

### Without opticode:
- Shorter prompts (~10-50 tokens)
- May ask clarifying questions
- Text descriptions instead of diffs
- May guess wrong files

### With opticode:
- Longer prompts (~300-1500 tokens with context)
- Vague requests blocked instantly
- Git diff format
- Relevant file context included
- DO/DONT constraints

## Share Your Results

After testing, compare:

```
Scenario: [what you tested]
Without opticode: [time, quality, issues]
With opticode: [time, quality, improvements]
Verdict: [which worked better]
```
