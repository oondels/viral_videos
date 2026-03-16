# AGENT BRIEFING

This document is the complete onboarding brief for a code agent working on this
repository.  Read it once per session before touching any file.  It answers:

1. What this system does and why it is built this way.
2. Where every relevant piece of code lives.
3. How to navigate, extend, and fix the codebase without breaking invariants.
4. What to do, in what order, in every predictable situation.
5. What never to do.

---

## 1. What this system is

A CLI tool that takes a JSON job description and produces a vertical MP4 video
(1080×1920, 9:16) of two characters having a short humorous dialogue.

One command → one input → one video:

```
python -m app.main --input inputs/examples/job_001.json
```

The pipeline is a linear chain of 10 stages.  Each stage reads artifacts written
by the previous stage and writes artifacts consumed by the next.  There is no
database, no message queue, no shared state — only files on disk.

---

## 2. The 10-stage pipeline (canonical order — never change)

```
1.  validate_input        reads: job JSON file
                          writes: nothing (raises on failure)

2.  init_job_workspace    reads: ValidatedJob
                          writes: output/jobs/<job_id>/ directory tree
                                  output/jobs/<job_id>/job_input.json

3.  write_script          reads: job, LLM provider
                          writes: script/script.json
                                  script/dialogue.json

4.  generate_tts          reads: dialogue.json, TTS provider, voices config
                          writes: audio/segments/NNN_speaker.wav  (one per line)
                                  audio/manifest.json

5.  build_timeline        reads: manifest.json
                          writes: script/timeline.json
                                  audio/master/master_audio.wav (normalised)
                                  audio/master/concat_list.txt  (debug)

6.  generate_lipsync      reads: timeline.json, character base.png files
                          writes: clips/NNN_speaker_talk.mp4 (one per line)
                                  updates clip_file field in timeline.json

7.  prepare_background    reads: assets/backgrounds/<style>/
                          writes: background/prepared_background.mp4

8.  generate_subtitles    reads: timeline.json
                          writes: subtitles/subtitles.srt

9.  compose_video         reads: all of the above
                          writes: render/final.mp4
                                  render/render_metadata.json

10. finalize_job          reads: nothing
                          writes: job.log event (stage_completed)
```

**Execution rule:** single-job is fail-fast.  Any stage exception stops
the pipeline immediately and raises `PipelineError`.  Upstream artifacts
remain on disk.  Never swallow exceptions silently.

---

## 3. Canonical workspace layout

Every job lives entirely under:

```
output/jobs/<job_id>/
├── script/
│   ├── script.json          ← title_hook + full dialogue
│   ├── dialogue.json        ← cleaned dialogue lines only
│   └── timeline.json        ← start_sec, end_sec, clip_file per line
├── audio/
│   ├── segments/
│   │   ├── 001_char_a.wav
│   │   └── 002_char_b.wav
│   ├── master/
│   │   ├── master_audio.wav  ← normalised, -14 LUFS
│   │   └── concat_list.txt
│   └── manifest.json
├── clips/
│   ├── 001_char_a_talk.mp4
│   └── 002_char_b_talk.mp4
├── background/
│   └── prepared_background.mp4
├── subtitles/
│   └── subtitles.srt
├── render/
│   ├── final.mp4
│   └── render_metadata.json
├── logs/
│   └── job.log
└── job_input.json           ← serialised ValidatedJob, used by --resume
```

**Rule:** never assemble these paths by hand.  Always use `JobContext`:

```python
ctx.script_json()          # output/jobs/<id>/script/script.json
ctx.master_audio()         # output/jobs/<id>/audio/master/master_audio.wav
ctx.clip(3, "char_b")      # output/jobs/<id>/clips/003_char_b_talk.mp4
ctx.final_mp4()            # output/jobs/<id>/render/final.mp4
```

`JobContext` is in `app/core/job_context.py`.  It is the single path authority.

---

## 4. Codebase map — where everything lives

```
app/
├── main.py                  CLI entry point (--input, --batch, --resume)
├── pipeline.py              run_pipeline(), resume_pipeline()
├── batch.py                 run_batch()
├── config.py                Config dataclass, loads .env
├── logger.py                get_process_logger(), JobLogger (JSON Lines)
│
├── core/
│   ├── contracts.py         ValidatedJob (Pydantic v2), validate_job()
│   ├── job_context.py       JobContext — canonical path authority
│   ├── types.py             primitive domain types
│   └── exceptions.py        ViralVideosError hierarchy
│
├── adapters/                external provider boundaries (never call APIs directly)
│   ├── llm_adapter.py       ScriptGenerator ABC, ScriptGenerationError
│   ├── tts_provider_adapter.py  TTSProvider ABC, TTSError, load_voice_mapping()
│   ├── lipsync_engine_adapter.py  LipSyncEngine ABC, LipSyncError
│   ├── ffmpeg_adapter.py    run_ffmpeg(), concat_audio(), normalize_audio(), …
│   ├── openai_llm_adapter.py      concrete OpenAI implementation
│   ├── elevenlabs_tts_adapter.py  concrete ElevenLabs implementation
│   └── static_lipsync_adapter.py  concrete static-image lip-sync (MVP default)
│
├── modules/                 pipeline stage implementations
│   ├── script_writer.py     write_script(ctx, llm_provider)
│   ├── tts.py               generate_tts(ctx, provider, voice_mapping)
│   ├── timeline_builder.py  build_timeline(ctx)
│   ├── lipsync.py           generate_lipsync(ctx, engine)
│   ├── background_selector.py  prepare_background(ctx, duration_sec)
│   ├── subtitles.py         generate_subtitles(ctx)
│   └── compositor.py        compose_video(ctx)
│
├── services/
│   ├── file_service.py      init_workspace(ctx)
│   ├── asset_service.py     load_character(), load_preset(), resolve_font()
│   └── render_service.py    write_render_metadata()
│
├── utils/
│   ├── path_utils.py        job_root(job_id) -> Path
│   ├── ffprobe_utils.py     get_media_duration(), get_video_dimensions()
│   ├── audio_utils.py       write_silence_wav()
│   ├── video_utils.py       make_color_video()  [test utility]
│   └── retry.py             retry(fn, retryable, max_attempts)
│
└── prompts/
    ├── script_system_prompt.md
    └── script_user_prompt_template.md

assets/
├── characters/
│   ├── char_a/base.png + metadata.json
│   └── char_b/base.png + metadata.json
├── fonts/LiberationSans-Bold.ttf
├── presets/shorts_default.json
└── backgrounds/{slime,sand,minecraft_parkour,marble_run,misc}/

config/
├── voices.json              char_id → ElevenLabs voice_id mapping
└── voices.example.json

tests/
├── unit/                    fast, no FFmpeg, no real API calls
└── integration/             use real FFmpeg; stub providers only
```

---

## 5. Canonical patterns — how things are done here

### 5.1 Adding a new pipeline stage

1. Create `app/modules/<name>.py` with a single public function:
   `def <stage_name>(ctx: JobContext, ...) -> <artifact_path>`.
2. Raise a domain-specific `XxxError(Exception)` on failure — never `raise Exception(...)`.
3. Read inputs via `ctx.*()` methods.  Write outputs to `ctx.*()` paths.
4. Register the stage in `run_pipeline()` in `app/pipeline.py` using `_run()` or
   `_run_with_retry()`.  Do not call the module function directly from `main.py`.
5. Add the canonical output artifact check to `resume_pipeline()` in `app/pipeline.py`.
6. Write tests in `tests/unit/` or `tests/integration/` following existing patterns.

### 5.2 Adding a new external provider

1. The ABC lives in `app/adapters/<capability>_adapter.py`.  Do not modify it.
2. Create `app/adapters/<provider>_<capability>_adapter.py` with a concrete subclass.
3. Wire it in `app/main.py` → `_build_providers()`.
4. Credentials go in `.env` and are accessed via `config.<field>`.
   Never hardcode API keys or embed them in the Docker image.

### 5.3 Adding a new character

1. Create `assets/characters/<char_id>/base.png` and `metadata.json`.
2. Add `<char_id>: <voice_id>` to `config/voices.json`.
3. Add `<char_id>` to `_ALLOWED_CHARACTERS` in `app/core/contracts.py`.
4. No code changes needed in any module.

### 5.4 Error handling

```python
# CORRECT — domain error with context
raise CompositorError(f"Clip file missing for item {item['index']}: {path}")

# WRONG — bare exception
raise Exception("something went wrong")

# WRONG — swallowing
try:
    ...
except Exception:
    pass
```

Every module has exactly one exception class.  Use it.

### 5.5 FFmpeg calls

Never call `subprocess` directly.  Always use `app/adapters/ffmpeg_adapter.py`:

```python
from app.adapters.ffmpeg_adapter import run_ffmpeg, FFmpegError

run_ffmpeg(["ffmpeg", "-y", "-i", str(input), ...])  # raises FFmpegError on failure
```

### 5.6 Logging

```python
# Process-level (before workspace exists)
logger = get_process_logger()
logger.info("message")

# Job-level (inside a stage, after init_workspace)
job_log.log(stage, "stage_started",   "Starting <stage>")
job_log.log(stage, "stage_completed", "Completed <stage>", duration_ms=elapsed)
job_log.log(stage, "stage_failed",    "Failed <stage>",
            duration_ms=elapsed, error_type=..., error_message=...)
job_log.log(stage, "stage_skipped",   "Skipped <stage> — artifacts present")
```

Only four valid event values: `stage_started`, `stage_completed`, `stage_failed`,
`stage_skipped`.  Do not invent new event names.

### 5.7 Tests

- Unit tests: `tests/unit/test_<module>.py`.  Use `tmp_path`, `monkeypatch`.
  Never call real APIs.  Never write to `output/` directly.
- Integration tests: `tests/integration/test_<feature>.py`.  Real FFmpeg allowed.
  Use `StubLLM`, `StubTTS`, `StubLipSync` from `tests/integration/test_pipeline.py`.
- Run: `docker run --rm -v $(pwd):/app -w /app viral-videos pytest tests/ -q`
- All tests must pass before marking a task complete.

---

## 6. Contracts that must never be broken

| Contract | Location | Why it matters |
|---|---|---|
| Stage order 1–10 | `pipeline.py`, `DESIGN_SPEC.md` §7.4 | downstream stages depend on upstream artifacts |
| `job_id` format: `job_YYYY_MM_DD_NNN` | `contracts.py` | used as directory name and log key |
| `JobContext` is the only path authority | `job_context.py` | prevents path drift between modules |
| Every external call behind an ABC adapter | `adapters/` | enables stubbing in tests and provider swap |
| `assets/` is read-only at runtime | — | no module may write to `assets/` |
| `output/` is write-only at runtime | — | no module may read from `output/` of another job |
| `job_input.json` written by `init_workspace` | `file_service.py` | required by `--resume` to reconstruct job |
| Final MP4: 1080×1920, SAR 1:1, 44100 Hz stereo AAC | `compositor.py` | platform compatibility |

---

## 7. Decision rules

**When to use `_run()` vs `_run_with_retry()`:**
- `_run_with_retry()` → stages that call external APIs: `write_script`, `generate_tts`,
  `generate_lipsync`.
- `_run()` → local computation stages: `build_timeline`, `prepare_background`,
  `generate_subtitles`, `compose_video`.

**When to stop and update documentation instead of writing code:**
- The task description contradicts `DESIGN_SPEC.md` or any spec in `docs/specs/`.
- A required spec file does not exist for the capability being implemented.
- Implementing the task would require changing an invariant listed in section 6 above.

**When to use `resume_pipeline()` vs `run_pipeline()`:**
- `run_pipeline()` → always, for new jobs from a JSON input file.
- `resume_pipeline()` → only when `output/jobs/<job_id>/job_input.json` already exists
  and you want to re-run from partial artifacts.

**When a test fails:**
- Fix the code, not the test assertion — unless the test is verifying a contract that
  was intentionally changed by the current task.

**How to choose between `tests/unit/` and `tests/integration/`:**
- If the test needs real FFmpeg output: `tests/integration/`.
- If the test can use `write_silence_wav()` or `make_color_video()` stubs: `tests/unit/`.
- If unsure: prefer `tests/unit/` (faster, less flaky).

---

## 8. What never to do

- **Never assemble artifact paths by hand.**
  Always use `JobContext` methods.

- **Never call FFmpeg or FFprobe via `subprocess` directly.**
  Use `app/adapters/ffmpeg_adapter.py` and `app/utils/ffprobe_utils.py`.

- **Never write to `assets/`.**
  It contains only static resources committed to the repository.

- **Never modify `run_pipeline()`** when adding features that extend the pipeline.
  Add new functions (`resume_pipeline`, batch wrappers) that compose with it.

- **Never embed credentials in code or Docker image.**
  All credentials go in `.env` and are read via `app/config.py`.

- **Never batch multiple tasks into one commit.**
  One task = one commit.  The commit message should reference the task ID.

- **Never mark a task `status: true` before its validation checks pass.**
  Run `pytest tests/ -q` before every status update.

- **Never create new exception classes outside `app/core/exceptions.py`
  or the module's own file.**
  Each module has exactly one exception class at the top of the file.

- **Never write to `PROGRESS.md` before the task's tests pass.**
  The entry is a record of what succeeded, not what was attempted.

---

## 9. Session startup protocol (read this every time)

```
1. Read TASKS.md           → identify the first task with status: false
                             whose depends_on tasks are all status: true
2. Read PROGRESS.md        → recover decisions and discoveries from prior sessions
3. Read docs/DESIGN_SPEC.md → confirm invariants and lookup spec files
4. Open only the spec files listed under read_first for the selected task
5. Implement exactly one task
6. Run: docker run --rm -v $(pwd):/app -w /app viral-videos pytest tests/ -q
7. If all tests pass:
   a. Set task status: true in TASKS.md
   b. Append one entry to PROGRESS.md
   c. Create one commit (message: "<type>: T-XXX — <short description>")
8. Stop.  The next session starts at step 1.
```

If step 6 fails: fix the code, re-run.  Do not advance to step 7.
If a stop condition in the task fires: update documentation, do not write code.

---

## 10. Key files for agent reference

| File | Purpose |
|---|---|
| `TASKS.md` | operational task queue; source of truth for what to do next |
| `PROGRESS.md` | persistent memory of completed tasks; read before starting |
| `docs/DESIGN_SPEC.md` | root architecture source of truth; lookup index for specs |
| `docs/specs/*.md` | detailed specs per capability; open only what the task needs |
| `CLAUDE.md` | project instructions for the agent runner |
| `CHANGELOG.md` | full project history by milestone; useful for audit and context |
| `bugs/` | post-mortem reports for diagnosed and resolved bugs |
| `.env` | runtime credentials (never commit, never log) |
| `config/voices.json` | character → ElevenLabs voice_id mapping |
| `assets/presets/shorts_default.json` | canonical render preset |
