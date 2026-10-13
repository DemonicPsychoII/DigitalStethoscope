"""Install a pinned compiler cache; compiler outputs remain inside disposable guests."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from build_support import ROOT
from validation_tools import install


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=ROOT / ".ci-compiler-tools")
    parser.add_argument(
        "--prepared", type=Path, default=Path("/opt/zephyr-workspace/compiler-tools")
    )
    args = parser.parse_args()
    pins = json.loads(Path(__file__).with_suffix(".json").read_text())
    install(pins, args.target, args.prepared)
    executable = args.target / "ccache"
    subprocess.run([str(executable), "--version"], check=True)
    if os.environ.get("GITHUB_PATH"):
        with Path(os.environ["GITHUB_PATH"]).open("a") as stream:
            stream.write(str(args.target) + "\n")
    if os.environ.get("GITHUB_ENV"):
        with Path(os.environ["GITHUB_ENV"]).open("a") as stream:
            stream.write(f"CCACHE_DIR={ROOT / '.ci-ccache'}\n")
            stream.write(f"CCACHE_BASEDIR={ROOT}\n")
            stream.write("CCACHE_COMPILERCHECK=content\nCCACHE_MAXSIZE=512M\n")


if __name__ == "__main__":
    main()
