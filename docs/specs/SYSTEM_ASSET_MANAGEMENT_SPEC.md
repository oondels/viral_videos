# SYSTEM_ASSET_MANAGEMENT_SPEC

## Purpose

Define the fixed asset tree, the minimum asset contracts, and validation behavior.

## In scope

- character assets;
- background assets;
- fonts;
- render presets;
- asset loading and validation.

## Character asset contract

Each character must live at:

`assets/characters/<character_id>/`

Required files:

- `base.png`
- `metadata.json`

`metadata.json` must contain at least:

```json
{
  "character_id": "char_a",
  "display_name": "Character A"
}
```

## Background asset contract

Backgrounds must be grouped by category:

- `assets/backgrounds/slime/`
- `assets/backgrounds/sand/`
- `assets/backgrounds/minecraft_parkour/`
- `assets/backgrounds/marble_run/`
- `assets/backgrounds/misc/`

Each background file must be a readable video file.

## Font contract

- Fonts used by subtitles and title overlays must live in `assets/fonts/`.
- The MVP must provide at least one bold subtitle-safe font.

## Preset contract

Render presets must live in `assets/presets/`.

Each preset JSON must define:

- `name`
- `width`
- `height`
- `fps`
- `title_box`
- `title_timing`
- `title_style`
- `active_speaker_box`
- `inactive_speaker_box`
- `subtitle_safe_area`
- `subtitle_style`

## Required behavior

- Asset validation must happen before a module uses the asset.
- The asset service must resolve assets by logical id, not hardcoded absolute paths.
- Presets must reference fonts by logical id or file name that resolves under `assets/fonts/`.
- Missing required assets must produce explicit errors.
- Generated outputs must never be written into `assets/`.

## Failure conditions

- missing character folder;
- missing `base.png`;
- missing `metadata.json`;
- missing preset file;
- missing font referenced by a preset;
- unreadable background asset;
- empty font directory when subtitles are enabled.

## Acceptance tests

- Loading a valid character id returns existing `base.png` and `metadata.json`.
- Loading an invalid character id fails clearly.
- Loading a valid preset returns all required fields.
- Loading a valid preset also resolves every referenced font under `assets/fonts/`.
- Background categories can be resolved by name.
