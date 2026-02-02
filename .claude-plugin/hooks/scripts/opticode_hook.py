#!/usr/bin/env python3
"""Claude Code Plugin Hook for opticode."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

def main() -> int:
    # DEBUG: Log that we're starting
    debug_log = Path("/tmp/opticode_hook_debug.log")
    with open(debug_log, "a") as f:
        f.write(f"\n=== HOOK CALLED ===\n")
        f.write(f"Args: {sys.argv}\n")
        f.write(f"CWD: {os.getcwd()}\n")
    
    try:
        event = json.loads(sys.stdin.read() or "{}")
        prompt = event.get("user_prompt", "") or event.get("prompt", "")
        
        with open(debug_log, "a") as f:
            f.write(f"Prompt: {prompt[:100]}...\n")
        
        # Get plugin root
        plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", 
                                         Path(__file__).parent.parent.parent))
        
        with open(debug_log, "a") as f:
            f.write(f"Plugin root: {plugin_root}\n")
        
        # Add src to path
        src_path = plugin_root / "src"
        if src_path.exists():
            sys.path.insert(0, str(src_path))
        
        # Try importing
        try:
            from opticode.optimizer import optimize_request
            from opticode.repo_context import init_repo_context
            
            with open(debug_log, "a") as f:
                f.write("Imports successful\n")
            
            ctx = init_repo_context(Path.cwd())
            result = optimize_request(prompt, ctx, quality=False)
            
            with open(debug_log, "a") as f:
                f.write(f"Optimization result: needs_clarification={result.needs_clarification}\n")
            
            if result.clarifying_question:
                output = {
                    "continue": False,
                    "stopReason": result.clarifying_question,
                    "suppressOutput": True,
                    "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}
                }
                print(json.dumps(output))
                with open(debug_log, "a") as f:
                    f.write(f"BLOCKED: {result.clarifying_question}\n")
                return 0
            
            # Let through with optimized prompt
            output = {
                "continue": True,
                "suppressOutput": True,
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": result.prompt
                }
            }
            print(json.dumps(output))
            with open(debug_log, "a") as f:
                f.write(f"PASSED THROUGH\n")
            return 0
            
        except Exception as e:
            with open(debug_log, "a") as f:
                f.write(f"ERROR: {type(e).__name__}: {e}\n")
                import traceback
                traceback.print_exc(file=f)
            # On error, let through
            print(json.dumps({
                "continue": True,
                "suppressOutput": True,
                "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}
            }))
            return 0
            
    except Exception as e:
        with open(debug_log, "a") as f:
            f.write(f"FATAL ERROR: {type(e).__name__}: {e}\n")
        print(json.dumps({
            "continue": True,
            "suppressOutput": True,
            "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}
        }))
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
