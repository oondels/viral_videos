"""Pipeline orchestrator — runs all 10 stages in canonical order for one job."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.adapters.lipsync_engine_adapter import LipSyncEngine, LipSyncError
from app.adapters.llm_adapter import ScriptGenerator, ScriptGenerationError
from app.adapters.tts_provider_adapter import TTSProvider, TTSError, load_voice_mapping
from app.config import config
from app.core.contracts import validate_job
from app.core.job_context import JobContext
from app.logger import JobLogger, get_process_logger
from app.modules.background_selector import prepare_background
from app.modules.compositor import compose_video
from app.modules.lipsync import generate_lipsync
from app.modules.script_writer import write_script
from app.modules.subtitles import generate_subtitles
from app.modules.timeline_builder import build_timeline
from app.modules.tts import generate_tts
from app.services.file_service import init_workspace
from app.utils.retry import retry

_process_logger = get_process_logger()


class PipelineError(Exception):
    """Raised when the pipeline cannot continue."""


def _now_ms() -> int:
    return int(time.monotonic() * 1000)


def run_pipeline(
    job_file: Path,
    llm_provider: ScriptGenerator,
    tts_provider: TTSProvider,
    lipsync_engine: LipSyncEngine,
) -> JobContext:
    """Execute the full single-job pipeline in canonical stage order.

    Stages run in the order mandated by SYSTEM_PIPELINE_ORCHESTRATION_SPEC:
    1. validate_input
    2. init_job_workspace
    3. write_script
    4. generate_tts
    5. build_timeline
    6. generate_lipsync
    7. prepare_background
    8. generate_subtitles
    9. compose_video
    10. finalize_job

    Execution is fail-fast: any stage exception stops the run immediately.
    Artifacts from completed stages remain on disk for inspection.

    Args:
        job_file: Path to the input JSON job file.
        llm_provider: ScriptGenerator implementation.
        tts_provider: TTSProvider implementation.
        lipsync_engine: LipSyncEngine implementation.

    Returns:
        The JobContext for the completed (or failed) job.

    Raises:
        PipelineError: wrapping the original exception from the failing stage.
    """
    # ------------------------------------------------------------------ #
    # Stage 1: validate_input                                              #
    # ------------------------------------------------------------------ #
    _process_logger.info("Stage: validate_input — %s", job_file)
    try:
        raw = json.loads(Path(job_file).read_text(encoding="utf-8"))
        job = validate_job(raw)
    except Exception as exc:
        _process_logger.error("validate_input failed: %s", exc)
        raise PipelineError(f"validate_input: {exc}") from exc

    ctx = JobContext(job=job)
    _process_logger.info("job_id=%s", job.job_id)

    # ------------------------------------------------------------------ #
    # Stage 2: init_job_workspace                                          #
    # ------------------------------------------------------------------ #
    _process_logger.info("Stage: init_job_workspace")
    t0_ws = _now_ms()
    try:
        init_workspace(ctx)
    except Exception as exc:
        _process_logger.error("init_job_workspace failed: %s", exc)
        raise PipelineError(f"init_job_workspace: {exc}") from exc

    job_log = JobLogger(job.job_id, ctx.job_log())
    # Retrospectively record init_job_workspace (log file now exists)
    elapsed_ws = _now_ms() - t0_ws
    job_log.log("init_job_workspace", "stage_started", "Starting init_job_workspace")
    job_log.log(
        "init_job_workspace", "stage_completed",
        "Completed init_job_workspace", duration_ms=elapsed_ws,
    )

    # ------------------------------------------------------------------ #
    # Helper: run one stage with timing and logging                        #
    # ------------------------------------------------------------------ #
    def _run(stage: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
        job_log.log(stage, "stage_started", f"Starting {stage}")
        t0 = _now_ms()
        try:
            result = fn(*args, **kwargs)
            elapsed = _now_ms() - t0
            job_log.log(stage, "stage_completed", f"Completed {stage}", duration_ms=elapsed)
            return result
        except Exception as exc:
            elapsed = _now_ms() - t0
            job_log.log(
                stage, "stage_failed", f"Failed {stage}",
                duration_ms=elapsed,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise PipelineError(f"{stage}: {exc}") from exc

    def _run_with_retry(
        stage: str,
        retryable: tuple[type[Exception], ...],
        fn: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Like _run but wraps fn in retry logic for transient provider errors."""
        def _call() -> Any:
            return fn(*args, **kwargs)

        job_log.log(stage, "stage_started", f"Starting {stage}")
        t0 = _now_ms()
        try:
            result = retry(
                _call,
                retryable=retryable,
                max_attempts=config.provider_max_retries,
            )
            elapsed = _now_ms() - t0
            job_log.log(stage, "stage_completed", f"Completed {stage}", duration_ms=elapsed)
            return result
        except Exception as exc:
            elapsed = _now_ms() - t0
            job_log.log(
                stage, "stage_failed", f"Failed {stage}",
                duration_ms=elapsed,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise PipelineError(f"{stage}: {exc}") from exc

    # ------------------------------------------------------------------ #
    # Stages 3–10                                                          #
    # ------------------------------------------------------------------ #
    try:
        voice_mapping = load_voice_mapping()

        _run_with_retry(
            "write_script", (ScriptGenerationError,),
            write_script, ctx, llm_provider,
        )
        _run_with_retry(
            "generate_tts", (TTSError,),
            generate_tts, ctx, tts_provider, voice_mapping,
        )
        _run("build_timeline", build_timeline, ctx)
        _run_with_retry(
            "generate_lipsync", (LipSyncError,),
            generate_lipsync, ctx, lipsync_engine,
        )

        timeline = json.loads(ctx.timeline_json().read_text(encoding="utf-8"))
        total_duration = timeline[-1]["end_sec"]
        _run("prepare_background", prepare_background, ctx, total_duration)

        _run("generate_subtitles", generate_subtitles, ctx)
        _run("compose_video", compose_video, ctx)

        # finalize_job
        job_log.log("finalize_job", "stage_started", "Starting finalize_job")
        job_log.log("finalize_job", "stage_completed", "Pipeline completed successfully")
        _process_logger.info("Pipeline completed: %s → %s", job.job_id, ctx.final_mp4())

    except PipelineError:
        raise
    except Exception as exc:
        raise PipelineError(f"Unexpected pipeline error: {exc}") from exc

    return ctx


def resume_pipeline(
    job_id: str,
    llm_provider: ScriptGenerator,
    tts_provider: TTSProvider,
    lipsync_engine: LipSyncEngine,
) -> JobContext:
    """Resume a previously started job from existing on-disk artifacts.

    Reads job_input.json from output/jobs/<job_id>/, reconstructs the
    ValidatedJob, and executes only the stages whose canonical output
    artifacts are absent.  Stages whose artifacts already exist emit a
    stage_skipped event and are not re-executed.

    Args:
        job_id: The job identifier (e.g. "job_2026_03_15_935").
        llm_provider: ScriptGenerator implementation.
        tts_provider: TTSProvider implementation.
        lipsync_engine: LipSyncEngine implementation.

    Returns:
        The JobContext for the resumed job.

    Raises:
        PipelineError: if job_input.json is missing, the job cannot be
            reconstructed, or any executed stage fails.
    """
    from app.core.contracts import ValidatedJob

    job_input_path = Path("output") / "jobs" / job_id / "job_input.json"
    if not job_input_path.exists():
        raise PipelineError(
            f"resume: job_input.json not found at {job_input_path}. "
            "Use --input with the original JSON file instead."
        )

    try:
        job = ValidatedJob.model_validate(
            json.loads(job_input_path.read_text(encoding="utf-8"))
        )
    except Exception as exc:
        raise PipelineError(
            f"resume: failed to reconstruct job from job_input.json: {exc}"
        ) from exc

    ctx = JobContext(job=job)

    try:
        init_workspace(ctx)
    except Exception as exc:
        raise PipelineError(f"init_job_workspace: {exc}") from exc

    job_log = JobLogger(job.job_id, ctx.job_log())

    def _run(stage: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
        job_log.log(stage, "stage_started", f"Starting {stage}")
        t0 = _now_ms()
        try:
            result = fn(*args, **kwargs)
            elapsed = _now_ms() - t0
            job_log.log(stage, "stage_completed", f"Completed {stage}", duration_ms=elapsed)
            return result
        except Exception as exc:
            elapsed = _now_ms() - t0
            job_log.log(
                stage, "stage_failed", f"Failed {stage}",
                duration_ms=elapsed,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise PipelineError(f"{stage}: {exc}") from exc

    def _run_with_retry(
        stage: str,
        retryable: tuple[type[Exception], ...],
        fn: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        def _call() -> Any:
            return fn(*args, **kwargs)

        job_log.log(stage, "stage_started", f"Starting {stage}")
        t0 = _now_ms()
        try:
            result = retry(
                _call,
                retryable=retryable,
                max_attempts=config.provider_max_retries,
            )
            elapsed = _now_ms() - t0
            job_log.log(stage, "stage_completed", f"Completed {stage}", duration_ms=elapsed)
            return result
        except Exception as exc:
            elapsed = _now_ms() - t0
            job_log.log(
                stage, "stage_failed", f"Failed {stage}",
                duration_ms=elapsed,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise PipelineError(f"{stage}: {exc}") from exc

    def _skip(stage: str) -> None:
        job_log.log(stage, "stage_skipped", f"Skipped {stage} — artifacts present")

    def _all_clips_exist() -> bool:
        if not ctx.timeline_json().exists():
            return False
        timeline: list[dict[str, Any]] = json.loads(
            ctx.timeline_json().read_text(encoding="utf-8")
        )
        return all(
            item.get("clip_file") and Path(item["clip_file"]).exists()
            for item in timeline
        )

    try:
        voice_mapping = load_voice_mapping()

        if ctx.script_json().exists() and ctx.dialogue_json().exists():
            _skip("write_script")
        else:
            _run_with_retry(
                "write_script", (ScriptGenerationError,),
                write_script, ctx, llm_provider,
            )

        if ctx.audio_manifest().exists():
            _skip("generate_tts")
        else:
            _run_with_retry(
                "generate_tts", (TTSError,),
                generate_tts, ctx, tts_provider, voice_mapping,
            )

        if ctx.timeline_json().exists() and ctx.master_audio().exists():
            _skip("build_timeline")
        else:
            _run("build_timeline", build_timeline, ctx)

        if _all_clips_exist():
            _skip("generate_lipsync")
        else:
            _run_with_retry(
                "generate_lipsync", (LipSyncError,),
                generate_lipsync, ctx, lipsync_engine,
            )

        if ctx.prepared_background().exists():
            _skip("prepare_background")
        else:
            timeline = json.loads(ctx.timeline_json().read_text(encoding="utf-8"))
            total_duration = timeline[-1]["end_sec"]
            _run("prepare_background", prepare_background, ctx, total_duration)

        if ctx.subtitles_srt().exists():
            _skip("generate_subtitles")
        else:
            _run("generate_subtitles", generate_subtitles, ctx)

        if ctx.final_mp4().exists():
            _skip("compose_video")
        else:
            _run("compose_video", compose_video, ctx)

        job_log.log("finalize_job", "stage_started", "Starting finalize_job")
        job_log.log("finalize_job", "stage_completed", "Pipeline completed successfully")
        _process_logger.info("Resume completed: %s → %s", job.job_id, ctx.final_mp4())

    except PipelineError:
        raise
    except Exception as exc:
        raise PipelineError(f"Unexpected pipeline error: {exc}") from exc

    return ctx
