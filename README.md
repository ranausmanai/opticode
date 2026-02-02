# opticode

opticode makes AI coding assistants (Claude Code, Codex CLI) more productive by detecting vague requests, adding relevant context, and enforcing structured output formats.

> **Note:** opticode is a **productivity** tool, not a cost-saver. It adds ~$4/month in token costs but saves ~6.7 hours of developer time worth $667/month through better first-try success rates (60% → 95%).

## Who is this for?

- **CLI-first developers** using Claude Code, Codex CLI, or similar tools
- **Teams** wanting consistent, reviewable AI outputs
- **Power users** making 20+ AI requests per day
- Anyone **frustrated with clarification round-trips** and vague AI responses

## What it does

```
Your vague request → opticode analyzes → Structured prompt → Better AI output
```

**Without opticode:**
```
You: "Improve the code"
AI: "What should I improve?"
You: "Error handling"
AI: [wrong file]
You: "No, I meant cache.py"
AI: [finally correct]
→ 45 seconds, 2 round trips, frustration
```

**With opticode:**
```
You: "Improve the code"
opticode: "This is vague. What specific change?"
You: "Add error handling to cache.py"
opticode: [adds context, constraints, format]
AI: [correct output first try]
→ 15 seconds, 1 round trip, happiness
```

## Quick Start

### Install

```bash
# Recommended
pipx install .

# Or local install
pip install -e .
```

### Set up transparent integration

```bash
# Makes opticode invisible - just use codex/claude normally
./setup-integrations.sh
source ~/.bashrc  # or ~/.zshrc
```

### Use

```bash
# These automatically go through opticode
codex "Add error handling to cache.py"
claude "Refactor the CLI module"
```

## Claude Code Plugin (✅ WORKING)

### Installation

```bash
# Inside Claude Code:
/plugin marketplace add /path/to/opticode
/plugin install opticode@opticode-marketplace
```

Or from GitHub (when published):
```bash
/plugin marketplace add your-github-org/opticode
/plugin install opticode@opticode-marketplace
```

Restart Claude Code after installing.

### What the Plugin Does

Automatically optimizes EVERY prompt you send to Claude:

```
> add dashboard
→ [opticode rewrites]: "TASK: Create React dashboard in src/components/Dashboard.tsx using recharts..."
→ [Claude receives structured prompt with context]

> fix the bug
→ [opticode blocks]: "Provide the specific file and error type."
→ [No tokens wasted on vague request]

> should we use redis or postgres  
→ [opticode blocks]: "This looks like a comparison. Specify: (1) 'Implement X'..."
→ [Forces you to pick one first]
```

### Plugin Commands

```bash
# Check plugin status
/plugin list

# Disable temporarily
/plugin disable opticode

# Re-enable
/plugin enable opticode

# Uninstall
/plugin uninstall opticode
```

### Alternative: CLI Alias

If you prefer not to use the plugin:

```bash
# Add to ~/.zshrc or ~/.bashrc
alias claude='opticode run --tool claude'

# Use normally
claude "add dashboard"  # Auto-optimized
```

## How It Works

```
User request
    |
    v
opticode analyze (local, 0.1ms)
    |
    +--> Detect vague/comparison/question requests → Block with guidance
    +--> Add repo context (file snippets, structure)
    +--> Enforce format (TASK, DO/DONT, ACCEPTANCE)
    |
    v
Structured prompt → AI tool → Better output
```

## Key Features

### 1. Vague Request Detection

Catches requests before wasting time:

```bash
$ opticode optimize "should we use redis or mysql"
This looks like a comparison. Specify: (1) 'Implement X' to build one, 
or (2) ask for analysis only.
```

### 2. Automatic Context Injection

Adds relevant file snippets and repo structure:

```
CONTEXT:
- repo: src/opticode/cache.py - local file cache
- snippet:
  cache.py (first 30 lines):
  def load_cache(facts_path: Path, history_path: Path) -> Cache:
      ...
```

### 3. Output Format Enforcement

No more rambling explanations:

```
OUTPUT: GIT_DIFF_ONLY
```

### 4. Constraint Enforcement

```
DO:
- Make only the necessary code changes
- Keep behavior consistent

DONT:
- Do not change unrelated files
- Do not add explanations or extra output
```

## Usage Modes

### Mode 1: Preview (see before sending)

```bash
opticode optimize "Add error handling"
```

### Mode 2: Transparent Wrapper (recommended)

After `setup-integrations.sh`:

```bash
codex "Add error handling"      # Automatically optimized
claude "Refactor the CLI"        # Automatically optimized
```

### Mode 3: Copy-Paste (for Cursor, web tools)

```bash
opticode optimize "your request" | pbcopy
# Paste into Cursor, ChatGPT, etc.
```

See [USAGE_MODES.md](USAGE_MODES.md) for all options.

## Benchmarks

Based on 20 test scenarios:

| Metric | Value |
|--------|-------|
| **First-try success** | 60% → 95% |
| **Requests clarified** | 50% (prevents waste) |
| **Time saved** | 6.7 hours/month |
| **Token cost** | +$4/month |
| **Net value** | **+$662/month** @ $100/hr |
| **Processing overhead** | 0.1ms |

Full benchmark report: [benchmark_report.html](benchmark_report.html)

## Configuration

Create `.opticode/config.json`:

```json
{
  "codex_cmd": "codex exec --skip-git-repo-check {prompt}",
  "claude_cmd": "claude"
}
```

## Optional: AI-Powered Intent Analysis

For better intent detection, download a tiny local model:

```bash
python download_model.py  # Downloads ~1GB Qwen2.5-1.5B model
```

Without the model, opticode uses fast rule-based detection (~80% accuracy).
With the model, it uses a 500M parameter LLM (~95% accuracy).

## Integration Guides

- [USAGE_MODES.md](USAGE_MODES.md) - Different ways to use opticode
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Tool-specific setups
- [BENCHMARKS.md](BENCHMARKS.md) - Detailed benchmark methodology

## Examples

### Clear request (optimized)

```bash
$ opticode optimize "Add error handling to cache.py"

TASK:
Add error handling to cache.py.

CONTEXT:
- repo: src - source code
- snippet:
  src/opticode/cache.py (first 30 lines):
  [code snippet]

FILES:
src/opticode/cache.py

DO:
- Make only the necessary code changes
- Keep behavior consistent
- Add or update tests

DONT:
- Do not change unrelated files
- Do not add new dependencies
- Do not add explanations

ACCEPTANCE:
- Error handling added
- Tests pass
- No regressions

OUTPUT:
GIT_DIFF_ONLY
```

### Vague request (clarified)

```bash
$ opticode optimize "Improve the code"
What specific change do you want, and where should it be applied?
```

### Comparison request (clarified)

```bash
$ opticode optimize "should we use redis or upstash"
This looks like a comparison. Specify: (1) 'Implement X' to build one, 
or (2) ask for analysis only.
```

## Known Limitations

- **Not for Cursor** - Cursor has excellent built-in context
- **Not for web chat** - Use copy-paste mode
- **Not a cost saver** - Costs ~$4/month more in tokens
- **Not a full agent** - Just optimizes prompts

## When NOT to use opticode

- Using Cursor (has its own context management)
- Using Aider (has smart file detection)
- Cost is more important than developer time
- You prefer conversational AI interaction

## When TO use opticode

- Using Claude Code CLI or Codex CLI
- Making 20+ AI requests per day
- Frustrated with clarification round-trips
- Want consistent, reviewable outputs
- Value developer time over token costs

## Requirements

- Python 3.11+
- Optional: llama-cpp-python (for AI-powered intent analysis)
- Optional: ~1GB model download (for better accuracy)

## License

MIT
