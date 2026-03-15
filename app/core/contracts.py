from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

# Known values for MVP — extended in T-013 when asset catalogue is finalised
_ALLOWED_BACKGROUND_STYLES: frozenset[str] = frozenset(
    {"auto", "minecraft_parkour", "slime", "sand", "marble_run", "misc"}
)
_ALLOWED_OUTPUT_PRESETS: frozenset[str] = frozenset({"shorts_default"})


def _generate_job_id() -> str:
    today = date.today()
    nnn = int(uuid.uuid4().hex[:3], 16) % 999 + 1
    return f"job_{today.strftime('%Y_%m_%d')}_{nnn:03d}"


class _JobInput(BaseModel):
    """Raw input payload. Only `topic` is required; all other fields are optional."""

    model_config = ConfigDict(extra="forbid")

    topic: str
    duration_target_sec: int = 30
    characters: list[str] = ["char_a", "char_b"]
    background_style: str = "auto"
    output_preset: str = "shorts_default"

    @field_validator("topic")
    @classmethod
    def topic_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("topic must not be empty or whitespace-only")
        return stripped

    @field_validator("duration_target_sec")
    @classmethod
    def duration_in_range(cls, v: int) -> int:
        if not (20 <= v <= 45):
            raise ValueError(
                f"duration_target_sec must be between 20 and 45 inclusive, got {v}"
            )
        return v

    @field_validator("characters")
    @classmethod
    def validate_characters(cls, v: list[str]) -> list[str]:
        if len(v) != 2:
            raise ValueError(
                f"characters must contain exactly 2 entries, got {len(v)}"
            )
        if len(set(v)) != 2:
            raise ValueError("characters must be unique")
        return v

    @field_validator("background_style")
    @classmethod
    def validate_background_style(cls, v: str) -> str:
        if v not in _ALLOWED_BACKGROUND_STYLES:
            raise ValueError(
                f"unknown background_style '{v}'; allowed: {sorted(_ALLOWED_BACKGROUND_STYLES)}"
            )
        return v

    @field_validator("output_preset")
    @classmethod
    def validate_output_preset(cls, v: str) -> str:
        if v not in _ALLOWED_OUTPUT_PRESETS:
            raise ValueError(
                f"unknown output_preset '{v}'; allowed: {sorted(_ALLOWED_OUTPUT_PRESETS)}"
            )
        return v


class ValidatedJob(BaseModel):
    """Fully validated job with all defaults materialized and job_id generated."""

    job_id: str
    topic: str
    duration_target_sec: int
    characters: list[str]
    background_style: str
    output_preset: str


def validate_job(payload: dict[str, Any]) -> ValidatedJob:
    """Validate a raw input dict and return a ValidatedJob with a generated job_id.

    Raises pydantic.ValidationError on any invalid or unknown field.
    The caller must not pass job_id in the payload.
    """
    job_input = _JobInput.model_validate(payload)
    return ValidatedJob(
        job_id=_generate_job_id(),
        topic=job_input.topic,
        duration_target_sec=job_input.duration_target_sec,
        characters=job_input.characters,
        background_style=job_input.background_style,
        output_preset=job_input.output_preset,
    )
