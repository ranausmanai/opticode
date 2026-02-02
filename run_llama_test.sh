#!/bin/bash
# Simple script to download and test llama.cpp with opticode

set -e

MODEL_DIR="$HOME/.opticode/models"
MODEL_FILE="$MODEL_DIR/qwen2-0_5b-instruct-q4_k_m.gguf"
MODEL_URL="https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF/resolve/main/qwen2-0_5b-instruct-q4_k_m.gguf"

echo "======================================================================"
echo "                    LLAMA.CPP TEST SCRIPT"
echo "======================================================================"
echo ""

# Check Python
echo "1. Checking Python..."
python --version || { echo "Python not found"; exit 1; }

# Check llama-cpp-python
echo ""
echo "2. Checking llama-cpp-python..."
python -c "from llama_cpp import Llama; print('   ✓ llama-cpp-python installed')" || {
    echo "   ✗ llama-cpp-python not installed"
    echo "   Installing..."
    pip install llama-cpp-python
}

# Download model if needed
echo ""
echo "3. Checking for model..."
if [ -f "$MODEL_FILE" ]; then
    SIZE=$(du -h "$MODEL_FILE" | cut -f1)
    echo "   ✓ Model found: $MODEL_FILE ($SIZE)"
else
    echo "   Model not found. Downloading (~400MB)..."
    mkdir -p "$MODEL_DIR"
    
    if command -v curl &> /dev/null; then
        curl -L --progress-bar -o "$MODEL_FILE" "$MODEL_URL"
    elif command -v wget &> /dev/null; then
        wget --progress=bar:force -O "$MODEL_FILE" "$MODEL_URL"
    else
        echo "   ✗ Need curl or wget to download"
        exit 1
    fi
    
    echo "   ✓ Download complete"
fi

# Run test
echo ""
echo "4. Running inference test..."
echo "   Loading model (this may take 10-30 seconds)..."
python << PYTHON_EOF
from llama_cpp import Llama
import sys

try:
    model = Llama(
        model_path="$MODEL_FILE",
        n_ctx=1024,
        verbose=False,
    )
    print("   ✓ Model loaded successfully!")
    print("")
    print("   Testing with: 'should we use redis or mysql'")
    
    output = model.create_chat_completion(
        messages=[
            {"role": "system", "content": "Analyze the request type: implement, compare, question, or unclear. Be brief."},
            {"role": "user", "content": "should we use redis or mysql"}
        ],
        max_tokens=30,
        temperature=0.1,
    )
    
    response = output["choices"][0]["message"]["content"]
    print(f"   Output: {response.strip()}")
    print("")
    print("   ✓ Inference successful!")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)
PYTHON_EOF

echo ""
echo "======================================================================"
echo "                    TEST COMPLETE"
echo "======================================================================"
echo ""
echo "You can now use opticode with the model:"
echo "  opticode status"
echo "  opticode optimize 'your request here'"
