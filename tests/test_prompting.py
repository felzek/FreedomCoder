from pathlib import Path

from freedomcoder.prompting import build_task_prompt, collect_file_contexts


def test_collect_file_contexts_respects_file_limit(tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    sample.write_text("print('x')\n" * 50, encoding="utf-8")

    contexts = collect_file_contexts(
        [sample],
        max_file_bytes=40,
        max_context_chars=200,
    )

    assert len(contexts) == 1
    assert contexts[0].truncated is True


def test_build_task_prompt_includes_agents_and_paths(tmp_path: Path) -> None:
    sample = tmp_path / "module.py"
    sample.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    contexts = collect_file_contexts(
        [sample],
        max_file_bytes=500,
        max_context_chars=500,
    )

    prompt = build_task_prompt(
        task="Suggest the smallest safe refactor.",
        mode="patch",
        agents_text="Prefer small diffs.",
        file_contexts=contexts,
    )

    assert "Prefer small diffs." in prompt
    assert "module.py" in prompt
    assert "Response contract:" in prompt
