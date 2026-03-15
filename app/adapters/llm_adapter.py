"""LLM provider adapter for script generation.

Defines the ScriptGenerator interface and prompt loading utilities.
Concrete implementations must subclass ScriptGenerator and override generate.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.contracts import ValidatedJob

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class ScriptGenerationError(Exception):
    """Raised when the provider fails to return a valid script payload."""


def load_system_prompt() -> str:
    """Load the script system prompt from disk."""
    return (_PROMPTS_DIR / "script_system_prompt.md").read_text(encoding="utf-8")


def load_user_prompt(job: ValidatedJob) -> str:
    """Render the user prompt template for the given job."""
    template = (_PROMPTS_DIR / "script_user_prompt_template.md").read_text(
        encoding="utf-8"
    )
    return template.format(
        topic=job.topic,
        duration_target_sec=job.duration_target_sec,
        char_0=job.characters[0],
        char_1=job.characters[1],
    )


class ScriptGenerator(ABC):
    """Provider-agnostic interface for LLM-based script generation.

    Subclasses must implement `generate`, which accepts prompt strings and
    returns a raw dict matching the script output contract:

        {
          "title_hook": str,
          "dialogue": [{"index": int, "speaker": str, "text": str}, ...]
        }

    Raise ScriptGenerationError on any provider or parsing failure.
    """

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        job: ValidatedJob,
    ) -> dict[str, Any]:
        """Call the LLM provider and return the raw script payload dict.

        Args:
            system_prompt: The system instruction string.
            user_prompt: The rendered user message string.
            job: The validated job (available for provider-specific tuning).

        Returns:
            A dict with keys ``title_hook`` and ``dialogue``.

        Raises:
            ScriptGenerationError: if the provider returns an invalid response.
        """
