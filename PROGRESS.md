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

## 2026-03-15 - T-013 - Prepare canonical character assets, fonts, and render presets

- Outcome: ativos canônicos criados; asset_service.py implementado; 16 unit tests passando (12 isolados + 4 de integração com ativos reais); 136 testes totais verdes.
- Files changed: assets/characters/char_a/base.png (criado, Pillow), assets/characters/char_a/metadata.json (criado), assets/characters/char_b/base.png (criado), assets/characters/char_b/metadata.json (criado), assets/fonts/LiberationSans-Bold.ttf (copiado, SIL OFL), assets/presets/shorts_default.json (criado, todos os campos obrigatórios), config/render.example.json (criado), app/services/asset_service.py (criado), tests/unit/test_asset_service.py (criado), TASKS.md (T-013 status → true).
- Validations: `pytest tests/unit/test_asset_service.py -v` → 16 passed; TestRealAssets confirma ativos reais no repo; load_character/load_preset/resolve_font/list_backgrounds falham claramente para entradas inválidas.
- Docs updated: none.
- Notes for next task: T-014 (lip-sync boundary, depends T-010 ✓ e T-013 ✓) está desbloqueado. Asset service usa CWD-relative paths via _ASSETS_ROOT = Path('assets'). load_character() retorna {'base_png': Path, 'metadata': dict}. load_preset() valida os 11 campos obrigatórios. Fonte canônica: LiberationSans-Bold.ttf. Preset canônico: shorts_default.

## 2026-03-15 - T-014 - Add the lip-sync engine boundary

- Outcome: interface LipSyncEngine (ABC) implementada; LipSyncError definida; 6 unit tests passando; 142 testes totais verdes.
- Files changed: app/adapters/lipsync_engine_adapter.py (criado), tests/unit/test_lipsync_adapter.py (criado), TASKS.md (T-014 status → true).
- Validations: `pytest tests/unit/test_lipsync_adapter.py -v` → 6 passed; interface não instanciável; subclasse concreta funciona; LipSyncError levantada corretamente.
- Docs updated: none.
- Notes for next task: T-015 depende de T-011 ✓ e T-014 ✓ — pode começar agora. LipSyncEngine.generate(image_path, audio_path, output_path) → Path é o contrato canônico. LipSyncError para falhas de engine. T-015 deve implementar generate_lipsync(ctx, engine) em app/modules/lipsync.py.

## 2026-03-15 - T-015 - Generate one talking-head clip per timeline item

- Outcome: generate_lipsync() implementado; um clip por item de timeline; timeline.json atualizado apenas em clip_file; 10 unit tests passando; 152 testes totais verdes.
- Files changed: app/modules/lipsync.py (criado), tests/unit/test_lipsync_module.py (criado), TASKS.md (T-015 status → true).
- Validations: `pytest tests/unit/test_lipsync_module.py -v` → 10 passed; `pytest tests/unit/ -q` → 152 passed; nomes de clip NNN_speaker_talk.mp4; apenas clip_file atualizado; duração dentro de 0.10s; erros claros para asset/engine ausentes.
- Docs updated: none.
- Notes for next task: T-016 (background selector, depends T-013 ✓) e T-017 (ffmpeg adapter, depends T-002 ✓) estão desbloqueados. generate_lipsync(ctx, engine) lê timeline.json, chama load_character(speaker), engine.generate(base_png, audio_file, clip_path), valida duração, escreve clip_file. BlackClipEngine (stub FFmpeg) em tests pode ser reutilizado em T-018.

## 2026-03-15 - T-016 - Select, loop, trim, and normalize the background video

- Outcome: prepare_background() implementado; seleção determinística por hash MD5 do job_id; looping via -stream_loop -1; trim via -t; scale-to-cover 1080x1920; 9 unit tests passando; 161 testes totais verdes.
- Files changed: app/modules/background_selector.py (criado), tests/unit/test_background_selector.py (criado), TASKS.md (T-016 status → true).
- Validations: `pytest tests/unit/test_background_selector.py -v` → 9 passed; seleção explícita usa categoria correta; auto-seleção determinística; fonte curta é loopada; fonte longa é trimada; output em canonical path.
- Docs updated: none.
- Notes for next task: T-017 (ffmpeg adapter, depends T-002 ✓) está desbloqueado. BackgroundError é a exceção canônica. prepare_background(ctx, required_duration_sec) é o contrato. _select_background(style, job_id) pode ser importada isoladamente para testes.

## 2026-03-15 - T-017 - Centralize FFmpeg and FFprobe operations

- Outcome: app/adapters/ffmpeg_adapter.py criado com run_ffmpeg(), concat_audio(), scale_and_trim_video(); ffprobe_utils.py expandido com get_media_duration() e get_video_dimensions(); app/utils/video_utils.py criado com make_color_video(); background_selector.py e timeline_builder.py refatorados para usar o adapter; 15 unit tests passando; 176 testes totais verdes.
- Files changed: app/adapters/ffmpeg_adapter.py (criado), app/utils/video_utils.py (criado), app/utils/ffprobe_utils.py (expandido: get_media_duration, get_video_dimensions, _run_ffprobe; get_audio_duration delegando a get_media_duration), app/modules/background_selector.py (refatorado para usar ffmpeg_adapter), app/modules/timeline_builder.py (refatorado para usar concat_audio), tests/unit/test_ffmpeg_adapter.py (criado), TASKS.md (T-017 status → true).
- Validations: `pytest tests/unit/test_ffmpeg_adapter.py -v` → 15 passed; `pytest tests/unit/ -q` → 176 passed; timeline e background testes ainda passam após refatoração.
- Docs updated: none.
- Notes for next task: T-018 (compositor, depends T-012 ✓, T-015 ✓, T-016 ✓, T-017 ✓) está desbloqueado. Usar scale_and_trim_video() e concat_audio() do ffmpeg_adapter no compositor. get_video_dimensions() disponível para validar saída. FFmpegError para falhas de comando. make_color_video() em video_utils disponível para fixtures de teste.

## 2026-03-15 - T-018 - Implement the final compositor and render metadata output

- Outcome: compose_video() implementado com filter_complex dinâmico; clips e imagens inativas por janela de tempo; título via drawtext; legendas via subtitles filter; render_metadata.json com todos os campos obrigatórios; 9 testes de integração passando; 185 testes totais verdes.
- Files changed: app/modules/compositor.py (criado), app/services/render_service.py (criado), tests/integration/test_compositor.py (criado), TASKS.md (T-018 status → true).
- Validations: `pytest tests/integration/test_compositor.py -v` → 9 passed; final.mp4 existe e é 1080x1920; duração dentro de 0.10s; render_metadata.json com todos os campos; erros claros para artifacts ausentes.
- Docs updated: none.
- Notes for next task: T-019 (pipeline end-to-end, depends T-018 ✓) está desbloqueado. compose_video(ctx) → Path; write_render_metadata(ctx, preset_name, n) → dict. filter_complex usa -itsoffset por clip e -loop 1 por imagem inativa; cada input referenciado exatamente uma vez. CompositorError para falhas.

## 2026-03-15 - T-019 - Chain the full single-job pipeline end to end

- Outcome: run_pipeline() implementado com os 10 stages canônicos em ordem; fail-fast; job_log emite stage_started/stage_completed/stage_failed; main.py atualizado; 7 testes de integração passando; 192 testes totais verdes.
- Files changed: app/pipeline.py (criado), app/main.py (atualizado), tests/integration/test_pipeline.py (criado), TASKS.md (T-019 status → true).
- Validations: `pytest tests/integration/test_pipeline.py -v` → 7 passed; final.mp4 produzido; todos os artefatos canônicos existem; ordem de stages verificada via job.log; falha em lipsync preserva script/audio/timeline; falha em validate_input não cria workspace.
- Docs updated: none.
- Notes for next task: T-020 (observability logging, depends T-019 ✓) está desbloqueado. run_pipeline(job_file, llm, tts, lipsync) é o contrato canônico. PipelineError wraps a exceção original. JobLogger já emite eventos em JSON Lines — T-020 deve validar e fortalecer os campos obrigatórios do contrato.

## 2026-03-15 - T-020 - Implement canonical stage logging and execution metadata

- Outcome: pipeline.py atualizado para emitir stage_started/stage_completed retrospectivos para init_job_workspace após criação do workspace; tests/integration/test_observability.py criado com 12 testes validando contrato completo de logging; todos passando.
- Files changed: app/pipeline.py (adicionados logs retrospectivos para init_job_workspace), tests/integration/test_observability.py (criado), TASKS.md (T-020 status → true).
- Validations: `pytest tests/integration/test_observability.py -v` → 12 passed; cada linha do log é JSON válido; campos obrigatórios presentes em todos os entries; nomes de stage canônicos; nomes de evento canônicos; job_id consistente; cada stage tem started+completed; sem stage_failed em run de sucesso; render_metadata.json presente em sucesso; exatamente 1 stage_failed em falha (generate_lipsync); stage_failed tem error_type e error_message; render_metadata.json ausente em falha; validate_input failure não cria job.log.
- Docs updated: none.
- Notes for next task: T-021 (batch processing, depends T-019 ✓) está desbloqueado. O contrato completo de logging está validado: JSON Lines em logs/job.log, campos {timestamp_utc, job_id, stage, event, message}, events canônicos {stage_started, stage_completed, stage_failed}, stage_failed inclui {error_type, error_message}. validate_input falha antes do workspace — nenhum log é criado. init_job_workspace é logado retrospectivamente após workspace criado.

## 2026-03-15 - T-021 - Add sequential batch processing and final batch report

- Outcome: batch runner implementado; app/main.py --batch wired para run_batch(); scripts/run_batch.sh criado; 10 integration tests passando; pré-existente regressão em test_stages_execute_in_canonical_order corrigida (expected_order faltava init_job_workspace introduzido em T-020); 214 testes totais verdes.
- Files changed: app/batch.py (já existia untracked, sem mudanças), inputs/batch/jobs.csv (já existia untracked), app/main.py (--batch branch implementado usando run_batch()), scripts/run_batch.sh (criado), tests/integration/test_batch.py (criado, 10 testes), tests/integration/test_pipeline.py (expected_order corrigido para incluir init_job_workspace), TASKS.md (T-021 status → true).
- Validations: `pytest tests/integration/test_batch.py -v` → 10 passed; `pytest tests/ -q` → 214 passed; batch com 2 itens válidos produz 2 workspaces isolados; batch com item inválido continua e reporta falha; report escrito em output/batch_reports/latest_report.json com todos os campos obrigatórios.
- Docs updated: none.
- Notes for next task: T-022 (hardening, depends T-020 ✓) e T-023 (docs, depends T-019 ✓) estão ambos desbloqueados. T-022 é o primeiro na ordem. run_batch(batch_file, llm, tts, lipsync) → report dict; cada item tem job_id, input_ref, status, output_file, error_message. _parse_row() converte CSV row em job payload (topic obrigatório; outros opcionais). job_id=None em itens falhados antes de run_pipeline.

## 2026-03-15 - T-022 - Harden the MVP with validation, retries, and minimum tests

- Outcome: app/core/exceptions.py criado com base ViralVideosError e hierarquia documentada; app/utils/retry.py criado com retry() exponential backoff; app/config.py expandido com provider_max_retries; pipeline.py atualizado para usar _run_with_retry() para write_script, generate_tts, generate_lipsync; 9 unit tests de retry passando; 223 testes totais verdes.
- Files changed: app/core/exceptions.py (criado), app/utils/retry.py (criado), app/config.py (provider_max_retries adicionado), app/pipeline.py (_run_with_retry() adicionado; write_script/generate_tts/generate_lipsync usam retry), tests/unit/test_retry.py (criado, 9 testes), TASKS.md (T-022 status → true).
- Validations: `pytest tests/unit/test_retry.py -v` → 9 passed; `pytest tests/ -q` → 223 passed; retry() falha-imediata para non-retryable; backoff exponencial verificado via monkeypatch de time.sleep.
- Docs updated: none.
- Notes for next task: T-023 (docs, depends T-019 ✓) é o último task. provider_max_retries configurável via env PROVIDER_MAX_RETRIES (default 3). retry() re-raises última exceção retryable após esgotar tentativas; non-retryable propaga imediatamente. _run_with_retry() é transparente ao contrato de logging (um stage_started, um stage_completed/failed).

## 2026-03-15 - T-023 - Add minimum operational documentation for humans and agents

- Outcome: README.md atualizado com status completo e seção de documentação técnica; scripts/run_single.sh criado; scripts/cleanup_temp.sh criado; Makefile criado com targets build/run/batch/test/lint/clean; lint corrigido em 5 arquivos (unused imports/vars); 223 testes ainda verdes; `ruff check app/` passa sem erros.
- Files changed: README.md (status table atualizado, seção de docs adicionada, scripts e Makefile documentados, estrutura de projeto corrigida), scripts/run_single.sh (criado), scripts/cleanup_temp.sh (criado), Makefile (criado), app/adapters/ffmpeg_adapter.py (import tempfile removido), app/services/render_service.py (import Path removido), app/modules/lipsync.py (import AssetError removido), app/utils/retry.py (import Any removido), app/main.py (variáveis renomeadas para suprimir F841), TASKS.md (T-023 status → true).
- Validations: `ruff check app/` → All checks passed; `pytest tests/ -q` → 223 passed; `python -m app.main --help` → saída correta; README aponta para docs/DESIGN_SPEC.md e docs/specs/.
- Docs updated: README.md.
- Notes for next task: Todos os 23 tasks do MVP estão completos. O pipeline end-to-end está implementado, testado e documentado. Para usar em produção: implementar adapters reais (LLM, TTS, LipSync) e registrá-los em app/main.py._build_providers().
