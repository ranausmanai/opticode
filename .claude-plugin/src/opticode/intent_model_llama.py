"""Alternative: llama.cpp backend for even faster inference.

This uses llama-cpp-python which is lighter than transformers+torch.
Requires: pip install llama-cpp-python
Model: Download a GGUF like qwen2.5-1.5b-instruct-q4_k_m.gguf (~1GB)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .intent_model import IntentResult, TinyIntentModel


class LlamaIntentModel(TinyIntentModel):
    """llama.cpp backend - faster, lighter than transformers."""
    
    def _load_model(self, model_path: Optional[str] = None) -> None:
        try:
            from llama_cpp import Llama
            
            # Look for GGUF model in standard locations
            model_file = self._find_gguf_model(model_path)
            if not model_file:
                self._available = False
                return
            
            # Load with minimal settings for fast inference
            self.model = Llama(
                model_path=str(model_file),
                n_ctx=2048,           # Small context is enough
                n_threads=4,          # Use 4 CPU cores
                verbose=False,
            )
            self._available = True
            
        except Exception:
            self._available = False
    
    def _find_gguf_model(self, model_path: Optional[str]) -> Optional[Path]:
        """Find GGUF model file."""
        if model_path and Path(model_path).exists():
            return Path(model_path)
        
        # Check environment variable
        env_path = os.environ.get("OPTICODE_MODEL")
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        # Check common locations
        search_paths = [
            Path.home() / ".opticode" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            Path.home() / ".opticode" / "models" / "qwen2-0_5b-instruct-q4_k_m.gguf",
            Path.home() / ".opticode" / "models" / "tinyllama-1.1b-chat-v1.0-q4_k_m.gguf",
            Path("./models/qwen2.5-1.5b-instruct-q4_k_m.gguf"),
            Path("./models/qwen2-0_5b-instruct-q4_k_m.gguf"),
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    def analyze(self, request: str) -> IntentResult:
        if not self._available:
            return self._fallback_analyze(request)
        
        system_prompt = """You analyze coding requests. Output exactly:
TYPE: implement|analyze|compare|question|unclear
REWRITTEN: <clean imperative version>
CONFIDENCE: 0.0-1.0
NEEDS_CLARIFICATION: yes|no
HINT: <guidance if unclear>

Remove: umm, idk, not sure, maybe, probably. Convert questions to tasks."""

        prompt = f"{system_prompt}\n\nRequest: {request}\n\nAnalysis:\n"
        
        try:
            output = self.model(
                prompt,
                max_tokens=150,
                temperature=0.1,
                stop=["Request:", "\n\n"],
            )
            
            response = output["choices"][0]["text"]
            return self._parse_response(response, request)
            
        except Exception:
            return self._fallback_analyze(request)


def download_model_instructions() -> str:
    """Instructions for downloading a tiny model."""
    return """
To enable AI-powered intent understanding, download a tiny GGUF model:

1. Create directory:
   mkdir -p ~/.opticode/models

2. Download Qwen2.5-1.5B (recommended, ~1GB):
   curl -L -o ~/.opticode/models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
     https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf

Or Qwen2-0.5B (~400MB):
   curl -L -o ~/.opticode/models/qwen2-0_5b-instruct-q4_k_m.gguf \
     https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF/resolve/main/qwen2-0_5b-instruct-q4_k_m.gguf

Or TinyLlama (~600MB):
   curl -L -o ~/.opticode/models/tinyllama-1.1b-chat-v1.0-q4_k_m.gguf \
     https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

3. Install llama-cpp-python:
   pip install llama-cpp-python

The model will load automatically on next run.
"""
