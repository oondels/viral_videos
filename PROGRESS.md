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

## 2026-03-15 - T-002 - Prepare the single-container Python and Docker environment

- Outcome: ambiente Docker validado; build bem-sucedido e FFmpeg 7.1.3 + FFprobe confirmados dentro do container.
- Files changed: docker-compose.yml (adicionado volume ./config:/app/config ausente que README já documentava).
- Validations: `docker build -t viral-videos .` → sucesso; `docker run --rm viral-videos python -c "..."` → FFmpeg 7.1.3 e FFprobe 7.1.3 disponíveis.
- Docs updated: none (README.md e DESIGN_SPEC.md já estavam corretos).
- Notes for next task: T-003 requer app/main.py, app/config.py, app/logger.py. config/ está montado no container. Confirmar que `python -m app.main --help` funciona e que o logger segue o contrato JSON Lines da observability spec.

## 2026-03-15 - T-003 - Add the minimal CLI, config loader, and logger foundation

- Outcome: app/config.py criado com carregamento canônico de .env; app/logger.py criado com get_process_logger() e JobLogger (JSON Lines); app/main.py atualizado para usar app.logger em vez de app.services.logging_config.
- Files changed: app/config.py (criado), app/logger.py (criado), app/main.py (import atualizado).
- Validations: `python -m app.main --help` → saída correta; JobLogger validado: cada linha é JSON válido com campos obrigatórios (timestamp_utc, job_id, stage, event, message) e campos opcionais corretos.
- Docs updated: none.
- Notes for next task: T-004 requer app/core/contracts.py e app/core/types.py. Ler SYSTEM_JOB_INPUT_SPEC.md. job_id format é job_YYYY_MM_DD_NNN. Unknown fields devem ser rejeitados.
