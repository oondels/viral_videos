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
