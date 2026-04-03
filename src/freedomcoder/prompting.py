from __future__ import annotations

from pathlib import Path

from freedomcoder.errors import ConfigurationError
from freedomcoder.models import FileContext


def collect_file_contexts(
    paths: list[Path],
    *,
    max_file_bytes: int,
    max_context_chars: int,
) -> list[FileContext]:
    unique_paths: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        unique_paths.append(resolved)
        seen.add(resolved)

    contexts: list[FileContext] = []
    used_chars = 0
    for path in unique_paths:
        if not path.is_file():
            raise ConfigurationError(f"Context file does not exist: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        encoded = text.encode("utf-8")
        truncated = False
        if len(encoded) > max_file_bytes:
            text = encoded[:max_file_bytes].decode("utf-8", errors="ignore")
            truncated = True
        remaining = max_context_chars - used_chars
        if remaining <= 0:
            break
        if len(text) > remaining:
            text = text[:remaining]
            truncated = True
        contexts.append(FileContext(path=path, content=text, truncated=truncated))
        used_chars += len(text)
    return contexts


def build_task_prompt(
    *,
    task: str,
    mode: str,
    agents_text: str,
    file_contexts: list[FileContext],
) -> str:
    sections = [
        "You are working inside a local code repository.",
        "Use only the task description, AGENTS instructions, and supplied file context.",
        "Do not claim to have inspected files that were not provided.",
    ]
    if agents_text.strip():
        sections.append(f"Repository instructions (AGENTS.md):\n{agents_text.strip()}")
    if file_contexts:
        blocks: list[str] = []
        for context in file_contexts:
            suffix = "\n[truncated]" if context.truncated else ""
            blocks.append(
                f"Path: {context.path.as_posix()}\n```text\n{context.content}\n```{suffix}"
            )
        sections.append("Supplied file context:\n" + "\n\n".join(blocks))
    sections.append(f"Task mode: {mode}")
    sections.append(f"User task:\n{task.strip()}")
    sections.append(_response_contract(mode))
    return "\n\n".join(sections)


def _response_contract(mode: str) -> str:
    if mode == "review":
        return (
            "Response contract:\n"
            "- findings first, ordered by severity\n"
            "- cite file paths when possible\n"
            "- keep the summary brief"
        )
    if mode == "plan":
        return (
            "Response contract:\n"
            "- give a short implementation plan\n"
            "- call out key risks or assumptions\n"
            "- suggest the smallest useful validation"
        )
    return (
        "Response contract:\n"
        "- prefer the smallest safe patch direction\n"
        "- include a unified diff when practical\n"
        "- say exactly what is missing if a safe diff is not possible"
    )
