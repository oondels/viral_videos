# Specs Index

## Purpose

This folder turns each major project capability into a single source of truth that is clear, testable, and implementation-ready for both humans and agents.

## Rules

- If code and spec disagree, the spec wins until the spec is updated.
- Every implementation task must point to one or more files in this folder.
- Specs define behavior, contracts, artifacts, error rules, and acceptance tests.
- Specs intentionally remove ambiguity; if a detail is missing, the spec must be updated before implementation continues.

## Standard spec structure

Each spec in this folder should define:

1. purpose;
2. scope;
3. inputs;
4. outputs;
5. required behavior;
6. failure conditions;
7. acceptance tests.

## Spec files

- `SYSTEM_JOB_INPUT_SPEC.md`: input contract, defaults, validation rules, and job identity.
- `MODULE_SCRIPT_WRITER_SPEC.md`: script generation contract and dialogue rules.
- `MODULE_TTS_SPEC.md`: per-line audio generation and manifest rules.
- `MODULE_TIMELINE_BUILDER_SPEC.md`: master audio and timeline generation rules.
- `MODULE_LIPSYNC_SPEC.md`: per-line talking head clip generation.
- `MODULE_BACKGROUND_SELECTOR_SPEC.md`: background selection, looping, and vertical preparation.
- `MODULE_SUBTITLES_SPEC.md`: subtitle generation rules from the timeline.
- `MODULE_COMPOSITOR_SPEC.md`: final video composition and render output.
- `SYSTEM_PIPELINE_ORCHESTRATION_SPEC.md`: stage order, stage contracts, and fail-fast behavior.
- `SYSTEM_ASSET_MANAGEMENT_SPEC.md`: fixed asset tree, loading rules, and validation.
- `SYSTEM_BATCH_PROCESSING_SPEC.md`: sequential batch generation and final report contract.
- `SYSTEM_OBSERVABILITY_SPEC.md`: logs, metadata, and event naming rules.

## Recommended implementation order

1. `SYSTEM_JOB_INPUT_SPEC.md`
2. `SYSTEM_ASSET_MANAGEMENT_SPEC.md`
3. `MODULE_SCRIPT_WRITER_SPEC.md`
4. `MODULE_TTS_SPEC.md`
5. `MODULE_TIMELINE_BUILDER_SPEC.md`
6. `MODULE_LIPSYNC_SPEC.md`
7. `MODULE_BACKGROUND_SELECTOR_SPEC.md`
8. `MODULE_SUBTITLES_SPEC.md`
9. `MODULE_COMPOSITOR_SPEC.md`
10. `SYSTEM_PIPELINE_ORCHESTRATION_SPEC.md`
11. `SYSTEM_OBSERVABILITY_SPEC.md`
12. `SYSTEM_BATCH_PROCESSING_SPEC.md`
