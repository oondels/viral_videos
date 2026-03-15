import argparse
import sys

from app.logger import get_process_logger

logger = get_process_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Viral Videos pipeline")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--input", metavar="FILE", help="JSON job file")
    group.add_argument("--batch", metavar="FILE", help="CSV file with multiple jobs")
    return parser.parse_args()


def _build_providers():
    """Instantiate the configured external provider adapters.

    Returns (llm_provider, tts_provider, lipsync_engine).
    Raises ImportError or RuntimeError if a required provider cannot be loaded.
    """
    from app.config import config

    # LLM provider — defaults to OpenAI
    from app.adapters.openai_llm_adapter import OpenAIScriptGenerator
    llm = OpenAIScriptGenerator(api_key=config.openai_api_key)

    # TTS provider — defaults to ElevenLabs
    from app.adapters.elevenlabs_tts_adapter import ElevenLabsTTSProvider
    tts = ElevenLabsTTSProvider(api_key=config.elevenlabs_api_key)

    # Lip-sync engine — defaults to SadTalker stub (provider must be registered)
    from app.adapters.lipsync_engine_adapter import LipSyncEngine
    raise NotImplementedError(
        "No lip-sync engine registered. "
        "Implement a LipSyncEngine adapter and register it here."
    )


def main() -> None:
    args = parse_args()

    if args.input:
        from pathlib import Path
        from app.pipeline import PipelineError, run_pipeline

        try:
            llm, tts, lipsync = _build_providers()
        except NotImplementedError as exc:
            logger.error("Provider setup failed: %s", exc)
            sys.exit(1)

        try:
            run_pipeline(Path(args.input), llm, tts, lipsync)
        except PipelineError as exc:
            logger.error("Pipeline failed: %s", exc)
            sys.exit(1)
        return

    if args.batch:
        from pathlib import Path
        from app.batch import run_batch

        try:
            llm, tts, lipsync = _build_providers()
        except NotImplementedError as exc:
            logger.error("Provider setup failed: %s", exc)
            sys.exit(1)

        try:
            run_batch(Path(args.batch), llm, tts, lipsync)
        except ValueError as exc:
            logger.error("Batch failed: %s", exc)
            sys.exit(1)
        return

    logger.info("Nenhum argumento fornecido. Use --input ou --batch.")
    logger.info("Exemplo: python -m app.main --input inputs/examples/job_001.json")


if __name__ == "__main__":
    try:
        main()
    except NotImplementedError as e:
        logger.error(str(e))
        sys.exit(1)
