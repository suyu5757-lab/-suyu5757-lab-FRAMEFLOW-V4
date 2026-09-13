from __future__ import annotations

from typing import Any


SUPPORTED_ASPECT_RATIOS = ("16:9", "1:1", "9:16")

# A design ratio is intentionally not translated into a provider pixel size.
# External generators may have their own size limits, but those limits must not
# rewrite the asset's semantic canvas or appear in the copyable Prompt.
ASPECT_RATIO_TO_IMAGE_SIZE: dict[str, str | None] = {
    "16:9": None,
    "1:1": None,
    "9:16": None,
}

IMAGE_SIZE_TO_PROVIDER_ASPECT_RATIO: dict[str, str] = {}

DEFAULT_BASE_ASSET_ASPECT_RATIOS = {
    "character": "16:9",
    "scene": "16:9",
    "prop": "1:1",
    "product": "1:1",
    "style": "16:9",
}

BASE_ASSET_LAYOUT_PROFILES = {
    "character": "character_reference_sheet",
    "scene": "empty_environment_board",
    "prop": "isolated_object_board",
    "product": "isolated_product_board",
    "style": "style_reference_board",
    "fusion": "fusion_frame",
    "shot": "shot_keyframe",
}


def normalize_aspect_ratio(value: Any, fallback: str = "1:1") -> str:
    """Normalize only the image sizes currently supported by the studio."""

    candidate = str(value or "").strip().lower().replace("×", "x")
    aliases = {
        "1536x1024": "16:9",
        "1024x1024": "1:1",
        "1024x1536": "9:16",
    }
    normalized = aliases.get(candidate, candidate)
    if normalized in SUPPORTED_ASPECT_RATIOS:
        return normalized
    safe_fallback = aliases.get(str(fallback or "").strip().lower(), str(fallback or "").strip())
    return safe_fallback if safe_fallback in SUPPORTED_ASPECT_RATIOS else "1:1"


def image_size_for_aspect_ratio(aspect_ratio: Any) -> str | None:
    return ASPECT_RATIO_TO_IMAGE_SIZE.get(normalize_aspect_ratio(aspect_ratio))


def provider_aspect_ratio_for_image_size(image_size: Any) -> str | None:
    """Return no provider ratio; provider geometry is no longer a prompt rule."""

    del image_size
    return None


def asset_layout_profile(asset_class: Any) -> str | None:
    """Return the stable base-image layout profile for one asset class."""

    value = str(asset_class or "").strip().lower()
    aliases = {
        "environment": "scene",
        "environment_prop": "scene",
        "environment_state": "scene",
        "background": "scene",
        "item": "prop",
        "product": "product",
    }
    canonical = aliases.get(value, value)
    return BASE_ASSET_LAYOUT_PROFILES.get(canonical)


def asset_generation_profile(
    asset_class: Any,
    project_output_aspect_ratio: Any = "9:16",
    explicit_aspect_ratio: Any = None,
) -> dict[str, str | None]:
    """Return the reference-image geometry for one logical asset.

    The project ratio describes the final shot/video canvas. Only Fusion and
    shot-level outputs inherit it. Base assets use a class-specific canvas so
    their identity, material, and spatial evidence are not cropped into the
    final delivery format prematurely.
    """

    asset_class_name = str(asset_class or "").strip().lower()
    if asset_class_name in {"audio", "music", "sfx"}:
        return {"aspect_ratio": None, "source": "not_applicable"}
    if asset_class_name in {"fusion", "shot"}:
        aspect_ratio = normalize_aspect_ratio(project_output_aspect_ratio, "9:16")
        return {"aspect_ratio": aspect_ratio, "source": "project_output"}
    aspect_ratio = DEFAULT_BASE_ASSET_ASPECT_RATIOS.get(asset_class_name, "1:1")
    return {"aspect_ratio": aspect_ratio, "source": "class_default"}
