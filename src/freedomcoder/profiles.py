from __future__ import annotations

import importlib.resources
import tomllib

from freedomcoder.errors import ProfileError
from freedomcoder.models import GenerationDefaults, ModelProfile


def _profile_resource_names() -> list[str]:
    resources = importlib.resources.files("freedomcoder.model_profiles")
    return sorted(
        resource.name
        for resource in resources.iterdir()
        if resource.is_file() and resource.name.endswith(".toml")
    )


def list_profiles() -> list[ModelProfile]:
    return [load_profile(name.removesuffix(".toml")) for name in _profile_resource_names()]


def load_profile(profile_id: str) -> ModelProfile:
    resource = importlib.resources.files("freedomcoder.model_profiles").joinpath(
        f"{profile_id}.toml"
    )
    if not resource.is_file():
        known = ", ".join(name.removesuffix(".toml") for name in _profile_resource_names())
        raise ProfileError(f"Unknown profile {profile_id!r}. Available profiles: {known}")
    raw = tomllib.loads(resource.read_text(encoding="utf-8"))
    generation = GenerationDefaults(**raw["generation_defaults"])
    return ModelProfile(
        id=raw["id"],
        label=raw["label"],
        model_id=raw["model_id"],
        source_provider=raw["source_provider"],
        upstream_lineage=raw["upstream_lineage"],
        description=raw["description"],
        intended_role=raw["intended_role"],
        context_strategy=raw["context_strategy"],
        recommended_quant=raw["recommended_quant"],
        when_to_use=raw["when_to_use"],
        latency_notes=raw["latency_notes"],
        memory_notes=raw["memory_notes"],
        default_model_name=raw["default_model_name"],
        notes=tuple(raw.get("notes", [])),
        quants=dict(raw["quants"]),
        generation_defaults=generation,
    )


def format_profile(profile: ModelProfile) -> str:
    quant_lines = "\n".join(
        f"  - {quant}: {filename}" for quant, filename in sorted(profile.quants.items())
    )
    note_lines = "\n".join(f"  - {note}" for note in profile.notes) or "  - None"
    defaults = profile.generation_defaults
    return (
        f"{profile.label}\n"
        f"  id: {profile.id}\n"
        f"  model id: {profile.model_id}\n"
        f"  provider: {profile.source_provider}\n"
        f"  lineage: {profile.upstream_lineage}\n"
        f"  intended role: {profile.intended_role}\n"
        f"  description: {profile.description}\n"
        f"  recommended quant: {profile.recommended_quant}\n"
        f"  when to use: {profile.when_to_use}\n"
        f"  context strategy: {profile.context_strategy}\n"
        f"  latency notes: {profile.latency_notes}\n"
        f"  memory notes: {profile.memory_notes}\n"
        f"  default model name: {profile.default_model_name}\n"
        f"  generation defaults:\n"
        f"    temperature={defaults.temperature}, top_p={defaults.top_p}, "
        f"top_k={defaults.top_k}, repetition_penalty={defaults.repetition_penalty}, "
        f"max_tokens={defaults.max_tokens}, enable_thinking={defaults.enable_thinking}\n"
        f"  supported quants:\n{quant_lines}\n"
        f"  notes:\n{note_lines}"
    )
