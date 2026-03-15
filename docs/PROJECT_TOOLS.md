# Ferramentas Necessárias

## 1. Objetivo deste Documento

Este documento define as ferramentas, bibliotecas, engines e utilitários necessários para construir o projeto de geração automática de vídeos curtos com personagens falando sobre fundos satisfatórios.

A intenção não é listar tudo o que existe no mercado, mas sim organizar uma stack pragmática para o MVP e indicar ferramentas alternativas quando fizer sentido.

---

## 2. Stack Base Recomendada

A stack principal recomendada para o MVP é:

* **Python** para orquestração e automação;
* **LLM** para geração de roteiro;
* **TTS provider** para voz sintética por personagem;
* **Wav2Lip** ou engine equivalente para lip-sync;
* **Whisper** ou solução similar para legendas/transcrição;
* **FFmpeg** para composição e render final.

Essa combinação é suficiente para construir um pipeline automático e extensível.

---

## 3. Linguagem Principal

### Python

Python deve ser a linguagem principal do projeto.

#### Motivos

* forte ecossistema para IA e multimídia;
* integração simples com subprocessos e APIs externas;
* facilidade para organizar pipeline por módulos;
* alta produtividade no MVP;
* boa base para automação em lote.

#### Função no projeto

* orquestração do pipeline;
* integração com APIs;
* manipulação de JSON e arquivos;
* execução de FFmpeg e engines externas;
* logs e controle de fluxo.

---

## 4. Geração de Roteiro

### Ferramenta principal

Um LLM deve ser usado para gerar o roteiro estruturado do vídeo.

#### O que ele precisa fazer

* criar hook inicial;
* gerar diálogo curto entre dois personagens;
* controlar tom humorístico;
* manter falas curtas;
* respeitar duração alvo.

#### Critérios importantes

* saída estruturada em JSON;
* previsibilidade de formato;
* baixa taxa de alucinação estrutural;
* boa aderência a prompts com restrições.

#### Alternativas viáveis

* OpenAI API;
* modelos open-source servidos localmente;
* integração futura com outro provider.

#### Observação arquitetural

O LLM deve ficar atrás de uma abstração do tipo `ScriptGenerator`, para permitir troca futura sem reescrever a pipeline.

---

## 5. Síntese de Voz (TTS)

### Ferramenta principal

Um provider de text-to-speech é necessário para transformar cada fala em áudio.

#### Requisitos do provider

* API estável;
* boa naturalidade;
* baixa latência razoável;
* controle de voz por personagem;
* saída consistente em formato utilizável.

#### O que o projeto precisa do TTS

* gerar um áudio por fala;
* aceitar múltiplos personagens/vozes;
* entregar duração confiável;
* funcionar bem com frases curtas.

#### Recomendação prática

Começar com um provider consolidado e com documentação boa.

#### Alternativas futuras

* engines open-source locais;
* TTS local para redução de custo;
* múltiplos providers com fallback.

#### Observação importante

O projeto deve abstrair esse componente em algo como `TTSProvider`.

---

## 6. Lip-Sync / Talking Head

### Objetivo

Gerar movimento labial em personagens a partir de uma imagem estática e um arquivo de áudio.

### Recomendação principal para MVP

Usar uma engine de lip-sync que aceite:

* imagem de entrada;
* áudio de entrada;
* export de vídeo curto por fala.

### O que essa ferramenta precisa entregar

* sincronização labial minimamente convincente;
* automação por script;
* execução em lote;
* compatibilidade com retratos/avatares estáticos.

### Critérios de escolha

* qualidade visual suficiente;
* baixa fricção de integração;
* pipeline automatizável;
* previsibilidade de saída.

### Observação estratégica

O projeto deve tratar o lip-sync como adapter isolado. Isso evita que a arquitetura fique presa a uma única engine.

---

## 7. Fundo Satisfatório

### Necessidade real

O fundo não precisa ser gerado por IA em tempo real no MVP. Isso aumentaria complexidade e custo sem necessidade.

### Estratégia recomendada

Usar uma biblioteca local de vídeos satisfatórios pré-coletados.

#### Tipos de fundo sugeridos

* slime;
* areia sendo cortada;
* marble run;
* gameplay hipnótico;
* Minecraft parkour;
* mix de cores e fluidos.

#### Requisitos do acervo

* boa resolução;
* duração razoável;
* loopável;
* compatível com crop vertical;
* movimento contínuo;
* baixo ruído visual competitivo.

### Ferramenta necessária

Não é uma engine específica, mas sim:

* pasta estruturada de assets;
* utilitário para seleção e adaptação de duração.

---

## 8. Geração de Legendas

### Objetivo

Criar legendas com timestamps para embutir no vídeo final.

### Requisitos

* geração automática;
* segmentação legível;
* compatibilidade com `.srt`;
* possibilidade de ajuste futuro de estilo.

### Estratégias possíveis

#### Estratégia 1 — a partir da timeline textual

Mais previsível para o MVP.

#### Estratégia 2 — a partir de transcrição do áudio

Útil como fallback ou validação cruzada.

### Ferramenta ideal

Uma solução de transcrição automática ou módulo próprio que gere `.srt`.

#### Observação

Mesmo usando ASR, o projeto deve permitir geração de legendas diretamente da timeline para ganhar controle.

---

## 9. Render e Composição

### Ferramenta central

A composição final deve ser feita por um motor de renderização automatizável.

### Recomendação principal

FFmpeg como núcleo de composição.

#### Por que ele é essencial

* suporta resize, crop, overlay, concat e subtitles;
* opera bem via CLI e subprocess;
* excelente para renderização não interativa;
* ideal para pipeline automatizado.

#### O que ele deve fazer no projeto

* ajustar o fundo para 9:16;
* sobrepor talking heads;
* combinar com áudio master;
* queimar legendas;
* exportar MP4 final.

### Observação arquitetural

Toda chamada de FFmpeg deve passar por uma camada utilitária dedicada, e não ser espalhada de forma desorganizada pelo projeto.

---

## 10. Utilitários de Sistema

### FFprobe

Necessário para:

* medir duração de áudios e vídeos;
* inspecionar codecs;
* validar arquivos intermediários.

### ImageMagick ou Pillow

Pode ser útil para:

* preparar imagens de personagens;
* redimensionar assets;
* padronizar formatos;
* gerar thumbnails.

### SoX ou utilitários de áudio

Opcionalmente úteis para:

* normalização;
* conversão;
* tratamento simples de áudio.

---

## 11. Gerenciamento de Dependências

### Python packages

O projeto deve usar um gerenciador claro de dependências.

#### Opções viáveis

* `requirements.txt` para simplicidade;
* Poetry para organização maior;
* uv se a equipe quiser instalação e lock mais rápidos.

### Recomendação para MVP

Começar simples, mas com versionamento explícito.

---

## 12. Ambiente de Execução

### Sistema operacional ideal

Linux.

#### Motivos

* melhor integração com FFmpeg e ferramentas open-source;
* ambiente mais previsível para automação;
* melhor aderência a deploy headless.

### Execução local vs servidor

#### Local

Bom para desenvolvimento inicial e debug.

#### Servidor

Bom para geração em lote e automações futuras.

### GPU

Pode ser necessária ou desejável para algumas engines de lip-sync e modelos locais.

---

## 13. Logs e Observabilidade

### Ferramentas mínimas

* logger estruturado;
* arquivos de log por job;
* metadados JSON de execução.

### O que deve ser registrado

* início e fim de cada etapa;
* duração da etapa;
* arquivos produzidos;
* erros e stack traces;
* parâmetros relevantes do job.

---

## 14. Ferramentas Futuras (Não obrigatórias no MVP)

Estas ferramentas não são essenciais no início, mas devem ser previstas arquiteturalmente.

### Fila de jobs

* RabbitMQ;
* Redis Queue;
* Celery.

### Automação operacional

* cron;
* n8n;
* OpenClaw.

### Interface administrativa

* FastAPI + painel web;
* Streamlit para protótipo;
* frontend dedicado em etapa posterior.

### Publicação automatizada

* APIs das redes sociais;
* agendadores externos;
* integração com ferramentas de social media.

---

## 15. Ferramentas de Desenvolvimento

### IDE

* VS Code ou similar.

### Testes

* pytest para testes de módulos e integrações básicas.

### Qualidade de código

* ruff;
* black;
* mypy opcional;
* pre-commit.

### Versionamento

* Git com branching simples para o MVP.

---

## 16. Stack Recomendada Final para o MVP

### Essenciais

* Python
* FFmpeg / FFprobe
* LLM para roteiro
* TTS provider
* Engine de lip-sync
* Gerador de legendas
* Biblioteca local de fundos

### Fortemente recomendados

* Pillow
* logger estruturado
* pytest
* linter/formatter

### Adiáveis

* painel web
* fila distribuída
* automação de postagem
* múltiplos engines com fallback

---

## 17. Diretriz para o Code Agent

Ao construir o projeto, o code agent deve sempre distinguir entre:

1. ferramenta obrigatória para o funcionamento do pipeline;
2. ferramenta auxiliar de preparação ou observabilidade;
3. ferramenta futura que não deve contaminar o MVP.

A prioridade deve ser implementar primeiro o conjunto mínimo que permita geração end-to-end com estabilidade, antes de adicionar sofisticação desnecessária.
