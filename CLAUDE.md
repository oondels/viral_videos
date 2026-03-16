# CLAUDE.md

This repository is intended to be worked through a Ralph Loop style workflow.

## Primary source of truth

- Read `docs/DESIGN_SPEC.md` first in every iteration.
- `docs/DESIGN_SPEC.md` is the root source of truth for product scope, architecture invariants, canonical paths, and the spec lookup index.
- Detailed behavior lives in `docs/specs/*.md`.
- Open only the spec files referenced by the current task or by the lookup index in `docs/DESIGN_SPEC.md`.
- If `TASKS.md`, `docs/DESIGN_SPEC.md`, and a file in `docs/specs/` disagree, stop and fix the documentation before writing code.
- If a change affects business rules, feature scope, contracts, or architecture, update `docs/DESIGN_SPEC.md`.
- If a change affects setup, execution flow, commands, or operator-facing usage, update `README.md`.

## Task loop contract

- `TASKS.md` is the operational memory for loop agents.
- `PROGRESS.md` is the persistent knowledge log of completed tasks and must be read before starting the next task.
- Pick the first task with `status: false` whose dependencies are satisfied.
- Complete exactly one task per iteration.
- Run the task validation checks before changing its status.
- Set a task to complete only after its acceptance criteria and validations pass.
- After completing a task, append the result of that task to `PROGRESS.md`.
- After completing a task, create one commit containing the work done for that task.
- Prefer one task per commit. Do not batch unrelated task work into the same commit.
- Stop after each completed task so the next iteration starts with fresh context.
- You have permisson to edit any file in the repository, but do not change `docs/DESIGN_SPEC.md` or `TASKS.md` without a clear reason related to the current task.
- You do not have permission to change any file outside of the current project. 

## Project status

- The repository is still in the documentation and planning phase.
- There is no production implementation yet.
- The next implementation work should follow `TASKS.md` in order.

## Canonical project summary

The project takes one topic as input and produces one vertical MP4 video through this pipeline:

`Input -> Orchestrator -> Script Writer -> TTS -> Timeline Builder -> Lip-Sync -> Background Selector -> Subtitle Generator -> FFmpeg Compositor -> Final MP4`

Core invariants:

- single Docker container in the MVP;
- file-based pipeline state;
- adapters around every external provider;
- one job workspace per `job_id` under `output/jobs/<job_id>/`;
- intermediate artifacts are preserved for debugging.

## Commands

The intended MVP commands are:

```bash
docker build -t viral-videos .
docker compose run --rm app python -m app.main --input inputs/examples/job_001.json
docker compose run --rm app python -m app.main --batch inputs/batch/jobs.csv
docker compose run --rm app pytest
docker compose run --rm app ruff check app/
```

Credentials must stay in `.env`, based on `.env.example`, and must never be embedded in the image.

## How to read the docs

- Start with `docs/DESIGN_SPEC.md`.
- Read `PROGRESS.md` after `docs/DESIGN_SPEC.md` to recover what was learned in previous iterations.
- Use its lookup table to find the exact file in `docs/specs/` for the capability you are working on.
- Treat the remaining files in `docs/PROJECT_*.md` as background context, not as the primary source of truth.
