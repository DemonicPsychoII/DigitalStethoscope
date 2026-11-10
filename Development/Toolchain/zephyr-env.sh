# Source to put the pinned west, CMake and Ninja on PATH and set the Zephyr variables
# in Bash on Linux or Git Bash on Windows: . Development/Toolchain/zephyr-env.sh
# The workspace is the one shared by all checkouts and worktrees for the current pins.
# shellcheck shell=bash

zephyr_environment_resolver="$(cd "$(dirname "${BASH_SOURCE[0]}")/../system/coding/tools/toolchain" && pwd)/toolchain_environment.py"
zephyr_environment_python="${PYTHON:-}"
if [[ -z "$zephyr_environment_python" ]]; then
    for zephyr_environment_candidate in python3 python; do
        # The Windows Store alias named python3 exists but cannot run scripts.
        if "$zephyr_environment_candidate" -c 'import sys' >/dev/null 2>&1; then
            zephyr_environment_python="$zephyr_environment_candidate"
            break
        fi
    done
fi
if zephyr_environment_script="$("$zephyr_environment_python" "$zephyr_environment_resolver" --format posix)"; then
    eval "$zephyr_environment_script"
    echo "Zephyr environment enabled from $STETHOSCOPE_TOOLCHAIN_WORKSPACE"
    for zephyr_environment_tool in west cmake ninja; do
        echo "  $zephyr_environment_tool -> $(command -v "$zephyr_environment_tool")"
    done
    echo 'west build -b esp32s3_devkitc/esp32s3/procpu <application>'
else
    echo 'Pinned toolchain not found; see the message above.' >&2
fi
unset zephyr_environment_resolver zephyr_environment_python zephyr_environment_candidate \
    zephyr_environment_script zephyr_environment_tool
