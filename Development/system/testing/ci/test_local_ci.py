import json
import shlex
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import local_ci
import toolchain_path  # noqa: F401
from build_support import (
    PIN_STAMP,
    PINS,
    PREPARED_MARKER,
    sdk_directory,
    toolchain_problems,
    workspace_matches_pins,
)


def elf_image(notes: bytes) -> bytes:
    """A minimal little-endian ELF32 image with one SHT_NOTE section."""
    header_size = 52
    section_offset = header_size + len(notes)
    identification = b"\x7fELF" + bytes([1, 1, 1]) + bytes(9)
    header = identification + struct.pack(
        "<HHIIIIIHHHHHH", 2, 94, 1, 0, 0, section_offset, 0, header_size, 0, 0, 40, 2, 0
    )
    null_section = bytes(40)
    note_section = struct.pack(
        "<IIIIIIIIII", 0, 7, 0, 0, header_size, len(notes), 0, 0, 4, 0
    )
    return header + notes + null_section + note_section


def note(name: bytes, note_type: int, description: bytes) -> bytes:
    padded_name = name + bytes(-len(name) % 4)
    padded_description = description + bytes(-len(description) % 4)
    return (
        struct.pack("<III", len(name), len(description), note_type)
        + padded_name
        + padded_description
    )


class FirmwareIdentityTest(unittest.TestCase):
    def test_reads_the_gnu_build_id_after_other_notes(self):
        build_id = bytes(range(20))
        image = elf_image(
            note(b"Xtensa_Info\0", 1, b"ABI=0\n\0\0") + note(b"GNU\0", 3, build_id)
        )
        self.assertEqual(local_ci.gnu_build_id(image), build_id.hex())

    def test_reports_no_build_id_for_an_image_linked_without_one(self):
        image = elf_image(note(b"Xtensa_Info\0", 1, b"ABI=0\n\0\0"))
        self.assertIsNone(local_ci.gnu_build_id(image))
        self.assertIsNone(local_ci.gnu_build_id(b"not an ELF image"))


class SharedWorkspaceTest(unittest.TestCase):
    def test_reuses_only_workspaces_recorded_with_the_current_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self.assertFalse(workspace_matches_pins(workspace))
            (workspace / PIN_STAMP).write_text(json.dumps({"pins": {**PINS, "x": 1}}))
            self.assertFalse(workspace_matches_pins(workspace))
            (workspace / PREPARED_MARKER).write_text(json.dumps({"pins": PINS}))
            self.assertTrue(workspace_matches_pins(workspace))

    def test_a_marker_that_is_not_an_object_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / PIN_STAMP).write_text("[]")
            (workspace / PREPARED_MARKER).write_text("null")
            self.assertFalse(workspace_matches_pins(workspace))

    def test_an_sdk_reused_from_elsewhere_is_taken_from_the_record(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            reused = Path(directory) / "other" / f"zephyr-sdk-{PINS['sdk_version']}"
            workspace.mkdir()
            reused.mkdir(parents=True)
            (reused / "sdk_version").write_text(PINS["sdk_version"])
            local = workspace / f"zephyr-sdk-{PINS['sdk_version']}"
            self.assertEqual(sdk_directory(workspace), local)
            (workspace / PIN_STAMP).write_text(
                json.dumps({"pins": PINS, "sdk": str(reused)})
            )
            self.assertEqual(sdk_directory(workspace), reused)
            local.mkdir()
            (local / "sdk_version").write_text(PINS["sdk_version"])
            self.assertEqual(sdk_directory(workspace), local)

    def test_an_incomplete_or_unrecorded_workspace_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            problems = toolchain_problems(Path(directory))
            self.assertIn("west missing", problems)
            self.assertIn("SDK compiler missing", problems)
            self.assertIn("no record of the current toolchain.json pins", problems)


class PlacementTest(unittest.TestCase):
    def test_auto_mode_sends_only_blocked_stages_to_the_annex(self):
        blockers = {"host": "no C compiler"}
        with (
            mock.patch.object(
                local_ci, "native_blocker", lambda stage, _: blockers.get(stage)
            ),
            mock.patch.object(local_ci.socket, "gethostname", return_value="talos"),
        ):
            self.assertEqual(
                local_ci.plan(["static", "host"], "auto", False),
                {"static": "native", "host": "remote"},
            )
            self.assertEqual(
                local_ci.plan(["static", "host"], "native", False),
                {"static": "native", "host": "native"},
            )

    def test_the_annex_never_sends_stages_to_itself(self):
        with (
            mock.patch.object(local_ci, "native_blocker", return_value="missing"),
            mock.patch.object(
                local_ci.socket, "gethostname", return_value=local_ci.REMOTE_HOST
            ),
        ):
            self.assertEqual(
                local_ci.plan(["build"], "auto", False), {"build": "native"}
            )


class AnnexHoldTest(unittest.TestCase):
    def test_keeps_only_when_no_hold_lasts_long_enough(self):
        now = 1_000_000.0
        with mock.patch.object(local_ci.time, "time", return_value=now):
            calls = []
            ends = iter([now + 7200])

            def annex_power(*arguments, report=False):
                calls.append(arguments)
                return {"idle": {"hold_until": next(ends)}} if report else None

            hold = local_ci.AnnexHold(60)
            with mock.patch.object(local_ci, "annex_power", annex_power):
                hold.ensure()
                hold.release()
        self.assertEqual(calls, [("status",)])
        self.assertIsNone(hold.owned_until)

    def test_releases_only_a_hold_it_still_owns(self):
        now = 1_000_000.0
        for later_hold, released in ((now + 3600, True), (now + 5000, False)):
            calls = []
            ends = iter([None, now + 3600, later_hold])

            def annex_power(*arguments, report=False):
                calls.append(arguments)
                return {"idle": {"hold_until": next(ends)}} if report else None

            hold = local_ci.AnnexHold(60)
            with (
                mock.patch.object(local_ci.time, "time", return_value=now),
                mock.patch.object(local_ci, "annex_power", annex_power),
            ):
                hold.ensure()
                hold.release()
            self.assertIn(("keep", "60"), calls)
            self.assertEqual(("release",) in calls, released)


class RemoteFollowTest(unittest.TestCase):
    def test_a_failed_hold_renewal_does_not_end_the_run(self):
        answers = iter([b"building\n\x1erunning", b"done\n\x1e0"])
        clock = iter(range(0, 100_000, 1000))
        hold = local_ci.AnnexHold(1)
        with (
            mock.patch.object(
                local_ci,
                "ssh",
                lambda *arguments, **options: subprocess.CompletedProcess(
                    [], 0, next(answers), b""
                ),
            ),
            mock.patch.object(
                hold, "ensure", side_effect=local_ci.StageFailure("coordinator down")
            ) as renewal,
            mock.patch.object(local_ci.time, "monotonic", lambda: next(clock)),
            mock.patch.object(local_ci.time, "sleep"),
            mock.patch("sys.stdout"),
        ):
            self.assertEqual(local_ci.remote_follow("scratch", hold), 0)
        renewal.assert_called_once()


class FollowTest(unittest.TestCase):
    def test_a_run_whose_process_is_gone_is_reported_lost(self):
        with tempfile.TemporaryDirectory() as directory:
            runs = Path(directory)
            run = runs / "run"
            run.mkdir()
            (run / "progress.log").write_text("started\n")
            (run / "pid").write_text("4242\n")
            with (
                mock.patch.object(local_ci, "RUNS", runs),
                mock.patch.object(local_ci, "process_alive", return_value=False),
                mock.patch("sys.stdout"),
            ):
                self.assertEqual(
                    local_ci.follow("run", timeout=5, from_start=True),
                    local_ci.RUN_LOST,
                )

    def test_an_unknown_run_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(local_ci, "RUNS", Path(directory)):
                with self.assertRaises(SystemExit) as raised:
                    local_ci.follow("missing", timeout=1, from_start=False)
        self.assertIn("unknown run missing", str(raised.exception))


@unittest.skipUnless(sys.platform.startswith("linux"), "process groups as on the annex")
class RemoteCleanupTest(unittest.TestCase):
    def test_a_member_that_handles_term_finishes_before_kill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scratch = root / "scratch"
            scratch.mkdir()
            ready = root / "ready"
            finished = root / "finished"
            # Like python under the remote wrapper: it needs a moment to unwind on TERM.
            member = (
                f"trap 'sleep 1; echo graceful > {shlex.quote(str(finished))}; exit 0' TERM; "
                f": > {shlex.quote(str(ready))}; "
                "while true; do sleep 0.1; done"
            )
            wrapper = (
                f"echo $$ > pid; bash -c {shlex.quote(member)}; echo $? > exit-code"
            )
            process = subprocess.Popen(
                ["bash", "-c", wrapper], cwd=scratch, start_new_session=True
            )
            # On the annex init reaps the wrapper; here a waiting thread does.
            reaper = threading.Thread(target=process.wait)
            reaper.start()
            deadline = time.monotonic() + 10
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(ready.exists(), "member did not install its TERM trap")
            script = local_ci.cleanup_script(shlex.quote(str(scratch)))
            subprocess.run(["bash", "-c", script], check=True, timeout=30)
            reaper.join(timeout=10)
            self.assertEqual(finished.read_text().strip(), "graceful")
            self.assertFalse(scratch.exists())


if __name__ == "__main__":
    unittest.main()
