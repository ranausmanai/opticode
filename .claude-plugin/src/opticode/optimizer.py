from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .intent_model import analyze_request, IntentResult
from .repo_context import (
    RepoContext,
    choose_files,
    collect_snippets,
    get_git_diff_summary,
    load_facts,
    load_repo_summary,
)


@dataclass
class OptimizeResult:
    prompt: str
    clarifying_question: Optional[str] = None


def optimize_request(request: str, ctx: RepoContext, quality: bool = False) -> OptimizeResult:
    request = (request or "").strip()
    if not request:
        return OptimizeResult(prompt="", clarifying_question="What is the specific task you want performed?")

    # Use tiny LLM to understand intent and rewrite request
    intent = analyze_request(request)

    force_original, hallucination_hint = detect_hallucinated_details(request, intent.rewritten, ctx.root)
    if hallucination_hint:
        return OptimizeResult(prompt="", clarifying_question=hallucination_hint)
    
    # Check if we need clarification based on intent analysis
    if intent.needs_clarification:
        if intent.clarification_hint:
            return OptimizeResult(prompt="", clarifying_question=intent.clarification_hint)
        # Fallback to rule-based clarification
        clarify = maybe_clarify(request, ctx)
        if clarify:
            return OptimizeResult(prompt="", clarifying_question=clarify)
    
    # Use the model's rewritten request if confidence is good
    if not force_original and intent.confidence >= 0.6 and intent.rewritten:
        effective_request = intent.rewritten
    else:
        effective_request = request

    task = build_task(effective_request, request_type=intent.request_type)
    files = choose_files(effective_request, ctx)
    context_bullets: List[str] = []

    diff_summary = get_git_diff_summary(ctx.root)
    if diff_summary:
        context_bullets.append(diff_summary)

    facts = load_facts(ctx)
    if facts:
        for fact in facts[:4]:
            context_bullets.append(fact)

    summary = load_repo_summary(ctx)
    if summary:
        for line in summary[:4]:
            context_bullets.append(f"repo: {line}")

    if not context_bullets:
        context_bullets.append("repo: (no summary yet)")

    if files:
        snippets = collect_snippets(ctx.root, files, max_lines=120)
        for snippet in snippets[:2]:
            context_bullets.append(f"snippet:\n{snippet}")

    max_context = 8 if quality else 6
    if len(context_bullets) > max_context:
        context_bullets = context_bullets[:max_context]

    do_bullets = build_do_bullets(effective_request, quality=quality, request_type=intent.request_type)
    dont_bullets = build_dont_bullets(request_type=intent.request_type)
    acceptance_bullets = build_acceptance_bullets(request_type=intent.request_type)
    output_format = get_output_format(intent.request_type)

    prompt = format_prompt(
        task=task,
        context=context_bullets,
        files=files,
        do=do_bullets,
        dont=dont_bullets,
        acceptance=acceptance_bullets,
        output=output_format,
    )
    prompt = enforce_cap(prompt, task, context_bullets, files, do_bullets, dont_bullets, acceptance_bullets, output_format)
    return OptimizeResult(prompt=prompt)


def maybe_clarify(request: str, ctx: RepoContext) -> Optional[str]:
    request_l = request.lower().strip()
    words = [w for w in request_l.replace("\n", " ").split(" ") if w]
    explicit_files = choose_files(request, ctx)

    vague_terms = {
        "improve",
        "better",
        "cleanup",
        "clean",
        "optimize",
        "refactor",
        "simplify",
        "enhance",
        "fix",
        "update",
        "adjust",
        "tweak",
        "revise",
        "polish",
    }
    has_vague = any(word in vague_terms for word in words)

    if len(words) <= 4 and not explicit_files:
        return "What specific change do you want, and which file or component should it affect?"

    if has_vague and not explicit_files and "add" not in words and "implement" not in words:
        return "What specific change do you want, and where should it be applied?"

    if "it" in words and "this" in words and not explicit_files:
        return "What exactly should be changed, and in which file or component?"

    return None


def detect_hallucinated_details(request: str, rewritten: str, root: Path) -> Tuple[bool, Optional[str]]:
    if not rewritten:
        return False, None

    request_l = request.lower()
    rewritten_l = rewritten.lower()

    request_files = extract_file_tokens(request)
    rewritten_files = extract_file_tokens(rewritten)
    has_explicit_files = bool(request_files)

    if rewritten_files:
        for token in rewritten_files:
            path = (root / token).resolve() if not Path(token).is_absolute() else Path(token)
            within_root = path == root or root in path.parents
            if (token not in request_files) and (not path.exists() or not within_root):
                if has_explicit_files:
                    return True, None
                return False, "Please specify the exact file or component to change. Avoid guessing file paths."

    tech_terms = [
        "react", "vue", "svelte", "angular", "next.js", "nextjs", "nuxt",
        "django", "flask", "fastapi", "rails", "laravel", "spring",
        "dotnet", "kotlin", "swift", "electron", "react native", "recharts",
    ]
    if len(request.split()) <= 4:
        for term in tech_terms:
            if term in rewritten_l and term not in request_l:
                if has_explicit_files:
                    return True, None
                return False, "Please specify the tech stack and target file/component so I don't invent details."

    return False, None


def extract_file_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    for raw in text.replace("\n", " ").split():
        token = raw.strip("'\"()[]{}.,:;")
        if "/" in token or "." in token:
            if any(token.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".toml", ".yaml", ".yml", ".txt"]):
                tokens.append(token)
    return sorted(set(tokens))


def build_task(request: str, request_type: str = "implement") -> str:
    sentence = request.split("\n", 1)[0].strip()
    sentence = sentence.rstrip(".!")
    
    # Handle different request types
    if request_type == "compare":
        return f"Compare the following options and provide a recommendation: {sentence}."
    elif request_type == "analyze":
        return f"Analyze the following and provide findings: {sentence}."
    elif request_type == "question":
        return f"Address the following question: {sentence}."
    
    # Standard implementation tasks
    if not sentence.lower().startswith(("add ", "fix ", "update ", "implement ", "remove ", "refactor ", "create ", "compare ", "analyze ", "address ")):
        sentence = f"Implement the following: {sentence}"
    if not sentence.endswith("."):
        sentence += "."
    return sentence


def build_do_bullets(request: str, quality: bool = False, request_type: str = "implement") -> List[str]:
    bullets: List[str] = []
    req = request.lower()
    
    # Adjust bullets based on request type
    if request_type == "compare":
        bullets.append("Provide objective comparison with pros/cons")
        bullets.append("Consider trade-offs for this specific codebase")
        bullets.append("Give a clear recommendation with reasoning")
        return bullets
    
    if request_type == "analyze":
        bullets.append("Focus on code quality and potential issues")
        bullets.append("Provide actionable findings")
        bullets.append("Suggest specific improvements where applicable")
        return bullets
    
    # Standard implementation bullets
    if "readme" in req or "docs" in req:
        bullets.append("Update documentation if behavior changes")
    bullets.append("Make only the necessary code changes")
    bullets.append("Keep behavior consistent and predictable")
    if "test" in req:
        bullets.append("Add or update tests relevant to the change")
    if quality:
        bullets.append("Prefer correctness and clarity over minimal edits")
    if len(bullets) < 3:
        bullets.append("Preserve existing CLI ergonomics")
    return bullets[:7]


def build_dont_bullets(request_type: str = "implement") -> List[str]:
    if request_type == "compare":
        return [
            "Do not write any code changes",
            "Do not recommend without justification",
            "Do not ignore existing codebase constraints",
        ]
    if request_type == "analyze":
        return [
            "Do not make code changes unless explicitly asked",
            "Do not provide vague feedback",
            "Do not ignore security or performance issues",
        ]
    return [
        "Do not change unrelated files",
        "Do not add new dependencies unless required",
        "Do not add explanations or extra output",
    ]


def build_acceptance_bullets(request_type: str = "implement") -> List[str]:
    if request_type == "compare":
        return [
            "Comparison covers key decision factors",
            "Recommendation is justified with reasoning",
            "Response is actionable for the team",
        ]
    if request_type == "analyze":
        return [
            "Analysis identifies concrete issues",
            "Findings are prioritized by impact",
            "Recommendations are specific and actionable",
        ]
    return [
        "Optimized prompt follows the required format",
        "Optimized prompt stays within 4,000 characters",
        "Local .opticode context is maintained",
    ]


def get_output_format(request_type: str) -> str:
    """Get appropriate output format for request type."""
    formats = {
        "implement": "GIT_DIFF_ONLY",
        "compare": "COMPARISON_AND_RECOMMENDATION - No code changes",
        "analyze": "ANALYSIS_REPORT - Findings and recommendations only",
        "question": "ANSWER_WITH_REASONING",
        "unclear": "CLARIFICATION_NEEDED",
    }
    return formats.get(request_type, "GIT_DIFF_ONLY")


def format_prompt(
    task: str,
    context: List[str],
    files: List[str],
    do: List[str],
    dont: List[str],
    acceptance: List[str],
    output: str,
) -> str:
    files_section = "discover minimal files" if not files else "\n".join(files)
    def bullets(items: List[str]) -> str:
        return "\n".join(f"- {item}" for item in items)

    parts = [
        "TASK:",
        task,
        "",
        "CONTEXT:",
        bullets(context),
        "",
        "FILES:",
        files_section,
        "",
        "DO:",
        bullets(do),
        "",
        "DONT:",
        bullets(dont),
        "",
        "ACCEPTANCE:",
        bullets(acceptance),
        "",
        "OUTPUT:",
        output,
    ]
    return "\n".join(parts)


def enforce_cap(
    prompt: str,
    task: str,
    context: List[str],
    files: List[str],
    do: List[str],
    dont: List[str],
    acceptance: List[str],
    output: str,
) -> str:
    if len(prompt) <= 4000:
        return prompt

    context = context.copy()
    do = do.copy()

    while len(prompt) > 4000 and context:
        context.pop()
        prompt = format_prompt(task, context, files, do, dont, acceptance, output)

    while len(prompt) > 4000 and len(do) > 3:
        do.pop()
        prompt = format_prompt(task, context, files, do, dont, acceptance, output)

    if len(prompt) > 4000:
        task = task[:200].rstrip() + "."
        prompt = format_prompt(task, context, files, do, dont, acceptance, output)

    return prompt
