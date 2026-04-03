# AGENTS.md

This repository is optimized for coding agents that can work precisely and honestly.

## Core Rules

- Start with the smallest relevant surface area.
- Do not scan the whole repository unless the task genuinely requires it.
- Prefer targeted reads over broad exploration.
- Keep diffs small, explicit, and easy to review.
- Validate only what the change touches before expanding.
- State uncertainty plainly instead of guessing.
- Never claim tests, speed, or benchmarks you did not actually run.

## Context Discipline

- Read only the files directly relevant to the task first.
- If you need more context, widen one layer at a time.
- Prefer file-specific summaries over repo-wide narration.
- Do not include giant file dumps in prompts or reports.
- Respect the configured file and context budgets when constructing prompts.

## Change Style

- Favor composable modules over clever abstractions.
- Keep configuration explicit and boring.
- Preserve Windows-friendly behavior unless a change clearly improves portability.
- Do not introduce a plugin system, background indexer, or agent orchestration layer in v0.1.

## Validation Rules

- Run the narrowest meaningful validation first.
- If you did not run a command, say so.
- If a large integration step is too expensive to validate locally, document that limitation clearly.

## Model Provenance Rules

- Treat `Qwen3.5-27B-heretic-v2` as a community Heretic / decensored derivative.
- Do not describe it as an official uncensored Qwen release.
- Be precise about which repo publishes which quant.

## Reporting

Every substantial task report should include:

1. what changed
2. what was validated
3. what remains unvalidated
4. any hardware or runtime assumptions
