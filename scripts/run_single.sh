#!/usr/bin/env bash
# Run the single-job pipeline via Docker Compose.
# Usage: ./scripts/run_single.sh <JOB_JSON_FILE>

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <job_json_file>"
    echo "Example: $0 inputs/examples/job_001.json"
    exit 1
fi

docker compose run --rm app python -m app.main --input "$1"
