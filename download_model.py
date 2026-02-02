#!/usr/bin/env python3
"""Download the tiny LLM for opticode's intent analysis.

Model: Qwen2.5-1.5B-Instruct (Q4_K_M quantized)
Size: ~1GB
Purpose: Understand and rewrite user requests locally
"""

import os
import sys
from pathlib import Path
from urllib.request import urlretrieve

MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_NAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_SIZE_MB = 1024


def get_model_dir() -> Path:
    """Get the directory to store models."""
    # Prefer ~/.opticode/models
    model_dir = Path.home() / ".opticode" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


def download_with_progress(url: str, dest: Path):
    """Download file with progress bar."""
    print(f"Downloading {MODEL_NAME} (~{MODEL_SIZE_MB}MB)...")
    print(f"Destination: {dest}")
    print()
    
    last_percent = 0
    
    def report_progress(block_num, block_size, total_size):
        nonlocal last_percent
        downloaded = block_num * block_size
        percent = min(int(downloaded * 100 / total_size), 100)
        if percent >= last_percent + 5:
            bar = "█" * (percent // 5) + "░" * (20 - percent // 5)
            print(f"\r[{bar}] {percent}%", end="", flush=True)
            last_percent = percent
    
    try:
        urlretrieve(url, dest, reporthook=report_progress)
        print(f"\n\n✓ Download complete: {dest}")
        return True
    except Exception as e:
        print(f"\n\n✗ Download failed: {e}")
        return False


def main():
    model_dir = get_model_dir()
    model_path = model_dir / MODEL_NAME
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"Model already exists: {model_path}")
        print(f"Size: {size_mb:.1f}MB")
        
        response = input("\nRe-download? [y/N]: ").strip().lower()
        if response != 'y':
            print("Using existing model.")
            return 0
        
        print()
    
    success = download_with_progress(MODEL_URL, model_path)
    
    if success:
        # Verify file size (should be ~1GB)
        actual_size = model_path.stat().st_size / (1024 * 1024)
        if actual_size < 100:  # Suspiciously small
            print(f"\n⚠ Warning: File seems small ({actual_size:.1f}MB). Download may have failed.")
            return 1
        
        print(f"\nModel ready!")
        print(f"\nYou can now use opticode with AI-powered intent understanding:")
        print(f"  opticode optimize \"your request\"")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
