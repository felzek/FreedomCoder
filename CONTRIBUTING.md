# Contributing

Thanks for considering a contribution to FreedomCoder.

## Ground Rules

- Keep the repository model-centered.
- Prefer small, reviewable changes over sweeping refactors.
- Match documentation to actual behavior.
- Do not overstate local hardware capability.
- Preserve the provenance language around the Heretic model lineage.

## Local Setup

```powershell
uv sync
```

Run the focused checks before sending changes:

```powershell
uv run pytest
```

## Contribution Expectations

- Add or update tests for meaningful behavior changes.
- Keep docs and examples in sync with the CLI.
- Avoid adding heavy dependencies unless they remove real complexity.
- Do not commit GGUF files, local caches, or machine-specific paths.

## Docs Standard

If a feature is incomplete, say so directly. We prefer a narrower, honest repo over a wider misleading one.
