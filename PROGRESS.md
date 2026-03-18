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
