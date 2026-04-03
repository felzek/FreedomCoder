from pathlib import Path

from freedomcoder.config import load_project_instructions, load_settings


def test_load_settings_reads_project_config(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "freedomcoder.toml"
    config.write_text(
        """
default_profile = "constrained"

[runtime]
ollama_host = "http://localhost:9999"
default_model = "demo-model"

[agent]
max_context_chars = 1234
max_file_bytes = 456
instructions_path = "AGENTS.md"
""".strip(),
        encoding="utf-8",
    )
    nested = tmp_path / "nested" / "deeper"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    settings = load_settings(start=Path.cwd())

    assert settings.config_path == config
    assert settings.default_profile == "constrained"
    assert settings.ollama_host == "http://localhost:9999"
    assert settings.default_model == "demo-model"
    assert settings.max_context_chars == 1234
    assert settings.max_file_bytes == 456


def test_load_project_instructions_walks_upward(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "AGENTS.md").write_text("keep diffs small", encoding="utf-8")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    settings = load_settings(start=Path.cwd())
    path, text = load_project_instructions(settings, start=Path.cwd())

    assert path == tmp_path / "AGENTS.md"
    assert "keep diffs small" in text
