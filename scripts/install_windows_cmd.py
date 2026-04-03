from __future__ import annotations

from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    target_dir = Path.home() / ".local" / "bin"
    target_dir.mkdir(parents=True, exist_ok=True)

    exe = repo_root / ".venv" / "Scripts" / "freedomcoder.exe"
    if not exe.is_file():
        raise SystemExit(f"FreedomCoder executable not found at {exe}. Run `uv sync` first.")

    cmd_path = target_dir / "freedomcoder.cmd"
    cmd_path.write_text(
        f'@echo off\nset "FREEDOMCODER_REPO={repo_root}"\n"{exe}" %*\n',
        encoding="ascii",
    )
    print(cmd_path)


if __name__ == "__main__":
    main()
