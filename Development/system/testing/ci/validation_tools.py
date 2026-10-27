"""Install reviewed, checksum-pinned validation tools without package-manager drift."""

import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
import urllib.request
from pathlib import Path


def binary(
    archive: bytes, digest: str, member: str, maximum_bytes: int = 32 * 1024 * 1024
) -> bytes:
    if hashlib.sha256(archive).hexdigest() != digest:
        raise ValueError("validator archive checksum mismatch")
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        entry = stream.getmember(member)
        if not entry.isfile() or entry.size > maximum_bytes:
            raise ValueError("validator is not a bounded regular file")
        return stream.extractfile(entry).read()


def prepared_binary(prepared: Path, name: str, pin: dict) -> bytes | None:
    maximum_bytes = pin.get("maximum_binary_bytes", 32 * 1024 * 1024)
    try:
        entry = json.loads((prepared / "manifest.json").read_text())[name]
        if entry["pin"] != pin:
            return None
        if (prepared / name).stat().st_size > maximum_bytes:
            return None
        payload = (prepared / name).read_bytes()
        if len(payload) > maximum_bytes:
            return None
        if hashlib.sha256(payload).hexdigest() != entry["binary_sha256"]:
            return None
        return payload
    except (OSError, ValueError, KeyError, TypeError):
        return None


def install(pins: dict, target: Path, prepared: Path | None = None) -> None:
    target.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, pin in pins.items():
        payload = prepared_binary(prepared, name, pin) if prepared else None
        if payload is None:
            request = urllib.request.Request(
                pin["url"], headers={"User-Agent": "stethoscope-ci"}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                maximum_archive_bytes = pin.get(
                    "maximum_archive_bytes", 32 * 1024 * 1024
                )
                archive = response.read(maximum_archive_bytes + 1)
            if len(archive) > maximum_archive_bytes:
                raise ValueError("validation tool archive exceeds size limit")
            payload = binary(
                archive,
                pin["sha256"],
                pin["member"],
                pin.get("maximum_binary_bytes", 32 * 1024 * 1024),
            )
        (target / name).write_bytes(payload)
        (target / name).chmod(0o755)
        manifest[name] = {
            "pin": pin,
            "binary_sha256": hashlib.sha256(payload).hexdigest(),
        }
    (target / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")


def node_runtime(root: Path) -> Path | None:
    local_runtime = os.environ.get("STETHO_NODE") if not os.environ.get("CI") else None
    if local_runtime:
        runtime = Path(local_runtime)
        if not runtime.is_absolute():
            raise RuntimeError("STETHO_NODE must be an absolute path to Node")
    elif sys.platform == "win32" and not os.environ.get("CI"):
        return None
    else:
        runtime = root / ".ci-validation-tools/node"
    if not runtime.is_file():
        raise RuntimeError(
            f"Node is required to execute the portal page JavaScript: {runtime}; "
            "run python Development/system/testing/ci/validation_tools.py first "
            "(Linux), or set STETHO_NODE to an absolute Node executable path locally"
        )
    return runtime


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=root / ".ci-validation-tools")
    parser.add_argument(
        "--prepared", type=Path, default=Path("/opt/stethoscope-ci/validation-tools")
    )
    args = parser.parse_args()
    pins = json.loads(Path(__file__).with_suffix(".json").read_text())
    install(pins, args.target, args.prepared)
    if os.environ.get("GITHUB_PATH"):
        with Path(os.environ["GITHUB_PATH"]).open("a") as stream:
            stream.write(str(args.target) + "\n")


if __name__ == "__main__":
    main()
