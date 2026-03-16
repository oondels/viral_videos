# MODULE_TTS_SPEC

## Purpose

Define the behavior for converting each dialogue line into a normalized audio segment plus a manifest.

## Inputs

- `output/jobs/<job_id>/script/dialogue.json`
- active voice config at `config/voices.json`
- `TTSProvider` interface

## Outputs

- `output/jobs/<job_id>/audio/segments/001_char_a.mp3`
- `output/jobs/<job_id>/audio/segments/002_char_b.mp3`
- `output/jobs/<job_id>/audio/manifest.json`

## Manifest contract

Each manifest item must contain:

```json
{
  "index": 1,
  "speaker": "char_a",
  "text": "Why does everything cost more now?",
  "voice_id": "voice_char_a",
  "audio_file": "output/jobs/<job_id>/audio/segments/001_char_a.mp3",
  "duration_sec": 2.31
}
```

## Required behavior

- The module must generate exactly one audio file per dialogue item.
- File naming must preserve line order and speaker id.
- Providers that return MP3 natively (e.g. ElevenLabs) must save the audio directly without conversion.
- All persisted segment files must share a consistent format per provider run.
- `duration_sec` must be measured from the persisted file, not estimated.
- Manifest order must match dialogue order exactly.
- Voice mapping resolution must use `config/voices.json` as the canonical runtime source.
- Missing voice mapping for any speaker must fail the module before partial generation continues.

## Validation rules

- `index` matches the dialogue item index;
- `speaker` matches the dialogue item speaker;
- `text` matches the dialogue item text exactly;
- `audio_file` exists on disk;
- `duration_sec` is greater than `0`.

## Failure conditions

- missing voice mapping for a speaker;
- provider error while generating any segment;
- persisted audio file is unreadable;
- persisted audio duration is `0` or negative.

## Acceptance tests

- A 6-line dialogue produces 6 segment files and 6 manifest items.
- Segment file names follow `NNN_<speaker>.mp3`.
- Every manifest item points to an existing file.
- A missing voice mapping raises a clear error and stops the module.
- The order of manifest items matches the order in `dialogue.json`.
