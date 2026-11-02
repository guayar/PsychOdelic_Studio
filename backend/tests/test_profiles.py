from psychodelic.workflows.profiles import check_profile, summary

OI = {
    "MiniMaxH3Extender": {}, "MiniMaxH3ReferenceToVideo": {}, "LoraLoaderModelOnly": {}, "CLIPLoader": {}, "VAELoader": {},
    "UNETLoader": {"input": {"required": {"unet_name": [["minimax_h3_ref2va_pruned_int8_convrot.safetensors"]]}}},
}


def test_missing_nodes_and_files_are_reported_with_actions():
    items = check_profile("h3_extender", OI)
    s = summary(items)
    assert s["ready"] is False
    missing_files = [i for i in items if i["kind"] == "file" and i["status"] == "MISSING"]
    assert any("minimax_h3_video_vae_fp16" in i["name"] or "lora" in i["name"].lower() for i in missing_files)
    assert all(i["action"] for i in items if i["status"] == "MISSING")


def test_ready_when_everything_listed():
    oi = {n: {"input": {"required": {"unet_name": [["minimax_h3_ref2va_pruned_int8_convrot.safetensors"]],
                                     "clip_name": [["qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"]],
                                     "vae_name": [["minimax_h3_video_vae_fp16.safetensors", "minimax_h3_audio_vae_fp32.safetensors"]],
                                     "lora_name": [["minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_resized_avg_rank_64_bf16.safetensors"]]}}}
          for n in ["MiniMaxH3Extender", "MiniMaxH3ReferenceToVideo", "LoraLoaderModelOnly", "CLIPLoader", "VAELoader", "UNETLoader"]}
    assert summary(check_profile("h3_extender", oi))["ready"] is True


def test_endpoint_unreachable_is_honest(client):
    r = client.get("/api/comfy/check/h3_extender").json()
    assert r["reachable"] is False and "nie dowod braku modeli" in r["detail"]


def test_endpoint_unknown_profile(client):
    assert client.get("/api/comfy/check/nie_ma").status_code == 404
