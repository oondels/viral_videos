"""Batch runner — processes multiple jobs sequentially from a CSV file."""
from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.adapters.lipsync_engine_adapter import LipSyncEngine
from app.adapters.llm_adapter import ScriptGenerator
from app.adapters.tts_provider_adapter import TTSProvider
from app.logger import get_process_logger
from app.pipeline import PipelineError, run_pipeline

_log = get_process_logger()

_REPORT_DIR = Path("output/batch_reports")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_csv(batch_file: Path) -> list[dict[str, str]]:
    """Read CSV rows as dicts. Raises ValueError if the file is unreadable."""
    try:
        text = batch_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Cannot read batch file '{batch_file}': {exc}") from exc
    reader = csv.DictReader(text.splitlines())
    return list(reader)


def _parse_row(row: dict[str, str], row_index: int) -> dict[str, Any]:
    """Convert a CSV row dict into a validated job payload dict.

    CSV columns (only ``topic`` is required):
    - topic
    - duration_target_sec  (optional integer)
    - background_style     (optional string)
    - characters           (optional, pipe-separated, e.g. "char_a|char_b")
    - output_preset        (optional string)

    Raises:
        ValueError: if a required field is missing or a value cannot be parsed.
    """
    job: dict[str, Any] = {}

    topic = row.get("topic", "").strip()
    if not topic:
        raise ValueError(f"row {row_index}: 'topic' is required and cannot be empty")
    job["topic"] = topic

    if row.get("duration_target_sec", "").strip():
        try:
            job["duration_target_sec"] = int(row["duration_target_sec"].strip())
        except ValueError as exc:
            raise ValueError(
                f"row {row_index}: 'duration_target_sec' must be an integer"
            ) from exc

    if row.get("background_style", "").strip():
        job["background_style"] = row["background_style"].strip()

    if row.get("characters", "").strip():
        job["characters"] = [c.strip() for c in row["characters"].split("|") if c.strip()]

    if row.get("output_preset", "").strip():
        job["output_preset"] = row["output_preset"].strip()

    return job


def run_batch(
    batch_file: Path,
    llm_provider: ScriptGenerator,
    tts_provider: TTSProvider,
    lipsync_engine: LipSyncEngine,
) -> dict[str, Any]:
    """Process multiple jobs from a CSV file sequentially.

    - Continues to the next item after any per-item failure.
    - Each item receives its own ``job_id`` via the normal pipeline.
    - Writes ``output/batch_reports/latest_report.json`` on completion.

    Args:
        batch_file: Path to the CSV file containing job rows.
        llm_provider: ScriptGenerator implementation.
        tts_provider: TTSProvider implementation.
        lipsync_engine: LipSyncEngine implementation.

    Returns:
        The report dict written to ``latest_report.json``.

    Raises:
        ValueError: if the batch file is unreadable or empty.
    """
    started_at = _utc_now()
    items: list[dict[str, Any]] = []

    rows = _read_csv(batch_file)
    _log.info("Batch: %d row(s) from %s", len(rows), batch_file)

    for i, row in enumerate(rows, start=1):
        input_ref = f"row_{i}"
        try:
            job_dict = _parse_row(row, i)
        except ValueError as exc:
            _log.warning("Batch %s parse error: %s", input_ref, exc)
            items.append({
                "job_id": None,
                "input_ref": input_ref,
                "status": "failed",
                "output_file": None,
                "error_message": str(exc),
            })
            continue

        # Write a temporary job file so run_pipeline can validate and load it.
        tmp_fd, tmp_name = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                json.dump(job_dict, fh, ensure_ascii=False)
            tmp_path = Path(tmp_name)

            try:
                ctx = run_pipeline(tmp_path, llm_provider, tts_provider, lipsync_engine)
                items.append({
                    "job_id": ctx.job.job_id,
                    "input_ref": input_ref,
                    "status": "success",
                    "output_file": str(ctx.final_mp4()),
                    "error_message": None,
                })
                _log.info("Batch %s succeeded: job_id=%s", input_ref, ctx.job.job_id)
            except PipelineError as exc:
                _log.warning("Batch %s failed: %s", input_ref, exc)
                items.append({
                    "job_id": None,
                    "input_ref": input_ref,
                    "status": "failed",
                    "output_file": None,
                    "error_message": str(exc),
                })
        finally:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass

    finished_at = _utc_now()
    succeeded = sum(1 for it in items if it["status"] == "success")
    failed = sum(1 for it in items if it["status"] == "failed")

    report: dict[str, Any] = {
        "started_at": started_at,
        "finished_at": finished_at,
        "total_jobs": len(items),
        "succeeded_jobs": succeeded,
        "failed_jobs": failed,
        "items": items,
    }

    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = _REPORT_DIR / "latest_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _log.info(
        "Batch complete: %d/%d succeeded → %s", succeeded, len(items), report_path
    )

    return report
