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


if __name__ == "__main__":
    unittest.main()
