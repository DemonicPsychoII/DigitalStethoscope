#!/usr/bin/env bash
# CI provisioning: the production setup builds the workspace; only a complete setup
# records the prepared-environment marker that later image checks compare against.
set -euo pipefail
ci_directory="$(cd "$(dirname "$0")" && pwd)"
repository="$(cd "$ci_directory/../../../.." && pwd)"
workspace="$repository/.ci-workspace"
if (($#)); then
    if [[ "$1" != --workspace || $# -ne 2 ]]; then
        echo "usage: $0 [--workspace PATH]" >&2
        exit 2
    fi
    workspace="$2"
fi
python3 "$ci_directory/prepared_env.py" invalidate zephyr "$workspace"
python3 "$repository/Development/system/coding/tools/toolchain/setup_zephyr.py" --workspace "$workspace"
python3 "$ci_directory/prepared_env.py" record zephyr "$workspace"
