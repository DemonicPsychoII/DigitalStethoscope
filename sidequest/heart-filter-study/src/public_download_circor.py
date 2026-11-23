"""Download the CirCor DigiScope Phonocardiogram Dataset 1.0.3 and verify every file against SHA256SUMS.txt.

Files are fetched one by one from the PhysioNet open-data S3 mirror in parallel. A partial file is
resumed with an HTTP Range request; a finished file is only accepted when its SHA-256 matches.
Rerunning skips every file that is already present and verified.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import datetime
import hashlib
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

STUDY_DIRECTORY = Path(__file__).resolve().parents[1]
TARGET_DIRECTORY = STUDY_DIRECTORY / "public-data" / "circor-1.0.3"
FILE_BASE_URL = "https://physionet-open.s3.amazonaws.com/circor-heart-sound/1.0.3/"
LANDING_PAGE_URL = "https://physionet.org/content/circor-heart-sound/1.0.3/"
CHECKSUM_FILE_NAME = "SHA256SUMS.txt"
PARTIAL_SUFFIX = ".part"
CHUNK_BYTES = 1 << 16
ATTEMPTS = 4


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(relative_name: str) -> Path:
    parts = relative_name.replace("\\", "/").split("/")
    candidate = Path(*parts)
    if (candidate.is_absolute() or candidate.drive or ":" in relative_name
            or any(part in ("", ".", "..") for part in parts)):
        raise ValueError(f"unsafe path in checksum list: {relative_name!r}")
    return candidate


def fetch_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def parse_checksum_list(text: str) -> dict[str, str]:
    expected_hashes = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        hash_value, relative_name = line.split(maxsplit=1)
        relative_name = relative_name.strip().lstrip("*")
        safe_relative_path(relative_name)
        expected_hashes[relative_name] = hash_value.lower()
    return expected_hashes


def download_with_resume(relative_name: str, expected_hash: str) -> tuple[str, int, str | None]:
    """Returns (relative name, size in bytes, error message or None)."""
    final_path = TARGET_DIRECTORY / safe_relative_path(relative_name)
    partial_path = final_path.with_name(final_path.name + PARTIAL_SUFFIX)
    if final_path.exists() and sha256_of_file(final_path) == expected_hash:
        partial_path.unlink(missing_ok=True)
        return relative_name, final_path.stat().st_size, None
    final_path.parent.mkdir(parents=True, exist_ok=True)
    url = FILE_BASE_URL + relative_name
    last_error = "unknown"
    for attempt in range(ATTEMPTS):
        try:
            existing_bytes = partial_path.stat().st_size if partial_path.exists() else 0
            request = urllib.request.Request(url)
            if existing_bytes:
                request.add_header("Range", f"bytes={existing_bytes}-")
            try:
                response = urllib.request.urlopen(request, timeout=60)
            except urllib.error.HTTPError as error:
                if error.code == 416:
                    partial_path.unlink(missing_ok=True)
                    continue
                raise
            with response:
                append = existing_bytes > 0 and response.status == 206
                with open(partial_path, "ab" if append else "wb") as stream:
                    for chunk in iter(lambda: response.read(CHUNK_BYTES), b""):
                        stream.write(chunk)
            if sha256_of_file(partial_path) == expected_hash:
                partial_path.replace(final_path)
                return relative_name, final_path.stat().st_size, None
            last_error = "SHA-256 mismatch"
            partial_path.unlink(missing_ok=True)
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            last_error = f"{type(error).__name__}: {error}"
            time.sleep(1.0 + attempt)
    return relative_name, 0, last_error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=32)
    arguments = parser.parse_args()

    TARGET_DIRECTORY.mkdir(parents=True, exist_ok=True)
    ready_marker = TARGET_DIRECTORY / "READY"
    ready_marker.unlink(missing_ok=True)

    checksum_text = fetch_bytes(FILE_BASE_URL + CHECKSUM_FILE_NAME).decode("utf-8")
    (TARGET_DIRECTORY / CHECKSUM_FILE_NAME).write_text(checksum_text, encoding="utf-8", newline="\n")
    expected_hashes = parse_checksum_list(checksum_text)

    failures = []
    total_bytes = 0
    verified_count = 0
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=arguments.workers) as executor:
        futures = {executor.submit(download_with_resume, name, value): name for name, value in expected_hashes.items()}
        for completed_count, future in enumerate(as_completed(futures), start=1):
            try:
                relative_name, size_bytes, error_message = future.result()
            except Exception as error:
                relative_name, size_bytes, error_message = futures[future], 0, f"{type(error).__name__}: {error}"
            if error_message is None:
                verified_count += 1
                total_bytes += size_bytes
            else:
                failures.append({"file": relative_name, "error": error_message})
            if completed_count % 500 == 0 or completed_count == len(futures):
                elapsed = time.monotonic() - started
                print(f"{completed_count}/{len(futures)} files, {total_bytes / 1e6:.1f} MB, "
                      f"{len(failures)} failures, {elapsed:.0f} s", flush=True)

    manifest = {
        "dataset": "CirCor DigiScope Phonocardiogram Dataset",
        "version": "1.0.3",
        "doi": "10.13026/tshs-mw03",
        "licence": "Open Data Commons Attribution License v1.0",
        "landing_page_url": LANDING_PAGE_URL,
        "source_url": FILE_BASE_URL,
        "checksum_file": CHECKSUM_FILE_NAME,
        "access_date": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "file_count": len(expected_hashes),
        "total_bytes": total_bytes,
        "verified_count": verified_count,
        "failures": sorted(failures, key=lambda failure: failure["file"]),
        "note": "file_count and verified_count exclude SHA256SUMS.txt itself, which lists no hash for itself",
    }
    (TARGET_DIRECTORY / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if not failures and verified_count == len(expected_hashes):
        ready_marker.touch()
        print("all files verified; READY written")
        return 0
    print(f"{len(failures)} files failed; READY not written")
    return 1


if __name__ == "__main__":
    sys.exit(main())
