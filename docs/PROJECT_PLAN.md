# Plano de Construção do Projeto

## 1. Objetivo deste Plano

Este documento descreve a ordem recomendada para construir o projeto do zero, com foco em reduzir risco técnico, validar o núcleo do pipeline cedo e dar contexto suficiente para um code agent implementar o sistema de forma incremental.

A prioridade não é “fazer tudo” logo no início. A prioridade é chegar rapidamente a um MVP funcional de ponta a ponta e, a partir disso, evoluir com segurança.

---

## 2. Princípios de Construção

Durante a implementação, o projeto deve seguir os seguintes princípios:

### 2.1 Construir do núcleo para fora

Primeiro o pipeline mínimo. Depois a sofisticação.

### 2.2 Validar cada etapa isoladamente

Cada módulo deve funcionar sozinho antes de ser acoplado ao fluxo completo.

### 2.3 Manter contratos claros

Entradas e saídas em JSON e arquivos nomeados de forma previsível.

### 2.4 Favorecer artefatos intermediários

Tudo que for gerado no pipeline deve poder ser inspecionado.

### 2.5 Evitar abstração prematura

No início, a modularidade deve existir, mas sem excesso de engenharia.

---

## 3. Meta do Primeiro Marco

O primeiro marco do projeto é simples e objetivo:

> Gerar um vídeo MP4 vertical completo a partir de um único tópico, sem edição manual.

Esse marco exige:

* roteiro;
* áudio;
* talking head;
* fundo;
* legenda;
* render final.

Se isso não estiver funcionando, qualquer expansão antes disso é distração técnica.

---

## 4. Fases de Construção

## Fase 1 — Preparação do repositório

### Objetivo

Criar a base estrutural do projeto.

### Decisão de ambiente: Docker container único

O projeto roda em um **único container Docker**. Não há orquestração multi-container no MVP.

Justificativa: o pipeline é sequencial, orientado a arquivos e acionado via CLI. Não existem serviços independentes, servidor persistente, fila de mensagens ou processamento paralelo — portanto, múltiplos containers adicionariam complexidade sem benefício real. Multi-container é uma evolução pós-MVP, quando houver API web e fila de jobs.

**Estrutura Docker:**

```
Dockerfile           # imagem base python:3.11-slim + FFmpeg + dependências
docker-compose.yml   # facilita execução local com volumes e variáveis de ambiente
.env.example         # template de todas as variáveis necessárias
.dockerignore
```

**Volumes montados em runtime:**

| Host | Container | Conteúdo |
|---|---|---|
| `./inputs/` | `/app/inputs` | Jobs de entrada |
| `./output/` | `/app/output` | Vídeos e artefatos gerados |
| `./assets/` | `/app/assets` | Personagens, fundos, fontes |
| `./temp/` | `/app/temp` | Cache temporário |

**Execução:**

```bash
# build
docker build -t viral-videos .

# rodar um job
docker-compose run --rm app python -m app.main --input inputs/job_001.json

# batch
docker-compose run --rm app python -m app.main --batch inputs/batch/jobs.csv
```

Credenciais (API keys) devem ser passadas via variáveis de ambiente (`.env`), nunca embutidas na imagem.

### Entregas

* repositório inicial;
* estrutura de pastas;
* `Dockerfile` funcional (python:3.11-slim + FFmpeg);
* `docker-compose.yml` com volumes mapeados;
* `.env.example` com todas as variáveis necessárias;
* `.dockerignore`;
* configuração de logs;
* arquivo de exemplo de input.

### Tarefas

1. criar o repositório;
2. definir a árvore inicial do projeto;
3. escrever o `Dockerfile` com dependências base;
4. escrever o `docker-compose.yml`;
5. adicionar `.env.example`;
6. criar pasta de assets;
7. criar pasta de outputs e temps.

### Critério de conclusão

Projeto executa `docker-compose run --rm app python -m app.main` sem erro e possui base pronta para crescer.

---

## Fase 2 — Definição de contratos internos

### Objetivo

Padronizar a linguagem interna do pipeline.

### Entregas

* contrato de input do job;
* contrato de roteiro;
* contrato de falas;
* contrato de timeline;
* padrão de naming dos arquivos.

### Tarefas

1. definir schema de input JSON;
2. definir formato do `script.json`;
3. definir formato do `timeline.json`;
4. definir convenção de nomes por `job_id`;
5. documentar isso no projeto.

### Critério de conclusão

Qualquer etapa do pipeline pode ler e escrever arquivos de forma previsível.

---

## Fase 3 — Módulo de geração de roteiro

### Objetivo

Gerar diálogo estruturado a partir de um tópico.

### Entregas

* módulo `script_writer`;
* prompt base do gerador;
* validação estrutural da saída.

### Tarefas

1. implementar interface `ScriptGenerator`;
2. criar prompt do sistema;
3. gerar saída em JSON;
4. validar número de falas, tamanho e speakers;
5. salvar o artefato no disco.

### Critério de conclusão

Dado um tema, o projeto gera um diálogo válido, curto e utilizável.

---

## Fase 4 — Módulo de TTS

### Objetivo

Transformar cada fala em áudio.

### Entregas

* módulo `tts.py`;
* mapeamento personagem -> voz;
* geração de arquivos de áudio por fala;
* manifesto com duração.

### Tarefas

1. implementar interface `TTSProvider`;
2. integrar com provider escolhido;
3. criar função de geração por fala;
4. medir duração com utilitário adequado;
5. salvar manifesto de saída.

### Critério de conclusão

O sistema gera todos os áudios individuais corretamente e sabe quanto cada fala dura.

---

## Fase 5 — Builder de timeline + áudio master

### Objetivo

Consolidar os tempos do vídeo.

### Entregas

* módulo `timeline_builder`;
* arquivo `timeline.json`;
* arquivo `master_audio.wav`.

### Tarefas

1. calcular `start` e `end` por fala;
2. concatenar áudios na ordem correta;
3. validar a duração total;
4. salvar os artefatos.

### Critério de conclusão

Existe uma linha do tempo utilizável para composição e legendas.

---

## Fase 6 — Módulo de talking head / lip-sync

### Objetivo

Gerar o vídeo de cada personagem falando.

### Entregas

* módulo `lipsync.py`;
* adapter da engine escolhida;
* export de clipes curtos por fala.

### Tarefas

1. preparar os assets dos personagens;
2. integrar a engine de lip-sync;
3. criar wrapper para execução por fala;
4. salvar um clipe por item da timeline;
5. associar o clipe ao item correspondente.

### Critério de conclusão

Cada fala possui um vídeo correspondente do personagem falando.

---

## Fase 7 — Módulo de fundo satisfatório

### Objetivo

Selecionar e adaptar o background final.

### Entregas

* módulo `background_selector.py`;
* biblioteca inicial de vídeos;
* saída `prepared_background.mp4`.

### Tarefas

1. criar a pasta de backgrounds;
2. classificar fundos por categoria;
3. implementar seleção automática;
4. cortar, redimensionar e adaptar duração;
5. salvar vídeo pronto para composição.

### Critério de conclusão

O sistema consegue produzir um background consistente para qualquer job válido.

---

## Fase 8 — Geração de legendas

### Objetivo

Gerar legendas automaticamente.

### Entregas

* módulo `subtitles.py`;
* arquivo `.srt`;
* estratégia base de segmentação.

### Tarefas

1. decidir fonte principal da legenda;
2. implementar segmentação por blocos curtos;
3. gerar timestamps coerentes;
4. salvar arquivo `.srt`.

### Critério de conclusão

O vídeo pode ser renderizado com legendas automáticas legíveis.

---

## Fase 9 — Compositor final

### Objetivo

Montar o vídeo completo.

### Entregas

* módulo `compositor.py`;
* layout base 9:16;
* export MP4 final.

### Tarefas

1. definir layout visual padrão;
2. alternar personagem principal conforme speaker ativo;
3. posicionar personagem secundário;
4. integrar áudio master;
5. queimar legendas;
6. exportar MP4 final.

### Critério de conclusão

O sistema gera um vídeo final completo sem edição manual.

---

## Fase 10 — Orquestração end-to-end

### Objetivo

Unificar todos os módulos em uma execução única.

### Entregas

* `main.py`;
* fluxo completo do job;
* logs por etapa;
* tratamento mínimo de falhas.

### Tarefas

1. implementar o orquestrador;
2. padronizar contexto do job;
3. encadear módulos;
4. registrar logs;
5. salvar metadata da execução.

### Critério de conclusão

Um comando único executa todo o pipeline do início ao fim.

---

## Fase 11 — Batch processing

### Objetivo

Permitir geração em escala básica.

### Entregas

* leitura de CSV ou lista JSON;
* processamento sequencial de múltiplos tópicos.

### Tarefas

1. implementar modo batch;
2. gerar `job_id` por item;
3. isolar outputs por job;
4. consolidar relatório final.

### Critério de conclusão

O sistema consegue gerar vários vídeos em sequência com pouca intervenção.

---

## Fase 12 — Hardening técnico

### Objetivo

Melhorar robustez do MVP.

### Entregas

* retries controlados;
* validação de assets;
* mensagens de erro melhores;
* testes de módulos críticos.

### Tarefas

1. adicionar validações de existência de arquivos;
2. adicionar retries para API externa;
3. tratar timeout e falha parcial;
4. criar testes para módulos centrais;
5. revisar logs.

### Critério de conclusão

O projeto passa de protótipo funcional para ferramenta operacional básica.

---

## 5. Ordem de Prioridade Real

Se houver restrição de tempo, a ordem real de prioridade deve ser:

1. orquestração mínima;
2. roteiro;
3. TTS;
4. timeline;
5. lip-sync;
6. composição final;
7. fundo;
8. legenda;
9. batch;
10. refinamentos.

### Motivo

Sem geração end-to-end, qualquer camada adicional é ornamentação técnica.

---

## 6. Riscos Técnicos Principais

### Risco 1 — Lip-sync inconsistente

Pode comprometer a percepção de qualidade.

### Mitigação

Padronizar imagem-base e limitar tamanho das falas.

### Risco 2 — Render final confuso visualmente

Pode prejudicar retenção.

### Mitigação

Testar um único layout forte antes de adicionar variantes.

### Risco 3 — TTS artificial demais

Pode quebrar o humor e a imersão.

### Mitigação

Ajustar escolha de vozes e pontuação do roteiro.

### Risco 4 — Pipeline frágil

Pode falhar em produção por detalhes de arquivos e dependências.

### Mitigação

Tratar artefatos intermediários como parte do produto, não como descarte.

---

## 7. Entregas Recomendadas por Sprint

### Sprint 1

* estrutura do projeto;
* contratos internos;
* input parser;
* script writer.

### Sprint 2

* TTS;
* timeline;
* áudio master.

### Sprint 3

* lip-sync por fala;
* preparação dos assets dos personagens.

### Sprint 4

* fundo satisfatório;
* compositor final;
* export MP4.

### Sprint 5

* legendas;
* batch;
* hardening.

---

## 8. Definição de Pronto do MVP

O MVP estará pronto quando:

* aceitar um input único em JSON;
* gerar todos os artefatos intermediários;
* renderizar um vídeo vertical final;
* operar sem edição manual;
* permitir repetição com diferentes temas.

---

## 9. Instrução Final para o Code Agent

O code agent deve construir o projeto em camadas pequenas, testáveis e acopladas por contratos simples.

A regra mais importante é:

> não avançar para sofisticação visual ou operacional antes que o pipeline end-to-end esteja validado.

Esse plano deve ser usado como referência de execução, priorização e disciplina técnica durante a construção do projeto.
