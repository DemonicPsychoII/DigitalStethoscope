import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import local_ci
import toolchain_path  # noqa: F401
from build_support import PIN_STAMP, PINS, PREPARED_MARKER, workspace_matches_pins


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


if __name__ == "__main__":
    unittest.main()
