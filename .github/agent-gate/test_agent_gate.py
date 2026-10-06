"""Unit tests for agent_gate.py. Run: python3 -m unittest discover -s .github/agent-gate -v"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock
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

    def test_missing_author_fails(self):
        d = g.evaluate(inputs(body=RISK))
        self.assertEqual(d.state, "failure")
        self.assertIn("agent-author", d.description)

    def test_no_review_fails(self):
        self.assertEqual(g.evaluate(inputs(comments=[])).state, "failure")

    def test_stale_review_after_push_fails(self):
        d = g.evaluate(inputs(comments=[review(sha=OLD)]))
        self.assertEqual(d.state, "failure")
        self.assertIn("re-review", d.description)

    def test_latest_review_wins(self):
        later_changes = review(verdict="changes", created="2026-10-02T11:00:00Z", cid=2)
        self.assertEqual(g.evaluate(inputs(comments=[review(), later_changes])).state, "failure")
        later_approve = review(created="2026-10-02T12:00:00Z", cid=3)
        self.assertEqual(g.evaluate(inputs(comments=[review(), later_changes, later_approve])).state, "success")

    def test_latest_marker_for_old_sha_blocks_even_if_earlier_matches(self):
        newer_old_sha = review(sha=OLD, created="2026-10-02T11:00:00Z", cid=2)
        self.assertEqual(g.evaluate(inputs(comments=[review(), newer_old_sha])).state, "failure")

    def test_self_review_fails(self):
        d = g.evaluate(inputs(comments=[review(session="auth-1")]))
        self.assertEqual(d.state, "failure")
        self.assertIn("author session", d.description)

    def test_untrusted_commenter_ignored(self):
        d = g.evaluate(inputs(comments=[review(association="NONE", login="stranger")]))
        self.assertEqual(d.state, "failure")

    def test_bot_review_is_never_trusted(self):
        # A PR controls its own pull_request workflows, which can comment as github-actions[bot].
        for association in ("NONE", "CONTRIBUTOR", "MEMBER"):
            bot = review(login="github-actions[bot]", association=association)
            self.assertEqual(g.evaluate(inputs(comments=[bot])).state, "failure", association)

    def test_bot_changes_verdict_cannot_hide_human_approval(self):
        bot = review(verdict="changes", login="github-actions[bot]", association="NONE",
                     created="2026-10-02T11:00:00Z", cid=2)
        self.assertEqual(g.evaluate(inputs(comments=[review(), bot])).state, "success")

    def test_reviewer_logins_restrict_who_can_review(self):
        only_app = frozenset({"reviewer-app[bot]"})
        self.assertEqual(g.evaluate(inputs(reviewer_logins=only_app)).state, "failure")
        app = review(login="reviewer-app[bot]", association="NONE")
        self.assertEqual(g.evaluate(inputs(comments=[app], reviewer_logins=only_app)).state, "success")

    def test_bot_report_comment_never_counts_as_review(self):
        fake = review(login="github-actions[bot]", association="NONE")
        fake["body"] = g.REPORT_MARKER + "\n" + fake["body"]
        self.assertEqual(g.evaluate(inputs(comments=[fake])).state, "failure")

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
        self.assertEqual(d.state, "failure")
        self.assertTrue(any("class=quick-fix" in n for n in d.notes))

    def test_unverified_revert_still_needs_review(self):
        d = g.evaluate(inputs(comments=[], revert=(False, "conflict-resolved")))
        self.assertEqual(d.state, "failure")
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
        self.assertEqual(d.state, "failure")
        runs = green_ci() + [{"id": 12, "name": "python-tests", "status": "completed", "conclusion": "failure"}]
        d = g.evaluate(inputs(body=body_with_class("feature"), owner_label=True, check_runs=runs))
        self.assertEqual(d.state, "failure")

    def test_policy_path_needs_owner_approval_whatever_the_class(self):
        for path in (".github/agent-gate/agent_gate.py", ".github/workflows/tests.yml", "AGENTS.md"):
            d = g.evaluate(inputs(changed_files=[path], owner_approval_paths=POLICY_PATHS))
            self.assertEqual(d.state, "failure", path)
            self.assertIn("policy path", d.description)
        d = g.evaluate(inputs(changed_files=["AGENTS.md"], owner_approval_paths=POLICY_PATHS, owner_label=True))
        self.assertEqual(d.state, "success", d.items)

    def test_failure_beats_pending(self):
        runs = green_ci() + [{"id": 12, "name": "x", "status": "queued", "conclusion": None}]
        self.assertEqual(g.evaluate(inputs(check_runs=runs, comments=[])).state, "failure")

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

    def test_native_coderabbit_approval_replaces_agent_marker(self):
        decision = g.evaluate(inputs(comments=[], review_bots={"coderabbitai[bot]": 136622811},
                                     native_reviews=[self.bot()]))
        self.assertEqual(decision.state, "success", decision.items)

    def test_native_approval_never_bypasses_unresolved_threads(self):
        decision = g.evaluate(inputs(comments=[], review_bots={"coderabbitai[bot]": 136622811},
                                     native_reviews=[self.bot()], unresolved_threads=1))
        self.assertEqual(decision.state, "failure")

    def test_stale_changed_dismissed_and_commented_bot_reviews_do_not_approve(self):
        for review in (self.bot(sha=OLD), self.bot(state="CHANGES_REQUESTED"),
                       self.bot(state="DISMISSED"), self.bot(state="COMMENTED")):
            with self.subTest(review=review):
                decision = g.evaluate(inputs(review_bots={"coderabbitai[bot]": 136622811},
                                             native_reviews=[review]))
                self.assertNotEqual(decision.state, "success")

    def test_matching_login_without_immutable_identity_never_counts(self):
        for review in (self.bot(uid=1), self.bot(login="another[bot]")):
            decision = g.evaluate(inputs(comments=[], review_bots={"coderabbitai[bot]": 136622811},
                                         native_reviews=[review]))
            self.assertEqual(decision.state, "failure")

    def test_later_comment_does_not_dismiss_a_native_approval(self):
        decision = g.evaluate(inputs(comments=[], review_bots={"coderabbitai[bot]": 136622811},
                                     native_reviews=[self.bot(), self.bot(state="COMMENTED", rid=100)]))
        self.assertEqual(decision.state, "success")

if __name__ == "__main__":
    unittest.main()
