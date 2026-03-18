# IMPLEMENTATION PLAN — PNG Alpha Channel Transparency Fix

## Type
fix

## Motivation
Os personagens (char_a e char_b) são PNGs com fundo transparente. O compositor
atual aplica `format=yuv420p` nos streams dos personagens antes do overlay, o
que descarta o canal alpha e substitui a transparência por fundo branco/preto.
O resultado visível é um retângulo sólido ao redor de cada personagem no vídeo
final.

## Scope

### In scope
- Correção do filter_complex em `compositor.py` para preservar alpha nos
  personagens até o overlay
- Ajuste do filtro `pad` (no path sem transição) para usar cor transparente
- Ajuste dos filtros `scale` nos dois paths (com e sem transição) para manter
  canal alpha
- Garantia de que a conversão `yuv420p` ocorra apenas na etapa final, após
  todos os overlays dos personagens
- Atualização do acceptance test relacionado no spec

### Out of scope
- Clips de lip-sync gerados pela engine (esses são MP4 e não têm alpha — o
  comportamento atual para clips está correto)
- Mudança no background selector
- Mudança na geração de legendas ou título

## Expected outcome
Personagens PNG compostos sobre o background sem nenhum artefato de borda
branca ou retângulo sólido. A transparência original do PNG é respeitada em
todos os frames do vídeo final.

## Key decisions

| Decision | Rationale |
|---|---|
| Usar `format=rgba` nos personagens antes do overlay | Preserva o canal alpha para que o filtro `overlay` do FFmpeg use alpha blending correto |
| Manter `format=yuv420p` apenas no último filtro antes da saída | `libx264` exige `yuv420p`, mas a conversão deve ocorrer depois de todos os composites |
| Substituir `pad` por `pad` com `color=0x00000000` (transparente) no path sem transição | O `pad` atual preenche bordas com preto sólido, o que cria artefatos quando o personagem não ocupa o box inteiro |
| Não alterar o path dos clips de lip-sync | Clips MP4 não têm canal alpha — `format=yuv420p` neles está correto e não deve ser alterado |

## Affected files / modules
- `app/modules/compositor.py` — único arquivo alterado

## References
- `docs/specs/MODULE_COMPOSITOR_SPEC.md`
- Print do output com fundo branco nos personagens

## Risk / open questions
- Clips de lip-sync gerados pelo static_lipsync_adapter podem ter fundo branco
  embutido no próprio vídeo (não é alpha do PNG — é pixel branco no MP4). Se
  isso ocorrer, o fix do compositor não resolve esse caso e será necessário um
  fix separado no adapter de lip-sync.
- Performance: `format=rgba` aumenta levemente o uso de memória no FFmpeg
  durante a composição. Não deve ser perceptível para vídeos de 30-45s.