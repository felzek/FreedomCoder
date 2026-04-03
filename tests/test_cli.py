from pathlib import Path

from freedomcoder.cli import main


def test_profiles_list_smoke(capsys) -> None:
    assert main(["profiles", "list"]) == 0
    out = capsys.readouterr().out
    assert "flagship:" in out
    assert "constrained:" in out


def test_task_print_prompt_smoke(tmp_path: Path, monkeypatch, capsys) -> None:
    (tmp_path / "AGENTS.md").write_text("no fake claims", encoding="utf-8")
    (tmp_path / "sample.py").write_text("print('hello')\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert (
        main(
            [
                "task",
                "--files",
                "sample.py",
                "--print-prompt",
                "Review this sample file.",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "Repository instructions" in out
    assert "sample.py" in out
