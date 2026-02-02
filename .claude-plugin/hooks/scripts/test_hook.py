#!/usr/bin/env python3
import json
import sys

# Simple test - just block everything with a message
print(json.dumps({
    "continue": False,
    "stopReason": "HOOK IS WORKING! This is a test block.",
    "suppressOutput": True,
    "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}
}))
