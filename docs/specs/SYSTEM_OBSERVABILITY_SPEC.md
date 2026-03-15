# SYSTEM_OBSERVABILITY_SPEC

## Purpose

Define how the pipeline records logs, stage events, and execution metadata.

## In scope

- per-job logging;
- canonical stage event names;
- render metadata;
- batch summary metadata.

## Log file contract

Each job that passes `validate_input` must write:

- `output/jobs/<job_id>/logs/job.log`

The MVP log format must be JSON Lines, one event per line.
Validation failures that happen before `job_id` materialization or workspace creation may be reported only through the process logger and must not force creation of a job workspace.

Each log event must contain:

- `timestamp_utc`
- `job_id`
- `stage`
- `event`
- `message`

Optional fields:

- `duration_ms`
- `artifact_path`
- `error_type`
- `error_message`

## Canonical events

Every stage must use these event names:

- `stage_started`
- `stage_completed`
- `stage_failed`

## Canonical stages

The allowed stage names are:

- `validate_input`
- `init_job_workspace`
- `write_script`
- `generate_tts`
- `build_timeline`
- `generate_lipsync`
- `prepare_background`
- `generate_subtitles`
- `compose_video`
- `finalize_job`

## Required behavior

- Once `init_job_workspace` begins, the orchestrator must write `stage_started` before a stage begins.
- The orchestrator must write `stage_completed` only after the stage output is safely persisted.
- On failure after workspace initialization, the orchestrator must write exactly one `stage_failed` event for the failing stage.
- Validation failures before workspace creation must still emit machine-readable process logs, but they do not require `logs/job.log`.
- `render_metadata.json` must be written only after `final.mp4` exists.
- Batch processing must also write `output/batch_reports/latest_report.json`.

## Failure conditions

- log file cannot be opened for append;
- log event is missing required fields;
- render metadata is written before final output exists.

## Acceptance tests

- A successful single job produces start and completion events from `init_job_workspace` through `finalize_job`.
- A failed single job after workspace initialization produces exactly one `stage_failed` event for the failing stage.
- A validation failure before workspace creation does not create `logs/job.log`.
- Every log line is valid JSON.
- `render_metadata.json` is absent on failed renders and present on successful renders.
