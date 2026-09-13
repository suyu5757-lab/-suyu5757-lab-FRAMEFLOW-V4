"""MiniMax-specific audio prompt preparation.

Visual Prompt rules intentionally do not share this module.  Audio assets keep
their existing Web/TTS preparation contract while the visual compiler moves to
the gpt-image-2-style-library contract.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


AUDIO_PROMPT_SCHEMA_VERSION = "minimax-speech-audio-v2"
AUDIO_PROMPT_FIELD_ORDER = [
    "sourceText", "providerText", "textStatus", "voiceSource", "voiceIdentity", "language", "locale", "dialect",
    "providerVoiceId", "providerVoiceName", "providerRegion", "performanceDirection", "emotion", "intensity",
    "pace", "pausePlan", "pronunciation", "provider", "model", "voiceId", "speed", "pitch", "volume",
    "languageBoost", "format", "targetDuration", "relevantShots", "continuityChecklist", "mustPreserve", "mustAvoid",
]
AUDIO_CONFIRMED_TEXT_STATUSES = {"confirmed", "user-confirmed", "approved", "locked", "final"}

AUDIO_LOCALE_LANGUAGE_BOOSTS = {
    "ja": "Japanese", "ja-jp": "Japanese", "zh": "Chinese", "zh-cn": "Chinese", "zh-tw": "Chinese",
    "en": "English", "en-us": "English", "en-gb": "English", "ko": "Korean", "ko-kr": "Korean",
    "fr": "French", "fr-fr": "French", "de": "German", "de-de": "German", "es": "Spanish", "es-es": "Spanish",
    "it": "Italian", "it-it": "Italian", "pt": "Portuguese", "pt-br": "Portuguese", "pt-pt": "Portuguese",
    "ru": "Russian", "ru-ru": "Russian", "ar": "Arabic", "tr": "Turkish", "nl": "Dutch", "vi": "Vietnamese",
    "id": "Indonesian", "id-id": "Indonesian", "th": "Thai", "th-th": "Thai", "ms": "Malay", "ms-my": "Malay",
    "fil": "Filipino", "fil-ph": "Filipino", "uk": "Ukrainian", "uk-ua": "Ukrainian", "pl": "Polish", "pl-pl": "Polish",
    "ro": "Romanian", "ro-ro": "Romanian", "cs": "Czech", "cs-cz": "Czech", "el": "Greek", "el-gr": "Greek",
    "hu": "Hungarian", "hu-hu": "Hungarian", "sv": "Swedish", "sv-se": "Swedish", "da": "Danish", "da-dk": "Danish",
    "fi": "Finnish", "fi-fi": "Finnish", "no": "Norwegian", "no-no": "Norwegian", "sk": "Slovak", "sk-sk": "Slovak",
    "bg": "Bulgarian", "bg-bg": "Bulgarian", "hr": "Croatian", "hr-hr": "Croatian", "ta": "Tamil", "ta-in": "Tamil",
    "te": "Telugu", "te-in": "Telugu", "hi": "Hindi", "hi-in": "Hindi", "he": "Hebrew", "he-il": "Hebrew",
    "fa": "Persian", "fa-ir": "Persian", "bn": "Bengali", "bn-bd": "Bengali", "af": "Afrikaans", "af-za": "Afrikaans",
    "ca": "Catalan", "ca-es": "Catalan", "sr": "Serbian", "sr-rs": "Serbian",
}


def _has(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set)):
        return any(_has(item) for item in value)
    if isinstance(value, dict):
        return any(_has(item) for item in value.values())
    return True


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value).strip()
    if isinstance(value, list):
        return "；".join(item for item in (_text(child) for child in value) if item)
    if isinstance(value, dict):
        return "；".join(item for item in (_text(child) for child in value.values()) if item)
    return str(value).strip()


def _first(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = source.get(key)
        if _has(value):
            return value
    return None


def _spoken_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("text", "content", "line", "spokenText", "spoken_text", "transcript"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return ""
    if isinstance(value, list):
        return "\n".join(item for item in (_spoken_text(child) for child in value) if item)
    return ""


def _status(value: Any, source_text: str) -> str:
    if isinstance(value, bool):
        return "confirmed" if value and source_text else "candidate" if source_text else "missing"
    normalized = str(value or "").strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "": "candidate" if source_text else "missing",
        "draft": "candidate", "pending": "candidate", "unconfirmed": "candidate",
        "user-confirmed": "confirmed", "approved": "confirmed", "locked": "confirmed", "final": "confirmed",
        "invalid": "conflict", "ambiguous": "conflict",
    }
    return aliases.get(normalized, normalized if normalized in {"missing", "candidate", "conflict", "confirmed"} else ("candidate" if source_text else "missing"))


def _language_boost(locale: Any, language: Any, explicit: Any) -> str | None:
    locale_value = _text(locale).lower().replace("_", "-")
    mapped = AUDIO_LOCALE_LANGUAGE_BOOSTS.get(locale_value) or AUDIO_LOCALE_LANGUAGE_BOOSTS.get(locale_value.split("-", 1)[0])
    if mapped:
        return mapped
    language_value = _text(language)
    if language_value == "Japanese" or any(item in language_value for item in ("日语", "日本語")):
        return "Japanese"
    if language_value == "Chinese" or any(item in language_value for item in ("中文", "汉语", "普通话")):
        return "Chinese"
    explicit_value = _text(explicit)
    if explicit_value and explicit_value.lower() not in {"auto", "automatic", "chinese"}:
        return explicit_value
    return None


def _context_shots(context: dict[str, Any] | None) -> list[dict[str, Any]]:
    values = context.get("shots") if isinstance(context, dict) else []
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _audio_details(source: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = source.get("audioDetails") if isinstance(source.get("audioDetails"), dict) else source.get("audio_details")
    raw_audio = deepcopy(raw) if isinstance(raw, dict) else {}
    source_text = _spoken_text(_first(raw_audio, "sourceText", "source_text", "spokenText", "spoken_text", "dialogueText", "dialogue_text", "line", "transcript", "text"))
    if not source_text:
        source_text = _spoken_text(_first(source, "sourceText", "source_text", "spokenText", "spoken_text", "dialogueText", "dialogue_text", "line", "transcript", "text"))
    provider_text = _spoken_text(_first(raw_audio, "providerText", "provider_text", "providerInput", "provider_input")) or source_text
    details = raw_audio
    details.update({
        "schemaVersion": AUDIO_PROMPT_SCHEMA_VERSION,
        "sourceText": source_text,
        "providerText": provider_text,
        "textStatus": _status(_first(raw_audio, "textStatus", "text_status", "dialogueStatus", "dialogue_status"), source_text),
    })

    def set_default(key: str, *aliases: str, default: Any = None) -> None:
        if not _has(details.get(key)):
            value = _first(raw_audio, key, *aliases)
            if not _has(value):
                value = _first(source, key, *aliases)
            if not _has(value):
                value = default
            if _has(value):
                details[key] = deepcopy(value)

    set_default("voiceSource", "voice_source", "sourceType", "source_type", default="system-preset")
    set_default("voiceIdentity", "voice_identity", "voiceProfile", "voice_profile", "voiceTraits", "voice_traits")
    set_default("language", "lang")
    set_default("locale", "languageLocale", "language_locale")
    set_default("dialect", "accent")
    set_default("performanceDirection", "performance_direction", "voiceDirection", "voice_direction", "instructions", "delivery", "direction")
    set_default("emotion", "mood")
    set_default("intensity", "energy")
    set_default("pace", "register", "speechRate", "speech_rate")
    set_default("pausePlan", "pause_plan", "pauses", "pause")
    set_default("pronunciation", "pronunciationDict", "pronunciation_dict", "pronunciationNotes", "pronunciation_notes")
    set_default("soundTags", "sound_tags", "interjections", "nonVerbal", "non_verbal")
    set_default("distance", "projectionDistance", "projection_distance")
    set_default("targetDuration", "target_duration", "duration")
    set_default("provider", default="minimax")
    set_default("model", default="speech-2.8-hd")
    set_default("voiceId", "voice_id", "providerVoiceId", "provider_voice_id")
    set_default("providerVoiceId", "provider_voice_id", "voiceId", "voice_id")
    set_default("providerVoiceName", "provider_voice_name")
    set_default("providerRegion", "provider_region", "region", default="cn")
    set_default("speed", default=1.0)
    set_default("pitch", default=0)
    set_default("volume", "vol", default=1.0)
    if not _has(details.get("languageBoost")):
        details["languageBoost"] = _language_boost(details.get("locale"), details.get("language"), _first(raw_audio, "languageBoost", "language_boost"))
    set_default("format", "audioFormat", "audio_format", default="wav")
    set_default("sampleRate", "sample_rate")
    set_default("bitrate")
    set_default("channel", "channels")
    set_default("stems", "tracks", "mixStems", "mix_stems")
    details["relevantShots"] = deepcopy(details.get("relevantShots") or details.get("relevant_shots") or [])
    if not isinstance(details["relevantShots"], list):
        details["relevantShots"] = []
    if not details["relevantShots"]:
        details["relevantShots"] = [str(item.get("id") or item.get("shotId") or item.get("shot_id")) for item in _context_shots(context) if item.get("id") or item.get("shotId") or item.get("shot_id")]
    details["continuityChecklist"] = source.get("continuityChecklist") or source.get("continuity_checklist") or []
    details["mustPreserve"] = source.get("mustPreserve") or source.get("must_preserve") or []
    details["mustAvoid"] = source.get("mustAvoid") or source.get("must_avoid") or []
    return details


def build_audio_prompt_package(prompt_pack: Any, fallback_prompt: str = "", *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    source = deepcopy(prompt_pack) if isinstance(prompt_pack, dict) else {}
    details = _audio_details(source, context)
    source_text = _spoken_text(details.get("sourceText"))
    provider_text = _spoken_text(details.get("providerText")) or source_text
    fallback = _spoken_text(fallback_prompt)
    if not source_text and fallback:
        source_text = fallback
        provider_text = fallback
        text_status = "candidate"
    else:
        text_status = _status(details.get("textStatus"), source_text)
    candidates: list[dict[str, str]] = []
    for shot in _context_shots(context):
        shot_id = str(shot.get("id") or shot.get("shotId") or shot.get("shot_id") or "").strip()
        raw = shot.get("dialogue") or shot.get("dialogues") or shot.get("narration") or shot.get("voiceover") or shot.get("voice_over") or shot.get("line") or shot.get("lines")
        spoken = _spoken_text(raw)
        if spoken:
            candidates.append({"shotId": shot_id, "kind": "旁白" if shot.get("narration") or shot.get("voiceover") else "对白", "text": spoken})
    unique_candidate_texts = list(dict.fromkeys(item["text"] for item in candidates))
    shot_ids = [str(item.get("id") or item.get("shotId") or item.get("shot_id")) for item in _context_shots(context) if item.get("id") or item.get("shotId") or item.get("shot_id")]
    direction = "；".join(item for item in (
        _text(details.get("voiceIdentity")), _text(details.get("language")), _text(details.get("dialect")), _text(details.get("performanceDirection")),
        f"情绪为{_text(details.get('emotion'))}" if _has(details.get("emotion")) else "",
        f"强度为{_text(details.get('intensity'))}" if _has(details.get("intensity")) else "",
        f"语速为{_text(details.get('pace'))}" if _has(details.get("pace")) else "",
        f"投射距离为{_text(details.get('distance'))}" if _has(details.get("distance")) else "",
    ) if item)
    warnings: list[str] = []
    if text_status != "confirmed":
        warnings.append("朗读文本尚未标记为 confirmed；请先确认每个镜头的唯一台词，再复制到 MiniMax Web。")
    if len(unique_candidate_texts) > 1:
        warnings.append("关联镜头存在多条不同文本；必须拆成多次生成，不能拼成一段。")
    if len(shot_ids) > len(candidates) and candidates:
        warnings.append("部分关联镜头没有明确朗读文本；请逐镜头确认台词或明确该镜头无对白。")
    if text_status == "conflict":
        warnings.append("当前文本存在镜头/台词冲突，暂不提供可复制的朗读文本。")
    return {
        "schemaVersion": AUDIO_PROMPT_SCHEMA_VERSION,
        "provider": "minimax",
        "operation": _text(details.get("operation")) or "tts",
        "sourceText": source_text,
        "providerText": provider_text,
        "copyText": provider_text if provider_text and text_status in AUDIO_CONFIRMED_TEXT_STATUSES else "",
        "candidateText": provider_text if provider_text and text_status not in AUDIO_CONFIRMED_TEXT_STATUSES else "",
        "textStatus": text_status,
        "direction": direction,
        "settings": {
            "provider": "minimax", "model": _text(details.get("model")) or "speech-2.8-hd",
            "voiceId": _text(details.get("providerVoiceId")) or _text(details.get("voiceId")) or "在 MiniMax Web 中选择固定系统音色",
            "voiceName": _text(details.get("providerVoiceName")) or "以实际试听结果为准",
            "region": _text(details.get("providerRegion")) or "cn",
            "languageBoost": _text(details.get("languageBoost")) or "自动识别",
            "emotion": _text(details.get("emotion")) or "留空",
            "speed": _text(details.get("speed")) or "1.0",
            "pitch": _text(details.get("pitch")) or "0",
            "volume": _text(details.get("volume")) or "1.0",
            "format": _text(details.get("format")) or "wav",
        },
        "pausePlan": deepcopy(details.get("pausePlan") or []),
        "pronunciation": deepcopy(details.get("pronunciation") or {}),
        "soundTags": deepcopy(details.get("soundTags") or []),
        "targetDuration": details.get("targetDuration"),
        "relevantShots": deepcopy(details.get("relevantShots") or shot_ids),
        "candidates": candidates,
        "continuity": deepcopy(details.get("continuityChecklist") or []),
        "mustPreserve": deepcopy(details.get("mustPreserve") or []),
        "mustAvoid": deepcopy(details.get("mustAvoid") or []),
        "warnings": warnings,
    }


def build_audio_prompt_text(prompt_pack: Any, fallback_prompt: str = "", *, context: dict[str, Any] | None = None) -> str:
    package = build_audio_prompt_package(prompt_pack, fallback_prompt, context=context)
    if package.get("copyText"):
        return str(package["copyText"])
    if package.get("candidateText"):
        return f"MiniMax Speech 2.8 Web：候选朗读文本待用户确认：{package['candidateText']}"
    return "MiniMax Speech 2.8 Web：尚未确认唯一朗读文本，暂不生成。"


def audio_prompt_contract() -> dict[str, Any]:
    return {
        "version": AUDIO_PROMPT_SCHEMA_VERSION,
        "workflow": "minimax-speech-web",
        "asset_class": "audio",
        "field_order": list(AUDIO_PROMPT_FIELD_ORDER),
        "prompt_pack_shape": {"schemaVersion": AUDIO_PROMPT_SCHEMA_VERSION, "audioDetails": "MiniMax Speech Web 控制字段"},
        "copy_boundary": "只有 confirmed 的实际朗读文本可以复制到 MiniMax 文本框；资产、镜头、QA 和流程字段留在工作台。",
    }


def canonicalize_audio_output(prompt_pack: Any, prompt: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    details = _audio_details(prompt_pack if isinstance(prompt_pack, dict) else {}, context)
    package = build_audio_prompt_package({"audioDetails": details}, prompt, context=context)
    quality = {
        "schema_version": AUDIO_PROMPT_SCHEMA_VERSION,
        "status": "ready" if package.get("copyText") else "needs-confirmation",
        "missing": [] if package.get("copyText") else ["confirmed sourceText"],
    }
    return {
        "prompt": build_audio_prompt_text({"audioDetails": details}, prompt, context=context),
        "copyablePrompt": package.get("copyText") or "",
        "promptPack": {"schemaVersion": AUDIO_PROMPT_SCHEMA_VERSION, "assetType": "audio", "audioDetails": details},
        "promptQuality": quality,
        "promptContractVersion": AUDIO_PROMPT_SCHEMA_VERSION,
        "promptWorkflow": "minimax-speech-web",
        "mustPreserve": details.get("mustPreserve") or [],
        "mustAvoid": details.get("mustAvoid") or [],
    }


__all__ = [
    "AUDIO_CONFIRMED_TEXT_STATUSES",
    "AUDIO_PROMPT_FIELD_ORDER",
    "AUDIO_PROMPT_SCHEMA_VERSION",
    "audio_prompt_contract",
    "build_audio_prompt_package",
    "build_audio_prompt_text",
    "canonicalize_audio_output",
]
