# PROGRESS

## T-043 — Preservar canal alpha nos personagens PNG no filter_complex do compositor
**Status:** complete
**Date:** 2026-03-17

### Changes
- `app/modules/compositor.py`: Replaced `format=yuv420p` with `format=rgba` in all 4 character stream filters (2 in transition path, 2 in static path).
- Static path `pad` filter now uses `color=0x00000000` (transparent) instead of default black.
- Final `-pix_fmt yuv420p` in the FFmpeg output command remains unchanged.
- `docker-compose.yml`: Added `./app:/app/app` and `./tests:/app/tests` volume mounts for development.

### Decisions
- The `format=rgba` ensures PNG alpha channel is preserved through the overlay pipeline.
- Conversion to `yuv420p` happens only at the final output stage via `-pix_fmt yuv420p`.

### Validation
- 9/9 integration tests passed.
- ruff check passed.

## T-044 — Adicionar acceptance test para verificar ausência de format=yuv420p nos streams dos personagens
**Status:** complete
**Date:** 2026-03-17

### Changes
- `tests/integration/test_compositor.py`: Added `TestFilterComplexAlpha` class with `test_character_streams_use_rgba_not_yuv420p` test.
- Test monkey-patches `run_ffmpeg` to capture the filter_complex without executing FFmpeg.
- Validates that character stream filters use `format=rgba` and do not contain `format=yuv420p`.

### Validation
- 10/10 integration tests passed.
- No new ruff errors introduced (3 pre-existing errors in the file remain).
