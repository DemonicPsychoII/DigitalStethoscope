"""Download the EPHNOGRAM database (WFDB part only) with checksum verification.

Resumable via HTTP Range requests, parallel, idempotent. Files keep the source's relative
paths below public-data/ephnogram-1.0.0/. MAT files are never downloaded.

Usage:
    .venv/Scripts/python.exe -I src/public_download_ephnogram.py [--stop-new-at HH:MM] [--workers N]
"""

import sys
from pathlib import Path, PurePosixPath

SOURCE_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE_DIRECTORY))

import argparse
import csv
import datetime
import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

STUDY_DIRECTORY = SOURCE_DIRECTORY.parent
TARGET_DIRECTORY = STUDY_DIRECTORY / "public-data" / "ephnogram-1.0.0"
PRIMARY_BASE_URL = "https://physionet-open.s3.amazonaws.com/ephnogram/1.0.0/"
CANONICAL_BASE_URL = "https://physionet.org/files/ephnogram/1.0.0/"
DATABASE_VERSION = "1.0.0"
DATABASE_DOI = "10.13026/tjtq-5911"
DATABASE_LICENCE = "Open Data Commons Attribution License v1.0"
SMALL_INDEX_FILES = ["LICENSE.txt", "RECORDS", "ECGPCGSpreadsheet.csv"]
CHUNK_BYTES = 1 << 20
RETRY_COUNT = 4
USER_AGENT = "heart-filter-study-downloader/1.0"

manifest_lock = threading.Lock()


def fetch_bytes(relative_path):
    last_error = None
    for base_url in (PRIMARY_BASE_URL, CANONICAL_BASE_URL):
        try:
            request = urllib.request.Request(base_url + relative_path, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read(), base_url
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
    raise RuntimeError(f"could not fetch {relative_path}: {last_error}")


def sha256_of_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK_BYTES * 4), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_checksums(text):
    checksums = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})\s+\*?(\S.*)", line.strip())
        if match:
            checksums[match.group(2)] = match.group(1)
    return checksums


def safe_target_path(relative_path):
    # Checked textually: Path.resolve() on Windows gave a spurious mismatch while another
    # download thread was creating the same directory.
    parts = PurePosixPath(relative_path).parts
    if (
        not parts
        or PurePosixPath(relative_path).is_absolute()
        or any(part in ("", ".", "..") or not re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in parts)
    ):
        raise ValueError(f"refusing unexpected path from checksum list: {relative_path}")
    return TARGET_DIRECTORY.joinpath(*parts)


class Manifest:
    def __init__(self, path):
        self.path = path
        self.data = {
            "source_url": CANONICAL_BASE_URL,
            "mirror_url": PRIMARY_BASE_URL,
            "database": "EPHNOGRAM",
            "header_comment": "The simultaneous electrocardiogram and phonocardiogram database",
            "version": DATABASE_VERSION,
            "doi": DATABASE_DOI,
            "licence": DATABASE_LICENCE,
            "licence_note": "LICENSE.txt holds the ODC Attribution License (ODC-By) text without a version number; v1.0 is taken from the PhysioNet project page",
            "access_dates": [],
            "files": {},
        }
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            self.data["access_dates"] = stored.get("access_dates", [])
            self.data["files"] = stored.get("files", {})
            if "priority_records" in stored:
                self.data["priority_records"] = stored["priority_records"]

    def record_access_date(self):
        today = datetime.date.today().isoformat()
        if today not in self.data["access_dates"]:
            self.data["access_dates"].append(today)

    def entry(self, relative_path):
        return self.data["files"].get(relative_path)

    def set_entry(self, relative_path, **fields):
        with manifest_lock:
            self.data["files"][relative_path] = fields
            self.save_locked()

    def save_locked(self):
        self.data["files"] = dict(sorted(self.data["files"].items()))
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def save(self):
        with manifest_lock:
            self.save_locked()


def already_verified(manifest, relative_path, expected_sha256):
    target = safe_target_path(relative_path)
    if not target.exists():
        return False
    entry = manifest.entry(relative_path)
    status = target.stat()
    if (
        entry
        and entry.get("verified")
        and entry.get("sha256") == expected_sha256
        and entry.get("size_bytes") == status.st_size
        and entry.get("modified_time_ns") == status.st_mtime_ns
    ):
        return True
    actual = sha256_of_file(target)
    verified = actual == expected_sha256
    manifest.set_entry(
        relative_path,
        size_bytes=status.st_size,
        sha256=actual,
        expected_sha256=expected_sha256,
        verified=verified,
        modified_time_ns=status.st_mtime_ns,
    )
    return verified


def download_file(manifest, relative_path, expected_sha256, statistics):
    if already_verified(manifest, relative_path, expected_sha256):
        return relative_path, True, 0
    target = safe_target_path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    partial = target.with_name(target.name + ".part")
    transferred = 0
    for attempt in range(RETRY_COUNT):
        offset = partial.stat().st_size if partial.exists() else 0
        headers = {"User-Agent": USER_AGENT}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        try:
            request = urllib.request.Request(PRIMARY_BASE_URL + relative_path, headers=headers)
            with urllib.request.urlopen(request, timeout=60) as response:
                if offset and response.status != 206:
                    offset = 0
                with open(partial, "ab" if offset else "wb") as handle:
                    for block in iter(lambda: response.read(CHUNK_BYTES), b""):
                        handle.write(block)
                        transferred += len(block)
                        statistics.add(len(block))
            break
        except urllib.error.HTTPError as error:
            if error.code == 416:
                break
            print(f"  retry {attempt + 1} {relative_path}: {error}", flush=True)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            print(f"  retry {attempt + 1} {relative_path}: {error}", flush=True)
        time.sleep(2 * (attempt + 1))
    if not partial.exists():
        return relative_path, False, transferred
    actual = sha256_of_file(partial)
    verified = actual == expected_sha256
    if verified:
        partial.replace(target)
        status = target.stat()
        manifest.set_entry(
            relative_path,
            size_bytes=status.st_size,
            sha256=actual,
            expected_sha256=expected_sha256,
            verified=True,
            modified_time_ns=status.st_mtime_ns,
        )
    else:
        print(f"  checksum mismatch {relative_path}; discarding partial file", flush=True)
        partial.unlink()
        manifest.set_entry(relative_path, size_bytes=0, sha256=actual, expected_sha256=expected_sha256, verified=False)
    return relative_path, verified, transferred


class TransferStatistics:
    def __init__(self):
        self.lock = threading.Lock()
        self.bytes_total = 0
        self.started = time.monotonic()

    def add(self, count):
        with self.lock:
            self.bytes_total += count

    def rate_megabytes_per_second(self):
        elapsed = max(time.monotonic() - self.started, 1e-6)
        return self.bytes_total / elapsed / 1e6


def normalise_scenario(text):
    return re.sub(r"\s*;\s*", "; ", " ".join(text.split())).strip()


def quality_score(note):
    note = note.strip().lower()
    if note == "good":
        return 2
    if note.startswith("good"):
        return 1
    return 0


def read_spreadsheet(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if not row.get("Record Name"):
                continue
            rows.append(row)
    return rows


def priority_order(spreadsheet_rows):
    """Return (priority record names, remaining record names)."""
    def score(row):
        return quality_score(row["ECG Notes"]) + quality_score(row["PCG Notes"])

    def channel_count(row):
        return int(row["Num Channels"])

    short_rest = [row for row in spreadsheet_rows if float(row["Record Duration (min)"]) < 1]
    long_records = [row for row in spreadsheet_rows if float(row["Record Duration (min)"]) >= 1]
    uncovered_subjects = {row["Subject ID"] for row in long_records}
    uncovered_scenarios = {normalise_scenario(row["Recording Scenario"]) for row in long_records}
    chosen = []
    candidates = list(long_records)
    while uncovered_subjects or uncovered_scenarios:
        def gain(row):
            new_coverage = (row["Subject ID"] in uncovered_subjects) + (
                normalise_scenario(row["Recording Scenario"]) in uncovered_scenarios
            )
            return (new_coverage, score(row), -channel_count(row))

        best = max(candidates, key=gain)
        if gain(best)[0] == 0:
            break
        chosen.append(best)
        candidates.remove(best)
        uncovered_subjects.discard(best["Subject ID"])
        uncovered_scenarios.discard(normalise_scenario(best["Recording Scenario"]))
    remaining = sorted(candidates, key=lambda row: (-score(row), channel_count(row), row["Record Name"]))
    priority = [row["Record Name"] for row in short_rest] + [row["Record Name"] for row in chosen]
    return priority, [row["Record Name"] for row in remaining]


def parse_stop_time(text):
    if not text:
        return None
    hour, minute = (int(part) for part in text.split(":"))
    return datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)


def run_batch(manifest, checksums, relative_paths, workers, statistics, stop_time):
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {}
        queue = list(relative_paths)
        while queue or pending:
            while queue and len(pending) < workers:
                if stop_time and datetime.datetime.now() >= stop_time:
                    print(f"stop time reached; not starting {len(queue)} further files", flush=True)
                    queue.clear()
                    break
                relative_path = queue.pop(0)
                future = executor.submit(download_file, manifest, relative_path, checksums[relative_path], statistics)
                pending[future] = relative_path
            if not pending:
                break
            finished = next(as_completed(pending))
            relative_path = pending.pop(finished)
            try:
                _, verified, transferred = finished.result()
            except Exception as error:  # noqa: BLE001 - one failed file must not stop the batch
                print(f"  failed {relative_path}: {error}", flush=True)
                verified, transferred = False, 0
            results[relative_path] = verified
            print(
                f"{'ok ' if verified else 'BAD'} {relative_path} {transferred / 1e6:7.1f} MB  "
                f"total {statistics.bytes_total / 1e6:8.1f} MB at {statistics.rate_megabytes_per_second():5.2f} MB/s",
                flush=True,
            )
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stop-new-at", help="local time HH:MM after which no new file is started")
    parser.add_argument("--workers", type=int, default=4)
    arguments = parser.parse_args()
    stop_time = parse_stop_time(arguments.stop_new_at)

    TARGET_DIRECTORY.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(TARGET_DIRECTORY / "MANIFEST.json")
    manifest.record_access_date()

    checksum_bytes, checksum_source = fetch_bytes("SHA256SUMS.txt")
    cross_check_bytes = None
    try:
        request = urllib.request.Request(CANONICAL_BASE_URL + "SHA256SUMS.txt", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            cross_check_bytes = response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"could not cross-check SHA256SUMS.txt against {CANONICAL_BASE_URL}: {error}", flush=True)
    checksum_path = safe_target_path("SHA256SUMS.txt")
    checksum_path.write_bytes(checksum_bytes)
    checksum_status = checksum_path.stat()
    manifest.set_entry(
        "SHA256SUMS.txt",
        size_bytes=checksum_status.st_size,
        sha256=hashlib.sha256(checksum_bytes).hexdigest(),
        verified=cross_check_bytes == checksum_bytes,
        verification="identical copy from both mirrors" if cross_check_bytes == checksum_bytes
        else "not verifiable: checksum list itself, mirrors not compared",
        fetched_from=checksum_source,
        modified_time_ns=checksum_status.st_mtime_ns,
    )
    checksums = parse_checksums(checksum_bytes.decode("utf-8"))
    print(f"{len(checksums)} checksummed files in source", flush=True)

    statistics = TransferStatistics()
    header_paths = sorted(path for path in checksums if path.startswith("WFDB/") and path.endswith(".hea"))
    small_results = run_batch(manifest, checksums, SMALL_INDEX_FILES + header_paths, 8, statistics, None)

    spreadsheet_rows = read_spreadsheet(safe_target_path("ECGPCGSpreadsheet.csv"))
    priority, remaining = priority_order(spreadsheet_rows)
    print("priority records:", " ".join(priority), flush=True)
    priority_paths = [f"WFDB/{name}.dat" for name in priority]
    remaining_paths = [f"WFDB/{name}.dat" for name in remaining]
    for path in priority_paths + remaining_paths:
        if path not in checksums:
            raise SystemExit(f"{path} is missing in SHA256SUMS.txt")

    priority_results = run_batch(manifest, checksums, priority_paths, arguments.workers, statistics, stop_time)
    priority_complete = all(small_results.values()) and all(
        priority_results.get(path) for path in priority_paths
    )
    manifest.data["priority_records"] = priority
    manifest.save()
    if priority_complete:
        (TARGET_DIRECTORY / "READY").touch()
        print("priority set verified; READY written", flush=True)

    run_batch(manifest, checksums, remaining_paths, arguments.workers, statistics, stop_time)
    manifest.save()
    verified_data = [
        path for path, entry in manifest.data["files"].items() if path.endswith(".dat") and entry.get("verified")
    ]
    print(
        f"done: {len(verified_data)} of {len(priority_paths) + len(remaining_paths)} .dat files verified; "
        f"{statistics.bytes_total / 1e6:.1f} MB transferred at {statistics.rate_megabytes_per_second():.2f} MB/s",
        flush=True,
    )


if __name__ == "__main__":
    main()
