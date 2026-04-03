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


def test_claude_code_env_prints_expected_variables(capsys) -> None:
    assert main(["claude-code", "env"]) == 0
    out = capsys.readouterr().out
    assert "ANTHROPIC_AUTH_TOKEN" in out
    assert "ANTHROPIC_BASE_URL" in out
    assert "claude --model " in out


def test_claude_code_launch_print_only_uses_requested_model(monkeypatch, capsys) -> None:
    monkeypatch.setattr("freedomcoder.cli.claude_binary", lambda: "claude")
    monkeypatch.setattr("freedomcoder.cli.ensure_model_available", lambda **kwargs: None)
    assert (
        main(
            [
                "claude-code",
                "launch",
                "--model",
                "demo-model",
                "--print-only",
                "--",
                "--dangerously-skip-permissions",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "claude --model demo-model --dangerously-skip-permissions" in out


def test_no_args_default_to_claude_code_launch(monkeypatch, capsys) -> None:
    monkeypatch.setattr("freedomcoder.cli.claude_binary", lambda: "claude")
    monkeypatch.setattr(
        "freedomcoder.cli.ollama_model_names",
        lambda host: {"freedomcoder-qwen14-tools:latest"},
    )
    monkeypatch.setattr("freedomcoder.cli.ensure_model_available", lambda **kwargs: None)
    assert main(["--print-only"]) == 0
    out = capsys.readouterr().out
    assert "claude --model freedomcoder-qwen14-tools" in out


def test_install_launcher_print_only(monkeypatch, capsys) -> None:
    monkeypatch.setattr("freedomcoder.cli.path_contains", lambda directory: False)
    assert main(["install-launcher", "--print-only"]) == 0
    out = capsys.readouterr().out
    assert "freedomcoder" in out
