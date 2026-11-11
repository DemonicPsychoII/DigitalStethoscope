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
    WORKSPACE_VARIABLE,
    bin_dir,
    sdk_directory,
    toolchain_problems,
    toolchain_workspace,
)

TOOLS = ("west", "cmake", "ninja")


def executable(directory: Path, name: str) -> Path:
    return directory / (f"{name}.exe" if os.name == "nt" else name)


def describe(workspace: Path) -> dict:
    workspace = workspace.resolve()
    tool_directory = bin_dir(workspace)
    return {
        "workspace": str(workspace),
        "path": [str(tool_directory)],
        "tools": {name: str(executable(tool_directory, name)) for name in TOOLS},
        "variables": {
            WORKSPACE_VARIABLE: str(workspace),
            "ZEPHYR_BASE": str(workspace / "zephyr"),
            "ZEPHYR_SDK_INSTALL_DIR": str(sdk_directory(workspace)),
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
        choices=("json", "posix", "locations"),
        default="json",
        help="locations prints the workspace and SDK paths without checking the tools",
    )
    arguments = parser.parse_args()
    workspace = toolchain_workspace()
    environment = describe(workspace)
    if arguments.format == "locations":
        locations = {
            "workspace": environment["workspace"],
            "sdk": environment["variables"]["ZEPHYR_SDK_INSTALL_DIR"],
        }
        sys.stdout.buffer.write((json.dumps(locations) + "\n").encode("utf-8"))
        return
    problems = toolchain_problems(workspace)
    if problems:
        raise SystemExit(
            f"Pinned toolchain not ready in {environment['workspace']}: "
            f"{'; '.join(problems)}. Run "
            "python Development/system/coding/tools/toolchain/setup_zephyr.py first."
        )
    if arguments.format == "json":
        output = json.dumps(environment, indent=2)
    else:
        output = posix_script(environment)
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
