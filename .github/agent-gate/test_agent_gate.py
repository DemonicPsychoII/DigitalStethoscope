"""Unit tests for agent_gate.py. Run: python3 -m unittest discover -s .github/agent-gate -v"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import Mock, patch
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_gate as g  # noqa: E402

HEAD = "a" * 40
OLD = "b" * 40
AUTHOR = "<!-- agent-author harness=claude model=claude-opus-5-5 session=auth-1 class=quick-fix -->"
RISK = """
## Risk & rollback
- **What could break:** the budget precheck could reject valid calls
- **How verified:** unit tests plus a smoke test against the live stack
- **How to revert:** scripts/revert-last-merge.sh <pr> --deploy
"""
BODY = f"{AUTHOR}\n## Summary\nThing.\n{RISK}\n## Verification\n- [x] tests"


def body_with_class(klass):
    return BODY.replace("class=quick-fix", f"class={klass}")


def comment(text, created="2026-10-02T09:00:00Z", association="OWNER", login="DemonicPsychoII", cid=50):
    return {"id": cid, "body": text, "created_at": created, "login": login, "association": association}


APPROVAL_ANY = '<!-- owner-approval sha=any quote="yes, ship the new dashboard" -->'
POLICY_PATHS = (".github/agent-gate/*", ".github/workflows/*", "AGENTS.md")


def review(verdict="approve", sha=HEAD, session="rev-1", reviewer="codex/gpt-5.5", created="2026-10-02T10:00:00Z",
           association="OWNER", login="DemonicPsychoII", cid=1, prefix=""):
    body = f"{prefix}<!-- agent-review verdict={verdict} sha={sha} reviewer={reviewer} session={session} -->\nLooks fine."
    return {"id": cid, "body": body, "created_at": created, "login": login, "association": association}


def green_ci():
    return [
        {"id": 10, "name": "mission-control-budget-tests", "status": "completed", "conclusion": "success"},
        {"id": 11, "name": "Zephyr / Firmware Build", "status": "completed", "conclusion": "skipped"},
    ]


def inputs(**kw):
    base = g.Inputs(
        number=7, state="open", draft=False, head_sha=HEAD, body=BODY, comments=[review()],
        check_runs=green_ci(), statuses=[], unresolved_threads=0,
        required_checks=["mission-control-budget-tests"],
    )
    return replace(base, **kw)


class ParsingTests(unittest.TestCase):
    def test_author_marker(self):
        self.assertEqual(g.parse_author(BODY)["session"], "auth-1")

    def test_author_harness_spellings(self):
        for harness in ("claude", "claude-code", "codex"):
            body = f"<!-- agent-author harness={harness} model=m-1 session=s-1 -->"
            self.assertEqual(g.parse_author(body)["harness"], harness)

    def test_template_placeholder_author_is_not_valid(self):
        self.assertIsNone(g.parse_author("<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> -->"))

    def test_marker_in_code_fence_is_ignored(self):
        self.assertIsNone(g.parse_author(f"```\n{AUTHOR}\n```"))
        self.assertIsNone(g.parse_review(f"```md\n{review()['body']}\n```"))

    def test_quoted_review_marker_is_ignored(self):
        self.assertIsNone(g.parse_review("> " + review()["body"]))

    def test_review_requires_full_sha(self):
        self.assertIsNone(g.parse_review(review(sha="abc1234")["body"]))

    def test_review_uppercase_sha_normalised(self):
        self.assertEqual(g.parse_review(review(sha="A" * 40)["body"])["sha"], "a" * 40)

    def test_revert_marker(self):
        self.assertEqual(g.parse_reverted(f"<!-- agent-revert of={HEAD},{OLD} -->"), [HEAD, OLD])
        self.assertEqual(g.parse_reverted("<!-- agent-revert of=nothex -->"), [])

    def test_risk_section_filled(self):
        self.assertEqual(g.risk_section_problems(BODY), [])

    def test_risk_section_missing(self):
        self.assertIn("no `## Risk & rollback` section", g.risk_section_problems("## Summary\nx")[0])

    def test_risk_section_template_unfilled(self):
        template = Path(__file__).resolve().parents[1].joinpath("pull_request_template.md").read_text()
        problems = g.risk_section_problems(template)
        self.assertEqual(len(problems), 3, problems)

    def test_filled_template_basis_preserves_author_and_risk_parsing(self):
        template = Path(__file__).resolve().parents[1].joinpath("pull_request_template.md").read_text()
        body = template.replace(
            "<!-- agent-author harness=<claude-code|codex> model=<id> session=<id> class=<quick-fix|feature|policy|revert> -->",
            AUTHOR,
        )
        body = body.replace("- **What could break:**", "- **What could break:** incorrect case selection")
        body = body.replace("- **How verified:**", "- **How verified:** tooling and host tests passed")
        body = body.replace("- **How to revert:**", "- **How to revert:** revert this commit")
        self.assertEqual(g.parse_author(body)["session"], "auth-1")
        self.assertEqual(g.risk_section_problems(body), [])

    def test_risk_placeholders_rejected(self):
        body = "## Risk & rollback\n- What could break: TODO\n- How verified: n/a\n- How to revert: -\n"
        self.assertEqual(len(g.risk_section_problems(body)), 3)

    def test_risk_section_stops_at_next_heading(self):
        body = ("## Risk & rollback\n- What could break: the deploy script\n- How verified:\n"
                "## Verification\nHow to revert: plenty of text here but in the wrong section\n")
        problems = g.risk_section_problems(body)
        self.assertIn("Risk & rollback: missing 'how to revert'", problems)
        self.assertIn("Risk & rollback: 'how verified' is not filled in", problems)

    def test_quoted_attribute_values(self):
        attrs = g.parse_attrs('sha=any quote="go ahead, merge it" id=q1')
        self.assertEqual(attrs, {"sha": "any", "quote": "go ahead, merge it", "id": "q1"})

    def test_owner_approval_marker(self):
        self.assertIsNotNone(g.owner_approval(APPROVAL_ANY, HEAD))
        self.assertIsNotNone(g.owner_approval(f'<!-- owner-approval sha={HEAD} quote="ok to merge" -->', HEAD))
        self.assertIsNone(g.owner_approval(f'<!-- owner-approval sha={OLD} quote="ok to merge" -->', HEAD))
        self.assertIsNone(g.owner_approval("<!-- owner-approval sha=any -->", HEAD))  # no quote
        self.assertIsNone(g.owner_approval(f"```\n{APPROVAL_ANY}\n```", HEAD))
        self.assertIsNone(g.owner_approval("> " + APPROVAL_ANY, HEAD))

    def test_owner_question_and_answer_markers(self):
        self.assertEqual(g.owner_questions("<!-- owner-question id=db-migration -->\nOK to drop?"), {"db-migration"})
        self.assertEqual(g.owner_answers("<!-- owner-answer id=db-migration -->\nOwner: yes"), {"db-migration"})
        self.assertEqual(g.owner_questions("<!-- owner-question id=<x> -->"), set())  # template placeholder

    def test_family(self):
        self.assertEqual(g.family("gpt-5.5-codex"), "openai")
        self.assertEqual(g.family("claude-opus-5-5"), "claude")
        self.assertEqual(g.family("o4-mini"), "openai")


class EvaluateTests(unittest.TestCase):
    def test_happy_path(self):
        d = g.evaluate(inputs())
        self.assertEqual(d.state, "success", d.items)
        self.assertEqual(d.notes, [])

    def test_draft_fails(self):
        self.assertEqual(g.evaluate(inputs(draft=True)).state, "failure")

    def test_closed_fails(self):
        self.assertEqual(g.evaluate(inputs(state="closed")).state, "failure")

    def test_human_pr_without_agent_metadata_passes(self):
        d = g.evaluate(inputs(body="Fix the audio buffer bounds."))
        self.assertEqual(d.state, "success", d.items)

    def test_untouched_agent_template_does_not_declare_agent_authorship(self):
        template = Path(__file__).resolve().parents[1].joinpath("pull_request_template.md").read_text()
        d = g.evaluate(inputs(body=template))
        self.assertEqual(d.state, "success", d.items)

    def test_incomplete_agent_declaration_still_fails(self):
        for marker in ("<!-- agent-author harness=codex -->",
                       AUTHOR.replace("session=auth-1", "session=<id>"),
                       AUTHOR.replace("class=quick-fix", "class=unknown")):
            with self.subTest(marker=marker):
                d = g.evaluate(inputs(body=marker + RISK))
                self.assertEqual(d.state, "failure", d.items)
                self.assertIn("agent-author", d.description)

    def test_agent_pr_still_requires_risk_evidence(self):
        d = g.evaluate(inputs(body=AUTHOR))
        self.assertEqual(d.state, "failure", d.items)
        self.assertIn("Risk & rollback", d.description)

    def test_unmarked_pr_preserves_review_ci_threads_and_owner_questions(self):
        for options in ({"comments": []}, {"comments": [review(sha=OLD)]},
                        {"check_runs": []}, {"unresolved_threads": 1},
                        {"comments": [review(), comment("<!-- owner-question id=q1 --> Proceed?")]}):
            with self.subTest(options=options):
                d = g.evaluate(inputs(body="Human-written fix.", **options))
                self.assertNotEqual(d.state, "success", d.items)

    def test_no_review_is_pending(self):
        d = g.evaluate(inputs(comments=[]))
        self.assertEqual(d.state, "pending", d.items)
        self.assertIn("waiting for an agent review", d.description)

    def test_stale_review_without_carry_forward_is_pending(self):
        d = g.evaluate(inputs(comments=[review(sha=OLD)]))
        self.assertEqual(d.state, "pending")
        self.assertIn("re-review", d.description)

    def test_latest_review_wins(self):
        later_changes = review(verdict="changes", created="2026-10-02T11:00:00Z", cid=2)
        self.assertEqual(g.evaluate(inputs(comments=[review(), later_changes])).state, "failure")
        later_approve = review(created="2026-10-02T12:00:00Z", cid=3)
        self.assertEqual(g.evaluate(inputs(comments=[review(), later_changes, later_approve])).state, "success")

    def test_latest_marker_for_old_sha_blocks_even_if_earlier_matches(self):
        newer_old_sha = review(sha=OLD, created="2026-10-02T11:00:00Z", cid=2)
        self.assertEqual(g.evaluate(inputs(comments=[review(), newer_old_sha])).state, "pending")

    def test_self_review_fails(self):
        d = g.evaluate(inputs(comments=[review(session="auth-1")]))
        self.assertEqual(d.state, "failure")
        self.assertIn("author session", d.description)

    def test_untrusted_commenter_ignored(self):
        d = g.evaluate(inputs(comments=[review(association="NONE", login="stranger")]))
        self.assertEqual(d.state, "pending")

    def test_bot_review_is_never_trusted(self):
        # A PR controls its own pull_request workflows, which can comment as github-actions[bot].
        for association in ("NONE", "CONTRIBUTOR", "MEMBER"):
            bot = review(login="github-actions[bot]", association=association)
            self.assertEqual(g.evaluate(inputs(comments=[bot])).state, "pending", association)

    def test_bot_changes_verdict_cannot_hide_human_approval(self):
        bot = review(verdict="changes", login="github-actions[bot]", association="NONE",
                     created="2026-10-02T11:00:00Z", cid=2)
        self.assertEqual(g.evaluate(inputs(comments=[review(), bot])).state, "success")

    def test_reviewer_logins_restrict_who_can_review(self):
        only_app = frozenset({"reviewer-app[bot]"})
        self.assertEqual(g.evaluate(inputs(reviewer_logins=only_app)).state, "pending")
        app = review(login="reviewer-app[bot]", association="NONE")
        self.assertEqual(g.evaluate(inputs(comments=[app], reviewer_logins=only_app)).state, "success")

    def test_bot_report_comment_never_counts_as_review(self):
        fake = review(login="github-actions[bot]", association="NONE")
        fake["body"] = g.REPORT_MARKER + "\n" + fake["body"]
        self.assertEqual(g.evaluate(inputs(comments=[fake])).state, "pending")

    def test_same_family_is_advisory_only(self):
        d = g.evaluate(inputs(comments=[review(reviewer="claude/claude-sonnet-5")]))
        self.assertEqual(d.state, "success")
        self.assertTrue(d.notes)

    def test_unresolved_threads_fail(self):
        self.assertEqual(g.evaluate(inputs(unresolved_threads=2)).state, "failure")

    def test_ci_failure_fails(self):
        runs = green_ci() + [{"id": 12, "name": "python-tests", "status": "completed", "conclusion": "failure"}]
        self.assertEqual(g.evaluate(inputs(check_runs=runs)).state, "failure")

    def test_ci_running_is_pending(self):
        runs = green_ci() + [{"id": 12, "name": "python-tests", "status": "in_progress", "conclusion": None}]
        self.assertEqual(g.evaluate(inputs(check_runs=runs)).state, "pending")

    def test_required_check_not_reported_is_pending(self):
        d = g.evaluate(inputs(required_checks=["mission-control-budget-tests", "static-checks"]))
        self.assertEqual(d.state, "pending")
        self.assertIn("static-checks", d.description)

    def test_rerun_supersedes_failed_attempt(self):
        runs = [
            {"id": 10, "name": "python-tests", "status": "completed", "conclusion": "failure"},
            {"id": 20, "name": "python-tests", "status": "completed", "conclusion": "success"},
        ] + green_ci()
        self.assertEqual(g.evaluate(inputs(check_runs=runs)).state, "success")

    def test_own_check_and_status_are_excluded(self):
        runs = green_ci() + [{"id": 30, "name": "agent-gate-evaluate", "status": "in_progress", "conclusion": None}]
        statuses = [{"context": "agent-gate", "state": "failure"}]
        self.assertEqual(g.evaluate(inputs(check_runs=runs, statuses=statuses)).state, "success")

    def test_ignored_and_failing_statuses(self):
        statuses = [{"context": "approved-gate", "state": "failure"}]
        self.assertEqual(g.evaluate(inputs(statuses=statuses)).state, "failure")
        self.assertEqual(
            g.evaluate(inputs(statuses=statuses, ignore_checks=frozenset({"approved-gate"}))).state, "success"
        )

    def test_status_counts_toward_required(self):
        d = g.evaluate(inputs(required_checks=["ext"], statuses=[{"context": "ext", "state": "success"}]))
        self.assertEqual(d.state, "success")

    def test_verified_revert_waives_review(self):
        d = g.evaluate(inputs(body=body_with_class("revert"), comments=[], revert=(True, "reverts abc1234")))
        self.assertEqual(d.state, "success", d.items)

    def test_verified_revert_waives_owner_approval_even_on_policy_paths(self):
        d = g.evaluate(inputs(body=body_with_class("revert"), comments=[], revert=(True, "reverts abc1234"),
                              changed_files=["AGENTS.md"], owner_approval_paths=POLICY_PATHS))
        self.assertEqual(d.state, "success", d.items)

    def test_revert_class_without_verification_fails_even_with_review(self):
        d = g.evaluate(inputs(body=body_with_class("revert"), revert=(False, "branch contains a merge commit")))
        self.assertEqual(d.state, "failure")
        self.assertIn("not a verified pure revert", d.description)
        d = g.evaluate(inputs(body=body_with_class("revert")))  # no agent-revert marker at all
        self.assertEqual(d.state, "failure")

    def test_verified_revert_without_revert_class_needs_review(self):
        d = g.evaluate(inputs(comments=[], revert=(True, "reverts abc1234")))
        self.assertEqual(d.state, "pending")
        self.assertTrue(any("class=quick-fix" in n for n in d.notes))

    def test_unverified_revert_still_needs_review(self):
        d = g.evaluate(inputs(comments=[], revert=(False, "conflict-resolved")))
        self.assertEqual(d.state, "pending")
        self.assertTrue(any("conflict-resolved" in n for n in d.notes))

    def test_open_owner_question_blocks_merge_even_for_reverts(self):
        q = comment("<!-- owner-question id=q1 -->\nShould this also cover the backup path? (asked in chat)")
        d = g.evaluate(inputs(comments=[review(), q]))
        self.assertEqual(d.state, "failure")
        self.assertIn("q1", d.description)
        d = g.evaluate(inputs(body=body_with_class("revert"), comments=[q], revert=(True, "reverts abc1234")))
        self.assertEqual(d.state, "failure")

    def test_owner_question_in_body_blocks(self):
        body = BODY + "\n<!-- owner-question id=scope -->\nKeep the old flag?"
        self.assertEqual(g.evaluate(inputs(body=body)).state, "failure")

    def test_owner_answer_unblocks(self):
        q = comment("<!-- owner-question id=q1 -->\nKeep the old flag?", cid=51)
        a = comment("<!-- owner-answer id=q1 -->\nOwner in chat: \"drop it\"", created="2026-10-02T09:30:00Z", cid=52)
        d = g.evaluate(inputs(comments=[review(), q, a]))
        self.assertEqual(d.state, "success", d.items)

    def test_answer_must_match_id_and_be_trusted(self):
        q = comment("<!-- owner-question id=q1 -->", cid=51)
        for a in (comment("<!-- owner-answer id=q2 -->", cid=52),
                  comment("<!-- owner-answer id=q1 -->", login="github-actions[bot]", association="NONE", cid=53),
                  comment("> <!-- owner-answer id=q1 -->", cid=54)):
            self.assertEqual(g.evaluate(inputs(comments=[review(), q, a])).state, "failure", a["body"])

    def test_resolved_threads_do_not_answer_questions(self):
        q = comment("<!-- owner-question id=q1 -->", cid=51)
        self.assertEqual(g.evaluate(inputs(comments=[review(), q], unresolved_threads=0)).state, "failure")

    def test_quick_fix_needs_no_owner_approval(self):
        d = g.evaluate(inputs(changed_files=["src/app.py"], owner_approval_paths=POLICY_PATHS))
        self.assertEqual(d.state, "success", d.items)

    def test_missing_or_unknown_class_fails(self):
        no_class = BODY.replace(" class=quick-fix", "")
        self.assertEqual(g.evaluate(inputs(body=no_class)).state, "failure")
        self.assertIn("class=", g.evaluate(inputs(body=no_class)).description)
        self.assertEqual(g.evaluate(inputs(body=body_with_class("lowrisk"))).state, "failure")

    def test_feature_and_policy_need_owner_approval(self):
        for klass in ("feature", "policy"):
            d = g.evaluate(inputs(body=body_with_class(klass)))
            self.assertEqual(d.state, "failure", klass)
            self.assertIn("owner approval", d.description)

    def test_review_alone_never_authorizes_a_feature(self):
        reviews = [review(cid=i, created=f"2026-10-02T1{i}:00:00Z") for i in range(1, 4)]
        self.assertEqual(g.evaluate(inputs(body=body_with_class("feature"), comments=reviews)).state, "failure")

    def test_owner_label_approves_feature(self):
        d = g.evaluate(inputs(body=body_with_class("feature"), owner_label=True))
        self.assertEqual(d.state, "success", d.items)

    def test_owner_approval_comment_approves_feature(self):
        d = g.evaluate(inputs(body=body_with_class("policy"), comments=[review(), comment(APPROVAL_ANY)]))
        self.assertEqual(d.state, "success", d.items)
        pinned = comment(f'<!-- owner-approval sha={HEAD} quote="merge it" -->')
        self.assertEqual(g.evaluate(inputs(body=body_with_class("feature"), comments=[review(), pinned])).state,
                         "success")

    def test_owner_approval_for_old_sha_or_from_bot_does_not_count(self):
        stale = comment(f'<!-- owner-approval sha={OLD} quote="merge it" -->')
        bot = comment(APPROVAL_ANY, login="github-actions[bot]", association="NONE")
        stranger = comment(APPROVAL_ANY, login="stranger", association="NONE")
        for c in (stale, bot, stranger):
            d = g.evaluate(inputs(body=body_with_class("feature"), comments=[review(), c]))
            self.assertEqual(d.state, "failure", c)

    def test_owner_approval_still_needs_review_and_ci(self):
        d = g.evaluate(inputs(body=body_with_class("feature"), owner_label=True, comments=[]))
        self.assertEqual(d.state, "pending")
        runs = green_ci() + [{"id": 12, "name": "python-tests", "status": "completed", "conclusion": "failure"}]
        d = g.evaluate(inputs(body=body_with_class("feature"), owner_label=True, check_runs=runs))
        self.assertEqual(d.state, "failure")

    def test_policy_path_needs_owner_approval_whatever_the_class(self):
        d = g.evaluate(inputs(changed_files=["AGENTS.md"], owner_approval_paths=POLICY_PATHS))
        self.assertEqual(d.state, "failure")
        self.assertIn("policy path", d.description)
        for path in (".github/agent-gate/agent_gate.py", ".github/workflows/tests.yml"):
            d = g.evaluate(inputs(body=body_with_class("policy"), changed_files=[path],
                                  owner_approval_paths=POLICY_PATHS))
            self.assertEqual(d.state, "failure", path)
            self.assertIn("owner approval", d.description)
        d = g.evaluate(inputs(changed_files=["AGENTS.md"], owner_approval_paths=POLICY_PATHS, owner_label=True))
        self.assertEqual(d.state, "success", d.items)

    def test_terminal_failure_beats_pending(self):
        runs = green_ci() + [{"id": 12, "name": "x", "status": "queued", "conclusion": None}]
        self.assertEqual(g.evaluate(inputs(check_runs=runs, comments=[review(verdict="changes")])).state,
                         "failure")

    def test_description_fits_status_limit(self):
        d = g.evaluate(inputs(comments=[], body="", draft=True, unresolved_threads=3))
        self.assertLessEqual(len(d.description), 140)

    def test_report_never_contains_a_review_marker(self):
        d = g.evaluate(inputs())
        self.assertIsNone(g.parse_review(g.render_report(inputs(), d, "https://x")))


class FakeEvents(g.GitHub):
    def __init__(self, events):
        super().__init__("o/r", "token")
        self.events = events

    def paginate(self, path, key=None):
        return self.events


def label_event(login, kind="labeled", name="approved", actor_type="User"):
    return {"event": kind, "label": {"name": name}, "actor": {"login": login, "type": actor_type}}


class OwnerLabelTests(unittest.TestCase):
    def test_human_applied_label_counts(self):
        gh = FakeEvents([label_event("DemonicPsychoII")])
        self.assertTrue(gh.owner_label(1, ["approved"], "approved"))

    def test_bot_applied_label_does_not_count(self):
        gh = FakeEvents([label_event("DemonicPsychoII"), label_event("DemonicPsychoII", "unlabeled"),
                         label_event("github-actions[bot]", actor_type="Bot")])
        self.assertFalse(gh.owner_label(1, ["approved"], "approved"))

    def test_label_absent(self):
        self.assertFalse(FakeEvents([label_event("DemonicPsychoII")]).owner_label(1, ["bug"], "approved"))


class TargetTests(unittest.TestCase):
    def test_explicit_comma_list(self):
        self.assertEqual(g.target_prs(None, "workflow_dispatch", {}, "7,9"), [7, 9])
        self.assertEqual(g.target_prs(None, "workflow_dispatch", {}, "12"), [12])

    def test_review_workflow_merge_ref_rechecks_only_linked_open_prs(self):
        api = Mock()
        api.repo = "owner/repo"
        api.paginate.return_value = [
            {"number": 3, "head": {"sha": "current"}},
            {"number": 4, "head": {"sha": "other"}},
        ]
        event = {"workflow_run": {"head_sha": "merge", "pull_requests": [{"number": 3}, {"number": 8}]}}
        self.assertEqual(g.target_prs(api, "workflow_run", event, ""), [3])
        event["workflow_run"] = {"head_sha": "other"}
        self.assertEqual(g.target_prs(api, "workflow_run", event, ""), [4])

    def test_event_numbers(self):
        self.assertEqual(g.target_prs(None, "pull_request_target", {"pull_request": {"number": 3}}, ""), [3])
        self.assertEqual(g.target_prs(None, "issue_comment", {"issue": {"number": 4, "pull_request": {"url": "u"}}}, ""), [4])
        self.assertEqual(g.target_prs(None, "issue_comment", {"issue": {"number": 4}}, ""), [])


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


class RevertVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "integration")
        git(self.repo, "config", "user.email", "t@t")
        git(self.repo, "config", "user.name", "t")
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "a.txt").write_text("".join(f"line {i}\n" for i in range(30)))
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.merge = self._merge_feature("feat", "a.txt", 5, "changed 5")
        self.other = self._merge_feature("feat2", "b.txt", None, "new file")

    def tearDown(self):
        self.tmp.cleanup()

    def _merge_feature(self, branch, path, line, text):
        git(self.repo, "checkout", "-qb", branch)
        f = self.repo / path
        if line is None:
            f.write_text(text + "\n")
        else:
            lines = f.read_text().splitlines(keepends=True)
            lines[line] = text + "\n"
            f.write_text("".join(lines))
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", f"change {branch}")
        git(self.repo, "checkout", "-q", "integration")
        git(self.repo, "merge", "-q", "--no-ff", "-m", f"Merge {branch}", branch)
        return git(self.repo, "rev-parse", "HEAD")

    def _revert_branch(self, *merges, extra=False):
        git(self.repo, "checkout", "-qb", "revert", "integration")
        for m in merges:
            git(self.repo, "revert", "--no-edit", "-m", "1", m)
        if extra:
            (self.repo / "c.txt").write_text("sneaky\n")
            git(self.repo, "add", ".")
            git(self.repo, "commit", "-qm", "extra")
        head = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "checkout", "-q", "integration")
        return head

    def test_clean_revert_verified(self):
        head = self._revert_branch(self.merge)
        ok, detail = g.verify_pure_revert(self.repo, "integration", head, [self.merge])
        self.assertTrue(ok, detail)

    def test_two_reverts_verified(self):
        head = self._revert_branch(self.other, self.merge)
        ok, detail = g.verify_pure_revert(self.repo, "integration", head, [self.merge, self.other])
        self.assertTrue(ok, detail)

    def test_extra_commit_rejected(self):
        head = self._revert_branch(self.merge, extra=True)
        self.assertFalse(g.verify_pure_revert(self.repo, "integration", head, [self.merge])[0])

    def test_wrong_merge_named_rejected(self):
        head = self._revert_branch(self.merge)
        self.assertFalse(g.verify_pure_revert(self.repo, "integration", head, [self.other])[0])

    def test_amended_revert_rejected(self):
        head = self._revert_branch(self.merge)
        git(self.repo, "checkout", "-q", head)
        (self.repo / "a.txt").write_text((self.repo / "a.txt").read_text() + "smuggled\n")
        git(self.repo, "commit", "-qam", "amended", "--amend")
        amended = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "checkout", "-q", "integration")
        self.assertFalse(g.verify_pure_revert(self.repo, "integration", amended, [self.merge])[0])

    def test_non_merge_target_rejected(self):
        base_commit = git(self.repo, "rev-list", "--max-parents=0", "HEAD")
        head = self._revert_branch(self.merge)
        self.assertFalse(g.verify_pure_revert(self.repo, "integration", head, [base_commit])[0])

    def test_revert_survives_later_unrelated_merge(self):
        head = self._revert_branch(self.merge)
        self._merge_feature("feat3", "a.txt", 25, "changed 25 later")
        ok, detail = g.verify_pure_revert(self.repo, "integration", head, [self.merge])
        self.assertTrue(ok, detail)

    def test_merge_inside_a_merged_branch_rejected(self):
        """A crafted merge inside a feature branch drops a commit's content, so the PR's net diff
        hides it; "reverting" that inner merge would bring the hidden content back unreviewed."""
        git(self.repo, "checkout", "-qb", "side", "integration")
        (self.repo / "side.txt").write_text("side\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "side")
        git(self.repo, "checkout", "-qb", "crafted", "integration")
        (self.repo / "hidden.txt").write_text("weakened gate\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "hidden")
        git(self.repo, "merge", "-q", "--no-ff", "-m", "crafted", "side")
        git(self.repo, "rm", "-q", "hidden.txt")
        git(self.repo, "commit", "-q", "--amend", "-m", "crafted")
        inner = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "checkout", "-q", "integration")
        git(self.repo, "merge", "-q", "--no-ff", "-m", "Merge crafted", "crafted")
        head = self._revert_branch(inner)
        ok, detail = g.verify_pure_revert(self.repo, "integration", head, [inner])
        self.assertFalse(ok)
        self.assertIn("first-parent", detail)


def gate_source(agent_value, bot_value, agent_indent="        "):
    """Two functions whose surrounding lines are identical, so their hunks differ only in position."""
    def function(name, value, indent):
        return (f"def {name}(approved):\n    checked = approved\n    checked = checked\n    checked = checked\n"
                f"    if checked:\n{indent}return {value}\n    return False\n\n\n")
    return (function("agent", agent_value, agent_indent) + function("bot", bot_value, "        ")).encode()


class TreeExactRevertVerificationTests(unittest.TestCase):
    """A pure revert must produce exactly the tree `git revert -m 1` produces, byte for byte."""

    GATE = ".github/agent-gate/agent_gate.py"
    LATE_NUL = b"A" * 9000 + b"\x00"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "integration")
        for key, value in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false"),
                           ("core.autocrlf", "false")):
            git(self.repo, "config", key, value)
        self.write(".gitattributes", b"rendered/*.svg -diff\n")
        self.write(self.GATE, gate_source("True", "bot_approved"))
        self.write("crlf.txt", b"first\r\nsecond\r\n")
        self.write("trailing.txt", b"value   \nother\t\n")
        self.write("old-name.txt", b"".join(b"renamed line %d\n" % i for i in range(20)))
        self.write("image.bin", b"header\x00first\x00")
        self.write("rendered/overview.svg", b"<svg><text>first</text></svg>\n")
        self.write("late-nul.dat", self.LATE_NUL + b"before\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        git(self.repo, "checkout", "-qb", "feature")
        self.write(self.GATE, gate_source("bot_approved", "bot_approved"))
        self.write("crlf.txt", b"first\r\nchanged\r\n")
        self.write("trailing.txt", b"value \nother\t\t\n")
        git(self.repo, "mv", "old-name.txt", "new-name.txt")
        self.write("image.bin", b"header\x00second\x00")
        self.write("rendered/overview.svg", b"<svg><text>second</text></svg>\n")
        self.write("late-nul.dat", self.LATE_NUL + b"after\n")
        git(self.repo, "commit", "-qam", "change everything")
        git(self.repo, "checkout", "-q", "integration")
        git(self.repo, "merge", "-q", "--no-ff", "-m", "Merge feature", "feature")
        self.merge = git(self.repo, "rev-parse", "HEAD")
        diff = git(self.repo, "diff", "-M", f"{self.merge}^1", self.merge)
        self.assertIn("Binary files", diff)
        self.assertIn("rename from old-name.txt", diff)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, content):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def revert_branch(self, tamper=None):
        git(self.repo, "checkout", "-qb", "revert", "integration")
        git(self.repo, "revert", "--no-edit", "-m", "1", self.merge)
        if tamper is not None:
            self.write(*tamper)
            git(self.repo, "commit", "-qa", "--amend", "--no-edit")
        head = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "checkout", "-q", "integration")
        git(self.repo, "branch", "-qD", "revert")
        return head

    def tampered_reverts(self):
        return {
            "re-indented": (self.GATE, gate_source("True", "bot_approved", agent_indent="    ")),
            "statement added": (self.GATE, gate_source("True", "bot_approved").replace(
                b"return False", b"return True\n    return False", 1)),
            "wrong function": (self.GATE, gate_source("bot_approved", "True")),
            "late NUL file": ("late-nul.dat", self.LATE_NUL + b"smuggled\n"),
            "altered binary": ("image.bin", b"header\x00smuggled\x00"),
            "altered non-diffable": ("rendered/overview.svg", b"<svg><text>smuggled</text></svg>\n"),
        }

    def evaluate(self, head):
        verification = g.verify_pure_revert(self.repo, "integration", head, [self.merge])
        return g.evaluate(inputs(body=body_with_class("revert"), comments=[], changed_files=[self.GATE],
                                 revert=verification, require_owner_approval=False))

    def test_exact_revert_verifies(self):
        head = self.revert_branch()
        ok, detail = g.verify_pure_revert(self.repo, "integration", head, [self.merge])
        self.assertTrue(ok, detail)
        d = self.evaluate(head)
        self.assertEqual(d.state, "success", d.items)

    def test_tampered_revert_does_not_verify(self):
        for name, tamper in self.tampered_reverts().items():
            with self.subTest(case=name):
                head = self.revert_branch(tamper)
                ok, detail = g.verify_pure_revert(self.repo, "integration", head, [self.merge])
                self.assertFalse(ok, detail)
                d = self.evaluate(head)
                self.assertEqual(d.state, "failure", d.items)
                failures = " ".join(t for s, t in d.items if s == "fail")
                self.assertIn("not a verified pure revert", failures)
                self.assertIn("separate `policy` PR", failures)


class AutomatedPolicyTests(unittest.TestCase):
    def bot(self, state="APPROVED", sha=HEAD, uid=136622811, login="coderabbitai[bot]", rid=99):
        return {"id": rid, "state": state, "commit_id": sha,
                "user": {"type": "Bot", "login": login, "id": uid}}

    def test_feature_policy_and_policy_paths_need_no_human_when_migrated(self):
        for klass in ("quick-fix", "feature", "policy"):
            decision = g.evaluate(inputs(body=body_with_class(klass), require_owner_approval=False,
                                         changed_files=["AGENTS.md"], owner_approval_paths=POLICY_PATHS))
            self.assertEqual(decision.state, "success", decision.items)

    def test_only_required_checks_block_under_migrated_policy(self):
        optional = {"id": 300, "name": "optional-nitpicks", "status": "completed", "conclusion": "failure"}
        self.assertEqual(g.evaluate(inputs(required_checks_only=True,
                                          check_runs=green_ci() + [optional],
                                          statuses=[{"context": "optional-review", "state": "pending"}])).state,
                         "success")
        missing = g.evaluate(inputs(required_checks_only=True, required_checks=["missing"]))
        self.assertEqual(missing.state, "pending")

    def test_native_coderabbit_approval_does_not_replace_the_agent_review(self):
        options = {"review_bots": {"coderabbitai[bot]": 136622811}, "native_reviews": [self.bot()]}
        decision = g.evaluate(inputs(comments=[], **options))
        self.assertEqual(decision.state, "pending", decision.items)
        self.assertIn("waiting for an agent review", decision.description)
        decision = g.evaluate(inputs(**options))
        self.assertEqual(decision.state, "success", decision.items)

    def test_dependabot_pr_without_agent_metadata_needs_the_agent_review_next_to_native_approval(self):
        options = {"body": "Bumps the actions group with 3 updates.",
                   "review_bots": {"coderabbitai[bot]": 136622811}}
        d = g.evaluate(inputs(comments=[], native_reviews=[self.bot()], **options))
        self.assertEqual(d.state, "pending", d.items)
        d = g.evaluate(inputs(native_reviews=[self.bot()], **options))
        self.assertEqual(d.state, "success", d.items)
        for bot_review in (self.bot(sha=OLD), self.bot(state="CHANGES_REQUESTED")):
            with self.subTest(review=bot_review):
                d = g.evaluate(inputs(comments=[], native_reviews=[bot_review], **options))
                self.assertNotEqual(d.state, "success", d.items)

    def test_native_approval_never_bypasses_unresolved_threads(self):
        decision = g.evaluate(inputs(comments=[], review_bots={"coderabbitai[bot]": 136622811},
                                     native_reviews=[self.bot()], unresolved_threads=1))
        self.assertEqual(decision.state, "failure")

    def test_stale_changed_and_dismissed_bot_reviews_do_not_approve(self):
        for review in (self.bot(sha=OLD), self.bot(state="CHANGES_REQUESTED"),
                       self.bot(state="DISMISSED")):
            with self.subTest(review=review):
                decision = g.evaluate(inputs(comments=[], review_bots={"coderabbitai[bot]": 136622811},
                                             native_reviews=[review]))
                self.assertNotEqual(decision.state, "success")

    def test_stale_native_approval_allows_valid_current_head_agent_fallback(self):
        options = {"review_bots": {"coderabbitai[bot]": 136622811},
                   "native_reviews": [self.bot(sha=OLD)]}
        decision = g.evaluate(inputs(**options))
        self.assertEqual(decision.state, "success", decision.items)
        for comments in ([], [review(sha=OLD)], [review(verdict="changes")],
                         [review(session="auth-1")], [review(association="NONE")]):
            with self.subTest(comments=comments):
                self.assertNotEqual(g.evaluate(inputs(comments=comments, **options)).state, "success")
        self.assertEqual(g.evaluate(inputs(unresolved_threads=1, **options)).state, "failure")
        self.assertNotEqual(g.evaluate(inputs(check_runs=[], **options)).state, "success")

    def test_native_changes_requests_and_dismissals_prevent_agent_fallback(self):
        for state in ("CHANGES_REQUESTED", "DISMISSED"):
            for sha in (HEAD, OLD):
                with self.subTest(state=state, sha=sha):
                    decision = g.evaluate(inputs(review_bots={"coderabbitai[bot]": 136622811},
                                                 native_reviews=[self.bot(state=state, sha=sha)]))
                    self.assertNotEqual(decision.state, "success")

    def test_recorded_fallback_replaces_only_stale_native_decisions(self):
        marker = f"<!-- review-fallback sha={HEAD} reason=rate-limited -->"
        options = {"review_bots": {"coderabbitai[bot]": 136622811}}
        for state in ("CHANGES_REQUESTED", "DISMISSED"):
            options["native_reviews"] = [self.bot(state=state, sha=OLD)]
            comments = [comment(marker), review()]
            self.assertEqual(g.evaluate(inputs(comments=comments, **options)).state, "success")
            for invalid_marker in (comment(marker.replace(HEAD, OLD)),
                                   comment(marker.replace("rate-limited", "optional")),
                                   comment(marker, association="NONE"),
                                   comment(marker, login="github-actions[bot]"),
                                   comment("```\n" + marker + "\n```"),
                                   comment("> " + marker),
                                   comment("    " + marker), comment("\t" + marker)):
                self.assertNotEqual(g.evaluate(inputs(comments=[invalid_marker, review()], **options)).state, "success")
            for invalid_review in (review(sha=OLD), review(verdict="changes"),
                                   review(session="auth-1"), review(association="NONE")):
                self.assertNotEqual(g.evaluate(inputs(comments=[comment(marker), invalid_review], **options)).state, "success")
            for changes in ({"unresolved_threads": 1}, {"check_runs": []}, {"draft": True},
                            {"body": BODY + "\n<!-- owner-question id=open -->\nDecision?"}):
                self.assertNotEqual(g.evaluate(inputs(comments=comments, **options, **changes)).state, "success")
            options["native_reviews"] = [self.bot(state=state, sha=HEAD)]
            self.assertNotEqual(g.evaluate(inputs(comments=comments, **options)).state, "success")

    def test_comment_only_bot_review_retains_independent_agent_fallback(self):
        options = {"review_bots": {"coderabbitai[bot]": 136622811},
                   "native_reviews": [self.bot(state="COMMENTED")]}
        self.assertEqual(g.evaluate(inputs(**options)).state, "success")
        self.assertEqual(g.evaluate(inputs(comments=[], **options)).state, "pending")
        self.assertEqual(g.evaluate(inputs(unresolved_threads=1, **options)).state, "failure")

    def test_matching_login_without_immutable_identity_never_counts(self):
        for review in (self.bot(uid=1), self.bot(login="another[bot]")):
            decision = g.evaluate(inputs(comments=[], review_bots={"coderabbitai[bot]": 136622811},
                                         native_reviews=[review]))
            self.assertEqual(decision.state, "pending")

    def test_later_comment_does_not_dismiss_a_native_approval(self):
        decision = g.evaluate(inputs(review_bots={"coderabbitai[bot]": 136622811},
                                     native_reviews=[self.bot(), self.bot(state="COMMENTED", rid=100)]))
        self.assertEqual(decision.state, "success")


def submitted(verdict="approve", sha=HEAD, session="rev-1", state="COMMENTED", submitted_at="2026-10-02T10:00:00Z",
              association="OWNER", login="DemonicPsychoII", rid=900):
    body = f"<!-- agent-review verdict={verdict} sha={sha} reviewer=codex/gpt-5.5 session={session} -->\nVerdict."
    return {"id": rid, "body": body, "state": state, "submitted_at": submitted_at,
            "user": {"login": login}, "author_association": association}


class ReviewBodyTests(unittest.TestCase):
    def test_review_submission_body_approves_current_sha(self):
        d = g.evaluate(inputs(comments=[], review_bodies=g.review_records([submitted()])))
        self.assertEqual(d.state, "success", d.items)

    def test_review_submission_for_stale_sha_is_pending(self):
        d = g.evaluate(inputs(comments=[], review_bodies=g.review_records([submitted(sha=OLD)])))
        self.assertEqual(d.state, "pending")
        self.assertIn("re-review", d.description)

    def test_later_changes_in_either_source_overrides_approve(self):
        later = "2026-10-02T11:00:00Z"
        changes_review = g.review_records([submitted(verdict="changes", submitted_at=later, rid=2)])
        self.assertEqual(g.evaluate(inputs(comments=[review()], review_bodies=changes_review)).state, "failure")
        approve_review = g.review_records([submitted()])
        changes_comment = review(verdict="changes", created=later, cid=2)
        self.assertEqual(g.evaluate(inputs(comments=[changes_comment], review_bodies=approve_review)).state,
                         "failure")
        latest = g.review_records([submitted(submitted_at="2026-10-02T12:00:00Z", rid=3)])
        self.assertEqual(g.evaluate(inputs(comments=[changes_comment], review_bodies=latest)).state, "success")

    def test_same_second_tie_across_sources_fails_closed(self):
        changes = g.review_records([submitted(verdict="changes", rid=1)])
        self.assertEqual(g.evaluate(inputs(comments=[review(cid=999)], review_bodies=changes)).state, "failure")

    def test_untrusted_pending_and_dismissed_review_submissions_ignored(self):
        for submission in (submitted(association="NONE", login="stranger"),
                           submitted(login="github-actions[bot]"),
                           submitted(state="DISMISSED"),
                           submitted(state="PENDING", submitted_at=None)):
            with self.subTest(review=submission):
                d = g.evaluate(inputs(comments=[], review_bodies=g.review_records([submission])))
                self.assertEqual(d.state, "pending", d.items)

    def test_review_submission_from_author_session_fails(self):
        d = g.evaluate(inputs(comments=[], review_bodies=g.review_records([submitted(session="auth-1")])))
        self.assertEqual(d.state, "failure")
        self.assertIn("author session", d.description)


def carried(allowed=True, sha=OLD, detail="the PR's own diff against integration is identical"):
    return g.CarryForward(sha, allowed, detail)


class CarryForwardEvaluateTests(unittest.TestCase):
    def test_identical_diff_carries_the_approval_forward(self):
        d = g.evaluate(inputs(comments=[review(sha=OLD)], approval_carry_forward=carried()))
        self.assertEqual(d.state, "success", d.items)
        self.assertTrue(any(f"approval carried forward from {OLD[:7]}" in text for _, text in d.items), d.items)
        self.assertTrue(any("were not reviewed" in text for _, text in d.items), d.items)

    def test_review_body_approval_is_carried_forward(self):
        d = g.evaluate(inputs(comments=[], review_bodies=g.review_records([submitted(sha=OLD)]),
                              approval_carry_forward=carried()))
        self.assertEqual(d.state, "success", d.items)

    def test_disallowed_or_mismatched_carry_forward_is_pending(self):
        for carry in (carried(allowed=False, detail="the PR's own diff against integration changed"),
                      carried(sha="c" * 40), None):
            with self.subTest(carry=carry):
                d = g.evaluate(inputs(comments=[review(sha=OLD)], approval_carry_forward=carry))
                self.assertEqual(d.state, "pending", d.items)
                self.assertIn("cannot be carried forward", d.description)

    def test_newer_changes_verdict_prevents_carry_forward(self):
        changes = review(verdict="changes", sha=OLD, created="2026-10-02T11:00:00Z", cid=2)
        d = g.evaluate(inputs(comments=[review(sha=OLD), changes], approval_carry_forward=carried()))
        self.assertEqual(d.state, "pending", d.items)
        self.assertIn("requested changes", d.description)

    def test_carried_self_review_still_fails(self):
        d = g.evaluate(inputs(comments=[review(sha=OLD, session="auth-1")], approval_carry_forward=carried()))
        self.assertEqual(d.state, "failure")
        self.assertIn("author session", d.description)

    def test_carry_forward_never_waives_ci_threads_or_owner_questions(self):
        question = comment("<!-- owner-question id=q1 -->\nKeep it?", cid=51)
        for options in ({"unresolved_threads": 1}, {"check_runs": []},
                        {"comments": [review(sha=OLD), question]}):
            with self.subTest(options=options):
                values = {"comments": [review(sha=OLD)], "approval_carry_forward": carried(), **options}
                self.assertNotEqual(g.evaluate(inputs(**values)).state, "success")


def changed_file(name="src/a.c", status="modified", patch="@@ -1 +1 @@\n-a\n+b", previous=None):
    entry = {"filename": name, "status": status}
    if patch is not None:
        entry["patch"] = patch
    if previous:
        entry["previous_filename"] = previous
    return entry


def force_push_timeline(pairs):
    nodes = [{"beforeCommit": {"oid": before} if before else None, "afterCommit": {"oid": after}}
             for before, after in pairs]
    return {"repository": {"pullRequest": {"timelineItems": {
        "nodes": nodes, "pageInfo": {"hasNextPage": False, "endCursor": None}}}}}


class FakeCompare(g.GitHub):
    def __init__(self, comparisons, pull_request_commits, force_pushes=()):
        super().__init__("o/r", "token")
        self.comparisons, self.pull_request_commits, self.requested = comparisons, pull_request_commits, []
        self.force_pushes = list(force_pushes)

    def get(self, path):
        self.requested.append(path)
        commit = path.rsplit("...", 1)[1]
        files = self.comparisons.get(commit)
        if files is None:
            raise urllib.error.HTTPError(path, 404, "Not Found", {}, None)
        return {"files": files}

    def paginate(self, path, key=None):
        return [{"sha": sha} for sha in self.pull_request_commits]

    def graphql(self, query, variables):
        self.requested.append("graphql:timelineItems")
        return force_push_timeline(self.force_pushes)


class CarryForwardApiTests(unittest.TestCase):
    def carry(self, approved_files, head_files, pull_request_commits=(OLD, HEAD), force_pushes=()):
        comparisons = {HEAD: head_files}
        if approved_files is not None:
            comparisons[OLD] = approved_files
        gh = FakeCompare(comparisons, list(pull_request_commits), force_pushes)
        return gh.approval_carry_forward(7, "integration", OLD, HEAD), gh

    def test_identical_diff_after_base_merge_is_carried(self):
        result, gh = self.carry([changed_file(), changed_file("b.md", "added")],
                                [changed_file("b.md", "added"), changed_file()])
        self.assertTrue(result.allowed, result.detail)
        self.assertIn("a commit of this PR", result.detail)
        self.assertEqual(gh.requested, [f"repos/o/r/compare/integration...{OLD}",
                                        f"repos/o/r/compare/integration...{HEAD}"])

    def test_head_replaced_by_a_force_push_is_carried(self):
        for force_pushes in ([(OLD, HEAD)], [(None, OLD), ("c" * 40, HEAD)]):
            with self.subTest(force_pushes=force_pushes):
                result, _ = self.carry([changed_file()], [changed_file()], pull_request_commits=(HEAD,),
                                       force_pushes=force_pushes)
                self.assertTrue(result.allowed, result.detail)
                self.assertIn("before a force-push", result.detail)

    def test_unrelated_resolvable_commit_with_identical_diff_is_not_carried(self):
        result, gh = self.carry([changed_file()], [changed_file()], pull_request_commits=(HEAD,),
                                force_pushes=[("c" * 40, HEAD)])
        self.assertFalse(result.allowed)
        self.assertIn("neither a commit of this PR", result.detail)
        self.assertEqual(gh.requested, ["graphql:timelineItems"])

    def test_force_pushed_head_no_longer_resolvable_is_not_carried(self):
        result, _ = self.carry(None, [changed_file()], pull_request_commits=(HEAD,), force_pushes=[(OLD, HEAD)])
        self.assertFalse(result.allowed)
        self.assertIn("not resolvable", result.detail)

    def test_current_commit_skips_the_force_push_lookup(self):
        _, gh = self.carry([changed_file()], [changed_file()])
        self.assertNotIn("graphql:timelineItems", gh.requested)

    def test_changed_patch_status_name_or_rename_source_is_not_carried(self):
        for head_file in (changed_file(patch="@@ -1 +1 @@\n-a\n+c"), changed_file(status="added"),
                          changed_file(name="src/other.c"), changed_file(status="renamed", previous="src/x.c")):
            with self.subTest(head_file=head_file):
                approved = changed_file(status="renamed", previous="src/y.c") if "previous_filename" in head_file \
                    else changed_file()
                result, _ = self.carry([approved], [head_file])
                self.assertFalse(result.allowed)
                self.assertIn("changed since", result.detail)

    def test_extra_file_is_not_carried(self):
        result, _ = self.carry([changed_file()], [changed_file(), changed_file("c.txt", "added")])
        self.assertFalse(result.allowed)

    def test_missing_patch_is_not_carried(self):
        for approved, head in (([changed_file(patch=None)], [changed_file(patch=None)]),
                               ([changed_file()], [changed_file(patch=None)])):
            with self.subTest(approved=approved, head=head):
                result, _ = self.carry(approved, head)
                self.assertFalse(result.allowed)
                self.assertIn("no patch", result.detail)

    def test_truncated_file_list_is_not_carried(self):
        files = [changed_file(f"f{index}.c") for index in range(g.COMPARE_FILE_LIMIT)]
        result, _ = self.carry(files, files)
        self.assertFalse(result.allowed)
        self.assertIn("truncated", result.detail)


class PendingAndTerminalTests(unittest.TestCase):
    def test_waiting_for_review_while_ci_runs_is_pending(self):
        runs = green_ci() + [{"id": 12, "name": "mission-control-budget-tests", "status": "in_progress",
                              "conclusion": None}]
        self.assertEqual(g.evaluate(inputs(comments=[], check_runs=runs)).state, "pending")

    def test_required_check_still_queued_is_pending(self):
        runs = [{"id": 12, "name": "mission-control-budget-tests", "status": "queued", "conclusion": None}]
        d = g.evaluate(inputs(check_runs=runs, required_checks_only=True))
        self.assertEqual(d.state, "pending", d.items)
        self.assertIn("queued", d.description)

    def test_changes_verdict_on_head_fails(self):
        self.assertEqual(g.evaluate(inputs(comments=[review(verdict="changes")])).state, "failure")

    def test_changes_verdict_on_older_commit_waits_for_re_review(self):
        d = g.evaluate(inputs(comments=[review(verdict="changes", sha=OLD)]))
        self.assertEqual(d.state, "pending")
        self.assertIn("requested changes", d.description)

    def test_newest_malformed_marker_fails(self):
        for marker in ("<!-- agent-review verdict=approve sha=abc1234 reviewer=codex/gpt-5.5 session=r -->",
                       f"<!-- agent-review verdict=lgtm sha={HEAD} reviewer=codex/gpt-5.5 session=r -->",
                       f"<!-- agent-review verdict=approve sha={HEAD} -->"):
            with self.subTest(marker=marker):
                broken = comment(marker, created="2026-10-02T11:00:00Z", cid=2)
                d = g.evaluate(inputs(comments=[review(), broken]))
                self.assertEqual(d.state, "failure", d.items)
                self.assertIn("malformed", d.description)
                malformed_review_body = {"id": 3, "body": marker, "state": "COMMENTED",
                                         "submitted_at": "2026-10-02T11:00:00Z", "user": {"login": "DemonicPsychoII"},
                                         "author_association": "OWNER"}
                d = g.evaluate(inputs(review_bodies=g.review_records([malformed_review_body])))
                self.assertEqual(d.state, "failure", d.items)

    def test_superseded_quoted_or_untrusted_malformed_marker_is_ignored(self):
        marker = "<!-- agent-review verdict=approve sha=abc1234 reviewer=codex/gpt-5.5 session=r -->"
        older = comment(marker, created="2026-10-02T09:00:00Z", cid=2)
        self.assertEqual(g.evaluate(inputs(comments=[older, review()])).state, "success")
        for ignored in (comment("> " + marker, created="2026-10-02T11:00:00Z", cid=3),
                        comment("```\n" + marker + "\n```", created="2026-10-02T11:00:00Z", cid=4),
                        comment(marker, created="2026-10-02T11:00:00Z", association="NONE", login="x", cid=5)):
            with self.subTest(comment=ignored["body"]):
                self.assertEqual(g.evaluate(inputs(comments=[review(), ignored])).state, "success")


class ScopeGuardTests(unittest.TestCase):
    GUARDED = (".github/agent-gate/agent_gate.py", ".github/agent-gate/fixtures/x.md",
               ".github/workflows/quality-gates.yml")

    def test_non_policy_agent_pr_changing_gate_or_workflows_fails(self):
        for klass in ("quick-fix", "feature", "revert"):
            for path in self.GUARDED:
                with self.subTest(klass=klass, path=path):
                    d = g.evaluate(inputs(body=body_with_class(klass), changed_files=["src/a.c", path],
                                          require_owner_approval=False))
                    self.assertEqual(d.state, "failure", d.items)
                    text = " ".join(t for s, t in d.items if s == "fail")
                    self.assertIn("separate `policy` PR", text)
                    self.assertIn("code under test", text)

    def test_policy_class_may_change_gate_and_workflows(self):
        d = g.evaluate(inputs(body=body_with_class("policy"), changed_files=list(self.GUARDED),
                              require_owner_approval=False))
        self.assertEqual(d.state, "success", d.items)

    def test_verified_pure_revert_may_change_gate_and_workflows(self):
        d = g.evaluate(inputs(body=body_with_class("revert"), comments=[], changed_files=list(self.GUARDED),
                              revert=(True, "reverts abc1234"), require_owner_approval=False))
        self.assertEqual(d.state, "success", d.items)
        self.assertIn(("ok", f"changes CI or the gate ({self.GUARDED[0]}) only as a verified pure revert"), d.items)

    def test_unverified_revert_changing_gate_or_workflows_fails_the_guard(self):
        d = g.evaluate(inputs(body=body_with_class("revert"), changed_files=list(self.GUARDED),
                              revert=(False, "branch contains extra commits"), require_owner_approval=False))
        self.assertEqual(d.state, "failure", d.items)
        self.assertIn("separate `policy` PR", " ".join(t for s, t in d.items if s == "fail"))

    def test_other_github_paths_are_not_guarded(self):
        d = g.evaluate(inputs(changed_files=[".github/pull_request_template.md", "AGENTS.md"],
                              require_owner_approval=False))
        self.assertEqual(d.state, "success", d.items)

    def test_renamed_out_of_guarded_path_counts(self):
        d = g.evaluate(inputs(changed_files=["tools/gate.py", ".github/agent-gate/agent_gate.py"],
                              require_owner_approval=False))
        self.assertEqual(d.state, "failure")

    def test_pr_without_agent_author_marker_skips_the_guard(self):
        for body in ("Bumps actions/checkout from 6 to 7.", "Human edit of the workflow."):
            with self.subTest(body=body):
                d = g.evaluate(inputs(body=body, changed_files=list(self.GUARDED), require_owner_approval=False))
                self.assertEqual(d.state, "success", d.items)


class CodeRabbitRequestTests(unittest.TestCase):
    BOTS = {"coderabbitai[bot]": 136622811}

    def bot(self, state="APPROVED", sha=HEAD):
        return {"id": 99, "state": state, "commit_id": sha,
                "user": {"type": "Bot", "login": "coderabbitai[bot]", "id": 136622811}}

    def test_unlabelled_pr_without_coderabbit_review_needs_only_the_agent_review(self):
        d = g.evaluate(inputs(review_bots=self.BOTS))
        self.assertEqual(d.state, "success", d.items)

    def test_label_waits_for_coderabbit_even_with_agent_approval(self):
        d = g.evaluate(inputs(review_bots=self.BOTS, coderabbit_label=True))
        self.assertEqual(d.state, "pending", d.items)
        self.assertIn("CodeRabbit", d.description)

    def test_label_with_coderabbit_approval_still_waits_for_the_agent_review(self):
        d = g.evaluate(inputs(comments=[], review_bots=self.BOTS, coderabbit_label=True,
                              native_reviews=[self.bot()]))
        self.assertEqual(d.state, "pending", d.items)
        self.assertIn(("ok", f"approved at {HEAD[:7]} by coderabbitai[bot]"), d.items)

    def test_label_with_coderabbit_approval_and_agent_approval_passes(self):
        d = g.evaluate(inputs(review_bots=self.BOTS, coderabbit_label=True, native_reviews=[self.bot()]))
        self.assertEqual(d.state, "success", d.items)

    def test_label_with_recorded_fallback_uses_the_agent_review(self):
        fallback = comment(f"<!-- review-fallback sha={HEAD} reason=unavailable -->", cid=60)
        d = g.evaluate(inputs(comments=[fallback, review()], review_bots=self.BOTS, coderabbit_label=True))
        self.assertEqual(d.state, "success", d.items)

    def test_existing_coderabbit_review_is_still_required_without_label(self):
        d = g.evaluate(inputs(review_bots=self.BOTS, native_reviews=[self.bot(state="CHANGES_REQUESTED")]))
        self.assertEqual(d.state, "failure", d.items)
        d = g.evaluate(inputs(review_bots=self.BOTS, native_reviews=[self.bot(state="CHANGES_REQUESTED", sha=OLD)]))
        self.assertEqual(d.state, "pending", d.items)


class FakePublish(g.GitHub):
    def __init__(self):
        super().__init__("o/r", "token")
        self.calls = []

    def request(self, method, path, body=None):
        self.calls.append((method, path))
        return None, {}


class StickyReportTests(unittest.TestCase):
    def test_report_is_edited_only_when_its_content_changes(self):
        decision = g.evaluate(inputs())
        old_report = g.render_report(inputs(), decision, "https://example.invalid/runs/1")
        sticky = {"id": 70, "body": old_report, "created_at": "2026-10-02T08:00:00Z",
                  "login": "github-actions[bot]", "association": "NONE"}
        unchanged = inputs(comments=[review(), sticky])
        gh = FakePublish()
        g.publish(gh, unchanged, g.evaluate(unchanged), "https://example.invalid/runs/2")
        self.assertEqual([method for method, _ in gh.calls], ["POST"])
        changed = inputs(comments=[sticky])
        gh = FakePublish()
        g.publish(gh, changed, g.evaluate(changed), "https://example.invalid/runs/3")
        self.assertEqual([method for method, _ in gh.calls], ["POST", "PATCH"])


MALFORMED_CHANGES = "<!-- agent-review verdict=changes sha=abc1234 reviewer=codex/gpt-5.5 session=rev-2 -->"


class TerminalVerdictPrecedenceTests(unittest.TestCase):
    BOTS = {"coderabbitai[bot]": 136622811}

    def native(self, state="APPROVED", sha=HEAD, rid=99):
        return {"id": rid, "state": state, "commit_id": sha,
                "user": {"type": "Bot", "login": "coderabbitai[bot]", "id": 136622811}}

    def terminal_cases(self):
        return {
            "changes on head": {"comments": [review(verdict="changes")]},
            "self-review": {"comments": [review(session="auth-1")]},
            "malformed newest marker": {"comments": [review(), comment(MALFORMED_CHANGES,
                                                                       created="2026-10-02T11:00:00Z", cid=2)]},
        }

    def test_coderabbit_label_wait_does_not_hide_terminal_agent_verdicts(self):
        for name, options in self.terminal_cases().items():
            with self.subTest(case=name):
                d = g.evaluate(inputs(review_bots=self.BOTS, coderabbit_label=True, **options))
                self.assertEqual(d.state, "failure", d.items)

    def test_coderabbit_label_wait_reports_the_agent_review_as_well(self):
        d = g.evaluate(inputs(review_bots=self.BOTS, coderabbit_label=True))
        self.assertEqual(d.state, "pending", d.items)
        texts = [text for _, text in d.items]
        self.assertTrue(any("CodeRabbit" in text for text in texts), texts)
        self.assertTrue(any(text.startswith(f"approved at {HEAD[:7]}") for text in texts), texts)

    def test_native_approval_does_not_hide_a_later_agent_changes_verdict(self):
        changes_body = g.review_records([submitted(verdict="changes", submitted_at="2026-10-02T11:00:00Z")])
        d = g.evaluate(inputs(comments=[review()], review_bodies=changes_body, review_bots=self.BOTS,
                              native_reviews=[self.native()]))
        self.assertEqual(d.state, "failure", d.items)
        self.assertIn("requests changes", d.description)

    def test_native_approval_does_not_hide_other_terminal_agent_verdicts(self):
        for name, options in self.terminal_cases().items():
            with self.subTest(case=name):
                d = g.evaluate(inputs(review_bots=self.BOTS, native_reviews=[self.native()], **options))
                self.assertEqual(d.state, "failure", d.items)

    def test_native_approval_waits_for_re_review_after_older_commit_changes_verdict(self):
        changes = review(verdict="changes", sha=OLD)
        d = g.evaluate(inputs(comments=[changes], review_bots=self.BOTS, native_reviews=[self.native()]))
        self.assertEqual(d.state, "pending", d.items)
        approval = review(created="2026-10-02T11:00:00Z", cid=2)
        d = g.evaluate(inputs(comments=[changes, approval], review_bots=self.BOTS, native_reviews=[self.native()]))
        self.assertEqual(d.state, "success", d.items)


class MarkerAttemptTests(unittest.TestCase):
    def test_later_malformed_marker_in_the_same_body_is_not_hidden_by_a_valid_one(self):
        body = review(sha=OLD)["body"] + "\n" + MALFORMED_CHANGES
        self.assertEqual(g.review_attempts(body)[1], None)
        self.assertIsNone(g.parse_review(body))
        d = g.evaluate(inputs(comments=[comment(body, created="2026-10-02T11:00:00Z")]))
        self.assertEqual(d.state, "failure", d.items)
        self.assertIn("malformed", d.description)
        record = submitted(sha=OLD)
        record["body"] += "\n" + MALFORMED_CHANGES
        d = g.evaluate(inputs(comments=[], review_bodies=g.review_records([record])))
        self.assertEqual(d.state, "failure", d.items)

    def test_valid_marker_after_a_malformed_one_in_the_same_body_is_the_verdict(self):
        body = MALFORMED_CHANGES + "\n" + review()["body"]
        self.assertEqual(g.parse_review(body)["sha"], HEAD)
        self.assertEqual(g.evaluate(inputs(comments=[comment(body)])).state, "success")

    def test_each_attempt_is_parsed_separately(self):
        body = "\n".join([review(verdict="changes", sha=OLD)["body"], MALFORMED_CHANGES, review()["body"]])
        attempts = g.review_attempts(body)
        self.assertEqual([attempt and attempt["verdict"] for attempt in attempts], ["changes", None, "approve"])


class FakeGather(g.GitHub):
    def __init__(self, base="integration", comments=(), reviews=(), pull_request_commits=(OLD, HEAD),
                 force_pushes=(), comparisons=None, labels=()):
        super().__init__("o/r", "token")
        self.base, self.comments, self.reviews = base, list(comments), list(reviews)
        self.pull_request_commits, self.force_pushes = list(pull_request_commits), list(force_pushes)
        self.comparisons = comparisons if comparisons is not None else {OLD: [changed_file()], HEAD: [changed_file()]}
        self.labels = list(labels)
        self.requested = []

    def get(self, path):
        self.requested.append(path)
        if path == "repos/o/r/pulls/7":
            return {"state": "open", "draft": False, "body": BODY, "labels": [{"name": n} for n in self.labels],
                    "head": {"sha": HEAD, "repo": {"full_name": "o/r"}}, "base": {"ref": self.base}}
        if path.startswith(f"repos/o/r/commits/{HEAD}/status"):
            return {"statuses": []}
        if "/compare/" in path:
            files = self.comparisons.get(path.rsplit("...", 1)[1])
            if files is None:
                raise urllib.error.HTTPError(path, 404, "Not Found", {}, None)
            return {"files": files}
        raise AssertionError(f"unexpected GET {path}")

    def paginate(self, path, key=None):
        self.requested.append(path)
        if path.endswith("/issues/7/comments"):
            return [{"id": c["id"], "body": c["body"], "created_at": c["created_at"], "user": {"login": c["login"]},
                     "author_association": c["association"]} for c in self.comments]
        if path.endswith("/pulls/7/reviews"):
            return self.reviews
        if path.endswith("/pulls/7/commits"):
            return [{"sha": sha} for sha in self.pull_request_commits]
        if "/check-runs" in path:
            return green_ci()
        if path.endswith("/pulls/7/files") or "/rules/branches/" in path:
            return []
        raise AssertionError(f"unexpected paginate {path}")

    def graphql(self, query, variables):
        if "timelineItems" in query:
            self.requested.append("graphql:timelineItems")
            return force_push_timeline(self.force_pushes)
        return {"repository": {"pullRequest": {"reviewThreads": {
            "nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}}}}


GATHER_CONFIG = {"required_checks": ["mission-control-budget-tests"], "require_owner_approval": False,
                 "required_checks_only": True}


class GatherCarryForwardTests(unittest.TestCase):
    def compare_paths(self, gh):
        return [path for path in gh.requested if "/compare/" in path]

    def test_review_body_only_approval_is_carried_forward(self):
        gh = FakeGather(reviews=[submitted(sha=OLD)])
        gathered = g.gather(gh, 7, GATHER_CONFIG, None)
        self.assertEqual(len(gathered.review_bodies), 1)
        self.assertTrue(gathered.approval_carry_forward.allowed, gathered.approval_carry_forward)
        self.assertEqual(self.compare_paths(gh), [f"repos/o/r/compare/integration...{OLD}",
                                                  f"repos/o/r/compare/integration...{HEAD}"])
        decision = g.evaluate(gathered)
        self.assertEqual(decision.state, "success", decision.items)
        self.assertTrue(any("carried forward" in text for _, text in decision.items))

    def test_compare_uses_the_current_base_branch(self):
        gh = FakeGather(base="feature/lower-layer", comments=[review(sha=OLD)])
        gathered = g.gather(gh, 7, GATHER_CONFIG, None)
        self.assertTrue(gathered.approval_carry_forward.allowed)
        self.assertEqual(self.compare_paths(gh), [f"repos/o/r/compare/feature%2Flower-layer...{OLD}",
                                                  f"repos/o/r/compare/feature%2Flower-layer...{HEAD}"])

    def test_changed_own_diff_against_the_new_base_is_not_carried(self):
        comparisons = {OLD: [changed_file()], HEAD: [changed_file(patch="@@ -1 +1 @@\n-a\n+other")]}
        gh = FakeGather(comments=[review(sha=OLD)], comparisons=comparisons)
        gathered = g.gather(gh, 7, GATHER_CONFIG, None)
        self.assertFalse(gathered.approval_carry_forward.allowed)
        self.assertEqual(g.evaluate(gathered).state, "pending")

    def test_commit_absent_from_the_pull_request_is_not_carried(self):
        gh = FakeGather(comments=[review(sha=OLD)], pull_request_commits=(HEAD,))
        gathered = g.gather(gh, 7, GATHER_CONFIG, None)
        self.assertFalse(gathered.approval_carry_forward.allowed)
        self.assertEqual(self.compare_paths(gh), [])
        self.assertEqual(g.evaluate(gathered).state, "pending")

    def test_commit_present_through_a_force_push_is_carried(self):
        gh = FakeGather(comments=[review(sha=OLD)], pull_request_commits=(HEAD,), force_pushes=[(OLD, HEAD)])
        gathered = g.gather(gh, 7, GATHER_CONFIG, None)
        self.assertTrue(gathered.approval_carry_forward.allowed, gathered.approval_carry_forward)

    def test_no_carry_forward_lookup_when_newest_verdict_is_changes_or_at_head(self):
        later_changes = review(verdict="changes", sha=OLD, created="2026-10-02T11:00:00Z", cid=2)
        for comments in ([review(sha=OLD), later_changes], [review()]):
            with self.subTest(comments=[c["body"][:40] for c in comments]):
                gh = FakeGather(comments=comments)
                gathered = g.gather(gh, 7, GATHER_CONFIG, None)
                self.assertIsNone(gathered.approval_carry_forward)
                self.assertEqual(self.compare_paths(gh), [])
                self.assertNotIn("repos/o/r/pulls/7/commits", gh.requested)

    def test_coderabbit_label_is_gathered(self):
        gathered = g.gather(FakeGather(labels=["coderabbit"]), 7, GATHER_CONFIG, None)
        self.assertTrue(gathered.coderabbit_label)


if __name__ == "__main__":
    unittest.main()
