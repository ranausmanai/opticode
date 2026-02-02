from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from selectors import DefaultSelector, EVENT_READ
from threading import Thread
from typing import Dict, Optional


def load_config(opticode_dir: Path) -> Dict[str, str]:
    config_path = opticode_dir / "config.json"
    defaults = {"codex_cmd": "codex exec --skip-git-repo-check {prompt}", "claude_cmd": "claude"}
    if not config_path.exists():
        return defaults
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    data = data if isinstance(data, dict) else {}
    codex_cmd = str(data.get("codex_cmd", defaults["codex_cmd"]))
    claude_cmd = str(data.get("claude_cmd", defaults["claude_cmd"]))
    return {"codex_cmd": codex_cmd, "claude_cmd": claude_cmd}


def _stream(src, dest):
    for line in iter(src.readline, ""):
        if not line:
            break
        dest.write(line)
        dest.flush()


def _build_cmd_list(cmd: str, prompt: str) -> tuple[list[str], Optional[str]]:
    tokens = shlex.split(cmd)
    if "{prompt}" not in cmd:
        return tokens, prompt

    built: list[str] = []
    for token in tokens:
        if "{prompt}" in token:
            if token == "{prompt}":
                built.append(prompt)
            else:
                built.append(token.replace("{prompt}", prompt))
        else:
            built.append(token)
    return built, None


def _run_with_pty(cmd_list: list[str], stdin_data: Optional[str]) -> int:
    try:
        import pty
    except Exception as exc:
        raise RuntimeError("PTY not available") from exc

    master_fd, slave_fd = pty.openpty()
    try:
        proc = subprocess.Popen(
            cmd_list,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
        )
    except FileNotFoundError:
        os.close(master_fd)
        os.close(slave_fd)
        raise
    finally:
        try:
            os.close(slave_fd)
        except Exception:
            pass

    if stdin_data:
        payload = stdin_data
        if not payload.endswith("\n"):
            payload += "\n"
        os.write(master_fd, payload.encode("utf-8", errors="ignore"))

    selector = DefaultSelector()
    selector.register(master_fd, EVENT_READ)

    stdin_fd = None
    try:
        stdin_fd = sys.stdin.fileno()
        selector.register(stdin_fd, EVENT_READ)
    except Exception:
        stdin_fd = None

    try:
        while True:
            if proc.poll() is not None:
                while True:
                    try:
                        data = os.read(master_fd, 4096)
                    except OSError:
                        data = b""
                    if not data:
                        break
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
                break

            events = selector.select(timeout=0.1)
            for key, _ in events:
                if key.fileobj == master_fd:
                    try:
                        data = os.read(master_fd, 4096)
                    except OSError:
                        data = b""
                    if not data:
                        continue
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
                elif stdin_fd is not None and key.fileobj == stdin_fd:
                    try:
                        data = os.read(stdin_fd, 4096)
                    except OSError:
                        data = b""
                    if not data:
                        try:
                            selector.unregister(stdin_fd)
                        except Exception:
                            pass
                        stdin_fd = None
                        continue
                    os.write(master_fd, data)
    finally:
        try:
            selector.close()
        except Exception:
            pass
        try:
            os.close(master_fd)
        except Exception:
            pass

    return proc.wait()


def run_tool(opticode_dir: Path, tool: str, prompt: str) -> int:
    cfg = load_config(opticode_dir)
    if tool == "codex":
        cmd = cfg.get("codex_cmd", "codex exec --skip-git-repo-check {prompt}")
    elif tool == "claude":
        cmd = cfg.get("claude_cmd", "claude")
    else:
        raise ValueError("tool must be 'codex' or 'claude'")

    cmd_list, stdin_data = _build_cmd_list(cmd, prompt)

    if not cmd_list:
        raise RuntimeError("Tool command is empty")

    try:
        return _run_with_pty(cmd_list, stdin_data)
    except FileNotFoundError:
        raise RuntimeError(f"Tool not installed or not found: {cmd_list[0]}")
    except Exception:
        pass

    try:
        proc = subprocess.Popen(
            cmd_list,
            stdin=subprocess.PIPE if stdin_data is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError(f"Tool not installed or not found: {cmd_list[0]}")

    threads = []
    if proc.stdout:
        t_out = Thread(target=_stream, args=(proc.stdout, sys.stdout), daemon=True)
        t_out.start()
        threads.append(t_out)
    if proc.stderr:
        t_err = Thread(target=_stream, args=(proc.stderr, sys.stderr), daemon=True)
        t_err.start()
        threads.append(t_err)

    if stdin_data is not None and proc.stdin:
        try:
            proc.stdin.write(stdin_data)
            proc.stdin.close()
        except Exception:
            pass

    for t in threads:
        t.join()

    return proc.wait()
