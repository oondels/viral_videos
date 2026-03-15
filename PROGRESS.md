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

## 2026-03-15 - T-001 - Scaffold the minimum repository work tree

- Outcome: estrutura canônica de pastas e pacotes Python criada com sucesso.
- Files changed: app/utils/__init__.py (criado), scripts/.gitkeep (criado), assets/backgrounds/slime/.gitkeep, assets/backgrounds/sand/.gitkeep, assets/backgrounds/minecraft_parkour/.gitkeep, assets/backgrounds/marble_run/.gitkeep, assets/backgrounds/misc/.gitkeep (criados), assets/backgrounds/.gitkeep (removido), TASKS.md (T-001 status → true).
- Validations: inspecionada a árvore completa de diretórios — todos os caminhos canônicos do DESIGN_SPEC e SYSTEM_ASSET_MANAGEMENT_SPEC estão presentes; nenhum arquivo gerado em runtime foi criado dentro de assets/.
- Docs updated: none.
- Notes for next task: T-002 (Docker environment) já tem Dockerfile, docker-compose.yml, .env.example, .dockerignore e requirements.txt no repositório. A validation check da T-002 exige buildar o container e confirmar que FFmpeg está disponível — isso ainda não foi validado.
