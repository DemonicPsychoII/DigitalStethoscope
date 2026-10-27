import base64
import json
import tempfile
import unittest
import zlib
from pathlib import Path

from validate_docs import (
    verification_coverage,
    PLANTUML_ALPHABET,
    SYSTEM,
    WORKFLOW,
    facts,
    line_anchor,
    listed,
    renders,
    supplemental_sources,
)

ENCODE = {v: k for k, v in PLANTUML_ALPHABET.items()}


def write(root: Path, path: str, text: str) -> str:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return path


def svg(body: str) -> str:
    deflate = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = deflate.compress(body.encode()) + deflate.flush()
    encoded = base64.b64encode(data).decode().rstrip("=").translate(ENCODE)
    return f"<svg><?plantuml-src {encoded}?></svg>"


class RenderTests(unittest.TestCase):
    def test_current_render_passes_and_stale_or_missing_render_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            puml = write(
                root, "a/view-one.puml", "@startuml view_one\nA -> B\n@enduml\n"
            )
            other = write(
                root, "a/view-two.puml", "@startuml view_two\nA -> C\n@enduml\n"
            )
            current = write(root, "a/rendered/view_one.svg", svg("A -> B"))
            self.assertEqual(renders([puml, current], root), [])
            write(root, current, svg("A -> C"))
            self.assertIn("stale render", renders([puml, current], root)[0])
            self.assertIn("missing render", renders([puml, other, current], root)[-1])


class IndexTests(unittest.TestCase):
    def test_unlisted_script_and_view_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ci = SYSTEM + "testing/ci/"
            arch = SYSTEM + "architecture/"
            write(root, ci + "OPERATIONS.md", "`listed.py`")
            write(root, arch + "README.md", "[v](view.puml)")
            write(root, arch + "system/VIEW-NOTES.md", "")
            paths = [ci + "listed.py", ci + "test_x.py", arch + "view.puml"]
            self.assertEqual(listed(paths, root), [])
            errors = listed([*paths, ci + "new.py", arch + "new.puml"], root)
            self.assertEqual(len(errors), 2)


class FactTests(unittest.TestCase):
    def tree(self, root: Path, local: str) -> list[str]:
        write(
            root,
            WORKFLOW,
            "python-version: '3.12.10'\nretention-days: 8\n"
            "run: python -m pytest -q -o junit_family=xunit1 --junitxml=artifacts/host.xml suite/tests/host\n",
        )
        write(
            root,
            SYSTEM + "testing/ci/validation_tools.json",
            json.dumps(
                {
                    "actionlint": {"version": "1.7.12"},
                    "shellcheck": {"version": "0.11.0"},
                }
            ),
        )
        write(
            root,
            SYSTEM + "requirements/system-requirements.md",
            "| REQ-01 |\n| REQ-02 |\n",
        )
        gates = write(
            root,
            SYSTEM + "testing/ci/OPERATIONS.md",
            "The required check names remain `Static`.\n\n" + local,
        )
        write(root, ".github/workflows/x.yml", "name: Static\n")
        return [gates]

    def test_required_contexts_must_be_present_and_resolve(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = self.tree(root, "suite/tests/host\n")
            guide = root / paths[0]
            guide.write_text("suite/tests/host\n", encoding="utf-8")
            self.assertIn("missing required check names", "\n".join(facts(paths, root)))
            guide.write_text(
                "The required check names remain `Missing`.\nsuite/tests/host\n",
                encoding="utf-8",
            )
            self.assertIn("required context Missing", "\n".join(facts(paths, root)))

    def test_matching_facts_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = "Python 3.12.10, 8 days, REQ-01…REQ-02, suite/tests/host\n"
            self.assertEqual(facts(self.tree(root, local), root), [])

    def test_drifted_facts_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = "Python 3.12.9, actionlint 1.7.11, 14 days, REQ-01–REQ-01\n"
            errors = "\n".join(facts(self.tree(root, local), root))
            for expected in (
                "3.12.9",
                "actionlint",
                "14 days",
                "REQ-01…REQ-01",
                "suite/tests/host",
            ):
                self.assertIn(expected, errors)


class LineAnchorTests(unittest.TestCase):
    def test_line_anchor_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(write(Path(tmp), "a.md", "1\n2\n3\n"))
            target = Path(tmp) / target
            self.assertTrue(line_anchor("L3", target))
            self.assertTrue(line_anchor("L1-L2", target))
            self.assertFalse(line_anchor("L4", target))
            self.assertFalse(line_anchor("heading", target))


class SupplementalSourceTests(unittest.TestCase):
    def test_supplemental_source_must_reach_both_registers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root,
                "thesis-material/_build/supplemental-sources.json",
                json.dumps({"keys": ["extra"]}),
            )
            write(root, "thesis-material/quellen.bib", "@misc{extra,\n}\n")
            write(root, "thesis-material/quellen.md", '<a id="extra"></a>\n')
            self.assertEqual(supplemental_sources(root), [])
            write(root, "thesis-material/quellen.md", "")
            self.assertEqual(len(supplemental_sources(root)), 1)

    def test_undeclared_supplemental_entry_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root,
                "thesis-material/_build/supplemental-sources.json",
                json.dumps({"keys": [], "bib": "@misc{hidden,\n}\n", "md": ""}),
            )
            write(root, "thesis-material/quellen.bib", "")
            write(root, "thesis-material/quellen.md", "")
            self.assertIn("hidden", supplemental_sources(root)[0])


class CoverageTests(unittest.TestCase):
    def check(self, catalogue, sources):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                "Development/system/testing/specification-verification.md": catalogue,
                **sources,
            }
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            return verification_coverage(root)

    def test_missing_case_is_reported_by_id(self):
        errors = self.check("| VT-01 | Startup |\n| VT-14 | Setup |", {})
        self.assertEqual(len(errors), 2)
        self.assertIn("VT-01 has no test/procedure reference", errors[0])
        self.assertIn("VT-14 has no test/procedure reference", errors[1])

    def test_source_reference_filename_and_explicit_gap_are_accepted(self):
        self.assertEqual(
            self.check(
                "VT-01 VT-02 VT-14\n- VT-02: Not yet covered — target case pending",
                {
                    "Development/system/coding/app/tests/host/test_flow.py": "# VT-14",
                    "Development/system/testing/system/VT-01.md": "Startup procedure",
                },
            ),
            [],
        )

    def test_ci_tests_evidence_and_production_comments_do_not_count(self):
        errors = self.check(
            "VT-14",
            {
                "Development/system/testing/ci/test_example.py": "# VT-14",
                "Development/system/testing/evidence/run.md": "VT-14",
                "Development/system/coding/app/main.c": "// VT-14",
            },
        )
        self.assertEqual(len(errors), 1)

    def test_gap_needs_a_reason_and_does_not_match_another_id(self):
        for whitespace in (" ", "  ", " \t "):
            with self.subTest(whitespace=whitespace):
                errors = self.check(
                    f"VT-01 VT-02\n- VT-01: Not yet covered{whitespace}\n", {}
                )
                self.assertEqual(len(errors), 2)

    def test_retired_cases_need_a_reason_and_are_separate_from_gaps(self):
        self.assertEqual(self.check("VT-05\n- VT-05: Retired — replay removed", {}), [])
        for whitespace in (" ", "  ", " \t "):
            with self.subTest(whitespace=whitespace):
                self.assertEqual(
                    len(self.check(f"VT-05\n- VT-05: Retired —{whitespace}\n", {})), 1
                )

    def test_covered_case_with_stale_gap_is_reported(self):
        for source in (
            "Development/system/coding/app/tests/host/test_flow.py",
            "Development/system/testing/WIFI/setup.md",
        ):
            with self.subTest(source=source):
                errors = self.check(
                    "VT-14\n- VT-14: Not yet covered — setup pending",
                    {source: "VT-14"},
                )
                self.assertEqual(len(errors), 1)
                self.assertIn("VT-14 has a test/procedure reference", errors[0])
                self.assertIn("stale", errors[0])


if __name__ == "__main__":
    unittest.main()
