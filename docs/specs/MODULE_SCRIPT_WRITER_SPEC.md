# MODULE_SCRIPT_WRITER_SPEC

## Purpose

Define the source-of-truth behavior for generating the structured script and dialogue artifacts.

## Inputs

- validated job input;
- `ScriptGenerator` provider interface;
- prompt files from `app/prompts/`.

## Outputs

- `output/jobs/<job_id>/script/script.json`
- `output/jobs/<job_id>/script/dialogue.json`

## Output contract

`script.json` must contain:

```json
{
  "job_id": "job_2026_03_15_001",
  "topic": "Explain inflation in a funny way",
  "title_hook": "Why your money suddenly feels weaker",
  "dialogue": [
    {"index": 1, "speaker": "char_a", "text": "Why does everything cost more now?"},
    {"index": 2, "speaker": "char_b", "text": "Because your money is doing less push-ups than prices are."}
  ]
}
```

`dialogue.json` must contain only the `dialogue` array.

## Required behavior

- The module must generate exactly one short dialogue for the provided topic.
- The dialogue must use exactly the two character ids from the input job.
- Speakers must alternate strictly from one line to the next.
- Dialogue length must be between `6` and `12` lines in the MVP.
- The module must use `job.duration_target_sec` as a planning input for line count and verbosity.
- The estimated spoken duration of the generated dialogue should target `job.duration_target_sec` within `5` seconds before TTS.
- Each line must be plain spoken text, not narration.
- Lines must not include speaker labels, stage directions, markdown, or emojis.
- The script language must match the input topic language.
- `title_hook` must be non-empty and shorter than `80` characters.
- The generated dialogue must be saved before any TTS step begins.

## Validation rules

- line indexes start at `1` and increase by `1`;
- every `speaker` must exist in `job.characters`;
- every `text` field must be non-empty after trim;
- no consecutive lines may use the same speaker.

## Failure conditions

- provider returns invalid JSON;
- provider omits required fields;
- dialogue fails alternation or line-count validation;
- dialogue estimate is grossly incompatible with the requested target duration;
- any line is empty after trim.

## Acceptance tests

- A valid job generates both `script.json` and `dialogue.json`.
- A dialogue with consecutive repeated speakers is rejected.
- A dialogue with fewer than `6` lines is rejected.
- A generated dialogue that clearly ignores `duration_target_sec` is rejected.
- A dialogue with empty text is rejected.
- `dialogue.json` contains the same ordered dialogue found in `script.json`.
