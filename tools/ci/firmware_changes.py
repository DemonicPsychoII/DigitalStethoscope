"""Skip firmware provisioning only when no firmware or CI input changed."""

import os
import subprocess
from pathlib import Path


def needs_firmware(paths: list[str]) -> bool:
    return any(
        path == ".github/workflows/quality-gates.yml"
        or path.startswith("software/evaluation/firmware/")
        or path.startswith("tools/ci/")
        or path.startswith("tools/toolchain/")
        or path.startswith("Development/system/coding/bringup-zephyr/")
        or path.startswith("Development/system/testing/ci/")
        or path.startswith("Development/system/coding/tools/")
        or path.startswith("Development/Toolchain/")
        for path in paths
    )


def main() -> None:
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            os.environ["BASE_SHA"],
            os.environ["HEAD_SHA"],
            "--",
        ]
    )
    paths = changed.decode("utf-8", errors="surrogateescape").split("\0")
    value = str(needs_firmware(paths)).lower()
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"firmware={value}\n")
    print(f"Firmware build required: {value}")


if __name__ == "__main__":
    main()
