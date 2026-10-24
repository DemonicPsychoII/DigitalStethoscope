#!/usr/bin/env bash
# Compatibility entry point; pins and setup are shared with Windows.
set -euo pipefail
python3 "$(dirname "$0")/setup_zephyr.py" "$@"
