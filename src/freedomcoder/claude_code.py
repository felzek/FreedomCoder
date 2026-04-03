from __future__ import annotations

import os
import shutil
import subprocess

from freedomcoder.errors import RuntimeIntegrationError
from freedomcoder.ollama import ollama_model_names


def claude_binary() -> str:
    binary = shutil.which("claude")
    if binary is None:
        raise RuntimeIntegrationError(
            "Claude Code is not installed or not on PATH. Install it before using this integration."
        )
    return binary


def claude_version() -> str:
    binary = claude_binary()
    completed = subprocess.run(
        [binary, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (completed.stdout or completed.stderr).strip() or "unknown"


def claude_environment(*, host: str) -> dict[str, str]:
    return {
        "ANTHROPIC_AUTH_TOKEN": "ollama",
        "ANTHROPIC_API_KEY": "",
        "ANTHROPIC_BASE_URL": host,
    }


def build_launch_command(*, model: str, extra_args: list[str] | None = None) -> list[str]:
    return [claude_binary(), "--model", model, *(extra_args or [])]


def ensure_model_available(*, host: str, model: str) -> None:
    names = ollama_model_names(host)
    normalized_names = {name.removesuffix(":latest") for name in names}
    if model not in names and model.removesuffix(":latest") not in normalized_names:
        available = ", ".join(sorted(names)) if names else "none"
        raise RuntimeIntegrationError(
            f"Ollama model {model!r} was not found on {host}. "
            f"Available models: {available}. "
            "Create the model first with `freedomcoder ollama create ...` or choose an installed model."
        )


def format_shell_snippet(
    *,
    shell: str,
    host: str,
    model: str,
    extra_args: list[str] | None = None,
) -> str:
    args = " ".join(_quote_for_shell(arg, shell) for arg in build_launch_command(model=model, extra_args=extra_args)[1:])
    if shell == "cmd":
        return (
            f"set ANTHROPIC_AUTH_TOKEN=ollama\n"
            f"set ANTHROPIC_API_KEY=\n"
            f"set ANTHROPIC_BASE_URL={host}\n"
            f"claude {args}"
        )
    if shell == "bash":
        return (
            "export ANTHROPIC_AUTH_TOKEN=ollama\n"
            'export ANTHROPIC_API_KEY=""\n'
            f'export ANTHROPIC_BASE_URL="{host}"\n'
            f"claude {args}"
        )
    return (
        '$env:ANTHROPIC_AUTH_TOKEN="ollama"\n'
        '$env:ANTHROPIC_API_KEY=""\n'
        f'$env:ANTHROPIC_BASE_URL="{host}"\n'
        f"claude {args}"
    )


def launch(
    *,
    host: str,
    model: str,
    extra_args: list[str] | None = None,
) -> int:
    env = os.environ.copy()
    env.update(claude_environment(host=host))
    completed = subprocess.run(
        build_launch_command(model=model, extra_args=extra_args),
        env=env,
        check=False,
    )
    return int(completed.returncode)


def _quote_for_shell(value: str, shell: str) -> str:
    if value == "":
        return '""'
    if shell == "cmd":
        if any(char in value for char in ' \t"'):
            return f'"{value.replace("\"", "\"\"")}"'
        return value
    if any(char in value for char in ' \t"'):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value
