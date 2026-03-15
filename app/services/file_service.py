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
    """
    for subdir in _WORKSPACE_SUBDIRS:
        (ctx.root() / subdir).mkdir(parents=True, exist_ok=True)
