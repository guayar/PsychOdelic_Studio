"""Profile wymagan: jakie wezly i jakie pliki modeli musi widziec ComfyUI, zeby dany tryb pracy dzialal.

Sprawdzanie jest czysto ODCZYTOWE: porownujemy schemat `object_info` z wymaganiami. Niczego nie instalujemy
ani nie pobieramy. Brak wezla/pliku = MISSING z opisem, co zrobic (decyzja i instalacja po stronie uzytkownika).

Wymagania pochodza z: kodu natywnego ComfyUI (wezly), szablonu Comfy i nazw uzywanych w produkcyjnych skryptach
(pliki). Kazda pozycja ma zrodlo, zeby bylo wiadomo, skad wiemy, ze jest potrzebna.
"""

PROFILES = {
    "h3_extender": {
        "title": "H3 Extender (produkcja: gen_extender_refine.py)",
        "nodes": [
            ("MiniMaxH3Extender", "kod tritant/ComfyUI_MiniMax_H3_Extender"),
            ("MiniMaxH3ReferenceToVideo", "kod Comfy-Org/ComfyUI nodes_minimax_h3.py"),
            ("LoraLoaderModelOnly", "rdzen ComfyUI (LoRA na model)"),
            ("CLIPLoader", "rdzen ComfyUI"),
            ("VAELoader", "rdzen ComfyUI"),
            ("UNETLoader", "rdzen ComfyUI"),
        ],
        "files": [
            ("UNETLoader", "unet_name", "minimax_h3_ref2va_pruned_int8_convrot.safetensors", "produkcja: gen_extender_refine.py"),
            ("CLIPLoader", "clip_name", "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "produkcja: gen_extender_refine.py"),
            ("VAELoader", "vae_name", "minimax_h3_video_vae_fp16.safetensors", "produkcja: gen_extender_refine.py"),
            ("VAELoader", "vae_name", "minimax_h3_audio_vae_fp32.safetensors", "produkcja: gen_extender_refine.py"),
            ("LoraLoaderModelOnly", "lora_name", "minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_resized_avg_rank_64_bf16.safetensors", "produkcja: gen_extender_refine.py"),
        ],
    },
    "h3_controlnet": {
        "title": "H3 Fun ControlNet (sterowanie geometria)",
        "nodes": [
            ("ModelPatchLoader", "rdzen ComfyUI (model patch)"),
            ("MiniMaxH3FunControlNetApply", "kod Comfy-Org/ComfyUI nodes_minimax_h3.py"),
        ],
        "files": [
            ("ModelPatchLoader", "name", "minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors", "szablon Comfy video_minimax_h3_fun_controlnet_union.json"),
        ],
    },
    "ltx_lipsync": {
        "title": "LTX lipsync (produkcja: gen_ltx_lip.py)",
        "nodes": [
            ("LoadAudio", "rdzen ComfyUI"),
            ("LTXAVTextEncoderLoader", "ComfyUI-LTXVideo"),
        ],
        "files": [],
    },
}


def check_profile(name, object_info):
    """Zwraca liste pozycji {kind, name, status, source, action}. status: FOUND | MISSING | NOT_LISTED."""
    if name not in PROFILES:
        raise KeyError(name)
    prof = PROFILES[name]
    items = []
    for node, source in prof["nodes"]:
        ok = node in object_info
        items.append({"kind": "node", "name": node, "status": "FOUND" if ok else "MISSING", "source": source,
                      "action": "" if ok else "Wezel nie jest zainstalowany w tym ComfyUI. Zainstaluj wlasciwy custom node swiadomie i zrestartuj ComfyUI."})
    for node, inp, fname, source in prof["files"]:
        spec = object_info.get(node, {}).get("input", {}).get("required", {}).get(inp)
        if spec is None:
            items.append({"kind": "file", "name": fname, "status": "MISSING", "source": source,
                          "action": f"Wezel {node} nie ma wejscia {inp} w tym ComfyUI."})
            continue
        options = spec[0] if isinstance(spec[0], list) else []
        found = fname in options
        items.append({"kind": "file", "name": fname, "status": "FOUND" if found else "MISSING", "source": source,
                      "action": "" if found else "Plik nie jest na liscie wyboru. Umiesc go w odpowiednim folderze models/ i odswiez ComfyUI. Nie podstawiaj innej nazwy."})
    return items


def summary(items):
    out = {"FOUND": 0, "MISSING": 0}
    for it in items:
        out[it["status"]] = out.get(it["status"], 0) + 1
    out["ready"] = out["MISSING"] == 0
    return out
