"""Regression coverage for routing, fail-closed results, promotion and recovery."""

import copy
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from build_support import BOARD, PROFILES
from ci_results import problems
from firmware_changes import suites
from firmware_release import PROJECT
from native_review import policy, probe
from native_tests import report
from post_merge import decision
from release_reuse import eligible, extract

SHA = "a" * 40


class OverhaulTests(unittest.TestCase):
    def test_native_only_change_skips_target_profiles(self):
        selected = suites(
            ["Development/system/coding/bringup-zephyr/tests/logic/src/main.c"]
        )
        self.assertTrue(selected["native"])
        self.assertFalse(selected["firmware"])
        self.assertFalse(selected["host"])

    def test_accounting_rejects_missing_failed_cancelled_and_unexpected_work(self):
        self.assertFalse(
            problems("success", "success", "skipped", "false", "false", "false", "true")
        )
        for heavy in ("skipped", "failure", "cancelled"):
            self.assertTrue(
                problems("success", "success", heavy, "false", "true", "false", "true")
            )
        self.assertTrue(
            problems("success", "success", "skipped", "", "false", "false", "true")
        )
        self.assertTrue(
            problems("failure", "success", "success", "true", "true", "false", "true")
        )
        self.assertTrue(
            problems("success", "failure", "success", "true", "true", "false", "true")
        )
        self.assertFalse(
            problems("success", "skipped", "skipped", "true", "true", "true", "false")
        )
        self.assertFalse(
            problems(
                "success", "success", "skipped", "false", "false", "true", "true", "123"
            )
        )

    def test_recovery_requires_repeated_verification_failure(self):
        failed = {"run_attempt": 1, "conclusion": "failure"}
        rerun = {"run_attempt": 2, "conclusion": "failure"}
        jobs = [
            {"steps": [{"name": "Pristine firmware build", "conclusion": "failure"}]}
        ]
        setup = [
            {
                "steps": [
                    {
                        "name": "Provision pinned Zephyr workspace",
                        "conclusion": "failure",
                    }
                ]
            }
        ]
        self.assertEqual(decision(failed, failed, jobs, jobs), "rerun")
        self.assertEqual(decision(failed, rerun, jobs, jobs), "confirmed")
        self.assertEqual(
            decision(failed, rerun, setup, setup), "infrastructure-or-unconfirmed"
        )
        self.assertEqual(
            decision(failed, rerun, jobs, setup), "infrastructure-or-unconfirmed"
        )
        self.assertEqual(
            decision(failed, {**rerun, "conclusion": "success"}, jobs, []), "recovered"
        )

    def test_promotion_rejects_other_runs_and_malformed_archives(self):
        run = {
            "status": "completed",
            "conclusion": "success",
            "event": "push",
            "head_branch": "integration",
            "head_sha": SHA,
            "path": ".github/workflows/quality-gates.yml",
            "head_repository": {"full_name": "o/r"},
        }
        self.assertTrue(eligible(run, "o/r", SHA))
        for key, value in (
            ("head_sha", "b" * 40),
            ("event", "pull_request"),
            ("conclusion", "failure"),
            ("head_branch", "other"),
        ):
            self.assertFalse(eligible({**run, key: value}, "o/r", SHA))
        manifest = {
            "schema": 1,
            "project": PROJECT,
            "commit": SHA,
            "board": BOARD,
            "dirty": False,
            "channel": "integration",
            "merge_commit": None,
            "files": [
                {
                    "profile": p,
                    "name": p + ".bin",
                    "sha256": hashlib.sha256(p.encode()).hexdigest(),
                }
                for p in PROFILES
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for bad in (None, "dirty", "checksum", "extra", "identity"):
                current = copy.deepcopy(manifest)
                if bad == "dirty":
                    current["dirty"] = True
                if bad == "checksum":
                    current["files"][0]["sha256"] = "0" * 64
                if bad == "identity":
                    current["commit"] = "b" * 40
                archive = root / "test.zip"
                with zipfile.ZipFile(archive, "w") as stream:
                    stream.writestr("manifest.json", json.dumps(current))
                    for p in PROFILES:
                        stream.writestr(p + ".bin", p)
                    if bad == "extra":
                        stream.writestr("../escape", "unexpected")
                if bad:
                    with self.assertRaises(ValueError):
                        extract(archive, root / bad, SHA)
                    self.assertFalse((root / bad).exists())
                else:
                    extract(archive, root / "valid", SHA)
                    self.assertTrue((root / "valid/offline.bin").is_file())

    def test_empty_native_success_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "junit.xml"
            with self.assertRaises(RuntimeError):
                report("PROJECT EXECUTION SUCCESSFUL", 0, target)
            self.assertIn('failures="1"', target.read_text())
            report("PASS - test_recovery\nPROJECT EXECUTION SUCCESSFUL", 0, target)
            self.assertIn('failures="0"', target.read_text())

    def test_native_migration_preserves_other_checks_and_requires_current_review(self):
        source = {
            "name": "protect",
            "target": "branch",
            "enforcement": "active",
            "conditions": {},
            "rules": [
                {"type": "pull_request", "parameters": {}},
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "required_status_checks": [
                            {"context": "agent-gate", "integration_id": 15368},
                            {
                                "context": "Quality / Static Checks",
                                "integration_id": 15368,
                            },
                        ]
                    },
                },
            ],
        }
        prepared = policy(source)
        self.assertEqual(
            len(prepared["rules"][1]["parameters"]["required_status_checks"]), 2
        )
        retired = policy(source, True)
        self.assertEqual(
            retired["rules"][1]["parameters"]["required_status_checks"],
            [{"context": "Quality / Static Checks", "integration_id": 15368}],
        )
        pr = {
            "baseRefName": "integration",
            "state": "OPEN",
            "isDraft": False,
            "reviewDecision": "APPROVED",
            "author": {"login": "author"},
            "headRefOid": SHA,
            "reviews": [
                {
                    "author": {"login": "fallback"},
                    "state": "APPROVED",
                    "commit": {"oid": SHA},
                }
            ],
        }
        probe(pr, "fallback")
        commented = {
            "author": {"login": "fallback"},
            "state": "COMMENTED",
            "commit": {"oid": SHA},
        }
        probe({**pr, "reviews": [*pr["reviews"], commented]}, "fallback")
        with self.assertRaises(ValueError):
            probe(
                {
                    **pr,
                    "reviews": [
                        *pr["reviews"],
                        {**pr["reviews"][0], "author": {"login": "another"}},
                    ],
                },
                "fallback",
            )
        with self.assertRaises(ValueError):
            probe({**pr, "headRefOid": "b" * 40}, "fallback")
        with self.assertRaises(ValueError):
            probe({**pr, "author": {"login": "fallback"}}, "fallback")
