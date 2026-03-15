# SYSTEM_PIPELINE_ORCHESTRATION_SPEC

## Purpose

Define the single-job pipeline order, stage boundaries, and fatal-error behavior.

## Inputs

- CLI call with `--input <job.json>`
- one validated job input

## Outputs

- a full job workspace under `output/jobs/<job_id>/`
- partial artifacts for completed stages when a later stage fails
- final `render/final.mp4` when the pipeline succeeds

## Canonical stage order

The orchestrator must run stages in this exact order:

1. `validate_input`
2. `init_job_workspace`
3. `write_script`
4. `generate_tts`
5. `build_timeline`
6. `generate_lipsync`
7. `prepare_background`
8. `generate_subtitles`
9. `compose_video`
10. `finalize_job`

## Required behavior

- Each stage must consume only the artifacts produced by earlier stages.
- Each stage must write its output to the canonical job paths before the next stage starts.
- Single-job execution is fail-fast in the MVP.
- If a stage fails, the orchestrator must stop immediately.
- A validation failure must stop the run without creating a fake job workspace only for logging.
- Completed artifacts from earlier stages must remain on disk for inspection.
- The orchestrator must not silently regenerate upstream artifacts after a downstream failure.

## Stage responsibilities

- `validate_input`: parse JSON, apply defaults, materialize runtime defaults, and reject invalid input.
- `init_job_workspace`: create directories and initialize logging.
- `write_script`: generate `script.json` and `dialogue.json`.
- `generate_tts`: generate audio segments and `manifest.json`.
- `build_timeline`: generate `master_audio.wav` and `timeline.json`.
- `generate_lipsync`: generate one clip per timeline item and update `clip_file`.
- `prepare_background`: create `prepared_background.mp4`.
- `generate_subtitles`: create `subtitles.srt`.
- `compose_video`: create `final.mp4` and `render_metadata.json`.
- `finalize_job`: record final job status and exit cleanly.

## Failure conditions

- any stage raises an unhandled exception;
- a required artifact for the next stage is missing;
- a stage writes malformed output.

## Acceptance tests

- A valid example input runs through all stages and produces `final.mp4`.
- A failure in `generate_lipsync` preserves script, audio, and timeline artifacts.
- A failure in `validate_input` produces no downstream artifacts.
- Stages execute in the canonical order above.
