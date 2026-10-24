"""Reject incomplete or misleading manual execution evidence."""

from copy import deepcopy
import json
import unittest

from manual_test_records import TEMPLATE, validate


class ManualRecordTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "test_id": "P22",
            "procedure": "testing/system/P22-final-legibility.md",
            "procedure_sha": "1" * 40,
            "device": "fixture-device",
            "firmware_build": "local fixture application",
            "firmware_sha": "2" * 40,
            "configuration": "Fixture only; not an executed run",
            "steps": [
                {
                    "id": "1",
                    "action": "Show code",
                    "expected": "Identify code",
                    "result": "pass",
                    "observations": "Correct identification",
                }
            ],
            "result": "pass",
            "sign_off": {
                "name": "Nico",
                "date": "2026-10-24T14:00:00+02:00",
                "signature_reference": "fixture-signature",
            },
        }

    def test_complete_signed_record(self):
        self.assertEqual(validate(self.record), [])

    def test_identity_observations_and_sign_off_are_required(self):
        for field in (
            "device",
            "firmware_build",
            "firmware_sha",
            "procedure_sha",
            "sign_off",
        ):
            record = deepcopy(self.record)
            del record[field]
            self.assertTrue(validate(record), field)
        for field in ("action", "expected", "observations"):
            record = deepcopy(self.record)
            record["steps"][0][field] = ""
            self.assertTrue(validate(record), field)

    def test_incomplete_or_failed_steps_cannot_pass(self):
        for outcome, expected in (
            ("fail", "fail"),
            ("blocked", "blocked"),
            ("not-run", "blocked"),
        ):
            record = deepcopy(self.record)
            record["steps"][0]["result"] = outcome
            self.assertTrue(validate(record))
            record["result"] = expected
            self.assertEqual(validate(record), [])

    def test_duplicate_steps_and_non_nico_signatures_fail(self):
        record = deepcopy(self.record)
        record["steps"].append(record["steps"][0])
        self.assertTrue(validate(record))
        for field, value in (
            ("name", "Agent"),
            ("date", "2026-10-24"),
            ("signature_reference", ""),
        ):
            record = deepcopy(self.record)
            record["sign_off"][field] = value
            self.assertTrue(validate(record))

    def test_template_placeholders_fail(self):
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        for field in (
            "test_id",
            "procedure",
            "device",
            "firmware_build",
            "configuration",
        ):
            record = deepcopy(self.record)
            record[field] = template[field]
            self.assertIn(
                f"{field} still holds the template placeholder", validate(record)
            )
        for field in ("action", "expected", "observations"):
            record = deepcopy(self.record)
            record["steps"][0][field] = template["steps"][0][field]
            self.assertIn(
                f"step 1: {field} still holds the template placeholder",
                validate(record),
            )

    def test_wrong_shapes_fail(self):
        for record in (None, [], {"steps": "pass"}, {"steps": [None]}, {"steps": []}):
            self.assertTrue(validate(record))
