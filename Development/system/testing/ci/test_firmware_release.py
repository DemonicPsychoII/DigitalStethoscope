"""Build identity and release staging shared by the boot banner and cloud uploads."""

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import firmware_release

NOW = datetime(2026, 10, 2, 3, 17, 5, tzinfo=timezone.utc)
HEAD = "b" * 40


def fake_git(branch="feat/x", dirty=""):
    answers = {
        ("rev-parse", "HEAD"): HEAD,
        ("rev-parse", "--abbrev-ref", "HEAD"): branch,
        ("status", "--porcelain", "--untracked-files=no"): dirty,
    }
    return lambda root, *args: answers[args]


class IdentityTests(unittest.TestCase):
    def test_local_build_defaults_to_local_channel_and_marks_dirty(self):
        with patch.object(firmware_release, "git", fake_git(dirty=" M src/main.c")):
            build = firmware_release.identity(Path("."), {}, NOW)
        self.assertEqual(
            (build.channel, build.commit, build.merge_commit, build.branch),
            ("local", HEAD, None, "feat/x"),
        )
        self.assertEqual(
            build.version("qc"), f"local {HEAD[:12]}-dirty qc 20261002T031705Z"
        )
        self.assertEqual(
            build.cmake_arg("qc"),
            f"-DSTETHO_BUILD_ID=local {HEAD[:12]}-dirty qc 20261002T031705Z",
        )

    def test_pr_build_names_the_head_commit_and_records_the_merged_tree(self):
        environ = {"STETHO_BUILD_CHANNEL": "pr-12", "STETHO_BUILD_COMMIT": "a" * 40}
        with patch.object(firmware_release, "git", fake_git(branch="HEAD")):
            build = firmware_release.identity(Path("."), environ, NOW)
        self.assertEqual(
            (build.commit, build.merge_commit, build.branch), ("a" * 40, HEAD, None)
        )
        self.assertEqual(
            build.version("offline"), f"pr-12 {'a' * 12}+merge offline 20261002T031705Z"
        )

    def test_unusual_branch_channels_stay_within_the_cmake_character_set(self):
        environ = {
            "STETHO_BUILD_CHANNEL": "branch/feat@x#1",
            "STETHO_BUILD_COMMIT": HEAD,
        }
        with patch.object(firmware_release, "git", fake_git(branch="feat@x#1")):
            build = firmware_release.identity(Path("."), environ, NOW)
        self.assertRegex(build.version("qc"), r"^[A-Za-z0-9 ._:+/-]+$")
        self.assertIsNone(build.branch)

    def test_short_or_foreign_commit_is_refused(self):
        with (
            patch.object(firmware_release, "git", fake_git()),
            self.assertRaises(SystemExit),
        ):
            firmware_release.identity(Path("."), {"STETHO_BUILD_COMMIT": "abc123"}, NOW)


class StageTests(unittest.TestCase):
    def test_manifest_lists_every_profile_with_its_checksum(self):
        build = firmware_release.Identity(
            "branch/feat/x", HEAD, None, False, "2026-10-02T03:17:05Z", None
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = []
            for profile in ("offline", "qc"):
                (root / profile).write_bytes(profile.encode())
                outputs.append((profile, root / profile))
            (root / "release").mkdir()
            (root / "release" / "stale.bin").write_bytes(b"old")
            manifest = firmware_release.stage(build, outputs, root / "release", "board")
            written = json.loads((root / "release/manifest.json").read_text())
            names = sorted(path.name for path in (root / "release").iterdir())
        self.assertEqual(manifest, written)
        self.assertEqual(
            names,
            [
                "manifest.json",
                f"stethoscope-branch-feat-x-{HEAD[:12]}-offline.bin",
                f"stethoscope-branch-feat-x-{HEAD[:12]}-qc.bin",
            ],
        )
        self.assertEqual(
            manifest["files"][1]["sha256"], hashlib.sha256(b"qc").hexdigest()
        )
        self.assertEqual(manifest["files"][1]["version"], build.version("qc"))
        self.assertEqual(
            (manifest["commit"], manifest["merge_commit"], manifest["dirty"]),
            (HEAD, None, False),
        )


if __name__ == "__main__":
    unittest.main()
