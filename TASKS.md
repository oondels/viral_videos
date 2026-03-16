---
spec_type: TASKS
status: ready
loop_mode: ralph
last_updated: 2026-03-16T00:00:00Z
inputs:
* docs/DESIGN_SPEC.md
* IMPLEMENTATION_PLAN.md
* docs/specs/README.md
* PROGRESS.md
---

# TASK PLAN

> Tasks here correspond to the current `IMPLEMENTATION_PLAN.md`.
> When a new plan begins, this file is replaced entirely.
> Completed task results are preserved in `PROGRESS.md`.

## LOOP_RULES

* On each iteration, select the first task with `status: false` whose `depends_on` tasks are all `true`.
* Read `docs/DESIGN_SPEC.md` first on every iteration.
* Read `IMPLEMENTATION_PLAN.md` to understand the purpose and scope of the current work.
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
