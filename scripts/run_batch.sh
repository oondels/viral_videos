#!/usr/bin/env bash
# Run the batch pipeline via Docker Compose.
# Usage: ./scripts/run_batch.sh [CSV_FILE]
#   CSV_FILE defaults to inputs/batch/jobs.csv

set -euo pipefail

CSV_FILE="${1:-inputs/batch/jobs.csv}"

docker compose run --rm app python -m app.main --batch "$CSV_FILE"
