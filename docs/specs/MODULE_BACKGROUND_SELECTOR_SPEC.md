# MODULE_BACKGROUND_SELECTOR_SPEC

## Purpose

Define how the project selects, trims, loops, and normalizes the satisfying background video for one job.

## Inputs

- validated job input;
- `output/jobs/<job_id>/script/timeline.json`
- background assets under `assets/backgrounds/`

## Outputs

- `output/jobs/<job_id>/background/prepared_background.mp4`

## Required behavior

- The module must choose exactly one background asset per job.
- If `background_style` is not `auto`, the selected asset must come from the matching category.
- If `background_style` is `auto`, selection must be deterministic for the same validated job input after defaults are materialized.
- The prepared background duration must be at least the final timeline duration.
- If the source background is shorter than required, the module must loop it.
- If the source background is longer than required, the module must trim it.
- The prepared background must be exported in vertical `9:16`.
- The prepared background must not be the authoritative audio source for the final video.

## Normalization rules

- target canvas is `1080x1920` for the MVP;
- scale-to-cover then crop must be used to avoid letterboxing;
- the background must preserve continuous motion;
- the background must not contain subtitles, titles, or watermarks added by this project.

## Failure conditions

- no background asset exists for the requested style;
- background file is unreadable;
- prepared output is shorter than the timeline;
- export to `prepared_background.mp4` fails.

## Acceptance tests

- A job with explicit `background_style` uses the requested category.
- A job with `background_style: auto` selects the same asset when re-run with the same validated job input.
- A short source background is looped to the required duration.
- The prepared background is `1080x1920`.
- The prepared background file exists at the expected path.
