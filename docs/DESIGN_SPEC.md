# DESIGN_SPEC

## 1. Papel deste documento

Este e o documento raiz de fonte de verdade do projeto.

Toda iteracao de um code agent em Ralph Loop deve:

1. abrir `TASKS.md`;
2. selecionar a primeira task com `status: false` e dependencias satisfeitas;
3. ler este arquivo por inteiro;
4. usar o indice de lookup abaixo para abrir somente as specs necessarias em `docs/specs/`;
5. executar uma unica task;
6. validar, atualizar status e parar.

Se houver conflito entre este arquivo, `TASKS.md` e qualquer arquivo em `docs/specs/`, o agente deve parar e corrigir a documentacao antes de continuar implementacao.

## 2. Verdade geral do produto

O projeto gera automaticamente videos curtos verticais no estilo de dialogo humoristico entre dois personagens.

Entrada:

- um `job` JSON com `topic`, `duration_target_sec`, `background_style`, `characters` e `output_preset`;
- execucao via CLI;
- suporte a execucao batch na fase final do MVP.

Saida:

- um arquivo final `MP4` vertical `9:16`;
- artefatos intermediarios auditaveis por job;
- logs estruturados por etapa.

Objetivo central:

`um unico comando -> um unico input JSON -> um unico video MP4 vertical completo`

## 3. Escopo do MVP

O MVP inclui:

- validacao de input de job;
- roteiro estruturado entre dois personagens;
- TTS por fala;
- timeline consolidada;
- lip-sync por fala;
- fundo satisfatorio unico por video;
- legendas geradas a partir da timeline;
- composicao final com FFmpeg;
- execucao end-to-end por CLI;
- batch sequencial basico;
- logs e metadados minimos.

O MVP nao inclui:

- painel web;
- publicacao automatica em redes sociais;
- fila distribuida;
- multiplos personagens ativos por cena;
- multiplas expressoes faciais;
- geracao procedural de fundo por IA;
- edicao manual em ferramentas externas.

## 4. Requisitos funcionais canonicos

- RF-01: gerar roteiro curto estruturado em dialogo entre dois personagens.
- RF-02: separar o roteiro por falas com ordem, speaker e texto limpo.
- RF-03: gerar um arquivo de audio por fala.
- RF-04: consolidar uma timeline com `start_sec`, `end_sec`, `duration_sec`, speaker, texto e caminhos de artefatos.
- RF-05: gerar um talking head por fala.
- RF-06: selecionar e preparar um fundo compativel com a duracao final.
- RF-07: compor fundo, personagens, hook, audio master e legendas em um video final.
- RF-08: gerar legendas com timestamps.
- RF-09: exportar um MP4 vertical final pronto para publicacao.
- RF-10: processar multiplos jobs em modo batch sequencial.

## 5. Requisitos nao funcionais canonicos

- RNF-01: automacao total, sem edicao manual.
- RNF-02: reproducibilidade por contratos e caminhos previsiveis.
- RNF-03: modularidade por adapters e contratos de arquivo.
- RNF-04: observabilidade com logs por etapa e metadados.
- RNF-05: extensibilidade para trocar providers e adicionar personagens/fundos.
- RNF-06: eficiencia operacional com stack simples e validacoes focadas.

## 6. Invariantes arquiteturais

- O projeto roda em um unico container Docker no MVP.
- A linguagem principal e Python.
- O pipeline e orientado a arquivos, nao a banco de dados.
- O sistema e executado primeiro via CLI.
- Toda integracao externa deve ficar atras de interface ou adapter.
- Cada etapa deve ler e escrever artefatos previsiveis em disco.
- Artefatos intermediarios fazem parte do produto e nao devem ser descartados silenciosamente.
- `assets/` contem apenas recursos fixos.
- `output/` contem apenas artefatos gerados.
- `temp/` contem apenas cache e intermediarios descartaveis.
- O pipeline de job unico e fail-fast no MVP.
- Batch continua para o proximo item mesmo se um item falhar.

## 7. Contratos e caminhos canonicos

### 7.1 Input de job

Exemplo canonico:

```json
{
  "topic": "explique inflacao de forma engracada",
  "duration_target_sec": 30,
  "background_style": "minecraft_parkour",
  "characters": ["char_a", "char_b"],
  "output_preset": "shorts_default"
}
```

Regras gerais:

- `topic` obrigatorio e nao vazio;
- `duration_target_sec` usa o default de runtime, `30` no MVP; quando informado, deve ficar entre `20` e `45`;
- `characters` default `["char_a", "char_b"]`; apos materializacao dos defaults, deve conter exatamente `2` personagens unicos;
- `background_style` default `auto`;
- `output_preset` default `shorts_default`;
- `job_id` e sempre gerado pelo sistema.

### 7.2 Workspace por job

Todo job deve persistir em:

- `output/jobs/<job_id>/script/`
- `output/jobs/<job_id>/audio/segments/`
- `output/jobs/<job_id>/audio/master/`
- `output/jobs/<job_id>/clips/`
- `output/jobs/<job_id>/background/`
- `output/jobs/<job_id>/subtitles/`
- `output/jobs/<job_id>/render/`
- `output/jobs/<job_id>/logs/`

### 7.3 Artefatos canonicos

- `script/script.json`
- `script/dialogue.json`
- `script/timeline.json`
- `audio/segments/001_char_a.mp3`
- `audio/segments/002_char_b.mp3`
- `audio/manifest.json`
- `audio/master/master_audio.wav`
- `clips/001_char_a_talk.mp4`
- `clips/002_char_b_talk.mp4`
- `background/prepared_background.mp4`
- `subtitles/subtitles.srt`
- `render/final.mp4`
- `render/render_metadata.json`
- `logs/job.log`

### 7.4 Pipeline canonico

Ordem obrigatoria de execucao:

1. `validate_input`
2. `init_job_workspace`
3. `write_script`
4. `generate_tts`
5. `build_timeline`
6. `generate_lipsync`
7. `prepare_background`
8. `generate_subtitles`
9. `compose_video`
10. `finalize_job`

## 8. Lookup index de specs

Use esta tabela para abrir apenas a documentacao necessaria para a task atual.

| Area | Keywords de busca | Abrir quando a task envolver | Arquivo |
|---|---|---|---|
| Spec overview | specs, index, lookup, source of truth | descobrir onde esta a spec detalhada de uma funcionalidade | `docs/specs/README.md` |
| Job input | input, job, payload, schema, validation, defaults, job_id | validar entrada, defaults, contrato do job | `docs/specs/SYSTEM_JOB_INPUT_SPEC.md` |
| Script writer | script, dialogue, hook, llm, prompt, speakers | gerar roteiro, prompts, saida de dialogo | `docs/specs/MODULE_SCRIPT_WRITER_SPEC.md` |
| TTS | tts, voice, speech, manifest, segment audio | gerar audio por fala, voice mapping | `docs/specs/MODULE_TTS_SPEC.md` |
| Timeline | timeline, master audio, start_sec, end_sec, concatenation | consolidar duracoes, audio master e timeline | `docs/specs/MODULE_TIMELINE_BUILDER_SPEC.md` |
| Lip-sync | lipsync, talking head, clip_file, character clip | gerar video por fala a partir de imagem + audio | `docs/specs/MODULE_LIPSYNC_SPEC.md` |
| Background | background, satisfying video, crop, loop, 9:16 | selecionar e adaptar o fundo | `docs/specs/MODULE_BACKGROUND_SELECTOR_SPEC.md` |
| Subtitles | subtitles, srt, captions, cue timing | gerar legendas a partir da timeline | `docs/specs/MODULE_SUBTITLES_SPEC.md` |
| Compositor | compositor, render, final mp4, ffmpeg, layout, preset | compor video final e metadata de render | `docs/specs/MODULE_COMPOSITOR_SPEC.md` |
| Assets | assets, characters, fonts, presets, metadata, backgrounds | localizar e validar recursos fixos | `docs/specs/SYSTEM_ASSET_MANAGEMENT_SPEC.md` |
| Orchestration | pipeline, stage order, fail-fast, single job | encadear etapas end-to-end | `docs/specs/SYSTEM_PIPELINE_ORCHESTRATION_SPEC.md` |
| Observability | logs, metadata, stage events, jsonl, monitoring | registrar eventos, logs e metadados | `docs/specs/SYSTEM_OBSERVABILITY_SPEC.md` |
| Batch | batch, csv, multi-job, report | processar varios jobs sequencialmente | `docs/specs/SYSTEM_BATCH_PROCESSING_SPEC.md` |

## 9. Regras de consulta para agents

- Nao abra todos os arquivos em `docs/specs/` na mesma iteracao.
- Sempre abra este arquivo primeiro.
- Depois abra somente as specs relacionadas a task atual.
- Se a task tocar duas capacidades, abra apenas as duas specs relevantes e nada alem disso.
- Se faltar detalhe para implementar sem ambiguidade, atualize a spec primeiro.
- Nao implemente comportamento que nao esteja em `TASKS.md` ou nas specs referenciadas.

## 10. Regras de produto

### Duracao

- videos entre `20` e `45` segundos;
- falas curtas;
- evitar monologos longos.

### Ritmo

- hook claro nos primeiros `2` segundos;
- densidade verbal alta, mas compreensivel;
- dinamismo visual mesmo com personagens baseados em imagem estatica.

### Legibilidade

- legenda grande;
- contraste suficiente;
- area segura para subtitulos definida por preset.

### Fundo

- movimento continuo;
- nao competir excessivamente com a fala;
- tratavel por crop, escurecimento ou blur leve.

## 11. Criterios de sucesso do MVP

O MVP estara pronto quando:

- aceitar um input JSON unico validado;
- gerar todos os artefatos intermediarios canonicos;
- renderizar `output/jobs/<job_id>/render/final.mp4`;
- operar sem edicao manual;
- repetir o processo para multiplos temas com pouca mudanca de configuracao.

## 12. Relacao com outros docs em /docs

- `docs/DESIGN_SPEC.md`: fonte de verdade raiz para escopo, invariantes e lookup.
- `docs/specs/*.md`: fonte de verdade detalhada por funcionalidade.
- `docs/PROJECT_PLAN.md`, `docs/PROJECT_ARCHITECTURE.md`, `docs/PROJECT_TOOLS.md`, `docs/PROJECT_WORKTREE.md`: contexto de apoio historico; use apenas se uma task ou uma spec exigir contexto adicional.
