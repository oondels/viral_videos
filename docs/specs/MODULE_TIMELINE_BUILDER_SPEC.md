# MODULE_TIMELINE_BUILDER_SPEC

## Purpose

Define the rules for consolidating audio segments into one master track and one timeline artifact.

## Inputs

- `output/jobs/<job_id>/audio/manifest.json`
- audio segment files referenced by the manifest

## Outputs

- `output/jobs/<job_id>/audio/master/master_audio.wav`
- `output/jobs/<job_id>/script/timeline.json`

## Timeline contract

Each timeline item must contain:

```json
{
  "index": 1,
  "speaker": "char_a",
  "text": "Why does everything cost more now?",
  "start_sec": 0.0,
  "end_sec": 2.31,
  "duration_sec": 2.31,
  "audio_file": "output/jobs/<job_id>/audio/segments/001_char_a.mp3",
  "clip_file": null
}
```

## Required behavior

- The module must concatenate audio segments in manifest order.
- The first item must start at `0.0`.
- The next item must start exactly where the previous item ends.
- The MVP timeline must not insert gaps or overlaps between lines.
- `duration_sec` must equal `end_sec - start_sec`.
- `clip_file` must exist as a field and start as `null`.
- `master_audio.wav` must contain the same ordered segments used in the timeline.

## Validation rules

- indexes are contiguous and start at `1`;
- `start_sec` is monotonic;
- `end_sec` is greater than `start_sec`;
- the final `end_sec` matches the master audio duration within `0.05` seconds.

## Failure conditions

- manifest is empty;
- referenced segment file is missing;
- segment order is inconsistent;
- total master duration does not match the timeline.

## Acceptance tests

- A manifest with 6 items produces 6 timeline items.
- The first timeline item starts at `0.0`.
- There are no gaps or overlaps between consecutive items.
- The last `end_sec` matches the measured duration of `master_audio.wav`.
- Every timeline item points to the original segment file from the manifest.
