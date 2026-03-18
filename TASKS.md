---
spec_type: TASKS
status: ready
loop_mode: ralph
last_updated: 2026-03-17T00:00:00Z
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

* id: T-043
  title: Preservar canal alpha nos personagens PNG no filter_complex do compositor
  status: true
  type: code
  depends_on: []
  read_first:
  * IMPLEMENTATION_PLAN.md
  * app/modules/compositor.py
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  goal: >
    Corrigir o filter_complex em compositor.py para que os PNGs dos personagens
    mantenham o canal alpha durante todo o pipeline de overlay, convertendo para
    yuv420p apenas na etapa final (após todos os composites), eliminando o
    artefato de retângulo sólido branco/preto ao redor dos personagens.
  scope: >
    app/modules/compositor.py — único arquivo modificado.
  instructions: |
    1. Abra app/modules/compositor.py e localize os quatro pontos onde
       `format=yuv420p` é aplicado nos streams dos personagens (dois no
       path com transição, dois no path sem transição).

    2. No path SEM transição (bloco `else`):
       a. No filtro do clip ativo (linha com `scale`, `force_original_aspect_ratio`,
          `pad`, `setsar`, `format=yuv420p`):
          - Remova `format=yuv420p` desse filtro.
          - Substitua `pad=...` por `pad={abox['w']}:{abox['h']}:(ow-iw)/2:(oh-ih)/2:color=0x00000000`
            (cor transparente em vez do padrão preto).
          - Adicione `format=rgba` após `setsar=1` para garantir que o stream
            entre no overlay com canal alpha ativo.
       b. No filtro da imagem inativa (linha com `scale`, `setsar`, `format=yuv420p`):
          - Remova `format=yuv420p`.
          - Adicione `format=rgba` após `setsar=1`.

    3. No path COM transição (bloco `if is_transition and dims_differ`):
       a. No filtro de escala do clip ativo (scale com eval=frame):
          - Substitua `format=yuv420p` por `format=rgba`.
       b. No filtro de escala da imagem inativa (scale com eval=frame):
          - Substitua `format=yuv420p` por `format=rgba`.

    4. Não altere nenhum outro filtro. O `format=yuv420p` do comando FFmpeg
       final (`-pix_fmt yuv420p`) e o filtro de subtítulos permanecem
       intocados — eles operam após todos os overlays.

    5. Confirme que nenhuma outra referência a `format=yuv420p` foi introduzida
       nos streams dos personagens.
  acceptance_criteria:
  * O filtro de cada personagem (clip ativo e imagem inativa) usa `format=rgba` em vez de `format=yuv420p` no path sem transição.
  * O filtro de cada personagem usa `format=rgba` em vez de `format=yuv420p` no path com transição.
  * O `pad` no path sem transição usa `color=0x00000000` (transparente).
  * O argumento `-pix_fmt yuv420p` no comando FFmpeg final permanece inalterado.
  * Todos os testes de integração em tests/integration/test_compositor.py passam.
  validation_checks:
  * docker compose run --rm app pytest tests/integration/test_compositor.py -q
  * docker compose run --rm app ruff check app/modules/compositor.py
  stop_conditions:
  * Se o FFmpeg retornar erro relacionado a pixel format incompatível entre o stream rgba e o filtro de subtítulos, parar e investigar se é necessário inserir um `format=rgba` explícito antes do filtro subtitles.
  * Se qualquer teste existente quebrar por razão não relacionada ao alpha channel, parar e reportar antes de continuar.
  rollback_notes:
  * Reverter app/modules/compositor.py ao estado anterior via `git checkout app/modules/compositor.py`.

* id: T-044
  title: Adicionar acceptance test para verificar ausência de format=yuv420p nos streams dos personagens
  status: true
  type: code
  depends_on: [T-043]
  read_first:
  * tests/integration/test_compositor.py
  * app/modules/compositor.py
  * docs/specs/MODULE_COMPOSITOR_SPEC.md
  goal: >
    Adicionar um teste de regressão em test_compositor.py que verifica que o
    filter_complex gerado pelo compositor não contém `format=yuv420p` nos
    streams intermediários dos personagens, prevenindo regressão do fix do
    canal alpha.
  scope: >
    tests/integration/test_compositor.py — único arquivo modificado.
  instructions: |
    1. Abra tests/integration/test_compositor.py e localize a classe
       `TestComposeVideo`.

    2. Adicione uma nova classe `TestFilterComplexAlpha` com um teste
       `test_character_streams_use_rgba_not_yuv420p`.

    3. O teste deve:
       a. Usar `monkeypatch.chdir(tmp_path)`, criar um ctx e chamar
          `_setup_all_artifacts`.
       b. Em vez de chamar `compose_video(ctx)` e validar o vídeo final,
          fazer monkey-patch em `app.modules.compositor.run_ffmpeg` para
          capturar o argumento `-filter_complex` sem executar o FFmpeg.
       c. Extrair o valor do filter_complex capturado.
       d. Dividir o filter_complex em filtros individuais (split por `;`).
       e. Identificar os filtros que processam os personagens: aqueles que
          contêm `scale` e terminam com um label do tipo `[c0]`, `[c1]`,
          `[img0]`, `[img1]`, etc.
       f. Afirmar que nenhum desses filtros contém a substring `format=yuv420p`.
       g. Afirmar que pelo menos um desses filtros contém `format=rgba`
          (confirma que a conversão de formato está presente, só que correta).

    4. Certifique-se de que o novo teste é independente e não depende da
       existência do FFmpeg instalado (o monkey-patch evita a execução real).
  acceptance_criteria:
  * O novo teste `test_character_streams_use_rgba_not_yuv420p` existe em TestFilterComplexAlpha.
  * O teste passa sem executar o FFmpeg real (usa monkey-patch em run_ffmpeg).
  * O teste falha se `format=yuv420p` for reintroduzido em qualquer filtro de personagem.
  * Todos os testes existentes continuam passando.
  validation_checks:
  * docker compose run --rm app pytest tests/integration/test_compositor.py -q
  * docker compose run --rm app ruff check tests/integration/test_compositor.py
  stop_conditions:
  * Se o monkey-patch em run_ffmpeg não for suficiente para interceptar os argumentos (por exemplo, por camadas de abstração adicionais), parar e verificar a assinatura de run_ffmpeg antes de continuar.
  rollback_notes:
  * Remover a classe `TestFilterComplexAlpha` adicionada ao arquivo de teste via `git checkout tests/integration/test_compositor.py`.
