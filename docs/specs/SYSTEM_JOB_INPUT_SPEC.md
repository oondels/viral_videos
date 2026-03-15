# SYSTEM_JOB_INPUT_SPEC

## Purpose

Define the canonical input contract for a single video generation job.

## In scope

- input JSON schema;
- defaults and validation;
- generated `job_id`;
- workspace directory creation requirements.

## Out of scope

- batch file parsing;
- script generation behavior;
- render layout behavior.

## Input contract

The system must accept one JSON object with this shape.
Only `topic` is required in the raw payload; omitted optional fields must be materialized during validation:

```json
{
  "topic": "Explain inflation in a funny way",
  "duration_target_sec": 30,
  "background_style": "minecraft_parkour",
  "characters": ["char_a", "char_b"],
  "output_preset": "shorts_default"
}
```

## Validation rules

- `topic` is required, must be a non-empty string after trim.
- `duration_target_sec` is optional and defaults to the runtime default duration, `30` in the MVP.
- When provided, `duration_target_sec` must be an integer between `20` and `45`, inclusive.
- `characters` is optional and defaults to `["char_a", "char_b"]`.
- After defaults are materialized, `characters` must contain exactly `2` unique character ids.
- `background_style` is optional and defaults to `auto`.
- `output_preset` is optional and defaults to `shorts_default`.
- Unknown top-level fields must be rejected in the MVP.
- The client must not provide `job_id`; the system generates it.

## Derived values

- `job_id` format must be `job_YYYY_MM_DD_NNN`.
- The system must create:
  - `output/jobs/<job_id>/script/`
  - `output/jobs/<job_id>/audio/segments/`
  - `output/jobs/<job_id>/audio/master/`
  - `output/jobs/<job_id>/clips/`
  - `output/jobs/<job_id>/background/`
  - `output/jobs/<job_id>/subtitles/`
  - `output/jobs/<job_id>/render/`
  - `output/jobs/<job_id>/logs/`

## Required behavior

- Input validation must happen before any external provider call.
- Invalid input must stop the job before artifact generation starts.
- The validated job object is the only source of truth for downstream modules.
- Defaults must be materialized in the validated job object, not applied implicitly later.

## Failure conditions

- missing `topic`;
- empty or whitespace-only topic;
- provided duration outside the allowed range;
- fewer or more than two provided or materialized characters;
- duplicate characters;
- unknown preset or unknown background style, when provided.

## Acceptance tests

- A job with only `topic` produces a validated job object with defaults filled in.
- A job with `duration_target_sec: 19` fails validation.
- A job with one character fails validation.
- A job with duplicate characters fails validation.
- A job with an extra unknown field fails validation.
