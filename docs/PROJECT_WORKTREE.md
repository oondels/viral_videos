# Estrutura do Projeto (Work Tree)

## 1. Objetivo desta Estrutura

Esta work tree define como o repositório deve ser organizado para suportar um pipeline de geração automática de vídeos curtos com personagens falantes, fundo satisfatório, legendas e render final.

A estrutura precisa favorecer:

* clareza para humanos e code agents;
* separação entre código, assets, temporários e outputs;
* facilidade de debug;
* escalabilidade incremental.

---

## 2. Princípios da Estrutura

### 2.1 Separar código de mídia

Assets e outputs nunca devem se misturar com os módulos de código.

### 2.2 Isolar temporários

Arquivos intermediários pesados devem ficar em área própria.

### 2.3 Preservar artefatos por job

Cada execução deve poder ser auditada separadamente.

### 2.4 Facilitar automação

A árvore deve ser simples o bastante para scripts navegarem sem ambiguidade.

---

## 3. Work Tree Recomendada

```text
auto-viral-video/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── pipeline.py
│   ├── config.py
│   ├── logger.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── job_context.py
│   │   ├── contracts.py
│   │   ├── exceptions.py
│   │   └── types.py
│   │
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── script_writer.py
│   │   ├── tts.py
│   │   ├── timeline_builder.py
│   │   ├── lipsync.py
│   │   ├── background_selector.py
│   │   ├── subtitles.py
│   │   └── compositor.py
│   │
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── llm_adapter.py
│   │   ├── tts_provider_adapter.py
│   │   ├── lipsync_engine_adapter.py
│   │   ├── subtitle_provider_adapter.py
│   │   └── ffmpeg_adapter.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asset_service.py
│   │   ├── file_service.py
│   │   ├── metadata_service.py
│   │   └── render_service.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── json_utils.py
│   │   ├── path_utils.py
│   │   ├── audio_utils.py
│   │   ├── video_utils.py
│   │   ├── ffprobe_utils.py
│   │   └── text_utils.py
│   │
│   └── prompts/
│       ├── script_system_prompt.md
│       └── script_user_prompt_template.md
│
├── assets/
│   ├── characters/
│   │   ├── char_a/
│   │   │   ├── base.png
│   │   │   ├── metadata.json
│   │   │   └── masks/
│   │   └── char_b/
│   │       ├── base.png
│   │       ├── metadata.json
│   │       └── masks/
│   │
│   ├── backgrounds/
│   │   ├── slime/
│   │   ├── sand/
│   │   ├── minecraft_parkour/
│   │   ├── marble_run/
│   │   └── misc/
│   │
│   ├── fonts/
│   │   └── Montserrat-Bold.ttf
│   │
│   ├── overlays/
│   │   ├── title_bar.png
│   │   └── gradient_shadow.png
│   │
│   └── presets/
│       ├── shorts_default.json
│       └── reels_default.json
│
├── config/
│   ├── app.example.toml
│   ├── voices.example.json
│   ├── render.example.json
│   └── environments/
│       ├── dev.toml
│       └── prod.toml
│
├── inputs/
│   ├── examples/
│   │   ├── job_001.json
│   │   └── job_002.json
│   ├── batch/
│   │   └── jobs.csv
│   └── topics/
│       └── topics_list.txt
│
├── output/
│   ├── jobs/
│   │   └── <job_id>/
│   │       ├── script/
│   │       │   ├── script.json
│   │       │   └── dialogue.json
│   │       ├── audio/
│   │       │   ├── segments/
│   │       │   ├── master/
│   │       │   └── manifest.json
│   │       ├── clips/
│   │       ├── background/
│   │       ├── subtitles/
│   │       ├── render/
│   │       │   ├── final.mp4
│   │       │   └── render_metadata.json
│   │       └── logs/
│   │           └── job.log
│   │
│   └── batch_reports/
│       └── latest_report.json
│
├── temp/
│   ├── cache/
│   ├── intermediate/
│   └── ffmpeg/
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_script_writer.py
│   │   ├── test_timeline_builder.py
│   │   └── test_subtitles.py
│   ├── integration/
│   │   ├── test_tts_pipeline.py
│   │   ├── test_compositor.py
│   │   └── test_end_to_end.py
│   └── fixtures/
│       ├── sample_inputs/
│       ├── sample_audio/
│       └── sample_assets/
│
├── scripts/
│   ├── run_single.sh
│   ├── run_batch.sh
│   ├── prepare_assets.sh
│   └── cleanup_temp.sh
│
├── docs/
│   ├── design-specs.md
│   ├── arquitetura-do-projeto.md
│   ├── pipeline-de-funcionamento.md
│   ├── ferramentas-necessarias.md
│   ├── plano-de-construcao-do-projeto.md
│   └── estrutura-do-projeto-work-tree.md
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
└── Makefile
```

---

## 4. Explicação por Diretório

### `app/`

Contém o código-fonte principal.

#### Função

Abriga o orquestrador, módulos do pipeline, adapters externos, utilitários e contratos internos.

---

### `app/core/`

Contém os elementos centrais do domínio do pipeline.

#### Exemplos

* `job_context.py`: estado de execução do job;
* `contracts.py`: contratos de entrada e saída;
* `exceptions.py`: erros customizados.

#### Objetivo

Dar previsibilidade e base comum para todos os módulos.

---

### `app/modules/`

Contém os módulos funcionais do pipeline.

#### Módulos esperados

* `script_writer.py`
* `tts.py`
* `timeline_builder.py`
* `lipsync.py`
* `background_selector.py`
* `subtitles.py`
* `compositor.py`

#### Objetivo

Cada módulo deve resolver uma etapa específica da geração do vídeo.

---

### `app/adapters/`

Contém integrações com ferramentas externas.

#### Exemplos

* provider de LLM;
* provider de TTS;
* engine de lip-sync;
* FFmpeg wrapper.

#### Objetivo

Evitar acoplamento direto entre o domínio do projeto e ferramentas externas.

---

### `app/services/`

Contém serviços transversais reutilizáveis.

#### Função

Concentrar lógica auxiliar de arquivo, asset, render e metadados sem contaminar os módulos principais.

---

### `app/utils/`

Contém funções utilitárias pequenas e reutilizáveis.

#### Regra

Não colocar lógica de negócio aqui. Apenas helpers técnicos.

---

### `app/prompts/`

Contém prompts e templates utilizados pelo módulo de geração de roteiro.

#### Objetivo

Separar o texto de prompting do código executável.

---

### `assets/`

Contém todos os recursos fixos do sistema.

#### Subpastas importantes

* `characters/`: imagens e metadados dos personagens;
* `backgrounds/`: biblioteca de fundos satisfatórios;
* `fonts/`: fontes para legendas e títulos;
* `overlays/`: elementos visuais adicionais;
* `presets/`: presets de renderização e layout.

#### Regra

Nada em `assets/` deve ser resultado temporário do pipeline.

---

### `config/`

Contém configurações do sistema.

#### Exemplos

* configurações de ambiente;
* mapeamento de vozes;
* parâmetros de render;
* presets de execução.

#### Regra

Separar configurações versionáveis de segredos em `.env`.

---

### `inputs/`

Contém entradas para jobs unitários ou batch.

#### Utilidade

* testes manuais;
* regressão;
* geração em lote;
* exemplos para code agent e desenvolvedores.

---

### `output/`

Contém todas as saídas persistidas do pipeline.

#### Estratégia

Cada job deve ter sua própria pasta.

#### Benefício

* facilita auditoria;
* permite reprocessamento parcial;
* ajuda no debug de falhas.

---

### `temp/`

Contém arquivos temporários e caches.

#### Regra

Pode ser limpo periodicamente sem comprometer o resultado final persistido.

---

### `tests/`

Contém a suíte de testes.

#### Organização sugerida

* `unit/`: testes de lógica isolada;
* `integration/`: testes entre módulos;
* `fixtures/`: dados e assets de teste.

---

### `scripts/`

Contém comandos utilitários e automações operacionais.

#### Exemplos

* rodar job único;
* rodar batch;
* preparar assets;
* limpar temporários.

---

### `docs/`

Contém a documentação do projeto.

#### Objetivo

Servir como camada de contexto para desenvolvedores e code agents.

---

## 5. Convenção de Saída por Job

Cada job deve ter estrutura semelhante a esta:

```text
output/jobs/job_2026_03_15_001/
├── script/
├── audio/
├── clips/
├── background/
├── subtitles/
├── render/
└── logs/
```

### Motivo

Separação forte por job simplifica:

* rastreabilidade;
* rollback;
* análise de falha;
* reuso parcial.

---

## 6. Convenções de Nomenclatura

### Arquivos de áudio por fala

```text
001_char_a.wav
002_char_b.wav
```

### Clipes de personagem

```text
001_char_a_talk.mp4
002_char_b_talk.mp4
```

### Artefatos principais

```text
script.json
dialogue.json
timeline.json
manifest.json
subtitles.srt
final.mp4
render_metadata.json
```

### Regras

* prefixos numéricos para preservar ordem;
* nomes descritivos;
* evitar espaços;
* usar padrão consistente em todo o pipeline.

---

## 7. Arquivos Raiz Importantes

### `README.md`

Explica o projeto, setup, execução e fluxo geral.

### `.env.example`

Mostra as variáveis esperadas sem expor segredos.

### `requirements.txt` / `pyproject.toml`

Gerenciam dependências.

### `Makefile`

Pode concentrar comandos como:

* setup;
* run;
* test;
* lint;
* clean.

---

## 8. Regra Estrutural para o Code Agent

Ao criar arquivos, o code agent deve seguir estas prioridades:

1. colocar módulos de pipeline em `app/modules/`;
2. colocar integrações externas em `app/adapters/`;
3. manter configs fora do código;
4. nunca misturar output gerado com assets estáticos;
5. preservar a convenção de pastas por job.

---

## 9. Versão Mínima da Work Tree para Início Rápido

Se for necessário começar enxuto, a estrutura mínima pode ser:

```text
auto-viral-video/
├── app/
│   ├── main.py
│   ├── script_writer.py
│   ├── tts.py
│   ├── timeline_builder.py
│   ├── lipsync.py
│   ├── background_selector.py
│   ├── subtitles.py
│   └── compositor.py
├── assets/
│   ├── characters/
│   ├── backgrounds/
│   └── fonts/
├── config/
├── inputs/
├── output/
├── temp/
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

Depois ela pode evoluir para a árvore completa.

---

## 10. Conclusão

Esta work tree foi desenhada para sustentar o MVP e também suportar evolução futura sem reorganizações traumáticas.

Ela deve ser tratada como padrão estrutural do projeto, especialmente porque ajuda um code agent a entender:

* onde cada responsabilidade vive;
* onde salvar artefatos;
* como navegar no repositório;
* como manter o pipeline limpo e previsível.
