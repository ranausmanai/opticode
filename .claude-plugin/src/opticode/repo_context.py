from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class RepoContext:
    root: Path
    opticode_dir: Path
    repo_summary_path: Path
    facts_path: Path
    history_path: Path


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return current


def init_repo_context(start: Path) -> RepoContext:
    root = find_repo_root(start)
    opticode_dir = root / ".opticode"
    repo_summary_path = opticode_dir / "repo_summary.txt"
    facts_path = opticode_dir / "facts.json"
    history_path = opticode_dir / "history.json"
    opticode_dir.mkdir(parents=True, exist_ok=True)
    repo_summary_path.write_text(build_repo_summary(root), encoding="utf-8")
    if not facts_path.exists():
        facts_path.write_text(json.dumps({"facts": []}, indent=2), encoding="utf-8")
    if not history_path.exists():
        history_path.write_text(json.dumps({"history": {}}, indent=2), encoding="utf-8")
    return RepoContext(
        root=root,
        opticode_dir=opticode_dir,
        repo_summary_path=repo_summary_path,
        facts_path=facts_path,
        history_path=history_path,
    )


def build_repo_summary(root: Path) -> str:
    entries = []
    for item in sorted(root.iterdir(), key=lambda p: p.name):
        if item.name in {".git", ".opticode"}:
            continue
        hint = hint_for_path(item)
        entries.append(f"{item.name} - {hint}")
    if not entries:
        entries.append("(empty repo)")
    return "\n".join(entries) + "\n"


def hint_for_path(path: Path) -> str:
    name = path.name.lower()
    if path.is_dir():
        if name == "src":
            return "source code"
        if name in {"tests", "test"}:
            return "tests"
        if name in {"docs", "doc"}:
            return "documentation"
        return "dir"
    if name in {"readme.md", "readme.rst"}:
        return "project overview"
    if name == "pyproject.toml":
        return "python project config"
    if name == "package.json":
        return "node project config"
    if name == "requirements.txt":
        return "python dependencies"
    if name.endswith(".md"):
        return "docs"
    if name.endswith(".py"):
        return "python file"
    return "file"


def load_facts(ctx: RepoContext) -> List[str]:
    try:
        data = json.loads(ctx.facts_path.read_text(encoding="utf-8"))
        facts = data.get("facts", [])
        if isinstance(facts, list):
            return [str(f).strip() for f in facts if str(f).strip()]
    except Exception:
        return []
    return []


def load_repo_summary(ctx: RepoContext, max_lines: int = 6) -> List[str]:
    try:
        lines = ctx.repo_summary_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    lines = [ln.strip() for ln in lines if ln.strip()]
    return lines[:max_lines]


def update_history(ctx: RepoContext, optimized_prompt: str) -> None:
    digest = hashlib.sha256(optimized_prompt.encode("utf-8")).hexdigest()
    try:
        data = json.loads(ctx.history_path.read_text(encoding="utf-8"))
    except Exception:
        data = {"history": {}}
    history = data.get("history", {})
    if not isinstance(history, dict):
        history = {}
    history[ctx.root.as_posix()] = digest
    data["history"] = history
    ctx.history_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    prompt_path = ctx.opticode_dir / "prompt_history.json"
    try:
        prompt_data = json.loads(prompt_path.read_text(encoding="utf-8"))
    except Exception:
        prompt_data = {"prompts": []}
    prompts = prompt_data.get("prompts", [])
    if not isinstance(prompts, list):
        prompts = []
    prompts.append({"prompt": optimized_prompt})
    prompt_data["prompts"] = prompts[-50:]
    prompt_path.write_text(json.dumps(prompt_data, indent=2), encoding="utf-8")


def extract_explicit_files(request: str, root: Path) -> List[str]:
    candidates = []
    parts = request.replace("\n", " ").split()
    for part in parts:
        token = part.strip("'\"()[]{}.,:;")
        if "." in token or "/" in token:
            if any(token.endswith(ext) for ext in [".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml"]):
                candidates.append(token)
    found = []
    for c in candidates:
        path = (root / c).resolve() if not os.path.isabs(c) else Path(c)
        try:
            within_root = path == root or root in path.parents
            if path.exists() and path.is_file() and within_root:
                found.append(path.relative_to(root).as_posix())
        except Exception:
            continue
    return sorted(set(found))


def infer_files(request: str, root: Path) -> List[str]:
    request_l = request.lower()
    inferred = []
    mapping = [
        ("cli", "src/opticode/cli.py"),
        ("optimizer", "src/opticode/optimizer.py"),
        ("context", "src/opticode/repo_context.py"),
        ("cache", "src/opticode/cache.py"),
        ("executor", "src/opticode/executor.py"),
        ("readme", "README.md"),
        ("docs", "README.md"),
    ]
    for key, path in mapping:
        if key in request_l:
            inferred.append(path)
    inferred = [p for p in inferred if (root / p).exists()]
    return sorted(set(inferred))


def choose_files(request: str, ctx: RepoContext) -> List[str]:
    explicit = extract_explicit_files(request, ctx.root)
    if explicit:
        return explicit
    inferred = infer_files(request, ctx.root)
    if inferred:
        return inferred
    return []


def collect_snippets(root: Path, files: Iterable[str], max_lines: int = 120) -> List[str]:
    snippets: List[str] = []
    remaining = max_lines
    for rel in files:
        if remaining <= 0:
            break
        path = root / rel
        if not path.exists() or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        take = min(30, remaining, len(lines))
        if take <= 0:
            continue
        snippet = [f"{rel} (first {take} lines):"]
        snippet.extend(lines[:take])
        snippets.append("\n".join(snippet))
        remaining -= take
    return snippets


def get_git_diff_summary(root: Path, max_lines: int = 6) -> str:
    if not (root / ".git").exists():
        return ""
    try:
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if status.returncode != 0:
            return ""
        if not status.stdout.strip():
            return ""
        diff = subprocess.run(
            ["git", "-C", str(root), "diff", "--stat"],
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [ln.strip() for ln in diff.stdout.splitlines() if ln.strip()]
        if not lines:
            return "repo: git changes present"
        lines = lines[:max_lines]
        return "repo: git diff summary: " + "; ".join(lines)
    except Exception:
        return ""


def get_git_changed_files(root: Path, max_files: int = 8) -> List[str]:
    if not (root / ".git").exists():
        return []
    try:
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if status.returncode != 0:
            return []
        files = []
        for line in status.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # Format: XY path
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                files.append(parts[1])
        return files[:max_files]
    except Exception:
        return []
