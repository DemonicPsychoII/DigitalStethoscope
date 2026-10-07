"""Changed pins, packages and missing prepared files fall back to provisioning."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import prepared_env as p


class PreparedTests(unittest.TestCase):
    def test_static_reuse_requires_exact_requirements_and_installed_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in p.STATIC_REQUIREMENTS:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("a==1 --hash=sha256:abc\n")
            installed = {"python": p.STATIC_PYTHON, "packages": {"a": "1"}}
            with (
                patch.object(p, "ROOT", root),
                patch.object(p, "python_state", return_value=installed),
            ):
                self.assertFalse(p.ready("static", root))
                p.record("static", root)
                self.assertTrue(p.ready("static", root))
                installed["packages"]["a"] = "2"
                self.assertFalse(p.ready("static", root))
                installed["packages"]["a"] = "1"
                (root / p.STATIC_REQUIREMENTS[0]).write_text("a==2\n")
                self.assertFalse(p.ready("static", root))

    def test_wrong_python_and_corrupt_or_missing_marker_fall_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / p.MARKER).write_text("broken json")
            self.assertFalse(p.ready("static", root))
            with patch.object(
                p, "python_state", return_value={"python": "3.11", "packages": {}}
            ):
                with self.assertRaises(ValueError):
                    p.record("static", root)

    def test_zephyr_reuse_checks_actual_sdk_and_blob_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            compiler = (
                root
                / f"zephyr-sdk-{p.PINS['sdk_version']}"
                / "gnu"
                / p.PINS["toolchain"]
                / "bin"
                / f"{p.PINS['toolchain']}-gcc"
            )
            compiler.parent.mkdir(parents=True)
            compiler.write_bytes(b"compiler")
            blobs = root / "hal_espressif/zephyr/blobs"
            blobs.mkdir(parents=True)
            blob = blobs / "radio.a"
            blob.write_bytes(b"blob")
            packages = {
                name: p.PINS[pin]
                for name, pin in [
                    ("west", "west_version"),
                    ("cmake", "cmake_version"),
                    ("ninja", "ninja_version"),
                    ("esptool", "esptool_version"),
                ]
            }
            listing = "\n".join(f"{name}|{name}" for name in p.PINS["modules"])
            with (
                patch.object(p.sys, "platform", "linux"),
                patch.object(
                    p,
                    "python_state",
                    return_value={"python": "3.12.3", "packages": packages},
                ),
                patch.object(p, "git_head", return_value=p.PINS["zephyr_revision"]),
                patch.object(p.subprocess, "check_output", return_value=listing),
            ):
                p.record("zephyr", root)
                self.assertTrue(p.ready("zephyr", root))
                blob.write_bytes(b"changed")
                self.assertFalse(p.ready("zephyr", root))
                blob.write_bytes(b"blob")
                compiler.unlink()
                self.assertFalse(p.ready("zephyr", root))
                compiler.with_suffix(".exe").write_bytes(b"compiler")
                with patch.object(p.sys, "platform", "win32"):
                    self.assertTrue(p.ready("zephyr", root))

    def test_changed_toolchain_state_invalidates_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = {
                "pins": {"revision": "a"},
                "modules": {"hal": "a"},
                "blobs": {"lib": "a"},
            }
            with patch.object(p, "state", return_value=state):
                p.record("zephyr", root)
                self.assertTrue(p.ready("zephyr", root))
                state["modules"]["hal"] = "b"
                self.assertFalse(p.ready("zephyr", root))
            with patch.object(
                p, "state", side_effect=ValueError("missing SDK or blobs")
            ):
                self.assertFalse(p.ready("zephyr", root))


if __name__ == "__main__":
    unittest.main()
