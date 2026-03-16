import json

from app.core.job_context import JobContext

_WORKSPACE_SUBDIRS = [
    "script",
    "audio/segments",
    "audio/master",
    "clips",
    "background",
    "subtitles",
    "render",
    "logs",
]


def init_workspace(ctx: JobContext) -> None:
    """Create the canonical job workspace directory tree.

    Creates every required subdirectory under output/jobs/<job_id>/.
    Idempotent — safe to call more than once.
    Also persists job_input.json at the workspace root for --resume support.
    """
    for subdir in _WORKSPACE_SUBDIRS:
        (ctx.root() / subdir).mkdir(parents=True, exist_ok=True)
    job_input_path = ctx.root() / "job_input.json"
    job_input_path.write_text(
        json.dumps(ctx.job.model_dump(), indent=2),
        encoding="utf-8",
    )
