"""Tiny local LLM for request understanding and rewriting.

Uses llama.cpp (llama-cpp-python) for fast CPU inference.
Falls back to rule-based if model unavailable.

Model: Qwen2.5-1.5B-Instruct quantized to Q4_K_M (~1GB)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from contextlib import redirect_stderr
from typing import Optional
import io


@dataclass
class IntentResult:
    """Result of intent analysis."""
    request_type: str  # "implement", "analyze", "compare", "question", "unclear"
    rewritten: str     # Cleaned up request
    confidence: float  # 0.0 - 1.0
    needs_clarification: bool
    clarification_hint: Optional[str] = None


class TinyIntentModel:
    """Tiny local LLM using llama.cpp for fast CPU inference."""
    
    # Model download info - Qwen2.5-1.5B for better intent classification
    DEFAULT_MODEL = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    MODEL_SIZE = "~1GB"
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_file: Optional[Path] = None
        self._available = False
        self._load_model(model_path)
    
    def _load_model(self, model_path: Optional[str] = None) -> None:
        """Try to load the tiny model with llama.cpp."""
        try:
            os.environ.setdefault("LLAMA_CPP_LOG_LEVEL", "ERROR")
            os.environ.setdefault("LLAMA_CPP_LOG_VERBOSITY", "0")
            from llama_cpp import Llama
            
            # Find model file
            model_file = self._find_model(model_path)
            if not model_file:
                self._available = False
                return
            
            self.model_file = model_file
            
            # Load with minimal settings for fast inference
            # Suppress llama.cpp warnings that print to stderr on some platforms
            with redirect_stderr(io.StringIO()):
                self.model = Llama(
                    model_path=str(model_file),
                    n_ctx=1024,           # Small context is plenty for intent analysis
                    n_threads=None,       # Auto-detect CPU cores
                    verbose=False,
                )
            self._available = True
            
        except ImportError:
            # llama-cpp-python not installed
            self._available = False
        except Exception:
            # Model loading failed
            self._available = False
    
    def _find_model(self, model_path: Optional[str] = None) -> Optional[Path]:
        """Find GGUF model file."""
        # Direct path provided
        if model_path:
            p = Path(model_path).expanduser()
            if p.exists():
                return p
        
        # Environment variable
        env_path = os.environ.get("OPTICODE_MODEL")
        if env_path:
            p = Path(env_path).expanduser()
            if p.exists():
                return p
        
        # Common locations
        search_paths = [
            Path.home() / ".opticode" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            Path.home() / ".opticode" / "models" / "qwen2-0_5b-instruct-q4_k_m.gguf",
            Path(".opticode") / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            Path(".opticode") / "models" / "qwen2-0_5b-instruct-q4_k_m.gguf",
            Path("models") / "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            Path("models") / "qwen2-0_5b-instruct-q4_k_m.gguf",
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    @property
    def available(self) -> bool:
        return self._available
    
    def get_model_status(self) -> dict:
        """Get status info about model availability."""
        model_path = self._find_model(None)
        return {
            "available": self._available,
            "model_file": str(model_path) if model_path else None,
            "model_name": self.DEFAULT_MODEL,
            "download_url": self.MODEL_URL,
            "size": self.MODEL_SIZE,
        }
    
    def analyze(self, request: str) -> IntentResult:
        """Analyze user request intent using the tiny LLM."""
        if not self._available:
            return self._fallback_analyze(request)
        
        # Build chat prompt for Qwen2
        messages = [
            {
                "role": "system",
                "content": """You analyze user requests for a coding assistant. 
Determine the intent and rewrite clearly.

Output EXACTLY in this format:
TYPE: implement|analyze|compare|question|unclear
REWRITTEN: <specific, actionable, with file path and tech>
CONFIDENCE: 0.0-1.0
NEEDS_CLARIFICATION: yes|no
HINT: <brief guidance if unclear>

CRITICAL - REWRITE RULES:
- BAD: "Add a dashboard" → GOOD: "Create a React dashboard component in src/components/Dashboard.tsx using recharts to display user metrics"
- BAD: "Add tests" → GOOD: "Add Jest unit tests for src/calculator.js covering edge cases: negative numbers, zero, decimals"
- If request mentions SPECIFIC FILE + ACTION (e.g., "fix auth.py null pointer"): TYPE: implement, NEEDS_CLARIFICATION: no
- If request is COMPARISON (vs, should we use A or B, which is better): NEEDS_CLARIFICATION: yes
- If request is TOO VAGUE ("fix the bug" with no file/error, "make it better"): NEEDS_CLARIFICATION: yes
- NEVER invent specifics not in the request (don't guess "React" if not mentioned)

Types:
- implement: Build/code something specific
- analyze: Review/explain without changing  
- compare: Choose between alternatives
- question: Asking how/what/why
- unclear: Too vague even after rewriting"""
            },
            {
                "role": "user",
                "content": f'Request: "{request}"'
            }
        ]
        
        try:
            with redirect_stderr(io.StringIO()):
                output = self.model.create_chat_completion(
                    messages=messages,
                    max_tokens=200,
                    temperature=0.1,
                    stop=["<|im_end|>", "<|endoftext|>"],
                )
            
            response = output["choices"][0]["message"]["content"]
            return self._parse_response(response, request)
            
        except Exception:
            return self._fallback_analyze(request)
    
    def _parse_response(self, response: str, original: str) -> IntentResult:
        """Parse the model's structured output."""
        # Extract fields with regex
        type_match = re.search(r'TYPE:\s*(\w+)', response, re.IGNORECASE)
        rewritten_match = re.search(r'REWRITTEN:\s*(.+?)(?:\n[A-Z]+:|$)', response, re.DOTALL)
        confidence_match = re.search(r'CONFIDENCE:\s*(0?\.\d+|1\.0|1)', response)
        needs_clar_match = re.search(r'NEEDS_CLARIFICATION:\s*(yes|no)', response, re.IGNORECASE)
        hint_match = re.search(r'HINT:\s*(.+?)(?:\n[A-Z]+:|$)', response, re.DOTALL)
        
        req_type = type_match.group(1).lower() if type_match else "unclear"
        
        rewritten = rewritten_match.group(1).strip() if rewritten_match else original
        # Clean up common issues
        rewritten = self._clean_rewritten(rewritten)
        
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
            except ValueError:
                confidence = 0.5
        else:
            confidence = 0.5
        
        # Determine if clarification needed
        if needs_clar_match:
            needs_clar = needs_clar_match.group(1).lower() == "yes"
        else:
            # Auto-determine based on type
            needs_clar = req_type in ('compare', 'question', 'unclear')
        
        # OVERRIDE: Comparisons always need clarification (can't build both options)
        if req_type == 'compare':
            needs_clar = True
        
        # Get hint from model or use type-based default
        hint = hint_match.group(1).strip() if hint_match else None
        
        # Override bad hints with type-based defaults
        bad_hints = ('none', 'none needed', 'n/a', '', 'no hint needed', 'no hint')
        hint_lower = hint.lower() if hint else ''
        # Check for exact bad hints OR hints that are too vague/statements instead of guidance
        is_bad = (
            not hint or 
            hint_lower in bad_hints or 
            'comparison' in hint_lower or 
            'question' in hint_lower or
            ('none' in hint_lower and 'needed' in hint_lower) or
            (len(hint) > 10 and '?' not in hint and not any(w in hint_lower for w in ['specify', 'provide', 'clarify', 'rephrase']))
        )
        if is_bad:
            hint = None  # Will be set below based on type
        
        # Set hint based on type if clarification needed
        if needs_clar and not hint:
            hint_map = {
                'compare': "This looks like a comparison. Specify: (1) 'Implement X' to build one, or (2) ask for analysis only.",
                'question': "This looks like a question. Rephrase as an imperative task: 'Implement X', 'Add Y', 'Fix Z'.",
                'unclear': "Your request is unclear. Please be specific: what should be built/changed?",
                'analyze': "This is an analysis request. Specify what code to analyze and what you're looking for.",
            }
            hint = hint_map.get(req_type, "Please clarify your request.")
        
        # If rewritten is useless, fall back to simple cleanup
        if not rewritten or len(rewritten) < 5 or rewritten == original:
            rewritten = self._simple_cleanup(original)
        
        return IntentResult(
            request_type=req_type,
            rewritten=rewritten,
            confidence=confidence,
            needs_clarification=needs_clar,
            clarification_hint=hint,
        )
    
    def _clean_rewritten(self, text: str) -> str:
        """Clean up model output."""
        # Remove quotes if the model added them
        text = text.strip('"\'')
        # Remove "N/A", "none", etc.
        if text.lower() in ('n/a', 'none', 'null', 'original'):
            return ""
        return text
    
    def _simple_cleanup(self, request: str) -> str:
        """Remove filler words as fallback."""
        fillers = [
            (r'\bum\w*\b', ''), (r'\buh\w*\b', ''), (r'\bhm+\b', ''),
            (r'\bidk\b', ''), (r'\bi don\'t know\b', ''),
            (r'\bnot sure\b', ''), (r'\bmaybe\b', ''),
            (r'\blike\b', ''), (r'\byou know\b', ''),
            (r'\bi guess\b', ''), (r'\bprobably\b', ''),
            (r'\bor something\b', ''), (r'\bwhatever\b', ''),
            (r'\s+', ' '),  # normalize whitespace
        ]
        cleaned = request
        for pattern, repl in fillers:
            cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
        return cleaned.strip()
    
    def _fallback_analyze(self, request: str) -> IntentResult:
        """Rule-based fallback when model unavailable."""
        req_l = request.lower()
        
        # Simple heuristics
        is_question = '?' in request
        has_fillers = any(w in req_l for w in ['umm', 'uhh', 'uh ', 'idk', 'not sure', 'maybe ', 'i guess'])
        
        # Comparison detection - more robust patterns
        is_compare = (
            any(w in req_l for w in [' vs ', ' versus ', 'compare', 'better than', 'better choice']) or
            ('which' in req_l and ('better' in req_l or 'use' in req_l)) or
            ('should' in req_l and ' or ' in req_l) or
            ('whether' in req_l and ' or ' in req_l) or
            ('dont know' in req_l and ' or ' in req_l) or
            (req_l.count(' or ') >= 2)  # Multiple options
        )
        # Count meaningful words (more than 2 chars, not just "idk", "what", "to", "do")
        meaningful = [w for w in req_l.split() if len(w) > 2 and w not in ('idk', 'what', 'the', 'and', 'for')]
        is_unclear = len(meaningful) < 3
        
        # Determine type
        if is_compare:
            req_type = "compare"
            rewritten = self._simple_cleanup(request)
            return IntentResult(
                request_type=req_type,
                rewritten=rewritten,
                confidence=0.5,
                needs_clarification=True,
                clarification_hint="This looks like a comparison. Specify: (1) 'Implement X' to build one, or (2) ask for analysis only.",
            )
        
        if is_question:
            req_type = "question"
            rewritten = self._simple_cleanup(request)
            return IntentResult(
                request_type=req_type,
                rewritten=rewritten,
                confidence=0.5,
                needs_clarification=True,
                clarification_hint="This looks like a question. Rephrase as an imperative task: 'Implement X', 'Add Y', 'Fix Z'.",
            )
        
        # Check for question patterns without question mark
        question_starts = ['how do i', 'how to', 'how can i', 'what is', 'what are', 'whats the', "what's the"]
        if any(req_l.startswith(q) for q in question_starts):
            req_type = "question"
            rewritten = self._simple_cleanup(request)
            return IntentResult(
                request_type=req_type,
                rewritten=rewritten,
                confidence=0.5,
                needs_clarification=True,
                clarification_hint="This looks like a question. Rephrase as an imperative task.",
            )
        
        # Check for uncertainty patterns that indicate unclear intent
        uncertainty_patterns = [
            'dont know', 'dont kno', 'idk', 'not sure', 
            'i dunno', 'no idea', 'confused about'
        ]
        has_uncertainty = any(p in req_l for p in uncertainty_patterns)
        
        if has_fillers or is_unclear or has_uncertainty:
            rewritten = self._simple_cleanup(request)
            # If cleanup removed everything or left something vague, it's unclear
            # Check if cleanup resulted in something useless
            vague_results = ('what to do', 'how to', 'help', 'help me', 'fix this', 'do this', 
                           'which to use', 'what to use', 'better choice')
            if not rewritten or len(rewritten.split()) < 2 or rewritten.lower() in vague_results:
                return IntentResult(
                    request_type="unclear",
                    rewritten=request,
                    confidence=0.3,
                    needs_clarification=True,
                    clarification_hint="Your request is unclear. Please be specific: what should be built/changed?",
                )
            # Cleanup helped, proceed with caution
            return IntentResult(
                request_type="implement",
                rewritten=rewritten,
                confidence=0.6,
                needs_clarification=False,
            )
        
        # Seems clear
        return IntentResult(
            request_type="implement",
            rewritten=request,
            confidence=0.7,
            needs_clarification=False,
        )


# Singleton instance
_model_instance: Optional[TinyIntentModel] = None


def get_intent_model() -> TinyIntentModel:
    """Get or create the singleton model instance."""
    global _model_instance
    if _model_instance is None:
        _model_instance = TinyIntentModel()
    return _model_instance


def analyze_request(request: str) -> IntentResult:
    """Analyze a user request (uses model if available, else rules)."""
    model = get_intent_model()
    return model.analyze(request)


def get_model_info() -> dict:
    """Get information about the model status."""
    model = get_intent_model()
    return model.get_model_status()
