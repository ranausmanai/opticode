#!/usr/bin/env python3
"""Quick test to verify llama.cpp is working with opticode's intent model."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 70)
print("LLAMA.CPP / INTENT MODEL TEST")
print("=" * 70)
print()

# Check if llama-cpp-python is installed
print("1. Checking llama-cpp-python installation...")
try:
    from llama_cpp import Llama
    print("   ✓ llama-cpp-python is installed")
except ImportError:
    print("   ✗ llama-cpp-python NOT installed")
    print()
    print("   Install with:")
    print("     pip install llama-cpp-python")
    sys.exit(1)

# Check for model
print()
print("2. Checking for model file...")

model_paths = [
    Path.home() / ".opticode" / "models" / "qwen2-0_5b-instruct-q4_k_m.gguf",
    Path(".opticode") / "models" / "qwen2-0_5b-instruct-q4_k_m.gguf",
    Path("models") / "qwen2-0_5b-instruct-q4_k_m.gguf",
]

model_file = None
for path in model_paths:
    if path.exists():
        model_file = path
        print(f"   ✓ Found model: {path}")
        print(f"     Size: {path.stat().st_size / (1024*1024):.1f} MB")
        break

if not model_file:
    print("   ✗ Model NOT found")
    print()
    print("   Download with:")
    print("     python download_model.py")
    print()
    print("   Or manually:")
    print("     mkdir -p ~/.opticode/models")
    print("     curl -L -o ~/.opticode/models/qwen2-0_5b-instruct-q4_k_m.gguf \\")
    print("       https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF/resolve/main/qwen2-0_5b-instruct-q4_k_m.gguf")
    sys.exit(1)

# Try loading the model
print()
print("3. Loading model (this may take 10-30 seconds)...")
try:
    model = Llama(
        model_path=str(model_file),
        n_ctx=1024,
        verbose=False,
    )
    print("   ✓ Model loaded successfully!")
except Exception as e:
    print(f"   ✗ Failed to load model: {e}")
    sys.exit(1)

# Test inference
print()
print("4. Testing inference...")

test_prompts = [
    "Add error handling to the cache module",
    "umm should we use redis or uptash idk",
    "How do I refactor this code?",
]

for prompt in test_prompts:
    print()
    print(f"   Input: \"{prompt}\"")
    
    messages = [
        {"role": "system", "content": "You analyze requests. Output: TYPE: implement|compare|question|unclear"},
        {"role": "user", "content": f"Analyze: {prompt}"},
    ]
    
    try:
        output = model.create_chat_completion(
            messages=messages,
            max_tokens=50,
            temperature=0.1,
        )
        response = output["choices"][0]["message"]["content"]
        print(f"   Output: {response[:100]}...")
        print(f"   ✓ Inference successful")
    except Exception as e:
        print(f"   ✗ Inference failed: {e}")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print()
print("To use with opticode:")
print("  opticode status          # Check if model is detected")
print("  opticode optimize '...'  # Run with AI intent analysis")
