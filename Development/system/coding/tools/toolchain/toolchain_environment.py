#!/usr/bin/env python3
"""Print the pinned firmware toolchain environment for shells and helper scripts.

The workspace is resolved like the CI and build scripts resolve it, so every checkout
and worktree uses the same pinned west, CMake, Ninja, Zephyr and SDK.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path, PureWindowsPath

from build_support import (
    PINS,
    WORKSPACE_VARIABLE,
    bin_dir,
    toolchain_workspace,
    workspace_matches_pins,
)

TOOLS = ("west", "cmake", "ninja")


def executable(directory: Path, name: str) -> Path:
    return directory / (f"{name}.exe" if os.name == "nt" else name)


def describe(workspace: Path) -> dict:
    workspace = workspace.resolve()
    tool_directory = bin_dir(workspace)
    return {
        "workspace": str(workspace),
        "pins_match": workspace_matches_pins(workspace),
        "path": [str(tool_directory)],
        "tools": {name: str(executable(tool_directory, name)) for name in TOOLS},
        "variables": {
            WORKSPACE_VARIABLE: str(workspace),
            "ZEPHYR_BASE": str(workspace / "zephyr"),
            "ZEPHYR_SDK_INSTALL_DIR": str(
                workspace / f"zephyr-sdk-{PINS['sdk_version']}"
            ),
            "ZEPHYR_TOOLCHAIN_VARIANT": "zephyr",
        },
    }


def posix_path(path: str) -> str:
    """Git Bash on Windows reads PATH entries as /c/... paths."""
    if os.name != "nt":
        return path
    windows = PureWindowsPath(path)
    drive = windows.drive.rstrip(":").lower()
    return "/" + drive + "/" + "/".join(windows.parts[1:])


def posix_script(environment: dict) -> str:
    lines = [
        f"export {name}={shlex.quote(value)}"
        for name, value in environment["variables"].items()
    ]
    prefix = ":".join(shlex.quote(posix_path(entry)) for entry in environment["path"])
    lines.append(f'export PATH={prefix}:"$PATH"')
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("json", "posix", "workspace"),
        default="json",
        help="workspace prints only the resolved path, without checking its tools",
    )
    arguments = parser.parse_args()
    environment = describe(toolchain_workspace())
    if arguments.format == "workspace":
        sys.stdout.buffer.write((environment["workspace"] + "\n").encode("utf-8"))
        return
    missing = [
        name for name, path in environment["tools"].items() if not Path(path).is_file()
    ]
    if missing:
        raise SystemExit(
            f"Pinned toolchain incomplete in {environment['workspace']}: "
            f"{', '.join(missing)} missing. Run "
            "python Development/system/coding/tools/toolchain/setup_zephyr.py first."
        )
    if arguments.format == "json":
        output = json.dumps(environment, indent=2)
    else:
        output = posix_script(environment)
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
