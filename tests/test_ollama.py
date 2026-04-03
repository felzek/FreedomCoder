from pathlib import Path

from freedomcoder.ollama import render_modelfile
from freedomcoder.profiles import load_profile


def test_render_modelfile_contains_qwen_stops(tmp_path: Path) -> None:
    profile = load_profile("flagship")
    gguf = tmp_path / "model.gguf"
    gguf.write_text("placeholder", encoding="utf-8")

    modelfile = render_modelfile(profile, gguf_path=gguf, context_window=8192)

    assert "FROM " in modelfile
    assert "PARAMETER num_ctx 8192" in modelfile
    assert 'PARAMETER stop "<|im_start|>"' in modelfile
    assert "<think>" in modelfile
