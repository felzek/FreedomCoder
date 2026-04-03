# Model Profiles

FreedomCoder ships two built-in profiles for the `Qwen3.5-27B-heretic-v2` lineage.

## Flagship

- Profile id: `flagship`
- Primary repo: `llmfan46/Qwen3.5-27B-heretic-v2-GGUF`
- Recommended quant: `Q4_K_M`
- Intended use: best local coding quality within the project's supported lineage

Use this when:

- you explicitly want the requested flagship Heretic 27B path
- you can tolerate heavy memory use and slower local latency
- you prefer quality over comfort

## Constrained

- Profile id: `constrained`
- Mirror repo: `mradermacher/Qwen3.5-27B-heretic-v2-GGUF`
- Recommended quant: `Q3_K_M`
- Intended use: lower-memory operation for the same lineage

Use this when:

- `Q4_K_M` is too heavy for your machine
- you still want the 27B Heretic lineage
- you understand that `Q3_K_M` is a compromise, not a lightweight path

## Q3_K_M vs Q4_K_M

Choose `Q3_K_M` when:

- memory pressure is the main blocker
- you want to keep context smaller and accept more quality loss

Choose `Q4_K_M` when:

- coding quality is the priority
- the machine can sustain the larger GGUF and context cache

Important:

- the constrained profile uses a mirror because the exact flagship GGUF repo does not currently expose `Q3_K_M`
- both profiles point at the same broader Heretic model lineage
- neither profile should be described as an official uncensored Qwen release
