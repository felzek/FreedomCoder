from freedomcoder.profiles import list_profiles, load_profile


def test_profiles_include_flagship_and_constrained() -> None:
    profile_ids = {profile.id for profile in list_profiles()}
    assert {"flagship", "constrained"} <= profile_ids


def test_flagship_profile_is_pinned_to_requested_repo() -> None:
    profile = load_profile("flagship")
    assert profile.model_id == "llmfan46/Qwen3.5-27B-heretic-v2-GGUF"
    assert profile.recommended_quant == "Q4_K_M"
    assert profile.filename_for_quant() == "Qwen3.5-27B-heretic-v2-Q4_K_M.gguf"


def test_constrained_profile_exposes_q3_quant() -> None:
    profile = load_profile("constrained")
    assert profile.model_id == "mradermacher/Qwen3.5-27B-heretic-v2-GGUF"
    assert profile.recommended_quant == "Q3_K_M"
    assert profile.filename_for_quant() == "Qwen3.5-27B-heretic-v2.Q3_K_M.gguf"
