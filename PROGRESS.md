# PROGRESS.md

## Purpose

This file is the persistent execution memory for completed tasks.

Every loop iteration must:

1. read this file before starting implementation;
2. use it to recover decisions, discoveries, blockers, and validations from earlier tasks;
3. append one new entry after completing exactly one task.

## Update rules

- Add one entry per completed task.
- Do not rewrite old entries unless they are factually wrong.
- Record only durable knowledge that helps the next iteration.
- Include the task id, outcome, files changed, validations run, and any follow-up note.

## Entry template

```md
## YYYY-MM-DD - T-XXX - Short title

- Outcome: what was completed.
- Files changed: path1, path2, path3.
- Validations: commands run or checks performed.
- Docs updated: DESIGN_SPEC.md, README.md, or none.
- Notes for next task: only the information the next iteration needs plus any additional context.
```

## Entries

## 2026-03-16 - T-001 - Prototipar abordagem de transição de escala no FFmpeg (spike)

- Outcome: spike concluído com sucesso. Três cenários testados: (A) zoompan, (B) scale com expressões de tempo, (B+) dois personagens com transições opostas. Decisão tomada: **usar filtro `scale` com expressões de tempo `t` e `eval=frame` no filter_complex**.
- Files changed: nenhum arquivo de produção alterado. `scripts/spike_transition.py` criado e removido antes do commit.
- Validations: `pytest tests/ -q` → todos os testes passam sem regressão.
- Docs updated: none.
- Decisão de abordagem (para uso em T-005):
  - **Abordagem escolhida:** filtro `scale` com `eval=frame` e expressões baseadas em `t` (tempo em segundos).
  - **Sintaxe FFmpeg exata:** `scale=w='EXPR':h='EXPR':eval=frame` onde EXPR usa `t` para interpolar entre tamanhos.
  - **Curva ease-in-out:** `(1 - cos(PI * min(t - t_switch, D) / D)) / 2` onde `D` = duração da transição.
  - **Ancoragem central:** overlay com `x='center_x - w/2'` e `y='center_y - h/2'` usando expressões dinâmicas.
  - **Dimensões pares:** `trunc(EXPR/2)*2` para garantir compatibilidade com yuv420p.
  - **Requisito crítico:** `eval=frame` é obrigatório no filtro `scale` — sem ele, FFmpeg rejeita variáveis de tempo `t`, `n`, `pos` com erro "not valid in init eval_mode".
  - **Sem arquivos intermediários:** single-pass filter_complex, compatível com o padrão do compositor existente.
  - **Granularidade:** 0.15s a 30fps = 4-5 frames. Mudança de ~22px/frame (W) e ~33px/frame (H) — suficiente para transição perceptível mas não abrupta. Considerar 0.3s (9 frames) se necessário.
  - **zoompan descartado:** funciona para imagem única mas não redimensiona o output — faz crop/zoom interno na resolução fixa. Não se integra ao padrão de overlay do compositor.
- Notes for next task: T-002 deve atualizar a spec com base nesta decisão. A sintaxe `scale=w='...':h='...':eval=frame` deve ser mencionada na spec como abordagem de implementação. O overlay aceita expressões em `x` e `y` para ancoragem dinâmica.

## 2026-03-16 - T-002 - Atualizar MODULE_COMPOSITOR_SPEC com comportamento de transição suave

- Outcome: spec atualizada com seção "Speaker transition behavior", novos campos de preset e render metadata, e novos critérios de aceitação.
- Files changed: docs/specs/MODULE_COMPOSITOR_SPEC.md.
- Validations: `pytest tests/ -q` → 233 passed; leitura manual da spec confirma consistência interna.
- Docs updated: docs/specs/MODULE_COMPOSITOR_SPEC.md.
- Notes for next task: T-003 deve adicionar `speaker_transition_duration_sec` e `speaker_anchor` ao preset `shorts_default.json` e validar em `asset_service.py`. Os campos estão definidos na spec como obrigatórios.

## 2026-03-16 - T-003 - Adicionar campos de transição ao preset shorts_default.json

- Outcome: campos `speaker_transition_duration_sec: 0.15` e `speaker_anchor: "center"` adicionados ao preset e à validação em `load_preset()`. Todas as fixtures de teste de integração atualizadas.
- Files changed: assets/presets/shorts_default.json, app/services/asset_service.py, tests/unit/test_asset_service.py, tests/integration/test_compositor.py, tests/integration/test_pipeline.py, tests/integration/test_batch.py, tests/integration/test_observability.py, tests/integration/test_resume.py.
- Validations: `pytest tests/ -q` → 233 passed.
- Docs updated: none.
- Notes for next task: T-004 deve refatorar `compose_video()` para posições horizontais fixas por personagem. Os novos campos de preset já estão disponíveis via `load_preset()`. Preset sem os novos campos levanta `AssetError` com mensagem descritiva.

## 2026-03-16 - T-004 - Implementar posições horizontais fixas por personagem no compositor

- Outcome: `compose_video()` refatorado para que cada personagem ocupe sempre a mesma posição horizontal fixa: char_a (primeiro alfabeticamente) sempre à esquerda (`abox.x`), char_b sempre à direita (`ibox.x`). Quando char_b é o speaker ativo, seu clip vai para o lado direito e a imagem inativa de char_a vai para o lado esquerdo — eliminando o swap de lado que ocorria antes.
- Files changed: app/modules/compositor.py, TASKS.md, PROGRESS.md.
- Validations: `pytest tests/integration/test_compositor.py -v` → 9 passed; `pytest tests/ -q` → 233 passed; `ruff check app/modules/compositor.py` → sem erros.
- Docs updated: none.
- Notes for next task: T-005 deve adicionar a animação de escala suave (ease-in-out) usando `scale` com `eval=frame` e expressões de tempo `t` conforme decisão do spike T-001. As posições horizontais fixas por personagem já estão implementadas — a animação deve interpolar apenas w/h (escala), mantendo x fixo por personagem. A troca de speaker ainda é um corte seco de escala neste ponto.

## 2026-03-16 - T-005 - Implementar animação de escala suave (ease-in-out) na troca de speaker

- Outcome: animação de escala suave implementada. Quando o speaker muda, ambos os personagens animam suavemente entre tamanhos ativo/inativo usando a abordagem do spike T-001: `scale` com `eval=frame` e expressões de tempo `t` com curva ease-in-out `(1 - cos(PI * clip(t - t_switch, 0, D) / D)) / 2`. Overlay usa `eval=frame` com posição x dinâmica para manter anchor fixo durante animação. Dimensões garantidas pares via `trunc(x/2)*2`.
- Files changed: app/modules/compositor.py, TASKS.md, PROGRESS.md.
- Validations: `pytest tests/integration/test_compositor.py -v` → 9 passed; `pytest tests/ -q` → 233 passed; `ruff check app/` → sem erros.
- Docs updated: none.
- Implementation details:
  - Duas funções helper adicionadas: `_scale_transition_expr()` (gera expressões FFmpeg de escala) e `_anchor_overlay_expr()` (gera expressões de posição com anchor).
  - `-itsoffset` adicionado aos inputs de imagem inativa para alinhar timestamps com tempo global.
  - Segmentos sem transição mantêm o path estático (sem `eval=frame`) para performance.
  - Suporte a `speaker_anchor` em 3 modos: `left`, `center`, `right`.
  - `speaker_transition_duration_sec` lido do preset e usado nas expressões.
  - Guard `trans_dur > 0` previne divisão por zero se duração for 0.
- Notes for next task: T-006 deve incluir `speaker_transition_duration_sec` no `render_metadata.json`. A lógica de transição está completa — T-006 é apenas metadata.
