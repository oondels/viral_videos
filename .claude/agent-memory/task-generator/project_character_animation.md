---
name: character_animation_feature
description: Context for the smooth character focus animation feature (T-036 to T-042) on branch feat/character-animation
type: project
---

Feature branch `feat/character-animation` adds smooth scale-based transition animation
when the active speaker changes in the compositor, replacing the current hard-cut behavior.

Tasks T-036 to T-042 cover this work. Last completed task before this feature: T-035.

**Why:** The current compositor in `app/modules/compositor.py` uses a hard cut (abrupt
scale swap) when the speaker changes. The new behavior animates scale smoothly over
`speaker_transition_duration_sec` (default 0.15s, ~4-5 frames at 30fps) with ease-in-out.

**How to apply:** When generating tasks for follow-on work to this feature, start from
T-043. The spike in T-036 must be completed and its FFmpeg approach decision documented
in PROGRESS.md before any implementation task (T-039, T-040) can be reliably scoped.

Key decisions locked in IMPLEMENTATION_PLAN.md:
- char_a always on the left, char_b always on the right (fixed horizontal positions)
- Animation via scale only (no opacity or position animation)
- New preset fields: `speaker_transition_duration_sec` (float) and `speaker_anchor` (left|center|right)
- All FFmpeg calls via `run_ffmpeg()`, all paths via `JobContext`
