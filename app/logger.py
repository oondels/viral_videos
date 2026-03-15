import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_process_logger() -> logging.Logger:
    """Return the process-level logger. Safe to call before workspace creation."""
    from app.config import config

    logger = logging.getLogger("viral_videos")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, config.log_level, logging.INFO))
    return logger


class JobLogger:
    """Writes JSON Lines events to the per-job log file.

    Must only be instantiated after the job workspace (including logs/) exists.
    Each call to log() appends one JSON object to logs/job.log.
    """

    def __init__(self, job_id: str, log_path: Path) -> None:
        self.job_id = job_id
        self.log_path = log_path

    def log(
        self,
        stage: str,
        event: str,
        message: str,
        *,
        duration_ms: int | None = None,
        artifact_path: str | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        entry: dict = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "job_id": self.job_id,
            "stage": stage,
            "event": event,
            "message": message,
        }
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        if artifact_path is not None:
            entry["artifact_path"] = artifact_path
        if error_type is not None:
            entry["error_type"] = error_type
        if error_message is not None:
            entry["error_message"] = error_message
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
