# opticode - Purpose Statement

## Problem Being Solved

When developers use AI coding assistants (Codex, Claude Code, etc.), they often write vague prompts like:
- "fix the bug" 
- "add tests"
- "make it faster"
- "should we use Redis or PostgreSQL?"

These vague prompts waste money (API tokens) and time (back-and-forth clarifications) because:
1. The AI either guesses wrong and produces incorrect code
2. Or the AI asks clarifying questions, requiring another API call
3. Or the AI produces a generic answer that doesn't fit the specific codebase

## What opticode Claims to Do

opticode is a **local prompt optimizer** that intercepts vague user requests before they reach expensive AI APIs, and either:

1. **Blocks vague requests** with a clarifying question (saving API tokens)
2. **Rewrites vague requests** into specific, actionable prompts with context

### Key Features

1. **Intent Classification (Local LLM)**
   - Uses a 1GB local model (Qwen2.5-1.5B) running on CPU
   - Classifies requests as: implement, analyze, compare, question, unclear
   - No network calls, no API keys needed for classification

2. **Prompt Rewriting**
   - Transforms vague requests into structured prompts:
     - "add dashboard" → "Create a React dashboard component in src/components/Dashboard.tsx using recharts"
     - "add tests" → "Add Jest unit tests for src/calculator.js covering edge cases: negative numbers, zero, decimals"

3. **Clarification for Unsalvageable Requests**
   - "fix the bug" → "Provide the specific file and the type of bug you want fixed"
   - "should we use Redis or Postgres" → "This looks like a comparison. Specify: (1) 'Implement X' to build one, or (2) ask for analysis only"

4. **Structured Output Format**
   - Adds context sections: TASK, CONTEXT, FILES, DO, DONT, ACCEPTANCE, OUTPUT
   - Includes repo context (file structure, relevant snippets)

5. **Transparent Integration**
   - Wrapper scripts make it invisible: `codex "add login"` automatically runs through opticode
   - Exit code 2 = needs clarification (doesn't send to API)
   - Exit code 0 = optimized prompt sent to tool

## How It Works (Architecture)

```
User Input → Intent Model (local) → Decision
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            Needs Clarification              Clear/rewritten
                    ↓                               ↓
            Show hint to user              Build structured prompt
            (no API tokens used)           Send to Codex/Claude
```

### Components

1. **intent_model.py** - Local LLM (llama.cpp) for classification
2. **optimizer.py** - Builds structured prompts with repo context
3. **cli.py** - Commands: optimize, run, status
4. **executor.py** - Runs the actual tool (codex/claude) with optimized prompt
5. **wrappers/** - Shell scripts that transparently wrap codex/claude commands

## Expected Benefits

| Metric | Claim |
|--------|-------|
| Token savings | ~65% of vague requests blocked before hitting API |
| Cost savings | ~$8.40 per 100 requests (blocked + better first responses) |
| Time savings | 6.7 hrs/month (fewer back-and-forth clarifications) |
| Quality | 95% first-try success vs 60% without optimization |
| Latency | <1ms per request (local model) |
| Offline | Works without internet once model is downloaded |

## Success Criteria (How to Verify)

### 1. Intent Classification Accuracy
- Run `python eval_quick.py` - should score 8/8 (100%)
- Tests: vague_dashboard, vague_bug_fix, clear_feature, vague_tests, vague_optimize, comparison, filler_words, clear_refactor

### 2. Token Savings
- Vague request like "fix the bug" should return clarification (exit code 2), NOT send to API
- Specific request like "fix auth.py line 42" should pass through optimized

### 3. Prompt Quality
- Compare: `opticode optimize "add dashboard"` vs raw request
- Should see: specific tech stack, file paths, acceptance criteria added

### 4. Integration
- `opticode run --tool codex "add login"` should work if codex is installed
- Wrapper scripts should make `codex "add login"` transparently use opticode

### 5. Local Model Performance
- `opticode status` should show model available
- Classification should work without internet connection

## What opticode Does NOT Do

1. **Not an AI coding tool itself** - It only optimizes prompts, doesn't write code
2. **Not a replacement for context-aware tools** - Cursor, Aider have their own context systems
3. **Not magic** - It can't make "fix the bug" work without user clarification
4. **Not always right** - The 1.5B model sometimes misclassifies; rule-based fallback exists

## Verification Commands

```bash
# 1. Check status
opticode status

# 2. Run evaluation
python eval_quick.py

# 3. Test optimization
opticode optimize "add dashboard"

# 4. Test vague request blocking
opticode optimize "fix the bug"  # Should show clarification

# 5. Test comparison blocking  
opticode optimize "Redis vs Postgres"  # Should show clarification

# 6. Test with actual tool (if installed)
opticode run --tool codex "add error handling to cache.py"
```

## Files to Review

- `src/opticode/intent_model.py` - Intent classification logic
- `src/opticode/optimizer.py` - Prompt building logic
- `src/opticode/cli.py` - CLI interface
- `eval_quick.py` - Test suite (8 cases)
- `wrappers/codex` and `wrappers/claude` - Transparent integration scripts
