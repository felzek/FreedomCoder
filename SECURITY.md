# Security Policy

## Scope

FreedomCoder is a local-first developer tool. It does not ship model weights, remote execution infrastructure, or secret storage.

## Reporting

If you find a security issue in the codebase, please report it privately to the maintainers before opening a public issue.

## Safe Usage Notes

- Do not paste secrets into prompts.
- Do not commit downloaded GGUF files into the repository.
- Review model output before applying it to code.
- Treat local model responses as untrusted suggestions, not guaranteed-safe actions.

## What We Take Seriously

- Path handling bugs
- Unsafe subprocess behavior
- Config parsing issues that could read or write unexpected files
- Supply-chain concerns in the download workflow
