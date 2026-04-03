from pathlib import Path
import os

from freedomcoder.launcher import (
    install_launcher,
    launcher_name,
    path_hint,
    render_launcher,
)


def test_render_windows_launcher_uses_cmd_wrapper(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    exe = repo / ".venv" / "Scripts"
    exe.mkdir(parents=True)
    (exe / "freedomcoder.exe").write_text("binary", encoding="ascii")

    text = render_launcher(repo_root=repo, platform="windows")

    assert text.startswith("@echo off")
    assert "freedomcoder.exe" in text
    assert "FREEDOMCODER_REPO" in text


def test_render_posix_launcher_uses_exec_wrapper(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    exe = repo / ".venv" / "bin"
    exe.mkdir(parents=True)
    (exe / "freedomcoder").write_text("binary", encoding="ascii")

    text = render_launcher(repo_root=repo, platform="posix")

    assert text.startswith("#!/usr/bin/env sh")
    assert 'exec ' in text
    assert ' "$@"' in text


def test_install_launcher_creates_executable_on_posix(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    exe_dir = repo / ".venv" / "bin"
    exe_dir.mkdir(parents=True)
    (exe_dir / "freedomcoder").write_text("binary", encoding="ascii")
    target_dir = tmp_path / "bin"

    installed = install_launcher(repo_root=repo, target_dir=target_dir, platform="posix")

    assert installed == target_dir / launcher_name(platform="posix")
    assert installed.is_file()
    assert installed.read_text(encoding="ascii").startswith("#!/usr/bin/env sh")
    if os.name != "nt":
        assert installed.stat().st_mode & 0o111


def test_path_hint_mentions_local_bin() -> None:
    hint = path_hint(directory=Path.home() / ".local" / "bin", platform="posix")
    assert ".local" in hint
    assert "bin" in hint
