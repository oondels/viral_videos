import argparse
import sys

from app.services.logging_config import setup_logging

logger = setup_logging()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Viral Videos pipeline")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--input", metavar="FILE", help="JSON job file")
    group.add_argument("--batch", metavar="FILE", help="CSV file with multiple jobs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.input:
        logger.info("Modo single job: %s", args.input)
        # Fase 10 — orquestrador será implementado aqui
        raise NotImplementedError("Pipeline ainda não implementado (Fase 10)")

    if args.batch:
        logger.info("Modo batch: %s", args.batch)
        # Fase 11 — batch processing será implementado aqui
        raise NotImplementedError("Batch ainda não implementado (Fase 11)")

    logger.info("Nenhum argumento fornecido. Use --input ou --batch.")
    logger.info("Exemplo: python -m app.main --input inputs/job_001.json")


if __name__ == "__main__":
    try:
        main()
    except NotImplementedError as e:
        logger.error(str(e))
        sys.exit(1)
