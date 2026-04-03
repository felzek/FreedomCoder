from __future__ import annotations

import json
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from freedomcoder.errors import RuntimeIntegrationError
from freedomcoder.models import ModelProfile


DEFAULT_SYSTEM_PROMPT = """You are FreedomCoder, a local coding assistant.
Work from the supplied task and file context only.
Prefer small, safe diffs.
Say clearly when information is missing.
Do not invent test results, benchmarks, or hidden file contents."""


def render_modelfile(
    profile: ModelProfile,
    *,
    source_ref: str,
    context_window: int,
    system_prompt: str | None = None,
) -> str:
    defaults = profile.generation_defaults
    prompt = (system_prompt or DEFAULT_SYSTEM_PROMPT).strip()
    template = """{{- if .System }}<|im_start|>system
{{ .System }}
{{- if .Tools }}

# Tools

You may call one or more functions to assist with the user query.
You are provided with function signatures below.

{{- range .Tools }}
{"type":"function","function":{"name":"{{ .Function.Name }}","description":"{{ .Function.Description }}","parameters":{{ .Function.Parameters }}}}
{{- end }}
{{- end }}<|im_end|>
{{ end }}
{{- range .Messages }}
{{- if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{- else if eq .Role "assistant" }}<|im_start|>assistant
{{- if .Content }}{{ .Content }}{{ end }}
{{- if .ToolCalls }}
{{- range .ToolCalls }}
<tool_call>
{"name":"{{ .Function.Name }}","arguments":{{ .Function.Arguments }}}
</tool_call>
{{- end }}
{{- end }}<|im_end|>
{{- else if eq .Role "tool" }}<|im_start|>user
<tool_response>
{{ .Content }}
</tool_response><|im_end|>
{{- end }}
{{- end }}<|im_start|>assistant
<think>
</think>
"""
    return (
        f"FROM {source_ref}\n\n"
        f'SYSTEM """\n{prompt}\n"""\n\n'
        f'TEMPLATE """\n{template}\n"""\n\n'
        f"PARAMETER num_ctx {context_window}\n"
        f"PARAMETER temperature {defaults.temperature}\n"
        f"PARAMETER top_p {defaults.top_p}\n"
        f"PARAMETER top_k {defaults.top_k}\n"
        f"PARAMETER repeat_penalty {defaults.repetition_penalty}\n"
        f'PARAMETER stop "<|im_start|>"\n'
        f'PARAMETER stop "<|im_end|>"\n'
    )


def create_model(*, name: str, modelfile_text: str, modelfile_out: Path | None = None) -> Path:
    if modelfile_out is not None:
        target = modelfile_out.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(modelfile_text, encoding="utf-8")
        _run_create(name=name, modelfile=target)
        return target

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".Modelfile", delete=False
    ) as handle:
        handle.write(modelfile_text)
        temp_path = Path(handle.name)
    _run_create(name=name, modelfile=temp_path)
    return temp_path


def ollama_tags(host: str) -> dict[str, object]:
    url = f"{host.rstrip('/')}/api/tags"
    request = urllib.request.Request(url, method="GET")
    return _json_request(request)


def ollama_model_names(host: str) -> set[str]:
    response = ollama_tags(host)
    models = response.get("models", [])
    if not isinstance(models, list):
        return set()
    names: set[str] = set()
    for model in models:
        if isinstance(model, dict):
            name = model.get("name")
            if isinstance(name, str):
                names.add(name)
    return names


def chat(*, host: str, model: str, prompt: str, options: dict[str, int | float]) -> str:
    url = f"{host.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": options,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    response = _json_request(request)
    try:
        return str(response["message"]["content"]).strip()
    except KeyError as exc:
        raise RuntimeIntegrationError("Ollama chat response did not contain message content.") from exc


def _run_create(*, name: str, modelfile: Path) -> None:
    completed = subprocess.run(
        ["ollama", "create", name, "-f", str(modelfile)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeIntegrationError(
            f"ollama create failed for {name!r}: {completed.stderr.strip() or completed.stdout.strip()}"
        )


def _json_request(request: urllib.request.Request) -> dict[str, object]:
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeIntegrationError(f"Failed to reach Ollama: {exc.reason}") from exc
