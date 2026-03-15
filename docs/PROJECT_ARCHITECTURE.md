# Arquitetura do Projeto

## 1. Visão Arquitetural

Este projeto deve ser tratado como um sistema de pipeline multimodal orientado a assets e processamento, não como uma aplicação tradicional focada em telas e banco de dados.

A arquitetura precisa receber um tópico, transformar esse tópico em múltiplos artefatos intermediários e produzir um vídeo final renderizado de forma totalmente automática.

O sistema deve seguir um desenho modular baseado em etapas desacopladas.

---

## 2. Macrocomponentes

A arquitetura recomendada é dividida nos seguintes blocos:

1. **Orquestração**
2. **Geração de roteiro**
3. **Síntese de voz**
4. **Geração de talking heads / lip-sync**
5. **Seleção e preparação de fundo**
6. **Geração de legendas**
7. **Composição e renderização**
8. **Gerenciamento de assets e outputs**
9. **Configuração e observabilidade**

---

## 3. Camadas da Arquitetura

### 3.1 Camada de Entrada

Responsável por receber a intenção de geração do vídeo.

Pode ter as seguintes formas:

* CLI;
* arquivo JSON;
* CSV batch;
* integração futura com webhook ou fila.

Exemplo de payload:

```json
{
  "topic": "explique procrastinação de forma engraçada",
  "duration_target_sec": 30,
  "background_style": "slime",
  "characters": ["char_a", "char_b"],
  "output_preset": "shorts_default"
}
```

---

### 3.2 Camada de Orquestração

Responsável por coordenar o fluxo de execução.

Funções principais:

* validar input;
* criar `job_id`;
* inicializar diretórios de trabalho;
* disparar cada etapa do pipeline;
* consolidar estados;
* lidar com falhas;
* registrar logs.

Esse componente deve atuar como o maestro do sistema.

---

### 3.3 Camada de Geração de Conteúdo

Responsável por produzir o roteiro estruturado.

Submódulos:

* `script_writer`;
* `dialogue_formatter`;
* `content_validator`.

Responsabilidades:

* gerar hook;
* criar falas curtas;
* manter alternância entre personagens;
* limitar complexidade textual;
* devolver estrutura consumível pelas próximas etapas.

Saída ideal:

```json
{
  "title_hook": "Peter explains procrastination badly",
  "dialogue": [
    {"speaker": "char_a", "text": "Why do people procrastinate?"},
    {"speaker": "char_b", "text": "Because the future version of you keeps getting dumped with your problems."}
  ]
}
```

---

### 3.4 Camada de Áudio

Responsável por transformar cada fala em voz sintética.

Submódulos:

* `voice_mapper`;
* `tts_provider`;
* `audio_normalizer`;
* `audio_concatenator`.

Responsabilidades:

* mapear personagem para voz;
* gerar arquivos individuais por fala;
* medir duração;
* normalizar volume, sample rate e codec;
* concatenar o áudio master.

Saídas esperadas:

* áudios individuais;
* áudio master;
* manifesto de falas com durações.

---

### 3.5 Camada de Animação Facial

Responsável por gerar vídeos curtos dos personagens falando.

Submódulos:

* `character_asset_loader`;
* `lipsync_engine_adapter`;
* `clip_exporter`.

Responsabilidades:

* carregar a imagem-base do personagem;
* associar áudio correto;
* gerar clipe de talking head;
* registrar falhas por fala.

Essa camada não deve conhecer regras de composição final. Ela apenas produz os clipes falantes.

---

### 3.6 Camada de Fundo

Responsável por selecionar e preparar o background satisfatório.

Submódulos:

* `background_selector`;
* `background_duration_adjuster`;
* `background_transformer`.

Responsabilidades:

* escolher o fundo por tema, preset ou aleatoriedade controlada;
* garantir duração mínima;
* aplicar loop se necessário;
* redimensionar/cortar para 9:16;
* opcionalmente aplicar blur ou escurecimento.

---

### 3.7 Camada de Legendas

Responsável por gerar o texto legendado com timestamps.

Submódulos:

* `transcriber`;
* `subtitle_segmenter`;
* `subtitle_formatter`.

Responsabilidades:

* transcrever o áudio master;
* segmentar frases curtas;
* gerar `.srt`;
* aplicar padrões visuais compatíveis com redes sociais.

---

### 3.8 Camada de Composição

Responsável por transformar todos os artefatos intermediários em um vídeo final.

Submódulos:

* `layout_engine`;
* `timeline_renderer`;
* `ffmpeg_composer`.

Responsabilidades:

* compor o fundo;
* alternar personagem principal conforme o speaker ativo;
* posicionar personagem secundário;
* embutir título/hook;
* queimar legendas;
* exportar MP4 final.

Essa é a camada que consolida todo o sistema.

---

### 3.9 Camada de Persistência de Artefatos

Responsável por armazenar os arquivos produzidos.

Categorias:

* assets fixos;
* arquivos temporários;
* saídas intermediárias;
* saídas finais;
* logs.

Essa separação é importante para permitir debug por etapa e reuso parcial de resultados.

---

## 4. Fluxo Arquitetural de Alto Nível

```text
Input
  -> Orchestrator
    -> Script Writer
    -> TTS Engine
    -> Audio Timeline Builder
    -> Lip-Sync Generator
    -> Background Selector
    -> Subtitle Generator
    -> Composer / FFmpeg Renderer
    -> Final MP4
```

---

## 5. Estilo Arquitetural Recomendado

### Padrão principal

Arquitetura modular por pipeline com adaptadores de ferramentas externas.

### Motivos

* facilita troca de provedores;
* reduz acoplamento;
* simplifica teste por etapa;
* melhora manutenção.

### Decisão importante

As integrações com ferramentas externas devem ficar atrás de interfaces/adapters.

Exemplos:

* `TTSProvider`;
* `LipSyncEngine`;
* `SubtitleProvider`;
* `Renderer`.

Assim, se você trocar ElevenLabs por outro TTS, o impacto fica isolado.

---

## 6. Contratos Internos Recomendados

### 6.1 Contrato de diálogo

```json
[
  {"speaker": "char_a", "text": "What is inflation?"},
  {"speaker": "char_b", "text": "It is when your money loses power."}
]
```

### 6.2 Contrato de fala renderizada

```json
{
  "speaker": "char_a",
  "text": "What is inflation?",
  "audio_file": "output/audio/001_char_a.wav",
  "duration_sec": 2.34
}
```

### 6.3 Contrato de timeline

```json
[
  {
    "index": 1,
    "speaker": "char_a",
    "text": "What is inflation?",
    "start": 0.0,
    "end": 2.34,
    "audio_file": "output/audio/001_char_a.wav",
    "clip_file": "output/clips/001_char_a.mp4"
  }
]
```

---

## 7. Decisões Técnicas Estruturais

### 7.1 Linguagem principal

Python.

Justificativa:

* bom ecossistema para IA;
* boa integração com subprocess, FFmpeg e ferramentas multimídia;
* facilidade para scripts e automação;
* bom equilíbrio entre velocidade de entrega e manutenção.

### 7.2 Execução

Inicialmente via CLI.

Justificativa:

* menor complexidade;
* melhor para MVP;
* fácil integração futura com cron, n8n, fila ou painel web.

### 7.3 Renderização

FFmpeg como motor principal de composição.

Justificativa:

* forte automação;
* composição robusta;
* excelente controle de áudio, vídeo, overlay e subtitles.

### 7.4 Estado

Estado orientado a arquivos + JSON intermediário.

Justificativa:

* simples de debugar;
* visível para o desenvolvedor;
* adequado para pipelines de mídia.

---

## 8. Estratégia de Extensão Futura

A arquitetura deve permitir futura evolução para:

* múltiplas duplas de personagens;
* presets de composição;
* múltiplos TTS providers;
* fila de jobs;
* painel administrativo;
* postagem automática;
* analytics de geração;
* A/B test de formatos.

---

## 9. Regras para o Code Agent

Ao construir a arquitetura, o code agent deve seguir as seguintes diretrizes:

1. evitar acoplamento direto entre módulos de negócio e provedores externos;
2. manter I/O explícito por arquivos e contratos JSON;
3. permitir execução de cada etapa de forma isolada;
4. tratar o pipeline como cadeia de transformação de artefatos;
5. separar claramente `assets`, `temp`, `output` e `config`.

---

## 10. Resultado Esperado da Arquitetura

Ao final da implementação do MVP, a arquitetura deve permitir que um único comando execute o fluxo completo:

```bash
python -m app.main --input inputs/job_001.json
```

E produza:

* logs da execução;
* artefatos intermediários auditáveis;
* vídeo final renderizado com consistência visual e sonora.
