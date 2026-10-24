"""Prepared validators must retain checked-out pins and intact binary content."""

import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validation_tools as tools


class ValidatorTests(unittest.TestCase):
    def test_matching_prepared_binary_avoids_network_and_changed_pins_fall_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = io.BytesIO()
            with tarfile.open(fileobj=archive, mode="w:gz") as stream:
                info = tarfile.TarInfo("validator")
                info.size = 6
                stream.addfile(info, io.BytesIO(b"binary"))
            payload = archive.getvalue()
            pin = {
                "url": "https://example.invalid/tool",
                "member": "validator",
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            prepared = root / "prepared"
            response = io.BytesIO(payload)
            with patch.object(tools.urllib.request, "urlopen", return_value=response):
                tools.install({"validator": pin}, prepared)
            with patch.object(tools.urllib.request, "urlopen") as network:
                tools.install({"validator": pin}, root / "job", prepared)
                network.assert_not_called()
            self.assertEqual((root / "job/validator").read_bytes(), b"binary")
            self.assertIsNone(
                tools.prepared_binary(
                    prepared, "validator", pin | {"version": "changed"}
                )
            )
            (prepared / "validator").write_bytes(b"tampered")
            self.assertIsNone(tools.prepared_binary(prepared, "validator", pin))
            (prepared / "manifest.json").write_text(json.dumps({}))
            self.assertIsNone(tools.prepared_binary(prepared, "validator", pin))

    def test_bad_archive_checksum_and_nonregular_member_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "checksum"):
            tools.binary(b"archive", "0" * 64, "validator")
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w:gz") as stream:
            info = tarfile.TarInfo("validator")
            info.type = tarfile.SYMTYPE
            info.linkname = "outside"
            stream.addfile(info)
        payload = archive.getvalue()
        with self.assertRaisesRegex(ValueError, "regular file"):
            tools.binary(payload, hashlib.sha256(payload).hexdigest(), "validator")

    def test_download_and_prepared_binary_respect_pin_size_limits(self):
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w:xz") as stream:
            entry = tarfile.TarInfo("node")
            entry.size = 6
            stream.addfile(entry, io.BytesIO(b"binary"))
        payload = archive.getvalue()
        pin = {
            "url": "https://example.invalid/node",
            "member": "node",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "maximum_archive_bytes": len(payload),
            "maximum_binary_bytes": 6,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = root / "prepared"
            with patch.object(
                tools.urllib.request, "urlopen", return_value=io.BytesIO(payload)
            ):
                tools.install({"node": pin}, prepared)
            with patch.object(tools.urllib.request, "urlopen") as network:
                tools.install({"node": pin}, root / "job", prepared)
                network.assert_not_called()
            self.assertEqual((root / "job/node").read_bytes(), b"binary")
            with (
                patch.object(
                    tools.urllib.request, "urlopen", return_value=io.BytesIO(payload)
                ),
                self.assertRaisesRegex(ValueError, "archive exceeds size limit"),
            ):
                tools.install(
                    {"node": pin | {"maximum_archive_bytes": len(payload) - 1}}, root
                )
            with (
                patch.object(
                    tools.urllib.request, "urlopen", return_value=io.BytesIO(payload)
                ),
                self.assertRaisesRegex(ValueError, "bounded regular file"),
            ):
                tools.install({"node": pin | {"maximum_binary_bytes": 5}}, root)
            (prepared / "node").write_bytes(b"oversized")
            self.assertIsNone(tools.prepared_binary(prepared, "node", pin))

    def test_ci_uses_only_explicit_installed_node_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundled = root / "externals/node24_alpine/bin/node"
            bundled.parent.mkdir(parents=True)
            bundled.write_bytes(b"unusable musl runtime")
            with (
                patch.dict(
                    tools.os.environ,
                    {
                        "CI": "true",
                        "PATH": str(bundled.parent),
                        "STETHO_NODE": str(bundled),
                    },
                    clear=True,
                ),
                patch.object(tools.sys, "platform", "win32"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "Node is required.*validation_tools"
                ):
                    tools.node_runtime(root)
                installed = root / ".ci-validation-tools/node"
                installed.parent.mkdir()
                installed.write_bytes(b"pinned runtime")
                self.assertEqual(tools.node_runtime(root), installed)

    def test_windows_local_skip_and_explicit_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.dict(tools.os.environ, {}, clear=True),
                patch.object(tools.sys, "platform", "win32"),
            ):
                self.assertIsNone(tools.node_runtime(root))
                with patch.dict(tools.os.environ, {"STETHO_NODE": "node"}):
                    with self.assertRaisesRegex(RuntimeError, "absolute path"):
                        tools.node_runtime(root)
                runtime = root / "node.exe"
                with patch.dict(tools.os.environ, {"STETHO_NODE": str(runtime)}):
                    with self.assertRaisesRegex(RuntimeError, "Node is required"):
                        tools.node_runtime(root)
                    runtime.touch()
                    self.assertEqual(tools.node_runtime(root), runtime)


if __name__ == "__main__":
    unittest.main()
