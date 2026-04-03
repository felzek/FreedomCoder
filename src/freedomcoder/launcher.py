from __future__ import annotations

import os
import shlex
import stat
import sys
from pathlib import Path

from freedomcoder.errors import RuntimeIntegrationError


def current_platform() -> str:
    return "windows" if os.name == "nt" else "posix"


def default_target_dir(*, platform: str | None = None) -> Path:
    _ = platform or current_platform()
    return Path.home() / ".local" / "bin"


def launcher_name(*, platform: str | None = None) -> str:
    return "freedomcoder.cmd" if (platform or current_platform()) == "windows" else "freedomcoder"


def venv_executable(*, repo_root: Path, platform: str | None = None) -> Path:
    normalized = platform or current_platform()
    if normalized == "windows":
        return repo_root / ".venv" / "Scripts" / "freedomcoder.exe"
    return repo_root / ".venv" / "bin" / "freedomcoder"


def render_launcher(*, repo_root: Path, platform: str | None = None) -> str:
    normalized = platform or current_platform()
    executable = venv_executable(repo_root=repo_root, platform=normalized)
    if not executable.is_file():
        raise RuntimeIntegrationError(
            f"FreedomCoder executable not found at {executable}. Run `uv sync` first."
        )

    if normalized == "windows":
        return (
            "@echo off\n"
            f'set "FREEDOMCODER_REPO={repo_root}"\n'
            f'"{executable}" %*\n'
        )

    quoted_repo = shlex.quote(str(repo_root))
    quoted_executable = shlex.quote(str(executable))
    return (
        "#!/usr/bin/env sh\n"
        f"export FREEDOMCODER_REPO={quoted_repo}\n"
        f'exec {quoted_executable} "$@"\n'
    )


def install_launcher(
    *,
    repo_root: Path | None = None,
    target_dir: Path | None = None,
    platform: str | None = None,
) -> Path:
    normalized = platform or current_platform()
    resolved_repo = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    destination_dir = (target_dir or default_target_dir(platform=normalized)).resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination = destination_dir / launcher_name(platform=normalized)
    destination.write_text(
        render_launcher(repo_root=resolved_repo, platform=normalized),
        encoding="ascii",
    )
    if normalized != "windows":
        mode = destination.stat().st_mode
        destination.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return destination


def path_contains(directory: Path) -> bool:
    target = directory.resolve()
    parts = [Path(part).resolve() for part in os.getenv("PATH", "").split(os.pathsep) if part]
    return target in parts


def path_hint(*, directory: Path, platform: str | None = None) -> str:
    normalized = platform or current_platform()
    if normalized == "windows":
        return f"Add {directory} to your PATH if the shell cannot find `freedomcoder` yet."
    return f'Add `export PATH="{directory}:$PATH"` to your shell profile if needed.'
