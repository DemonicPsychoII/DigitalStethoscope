import base64
import json
import tempfile
import unittest
import zlib
from pathlib import Path

from validate_docs import (
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
            write(root, ci + "README.md", "`listed.py`")
            write(root, arch + "README.md", "[v](view.puml)")
            write(root, arch + "VIEW-NOTES.md", "")
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
            "run: python -m pytest -q suite/tests/host\n",
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
            SYSTEM + "testing/CI-QUALITY-GATES.md",
            "Required contexts remain:\n\n- `Static`\n\n" + local,
        )
        write(root, SYSTEM + "testing/ci/OPERATIONS.md", local)
        write(root, ".github/workflows/x.yml", "name: Static\n")
        return [gates]

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


if __name__ == "__main__":
    unittest.main()
