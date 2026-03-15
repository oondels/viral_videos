"""OpenAI concrete implementation of the ScriptGenerator interface."""
from __future__ import annotations

import json
from typing import Any

from app.adapters.llm_adapter import ScriptGenerationError, ScriptGenerator
from app.core.contracts import ValidatedJob


class OpenAIScriptGenerator(ScriptGenerator):
    """Calls the OpenAI Chat Completions API to generate a structured script.

    Requires OPENAI_API_KEY to be set in the environment (via .env).
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise ScriptGenerationError(
                "OPENAI_API_KEY is not set. Add it to your .env file."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ScriptGenerationError(
                "openai package is not installed. Run: pip install openai"
            ) from exc
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        job: ValidatedJob,
    ) -> dict[str, Any]:
        """Call OpenAI and return the raw script payload dict.

        Raises:
            ScriptGenerationError: on API error, invalid JSON, or missing keys.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            raise ScriptGenerationError(f"OpenAI API error: {exc}") from exc

        raw = response.choices[0].message.content or ""
        try:
            payload: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ScriptGenerationError(
                f"OpenAI returned invalid JSON: {exc}\nRaw response: {raw[:200]}"
            ) from exc

        if "title_hook" not in payload or "dialogue" not in payload:
            raise ScriptGenerationError(
                f"OpenAI response missing required keys. Got: {list(payload)}"
            )

        return payload
