"""Unit tests for T-013: asset service and fixed asset validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.asset_service import (
    AssetError,
    load_character,
    load_preset,
    list_backgrounds,
    resolve_font,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _make_char_dir(tmp_path: Path, char_id: str) -> Path:
    char_dir = tmp_path / "assets" / "characters" / char_id
    char_dir.mkdir(parents=True)
    (char_dir / "base.png").write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG header
    (char_dir / "metadata.json").write_text(
        json.dumps({"character_id": char_id, "display_name": f"Char {char_id}"}),
        encoding="utf-8",
    )
    return char_dir


def _make_preset(tmp_path: Path, preset_name: str) -> Path:
    presets_dir = tmp_path / "assets" / "presets"
    presets_dir.mkdir(parents=True, exist_ok=True)
    preset = {f: f"value_{f}" for f in _REQUIRED_PRESET_FIELDS}
    preset["name"] = preset_name
    preset_path = presets_dir / f"{preset_name}.json"
    preset_path.write_text(json.dumps(preset), encoding="utf-8")
    return preset_path


def _make_font(tmp_path: Path, font_name: str = "TestBold.ttf") -> Path:
    fonts_dir = tmp_path / "assets" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    font_path = fonts_dir / font_name
    font_path.write_bytes(b"\x00\x01\x00\x00")  # minimal font stub
    return font_path


# ---------------------------------------------------------------------------
# load_character
# ---------------------------------------------------------------------------

class TestLoadCharacter:
    def test_valid_character_returns_base_png_and_metadata(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_char_dir(tmp_path, "char_a")
        result = load_character("char_a")
        assert result["base_png"].exists()
        assert result["metadata"]["character_id"] == "char_a"

    def test_missing_character_folder_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "assets" / "characters").mkdir(parents=True, exist_ok=True)
        with pytest.raises(AssetError, match="folder missing"):
            load_character("char_x")

    def test_missing_base_png_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        char_dir = tmp_path / "assets" / "characters" / "char_a"
        char_dir.mkdir(parents=True)
        (char_dir / "metadata.json").write_text(
            json.dumps({"character_id": "char_a", "display_name": "A"}),
            encoding="utf-8",
        )
        with pytest.raises(AssetError, match="base.png missing"):
            load_character("char_a")

    def test_missing_metadata_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        char_dir = tmp_path / "assets" / "characters" / "char_a"
        char_dir.mkdir(parents=True)
        (char_dir / "base.png").write_bytes(b"\x89PNG")
        with pytest.raises(AssetError, match="metadata.json missing"):
            load_character("char_a")


# ---------------------------------------------------------------------------
# load_preset
# ---------------------------------------------------------------------------

class TestLoadPreset:
    def test_valid_preset_returns_all_required_fields(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_preset(tmp_path, "shorts_default")
        preset = load_preset("shorts_default")
        assert _REQUIRED_PRESET_FIELDS.issubset(preset.keys())

    def test_missing_preset_file_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "assets" / "presets").mkdir(parents=True, exist_ok=True)
        with pytest.raises(AssetError, match="missing"):
            load_preset("nonexistent")

    def test_preset_missing_required_field_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        presets_dir = tmp_path / "assets" / "presets"
        presets_dir.mkdir(parents=True, exist_ok=True)
        incomplete = {"name": "shorts_default", "width": 1080}
        (presets_dir / "shorts_default.json").write_text(
            json.dumps(incomplete), encoding="utf-8"
        )
        with pytest.raises(AssetError, match="missing required fields"):
            load_preset("shorts_default")


# ---------------------------------------------------------------------------
# resolve_font
# ---------------------------------------------------------------------------

class TestResolveFont:
    def test_valid_font_returns_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _make_font(tmp_path, "TestBold.ttf")
        font_path = resolve_font("TestBold.ttf")
        assert font_path.exists()
        assert font_path.name == "TestBold.ttf"

    def test_missing_font_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
        with pytest.raises(AssetError, match="missing"):
            resolve_font("NoFont.ttf")


# ---------------------------------------------------------------------------
# list_backgrounds
# ---------------------------------------------------------------------------

class TestListBackgrounds:
    def test_valid_category_returns_video_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cat_dir = tmp_path / "assets" / "backgrounds" / "minecraft_parkour"
        cat_dir.mkdir(parents=True)
        (cat_dir / "video1.mp4").write_bytes(b"\x00")
        (cat_dir / "video2.mp4").write_bytes(b"\x00")
        (cat_dir / "readme.txt").write_text("ignore me")
        results = list_backgrounds("minecraft_parkour")
        assert len(results) == 2
        assert all(p.suffix == ".mp4" for p in results)

    def test_empty_category_returns_empty_list(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cat_dir = tmp_path / "assets" / "backgrounds" / "slime"
        cat_dir.mkdir(parents=True)
        assert list_backgrounds("slime") == []

    def test_missing_category_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "assets" / "backgrounds").mkdir(parents=True, exist_ok=True)
        with pytest.raises(AssetError, match="missing"):
            list_backgrounds("nonexistent_category")


# ---------------------------------------------------------------------------
# Integration: real committed assets
# ---------------------------------------------------------------------------

class TestRealAssets:
    """Validate that committed assets pass the service contracts."""

    def test_char_a_loads_successfully(self):
        result = load_character("char_a")
        assert result["base_png"].exists()
        assert result["metadata"]["character_id"] == "char_a"

    def test_char_b_loads_successfully(self):
        result = load_character("char_b")
        assert result["base_png"].exists()
        assert result["metadata"]["character_id"] == "char_b"

    def test_shorts_default_preset_loads_with_all_fields(self):
        preset = load_preset("shorts_default")
        assert _REQUIRED_PRESET_FIELDS.issubset(preset.keys())

    def test_liberation_sans_bold_font_resolves(self):
        font_path = resolve_font("LiberationSans-Bold.ttf")
        assert font_path.exists()
