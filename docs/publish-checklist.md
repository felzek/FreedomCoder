# Publish Checklist

- Confirm README commands still match the CLI.
- Confirm AGENTS.md matches actual repository expectations.
- Confirm no secrets or absolute machine paths are present.
- Confirm no GGUF files or local caches are tracked.
- Confirm model provenance language is accurate and not misleading.
- Confirm the flagship profile still points at `llmfan46/Qwen3.5-27B-heretic-v2-GGUF`.
- Confirm constrained profile notes still explain the `Q3_K_M` mirror honestly.
- Run tests and record exactly what passed.
- Review CI status on both Windows and Linux.
- Ensure limitations are documented before release.
