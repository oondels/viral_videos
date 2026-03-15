# MODULE_SUBTITLES_SPEC

## Purpose

Define the MVP subtitle generation contract using the timeline as the single source of truth.

## Inputs

- `output/jobs/<job_id>/script/timeline.json`

## Outputs

- `output/jobs/<job_id>/subtitles/subtitles.srt`

## Required behavior

- The MVP subtitle source of truth is the timeline text, not ASR.
- The module must generate exactly one subtitle cue per timeline item.
- Subtitle cue order must match timeline order exactly.
- Cue text must match `timeline.text` exactly.
- Cue start time must equal `timeline.start_sec`.
- Cue end time must equal `timeline.end_sec`.
- The module must write valid SRT numbering starting at `1`.

## Formatting rules

- one cue per timeline item;
- no subtitle rewriting or paraphrasing;
- no speaker labels in subtitle text;
- no extra punctuation may be introduced by the subtitle module.

## Failure conditions

- timeline file is missing;
- timeline items are unordered;
- a cue would have `end <= start`;
- SRT serialization fails.

## Acceptance tests

- A timeline with 6 items produces 6 subtitle cues.
- The first cue starts at `00:00:00,000`.
- Cue text matches timeline text exactly.
- Cue numbering is contiguous and starts at `1`.
- The generated file is parseable as valid SRT.
