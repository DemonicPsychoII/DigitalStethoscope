"""Install reviewed, checksum-pinned workflow validators without package-manager drift."""

import argparse
import hashlib
import io
import json
import os
import tarfile
import urllib.request
from pathlib import Path


def binary(archive: bytes, digest: str, member: str) -> bytes:
    if hashlib.sha256(archive).hexdigest() != digest:
        raise ValueError("validator archive checksum mismatch")
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        entry = stream.getmember(member)
        if not entry.isfile() or entry.size > 32 * 1024 * 1024:
            raise ValueError("validator is not a bounded regular file")
        return stream.extractfile(entry).read()


def prepared_binary(prepared: Path, name: str, pin: dict) -> bytes | None:
    try:
        entry = json.loads((prepared / "manifest.json").read_text())[name]
        if entry["pin"] != pin:
            return None
        if (prepared / name).stat().st_size > 32 * 1024 * 1024:
            return None
        payload = (prepared / name).read_bytes()
        if len(payload) > 32 * 1024 * 1024:
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
                archive = response.read(32 * 1024 * 1024 + 1)
            payload = binary(archive, pin["sha256"], pin["member"])
        (target / name).write_bytes(payload)
        (target / name).chmod(0o755)
        manifest[name] = {
            "pin": pin,
            "binary_sha256": hashlib.sha256(payload).hexdigest(),
        }
    (target / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")


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
