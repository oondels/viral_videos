# CHANGELOG

All notable changes to this project are documented in this file.

Format: based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: milestone-based, aligned with `TASKS.md` task IDs.
Source of truth for pipeline architecture: `docs/DESIGN_SPEC.md`.
Detailed bug history: `bugs/`.

---

## [Hotfix] — 2026-03-16 — Docker File Ownership & TTS Adapter Fix

### Fixed — BUG-002: Output files owned by root, inaccessible to host GUI apps

> Full diagnosis: `bugs/bug-root-owned-output-files-2026-03-16.md`

- `docker-compose.yml`: added `user: "${UID}:${GID}"` so the container runs as the
  host user. All output files now inherit correct ownership instead of `root:root`.
  Snap-confined players (mpv, VLC) previously refused to open root-owned files,
  making valid output appear "corrupted".
- `app/adapters/elevenlabs_tts_adapter.py`: moved `output_path.parent.mkdir()` to
  **before** `open()`. Previously the directory creation happened after the file
  write, which would fail on a fresh directory not pre-created by `init_workspace()`.
  Also removed orphaned debug print statement.

**Test count:** 233 (no regressions)

---

## [Milestone 4] — 2026-03-15 — Resume Mode & Output Compatibility

### Added — T-027: Modo --resume (resume_pipeline)

- `app/services/file_service.py`: `init_workspace()` now serializes `ctx.job.model_dump()`
  to `output/jobs/<job_id>/job_input.json` on every run (idempotent). Required for resume
  support so the pipeline can reconstruct the `ValidatedJob` without the original JSON file.
- `app/pipeline.py`: new `resume_pipeline(job_id, llm, tts, lipsync) -> JobContext` function.
  Reads `job_input.json`, reconstructs `ValidatedJob` via `model_validate`, checks canonical
  output artifacts per stage, emits `stage_skipped` event for stages whose artifacts are
  already on disk, and executes normally for stages with missing artifacts. `finalize_job`
  always runs.
- `app/main.py`: `--resume JOB_ID` added to the mutually exclusive CLI group. Calls
  `resume_pipeline()` and exits with code 1 on `PipelineError`.
- `tests/integration/test_resume.py`: 10 new integration tests covering `job_input.json`
  persistence, full-skip when workspace is complete, selective re-execution of
  `compose_video` when `final.mp4` is deleted, `stage_skipped` event validation, and error
  paths for missing or malformed `job_input.json`.

**Test count:** 223 → 233 (+ 10)

---

### Fixed — T-026: MP4 output unusable on VLC, WhatsApp, VS Code, Google Drive

> Full diagnosis: `bugs/bug-corrupted-mp4-output-2026-03-15.md`

- `app/modules/compositor.py` — three surgical fixes in `compose_video()`:

  1. **SAR 10240:10239 → 1:1**: added `setsar=1` to the `scale` filter of every active
     speaker clip in `filter_complex`. VLC and platform validators enforce SAR 1:1; the
     non-unity value was inherited from the lip-sync engine's source clips and propagated
     into the final output.

  2. **Audio 22050 Hz mono → 44100 Hz stereo**: added `-ar 44100 -ac 2` to the final
     FFmpeg AAC encode command. ElevenLabs TTS outputs PCM at 22050 Hz mono; VS Code's
     embedded player and WhatsApp require 44100 Hz stereo AAC.

  3. **Bitrate ~4 Mbps → ~1.5–2 Mbps**: added `-preset fast -crf 28` to the x264 encode
     command. Default x264 settings produced ~17 MB files for 35-second jobs, exceeding
     WhatsApp's 16 MB upload limit.

**Test count:** 223 → 223 (no regressions; ffprobe-level validation is manual)

---

## [Milestone 3] — 2026-03-15 — Bug Fixes & Quality

### Fixed — T-025: Subtitles rendered too large (libass PlayResY mismatch)

- `app/modules/compositor.py`: before building the `force_style` string, compute the
  libass-adjusted font size using the formula
  `libass_font_size = max(1, round(font_size_px × 288 / canvas_height))`.
  libass uses `PlayResY=288` as its internal reference height when rendering SRT files;
  passing raw pixel values caused `FontSize=64` to render as ~427 px on a 1920-tall canvas.
  The fix maps 64 px → 10 libass pts, which renders as visually ≈64 px on the final video.
- `assets/presets/shorts_default.json`: `font_size: 64` preserved. The value now means
  "64 visual pixels at the preset's native canvas height", an intuitive unit.
- Added inline comment explaining `_LIBASS_PLAY_RES_Y = 288` constant and scaling rationale.

**Test count:** 223 → 223 (no regressions)

---

### Fixed — T-024: Silent/quiet audio from ElevenLabs TTS

- `app/adapters/elevenlabs_tts_adapter.py`: added `VoiceSettings(use_speaker_boost=True)`
  to the `__init__` and passed `voice_settings` to `text_to_speech.convert()`. ElevenLabs
  default settings produce lower-amplitude output; `use_speaker_boost=True` raises loudness
  at the source.
- `app/adapters/ffmpeg_adapter.py`: added `normalize_audio()` function applying the
  `loudnorm=I=-14:TP=-1.5:LRA=11` FFmpeg filter (YouTube/streaming standard -14 LUFS).
  Uses an atomic `_loudnorm_tmp.wav` → `Path.replace()` pattern to avoid read/write
  conflicts.
- `app/modules/timeline_builder.py`: `normalize_audio()` called immediately after
  `concat_audio()` in `build_timeline()`, replacing `master_audio.wav` in-place.
  Individual segment WAVs remain untouched (raw ElevenLabs output preserved for debugging).

**Test count:** 223 → 223 (no regressions)

---

### Added — Concrete Provider Adapters (pre-task hotfixes)

- `app/adapters/openai_llm_adapter.py`: `OpenAIScriptGenerator` — concrete LLM adapter
  wrapping the OpenAI API; structured JSON output via `response_format`.
- `app/adapters/elevenlabs_tts_adapter.py`: `ElevenLabsTTSProvider` — concrete TTS adapter
  writing raw PCM bytes as WAV; `pcm_22050` format with 44-byte WAV header construction.
- `app/adapters/static_lipsync_adapter.py`: `StaticImageLipSync` — lip-sync adapter that
  loops the character's `base.png` over the audio segment using FFmpeg, requiring no GPU.
- `app/main.py`: `_build_providers()` wired to load real OpenAI, ElevenLabs, and
  StaticImageLipSync adapters from `.env` credentials.
- `config/voices.json`: updated with real ElevenLabs voice IDs for `char_a` and `char_b`.

---

## [Milestone 2] — 2026-03-15 — MVP Hardening & Operations

### Added — T-023: Operational documentation

- `README.md`: updated with complete pipeline status table, technical documentation
  section, scripts reference, and Makefile targets.
- `scripts/run_single.sh`: convenience wrapper for single-job execution.
- `scripts/run_batch.sh`: convenience wrapper for batch execution.
- `Makefile`: targets `build`, `run`, `batch`, `test`, `lint`, `clean`.
- Lint fixes across 5 files (unused imports and variables suppressed via ruff).

---

### Added — T-022: Hardening — exceptions, retry, and configuration

- `app/core/exceptions.py`: base `ViralVideosError` and documented exception hierarchy
  (`ScriptGenerationError`, `TTSError`, `LipSyncError`, `TimelineError`, `BackgroundError`,
  `SubtitleError`, `CompositorError`, `PipelineError`).
- `app/utils/retry.py`: `retry(fn, retryable, max_attempts, base_delay)` with exponential
  backoff. Re-raises the last retryable exception after exhausting attempts; non-retryable
  exceptions propagate immediately.
- `app/config.py`: `provider_max_retries` field added (env `PROVIDER_MAX_RETRIES`,
  default 3).
- `app/pipeline.py`: `_run_with_retry()` helper added; `write_script`, `generate_tts`,
  and `generate_lipsync` use retry logic for transient provider failures.
- `tests/unit/test_retry.py`: 9 unit tests for retry behaviour.

**Test count:** 214 → 223 (+ 9)

---

### Added — T-021: Sequential batch processing

- `app/batch.py`: `run_batch(batch_file, llm, tts, lipsync)` — sequential execution; each
  row in the CSV becomes one job; pipeline failures are caught per-item (batch continues);
  report written to `output/batch_reports/latest_report.json`.
- `app/main.py`: `--batch FILE` CLI argument wired to `run_batch()`.
- `inputs/batch/jobs.csv`: canonical example batch input file.
- `tests/integration/test_batch.py`: 10 integration tests.

**Test count:** 204 → 214 (+ 10)

---

### Added — T-020: Canonical stage logging and execution metadata

- `app/pipeline.py`: retrospective `stage_started` / `stage_completed` events emitted for
  `init_job_workspace` after the log file exists.
- `tests/integration/test_observability.py`: 12 integration tests validating the full
  JSON Lines logging contract: required fields, canonical stage/event names, consistent
  `job_id`, `stage_failed` fields, `render_metadata.json` presence, and
  `validate_input` failure producing no `job.log`.

**Test count:** 192 → 204 (+ 12)

---

### Added — T-019: Full single-job pipeline end-to-end

- `app/pipeline.py`: `run_pipeline(job_file, llm, tts, lipsync) -> JobContext` — 10 canonical
  stages in mandatory order; fail-fast; `stage_started / stage_completed / stage_failed`
  events via `JobLogger`; `PipelineError` wraps original exceptions.
- `app/main.py`: `--input FILE` wired to `run_pipeline()`.
- `tests/integration/test_pipeline.py`: 7 integration tests.

**Test count:** 185 → 192 (+ 7)

---

## [Milestone 1] — 2026-03-15 — Core Modules & Pipeline Skeleton

### Added — T-018: Compositor and render metadata

- `app/modules/compositor.py`: `compose_video(ctx) -> Path` — dynamic `filter_complex`
  with background scaling, per-segment clip/inactive-image overlays with temporal
  `enable='between(t,...)'` windows, `drawtext` title hook, and `subtitles` SRT burn.
  Codec: `libx264 / yuv420p / AAC`; resolution: `1080×1920`; FPS: from preset.
- `app/services/render_service.py`: `write_render_metadata()` — writes
  `render_metadata.json` with all required fields.
- `tests/integration/test_compositor.py`: 9 integration tests.

**Test count:** 176 → 185 (+ 9)

---

### Added — T-017: Centralised FFmpeg and FFprobe operations

- `app/adapters/ffmpeg_adapter.py`: `run_ffmpeg()`, `concat_audio()`,
  `scale_and_trim_video()`, `normalize_audio()`.
- `app/utils/ffprobe_utils.py`: extended with `get_media_duration()`,
  `get_video_dimensions()`, `_run_ffprobe()`.
- `app/utils/video_utils.py`: `make_color_video()` test utility.
- `app/modules/background_selector.py` and `app/modules/timeline_builder.py` refactored
  to use the new adapter.
- `tests/unit/test_ffmpeg_adapter.py`: 15 unit tests.

**Test count:** 161 → 176 (+ 15)

---

### Added — T-016: Background selector

- `app/modules/background_selector.py`: `prepare_background(ctx, required_duration_sec)`
  — deterministic category selection via MD5 hash of `job_id`; short sources looped via
  `-stream_loop -1`; long sources trimmed via `-t`; scale-to-cover `1080×1920`.
- `tests/unit/test_background_selector.py`: 9 unit tests.

**Test count:** 152 → 161 (+ 9)

---

### Added — T-015: Talking-head clip generation (LipSync module)

- `app/modules/lipsync.py`: `generate_lipsync(ctx, engine)` — one clip per timeline item;
  calls `engine.generate(base_png, audio_file, clip_path)`; validates duration tolerance
  (0.10 s); updates `clip_file` in `timeline.json`.
- `tests/unit/test_lipsync_module.py`: 10 unit tests.

**Test count:** 142 → 152 (+ 10)

---

### Added — T-014: LipSync engine adapter boundary

- `app/adapters/lipsync_engine_adapter.py`: abstract `LipSyncEngine` with
  `generate(image_path, audio_path, output_path) -> Path`; `LipSyncError`.
- `tests/unit/test_lipsync_adapter.py`: 6 unit tests.

**Test count:** 136 → 142 (+ 6)

---

### Added — T-013: Character assets, fonts, and render presets

- `assets/characters/char_a/base.png` and `assets/characters/char_b/base.png`: synthetic
  character images generated with Pillow.
- `assets/characters/*/metadata.json`: canonical character metadata.
- `assets/fonts/LiberationSans-Bold.ttf`: SIL OFL licensed font.
- `assets/presets/shorts_default.json`: canonical render preset with all 11 required fields.
- `app/services/asset_service.py`: `load_character()`, `load_preset()`, `resolve_font()`,
  `list_backgrounds()`.
- `tests/unit/test_asset_service.py`: 16 unit tests (12 isolated + 4 real-asset).

**Test count:** 120 → 136 (+ 16)

---

### Added — T-012: Subtitle generation

- `app/modules/subtitles.py`: `generate_subtitles(ctx)` — one SRT cue per timeline item;
  gap-free timing; text preserved verbatim; `_sec_to_srt_timestamp()` utility.
- `tests/unit/test_subtitles.py`: 11 unit tests.

**Test count:** 109 → 120 (+ 11)

---

### Added — T-011: Timeline builder and master audio

- `app/modules/timeline_builder.py`: `build_timeline(ctx)` — sequential `start_sec /
  end_sec / duration_sec` without gaps; `master_audio.wav` concatenated via FFmpeg concat
  demuxer; `timeline.json` persisted; `concat_list.txt` preserved for debugging.
- `tests/unit/test_timeline_builder.py`: 14 unit tests.

**Test count:** 95 → 109 (+ 14)

---

### Added — T-010: Per-line audio generation (TTS module)

- `app/modules/tts.py`: `generate_tts(ctx, provider, voice_mapping)` — one WAV segment per
  dialogue line; `manifest.json` with duration measured via ffprobe.
- `app/utils/ffprobe_utils.py`: `get_audio_duration()`.
- `app/utils/audio_utils.py`: `write_silence_wav()`.
- `tests/unit/test_tts_module.py`: 13 unit tests.

**Test count:** 82 → 95 (+ 13)

---

### Added — T-009: TTS provider boundary and voice mapping

- `app/adapters/tts_provider_adapter.py`: abstract `TTSProvider` with
  `synthesize(text, voice_id, output_path)`; `TTSError`; `load_voice_mapping()`;
  `resolve_voice_id()`.
- `config/voices.json` and `config/voices.example.json`.
- `tests/unit/test_tts_adapter.py`: 13 unit tests.

**Test count:** 69 → 82 (+ 13)

---

### Added — T-008: Script writer module

- `app/modules/script_writer.py`: `write_script(ctx, llm_provider)` — validates dialogue
  structure (6–12 lines, alternating speakers, non-empty text, known speakers,
  contiguous indexing, `title_hook`); persists `script.json` and `dialogue.json`.
- `tests/unit/test_script_writer.py`: 15 unit tests.

**Test count:** 54 → 69 (+ 15)

---

### Added — T-007: Script generation prompts and LLM adapter boundary

- `app/adapters/llm_adapter.py`: abstract `ScriptGenerator` with
  `generate(system_prompt, user_prompt, job) -> dict`; `ScriptGenerationError`;
  `load_system_prompt()`; `load_user_prompt(job)`.
- `app/prompts/script_system_prompt.md` and `app/prompts/script_user_prompt_template.md`.
- `tests/unit/test_llm_adapter.py`: 12 unit tests.

**Test count:** 42 → 54 (+ 12)

---

### Added — T-006: Canonical sample inputs and test fixtures

- `inputs/examples/job_001.json`: canonical full example job.
- `inputs/examples/job_002.json`: minimal example job.
- `tests/fixtures/sample_inputs/valid_minimal.json` and `valid_full.json`.
- All validated against `validate_job()`.

---

### Added — T-005: Job context and canonical workspace paths

- `app/utils/path_utils.py`: `job_root(job_id) -> Path`.
- `app/core/job_context.py`: `JobContext` — frozen dataclass; canonical path authority
  for all pipeline artifacts under `output/jobs/<job_id>/`.
- `app/services/file_service.py`: `init_workspace(ctx)` — creates all canonical
  subdirectories; idempotent.
- `tests/unit/test_job_context.py`: 22 unit tests.

**Test count:** 20 → 42 (+ 22)

---

### Added — T-004: Validated job input contract

- `app/core/types.py`: primitive domain types.
- `app/core/contracts.py`: `ValidatedJob` (Pydantic v2 model) with `validate_job()`;
  `job_id` auto-generated as `job_YYYY_MM_DD_NNN`; unknown fields rejected; all defaults
  materialised on validation.
- `tests/unit/test_contracts.py`: 20 unit tests.

**Test count:** 0 → 20 (+ 20)

---

### Added — T-003: CLI, config loader, and logger foundation

- `app/config.py`: `Config` dataclass loading `.env` via `python-dotenv`; canonical env
  variables for API keys, paths, and pipeline settings.
- `app/logger.py`: `get_process_logger()` (standard logging); `JobLogger` — JSON Lines
  writer for `logs/job.log` with required fields `{timestamp_utc, job_id, stage, event,
  message}`.
- `app/main.py`: initial CLI with `--input` and `--batch` argument groups; `--help` works.

---

### Added — T-002: Docker environment validation

- `docker-compose.yml`: added missing `./config:/app/config` volume mount.
- Validated: `docker build -t viral-videos .` succeeds; FFmpeg 7.1.3 and FFprobe 7.1.3
  confirmed available inside the container.

---

## [Foundation] — 2026-03-15 — Project Bootstrap

### Added — T-001: Repository work tree scaffold

- Created canonical directory tree per `DESIGN_SPEC.md` and
  `docs/specs/SYSTEM_ASSET_MANAGEMENT_SPEC.md`:
  `app/`, `assets/backgrounds/{slime,sand,minecraft_parkour,marble_run,misc}/`,
  `scripts/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `output/`,
  `temp/`, `docs/specs/`, `inputs/examples/`, `inputs/batch/`, `config/`.
- `app/utils/__init__.py` created; no runtime artifacts inside `assets/`.

---

### Added — Pre-task foundation commits

| Commit | Description |
|---|---|
| `5d30747` | Initial project proposal and planning documents |
| `13798d8` | `.gitignore` |
| `bc54949` | Documentation restructure and expansion |
| `0479262` | Docker infrastructure and dependency definitions |
| `e0ca212` | Initial application skeleton, tests, and static assets |
| `0f98f23` | Initial `README.md` |
| `6763d43` | Agent workflow operational files |
| `c911153` | Updated `.gitignore` to exclude background MP4 files |
| `17ab567` | Expanded README with detailed pipeline steps and configuration |

---

## Architecture invariants (never change without updating DESIGN_SPEC.md)

- Single Docker container in the MVP.
- File-based pipeline state — no database.
- One job workspace per `job_id` under `output/jobs/<job_id>/`.
- Every external integration behind an adapter interface.
- Pipeline is fail-fast for single-job runs; batch continues on per-item failure.
- Intermediate artifacts are preserved for debugging and auditing.
- `assets/` — static resources only. `output/` — generated artifacts only.

---

## Test suite growth

| Milestone | Tasks | Tests added | Cumulative |
|---|---|---|---|
| Foundation | T-001 – T-003 | 0 | 0 |
| Milestone 1 | T-004 – T-018 | +185 | 185 |
| Milestone 2 | T-019 – T-023 | +38 | 223 |
| Milestone 3 | T-024 – T-026 | 0 | 223 |
| Milestone 4 | T-027 | +10 | **233** |
