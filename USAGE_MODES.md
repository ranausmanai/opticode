# opticode Usage Modes

## Quick Decision: Which Mode Should I Use?

| You want to... | Use this mode | Command |
|---------------|---------------|---------|
| Just see the optimized prompt | Preview | `opticode optimize "request"` |
| Optimize + send to AI tool | Transparent wrapper | `codex "request"` (after setup) |
| Use in Cursor | Copy-paste | `opticode optimize "request" \| pbcopy` |
| Use in your own script | Python API | `optimize_request(text, ctx)` |
| Batch process requests | HTTP API | `POST /optimize` |

---

## Mode 1: Preview (See Before Sending)

**Best for:** Understanding what opticode does, testing requests

```bash
opticode optimize "Add error handling to the cache module"
```

**Output:**
```
TASK:
Add error handling to the cache module.

CONTEXT:
- repo: src - source code
- snippet:
cache.py (first 30 lines):
...

FILES:
cache.py

DO:
- Make only the necessary code changes
...

OUTPUT:
GIT_DIFF_ONLY
```

**When to use:**
- Learning how opticode works
- Debugging why a request was clarified
- Copying to Cursor/ChatGPT web

---

## Mode 2: Transparent Wrapper (Recommended)

**Best for:** Daily use with Claude Code or Codex CLI

### Setup (one-time)

```bash
./setup-integrations.sh
source ~/.bashrc  # or ~/.zshrc
```

### Usage

```bash
# These automatically go through opticode
codex "Add error handling to cache.py"
claude "Refactor the CLI module"

# You won't notice opticode is there
# But you'll get better responses
```

**What happens:**
1. You type `codex "Add error handling"`
2. Wrapper calls `opticode run --tool codex "Add error handling"`
3. opticode analyzes and optimizes
4. Sends structured prompt to Codex
5. You see the response

**When to use:**
- Daily coding with AI assistants
- You want opticode to "just work"
- You use CLI tools frequently

---

## Mode 3: Copy-Paste (For Cursor, Web, etc.)

**Best for:** Cursor, GitHub Copilot web, ChatGPT, etc.

### macOS

```bash
opticode optimize "your request" | pbcopy
# Now paste into Cursor/ChatGPT
```

### Linux

```bash
opticode optimize "your request" | xclip -selection clipboard
# Now paste
```

### Windows (WSL)

```bash
opticode optimize "your request" | clip.exe
# Now paste
```

**When to use:**
- Cursor (no CLI to wrap)
- GitHub Copilot web interface
- ChatGPT web
- Any web-based AI tool

---

## Mode 4: Python API (For Your Tools)

**Best for:** Building your own tools, automation

```python
from opticode.optimizer import optimize_request
from opticode.repo_context import init_repo_context
from pathlib import Path

# Initialize context for repo
ctx = init_repo_context(Path.cwd())

# Optimize a request
result = optimize_request("Add error handling", ctx)

if result.clarifying_question:
    print(f"Need clarification: {result.clarifying_question}")
else:
    # Send to OpenAI, Anthropic, etc.
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": result.prompt}]
    )
```

**When to use:**
- Building custom AI coding tools
- Integrating into existing workflows
- Batch processing requests

---

## Mode 5: HTTP API Server

**Best for:** Microservices, remote access

Start server:
```bash
python -c "
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class Request(BaseModel):
    text: str
    repo_path: str = '.'

@app.post('/optimize')
def optimize(req: Request):
    from opticode.optimizer import optimize_request
    from opticode.repo_context import init_repo_context
    from pathlib import Path
    
    ctx = init_repo_context(Path(req.repo_path))
    result = optimize_request(req.text, ctx)
    
    return {
        'prompt': result.prompt,
        'clarify': result.clarifying_question,
        'should_send': result.clarifying_question is None
    }

uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

Use it:
```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{"text": "Add error handling"}'
```

**When to use:**
- Team-wide optimization service
- Remote/CI integration
- Language-agnostic access

---

## Mode Comparison Table

| Mode | Setup | Speed | Best For |
|------|-------|-------|----------|
| Preview | None | 0.1ms | Learning, debugging |
| Wrapper | One-time shell setup | 0.1ms | Daily CLI use |
| Copy-paste | None | 0.1ms + manual | Cursor, web tools |
| Python API | pip install | 0.1ms | Custom tools |
| HTTP API | Server setup | Network | Teams, services |

---

## Tool-Specific Recommendations

### Claude Code
```bash
# Setup
./setup-integrations.sh

# Use
claude "Refactor the cache module"
```

### Codex CLI
```bash
# Setup
./setup-integrations.sh

# Use
codex "Add error handling to cache.py"
```

### Cursor
```bash
# No CLI to wrap, use copy-paste
opticode optimize "your request" | pbcopy
# Then paste into Cursor chat
```

### GitHub Copilot (VS Code)
```bash
# Copy-paste mode
opticode optimize "your request" | pbcopy
# Paste into Copilot chat
```

### Kimi (Moonshot AI)
```python
# Python API mode
from opticode.optimizer import optimize_request
# Then send to Kimi API
```

### Continue.dev
```bash
# May be redundant - Continue has its own context
# But can use for vague request detection:
opticode optimize "your request"  # Check if it needs clarification
```

---

## Aliases for Convenience

Add to your shell config:

```bash
# ~/.bashrc or ~/.zshrc

# Short aliases
alias opt='opticode optimize'
alias optc='opticode optimize | pbcopy'
alias opts='opticode status'

# Tool wrappers (after setup-integrations.sh)
alias codex='opticode run --tool codex'
alias claude='opticode run --tool claude'
```

Then use:
```bash
opt "Add error handling"        # Just optimize
optc "Add error handling"       # Optimize and copy
opts                             # Check status
codex "Add error handling"      # Optimize and run
```

---

## Troubleshooting

### "codex: command not found" after setup

```bash
# Reload shell config
source ~/.bashrc  # or ~/.zshrc

# Or check PATH
echo $PATH | grep opticode
```

### Wrapper not working

```bash
# Check which codex is being used
which codex

# Should show: /Users/you/.opticode/wrappers/codex
# If not, PATH order is wrong
```

### Copy-paste not working on Linux

```bash
# Install xclip
sudo apt-get install xclip  # Ubuntu/Debian
sudo pacman -S xclip        # Arch

# Or use xsel
sudo apt-get install xsel
opticode optimize "request" | xsel --clipboard
```
