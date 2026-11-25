import unittest

from gitlab_transfer import SYSTEM, content_findings, link_findings, transfer_set

DESIGN = SYSTEM + "design/AUDIO/README.md"


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
    def assert_found(self, line, name):
        findings = content_findings(DESIGN, line)
        self.assertTrue(any(name in finding for finding in findings), findings)

    def test_project_history_and_private_details_are_found(self):
        self.assert_found("Nico decided this.", "project member")
        self.assert_found("The value was set on 10 November 2026.", "written date")
        self.assert_found("This is a project decision.", "decision record")
        self.assert_found("See TICKET-213.", "ticket id")
        self.assert_found("Created by X on behalf of Y.", "chat or agent trace")
        self.assert_found(
            "The server is https://192.168.2.40:8443/fhir.", "private network detail"
        )
        self.assert_found("[log](../../planning/README.md)", "not transferred")

    def test_source_entries_and_the_hotspot_address_pass(self):
        accepted = (
            "[1] Espressif Systems, *Wi-Fi Driver*, v5.4.2, <https://example.org> (accessed 24 October 2026).\n"
            "\n"
            "The setup page is served at 192.168.4.1; the pool starts at 192.168.4.10.\n"
            "The device presents no client certificate.\n"
            "\n"
            "[2] TDK InvenSense, *INMP441*, revision 1.0,\n"
            "6 February 2014, <https://example.org>.\n"
        )
        self.assertEqual(content_findings(DESIGN, accepted), [])

    def test_date_after_a_source_entry_has_ended_is_found(self):
        text = "[1] A source, 2019.\n\nThe value was set on 10 November 2026.\n"
        findings = content_findings(DESIGN, text)
        self.assertEqual(len(findings), 1)
        self.assertIn(":3:", findings[0])

    def test_accepted_file_passes_only_its_own_rule(self):
        profile = SYSTEM + "coding/server-profiles/lab-hapi.toml"
        self.assertEqual(
            content_findings(profile, 'base_url = "https://192.168.2.40:8443/fhir"'), []
        )
        self.assertEqual(len(content_findings(profile, "# Nico")), 1)


class LinkTests(unittest.TestCase):
    def test_link_to_a_file_outside_the_set_is_found(self):
        selected = {
            DESIGN,
            SYSTEM + "design/AUDIO/parameters.md",
            SYSTEM + "design/README.md",
        }
        text = "[a](parameters.md) [b](../README.md#x) [c](https://example.org) [d](../../testing/ci/run_ci.py) [e](#local)"
        findings = link_findings(DESIGN, text, selected)
        self.assertEqual(len(findings), 1)
        self.assertIn("testing/ci/run_ci.py", findings[0])

    def test_link_to_a_transferred_folder_passes(self):
        selected = {DESIGN, SYSTEM + "design/AUDIO/puml/audio-state.puml"}
        self.assertEqual(link_findings(DESIGN, "[sources](puml/)", selected), [])


if __name__ == "__main__":
    unittest.main()
