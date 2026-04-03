from __future__ import annotations

import os
import tomllib
from pathlib import Path

from freedomcoder.errors import ConfigurationError
from freedomcoder.models import Settings


def find_upwards(filename: str, *, start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / filename
        if candidate.is_file():
            return candidate
    return None


def load_settings(*, start: Path | None = None) -> Settings:
    config_path = find_upwards("freedomcoder.toml", start=start)
    data: dict[str, object] = {}
    if config_path is not None:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))

    runtime = _expect_mapping(data.get("runtime"), "runtime")
    agent = _expect_mapping(data.get("agent"), "agent")

    default_profile = _env_or_value(
        "FREEDOMCODER_DEFAULT_PROFILE", data.get("default_profile"), "flagship"
    )
    ollama_host = _env_or_value(
        "FREEDOMCODER_OLLAMA_HOST", runtime.get("ollama_host"), "http://127.0.0.1:11434"
    )
    default_model = _env_or_value(
        "FREEDOMCODER_DEFAULT_MODEL", runtime.get("default_model"), None
    )
    max_context_chars = int(
        _env_or_value(
            "FREEDOMCODER_MAX_CONTEXT_CHARS",
            agent.get("max_context_chars"),
            24_000,
        )
    )
    max_file_bytes = int(
        _env_or_value(
            "FREEDOMCODER_MAX_FILE_BYTES",
            agent.get("max_file_bytes"),
            12_000,
        )
    )
    instructions_path = _env_or_value(
        "FREEDOMCODER_INSTRUCTIONS_PATH",
        agent.get("instructions_path"),
        "AGENTS.md",
    )
    return Settings(
        default_profile=str(default_profile),
        ollama_host=str(ollama_host),
        default_model=str(default_model) if default_model else None,
        max_context_chars=max_context_chars,
        max_file_bytes=max_file_bytes,
        instructions_path=str(instructions_path),
        config_path=config_path,
    )


def load_project_instructions(settings: Settings, *, start: Path | None = None) -> tuple[Path | None, str]:
    current = (start or Path.cwd()).resolve()
    configured = Path(settings.instructions_path)
    if configured.is_absolute():
        candidate = configured
    else:
        candidate = current / configured
        if not candidate.is_file():
            candidate = find_upwards(settings.instructions_path, start=current)
    if candidate is None or not candidate.is_file():
        return None, ""
    return candidate, candidate.read_text(encoding="utf-8")


def _env_or_value(name: str, value: object, default: object) -> object:
    return os.getenv(name, value if value is not None else default)


def _expect_mapping(value: object, name: str) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"Expected [{name}] to be a TOML table.")
    return value
