# opticode Integration Guide

How to integrate opticode into your workflow for maximum benefit.

## The Problem with Current Usage

The current `opticode run --tool codex` pattern is clunky because:
- You have to remember to use it
- Extra typing
- Mental overhead

**Better approach:** Make opticode transparent/invisible.

---

## Integration Pattern 1: Shell Alias (Easiest)

### Bash/Zsh

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Wrap codex with opticode
alias codex='opticode-run-codex'
function opticode-run-codex() {
    opticode run --tool codex "$@"
}

# Wrap claude with opticode  
alias claude='opticode-run-claude'
function opticode-run-claude() {
    opticode run --tool claude "$@"
}
```

Now use normally:
```bash
codex "Add error handling to cache.py"  # Automatically optimized
```

### Fish Shell

```fish
# ~/.config/fish/config.fish
function codex
    opticode run --tool codex $argv
end

function claude
    opticode run --tool claude $argv
end
```

---

## Integration Pattern 2: Proxy Script (Transparent)

Create a proxy that intercepts calls:

### ~/.local/bin/codex
```bash
#!/bin/bash
# Transparent opticode wrapper for codex

# Check if we should optimize (skip for --help, --version, etc.)
if [[ "$1" == "--help" || "$1" == "--version" || "$1" == "-h" ]]; then
    exec /usr/local/bin/codex "$@"
fi

# Optimize and run
exec opticode run --tool codex "$@"
```

Make it first in PATH:
```bash
chmod +x ~/.local/bin/codex
export PATH="$HOME/.local/bin:$PATH"
```

---

## Integration Pattern 3: VS Code Extension (IDE Integration)

### Concept: opticode-vscode

```typescript
// Extension activates on AI commands
// Intercepts requests before sending to GitHub Copilot, Cody, etc.

// When user types in Copilot chat:
// "Add error handling"

// Extension calls opticode.optimize(request)
// Gets back structured prompt
// Sends structured version to Copilot

// User sees better responses automatically
```

### Implementation Sketch

```typescript
// src/extension.ts
import * as vscode from 'vscode';
import { optimizeRequest } from './opticode';

export function activate(context: vscode.ExtensionContext) {
    // Intercept Copilot chat requests
    const provider = new OptimizedChatProvider();
    
    context.subscriptions.push(
        vscode.chat.registerChatParticipant('opticode', provider)
    );
}

class OptimizedChatProvider implements vscode.ChatParticipant {
    async requestHandler(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        response: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ) {
        // Optimize the prompt before sending to AI
        const optimized = await optimizeRequest(request.prompt);
        
        if (optimized.clarifying_question) {
            // Show clarification to user
            response.markdown(optimized.clarifying_question);
            return;
        }
        
        // Forward optimized prompt to actual AI
        const aiResponse = await vscode.lm.sendRequest(
            { prompt: optimized.prompt },
            {},
            token
        );
        
        // Stream response back
        for await (const fragment of aiResponse.text) {
            response.markdown(fragment);
        }
    }
}
```

---

## Integration Pattern 4: Cursor Integration

Cursor doesn't have a CLI, but you can use opticode differently:

### Option A: Pre-process in terminal, paste into Cursor

```bash
# Generate optimized prompt
opticode optimize "Add error handling to cache module" | pbcopy

# Paste into Cursor chat
# (Now has structured context, constraints, etc.)
```

### Option B: Cursor Rules Integration

Add to `.cursorrules`:

```
When receiving requests, they may already be optimized with this format:

TASK:
[imperative task description]

CONTEXT:
- repo: [structure info]
- snippet: [relevant code]

FILES:
[files to modify]

DO:
- [constraints]

DONT:
- [anti-constraints]

ACCEPTANCE:
- [success criteria]

OUTPUT:
GIT_DIFF_ONLY

Respect these constraints strictly.
```

---

## Integration Pattern 5: API Mode (Programmatic)

Use opticode as a library in your tools:

### Python API

```python
from opticode.optimizer import optimize_request
from opticode.repo_context import init_repo_context

ctx = init_repo_context(Path.cwd())

# In your tool, before calling AI API
user_input = "Add error handling"
result = optimize_request(user_input, ctx)

if result.clarifying_question:
    # Ask user to clarify
    print(result.clarifying_question)
else:
    # Send optimized prompt to OpenAI/Anthropic
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": result.prompt}]
    )
```

### HTTP API Server

```python
# opticode-server.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class OptimizeRequest(BaseModel):
    request: str
    repo_path: str = "."

@app.post("/optimize")
async def optimize(req: OptimizeRequest):
    ctx = init_repo_context(Path(req.repo_path))
    result = optimize_request(req.request, ctx)
    return {
        "prompt": result.prompt,
        "clarifying_question": result.clarifying_question,
        "should_send": result.clarifying_question is None
    }

# Run: uvicorn opticode-server:app
# Use: curl -X POST http://localhost:8000/optimize \
#        -H "Content-Type: application/json" \
#        -d '{"request": "Add error handling"}'
```

---

## Integration Pattern 6: Git Hook (Pre-commit)

Check if AI-generated changes follow constraints:

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Check for opticode acceptance criteria in commit messages
# or verify changes don't violate constraints

COMMIT_MSG_FILE=$1

# If commit mentions AI assistance, verify constraints
if grep -q "AI\|assistant\|copilot" "$COMMIT_MSG_FILE"; then
    echo "⚠️  AI-assisted commit detected"
    echo "Checking constraints..."
    
    # Check no unrelated files modified
    # Check tests added if needed
    # etc.
fi
```

---

## Tool-Specific Recommendations

### Claude Code
```bash
# Best: Shell alias
alias claude='opticode run --tool claude'

# Claude Code config: ~/.claude/config.json
{
  "prompt_optimizer": "opticode"
}
```

### Codex CLI
```bash
# Best: Proxy script or alias
alias codex='opticode run --tool codex'

# Or use opticode optimize + pipe
codex <<< $(opticode optimize "Add error handling")
```

### Cursor
```bash
# Best: Use opticode as preprocessor
opticode optimize "your request" | pbcopy
# Then paste into Cursor

# Or add .cursorrules (see Pattern 4)
```

### Kimi (Moonshot AI)
```python
# Use Python API (Pattern 5)
# Kimi doesn't have official CLI yet
```

### Continue.dev / Aider
```bash
# These tools have their own context management
# opticode may be redundant
# But can still help with vague request detection
```

### GitHub Copilot (VS Code)
```bash
# Wait for VS Code extension (Pattern 3)
# Or use CLI workflow with copilot CLI
gh copilot suggest -t shell "$(opticode optimize 'find all TODOs')"
```

---

## Recommended: The "Transparent Wrapper" Setup

### Step 1: Create wrapper scripts

```bash
mkdir -p ~/.opticode/wrappers

# ~/.opticode/wrappers/codex
cat > ~/.opticode/wrappers/codex << 'EOF'
#!/bin/bash
exec opticode run --tool codex "$@"
EOF
chmod +x ~/.opticode/wrappers/codex

# ~/.opticode/wrappers/claude
cat > ~/.opticode/wrappers/claude << 'EOF'
#!/bin/bash
exec opticode run --tool claude "$@"
EOF
chmod +x ~/.opticode/wrappers/claude
```

### Step 2: Add to PATH

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.opticode/wrappers:$PATH"
```

### Step 3: Use normally

```bash
codex "Add error handling"  # Automatically optimized
claude "Refactor the CLI"   # Automatically optimized
```

---

## When NOT to Use opticode

Don't use opticode with:
- **Cursor** - Has its own excellent context management
- **Aider** - Already has smart file detection
- **Continue.dev** - Has its own context system
- **ChatGPT web** - No CLI to wrap

DO use opticode with:
- **Claude Code CLI** - No built-in context detection
- **Codex CLI** - No built-in constraints
- **Direct API calls** - Your own scripts
- **Custom tools** - Where you control the pipeline

---

## Future: Native Integrations

Ideally, these tools would integrate opticode natively:

```json
// .cursor/settings.json
{
  "ai.promptOptimizer": "opticode"
}

// .codex/config.json
{
  "optimizePrompts": true,
  "optimizer": "opticode"
}

// claude.config.json
{
  "prompt_enhancement": "opticode"
}
```

Until then, use the wrapper/alias approach!
