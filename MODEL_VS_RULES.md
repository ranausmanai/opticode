# AI Model vs Rule-Based Detection

## Current Situation

The **400MB Qwen2-0.5B model** is not reliable enough for intent classification:
- Accuracy: ~57% on test cases
- Speed: ~500ms per request (slow)
- False negatives: Lets through requests that should be blocked

The **rule-based fallback** is actually more reliable:
- Accuracy: ~71% on test cases  
- Speed: ~0.1ms per request (fast)
- Predictable behavior

## Recommendation: Use Rules, Not Model

For this use case (intent classification), a 0.5B parameter model is **too small** to be reliable. The regex/heuristic approach works better.

## How to Disable Model (Use Rules Only)

### Option 1: Environment Variable

```bash
export OPTICODE_USE_MODEL=false
opticode optimize "your request"
```

### Option 2: Code Change

In `src/opticode/intent_model.py`, modify `analyze_request()`:

```python
def analyze_request(request: str) -> IntentResult:
    """Analyze a user request (rules only, skip model)."""
    model = get_intent_model()
    
    # Skip model, use rules directly
    if model.available and os.environ.get('OPTICODE_USE_MODEL') != 'false':
        return model.analyze(request)
    
    # Use rules only (faster, more reliable)
    return model._fallback_analyze(request)
```

### Option 3: Delete Model File

```bash
rm ~/.opticode/models/qwen2-0_5b-instruct-q4_k_m.gguf
# Will automatically fall back to rules
```

## When Would Model Be Better?

A larger model (7B+ parameters) would be better for:
- Understanding nuanced context
- Handling complex ambiguous requests
- Better confidence calibration

But for a 0.5B model:
- Rules are more reliable
- Rules are 5000x faster
- Rules don't require 400MB download

## Current Behavior

With model loaded:
- Model runs first (500ms)
- If model fails, falls back to rules
- Model often misclassifies

Without model:
- Rules run immediately (0.1ms)
- Consistent, predictable behavior
- No Metal/GPU warnings

## Simpler Architecture

Consider removing the model entirely and just using rules:

```python
# Simplified intent_model.py
def analyze_request(request: str) -> IntentResult:
    return _rule_based_analyze(request)
```

Benefits:
- Faster (0.1ms vs 500ms)
- Smaller (no 400MB download)
- More reliable
- No dependencies on llama-cpp-python
