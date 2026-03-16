"""Asset service — resolves and validates fixed assets from the assets/ tree."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ASSETS_ROOT = Path("assets")

_REQUIRED_PRESET_FIELDS = {
    "name",
    "width",
    "height",
    "fps",
    "title_box",
    "title_timing",
    "title_style",
    "active_speaker_box",
    "inactive_speaker_box",
    "subtitle_safe_area",
    "subtitle_style",
    "speaker_transition_duration_sec",
    "speaker_anchor",
}


class AssetError(Exception):
    """Raised when a required asset is missing or invalid."""


def _assets_root() -> Path:
    return _ASSETS_ROOT


def load_character(character_id: str) -> dict[str, Any]:
    """Resolve and validate a character asset.

    Args:
        character_id: logical character id (e.g. 'char_a').

    Returns:
        dict with keys 'base_png' (Path) and 'metadata' (dict).

    Raises:
        AssetError: if the character folder, base.png, or metadata.json is missing.
    """
    char_dir = _assets_root() / "characters" / character_id
    if not char_dir.is_dir():
        raise AssetError(f"Character folder missing: {char_dir}")

    base_png = char_dir / "base.png"
    if not base_png.exists():
        raise AssetError(f"Character base.png missing: {base_png}")

    metadata_path = char_dir / "metadata.json"
    if not metadata_path.exists():
        raise AssetError(f"Character metadata.json missing: {metadata_path}")

    metadata: dict[str, Any] = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )
    return {"base_png": base_png, "metadata": metadata}


def load_preset(preset_name: str) -> dict[str, Any]:
    """Load and validate a render preset.

    Args:
        preset_name: preset name without extension (e.g. 'shorts_default').

    Returns:
        The preset dict with all required fields.

    Raises:
        AssetError: if the preset file is missing or lacks required fields.
    """
    preset_path = _assets_root() / "presets" / f"{preset_name}.json"
    if not preset_path.exists():
        raise AssetError(f"Preset file missing: {preset_path}")

    preset: dict[str, Any] = json.loads(preset_path.read_text(encoding="utf-8"))

    missing = _REQUIRED_PRESET_FIELDS - set(preset.keys())
    if missing:
        raise AssetError(
            f"Preset '{preset_name}' missing required fields: {sorted(missing)}"
        )

    return preset


def resolve_font(font_filename: str) -> Path:
    """Resolve a font file from assets/fonts/.

    Args:
        font_filename: font file name (e.g. 'LiberationSans-Bold.ttf').

    Returns:
        Absolute-resolved Path to the font file.

    Raises:
        AssetError: if the font file does not exist.
    """
    font_path = _assets_root() / "fonts" / font_filename
    if not font_path.exists():
        raise AssetError(f"Font file missing: {font_path}")
    return font_path


def list_backgrounds(category: str) -> list[Path]:
    """Return all background video files in a given category folder.

    Args:
        category: background category name (e.g. 'minecraft_parkour').

    Returns:
        List of Paths to background files in the category folder.

    Raises:
        AssetError: if the category folder does not exist.
    """
    cat_dir = _assets_root() / "backgrounds" / category
    if not cat_dir.is_dir():
        raise AssetError(f"Background category folder missing: {cat_dir}")

    return [
        p for p in sorted(cat_dir.iterdir())
        if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv"}
    ]
