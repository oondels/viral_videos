# MODULE_LIPSYNC_SPEC

## Purpose

Define the behavior for generating one talking-head clip per timeline item.

## Inputs

- `output/jobs/<job_id>/script/timeline.json`
- character assets from `assets/characters/<character_id>/`
- `LipSyncEngine` interface

## Outputs

- `output/jobs/<job_id>/clips/001_char_a_talk.mp4`
- `output/jobs/<job_id>/clips/002_char_b_talk.mp4`
- updated `output/jobs/<job_id>/script/timeline.json` with `clip_file`

## Required behavior

- The module must generate exactly one clip per timeline item.
- The selected character asset must match the `speaker` field.
- Output file naming must preserve line order and speaker id.
- The clip must visually represent the requested character speaking the matching audio.
- The clip duration must match the source audio duration within `0.10` seconds.
- The clip must not contain burned subtitles or title text.
- If the engine forces an audio track in the clip, the compositor must ignore that track; the master audio remains authoritative.

## Timeline update rule

- After a clip is generated, the corresponding `timeline.json` item must be updated in place.
- `clip_file` must contain the generated clip path.
- No other timeline fields may be changed by this module.

## Failure conditions

- missing character asset;
- missing source audio file;
- engine execution failure;
- generated clip path missing on disk;
- generated clip duration outside the allowed tolerance.

## Acceptance tests

- A timeline with 6 items produces 6 clip files.
- Each generated clip updates exactly one `clip_file` in the timeline.
- Every clip file name follows `NNN_<speaker>_talk.mp4`.
- A missing character asset fails the module with a clear error.
- The module does not modify `start_sec`, `end_sec`, or `text`.
