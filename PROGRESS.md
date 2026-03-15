# PROGRESS.md

## Purpose

This file is the persistent execution memory for completed tasks.

Every loop iteration must:

1. read this file before starting implementation;
2. use it to recover decisions, discoveries, blockers, and validations from earlier tasks;
3. append one new entry after completing exactly one task.

## Update rules

- Add one entry per completed task.
- Do not rewrite old entries unless they are factually wrong.
- Record only durable knowledge that helps the next iteration.
- Include the task id, outcome, files changed, validations run, and any follow-up note.

## Entry template

```md
## YYYY-MM-DD - T-XXX - Short title

- Outcome: what was completed.
- Files changed: path1, path2, path3.
- Validations: commands run or checks performed.
- Docs updated: DESIGN_SPEC.md, README.md, or none.
- Notes for next task: only the information the next iteration needs plus any additional context.
```

## Entries

No completed tasks recorded yet.
