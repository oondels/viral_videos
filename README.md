# viral-videos

Gerador automatizado de vídeos curtos verticais no estilo de diálogo humorístico entre dois personagens.

**Um único comando. Um único input JSON. Um único vídeo MP4 vertical completo.**

---

## Como funciona

O sistema recebe um tópico e produz um vídeo vertical 9:16 pronto para publicação, passando por estas etapas na ordem:

```
Input JSON
  → 1. validate_input        — valida schema, materializa defaults, gera job_id
  → 2. init_job_workspace    — cria árvore de diretórios em output/jobs/<job_id>/
  → 3. write_script          — LLM gera hook + diálogo entre dois personagens
  → 4. generate_tts          — TTS por fala → WAV por linha + manifest.json
  → 5. build_timeline        — concatena WAVs → master_audio.wav + timeline.json
  → 6. generate_lipsync      — lip-sync por fala → clip MP4 por linha
  → 7. prepare_background    — seleciona fundo, adapta duração e formato 9:16
  → 8. generate_subtitles    — gera subtitles.srt a partir da timeline
  → 9. compose_video         — FFmpeg compõe tudo → final.mp4
  → 10. finalize_job         — metadados de render + log final
```

Todos os artefatos intermediários são preservados por job para auditoria e debug.

---

## Requisitos

- Docker
- Docker Compose
- Credenciais das APIs externas (OpenAI, ElevenLabs)

---

## Configuração

### 1. Credenciais

```bash
cp .env.example .env
```

Edite `.env` com suas chaves:

| Variável | Descrição |
|---|---|
| `OPENAI_API_KEY` | Chave da OpenAI — usada na geração de roteiro |
| `ELEVENLABS_API_KEY` | Chave da ElevenLabs — usada no TTS |
| `GOOGLE_APPLICATION_CREDENTIALS` | Credenciais Google Cloud TTS (alternativo) |
| `LOG_LEVEL` | Nível de log (`INFO`, `DEBUG`) |
| `DEFAULT_DURATION_SEC` | Duração padrão do vídeo em segundos (padrão: `30`) |

### 2. Mapeamento de vozes

O arquivo `config/voices.json` mapeia cada `character_id` para um `voice_id` da API de TTS:

```json
{
  "char_a": "seu_voice_id_aqui",
  "char_b": "outro_voice_id_aqui"
}
```

Use `config/voices.example.json` como ponto de partida. Os `voice_id` válidos dependem do provedor configurado (ElevenLabs, Google TTS, etc.).

### 3. Fundos

Coloque arquivos de vídeo MP4 nas pastas de categoria correspondentes:

```
assets/backgrounds/
├── minecraft_parkour/   # clips de Minecraft parkour
├── slime/               # vídeos de slime
├── sand/                # areia cinética
├── marble_run/          # corrida de bolinhas
└── misc/                # outros fundos satisfatórios
```

Use `background_style: "auto"` no input para seleção automática entre as categorias disponíveis.

---

## Uso

### Build

```bash
docker build -t viral-videos .
```

### Job único

```bash
docker-compose run --rm app python -m app.main --input inputs/examples/job_001.json
```

### Batch

```bash
docker-compose run --rm app python -m app.main --batch inputs/batch/jobs.csv
```

### Testes

```bash
# Todos os testes
docker-compose run --rm app pytest

# Apenas testes unitários
docker-compose run --rm app pytest tests/unit/ -v

# Um módulo específico
docker-compose run --rm app pytest tests/unit/test_timeline_builder.py -v
```

### Linting

```bash
docker-compose run --rm app ruff check app/
```

### Makefile (atalhos)

```bash
make build                                    # build da imagem
make run INPUT=inputs/examples/job_001.json   # job único
make batch CSV=inputs/batch/jobs.csv          # batch
make test                                     # todos os testes
make lint                                     # linter
make clean                                    # limpar temp/
```

### Scripts auxiliares

```bash
./scripts/run_single.sh inputs/examples/job_001.json   # job único via Docker Compose
./scripts/run_batch.sh inputs/batch/jobs.csv           # batch via Docker Compose
./scripts/cleanup_temp.sh                              # limpar temp/
```

---

## Formato do input

Arquivo JSON por job:

```json
{
  "topic": "explique inflação de forma engraçada",
  "duration_target_sec": 30,
  "background_style": "minecraft_parkour",
  "characters": ["char_a", "char_b"],
  "output_preset": "shorts_default"
}
```

| Campo | Obrigatório | Padrão | Descrição |
|---|---|---|---|
| `topic` | sim | — | Tema do vídeo (não vazio) |
| `duration_target_sec` | não | `30` | Entre 20 e 45 segundos |
| `background_style` | não | `auto` | `minecraft_parkour`, `slime`, `sand`, `marble_run`, `misc`, `auto` |
| `characters` | não | `["char_a", "char_b"]` | Exatamente 2 personagens únicos |
| `output_preset` | não | `shorts_default` | Preset de exportação em `assets/presets/` |

O `job_id` é sempre gerado automaticamente pelo sistema no formato `job_YYYY_MM_DD_NNN`.

Exemplos prontos em `inputs/examples/`.

---

## Saída

Cada job gera um workspace isolado em `output/jobs/<job_id>/`:

```
output/jobs/<job_id>/
├── script/
│   ├── script.json          # roteiro bruto com title_hook
│   ├── dialogue.json        # falas estruturadas (index, speaker, text)
│   └── timeline.json        # timeline consolidada com start_sec/end_sec
├── audio/
│   ├── segments/
│   │   ├── 001_char_a.wav   # áudio por fala
│   │   └── 002_char_b.wav
│   ├── manifest.json        # fala → arquivo → duração medida
│   └── master/
│       ├── master_audio.wav # áudio final concatenado
│       └── concat_list.txt  # lista de concatenação (debug)
├── clips/
│   ├── 001_char_a_talk.mp4  # talking head por fala
│   └── 002_char_b_talk.mp4
├── background/
│   └── prepared_background.mp4
├── subtitles/
│   └── subtitles.srt
├── render/
│   ├── final.mp4            # vídeo final 1080x1920
│   └── render_metadata.json
└── logs/
    └── job.log              # eventos JSON Lines por stage
```

---

## Estrutura do projeto

```
.
├── app/
│   ├── main.py                        # entrypoint CLI
│   ├── config.py                      # carregamento de .env
│   ├── logger.py                      # logger JSON Lines (process + job)
│   ├── core/
│   │   ├── contracts.py               # validação Pydantic do input de job
│   │   ├── job_context.py             # autoridade canônica de paths por job
│   │   └── types.py                   # tipos compartilhados
│   ├── modules/
│   │   ├── script_writer.py           # gera script.json e dialogue.json
│   │   ├── tts.py                     # gera segmentos WAV e manifest.json
│   │   ├── timeline_builder.py        # gera master_audio.wav e timeline.json
│   │   ├── lipsync.py                 # gera clips por fala, atualiza clip_file
│   │   ├── subtitles.py               # gera subtitles.srt
│   │   ├── background_selector.py     # seleciona e prepara fundo 9:16
│   │   └── compositor.py              # FFmpeg compõe final.mp4
│   ├── adapters/
│   │   ├── llm_adapter.py             # interface ScriptGenerator (ABC)
│   │   ├── tts_provider_adapter.py    # interface TTSProvider (ABC)
│   │   ├── lipsync_engine_adapter.py  # interface LipSyncEngine (ABC)
│   │   └── ffmpeg_adapter.py          # wraps FFmpeg/FFprobe shell commands
│   ├── services/
│   │   ├── asset_service.py           # resolve e valida ativos fixos
│   │   ├── file_service.py            # cria workspace por job
│   │   └── render_service.py          # escreve render_metadata.json
│   ├── core/
│   │   ├── contracts.py               # validação Pydantic do input de job
│   │   ├── exceptions.py              # hierarquia base de exceções
│   │   ├── job_context.py             # autoridade canônica de paths por job
│   │   └── types.py                   # tipos compartilhados
│   └── utils/
│       ├── path_utils.py              # paths canônicos de output
│       ├── audio_utils.py             # geração de WAV silencioso (testes)
│       ├── ffprobe_utils.py           # medição de duração via ffprobe
│       ├── retry.py                   # retry com backoff exponencial
│       └── video_utils.py             # helpers de vídeo (testes)
├── assets/
│   ├── characters/
│   │   ├── char_a/                    # base.png + metadata.json
│   │   └── char_b/                    # base.png + metadata.json
│   ├── backgrounds/                   # vídeos de fundo por categoria
│   ├── fonts/
│   │   └── LiberationSans-Bold.ttf   # fonte de legenda incluída
│   └── presets/
│       └── shorts_default.json        # preset 1080x1920, 30fps
├── config/
│   ├── voices.json                    # mapeamento character_id → voice_id
│   ├── voices.example.json            # template de exemplo
│   └── render.example.json            # exemplo de configuração de render
├── inputs/
│   ├── examples/                      # jobs de exemplo prontos para uso
│   └── batch/                         # CSVs para execução em lote
├── docs/
│   ├── DESIGN_SPEC.md                 # fonte de verdade do projeto — leia primeiro
│   └── specs/                         # specs detalhadas por módulo e subsistema
├── scripts/
│   ├── run_single.sh                  # atalho para job único via Docker Compose
│   ├── run_batch.sh                   # atalho para batch via Docker Compose
│   └── cleanup_temp.sh                # limpa temp/
├── tests/
│   ├── unit/                          # testes por módulo
│   ├── integration/                   # testes end-to-end por pipeline
│   └── fixtures/                      # inputs de exemplo para testes
├── output/                            # artefatos gerados (não commitar)
├── temp/                              # cache temporário
├── Makefile                           # atalhos para build, run, test, lint, clean
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Adicionando personagens e fundos

### Novo personagem

1. Crie a pasta `assets/characters/<character_id>/`
2. Adicione `base.png` (imagem do personagem, recomendado 400x600+)
3. Adicione `metadata.json`:
   ```json
   { "character_id": "<character_id>", "display_name": "Nome do Personagem" }
   ```
4. Adicione o `voice_id` correspondente em `config/voices.json`

### Novo fundo

Copie um arquivo MP4 para a pasta de categoria adequada em `assets/backgrounds/`. O sistema seleciona automaticamente dentro da categoria escolhida no input.

---

## Providers externos

Todas as integrações externas ficam atrás de interfaces abstratas (adapters). Nenhum módulo do pipeline acessa APIs diretamente.

| Interface | Localização | Substitui |
|---|---|---|
| `ScriptGenerator` | `app/adapters/llm_adapter.py` | OpenAI, Anthropic, Gemini, local LLM |
| `TTSProvider` | `app/adapters/tts_provider_adapter.py` | ElevenLabs, Google TTS, Azure TTS |
| `LipSyncEngine` | `app/adapters/lipsync_engine_adapter.py` | SadTalker, Wav2Lip, D-ID, HeyGen |

Para usar um provider diferente, implemente a interface correspondente e injete no pipeline.

---

## Volumes Docker

| Host | Container | Conteúdo |
|---|---|---|
| `./inputs/` | `/app/inputs` | Jobs de entrada |
| `./output/` | `/app/output` | Vídeos e artefatos gerados |
| `./assets/` | `/app/assets` | Personagens, fundos, fontes, presets |
| `./config/` | `/app/config` | Mapeamento de vozes e configurações de runtime |
| `./temp/` | `/app/temp` | Cache temporário |

---

## Status de implementação

| # | Módulo / Componente | Status |
|---|---|---|
| T-001 | Estrutura de pastas e pacotes Python | ✅ |
| T-002 | Ambiente Docker (Python 3.11, FFmpeg) | ✅ |
| T-003 | CLI, config loader, logger JSON Lines | ✅ |
| T-004 | Validação de input de job (Pydantic v2) | ✅ |
| T-005 | Job context e paths canônicos | ✅ |
| T-006 | Exemplos de input e fixtures de teste | ✅ |
| T-007 | Prompts de roteiro e interface LLM | ✅ |
| T-008 | Módulo gerador de roteiro | ✅ |
| T-009 | Interface TTS e mapeamento de vozes | ✅ |
| T-010 | Geração de áudio por fala + manifest.json | ✅ |
| T-011 | master_audio.wav + timeline.json | ✅ |
| T-012 | Geração de subtitles.srt | ✅ |
| T-013 | Ativos fixos (personagens, fonte, preset) | ✅ |
| T-014 | Interface lip-sync (adapter boundary) | ✅ |
| T-015 | Geração de clips por fala (lip-sync) | ✅ |
| T-016 | Seleção e preparação do fundo | ✅ |
| T-017 | Adapter centralizado de FFmpeg | ✅ |
| T-018 | Compositor final (FFmpeg) → final.mp4 | ✅ |
| T-019 | Pipeline end-to-end de job único | ✅ |
| T-020 | Logs e metadados canônicos por stage | ✅ |
| T-021 | Processamento batch sequencial | ✅ |
| T-022 | Hardening: erros, retries, timeouts | ✅ |
| T-023 | Documentação operacional final | ✅ |

Consulte `TASKS.md` para o estado detalhado e `PROGRESS.md` para o histórico de progresso.

---

## Documentação técnica

| Documento | Conteúdo |
|---|---|
| `docs/DESIGN_SPEC.md` | Fonte de verdade raiz — escopo, invariantes arquiteturais, paths canônicos |
| `docs/specs/` | Specs detalhadas por módulo e subsistema |
| `docs/specs/README.md` | Índice de todas as specs |

Comece por `docs/DESIGN_SPEC.md` antes de qualquer outra documentação.
