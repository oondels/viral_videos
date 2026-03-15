# viral-videos

Gerador automatizado de vídeos curtos verticais no estilo de diálogo humorístico entre dois personagens.

Um único comando. Um único input JSON. Um único vídeo MP4 vertical completo.

---

## Como funciona

O sistema recebe um tópico e produz um vídeo vertical 9:16 pronto para publicação, passando por:

```
Input JSON
  → Validação
  → Gerador de roteiro (LLM)
  → TTS por fala
  → Timeline consolidada
  → Lip-sync por personagem
  → Seleção de fundo
  → Geração de legendas
  → Composição final (FFmpeg)
  → final.mp4
```

Todos os artefatos intermediários são preservados por job para auditoria e debug.

---

## Requisitos

- Docker
- Docker Compose
- Credenciais das APIs externas (OpenAI, ElevenLabs)

---

## Configuração

Copie o arquivo de exemplo e preencha as credenciais:

```bash
cp .env.example .env
```

Variáveis necessárias:

| Variável | Descrição |
|---|---|
| `OPENAI_API_KEY` | Chave da OpenAI (geração de roteiro) |
| `ELEVENLABS_API_KEY` | Chave da ElevenLabs (TTS) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Credenciais Google Cloud TTS (alternativo) |
| `LOG_LEVEL` | Nível de log (`INFO`, `DEBUG`) |
| `DEFAULT_DURATION_SEC` | Duração padrão do vídeo em segundos |
| `DEFAULT_BACKGROUND_STYLE` | Estilo de fundo padrão (`minecraft_parkour`, `auto`, etc.) |

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
docker-compose run --rm app pytest
```

### Linting

```bash
docker-compose run --rm app ruff check app/
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

| Campo | Obrigatório | Descrição |
|---|---|---|
| `topic` | sim | Tema do vídeo (não vazio) |
| `duration_target_sec` | não | Entre 20 e 45 segundos (padrão: 30) |
| `background_style` | não | Estilo do fundo (padrão fixo: `auto`) |
| `characters` | não | Exatamente 2 personagens únicos (padrão: `["char_a", "char_b"]`) |
| `output_preset` | não | Preset de exportação (padrão: `shorts_default`) |

O `job_id` é sempre gerado automaticamente pelo sistema.

---

## Saída

Cada job gera um workspace isolado em `output/jobs/<job_id>/`:

```
output/jobs/<job_id>/
├── script/
│   ├── script.json          # roteiro bruto
│   ├── dialogue.json        # falas estruturadas
│   └── timeline.json        # timeline consolidada com tempos
├── audio/
│   ├── segments/
│   │   ├── 001_char_a.wav   # áudio de cada fala
│   │   └── 002_char_b.wav
│   ├── manifest.json        # mapeamento fala → arquivo → duração
│   └── master/
│       └── master_audio.wav # áudio final concatenado
├── clips/
│   ├── 001_char_a_talk.mp4  # talking head por fala
│   └── 002_char_b_talk.mp4
├── background/
│   └── prepared_background.mp4
├── subtitles/
│   └── subtitles.srt
├── render/
│   ├── final.mp4            # vídeo final
│   └── render_metadata.json
└── logs/
    └── job.log
```

---

## Estrutura do projeto

```
.
├── app/                  # código fonte
│   └── main.py           # entrypoint do pipeline
├── assets/               # recursos fixos (personagens, fontes, fundos)
├── config/               # configurações de runtime (mapeamento de vozes)
├── inputs/               # jobs de entrada
│   ├── examples/
│   └── batch/
├── output/               # artefatos gerados (não commitar)
├── temp/                 # cache temporário
├── tests/                # testes automatizados
├── docs/
│   ├── DESIGN_SPEC.md    # fonte de verdade do projeto
│   ├── PROJECT_PLAN.md   # plano de construção
│   └── specs/            # specs detalhadas por módulo
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

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

## Status

O projeto está em fase de implementação. Consulte `TASKS.md` para o estado atual das tarefas e `PROGRESS.md` para o histórico de progresso.
