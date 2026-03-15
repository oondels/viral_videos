#!/usr/bin/env bash
# Remove temporary files from the temp/ directory.
# Permanent outputs in output/ are not affected.

set -euo pipefail

TEMP_DIR="${1:-temp}"

if [[ ! -d "$TEMP_DIR" ]]; then
    echo "Nothing to clean: $TEMP_DIR does not exist."
    exit 0
fi

echo "Cleaning $TEMP_DIR ..."
find "$TEMP_DIR" -mindepth 1 -delete
echo "Done."
