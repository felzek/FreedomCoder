# Happy Path

Example task flow:

1. Inspect the flagship profile.
2. Download the recommended quant.
3. Create an Ollama model.
4. Run a focused task against two or three specific files.

Example command:

```powershell
uv run freedomcoder task `
  --model freedomcoder-27b-q4km `
  --files src\freedomcoder\cli.py src\freedomcoder\profiles.py `
  --mode review `
  "Review how profile selection is handled and call out the smallest high-value fix."
```
