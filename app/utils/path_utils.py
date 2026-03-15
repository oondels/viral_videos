from pathlib import Path

OUTPUT_ROOT: Path = Path("output")
JOBS_ROOT: Path = OUTPUT_ROOT / "jobs"


def job_root(job_id: str) -> Path:
    """Return the root workspace directory for a given job_id."""
    return JOBS_ROOT / job_id
