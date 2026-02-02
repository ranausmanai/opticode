#!/usr/bin/env python3
"""Quick evaluation: Does opticode actually improve prompts?"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from opticode.optimizer import optimize_request
from opticode.repo_context import init_repo_context

# Test cases: (input, criteria_for_good_output)
TEST_CASES = [
    {
        "name": "vague_dashboard",
        "input": "add dashboard or graphic",
        "check": lambda r: r.clarifying_question or (r.prompt and ("src/" in r.prompt or "component" in r.prompt.lower()))
    },
    {
        "name": "vague_bug_fix", 
        "input": "fix the bug",
        "check": lambda r: r.clarifying_question or (r.prompt and "specific" in r.prompt.lower())
    },
    {
        "name": "clear_feature",
        "input": "Add error handling to cache.py",
        "check": lambda r: r.prompt and "cache.py" in r.prompt and not r.clarifying_question
    },
    {
        "name": "vague_tests",
        "input": "add tests",
        "check": lambda r: r.clarifying_question or (r.prompt and ("jest" in r.prompt.lower() or "pytest" in r.prompt.lower()))
    },
    {
        "name": "vague_optimize",
        "input": "make it faster",
        "check": lambda r: r.clarifying_question or (r.prompt and ("performance" in r.prompt.lower() or "specific" in r.prompt.lower()))
    },
    {
        "name": "comparison",
        "input": "should we use redis or postgres",
        "check": lambda r: r.clarifying_question is not None  # Should ask for clarification
    },
    {
        "name": "filler_words",
        "input": "umm maybe add like some logging or something",
        "check": lambda r: r.clarifying_question or (r.prompt and "like" not in r.prompt.lower() and "something" not in r.prompt.lower())
    },
    {
        "name": "clear_refactor",
        "input": "Refactor cli.py to use argparse subparsers",
        "check": lambda r: r.prompt and "cli.py" in r.prompt and "argparse" in r.prompt.lower()
    }
]

def run_eval():
    ctx = init_repo_context(Path.cwd())
    
    print("=" * 70)
    print("OPTICODE QUICK EVAL (8 test cases)")
    print("=" * 70)
    print()
    
    passed = 0
    results = []
    
    for test in TEST_CASES:
        result = optimize_request(test["input"], ctx)
        success = test["check"](result)
        
        status = "✓ PASS" if success else "✗ FAIL"
        passed += 1 if success else 0
        
        print(f"{status} | {test['name']}")
        print(f"   Input: \"{test['input']}\"")
        
        if result.clarifying_question:
            print(f"   → Clarified: {result.clarifying_question[:60]}...")
        else:
            output = result.prompt[:80].replace('\n', ' ')
            print(f"   → Output: {output}...")
        
        results.append({
            "name": test["name"],
            "passed": success,
            "input": test["input"],
            "clarified": result.clarifying_question is not None,
            "output": result.prompt[:100] if result.prompt else "N/A"
        })
        print()
    
    print("=" * 70)
    print(f"SCORE: {passed}/{len(TEST_CASES)} ({passed/len(TEST_CASES)*100:.0f}%)")
    print("=" * 70)
    
    # Summary
    print("\nBREAKDOWN:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {len(TEST_CASES) - passed}")
    
    if passed < len(TEST_CASES):
        print("\nFAILED CASES:")
        for r in results:
            if not r["passed"]:
                print(f"  - {r['name']}: {r['input'][:40]}...")
    
    return passed / len(TEST_CASES)

if __name__ == "__main__":
    score = run_eval()
    print(f"\nOverall: {score*100:.0f}%")
    
    if score >= 0.75:
        print("✓ Good enough!")
    elif score >= 0.5:
        print("⚠ Needs improvement")
    else:
        print("✗ Not working well")
