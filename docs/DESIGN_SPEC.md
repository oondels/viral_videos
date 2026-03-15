# Design Specs

## 1. Visão do Produto

O projeto tem como objetivo gerar automaticamente vídeos curtos no estilo de explicação humorística entre dois personagens, com foco em plataformas de vídeo vertical como TikTok, Instagram Reels, YouTube Shorts e similares.

A proposta central é transformar um tema textual em um vídeo finalizado, sem necessidade de edição manual. O sistema deve ser capaz de:

* receber um tema ou prompt de entrada;
* gerar um roteiro de diálogo curto entre dois personagens;
* converter cada fala em áudio usando TTS;
* animar imagens estáticas dos personagens com sincronização labial;
* compor esse conteúdo sobre um vídeo de fundo satisfatório;
* gerar legendas automaticamente;
* exportar um vídeo final em formato vertical, pronto para publicação nas redes sociais.

---

## 2. Objetivo do Sistema

Construir um pipeline automatizado de geração de vídeos virais curtos, orientado por código, com foco em:

* escalabilidade;
* baixo esforço operacional;
* repetibilidade visual;
* rapidez para testar temas e formatos;
* compatibilidade com automação em lote.

O sistema não deve depender de edição manual em CapCut, Premiere ou qualquer editor tradicional.

---

## 3. Escopo do MVP

O MVP deve atender às seguintes capacidades mínimas:

### Entrada

* tema do vídeo;
* duração alvo;
* estilo de fundo (ou seleção automática);
* seleção de dupla de personagens.

### Saída

* vídeo MP4 final em 9:16;
* áudio sincronizado;
* legendas embutidas;
* composição visual consistente;
* estrutura pronta para geração em lote.

### Incluído no MVP

* 2 personagens fixos;
* 1 imagem-base por personagem;
* roteiro curto estruturado;
* TTS por fala;
* lip-sync por fala;
* fundo satisfatório único por vídeo;
* export automatizado.

### Fora do MVP

* painel web completo;
* publicação automática em redes sociais;
* múltiplas expressões faciais por personagem;
* variações avançadas de câmera;
* geração procedural do fundo por IA;
* múltiplos personagens por cena simultânea com inteligência de blocking.

---

## 4. Público-Alvo

O projeto é voltado para:

* operação de conteúdo automatizado para redes sociais;
* testes de formatos virais;
* produção em escala de vídeos curtos;
* criadores que desejam um pipeline programável e reproduzível.

---

## 5. Requisitos Funcionais

### RF-01 — Geração de roteiro

O sistema deve gerar um roteiro curto em formato estruturado de diálogo entre dois personagens.

### RF-02 — Separação por falas

Cada linha do roteiro deve ser separada por personagem, com ordem definida e texto limpo.

### RF-03 — Geração de áudio

Cada fala deve ser convertida em um arquivo de áudio independente.

### RF-04 — Linha do tempo

O sistema deve calcular a linha do tempo consolidada com início, fim, personagem e texto de cada fala.

### RF-05 — Animação facial

O sistema deve gerar clipes curtos de personagem falando a partir de imagem estática + áudio.

### RF-06 — Seleção de fundo

O sistema deve selecionar e preparar um vídeo de fundo satisfatório compatível com a duração final.

### RF-07 — Composição visual

O sistema deve compor automaticamente fundo, personagem principal, personagem secundário e demais elementos visuais.

### RF-08 — Legendas

O sistema deve gerar legendas automaticamente com timestamps.

### RF-09 — Render final

O sistema deve exportar um arquivo MP4 vertical com todos os elementos finalizados.

### RF-10 — Execução em lote

O sistema deve aceitar múltiplos tópicos para geração sequencial ou por fila.

---

## 6. Requisitos Não Funcionais

### RNF-01 — Automação total

O pipeline deve funcionar sem intervenção manual na edição.

### RNF-02 — Reprodutibilidade

A execução deve ser previsível, com estrutura de entrada e saída clara.

### RNF-03 — Modularidade

Os componentes devem ser desacoplados para facilitar troca de ferramentas.

### RNF-04 — Observabilidade

O pipeline deve registrar logs por etapa e falhas intermediárias.

### RNF-05 — Extensibilidade

O sistema deve permitir futura adição de novos personagens, novos fundos e novos modelos.

### RNF-06 — Eficiência operacional

O sistema deve priorizar ferramentas e fluxos que reduzam custo por vídeo.

---

## 7. Formato de Entrada

Exemplo de entrada mínima:

```json
{
  "topic": "explique inflação de forma engraçada",
  "duration_target_sec": 30,
  "background_style": "minecraft_parkour",
  "characters": ["char_a", "char_b"]
}
```

---

## 8. Formato de Saída Esperado

### Saída principal

* `output/final/<video_id>.mp4`

### Saídas intermediárias

* roteiro em JSON;
* falas separadas por personagem;
* áudios individuais;
* áudio master concatenado;
* timeline consolidada;
* clipes de talking head;
* legendas `.srt`;
* metadados da renderização.

---

## 9. Regras de Produto

### Duração

* vídeos preferencialmente entre 20 e 45 segundos;
* cada fala deve ser curta;
* evitar monólogos longos.

### Legibilidade

* legenda grande;
* contraste suficiente com o fundo;
* layout vertical centrado em retenção.

### Ritmo

* os primeiros 2 segundos devem ter hook claro;
* a densidade verbal deve ser alta, mas compreensível;
* o vídeo precisa parecer dinâmico mesmo com personagens estáticos animados.

### Fundo

* deve ter movimento contínuo;
* não pode competir excessivamente com a fala;
* deve ser tratável via blur leve, escurecimento ou crop inteligente.

---

## 10. Restrições Técnicas

* o projeto deve evitar dependência de edição manual;
* o pipeline deve ser executável por script/CLI;
* a composição final deve ser baseada em ferramentas automatizáveis;
* deve existir separação clara entre assets, processamento e saída.

---

## 11. Diretrizes para o Code Agent

O code agent deve interpretar este projeto como um sistema de pipeline multimodal, não como um app tradicional CRUD.

Prioridades de implementação:

1. padronizar contratos de entrada e saída;
2. garantir execução end-to-end do MVP;
3. produzir artefatos intermediários auditáveis;
4. facilitar debug por etapa;
5. manter o código modular para substituição futura de TTS, lip-sync e ASR.

---

## 12. Critérios de Sucesso do MVP

O MVP será considerado bem-sucedido quando conseguir:

* gerar um vídeo vertical completo a partir de um único tópico;
* produzir roteiro, áudio, lip-sync, fundo, legendas e render final automaticamente;
* operar sem edição manual;
* ser repetido para múltiplos tópicos com mínima alteração de configuração.
