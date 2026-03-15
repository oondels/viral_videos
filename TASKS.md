---
spec_type: TASKS
feature_slug: viral-videos-mvp
status: ready
version: 2.0
loop_mode: ralph
last_updated: 2026-03-15T00:00:00Z
inputs:
* docs/DESIGN_SPEC.md
* docs/specs/README.md
* PROGRESS.md
---

# TASK PLAN - viral-videos-mvp

## LOOP_RULES

* On each iteration, select the first task with `status: false` whose `depends_on` tasks are all `true`.
* Read `docs/DESIGN_SPEC.md` first on every iteration.
* Read `PROGRESS.md` after `docs/DESIGN_SPEC.md` to recover the knowledge produced by previous completed tasks.
* Then read only the files listed under `read_first` for the selected task.
* Complete exactly one task per iteration.
* Run every listed validation check before marking a task complete.
* If any stop condition triggers, stop and update the docs instead of guessing.
* If the task changes business rules, feature scope, contracts, or architecture, update `docs/DESIGN_SPEC.md`.
* If the task changes setup, commands, or operator-facing usage, update `README.md`.
* After a task passes validation, append its outcome to `PROGRESS.md`.
* After a task passes validation, set its `status` to `true`, create one commit for that task, persist the changes, and stop the iteration.

## REVIEW_GATE

* `docs/DESIGN_SPEC.md` and the referenced spec files are internally consistent.
* `PROGRESS.md` reflects the durable knowledge from all completed tasks.
* Task dependencies are acyclic.
* Each task has one clear goal and one bounded scope.
* The next executable task can be selected deterministically.

## TASKS

* id: T-001
  title: Scaffold the minimum repository work tree
  status: true
  type: code
  depends_on: []
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_ASSET_MANAGEMENT_SPEC.md
  goal: Create the minimum folder and package structure required by the MVP.
  scope: app/, app/core/, app/modules/, app/adapters/, app/services/, app/utils/, app/prompts/, assets/, config/, inputs/, output/, temp/, tests/, scripts/
  instructions: Create only the canonical folder structure and placeholder package markers. Do not implement business logic in this task.
  acceptance_criteria:
  * The repository contains the canonical top-level folders defined in DESIGN_SPEC.
  * Python package directories under `app/` exist with `__init__.py` files where needed.
  * No runtime-generated files are created inside `assets/`.
  validation_checks:
  * Inspect the resulting tree and confirm the required directories exist.
  * Confirm the structure matches the asset and output separation rules.
  stop_conditions:
  * STOP if the directory rules in DESIGN_SPEC and SYSTEM_ASSET_MANAGEMENT_SPEC conflict.
  rollback_notes:
  * Remove placeholder directories or files that do not belong to the canonical structure.

* id: T-002
  title: Prepare the single-container Python and Docker environment
  status: true
  type: infra
  depends_on: [T-001]
  read_first:
  * docs/DESIGN_SPEC.md
  goal: Make the repository runnable inside one Docker container with the base multimedia dependencies.
  scope: Dockerfile, docker-compose.yml, .dockerignore, .env.example, pyproject.toml or requirements.txt, .gitignore
  instructions: Add only the minimum environment needed to run the future CLI and FFmpeg-based pipeline. Keep secrets out of the image.
  acceptance_criteria:
  * The repository has a single-container Docker setup.
  * FFmpeg and FFprobe are available inside the container.
  * Dependency installation is explicit and versioned.
  validation_checks:
  * Build the container successfully.
  * Run a simple Python command in the container and confirm FFmpeg is available.
  stop_conditions:
  * STOP if DESIGN_SPEC leaves the runtime base image or single-container decision ambiguous.
  rollback_notes:
  * Revert container setup files if they introduce multi-container or secret-handling behavior outside the MVP.

* id: T-003
  title: Add the minimal CLI, config loader, and logger foundation
  status: true
  type: code
  depends_on: [T-002]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_JOB_INPUT_SPEC.md
  * docs/specs/SYSTEM_OBSERVABILITY_SPEC.md
  * docs/specs/SYSTEM_PIPELINE_ORCHESTRATION_SPEC.md
  goal: Create the basic application entry point and shared runtime services.
  scope: app/main.py, app/config.py, app/logger.py
  instructions: Implement CLI argument parsing, configuration loading, and a logger scaffold without executing the full pipeline yet.
  acceptance_criteria:
  * `python -m app.main --help` works.
  * Config loading has one canonical entry point.
  * Logging can write a per-job file once a validated `job_id` exists and the workspace is initialized.
  validation_checks:
  * Run the CLI help command successfully.
  * Confirm logger creation follows the JSON Lines contract from the observability spec.
  stop_conditions:
  * STOP if the CLI entry contract and orchestration stage naming conflict.
  rollback_notes:
  * Revert CLI flags or logger setup if they create behavior outside single-job or batch entry points.

* id: T-004
  title: Implement the validated single-job input contract
  status: false
  type: code
  depends_on: [T-003]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_JOB_INPUT_SPEC.md
  goal: Create the canonical job schema and validation layer.
  scope: app/core/contracts.py, app/core/types.py, tests/unit/
  instructions: Implement the validated job object with defaults, field validation, and explicit rejection of unknown fields.
  acceptance_criteria:
  * A validated job contract exists for topic, duration, background style, characters, and preset.
  * Invalid inputs fail before any downstream stage runs.
  * The system generates `job_id` instead of accepting it from the input file.
  validation_checks:
  * Run focused unit tests for valid and invalid job payloads.
  * Confirm the validated object materializes defaults explicitly.
  stop_conditions:
  * STOP if the input schema in DESIGN_SPEC and SYSTEM_JOB_INPUT_SPEC disagree.
  rollback_notes:
  * Remove the new schema and tests if validation behavior cannot be aligned safely with the spec.

* id: T-005
  title: Add job context and canonical workspace path services
  status: false
  type: code
  depends_on: [T-004]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_JOB_INPUT_SPEC.md
  goal: Centralize `job_id`, workspace creation, and canonical artifact paths.
  scope: app/core/job_context.py, app/services/file_service.py, app/utils/path_utils.py
  instructions: Implement one shared path authority for every job artifact directory and file location.
  acceptance_criteria:
  * A job creates the expected directory tree under `output/jobs/<job_id>/`.
  * Downstream modules can resolve paths without hardcoded string assembly.
  * The canonical path layout matches DESIGN_SPEC.
  validation_checks:
  * Create a sample job context and confirm every expected directory is created.
  * Confirm all returned paths stay outside `assets/`.
  stop_conditions:
  * STOP if two different artifact layouts appear in the docs.
  rollback_notes:
  * Revert path helpers that create non-canonical directories or mixed asset/output locations.

* id: T-006
  title: Create canonical sample inputs and test fixtures
  status: false
  type: docs
  depends_on: [T-004]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_JOB_INPUT_SPEC.md
  goal: Add repeatable input examples for manual runs and tests.
  scope: inputs/examples/job_001.json, inputs/examples/job_002.json, tests/fixtures/sample_inputs/
  instructions: Create only valid, minimal example jobs that match the canonical input contract.
  acceptance_criteria:
  * At least one valid single-job example exists.
  * Fixture payloads match the validated job contract exactly.
  * Sample inputs do not introduce fields outside the spec.
  validation_checks:
  * Validate the example jobs through the job schema.
  * Confirm the files can be reused by later CLI and integration tests.
  stop_conditions:
  * STOP if the example payload needs a field not defined by the input spec.
  rollback_notes:
  * Remove fixture fields that are not part of the approved input contract.

* id: T-007
  title: Add script-generation prompts and provider interface
  status: false
  type: code
  depends_on: [T-004]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_SCRIPT_WRITER_SPEC.md
  goal: Create the prompt files and the adapter boundary for script generation.
  scope: app/prompts/script_system_prompt.md, app/prompts/script_user_prompt_template.md, app/adapters/llm_adapter.py
  instructions: Define the provider interface and prompt assets without locking the pipeline to one LLM vendor.
  acceptance_criteria:
  * A `ScriptGenerator` interface or equivalent exists.
  * Prompt files are separated from executable code.
  * The interface returns data that can be validated against the script spec.
  validation_checks:
  * Confirm prompt files load from disk through one canonical path.
  * Run focused tests for the adapter interface shape if added.
  stop_conditions:
  * STOP if prompt rules and output contract expectations conflict.
  rollback_notes:
  * Revert provider-specific assumptions that leak into the module boundary.

* id: T-008
  title: Implement the script writer module
  status: false
  type: code
  depends_on: [T-005, T-007]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_SCRIPT_WRITER_SPEC.md
  goal: Generate `script.json` and `dialogue.json` from a validated job.
  scope: app/modules/script_writer.py, tests/unit/, tests/integration/
  instructions: Generate a structured title hook and alternating two-character dialogue, then persist both artifacts to the canonical script directory.
  acceptance_criteria:
  * `script.json` and `dialogue.json` are both written to disk.
  * Dialogue alternates speakers strictly and uses only the requested characters.
  * Generated output passes all structural validation rules in the spec.
  validation_checks:
  * Run focused tests for dialogue structure and file persistence.
  * Confirm invalid provider output is rejected clearly.
  stop_conditions:
  * STOP if the provider cannot return output that matches the required contract.
  rollback_notes:
  * Revert script persistence logic if it writes malformed or non-canonical artifacts.

* id: T-009
  title: Add the TTS provider boundary and voice mapping config
  status: false
  type: code
  depends_on: [T-004]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_TTS_SPEC.md
  goal: Define the voice configuration and provider adapter for per-line speech generation.
  scope: app/adapters/tts_provider_adapter.py, config/voices.json, config/voices.example.json
  instructions: Add the provider interface and a canonical mapping from character id to voice id, with `config/voices.json` as the runtime source of truth.
  acceptance_criteria:
  * A `TTSProvider` interface or equivalent exists.
  * Voice mapping is configuration-driven, not hardcoded in module logic.
  * Missing voice mappings can be detected before audio generation begins.
  validation_checks:
  * Run focused validation for loading the voice mapping config.
  * Confirm the adapter contract exposes one call per dialogue line.
  stop_conditions:
  * STOP if voice mapping requirements are missing or ambiguous for the two-character MVP.
  rollback_notes:
  * Remove provider-specific fields that are not required by the canonical TTS contract.

* id: T-010
  title: Implement per-line audio generation and manifest persistence
  status: false
  type: code
  depends_on: [T-008, T-009]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_TTS_SPEC.md
  goal: Convert each dialogue line into a normalized WAV file and manifest entry.
  scope: app/modules/tts.py, app/utils/audio_utils.py, app/utils/ffprobe_utils.py, tests/unit/, tests/integration/
  instructions: Generate one audio segment per dialogue item, normalize persisted files, and write `manifest.json` with measured durations.
  acceptance_criteria:
  * Every dialogue line produces one segment file in `audio/segments/`.
  * `manifest.json` exists and matches dialogue order exactly.
  * Durations are measured from persisted files, not estimated.
  validation_checks:
  * Run focused tests for segment generation and manifest shape.
  * Confirm every manifest path points to an existing file.
  stop_conditions:
  * STOP if the persisted audio format cannot satisfy the normalization rules in the spec.
  rollback_notes:
  * Revert partial segment generation if manifest order or naming becomes non-canonical.

* id: T-011
  title: Build the master audio file and canonical timeline
  status: false
  type: code
  depends_on: [T-010]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_TIMELINE_BUILDER_SPEC.md
  goal: Concatenate audio segments into one master file and compute the canonical timeline.
  scope: app/modules/timeline_builder.py, tests/unit/, tests/integration/
  instructions: Build `master_audio.wav`, compute `start_sec`, `end_sec`, and `duration_sec` for each line, and initialize `clip_file` as `null`.
  acceptance_criteria:
  * `master_audio.wav` exists in the canonical master audio directory.
  * `timeline.json` exists and matches manifest order exactly.
  * The final timeline end time matches the measured master audio duration within the spec tolerance.
  validation_checks:
  * Run focused tests for gap-free timeline generation.
  * Confirm the last timeline item aligns with the master audio duration.
  stop_conditions:
  * STOP if the manifest is malformed or audio durations cannot be measured reliably.
  rollback_notes:
  * Revert timeline output if there are gaps, overlaps, or non-canonical field names.

* id: T-012
  title: Generate subtitles directly from the timeline
  status: false
  type: code
  depends_on: [T-011]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_SUBTITLES_SPEC.md
  goal: Generate `subtitles.srt` using the timeline text and timing as the only source of truth.
  scope: app/modules/subtitles.py, tests/unit/
  instructions: Write one SRT cue per timeline item without rewriting, paraphrasing, or resegmenting the text.
  acceptance_criteria:
  * `subtitles.srt` exists in the canonical subtitles directory.
  * Cue order, start times, end times, and text match the timeline exactly.
  * The file is valid SRT.
  validation_checks:
  * Run focused tests for SRT numbering and timing.
  * Confirm the generated file can be parsed as valid SRT.
  stop_conditions:
  * STOP if the timeline contract is missing or malformed.
  rollback_notes:
  * Revert subtitle generation if it changes dialogue text or timing semantics.

* id: T-013
  title: Prepare canonical character assets, fonts, and render presets
  status: false
  type: docs
  depends_on: [T-001]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_ASSET_MANAGEMENT_SPEC.md
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  goal: Add the minimum fixed assets and config files required by the MVP.
  scope: assets/characters/, assets/backgrounds/, assets/fonts/, assets/presets/, config/render.example.json, app/services/asset_service.py
  instructions: Create the canonical asset folders and the minimum metadata structures needed for character lookup, preset lookup, and font resolution.
  acceptance_criteria:
  * Character folders exist with `base.png` and `metadata.json`.
  * At least one subtitle-safe font exists in `assets/fonts/`.
  * At least one render preset exists with all required preset fields.
  validation_checks:
  * Run focused asset validation checks.
  * Confirm missing assets fail clearly through the asset service.
  stop_conditions:
  * STOP if the preset field list and compositor contract disagree.
  rollback_notes:
  * Remove asset files that do not conform to the canonical folder contracts.

* id: T-014
  title: Add the lip-sync engine boundary
  status: false
  type: code
  depends_on: [T-010, T-013]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_LIPSYNC_SPEC.md
  goal: Define the adapter contract for generating one talking-head clip from one image and one audio file.
  scope: app/adapters/lipsync_engine_adapter.py, app/modules/lipsync.py
  instructions: Add the engine interface and keep provider-specific behavior out of the pipeline orchestration layer.
  acceptance_criteria:
  * A `LipSyncEngine` interface or equivalent exists.
  * The interface accepts a character asset and one audio segment as input.
  * The interface returns one generated clip path as output.
  validation_checks:
  * Run focused tests for interface shape or adapter stubs if added.
  * Confirm the boundary does not mutate unrelated timeline fields.
  stop_conditions:
  * STOP if the selected engine cannot satisfy the clip contract defined by the spec.
  rollback_notes:
  * Revert provider-specific logic that leaks beyond the adapter boundary.

* id: T-015
  title: Generate one talking-head clip per timeline item
  status: false
  type: code
  depends_on: [T-011, T-014]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_LIPSYNC_SPEC.md
  goal: Produce per-line talking-head clips and update the canonical timeline with `clip_file`.
  scope: app/modules/lipsync.py, tests/unit/, tests/integration/
  instructions: Generate one clip per timeline item, store it in the canonical clips directory, and update only the `clip_file` field in the timeline.
  acceptance_criteria:
  * A clip file exists for every timeline item.
  * Timeline entries are updated in place with the correct clip path.
  * Clip duration stays within the allowed tolerance versus its source audio.
  validation_checks:
  * Run focused tests for clip naming, timeline update behavior, and duration tolerance.
  * Confirm no other timeline fields are changed.
  stop_conditions:
  * STOP if character assets are missing or a generated clip violates the duration tolerance.
  rollback_notes:
  * Revert clip generation and timeline mutations if the module changes non-clip timeline data.

* id: T-016
  title: Select, loop, trim, and normalize the background video
  status: false
  type: code
  depends_on: [T-013]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_BACKGROUND_SELECTOR_SPEC.md
  goal: Produce one prepared background video with the required duration and vertical layout.
  scope: app/modules/background_selector.py, tests/unit/, tests/integration/
  instructions: Select exactly one background asset, then loop or trim it to match the required duration and export it as `prepared_background.mp4`.
  acceptance_criteria:
  * One prepared background file exists in the canonical background directory.
  * The prepared background is `1080x1920`.
  * The prepared background duration is at least the full timeline duration.
  validation_checks:
  * Run focused tests for category selection, deterministic auto-selection, and duration adaptation.
  * Confirm the export path matches the canonical artifact contract.
  stop_conditions:
  * STOP if no readable background asset exists for the requested category.
  rollback_notes:
  * Revert any background selection logic that breaks deterministic selection or output format rules.

* id: T-017
  title: Centralize FFmpeg and FFprobe operations
  status: false
  type: code
  depends_on: [T-002]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_BACKGROUND_SELECTOR_SPEC.md
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  goal: Create one reusable adapter layer for multimedia shell commands.
  scope: app/adapters/ffmpeg_adapter.py, app/utils/video_utils.py, app/utils/ffprobe_utils.py
  instructions: Move FFmpeg and FFprobe invocation behind reusable helpers so modules do not assemble shell commands ad hoc.
  acceptance_criteria:
  * FFmpeg calls flow through one adapter layer.
  * FFprobe lookups are reusable by audio, background, and compositor stages.
  * Modules can request media operations without duplicating shell command assembly.
  validation_checks:
  * Run focused tests or smoke checks for the adapter helpers.
  * Confirm touched modules no longer build raw FFmpeg commands inline where avoidable.
  stop_conditions:
  * STOP if adapter abstractions hide required control from module-level specs.
  rollback_notes:
  * Revert abstractions that make FFmpeg behavior less explicit or less testable.

* id: T-018
  title: Implement the final compositor and render metadata output
  status: false
  type: code
  depends_on: [T-012, T-015, T-016, T-017]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  goal: Compose the prepared background, per-line clips, title hook, subtitles, and master audio into the final MP4.
  scope: app/modules/compositor.py, app/services/render_service.py, tests/integration/
  instructions: Use the selected render preset as the geometry source of truth and produce both `final.mp4` and `render_metadata.json`.
  acceptance_criteria:
  * `render/final.mp4` exists.
  * `render/render_metadata.json` exists and matches the required metadata contract.
  * The final video uses `master_audio.wav` as the authoritative audio track.
  validation_checks:
  * Run focused integration checks for final output existence, duration tolerance, and output resolution.
  * Confirm subtitles are burned into the final render.
  stop_conditions:
  * STOP if any required clip, preset, background, subtitle, or master audio artifact is missing.
  rollback_notes:
  * Revert compositor changes that hardcode layout geometry outside preset files or violate the render contract.

* id: T-019
  title: Chain the full single-job pipeline end to end
  status: false
  type: code
  depends_on: [T-018]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_PIPELINE_ORCHESTRATION_SPEC.md
  goal: Execute the entire pipeline for one job through one command.
  scope: app/pipeline.py, app/main.py, tests/integration/
  instructions: Implement the canonical stage order and fail-fast behavior for a single validated job.
  acceptance_criteria:
  * One CLI command runs the full single-job pipeline.
  * Stages execute in the canonical order from the orchestration spec.
  * A stage failure stops downstream execution but preserves upstream artifacts.
  validation_checks:
  * Run an end-to-end test or smoke run using `inputs/examples/job_001.json`.
  * Confirm a forced downstream failure preserves completed upstream artifacts.
  stop_conditions:
  * STOP if stage order or artifact ownership is ambiguous.
  rollback_notes:
  * Revert orchestration behavior that silently reruns or overwrites upstream artifacts after failure.

* id: T-020
  title: Implement canonical stage logging and execution metadata
  status: false
  type: code
  depends_on: [T-019]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_OBSERVABILITY_SPEC.md
  goal: Persist job logs and stage events in a machine-readable format.
  scope: app/logger.py, app/pipeline.py, tests/integration/
  instructions: Emit canonical `stage_started`, `stage_completed`, and `stage_failed` events to `logs/job.log` as JSON Lines after workspace initialization; validation failures before job creation may stay in the process logger.
  acceptance_criteria:
  * Every canonical stage from `init_job_workspace` onward produces the expected log events.
  * Failed stages after workspace initialization emit exactly one `stage_failed` event.
  * Render metadata exists only for successful renders.
  validation_checks:
  * Run focused checks that parse `logs/job.log` as JSON Lines.
  * Confirm log stage names match the canonical allowed list.
  stop_conditions:
  * STOP if observability stage names conflict with orchestration stage names.
  rollback_notes:
  * Revert logging changes that create non-JSON log lines or duplicate failure events.

* id: T-021
  title: Add sequential batch processing and final batch report
  status: false
  type: code
  depends_on: [T-019]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_BATCH_PROCESSING_SPEC.md
  goal: Process multiple jobs sequentially and record one batch summary report.
  scope: app/main.py, scripts/run_batch.sh, inputs/batch/jobs.csv, tests/integration/
  instructions: Reuse the single-job pipeline contract for each batch item and continue after per-item failures.
  acceptance_criteria:
  * Batch mode processes items sequentially.
  * Each batch item gets its own `job_id` and isolated workspace.
  * `output/batch_reports/latest_report.json` is written with the required summary fields.
  validation_checks:
  * Run a mixed batch with both valid and invalid items.
  * Confirm the final report records successes and failures correctly.
  stop_conditions:
  * STOP if batch input parsing introduces a second, conflicting job schema.
  rollback_notes:
  * Revert batch behavior that aborts the entire batch on the first failing item.

* id: T-022
  title: Harden the MVP with validation, retries, and minimum tests
  status: false
  type: code
  depends_on: [T-020]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/SYSTEM_JOB_INPUT_SPEC.md
  * docs/specs/SYSTEM_ASSET_MANAGEMENT_SPEC.md
  * docs/specs/SYSTEM_PIPELINE_ORCHESTRATION_SPEC.md
  * docs/specs/SYSTEM_OBSERVABILITY_SPEC.md
  goal: Convert the prototype into a minimally robust operational tool.
  scope: app/core/exceptions.py, tests/unit/, tests/integration/, touched modules
  instructions: Add only the minimum hardening required by the MVP: clearer errors, asset validation, controlled retries for external providers, timeouts, and focused tests for the most failure-prone modules.
  acceptance_criteria:
  * Main validation failures are explicit and readable.
  * Provider-facing stages can retry within a controlled policy.
  * The minimum focused test suite exists for critical contracts and end-to-end flow.
  validation_checks:
  * Run focused unit and integration tests for the hardened paths.
  * Confirm failure scenarios stop in the correct stage with readable errors and preserved artifacts.
  stop_conditions:
  * STOP if a hardening change alters the product contract instead of enforcing it.
  rollback_notes:
  * Revert resilience logic that hides failures, changes artifact contracts, or weakens determinism.

* id: T-023
  title: Add minimum operational documentation for humans and agents
  status: false
  type: docs
  depends_on: [T-019]
  read_first:
  * docs/DESIGN_SPEC.md
  * docs/specs/README.md
  goal: Make the repository runnable and understandable without extra tribal knowledge.
  scope: README.md, scripts/run_single.sh, scripts/cleanup_temp.sh, Makefile
  instructions: Document only the minimum setup, run, batch, test, lint, and cleanup flows needed for the MVP.
  acceptance_criteria:
  * The README describes the MVP flow and canonical commands.
  * Operational helper scripts exist for single-run, batch, and cleanup flows when needed.
  * The documented commands match the actual repository behavior.
  validation_checks:
  * Follow the documented commands and confirm they work as written.
  * Confirm the README points readers to `docs/DESIGN_SPEC.md` and `docs/specs/`.
  stop_conditions:
  * STOP if the documented behavior diverges from the implemented commands.
  rollback_notes:
  * Revert documentation that describes unsupported workflows or non-canonical artifact paths.

## GLOBAL_CHECKS

* Confirm all touched tests pass before marking any task complete.
* Confirm task dependencies remain acyclic after every edit to this file.
* Confirm no task introduces scope outside `docs/DESIGN_SPEC.md` and the referenced files in `docs/specs/`.
* Confirm `PROGRESS.md` was updated with the result of the completed task.
* Confirm the completed task was recorded in its own commit.
* Confirm the next loop iteration can choose the next task without reading unrelated files.
