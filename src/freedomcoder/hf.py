from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import hf_hub_download

from freedomcoder.models import ModelProfile


def download_profile_quant(
    profile: ModelProfile,
    *,
    quant: str | None = None,
    output_dir: Path | None = None,
    token: str | None = None,
) -> Path:
    filename = profile.filename_for_quant(quant)
    destination = (output_dir or Path(".freedomcoder/models")).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    resolved_token = token or os.getenv("HF_TOKEN") or None
    path = hf_hub_download(
        repo_id=profile.model_id,
        filename=filename,
        local_dir=str(destination),
        token=resolved_token,
    )
    return Path(path)
