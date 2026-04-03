import pytest

from freedomcoder.claude_code import ensure_model_available, format_shell_snippet
from freedomcoder.errors import RuntimeIntegrationError


def test_ensure_model_available_accepts_latest_suffix(monkeypatch) -> None:
    monkeypatch.setattr(
        "freedomcoder.claude_code.ollama_model_names",
        lambda host: {"demo-model:latest"},
    )
    ensure_model_available(host="http://127.0.0.1:11434", model="demo-model")


def test_ensure_model_available_raises_for_missing_model(monkeypatch) -> None:
    monkeypatch.setattr(
        "freedomcoder.claude_code.ollama_model_names",
        lambda host: {"other-model:latest"},
    )
    with pytest.raises(RuntimeIntegrationError):
        ensure_model_available(host="http://127.0.0.1:11434", model="demo-model")


def test_format_shell_snippet_includes_claude_command() -> None:
    text = format_shell_snippet(
        shell="powershell",
        host="http://127.0.0.1:11434",
        model="demo-model",
        extra_args=["-p", "say hi"],
    )
    assert '$env:ANTHROPIC_BASE_URL="http://127.0.0.1:11434"' in text
    assert 'claude --model demo-model -p "say hi"' in text
