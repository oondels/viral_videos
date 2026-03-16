# IMPLEMENTATION PLAN — Animação de foco suave nos personagens durante a fala

## Type

feat

## Motivation

O compositor atual (`compositor.py`) renderiza dois personagens lado a lado — o speaker ativo em destaque (maior) e o inativo menor — mas a troca entre speakers acontece com corte seco: num frame o char_a está grande e o char_b pequeno, no frame seguinte os tamanhos se invertem abruptamente. Isso produz um efeito visual rígido e pouco profissional, especialmente em vídeos curtos de alta retenção como YouTube Shorts.

A animação de foco suave (scale transition) entre estados ativo/inativo torna a troca de speaker fluida e visualmente agradável, melhorando a percepção de qualidade do vídeo final sem alterar o pipeline existente.

## Scope

### In scope

- Posições horizontais fixas por personagem: char_a sempre à esquerda, char_b sempre à direita. Nenhum personagem troca de lado durante o vídeo.
- Animação de escala suave (interpolação) ao transicionar entre `active_speaker_box` e `inactive_speaker_box`, com duração configurável (default `0.15s`) e curva ease-in-out.
- Centro de cada personagem ancorado à sua posição horizontal fixa durante a animação.
- Novos campos no preset: `speaker_transition_duration_sec` (float, default `0.15`) e `speaker_anchor` (`left` | `center` | `right`, default `center`).
- Registro de `speaker_transition_duration_sec` em `render_metadata.json`.
- Atualização de `MODULE_COMPOSITOR_SPEC.md` com o comportamento de transição e os novos campos de preset.
- Novos acceptance tests: ausência de cortes secos de escala, ambos personagens presentes em todo frame, posição horizontal constante por personagem.

### Out of scope

- Alteração de contratos de outros módulos (TTS, timeline builder, lipsync, etc.).
- Animações de opacidade, rotação ou efeitos visuais além de escala.
- Suporte a mais de dois personagens.
- Alterações no formato do `timeline.json`.
- Mudanças na lógica de seleção de speaker (vem do timeline, sem alteração).

## Expected outcome

O vídeo final renderizado apresenta ambos os personagens em posições horizontais fixas durante todo o vídeo. Quando o speaker ativo muda, o personagem que passa a falar cresce suavemente de `inactive_speaker_box` para `active_speaker_box` em `0.15s` (configurável), enquanto o que deixa de falar encolhe de `active_speaker_box` para `inactive_speaker_box` no mesmo intervalo. A transição usa curva ease-in-out. Não há corte seco de tamanho em nenhum frame. Todos os testes existentes do compositor continuam passando.

## Key decisions

| Decision | Rationale |
|----------|-----------|
| Posições horizontais fixas por personagem (sem swap de lado) | Elimina o salto visual de personagens trocando de posição; cada personagem ocupa sempre o mesmo espaço no canvas. |
| Animação via escala (não via opacidade ou posição) | A escala é o diferenciador visual entre ativo/inativo no layout atual; animar apenas a escala mantém consistência com o design existente. |
| Implementação via `zoompan`, frames interpolados ou vídeo intermediário pré-renderizado em `temp/` | FFmpeg filter_complex com `zoompan` ou geração de frames intermediários são as formas viáveis de produzir transição suave sem dependência externa. A escolha da abordagem será definida na task de implementação. |
| Configuração via preset (`speaker_transition_duration_sec`, `speaker_anchor`) | Mantém o preset como única fonte de geometria e comportamento visual, sem hardcode no módulo. |
| Toda lógica nova em `compositor.py` e/ou `app/utils/video_utils.py` | Respeita a separação de responsabilidades atual; o compositor orquestra a composição, utils contém helpers reutilizáveis. |
| Chamadas FFmpeg exclusivamente via `run_ffmpeg()` | Contrato existente — nenhuma chamada FFmpeg direta é permitida. |
| Paths exclusivamente via `JobContext` | Contrato existente — nenhuma path montada fora de `JobContext`. |

## Affected files / modules

- `docs/specs/MODULE_COMPOSITOR_SPEC.md` — adicionar comportamento de transição suave e novos campos de preset.
- `assets/presets/shorts_default.json` — adicionar `speaker_transition_duration_sec` e `speaker_anchor`.
- `app/modules/compositor.py` — refatorar composição para posições fixas por personagem e adicionar lógica de transição de escala.
- `app/utils/video_utils.py` — helper para interpolação de escala / geração de frames de transição (se necessário, a ser criado).
- `app/services/render_service.py` — incluir `speaker_transition_duration_sec` no `render_metadata.json`.
- `app/core/job_context.py` — adicionar path para artefatos temporários de transição em `temp/` (se necessário).
- `tests/` — novos acceptance tests para validar transição suave, presença simultânea dos personagens e posição horizontal constante.

## References

- `docs/specs/MODULE_COMPOSITOR_SPEC.md` — spec atual do compositor.
- `assets/presets/shorts_default.json` — preset de referência com `active_speaker_box` e `inactive_speaker_box`.
- `app/modules/compositor.py` — implementação atual da composição com corte seco.
- `app/adapters/ffmpeg_adapter.py` — `run_ffmpeg()`, interface obrigatória para chamadas FFmpeg.
- `app/core/job_context.py` — autoridade canônica de paths.

## Risk / open questions

- A abordagem ideal de animação (filtro `zoompan` no filter_complex vs. pré-renderização de frames intermediários) precisa ser prototipada — `zoompan` pode ter limitações com overlay de múltiplos inputs, enquanto pré-renderização aumenta tempo de render e uso de disco em `temp/`.
- A curva ease-in-out pode exigir cálculo manual de keyframes se `zoompan` não suportar easing nativo — nesse caso, a interpolação precisa ser feita frame-a-frame com expressões FFmpeg ou geração de frames via Python.
- A transição de `0.15s` a 30fps corresponde a ~4-5 frames — verificar se essa granularidade é suficiente para uma animação perceptivelmente suave ou se o default deve ser ajustado.
- Garantir que a ancoragem do centro do personagem durante a animação de escala não cause deslocamento visual quando `speaker_anchor` é `center` e as boxes ativa/inativa têm posições x/y diferentes.
