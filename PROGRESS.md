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

## 2026-03-15 - T-004 - Implement the validated single-job input contract

- Outcome: contrato de validação canônico implementado com Pydantic v2; 20 unit tests passando.
- Files changed: app/core/types.py (criado), app/core/contracts.py (criado), tests/unit/test_contracts.py (criado).
- Validations: `docker run --rm -v $(pwd):/app -w /app viral-videos pytest tests/unit/test_contracts.py -v` → 20 passed; defaults materializados corretamente; job_id gerado no formato job_YYYY_MM_DD_NNN.
- Docs updated: none.
- Notes for next task: T-005 e T-006 são ambos desbloqueados (depends_on T-004). T-005 centraliza job_id e workspace paths (app/core/job_context.py, app/services/file_service.py, app/utils/path_utils.py). T-006 adiciona fixtures de input. _ALLOWED_BACKGROUND_STYLES e _ALLOWED_OUTPUT_PRESETS em contracts.py são o local canônico para valores válidos de background/preset — T-013 pode expandir essa lista.

## 2026-03-15 - T-005 - Add job context and canonical workspace path services

- Outcome: autoridade canônica de paths implementada; workspace criado sob output/jobs/<job_id>/; 22 unit tests passando.
- Files changed: app/utils/path_utils.py (criado), app/core/job_context.py (criado), app/services/file_service.py (criado), tests/unit/test_job_context.py (criado), TASKS.md (T-005 status → true).
- Validations: `pytest tests/unit/test_job_context.py -v` → 22 passed; todos os subdirs canônicos criados; nenhum path fora de output/jobs/<job_id>; sem criação de assets/.
- Docs updated: none.
- Notes for next task: T-006 (fixtures) e T-007 (LLM adapter) são desbloqueados. T-006 depende do contrato de validação de T-004 — usar validate_job() para confirmar que os exemplos são válidos. T-007 cria o adapter LLM e prompts. T-008 depende de T-005 e T-007. JobContext é o objeto canônico de paths — todos os módulos devem recebê-lo por injeção.

## 2026-03-15 - T-006 - Create canonical sample inputs and test fixtures

- Outcome: exemplos canônicos de input e fixtures de teste criados; todos validados pelo schema.
- Files changed: inputs/examples/job_001.json (output_preset adicionado), inputs/examples/job_002.json (criado, minimal), tests/fixtures/sample_inputs/valid_minimal.json (criado), tests/fixtures/sample_inputs/valid_full.json (criado), TASKS.md (T-006 status → true).
- Validations: `validate_job()` executada em todos os 4 arquivos → todos passam com defaults corretos materializados.
- Docs updated: none.
- Notes for next task: T-007 (LLM adapter) e T-009 (TTS adapter) são os próximos desbloqueados. T-007 cria app/prompts/ + app/adapters/llm_adapter.py com interface ScriptGenerator. T-008 depende de T-005 ✓ e T-007. T-009 cria app/adapters/tts_provider_adapter.py + config/voices.json. tests/fixtures/sample_inputs/ pode ser reusado por testes de integração futuros.

## 2026-03-15 - T-007 - Add script-generation prompts and provider interface

- Outcome: interface ScriptGenerator (ABC), carregador de prompts e arquivos de prompt criados; 12 unit tests passando.
- Files changed: app/prompts/script_system_prompt.md (criado), app/prompts/script_user_prompt_template.md (criado), app/adapters/llm_adapter.py (criado), tests/unit/test_llm_adapter.py (criado), TASKS.md (T-007 status → true).
- Validations: `pytest tests/unit/test_llm_adapter.py -v` → 12 passed; prompts carregam do disco; interface abstrata não instanciável; subclasse concreta funciona.
- Docs updated: none.
- Notes for next task: T-008 depende de T-005 ✓ e T-007 ✓ — pode começar agora. T-009 (TTS adapter) também está desbloqueado (depends_on T-004 ✓). Interface ScriptGenerator: generate(system_prompt, user_prompt, job) → dict com title_hook + dialogue. ScriptGenerationError para falhas de provider. load_system_prompt() e load_user_prompt(job) são os loaders canônicos de prompts.

## 2026-03-15 - T-008 - Implement the script writer module

- Outcome: módulo write_script() implementado com validação completa e persistência canônica; 15 unit tests passando.
- Files changed: app/modules/script_writer.py (criado), tests/unit/test_script_writer.py (criado), TASKS.md (T-008 status → true).
- Validations: `pytest tests/unit/test_script_writer.py -v` → 15 passed; script.json e dialogue.json escritos corretamente; alternação de speakers, line count, index, empty text, unknown speaker e title_hook rejeitados corretamente.
- Docs updated: none.
- Notes for next task: T-009 (TTS adapter) depende de T-004 ✓ — pode começar agora. T-010 depende de T-008 ✓ e T-009. Contrato de write_script: JobContext → persiste script_json() e dialogue_json() com JSON canônico. ScriptGenerationError é a exceção para falhas de validação do provider.

## 2026-03-15 - T-009 - Add the TTS provider boundary and voice mapping config

- Outcome: interface TTSProvider (ABC), loaders de voice mapping e config/voices.json criados; 13 unit tests passando.
- Files changed: app/adapters/tts_provider_adapter.py (criado), config/voices.example.json (criado), config/voices.json (criado), tests/unit/test_tts_adapter.py (criado), TASKS.md (T-009 status → true).
- Validations: `pytest tests/unit/test_tts_adapter.py -v` → 13 passed; load_voice_mapping() e resolve_voice_id() funcionam; TTSProvider não instanciável diretamente; subclasse concreta funciona.
- Docs updated: none.
- Notes for next task: T-010 depende de T-008 ✓ e T-009 ✓ — pode começar agora. TTSProvider.synthesize(text, voice_id, output_path) é o contrato canônico. load_voice_mapping() carrega config/voices.json (runtime path relativo ao CWD). resolve_voice_id(character, mapping) levanta TTSError para speakers sem mapeamento. config/voices.json está commitado com voice_ids de placeholder para char_a e char_b.

## 2026-03-15 - T-010 - Implement per-line audio generation and manifest persistence

- Outcome: módulo generate_tts() implementado; 13 unit tests passando; 95 testes totais verdes.
- Files changed: app/modules/tts.py (criado), app/utils/ffprobe_utils.py (criado), app/utils/audio_utils.py (criado), tests/unit/test_tts_module.py (criado), TASKS.md (T-010 status → true).
- Validations: `pytest tests/unit/ -v` → 95 passed; segmentos gerados em audio/segments/NNN_speaker.wav; manifest.json com campos obrigatórios; duration_sec medida via ffprobe; voice mapping ausente falha antes de qualquer síntese; arquivo não escrito levanta TTSError.
- Docs updated: none.
- Notes for next task: T-011 depende de T-010 ✓ — pode começar. generate_tts(ctx, provider, voice_mapping) → lista de dicts do manifesto. audio_utils.write_silence_wav() pode ser reutilizado em testes futuros. ffprobe_utils.get_audio_duration() é o utilitário canônico para medir duração de áudio.

## 2026-03-15 - T-011 - Build the master audio file and canonical timeline

- Outcome: build_timeline() implementado; master_audio.wav concatenado via FFmpeg concat demuxer; timeline.json com start_sec/end_sec/duration_sec calculados sem gaps; 14 unit tests passando; 109 testes totais verdes.
- Files changed: app/modules/timeline_builder.py (criado), tests/unit/test_timeline_builder.py (criado), TASKS.md (T-011 status → true).
- Validations: `pytest tests/unit/test_timeline_builder.py -v` → 14 passed; `pytest tests/unit/ -q` → 109 passed; primeiro item em 0.0; sem gaps; last end_sec dentro de 0.05s do master; clip_file=null.
- Docs updated: none.
- Notes for next task: T-012 (subtitles, depends T-011 ✓) e T-013 (assets, depends T-001 ✓) estão ambos desbloqueados. T-014 depende de T-010 ✓ e T-013. T-015 depende de T-011 ✓ e T-014. TimelineError é a exceção canônica do módulo. concat_list.txt fica em audio/master/ como artefato de debug.

## 2026-03-15 - T-012 - Generate subtitles directly from the timeline

- Outcome: generate_subtitles() implementado; subtitles.srt gerado com um cue por item de timeline; texto preservado exatamente; 11 unit tests passando; 120 testes totais verdes.
- Files changed: app/modules/subtitles.py (criado), tests/unit/test_subtitles.py (criado), TASKS.md (T-012 status → true).
- Validations: `pytest tests/unit/test_subtitles.py -v` → 11 passed; primeiro cue em 00:00:00,000; numeração contígua desde 1; timings gap-free; texto idêntico ao da timeline; arquivo válido SRT.
- Docs updated: none.
- Notes for next task: T-013 (assets, depends T-001 ✓) está desbloqueado. T-014 depende de T-010 ✓ e T-013. T-015 depende de T-011 ✓ e T-014. SubtitleError é a exceção canônica. _sec_to_srt_timestamp() converte segundos para HH:MM:SS,mmm.
