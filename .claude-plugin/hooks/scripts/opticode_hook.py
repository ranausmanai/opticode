#!/usr/bin/env python3
"""Claude Code Plugin Hook for opticode."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

def _ensure_imports(project_root: Path) -> None:
    try:
        import opticode
        return
    except ImportError:
        pass
    src_path = project_root / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))

def main() -> int:
    event = json.loads(sys.stdin.read() or "{}")
    prompt = event.get("user_prompt", "") or event.get("prompt", "")
    
    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
    
    try:
        _ensure_imports(project_root)
        from opticode.optimizer import optimize_request
        from opticode.repo_context import init_repo_context, update_history
        
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
        # On error, let prompt through
        print(json.dumps({
            "continue": True,
            "suppressOutput": True,
            "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}
        }))
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
