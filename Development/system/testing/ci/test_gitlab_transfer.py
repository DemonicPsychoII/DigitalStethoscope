import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch

from gitlab_transfer import (
    ACCEPTED,
    GITLAB_README_SOURCE,
    SYSTEM,
    check,
    content_findings,
    export,
    gitlab_readme,
    link_findings,
    review_findings,
    transfer_set,
)

DESIGN = SYSTEM + "design/AUDIO/README.md"
PROFILE = SYSTEM + "coding/server-profiles/lab-hapi.toml"


class TransferSetTests(unittest.TestCase):
    def test_product_folders_are_transferred_and_the_rest_is_not(self):
        paths = [
            SYSTEM + "spec/product-scope.md",
            SYSTEM + "design/AUDIO/README.md",
            SYSTEM + "coding/app/main.c",
            SYSTEM + "coding/app/tests/host/test_x.py",
            SYSTEM + "planning/decision-trace.md",
            SYSTEM + "testing/verification-allocation.md",
            SYSTEM + "testing/ci/run_ci.py",
            "thesis-material/quellen.md",
        ]
        self.assertEqual(
            transfer_set(paths),
            sorted(
                [
                    SYSTEM + "spec/product-scope.md",
                    SYSTEM + "design/AUDIO/README.md",
                    SYSTEM + "coding/app/main.c",
                    SYSTEM + "testing/verification-allocation.md",
                ]
            ),
        )


class ContentTests(unittest.TestCase):
    def assert_found(self, text, name):
        findings = content_findings(DESIGN, text)
        self.assertTrue(any(name in finding for finding in findings), findings)

    def test_project_history_is_found(self):
        self.assert_found("Nico decided this.", "project member")
        self.assert_found("NICO decided this.", "project member")
        self.assert_found("This is a project decision.", "decision record")
        self.assert_found("See TICKET-213.", "ticket id")
        self.assert_found("Created by X on behalf of Y.", "chat or agent trace")
        self.assert_found("Written with Claude-Fable-5.2.", "chat or agent trace")
        self.assert_found("[log](../../planning/README.md)", "not transferred")

    def test_review_findings_are_found_in_pages(self):
        self.assert_review(
            DESIGN, "This design refines the architecture.", "page describes itself"
        )
        self.assert_review(
            DESIGN, "This Design refines the architecture.", "page describes itself"
        )
        self.assert_review(
            DESIGN, "The steps below add the rules.", "page describes itself"
        )
        self.assert_review(DESIGN, "The MVP sends one result.", "status word")
        self.assert_review(
            DESIGN, "The configuration enables CONFIG_SNTP.", "design reports the build"
        )
        self.assert_review(
            DESIGN, "L2 decides the retry.", "layer named instead of the module"
        )
        self.assert_review(
            DESIGN, "L2 retries the join.", "layer named instead of the module"
        )
        self.assert_review(
            DESIGN, "The hotspot waits for the phone.", "phone without its owner"
        )
        self.assert_review(DESIGN, "Covers REQ-09.", "requirement id without a link")
        self.assert_review(
            SYSTEM + "architecture/system/puml/mvp-session-state.puml",
            "@startuml",
            "file name",
        )

    def test_links_into_the_code_are_found_in_every_form(self):
        expected = "into the code"
        self.assert_review(
            DESIGN, "See [storage](../../coding/app/storage.c).", expected
        )
        self.assert_review(
            DESIGN, "See [storage][s].\n\n[s]: ../../coding/app/storage.c", expected
        )
        self.assert_review(
            DESIGN, '<a href="../../coding/app/storage.c">storage</a>', expected
        )
        viewer = SYSTEM + "architecture/system/review.html"
        self.assert_review(
            viewer, '<a href="../../coding/app/README.md">app</a>', expected
        )
        public = "See [guide](https://example.org/secure-coding/rules.html) and [page](../secure-coding/notes.md)."
        self.assertEqual(review_findings(DESIGN, public), [])

    def test_requirement_ids_pass_in_every_link_form(self):
        target = "../../requirements/system-requirements.md#req-09"
        for linked in (
            f"Covers [REQ-09]({target}).",
            f"Covers [REQ-09][r9].\n\n[r9]: {target}",
            f"Covers [REQ-09][].\n\n[REQ-09]: {target}",
            f"Covers [REQ-09].\n\n[REQ-09]: {target}",
            f"Covers [REQ-09\nand more]({target}).",
            f'Covers <a href="{target}">REQ-09</a>.',
            f'Covers <a href="{target}"><code>REQ-09</code></a>.',
        ):
            self.assertEqual(review_findings(DESIGN, linked), [], linked)

    def test_requirement_ids_need_a_real_link(self):
        expected = "requirement id without a link"
        self.assert_review(DESIGN, "Covers [REQ-09][missing].", expected)
        self.assert_review(DESIGN, "Covers [REQ-09].", expected)
        self.assert_review(DESIGN, '<a id="req-09">REQ-09</a>', expected)
        self.assert_review(
            DESIGN, "Covers REQ-09 and [REQ-10](x.md#req-10).", expected + ": REQ-09"
        )

    def test_a_link_to_the_code_folder_itself_is_found(self):
        self.assert_review(DESIGN, "See the [code](../../coding/).", "into the code")
        self.assert_review(DESIGN, "See the [code](../../coding).", "into the code")

    def test_source_entries_keep_their_wording_and_prose_does_not(self):
        entry = (
            "The limit follows the standard [1].\n"
            "\n"
            "[1] A. Author, Proposed changes to the phone: a TODO, 2020,\n"
            "    accessed 1 November 2026.\n"
        )
        self.assertEqual(review_findings(DESIGN, entry), [])
        self.assert_review(DESIGN, "The proposed limit is 5 s.", "status word")
        self.assert_review(DESIGN, "The *proposed* limit is 5 s [1].", "status word")
        self.assert_review(
            DESIGN, "| The *proposed* limit | Basis [S1] [S2] |", "status word"
        )
        self.assert_review(
            DESIGN, "See *this page* for the limit [2].", "page describes itself"
        )
        # A title in running text is the project's line until it is accepted with a reason.
        title = "The rule follows *A Proposed Standard* [3]."
        self.assert_review(DESIGN, title, "status word")
        with patch.dict(ACCEPTED, {(DESIGN, "status word"): frozenset({"Proposed"})}):
            self.assertEqual(review_findings(DESIGN, title), [])
            self.assert_review(DESIGN, "The MVP sends one result.", "status word")

    def test_table_rows_are_counted_as_markdown_counts_them(self):
        expected = "table row has"
        self.assert_review(
            DESIGN, "| a | b |\n|---|---|\n| 1 |", "table row has 1 cells"
        )
        self.assert_review(
            DESIGN, "a | b\n--- | ---\n1 | 2 | 3", "table row has 3 cells"
        )
        self.assert_review(
            DESIGN,
            "| a | b |\n|---|---|\n| 1 | 2 |\nonly one cell",
            "table row has 1 cells",
        )
        # A code span does not protect a pipe; an escaped pipe is text.
        self.assert_review(
            DESIGN, "| a | b |\n|---|---|\n| `x|y` | 2 |", "table row has 3 cells"
        )
        for valid in (
            "| a | b |\n|---|---|\n| 1 | 2 |",
            "| a | b\n|---|---\n| 1 | 2",
            "a | b\n:-- | --:\n1 | 2",
            "| a | b |\n|---|---|\n| `x\\|y` | 2 |",
            "| a \\| c | b |\n|---|---|\n| 1 | 2 |",
            "```\n| a | b |\n|---|---|\n| 1 |\n```",
            "~~~\n| a | b |\n|---|---|\n| 1 |\n~~~",
            "| a | b |\n|---|---|\n| 1 | 2 |\n\nA paragraph after the table.",
            "| a | b |\n|---|---|\n| 1 | 2 |\n## Heading",
            "A paragraph with a | pipe\n---\n\nText.",
            "A sentence with a | pipe.\n\nAnother line.",
        ):
            self.assertFalse(
                any(expected in finding for finding in review_findings(DESIGN, valid)),
                valid,
            )

    def test_conditions_that_call_a_function_are_found(self):
        source = SYSTEM + "coding/app/L1_services/L1_STORAGE/storage.c"
        expected = "condition calls a function"
        self.assert_review(
            source,
            "    if(sys_get_le32(bytes) != checksum)",
            expected + ": sys_get_le32",
        )
        self.assert_review(
            source,
            "    while((result == 0) &&\n          storage_hasNext(reader))",
            "storage_hasNext",
        )
        self.assert_review(
            source, "    if\n    (storage_isReady())\n    {", "storage_isReady"
        )
        self.assert_review(source, "    else if(storage_isReady())", "storage_isReady")
        self.assert_review(
            source, "    do { x++; } while(storage_hasNext(reader));", "storage_hasNext"
        )
        self.assert_review(
            source,
            "#define DRAIN(reader) \\\n    while \\\n    (storage_hasNext(reader)) \\\n    { }",
            "storage_hasNext",
        )
        self.assert_review(source, "    if((*handler)(code))", "call through a pointer")
        self.assert_review(
            source, "    if(handlers[index](code))", "call through a pointer"
        )
        self.assert_review(source, "    if(isReady) /* TODO check */", "status word")
        self.assert_review(
            source, "/* L1 compares by itself. */", "layer named instead of the module"
        )
        third_line = review_findings(source, "int a;\r\nint b;\r\nif(call(a))\r\n")
        self.assertTrue(
            any(":3: condition calls a function" in finding for finding in third_line),
            third_line,
        )

    def test_conditions_that_test_named_values_pass(self):
        source = SYSTEM + "coding/app/L1_services/L1_STORAGE/storage.c"
        for valid in (
            "    const bool isMatch = (sys_get_le32(bytes) == checksum);\n    if(isMatch)",
            "    if(isMatch && IS_ENABLED(CONFIG_X) && (length < sizeof(buffer)))",
            "    if((size_t)(length) > limit)",
            "    if(isReady) { storage_close(reader); }",
            "    if(isReady) /* storage_close(reader) runs later */",
            "    if(isReady) // see storage_close(reader)",
            "    // a comment that continues \\\n    if(storage_isReady())\n    value = 1;",
            '    if(isReady) { LOG_INF("call(%d)", value); }',
            "    while(index < count)\n    {\n        storage_read(reader);\n    }",
            "    notify(isReady);",
        ):
            self.assertEqual(review_findings(source, valid), [], valid)

    def test_plain_text_passes_the_review_rules(self):
        page = (
            "SNTP synchronization refines the architecture under "
            "[REQ-09](../../requirements/system-requirements.md#req-09).\n"
            "The operator's phone joins the hotspot.\n"
            "`CONFIG_SNTP_UNCERTAINTY` must be enabled.\n"
        )
        self.assertEqual(review_findings(DESIGN, page), [])
        architecture = SYSTEM + "architecture/system/firmware-structure.md"
        self.assertEqual(
            review_findings(architecture, "L2 owns orchestration. L0 is Zephyr."), []
        )
        requirements = "REQ-09 The device delivers the result."
        self.assertEqual(
            review_findings(
                SYSTEM + "requirements/system-requirements.md", requirements
            ),
            [],
        )

    def test_third_party_and_reference_code_are_not_reviewed(self):
        text = "/* TODO this page */\nif(call(x))"
        self.assertEqual(
            review_findings(SYSTEM + "coding/third_party/parser/http_parser.c", text),
            [],
        )
        self.assertEqual(
            review_findings(
                SYSTEM + "references/newtec-pulsoxy/lib/FhirService.cpp", text
            ),
            [],
        )

    def assert_review(self, path, text, expected):
        findings = review_findings(path, text)
        self.assertTrue(
            any(expected in finding for finding in findings), (text, findings)
        )

    def test_dates_are_found_in_every_written_form(self):
        for text in (
            "The value was set on 10 November 2026.",
            "The value was set on 13 Nov 2026.",
            "The value was set on 2026-11-13.",
            "The lab record of 8 November 2026 was accessed by the tester.",
            "[1] A source, 2019.\n\nThe value was set on 10 November 2026.",
            "[1] A source, accessed 11 November 2026; page numbers\nchecked 13 November 2026.",
        ):
            with self.subTest(text=text):
                self.assert_found(text, "written date")

    def test_private_network_details_are_found(self):
        for text in (
            "The server is https://192.168.2.40:8443/fhir.",
            "The server is 10.2.3.4.",
            "The hotspot gives 172.20.10.8.",
            "The host is staging.office.local.",
            "The host is NGLegion.",
            "Write to someone@example.org.",
        ):
            with self.subTest(text=text):
                self.assert_found(text, "private network detail")

    def test_citations_public_addresses_and_author_names_pass(self):
        accepted = (
            "[1] Espressif Systems, *Wi-Fi Driver*, v5.4.2, <https://example.org> (accessed 24 October 2026).\n"
            "\n"
            "The setup page is served at 192.168.4.1; the pool starts at 192.168.4.10.\n"
            "The example server is https://192.0.2.10:8443/fhir.\n"
            "\n"
            "[2] TDK InvenSense, *INMP441*, revision 1.0,\n"
            "6 February 2014, <https://example.org>.\n"
            "\n"
            "[3] Claude E. Shannon, *A Mathematical Theory of Communication*, 1948.\n"
        )
        self.assertEqual(content_findings(DESIGN, accepted), [])

    def test_accepted_values_of_the_lab_profile_pass_and_new_ones_do_not(self):
        reviewed = 'description = "server on nglegion, home network 192.168.2.0/24 or hotspot 172.20.10.0/28"\n'
        self.assertEqual(content_findings(PROFILE, reviewed), [])
        self.assertEqual(
            len(
                content_findings(PROFILE, 'base_url = "https://192.168.2.99:8443/fhir"')
            ),
            1,
        )
        self.assertEqual(len(content_findings(PROFILE, "# Nico")), 1)


class LinkTests(unittest.TestCase):
    SELECTED = {
        DESIGN,
        SYSTEM + "design/AUDIO/parameters.md",
        SYSTEM + "design/AUDIO/a(b).md",
        SYSTEM + "design/AUDIO/puml/audio-state.puml",
        SYSTEM + "design/README.md",
    }

    def test_links_inside_the_set_pass(self):
        text = (
            "[a](parameters.md) [b](../README.md#x) [c](https://example.org) [e](#local)\n"
            '[f](parameters.md "title") [g](a(b).md) [sources](puml/)\n'
            "[ref]: parameters.md\n"
        )
        self.assertEqual(link_findings(DESIGN, text, self.SELECTED), [])

    def test_links_outside_the_set_are_found_in_every_form(self):
        for text in (
            "[d](../../testing/ci/run_ci.py)",
            '[d](../../testing/ci/run_ci.py "title")',
            "![d](rendered/missing.svg)",
            "[ref]: ../../planning/README.md",
            '<img src="rendered/missing.svg">',
        ):
            with self.subTest(text=text):
                self.assertEqual(len(link_findings(DESIGN, text, self.SELECTED)), 1)

    def test_link_that_leaves_the_repository_is_found(self):
        findings = link_findings(
            DESIGN, "[x](../../../../../outside.md)", self.SELECTED
        )
        self.assertEqual(len(findings), 1)
        self.assertIn("leaves the repository", findings[0])

    def test_html_pages_are_checked(self):
        page = SYSTEM + "design/AUDIO/view.html"
        self.assertEqual(
            len(link_findings(page, '<a href="missing.md">x</a>', self.SELECTED)), 1
        )


class SnapshotTests(unittest.TestCase):
    README = (
        b"[spec](../spec/product-scope.md) and [code](../coding/app/README.md#build)\n"
    )

    def files(self):
        return {
            SYSTEM + "spec/product-scope.md": b"# Product\n",
            SYSTEM
            + "coding/app/README.md": b"# Firmware\n\n[spec](../../spec/product-scope.md)\n",
            GITLAB_README_SOURCE: self.README,
        }

    def test_clean_snapshot_passes_and_every_file_is_decoded(self):
        self.assertEqual(check(self.files()), [])
        files = self.files()
        files[SYSTEM + "design/AUDIO/rendered/view.svg"] = (
            b"<svg><text>Nico</text></svg>"
        )
        files[SYSTEM + "coding/app/Kconfig"] = b"# Nico\n"
        files[SYSTEM + "coding/app/notes.txt"] = "Nico".encode("utf-16")
        findings = check(files)
        self.assertEqual(len(findings), 3, findings)
        self.assertTrue(any("not UTF-8 text" in finding for finding in findings))

    def test_missing_root_page_and_its_broken_links_are_found(self):
        files = self.files()
        del files[GITLAB_README_SOURCE]
        self.assertEqual(len(check(files)), 1)
        files = self.files()
        files[GITLAB_README_SOURCE] = b"[gone](../design/README.md)\n"
        self.assertEqual(len(check(files)), 1)

    def test_root_page_link_that_is_not_rewritten_is_found(self):
        for text in (
            b'[spec](../spec/product-scope.md "title")\n',
            b"[spec]: ../spec/product-scope.md\n",
            b'<a href="../spec/product-scope.md">spec</a>\n',
        ):
            with self.subTest(text=text):
                files = self.files()
                files[GITLAB_README_SOURCE] = text
                findings = check(files)
                self.assertEqual(len(findings), 1, findings)
                self.assertIn("README.md", findings[0])

    def test_root_page_links_are_rewritten_for_the_root(self):
        self.assertEqual(
            gitlab_readme(self.README.decode("utf-8")),
            f"[spec]({SYSTEM}spec/product-scope.md) and [code]({SYSTEM}coding/app/README.md#build)\n",
        )

    def test_export_writes_a_new_directory_and_refuses_an_existing_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "export"
            self.assertEqual(export(self.files(), destination), 3)
            self.assertTrue((destination / "README.md").is_file())
            self.assertTrue((destination / SYSTEM / "spec/product-scope.md").is_file())
            self.assertFalse((destination / GITLAB_README_SOURCE).exists())
            with self.assertRaises(FileExistsError):
                export(self.files(), destination)


if __name__ == "__main__":
    unittest.main()
