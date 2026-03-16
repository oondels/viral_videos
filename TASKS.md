---
spec_type: TASKS
status: ready
loop_mode: ralph
last_updated: 2026-03-16T00:00:00Z
inputs:
* docs/DESIGN_SPEC.md
* IMPLEMENTATION_PLAN.md
* docs/specs/README.md
* PROGRESS.md
---

# TASK PLAN

> Tasks here correspond to the current `IMPLEMENTATION_PLAN.md`.
> When a new plan begins, this file is replaced entirely.
> Completed task results are preserved in `PROGRESS.md`.

## LOOP_RULES

* On each iteration, select the first task with `status: false` whose `depends_on` tasks are all `true`.
* Read `docs/DESIGN_SPEC.md` first on every iteration.
* Read `IMPLEMENTATION_PLAN.md` to understand the purpose and scope of the current work.
* Read `PROGRESS.md` after `docs/DESIGN_SPEC.md` to recover the knowledge produced by previous completed tasks.
* Then read only the files listed under `read_first` for the selected task.
* Complete exactly one task per iteration.
* Run every listed validation check before marking a task complete.
* If any stop condition triggers, stop and update the docs instead of guessing.
* If the task changes business rules, feature scope, contracts, or architecture, update `docs/DESIGN_SPEC.md`.
* If the task changes setup, commands, or operator-facing usage, update `README.md`.
* After a task passes validation, append its outcome to `PROGRESS.md`.
* After a task passes validation, set its `status` to `true`, create one commit for that task, persist the changes, and stop the iteration.

## REVIEW_GATE

* `docs/DESIGN_SPEC.md` and the referenced spec files are internally consistent.
* `PROGRESS.md` reflects the durable knowledge from all completed tasks.
* Task dependencies are acyclic.
* Each task has one clear goal and one bounded scope.
* The next executable task can be selected deterministically.

## TASKS

* id: T-001
  title: Prototipar abordagem de transição de escala no FFmpeg (spike)
  status: true
  type: chore
  depends_on: []
  read_first:
  * IMPLEMENTATION_PLAN.md
  * app/modules/compositor.py
  * app/adapters/ffmpeg_adapter.py
  * assets/presets/shorts_default.json
  goal: >
    Determinar a abordagem viável de animação de escala suave no FFmpeg antes
    de comprometer qualquer mudança de produção. O spike deve validar se
    `zoompan` suporta interpolação ease-in-out com múltiplos overlays
    simultâneos ou se a abordagem correta é geração de frames intermediários
    via expressões `scale` com variável de tempo `t`. O resultado é uma decisão
    documentada em `PROGRESS.md`, não código de produção.
  scope: >
    Nenhum arquivo de produção alterado. O spike pode criar um script
    temporário em `scripts/spike_transition.py` (não commitado em produção)
    para testar comandos FFmpeg isoladamente com os assets existentes
    (`assets/characters/char_a/base.png`, `assets/characters/char_b/base.png`).
    O resultado do spike deve responder: (1) `zoompan` funciona com overlay de
    dois inputs simultâneos? (2) `scale=w='lerp(w1,w2,t/dur)':...` é suportado
    com expressões de tempo relativo? (3) Qual abordagem produz transição
    perceptivelmente suave a 30fps em 4-5 frames (0.15s)?
  instructions: |
    1. Criar `scripts/spike_transition.py` com dois cenários de teste FFmpeg
       mínimos usando os assets de personagem existentes:
       - Cenário A: usar filtro `zoompan` para animar escala de um único input
         de imagem entre dois tamanhos em 0.15s, verificar se a expressão
         aceita variáveis de tempo `t` e curva ease-in-out.
       - Cenário B: usar `scale=w='if(lt(t,0.15),lerp(500,400,t/0.15),400)'`
         (ou expressão equivalente) diretamente no filtro `scale` dentro do
         filter_complex, verificar se FFmpeg aceita expressões de tempo
         relativo ao clip no contexto de overlay.
    2. Executar cada cenário via `run_ffmpeg()` do adapter (nunca chamada
       direta de subprocess) e registrar se o comando foi aceito sem erro.
    3. Inspecionar os 4-5 frames do intervalo de transição com `ffprobe` ou
       extração de frames para confirmar se a variação de tamanho é perceptível
       e suave.
    4. Documentar a decisão em `PROGRESS.md` com: abordagem escolhida,
       sintaxe FFmpeg exata que funciona, limitações encontradas, e se o
       default de 0.15s (4-5 frames a 30fps) é visualmente suficiente.
    5. Remover `scripts/spike_transition.py` antes do commit.
  acceptance_criteria:
  * PROGRESS.md contém entrada T-001 com a decisão de abordagem documentada.
  * A decisão especifica a sintaxe FFmpeg exata (filtro e expressão) a ser usada em T-003.
  * O spike confirma se 4-5 frames (0.15s a 30fps) produzem transição perceptível.
  * Nenhum arquivo de produção foi alterado.
  * `scripts/spike_transition.py` não está presente no commit.
  validation_checks:
  * `pytest tests/ -q` → mesmo número de testes passando que antes (nenhuma regressão).
  * `git diff --name-only` não inclui arquivos de `app/` ou `assets/` ou `docs/`.
  stop_conditions:
  * Se nenhuma abordagem FFmpeg produzir transição suave sem erros de sintaxe,
    parar e documentar a limitação em PROGRESS.md antes de prosseguir.
  * Se `zoompan` e expressões de `scale` com tempo ambos falharem, documentar
    a necessidade de geração de frames intermediários via Python (Pillow) antes
    de iniciar T-002.
  rollback_notes:
  * Não há código de produção para reverter — o spike não altera arquivos de produção.

* id: T-002
  title: Atualizar MODULE_COMPOSITOR_SPEC com comportamento de transição suave
  status: true
  type: docs
  depends_on: [T-001]
  read_first:
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  * IMPLEMENTATION_PLAN.md
  * PROGRESS.md
  goal: >
    Atualizar `MODULE_COMPOSITOR_SPEC.md` para documentar o comportamento de
    transição suave de escala entre speakers, os novos campos de preset
    (`speaker_transition_duration_sec`, `speaker_anchor`), a semântica de
    posições horizontais fixas por personagem, e os novos critérios de
    aceitação. A spec deve ser consistente com a decisão de abordagem
    documentada em T-001.
  scope: >
    Apenas `docs/specs/MODULE_COMPOSITOR_SPEC.md`. Nenhum código alterado.
  instructions: |
    1. Adicionar seção "Speaker transition behavior" à spec com:
       - Descrição das posições horizontais fixas: char_a sempre à esquerda,
         char_b sempre à direita, sem swap de lado em nenhum frame.
       - Descrição da animação de escala suave: quando o speaker ativo muda,
         o personagem que passa a falar cresce de `inactive_speaker_box` para
         `active_speaker_box` em `speaker_transition_duration_sec` segundos;
         o personagem que deixa de falar encolhe no mesmo intervalo.
       - Curva ease-in-out obrigatória.
       - Ausência de corte seco de escala em qualquer frame.
       - Ambos os personagens presentes em todo frame do vídeo.
       - Posição horizontal (x) de cada personagem constante durante toda a
         animação (ancoragem via `speaker_anchor`).
    2. Adicionar os novos campos obrigatórios de preset na seção
       "Required preset fields":
       - `speaker_transition_duration_sec` (float, seconds)
       - `speaker_anchor` (string: `left` | `center` | `right`)
    3. Adicionar `speaker_transition_duration_sec` na seção
       "Render metadata contract" como campo obrigatório do
       `render_metadata.json`.
    4. Adicionar critérios de aceitação na seção "Acceptance tests":
       - Nenhum corte seco de escala entre frames consecutivos de troca de speaker.
       - Ambos os personagens presentes em todo frame do vídeo.
       - A posição horizontal (x) de cada personagem permanece constante
         durante toda a duração do vídeo.
  acceptance_criteria:
  * `docs/specs/MODULE_COMPOSITOR_SPEC.md` contém seção "Speaker transition behavior".
  * A spec lista `speaker_transition_duration_sec` e `speaker_anchor` como campos obrigatórios do preset.
  * A spec lista `speaker_transition_duration_sec` como campo obrigatório do `render_metadata.json`.
  * A spec lista os três novos critérios de aceitação de transição.
  * A spec não contradiz nenhum comportamento existente documentado.
  validation_checks:
  * Leitura manual da spec para confirmar consistência interna.
  * `pytest tests/ -q` → nenhuma regressão (testes não leem a spec diretamente).
  stop_conditions:
  * Se a decisão de T-001 revelar comportamento incompatível com o que o
    IMPLEMENTATION_PLAN descreve, parar e resolver a contradição antes de
    atualizar a spec.
  rollback_notes:
  * Reverter `docs/specs/MODULE_COMPOSITOR_SPEC.md` ao estado anterior via `git checkout`.

* id: T-003
  title: Adicionar campos de transição ao preset shorts_default.json
  status: true
  type: chore
  depends_on: [T-002]
  read_first:
  * assets/presets/shorts_default.json
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  * app/services/asset_service.py
  goal: >
    Adicionar os campos `speaker_transition_duration_sec` e `speaker_anchor`
    ao preset `assets/presets/shorts_default.json` com os valores default
    definidos no plano (`0.15` e `"center"` respectivamente), e garantir que
    `asset_service.load_preset()` valida a presença dos novos campos.
  scope: >
    `assets/presets/shorts_default.json` e `app/services/asset_service.py`.
    Nenhum outro arquivo alterado.
  instructions: |
    1. Abrir `assets/presets/shorts_default.json` e adicionar após o campo
       `subtitle_style`:
       - `"speaker_transition_duration_sec": 0.15`
       - `"speaker_anchor": "center"`
    2. Abrir `app/services/asset_service.py` e localizar a lista de campos
       obrigatórios validados por `load_preset()`. Adicionar
       `"speaker_transition_duration_sec"` e `"speaker_anchor"` a essa lista.
    3. Confirmar que `load_preset("shorts_default")` retorna o preset sem erro
       e que os dois novos campos estão presentes no dict retornado.
  acceptance_criteria:
  * `assets/presets/shorts_default.json` contém `speaker_transition_duration_sec: 0.15`.
  * `assets/presets/shorts_default.json` contém `speaker_anchor: "center"`.
  * `app/services/asset_service.py` valida os dois novos campos em `load_preset()`.
  * `load_preset("shorts_default")` não levanta exceção.
  * Um preset sem os novos campos levanta erro descritivo em `load_preset()`.
  validation_checks:
  * `pytest tests/unit/test_asset_service.py -v` → todos os testes passam.
  * `pytest tests/ -q` → nenhuma regressão.
  stop_conditions:
  * Se `load_preset()` não tiver uma lista explícita de campos obrigatórios
    (i.e., validação implícita ou ausente), parar e implementar a validação
    explícita antes de adicionar os novos campos.
  rollback_notes:
  * Reverter `assets/presets/shorts_default.json` e `app/services/asset_service.py`
    via `git checkout` se os testes existentes quebrarem.

* id: T-004
  title: Implementar posições horizontais fixas por personagem no compositor
  status: false
  type: code
  depends_on: [T-003]
  read_first:
  * app/modules/compositor.py
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  * assets/presets/shorts_default.json
  * app/core/job_context.py
  goal: >
    Refatorar `compose_video()` em `compositor.py` para que cada personagem
    ocupe sempre a mesma posição horizontal fixa durante todo o vídeo —
    char_a à esquerda, char_b à direita — eliminando o comportamento atual
    onde o personagem ativo aparece sempre na `active_speaker_box` e o inativo
    sempre na `inactive_speaker_box` independentemente de qual personagem é
    qual. Esta task introduz apenas as posições fixas (sem animação de
    transição), que será adicionada em T-005.
  scope: >
    Apenas `app/modules/compositor.py`. Nenhum outro arquivo alterado.
    A lógica de composição deve continuar usando `run_ffmpeg()` e
    `JobContext` para todos os paths.
  instructions: |
    1. No início de `compose_video()`, após carregar o preset, determinar qual
       personagem é char_a e qual é char_b a partir da lista `all_speakers`
       (ordenada alfabeticamente — char_a é sempre o primeiro).
    2. Definir um mapeamento fixo de personagem para posição:
       - char_a → posição esquerda: usar `active_speaker_box` quando ativo,
         `inactive_speaker_box` quando inativo, mas com x fixo em
         `active_speaker_box.x` (lado esquerdo do canvas).
       - char_b → posição direita: usar `active_speaker_box` quando ativo,
         `inactive_speaker_box` quando inativo, mas com x fixo em
         `inactive_speaker_box.x` (lado direito do canvas).
       Nota: por ora, sem animação — a troca ainda é um corte seco de escala,
       mas cada personagem permanece no seu lado. A animação suave vem em T-005.
    3. Refatorar o loop de filter_complex para que cada item de timeline
       sobreponha os dois personagens simultaneamente (ativo e inativo), cada
       um na sua posição x fixa, com o tamanho determinado pelo seu estado
       (ativo ou inativo) no item atual.
    4. Garantir que a imagem do personagem inativo continue sendo carregada de
       `load_character(inactive_id)["base_png"]` e que o clip ativo continue
       vindo de `item["clip_file"]`.
    5. Manter todos os contratos existentes: `run_ffmpeg()`, `JobContext`,
       `CompositorError`, `write_render_metadata()`.
  acceptance_criteria:
  * `pytest tests/integration/test_compositor.py -v` → todos os testes passam.
  * `pytest tests/ -q` → nenhuma regressão.
  * O filter_complex gerado coloca char_a sempre à esquerda e char_b sempre à direita em cada item de timeline.
  * Nenhuma chamada FFmpeg direta (subprocess) fora de `run_ffmpeg()`.
  * Nenhum path montado fora de `JobContext`.
  validation_checks:
  * `pytest tests/integration/test_compositor.py -v` → todos passam.
  * `pytest tests/ -q` → nenhuma regressão.
  * `ruff check app/modules/compositor.py` → sem erros.
  stop_conditions:
  * Se o preset `shorts_default.json` não tiver posições x distintas para
    `active_speaker_box` e `inactive_speaker_box` que separem claramente os
    lados esquerdo e direito do canvas, parar e revisar o preset antes de
    prosseguir.
  rollback_notes:
  * Reverter `app/modules/compositor.py` via `git checkout` se os testes de
    integração do compositor quebrarem.

* id: T-005
  title: Implementar animação de escala suave (ease-in-out) na troca de speaker
  status: false
  type: code
  depends_on: [T-004]
  read_first:
  * app/modules/compositor.py
  * PROGRESS.md
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  goal: >
    Adicionar a lógica de transição de escala suave em `compose_video()` para
    que, quando o speaker ativo muda, ambos os personagens animem suavemente
    entre os tamanhos ativo/inativo usando a abordagem determinada no spike
    T-001 (documentada em `PROGRESS.md`). A duração e a âncora vêm dos novos
    campos `speaker_transition_duration_sec` e `speaker_anchor` do preset.
    Nenhum corte seco de escala deve ocorrer em nenhum frame.
  scope: >
    `app/modules/compositor.py` e, se necessário, `app/utils/video_utils.py`
    para helpers de interpolação. Nenhum outro módulo alterado. Toda lógica
    FFmpeg via `run_ffmpeg()`. Todos os paths via `JobContext`.
  instructions: |
    1. Ler `PROGRESS.md` para recuperar a decisão de abordagem do spike T-001
       (sintaxe FFmpeg exata e limitações documentadas).
    2. Calcular os instantes de troca de speaker a partir do `timeline`: um
       instante de troca ocorre quando `timeline[i]["speaker"] !=
       timeline[i-1]["speaker"]` — registrar o `start_sec` de cada item como
       início da janela de transição.
    3. Para cada personagem em cada janela de transição, construir a expressão
       FFmpeg de escala animada conforme a abordagem escolhida no spike:
       - Usar `speaker_transition_duration_sec` do preset como duração `D`.
       - Usar curva ease-in-out: `f(t) = t < D ? (1 - cos(PI*t/D)) / 2 : 1`
         ou equivalente suportado pelo FFmpeg.
       - Interpolar `w` e `h` entre tamanho inativo e tamanho ativo (ou
         vice-versa) durante `[t_switch, t_switch + D]`.
       - Fora da janela de transição, usar tamanho fixo (ativo ou inativo).
    4. Aplicar `speaker_anchor` do preset para calcular a posição x de overlay
       de cada personagem de modo que o centro (ou borda configurada) do
       personagem permaneça na posição horizontal fixa durante a animação.
    5. Integrar as expressões no filter_complex preservando todos os outputs
       rotulados existentes (`[bg_titled]`, `[final_v]`, etc.).
    6. Se a abordagem exigir artefatos temporários em `temp/`, usar paths via
       `JobContext` (adicionar `ctx.temp_dir()` se ainda não existir).
  acceptance_criteria:
  * `pytest tests/integration/test_compositor.py -v` → todos os testes passam.
  * `pytest tests/ -q` → nenhuma regressão.
  * O filter_complex não usa tamanhos fixos hardcoded nos frames de troca de speaker — as expressões de escala referenciam o tempo `t`.
  * `speaker_transition_duration_sec` do preset é lido e usado na construção das expressões de animação.
  * `speaker_anchor` do preset é lido e usado no cálculo do x de overlay.
  * `ruff check app/modules/compositor.py` → sem erros.
  validation_checks:
  * `pytest tests/integration/test_compositor.py -v` → todos passam.
  * `pytest tests/ -q` → nenhuma regressão.
  * `ruff check app/` → sem erros.
  stop_conditions:
  * Se a abordagem do spike T-001 não for viável com os assets disponíveis
    (chars de teste são imagens simples), parar e criar um caso de teste
    mínimo antes de continuar.
  * Se as expressões FFmpeg de tempo relativo não funcionarem no contexto de
    overlay com múltiplos inputs, parar e documentar a limitação antes de
    escolher abordagem alternativa.
  rollback_notes:
  * Reverter `app/modules/compositor.py` e `app/utils/video_utils.py` via
    `git checkout` se os testes de integração quebrarem.

* id: T-006
  title: Incluir speaker_transition_duration_sec no render_metadata.json
  status: false
  type: code
  depends_on: [T-005]
  read_first:
  * app/services/render_service.py
  * app/modules/compositor.py
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  goal: >
    Atualizar `write_render_metadata()` em `render_service.py` e sua chamada
    em `compositor.py` para incluir o campo `speaker_transition_duration_sec`
    no `render_metadata.json`, conforme definido na spec atualizada em T-002.
  scope: >
    `app/services/render_service.py` e `app/modules/compositor.py`.
    Nenhum outro arquivo alterado.
  instructions: |
    1. Atualizar a assinatura de `write_render_metadata()` para aceitar
       `speaker_transition_duration_sec: float` como parâmetro adicional.
    2. Adicionar `"speaker_transition_duration_sec"` ao dict `metadata` gerado
       pela função, com o valor do parâmetro recebido.
    3. Adicionar `"speaker_transition_duration_sec"` ao set
       `_REQUIRED_METADATA_FIELDS` para que a validação existente (se houver)
       cubra o novo campo.
    4. Em `compositor.py`, atualizar a chamada a `write_render_metadata()` para
       passar o valor lido do preset:
       `preset["speaker_transition_duration_sec"]`.
  acceptance_criteria:
  * `render_metadata.json` gerado contém o campo `speaker_transition_duration_sec` com o valor do preset.
  * `write_render_metadata()` aceita e persiste o novo parâmetro.
  * `pytest tests/integration/test_compositor.py -v` → todos os testes passam (incluindo validação de render_metadata).
  * `pytest tests/ -q` → nenhuma regressão.
  validation_checks:
  * `pytest tests/integration/test_compositor.py -v` → todos passam.
  * `pytest tests/ -q` → nenhuma regressão.
  * `ruff check app/services/render_service.py app/modules/compositor.py` → sem erros.
  stop_conditions:
  * Se `write_render_metadata()` for chamada de outros locais além de
    `compositor.py`, atualizar todas as chamadas antes de marcar a task
    como completa.
  rollback_notes:
  * Reverter `app/services/render_service.py` e `app/modules/compositor.py`
    via `git checkout` se os testes quebrarem.

* id: T-007
  title: Adicionar acceptance tests de transição suave no compositor
  status: false
  type: code
  depends_on: [T-006]
  read_first:
  * tests/integration/test_compositor.py
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  * app/modules/compositor.py
  goal: >
    Escrever novos testes de aceitação em `tests/integration/test_compositor.py`
    que validem os três critérios de transição definidos na spec atualizada:
    (1) ausência de cortes secos de escala, (2) presença simultânea de ambos
    os personagens em todo frame, (3) posição horizontal constante por
    personagem. Os testes devem usar os assets de personagem e preset
    existentes e executar o compositor end-to-end.
  scope: >
    Apenas `tests/integration/test_compositor.py`. Nenhum código de produção
    alterado. Os testes podem usar `ffprobe` via `ffprobe_utils` para
    inspecionar o output se necessário.
  instructions: |
    1. Adicionar teste `test_no_hard_cut_on_speaker_change`: gerar um vídeo
       com pelo menos dois itens de timeline com speakers diferentes; extrair
       frames do intervalo de troca com `ffprobe` ou `ffmpeg -vframes`; verificar
       que nenhum par de frames consecutivos ao redor do instante de troca tem
       diferença de tamanho de personagem maior que o esperado de um corte seco.
       (Abordagem alternativa: verificar que o filter_complex gerado contém
       expressões de tempo `t` nas chamadas de `scale` dos personagens, o que
       é verificável sem render completo.)
    2. Adicionar teste `test_both_characters_present_every_segment`: verificar
       que o filter_complex gerado para um vídeo com dois speakers contém
       exactamente dois inputs de imagem de personagem por item de timeline
       (ativo e inativo), confirmando presença simultânea.
    3. Adicionar teste `test_character_x_position_is_fixed`: para um vídeo com
       dois itens de timeline com speakers alternados, verificar que a posição
       x de overlay de char_a é a mesma no item 1 e no item 2, e que a posição
       x de overlay de char_b é a mesma em ambos os itens.
    4. Adicionar teste `test_render_metadata_includes_transition_duration`:
       verificar que `render_metadata.json` gerado contém
       `speaker_transition_duration_sec` com o valor correto do preset.
  acceptance_criteria:
  * Os quatro novos testes existem em `tests/integration/test_compositor.py`.
  * `pytest tests/integration/test_compositor.py -v` → todos os testes (novos e existentes) passam.
  * `pytest tests/ -q` → nenhuma regressão no total de testes.
  * Os testes falham se `compositor.py` for revertido para a implementação sem transição (corte seco).
  validation_checks:
  * `pytest tests/integration/test_compositor.py -v` → todos passam.
  * `pytest tests/ -q` → nenhuma regressão.
  * `ruff check tests/integration/test_compositor.py` → sem erros.
  stop_conditions:
  * Se não for possível verificar a ausência de corte seco sem render completo
    (por limitação dos assets de teste), usar verificação do filter_complex
    gerado como proxy aceitável e documentar essa decisão.
  rollback_notes:
  * Remover apenas os novos testes adicionados se causarem falhas inesperadas
    nos testes existentes; nunca alterar os testes existentes.
