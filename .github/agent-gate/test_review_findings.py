"""Keep optional findings nonblocking without losing review identity or blocking evidence."""

import unittest
from pathlib import Path
from unittest.mock import Mock

import agent_gate as gate
from review_findings import nonblocking_finding, nonblocking_review


HEAD = "a" * 40
BOT = {"login": "coderabbitai[bot]", "type": "Bot", "id": 136622811}
BOTS = {BOT["login"]: BOT["id"]}
MINOR = "_⚠️ Potential issue_ | _🟡 Minor_\n\nOptional diagnostic wording."
MAJOR = "_⚠️ Potential issue_ | _🟠 Major_\n\nCredential loss."


def decision(body="**Actionable comments posted: 1**", findings=None, **changes):
    review = {"id": 99, "state": "CHANGES_REQUESTED", "commit_id": HEAD, "body": body, "user": BOT}
    values = dict(number=1, state="open", draft=False, head_sha=HEAD, body="Human PR",
                  comments=[], check_runs=[], statuses=[], unresolved_threads=0, required_checks=[],
                  require_owner_approval=False, review_bots=BOTS, native_reviews=[review],
                  allow_minor_coderabbit_findings=True, review_comments=findings if findings is not None else [
                      {"id": 1, "user": BOT, "pull_request_review_id": 99, "body": MINOR}])
    values.update(changes)
    return gate.evaluate(gate.Inputs(**values))


class FindingSeverityTests(unittest.TestCase):
    def test_published_minor_summary_formats(self):
        summary = (Path(__file__).parent / "fixtures/coderabbit-minor-summary.md").read_text(encoding="utf-8")
        self.assertTrue(nonblocking_review(summary, [MINOR] * 6))

    def test_picture_only_prompt_icon(self):
        summary = ('**Actionable comments posted: 1**\n\n---\n\n<details><summary>'
                   '<picture><source media="dark"><img src="icon.svg"></picture> Prompt to fix review comments'
                   '</summary>\n```\nRepeated finding\n```\n</details>')
        self.assertTrue(nonblocking_review(summary, [MINOR]))
        self.assertFalse(nonblocking_review(summary, [MAJOR]))
        self.assertFalse(nonblocking_review(summary, [MINOR] * 5))
        self.assertFalse(nonblocking_review(summary, [MINOR] * 5 + [MAJOR]))
        self.assertFalse(nonblocking_review(summary.replace(" Trivial**", " Major**"), [MINOR] * 6))
        self.assertFalse(nonblocking_review(summary.replace("comments: 1", "comments: 2"), [MINOR] * 6))
        self.assertFalse(nonblocking_review(summary + "\nUnclassified concern", [MINOR] * 6))
        summary = summary.replace("🤖 Prompt to fix review comments", '<picture><img src="icon.svg"></picture>🤖 Prompt to fix review comments')
        self.assertTrue(nonblocking_review(summary, [MINOR] * 6))

    def test_explicit_minor_and_nitpick_are_nonblocking(self):
        for header in (MINOR, "_🧹 Nitpick_ | _🔵 Trivial_\n\nOptional refactoring."):
            self.assertTrue(nonblocking_finding(header))

    def test_blocking_unknown_quoted_and_fenced_headers_stay_blocking(self):
        for body in (MAJOR, MAJOR.replace("Major", "Critical"), "Minor: change this",
                     "> " + MINOR, "```\n" + MINOR + "\n```", "", MINOR.replace("Minor", "Unknown")):
            with self.subTest(body=body):
                self.assertFalse(nonblocking_finding(body))

    def test_current_bot_headers_preserve_severity(self):
        icon = '<picture><img src="icon.svg" alt=""></picture>'
        for separator in (" | ", " · "):
            for severity in ("Minor", "Trivial", "Major", "Critical"):
                classification = f"**{icon} {severity}**"
                category = "**Functional Correctness**"
                if separator == " | ":
                    classification = category + separator + classification
                else:
                    classification += separator + category
                body = "<!-- coderabbit-ai-generated:v1 -->\n\n" + classification + separator + "**Quick win**\n\nFinding."
                with self.subTest(separator=separator, severity=severity):
                    self.assertEqual(nonblocking_finding(body), severity in {"Minor", "Trivial"})
                    self.assertFalse(nonblocking_finding("> " + body))
                    self.assertFalse(nonblocking_finding("```\n" + body + "\n```"))

    def test_current_head_minor_changes_request_satisfies_review(self):
        self.assertEqual(decision().state, "success")

    def test_missing_mismatched_or_extra_findings_block(self):
        for findings in ([], [{"body": MINOR}], [
            {"user": BOT, "pull_request_review_id": 99, "body": MINOR},
            {"user": BOT, "pull_request_review_id": 99, "body": MAJOR}]):
            self.assertEqual(decision(findings=findings).state, "failure")

    def test_identity_cannot_be_replaced_by_similar_login_or_wrong_id(self):
        self.assertTrue(gate.authenticated_coderabbit({"user": {**BOT, "login": "coderabbitai"}}, BOTS))
        self.assertFalse(gate.authenticated_coderabbit({"user": {**BOT, "id": None}}, {}))
        for user in ({**BOT, "id": 1}, {**BOT, "type": "User"}, {**BOT, "login": "other[bot]"}):
            findings = [{"user": user, "pull_request_review_id": 99, "body": MINOR}]
            self.assertEqual(decision(findings=findings).state, "failure")

    def test_minor_review_does_not_waive_other_conditions(self):
        for changes in ({"unresolved_threads": 1}, {"required_checks": ["missing"]},
                        {"draft": True}, {"head_sha": "b" * 40},
                        {"body": "<!-- owner-question id=security -->\nChoose access control."}):
            self.assertNotEqual(decision(**changes).state, "success")

    def test_unknown_general_review_text_and_unclassified_sections_block(self):
        for suffix in ("\nGeneral blocking concern", "\n<details><summary>New finding format</summary>Minor</details>",
                       "\n<details><summary>⚠️ Outside diff range comments (1)</summary>Unclassified concern</details>",
                       "\n<details><summary>⚠️ Outside diff range comments (1)</summary>\n" + MAJOR + "\n</details>"):
            self.assertEqual(decision(body="**Actionable comments posted: 1**" + suffix).state, "failure")

    def test_minor_summary_and_duplicate_prompt_are_accounted_for(self):
        summary = ("**Actionable comments posted: 1**\n<details>\n<summary>🧹 Nitpick comments (1)</summary>\n"
                   + MINOR + "\n</details>\n<details><summary>📜 Review details</summary>Files: 1</details>")
        self.assertTrue(nonblocking_review(summary, [MINOR]))
        self.assertFalse(nonblocking_review(summary.replace("(1)", "(2)"), [MINOR]))
        self.assertFalse(nonblocking_review(summary.replace("Minor", "Critical"), [MINOR]))
        summary_only_nitpick = ("**Actionable comments posted: 1**\n"
                               "<details><summary>🧹 Nitpick comments (1)</summary>\n"
                               "<blockquote><details><summary>source.c (1)</summary>\n"
                               "`12`: **Consider a clearer name.**\n</details></blockquote></details>")
        self.assertTrue(nonblocking_review(summary_only_nitpick, [MINOR]))
        self.assertFalse(nonblocking_review(summary_only_nitpick.replace("Nitpick", "Outside diff range"), [MINOR]))

    def test_empty_changes_request_is_not_an_approval(self):
        self.assertFalse(nonblocking_review("**Actionable comments posted: 0**", []))

    def test_thread_pagination_checks_root_authorship_and_severity(self):
        def thread(body, author=None, resolved=False):
            return {"isResolved": resolved, "comments": {"nodes": [{"databaseId": "1", "body": body, "author": author or {
                "login": "coderabbitai", "__typename": "Bot", "databaseId": BOT["id"]}}]}}
        def page(threads, following=False):
            return {"repository": {"pullRequest": {"reviewThreads": {"nodes": threads,
                "pageInfo": {"hasNextPage": following, "endCursor": "next"}}}}}
        api = gate.GitHub("owner/repo", "unused")
        api.graphql = Mock(side_effect=[page([thread(MINOR), thread(MAJOR)], True), page([
            thread(MAJOR, resolved=True), thread(MINOR, {"login": "owner", "__typename": "User"}), thread("unknown")])])
        self.assertEqual(api.unresolved_threads(1, BOTS), 3)
        self.assertEqual(api.graphql.call_args_list[1].args[1]["c"], "next")
        api.graphql = Mock(return_value=page([thread(MINOR)]))
        self.assertEqual(api.unresolved_threads(1), 1)
        replies = [{"id": 2, "in_reply_to_id": 1, "user": BOT, "body": MAJOR}]
        self.assertEqual(api.unresolved_threads(1, BOTS, replies), 1)
        replies[0]["body"] = MINOR
        self.assertEqual(api.unresolved_threads(1, BOTS, replies), 0)


if __name__ == "__main__":
    unittest.main()
