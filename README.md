# FreedomCoder

_A local-first open-source coding agent built around Qwen3.5-27B-heretic-v2._

FreedomCoder is a Windows-friendly, terminal-first coding-agent scaffold centered on the **community Heretic / decensored Qwen3.5-27B GGUF lineage**. It is built to make one thing easy and honest:

1. inspect the flagship Heretic 27B model profiles,
2. pull the right GGUF from Hugging Face,
3. turn that GGUF into a local runtime with Ollama,
4. run focused coding tasks with minimal context waste.

This repository is **model-centered first**, not a generic agent platform.

## Status

Implemented in v0.1:

- Built-in model profiles for the `Qwen3.5-27B-heretic-v2` lineage
- Quant-aware Hugging Face pull workflow
- Ollama model creation from local GGUF files
- Project `AGENTS.md` discovery and loading
- Focused task prompting that only includes the files you explicitly pass
- Basic config loading, tests, and CI

Intentionally out of scope in v0.1:

- Automated repo-wide indexing
- Automatic patch application
- Tool execution inside the model loop
- Multi-runtime orchestration beyond Ollama
- Claims of benchmark superiority or consumer-hardware magic

## Model Provenance

FreedomCoder is built around the following runtime target:

- Flagship Hugging Face GGUF target: `llmfan46/Qwen3.5-27B-heretic-v2-GGUF`

Important provenance note:

- This is a **community Heretic / decensored derivative** in the Qwen3.5-27B ecosystem.
- It is **not** an official uncensored Qwen release from Qwen.
- The constrained-memory `Q3_K_M` profile uses the same model lineage through the `mradermacher/Qwen3.5-27B-heretic-v2-GGUF` mirror because the exact `llmfan46` GGUF repo does not publish `Q3_K_M`.

## Quant Guidance

FreedomCoder treats these as the default starting points:

- `Q4_K_M`: recommended quality mode
- `Q3_K_M`: constrained-memory mode

Tradeoffs:

- `Q4_K_M` is the best default if you actually have the memory budget for a 27B local workflow.
- `Q3_K_M` exists for machines that cannot reasonably absorb `Q4_K_M`, but it is still a large model and should not be confused with a lightweight laptop path.
- Larger quants (`Q5`, `Q6`, `Q8`, BF16) require substantially more memory and are documented as such in the built-in profiles.

For the current flagship repo:

- `Q4_K_M` GGUF is published directly by `llmfan46`
- larger quants are also available
- `Q3_K_M` requires the mirror profile

## Hardware Honesty

This repository is intentionally direct about local tradeoffs:

- A 27B GGUF is heavy even before context cache growth.
- `Q4_K_M` is a serious local model, not a casual one.
- Windows users often end up in a mixed GPU + RAM path or CPU-heavy fallback.
- Wider context windows materially increase memory pressure.
- If your machine is constrained, reduce quant and context before blaming the toolchain.

FreedomCoder does **not** claim that `Qwen3.5-27B-heretic-v2` is pleasant on low-memory consumer hardware. It gives you a cleaner way to operate it if you choose to run it anyway.

## Quick Start

### 1. Install the project

```powershell
uv sync
```

### 2. Inspect built-in model profiles

```powershell
uv run freedomcoder profiles list
uv run freedomcoder profiles show flagship
uv run freedomcoder profiles show constrained
```

### 3. Download a GGUF from Hugging Face

Recommended quality:

```powershell
uv run freedomcoder pull --profile flagship --output-dir .freedomcoder\models
```

Constrained mode:

```powershell
uv run freedomcoder pull --profile constrained --output-dir .freedomcoder\models
```

### 4. Create an Ollama model from the GGUF

```powershell
uv run freedomcoder ollama create --profile flagship --gguf .freedomcoder\models\Qwen3.5-27B-heretic-v2-Q4_K_M.gguf
```

If you already have a local Ollama model and want to wrap it with FreedomCoder's tool-aware template:

```powershell
uv run freedomcoder ollama create --profile flagship --from-model qwen14b-creative-uncensored:latest --name freedomcoder-qwen14-tools
```

### 5. Run a focused coding task

```powershell
uv run freedomcoder task ^
  --model freedomcoder-27b-q4km ^
  --files src\freedomcoder\cli.py src\freedomcoder\config.py ^
  --mode patch ^
  "Suggest the smallest safe change to improve configuration error messages."
```

### 6. Launch Claude Code against the local Ollama model

Print the exact shell setup first:

```powershell
uv run freedomcoder claude-code env
```

Then launch Claude Code against the local FreedomCoder model:

```powershell
uv run freedomcoder claude-code launch
```

If you want to inspect the command without launching:

```powershell
uv run freedomcoder claude-code launch --print-only
```

If you want to target a different installed Ollama model while testing:

```powershell
uv run freedomcoder claude-code launch --model qwen14b-creative-uncensored
```

Notes:

- This integration uses Ollama's Anthropic-compatible API so Claude Code can talk to a local model.
- FreedomCoder's generated Ollama models use a tool-aware Qwen-style template so agent clients like Claude Code have a better chance of working correctly.
- Claude Code itself recommends large context windows for best results. Ollama's current Claude Code integration docs recommend at least `64k` context when hardware allows it.
- For a local 27B model, that context target can be expensive. Start smaller if needed and raise it only when the machine proves stable.

## Core Workflow

The intended v0.1 workflow is:

1. choose a built-in profile,
2. download the matching GGUF,
3. create a local Ollama model,
4. point FreedomCoder at a small set of relevant files,
5. ask for a plan, review, or patch-oriented response.

This keeps context tight and avoids the fake sophistication of a repo-wide agent that silently burns tokens on irrelevant files.

## Configuration

FreedomCoder reads an optional `freedomcoder.toml` from the current directory or its parents.

Example:

```toml
default_profile = "flagship"

[runtime]
ollama_host = "http://127.0.0.1:11434"
default_model = "freedomcoder-27b-q4km"

[agent]
max_context_chars = 24000
max_file_bytes = 12000
instructions_path = "AGENTS.md"
```

See `examples/config/freedomcoder.toml` for a fuller sample.

## CLI Overview

```text
freedomcoder doctor
freedomcoder profiles list
freedomcoder profiles show flagship
freedomcoder pull --profile flagship
freedomcoder ollama create --profile flagship --gguf <path>
freedomcoder task --model <ollama-model> --files <paths...> "<task>"
freedomcoder claude-code env
freedomcoder claude-code launch
```

## What Is Actually Implemented Now

FreedomCoder v0.1 gives you:

- profile-backed model selection
- quant-aware downloads
- Ollama import support
- AGENTS-aware prompt construction
- narrow local task execution
- Claude Code launch support through Ollama's Anthropic-compatible endpoint

It does **not** yet give you:

- autonomous shell/file tool use
- patch application
- benchmark-driven tuning
- background indexing
- editor plugins

## Validation

This repo only claims validation that was actually run. See the final implementation notes and CI workflow for the exact checks.

## Documentation Map

- Root agent rules: `AGENTS.md`
- Contribution guide: `CONTRIBUTING.md`
- Security policy: `SECURITY.md`
- Model strategy: `docs/model-profiles.md`
- Publish checklist: `docs/publish-checklist.md`
