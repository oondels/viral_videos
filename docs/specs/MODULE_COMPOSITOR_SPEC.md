# MODULE_COMPOSITOR_SPEC

## Purpose

Define the final video composition contract for turning all generated artifacts into one publishable MP4.

## Inputs

- `output/jobs/<job_id>/background/prepared_background.mp4`
- `output/jobs/<job_id>/audio/master/master_audio.wav`
- `output/jobs/<job_id>/script/timeline.json`
- `output/jobs/<job_id>/subtitles/subtitles.srt`
- `output/jobs/<job_id>/script/script.json`
- character base assets from `assets/characters/<character_id>/base.png`
- font assets referenced by the selected render preset under `assets/fonts/`
- render preset from `assets/presets/<preset>.json`

## Outputs

- `output/jobs/<job_id>/render/final.mp4`
- `output/jobs/<job_id>/render/render_metadata.json`

## Render contract

The MVP final video must be:

- resolution `1080x1920`;
- frame rate `30 fps`;
- codec `H.264`;
- pixel format `yuv420p`;
- audio source `master_audio.wav`.

## Required behavior

- The compositor must use exactly one prepared background for the full video.
- The compositor must use the master audio as the only authoritative final audio track.
- The compositor must burn subtitles into the final output.
- The compositor must render exactly two visual character roles: active speaker and inactive speaker.
- The active speaker visual must come from the current `timeline.clip_file`.
- The inactive speaker visual must come from the non-speaking character `base.png`.
- The active speaker at any moment is determined by the current timeline item speaker.
- The title hook must be taken from `script.json.title_hook`.
- The title hook must become visible within the first `2` seconds of the final video.
- Layout geometry must come from the selected render preset, not hardcoded magic numbers in the module.
- Title and subtitle styling must come from the selected render preset, including font references.

## Speaker transition behavior

- Each character occupies a fixed horizontal position for the entire video duration: the first character (alphabetically) is always on the left, the second is always on the right. No character swaps sides at any point.
- Both characters must be visible in every frame of the video.
- When the active speaker changes, the newly active character smoothly scales from `inactive_speaker_box` dimensions to `active_speaker_box` dimensions over `speaker_transition_duration_sec` seconds. Simultaneously, the previously active character scales from `active_speaker_box` to `inactive_speaker_box` in the same interval.
- The scale transition must use an ease-in-out curve: `(1 - cos(PI * t / D)) / 2` where `D` is `speaker_transition_duration_sec`.
- During the scale animation, each character's anchor point (controlled by `speaker_anchor`) must remain at a fixed horizontal position. For `center` anchor, the character's center x stays constant; for `left`, the left edge stays constant; for `right`, the right edge stays constant.
- There must be no hard cut (instantaneous size change) between consecutive frames at any speaker transition point.
- Implementation uses the FFmpeg `scale` filter with `eval=frame` and time-based expressions referencing `t`, integrated into the existing `filter_complex` builder. No intermediate files are required.

## Required preset fields

The active preset must define:

- canvas size;
- frame rate;
- title box;
- title timing;
- title style;
- active speaker box;
- inactive speaker box;
- subtitle safe area;
- subtitle style;
- `speaker_transition_duration_sec` (float, seconds — default `0.15`);
- `speaker_anchor` (string: `left` | `center` | `right` — default `center`).

## Render metadata contract

`render_metadata.json` must contain at least:

- `job_id`
- `output_file`
- `duration_sec`
- `preset_name`
- `background_file`
- `subtitle_file`
- `timeline_item_count`
- `speaker_transition_duration_sec`

## Failure conditions

- missing preset file;
- missing clip file for any timeline item;
- missing character `base.png` required for the inactive speaker render;
- missing prepared background;
- missing master audio;
- missing font asset referenced by the active preset;
- FFmpeg composition failure;
- final output missing on disk.

## Acceptance tests

- The final video exists at `render/final.mp4`.
- The final video is `1080x1920`.
- The final video duration matches the timeline duration within `0.10` seconds.
- The final audio track matches `master_audio.wav`.
- The title hook is visible within the first `2` seconds.
- `render_metadata.json` exists and references the final output path.
- No hard cut in scale between consecutive frames at any speaker transition point.
- Both characters are visible in every frame of the video.
- Each character's horizontal position (x) remains constant throughout the entire video duration.
