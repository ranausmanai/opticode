#!/usr/bin/env python3
"""Claude Code Plugin Hook for opticode."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

def _ensure_imports() -> Path:
    """Ensure opticode can be imported, return plugin root."""
    # Get plugin root from environment or infer from script location
    plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", 
                                     Path(__file__).parent.parent.parent))
    
    # Try importing opticode from various locations
    try:
        import opticode
        return plugin_root
    except ImportError:
        pass
    
    # Try from plugin's src directory
    src_path = plugin_root / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        try:
            import opticode
            return plugin_root
        except ImportError:
            pass
    
    # Try from current working directory (if in a project with opticode)
    cwd_src = Path.cwd() / "src"
    if cwd_src.exists():
        sys.path.insert(0, str(cwd_src))
        try:
            import opticode
            return Path.cwd()
        except ImportError:
            pass
    
    return plugin_root

def main() -> int:
    event = json.loads(sys.stdin.read() or "{}")
    prompt = event.get("user_prompt", "") or event.get("prompt", "")
    
    plugin_root = _ensure_imports()
    
    try:
        from opticode.optimizer import optimize_request
        from opticode.repo_context import init_repo_context, update_history
        
        # Use current working directory as project root
        project_root = Path.cwd()
        ctx = init_repo_context(project_root)
        result = optimize_request(prompt, ctx, quality=False)
        
        if result.clarifying_question:
            print(json.dumps({
                "continue": False,
                "stopReason": result.clarifying_question,
                "suppressOutput": True,
                "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}
            }))
            return 0
        
        update_history(ctx, result.prompt)
        print(json.dumps({
            "continue": True,
            "suppressOutput": True,
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": result.prompt
            }
        }))
        return 0
        
    except Exception as e:
        # On error, show the error and let prompt through
        # This helps debug issues
        import traceback
        error_msg = f"opticode error: {str(e)}"
        # Uncomment for debugging: traceback.print_exc()
        print(json.dumps({
            "continue": True,
            "suppressOutput": True,
            "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}
        }))
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
