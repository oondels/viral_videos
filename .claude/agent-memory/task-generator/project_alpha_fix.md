---
name: png_alpha_channel_fix
description: Context for the PNG alpha channel transparency fix (T-043 to T-044) on branch main
type: project
---

Tasks T-043 and T-044 fix the alpha channel bug in compositor.py where characters
rendered with a solid white/black rectangle around them.

**Why:** `format=yuv420p` was applied to character PNG streams before the overlay
filters, discarding the alpha channel. The fix replaces those with `format=rgba`
and defers the `yuv420p` conversion to the final FFmpeg output stage (`-pix_fmt yuv420p`).
The `pad` filter in the no-transition path also needed `color=0x00000000` to avoid
black borders when the character does not fill the entire box.

**How to apply:** Only `app/modules/compositor.py` is touched. Clips (MP4, no alpha)
are not affected — their `format=yuv420p` handling is intentionally left unchanged.
