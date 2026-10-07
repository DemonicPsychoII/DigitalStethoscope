"""Install reviewed, checksum-pinned workflow validators without package-manager drift."""

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


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    pins = json.loads(Path(__file__).with_suffix(".json").read_text())
    target = root / ".ci-validation-tools"
    target.mkdir(exist_ok=True)
    for name, pin in pins.items():
        request = urllib.request.Request(
            pin["url"], headers={"User-Agent": "stethoscope-ci"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            archive = response.read(32 * 1024 * 1024 + 1)
        (target / name).write_bytes(binary(archive, pin["sha256"], pin["member"]))
        (target / name).chmod(0o755)
    if os.environ.get("GITHUB_PATH"):
        with Path(os.environ["GITHUB_PATH"]).open("a") as stream:
            stream.write(str(target) + "\n")


if __name__ == "__main__":
    main()
