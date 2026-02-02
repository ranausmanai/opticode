# opticode Claude Code Plugin

Prompt linting and repo-aware context injection for Claude Code.

## What It Does

Automatically optimizes your prompts before Claude processes them:

- **Blocks vague requests** - "fix the bug" → Shows guidance
- **Rewrites unclear requests** - "add dashboard" → Specific file paths, tech stack
- **Adds repo context** - File snippets, structure, constraints

## Installation

From GitHub (when published):
```
/plugin marketplace add your-github-org/opticode
/plugin install opticode@opticode-marketplace
```

## Usage

Just use Claude Code normally - prompts auto-optimize:

```
> add dashboard
→ [opticode rewrites to specific prompt]
→ [Claude receives structured prompt]

> fix the bug
→ opticode: "Provide specific file and error"
→ [Blocked until clarified]
```
