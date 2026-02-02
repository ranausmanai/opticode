# Hello world
# Hello world
# Hello world
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
import subprocess

from .executor import run_tool
from .dashboard import run_dashboard
from .intent_model import get_model_info
from .optimizer import optimize_request
from .repo_context import init_repo_context, update_history, get_git_changed_files, get_git_diff_summary


def _read_request(args: argparse.Namespace) -> str:
    if args.request:
        return " ".join(args.request).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def cmd_optimize(args: argparse.Namespace) -> int:
    request = _read_request(args)
    ctx = init_repo_context(Path.cwd())
    result = optimize_request(request, ctx, quality=args.quality)
    if result.clarifying_question:
        print(result.clarifying_question)
        return 2
    print(result.prompt)
    update_history(ctx, result.prompt)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    request = _read_request(args)
    ctx = init_repo_context(Path.cwd())
    result = optimize_request(request, ctx, quality=args.quality)
    
    if result.clarifying_question:
        print(result.clarifying_question)
        
        # Interactive mode: allow user to clarify inline
        if args.interactive and sys.stdin.isatty():
            try:
                clarification = input("> ").strip()
                if clarification:
                    # Combine original request with clarification
                    combined = f"{request} - {clarification}"
                    print(f"\n→ Continuing with: {combined[:60]}...")
                    result = optimize_request(combined, ctx, quality=args.quality)
                    if result.clarifying_question:
                        # Still needs more clarification
                        print(result.clarifying_question)
                        return 2
                    # Got a good prompt, continue to run
                else:
                    return 2  # User gave empty response
            except (EOFError, KeyboardInterrupt):
                print("\nAborted.")
                return 130
        else:
            return 2  # Non-interactive mode, exit with hint
    
    update_history(ctx, result.prompt)
    try:
        return run_tool(ctx.opticode_dir, args.tool, result.prompt)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    info = get_model_info()
    print("opticode status")
    print("=" * 40)
    print(f"Intent model: {'✓ Available' if info['available'] else '✗ Not available'}")
    print(f"Model file: {info['model_file'] or 'Not found'}")
    print(f"Model name: {info['model_name']}")
    print(f"Model size: {info['size']}")
    if not info['available']:
        print()
        print("To enable AI-powered intent understanding:")
        print(f"  1. Download: python download_model.py")
        print(f"  2. Or: curl -L -o ~/.opticode/models/{info['model_name']} {info['download_url']}")
    if args.self_test:
        print()
        print("Self-test:")
        env = dict(os.environ)
        env.setdefault("OMP_NUM_THREADS", "1")
        env.setdefault("LLAMA_NUM_THREADS", "1")
        env.setdefault("LLAMA_METAL", "0")
        code = (
            "from opticode.intent_model import TinyIntentModel;"
            "from pathlib import Path;"
            "import sys;"
            "p=Path.home()/'.opticode/models'/sys.argv[1];"
            "m=TinyIntentModel(model_path=str(p));"
            "print('available:', m.available);"
            "print('model_file:', m.model_file);"
            "r=m.analyze('Add error handling to cache.py') if m.available else None;"
            "print('type:', r.request_type if r else 'n/a');"
            "print('confidence:', r.confidence if r else 'n/a');"
            "print('needs_clarification:', r.needs_clarification if r else 'n/a');"
        )
        model_name = info["model_name"]
        proc = subprocess.run(
            [sys.executable, "-c", code, model_name],
            env=env,
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0:
            print("✓ Model load OK")
            if proc.stdout.strip():
                print(proc.stdout.strip())
        else:
            print("✗ Model load failed")
            if proc.stderr.strip():
                print(proc.stderr.strip())
    return 0


@dataclass
class ChatMessage:
    request: str
    task: str
    files: list[str]


def _chat_history_path(ctx) -> Path:
    return ctx.opticode_dir / "chat_history.json"


def _load_chat_history(ctx) -> list[ChatMessage]:
    path = _chat_history_path(ctx)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    msgs = data.get("messages", [])
    out: list[ChatMessage] = []
    if isinstance(msgs, list):
        for m in msgs[-10:]:
            if not isinstance(m, dict):
                continue
            out.append(
                ChatMessage(
                    request=str(m.get("request", "")).strip(),
                    task=str(m.get("task", "")).strip(),
                    files=list(m.get("files", [])) if isinstance(m.get("files", []), list) else [],
                )
            )
    return out


def _save_chat_history(ctx, messages: list[ChatMessage]) -> None:
    path = _chat_history_path(ctx)
    payload = {
        "messages": [
            {"request": m.request, "task": m.task, "files": m.files} for m in messages[-10:]
        ]
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_chat_context(ctx, history: list[ChatMessage], max_lines: int = 12) -> str:
    lines: list[str] = []
    if history:
        lines.append("Recent intents:")
        for i, m in enumerate(history[-3:], start=1):
            task = m.task.replace("\n", " ").strip()
            if len(task) > 80:
                task = task[:77] + "..."
            lines.append(f"{i}) {task}")
    changed = get_git_changed_files(ctx.root)
    if changed:
        files = ", ".join(changed[:6])
        lines.append(f"Files touched: {files}")
    diff = get_git_diff_summary(ctx.root)
    if diff:
        lines.append(f"{diff}")
    if not lines:
        return ""
    # Trim to max lines
    lines = lines[:max_lines]
    return "RECENT_CONTEXT:\n" + "\n".join(f"- {ln}" for ln in lines)


def cmd_chat(args: argparse.Namespace) -> int:
    ctx = init_repo_context(Path.cwd())
    history = _load_chat_history(ctx)
    show_context = not args.no_show

    print("opticode chat (type /exit to quit, /show to toggle context, /clear to reset history)")
    while True:
        try:
            user_in = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 130
        if not user_in:
            continue
        if user_in in ("/exit", "/quit"):
            return 0
        if user_in == "/show":
            show_context = not show_context
            print(f"Context display: {'on' if show_context else 'off'}")
            continue
        if user_in == "/clear":
            history = []
            _save_chat_history(ctx, history)
            print("History cleared.")
            continue

        result = optimize_request(user_in, ctx, quality=args.quality)
        if result.clarifying_question:
            print(result.clarifying_question)
            continue

        context_block = _build_chat_context(ctx, history)
        prompt = result.prompt
        if context_block:
            prompt = context_block + "\n\n" + prompt

        if show_context and context_block:
            print(context_block)

        update_history(ctx, result.prompt)
        try:
            print("→ Sending to codex..." if args.tool == "codex" else "→ Sending to claude...")
            exit_code = run_tool(ctx.opticode_dir, args.tool, prompt)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            exit_code = 1

        files = []
        lines = result.prompt.splitlines() if result.prompt else []
        if "FILES:" in lines:
            idx = lines.index("FILES:") + 1
            while idx < len(lines):
                line = lines[idx].strip()
                if line == "DO:":
                    break
                if line and not line.endswith(":") and line != "discover minimal files":
                    files.append(line)
                idx += 1
        task_line = ""
        if len(lines) >= 2 and lines[0] == "TASK:":
            task_line = lines[1].strip()
        history.append(ChatMessage(request=user_in, task=task_line, files=files))
        _save_chat_history(ctx, history)

        if exit_code != 0:
            return exit_code


def cmd_dashboard(args: argparse.Namespace) -> int:
    ctx = init_repo_context(Path.cwd())
    run_dashboard(ctx.opticode_dir, args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opticode",
        description="Compact prompt optimizer and CLI wrapper for Codex/Claude Code",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_opt = sub.add_parser("optimize", help="Rewrite a request into a compact job spec")
    p_opt.add_argument("--quality", action="store_true", help="Include extra context when safe")
    p_opt.add_argument("request", nargs=argparse.REMAINDER, help="Free-form request")
    p_opt.set_defaults(func=cmd_optimize)

    p_run = sub.add_parser("run", help="Rewrite a request and run it through a tool")
    p_run.add_argument("--tool", choices=["codex", "claude"], required=True)
    p_run.add_argument("--quality", action="store_true", help="Include extra context when safe")
    p_run.add_argument("--interactive", "-i", action="store_true", 
                       help="Ask for clarification inline instead of exiting")
    p_run.add_argument("request", nargs=argparse.REMAINDER, help="Free-form request")
    p_run.set_defaults(func=cmd_run)

    p_status = sub.add_parser("status", help="Check opticode status and model availability")
    p_status.add_argument("--self-test", action="store_true", help="Load model in a subprocess and run a tiny probe")
    p_status.set_defaults(func=cmd_status)

    p_chat = sub.add_parser("chat", help="Interactive prompt optimizer loop")
    p_chat.add_argument("--tool", choices=["codex", "claude"], required=True)
    p_chat.add_argument("--quality", action="store_true", help="Include extra context when safe")
    p_chat.add_argument("--no-show", action="store_true", help="Do not show context block before sending")
    p_chat.set_defaults(func=cmd_chat)

    p_dash = sub.add_parser("dashboard", help="Run a local dashboard for prompt history")
    p_dash.add_argument("--port", type=int, default=7777)
    p_dash.set_defaults(func=cmd_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
