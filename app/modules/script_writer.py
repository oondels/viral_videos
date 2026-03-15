"""Script writer module — generates and persists script.json and dialogue.json."""
from __future__ import annotations

import json
from typing import Any

from app.adapters.llm_adapter import (
    ScriptGenerationError,
    ScriptGenerator,
    load_system_prompt,
    load_user_prompt,
)
from app.core.contracts import ValidatedJob
from app.core.job_context import JobContext

_MIN_DIALOGUE_LINES = 6
_MAX_DIALOGUE_LINES = 12
_MAX_TITLE_HOOK_LEN = 80


def _validate_script_payload(payload: dict[str, Any], job: ValidatedJob) -> None:
    """Raise ScriptGenerationError if payload does not satisfy the spec."""
    title_hook = payload.get("title_hook", "")
    if not isinstance(title_hook, str) or not title_hook.strip():
        raise ScriptGenerationError("title_hook is missing or empty")
    if len(title_hook) >= _MAX_TITLE_HOOK_LEN:
        raise ScriptGenerationError(
            f"title_hook must be under {_MAX_TITLE_HOOK_LEN} characters, got {len(title_hook)}"
        )

    dialogue = payload.get("dialogue")
    if not isinstance(dialogue, list):
        raise ScriptGenerationError("dialogue must be a list")

    n = len(dialogue)
    if n < _MIN_DIALOGUE_LINES or n > _MAX_DIALOGUE_LINES:
        raise ScriptGenerationError(
            f"dialogue must have between {_MIN_DIALOGUE_LINES} and {_MAX_DIALOGUE_LINES} "
            f"lines, got {n}"
        )

    characters = set(job.characters)
    prev_speaker: str | None = None

    for i, line in enumerate(dialogue):
        if not isinstance(line, dict):
            raise ScriptGenerationError(f"dialogue[{i}] is not an object")

        expected_index = i + 1
        idx = line.get("index")
        if idx != expected_index:
            raise ScriptGenerationError(
                f"dialogue[{i}].index must be {expected_index}, got {idx!r}"
            )

        speaker = line.get("speaker")
        if speaker not in characters:
            raise ScriptGenerationError(
                f"dialogue[{i}].speaker {speaker!r} is not in job.characters "
                f"{sorted(characters)}"
            )
        if speaker == prev_speaker:
            raise ScriptGenerationError(
                f"dialogue[{i}].speaker {speaker!r} repeats the previous speaker "
                "(strict alternation required)"
            )
        prev_speaker = speaker

        text = line.get("text", "")
        if not isinstance(text, str) or not text.strip():
            raise ScriptGenerationError(f"dialogue[{i}].text is empty or missing")


def write_script(ctx: JobContext, generator: ScriptGenerator) -> dict[str, Any]:
    """Generate, validate, and persist script.json and dialogue.json.

    Args:
        ctx: JobContext for canonical path resolution.
        generator: ScriptGenerator implementation.

    Returns:
        The full script payload dict (matching script.json on disk).

    Raises:
        ScriptGenerationError: if the provider output is invalid.
    """
    job = ctx.job
    system_prompt = load_system_prompt()
    user_prompt = load_user_prompt(job)

    raw = generator.generate(system_prompt, user_prompt, job)

    _validate_script_payload(raw, job)

    script: dict[str, Any] = {
        "job_id": job.job_id,
        "topic": job.topic,
        "title_hook": raw["title_hook"].strip(),
        "dialogue": raw["dialogue"],
    }

    ctx.script_json().write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ctx.dialogue_json().write_text(
        json.dumps(raw["dialogue"], ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return script
