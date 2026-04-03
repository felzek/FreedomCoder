from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GenerationDefaults:
    temperature: float
    top_p: float
    top_k: int
    presence_penalty: float
    repetition_penalty: float
    max_tokens: int
    enable_thinking: bool = False

    def ollama_options(self, *, num_ctx: int) -> dict[str, int | float]:
        return {
            "num_ctx": num_ctx,
            "num_predict": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repetition_penalty,
        }


@dataclass(frozen=True)
class ModelProfile:
    id: str
    label: str
    model_id: str
    source_provider: str
    upstream_lineage: str
    description: str
    intended_role: str
    context_strategy: str
    recommended_quant: str
    when_to_use: str
    latency_notes: str
    memory_notes: str
    default_model_name: str
    notes: tuple[str, ...]
    quants: dict[str, str]
    generation_defaults: GenerationDefaults

    def filename_for_quant(self, quant: str | None = None) -> str:
        selected = quant or self.recommended_quant
        try:
            return self.quants[selected]
        except KeyError as exc:
            supported = ", ".join(sorted(self.quants))
            raise KeyError(
                f"Unsupported quant {selected!r} for profile {self.id!r}. "
                f"Supported quants: {supported}"
            ) from exc


@dataclass(frozen=True)
class Settings:
    default_profile: str = "flagship"
    ollama_host: str = "http://127.0.0.1:11434"
    default_model: str | None = None
    max_context_chars: int = 24_000
    max_file_bytes: int = 12_000
    instructions_path: str = "AGENTS.md"
    config_path: Path | None = None


@dataclass(frozen=True)
class FileContext:
    path: Path
    content: str
    truncated: bool

