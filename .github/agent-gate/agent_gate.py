#!/usr/bin/env python3
"""agent-gate: decide whether a coding agent may merge its own pull request.

Publishes the commit status `agent-gate` on the PR's head SHA. The `integration` ruleset requires
that status (from the GitHub Actions app), so this file is the merge policy. It passes only if:

  1. the PR is open and not a draft;
  2. the body carries a valid
     `<!-- agent-author harness=.. model=.. session=.. class=<quick-fix|feature|policy|revert> -->`;
  3. the body's "Risk & rollback" section answers what could break / how verified / how to revert;
  4. every `<!-- owner-question id=X -->` (body or trusted comment) has a matching trusted
     `<!-- owner-answer id=X -->` comment — resolving a thread is not an answer;
  5. authorization, by class:
       revert     the PR is a machine-verified pure revert of merge commit(s) (`agent-revert of=..`,
                  see `verify_pure_revert`); review and owner approval are waived. An unverified
                  `class=revert` fails: a revert that grew other changes is a fix and needs review.
       quick-fix  the LATEST `<!-- agent-review verdict=.. sha=.. reviewer=.. session=.. -->`
                  comment approves exactly the current head SHA, from another session;
       feature,   the same review, PLUS an owner approval: the human-applied `approved` label or a
       policy     trusted `<!-- owner-approval sha=<head sha|any> quote="..." -->` comment.
     A PR touching `owner_approval_paths` (config.json: the gate, workflows, agent instructions)
     needs the owner approval whatever its class, so a policy change cannot pass as a quick fix;
  6. no review thread is unresolved;
  7. every other check run / commit status on the head SHA is green, and every required check
     has reported (missing or still-running checks make the gate `pending`, not `failure`).

Trust: only comments from OWNER/MEMBER/COLLABORATOR accounts count, never a `[bot]` account (a PR
can make its own `pull_request` workflow comment as github-actions[bot]). All agents and the owner
share one GitHub account, so class, session and owner-approval comments are honour-based; the
`approved` label, applied by a human and checked against the label event's actor, is the stronger
signal. `reviewer_logins` restricts review verdicts to dedicated reviewer accounts once they exist.

Everything is read from LIVE API state, never from the triggering event's payload: the gate is
re-run on pushes, body edits, review comments and CI completion, and each run must judge the PR as
it is now. The verdict is written as a commit status on the head SHA it was computed for, so a
result for an older push can never satisfy a newer one.

Stdlib only; `evaluate()` is pure and unit-tested in test_agent_gate.py.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

GATE_CONTEXT = "agent-gate"
# The workflow jobs that run this script; their own check runs must not gate themselves.
GATE_JOB_NAMES = frozenset({"agent-gate-evaluate", "agent-gate-resolve"})
REPORT_MARKER = "<!-- agent-gate-report -->"
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
# Only used to find the gate's own sticky report comment, never to trust a verdict.
REPORT_BOTS = frozenset({"github-actions[bot]"})
CLASSES = ("quick-fix", "feature", "policy", "revert")
NEEDS_OWNER_APPROVAL = frozenset({"feature", "policy"})
GREEN_CONCLUSIONS = frozenset({"success", "skipped", "neutral"})

_SHA = re.compile(r"^[0-9a-f]{40}$")
_VALUE = re.compile(r"^[A-Za-z0-9._:/@+-]{1,200}$")
_ATTR = re.compile(r'([a-z]+)=("[^"]*"|\S+)')
_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_FENCE = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$", re.M | re.S)
_AUTHOR = re.compile(r"<!--[ \t]*agent-author[ \t]+([^>]*?)[ \t]*-->")
_REVERT = re.compile(r"<!--[ \t]*agent-revert[ \t]+([^>]*?)[ \t]*-->")
# Line-anchored: a marker quoted in a reply (`> <!-- agent-review ... -->`) is not a review.
_REVIEW = re.compile(r"^[ \t]*<!--[ \t]*agent-review[ \t]+([^>]*?)[ \t]*-->", re.M)
# Owner markers, line-anchored like reviews.
_OWNER_APPROVAL = re.compile(r"^[ \t]*<!--[ \t]*owner-approval[ \t]+([^>]*?)[ \t]*-->", re.M)
_OWNER_QUESTION = re.compile(r"^[ \t]*<!--[ \t]*owner-question[ \t]+([^>]*?)[ \t]*-->", re.M)
_OWNER_ANSWER = re.compile(r"^[ \t]*<!--[ \t]*owner-answer[ \t]+([^>]*?)[ \t]*-->", re.M)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_RISK_HEADING = re.compile(r"^#{1,4}[ \t]*Risk[ \t]*(?:&|and)[ \t]*rollback\b.*$", re.M | re.I)
_ANY_HEADING = re.compile(r"^#{1,4}[ \t]+\S", re.M)
RISK_FIELDS = {
    "what could break": re.compile(r"what\s+could\s+break", re.I),
    "how verified": re.compile(r"how\s+(?:it\s+was\s+|was\s+it\s+)?verified", re.I),
    "how to revert": re.compile(r"how\s+to\s+(?:revert|roll\s*back)", re.I),
}
PLACEHOLDERS = frozenset({"", "-", "tbd", "todo", "n/a", "na", "none", "...", "?", "x"})
MIN_RISK_ANSWER = 8


# --------------------------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------------------------


def strip_code(text: str) -> str:
    """Drop fenced code blocks so a documented example marker is never parsed as a real one."""
    return _FENCE.sub("", text or "")


def parse_attrs(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for key, value in _ATTR.findall(raw):
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        attrs.setdefault(key, value)
    return attrs


def _valid(attrs: dict[str, str], keys: tuple[str, ...]) -> bool:
    return all(_VALUE.match(attrs.get(k, "")) for k in keys)


def parse_author(body: str) -> dict[str, str] | None:
    for match in _AUTHOR.finditer(strip_code(body)):
        attrs = parse_attrs(match.group(1))
        if _valid(attrs, ("harness", "model", "session")):
            return attrs
    return None


def owner_approval(body: str, head_sha: str) -> dict[str, str] | None:
    """A valid `<!-- owner-approval sha=<head|any> quote="..." -->` in one comment, if it covers
    `head_sha`. The quote records the owner's chat answer verbatim (honour-based)."""
    for match in _OWNER_APPROVAL.finditer(strip_code(body)):
        attrs = parse_attrs(match.group(1))
        sha = attrs.get("sha", "").lower()
        if len(attrs.get("quote", "").strip()) < 3:
            continue
        if sha == "any" or (_SHA.match(sha) and sha == head_sha.lower()):
            return attrs
    return None


def _ids(rx: re.Pattern[str], body: str) -> set[str]:
    out = set()
    for match in rx.finditer(strip_code(body)):
        ident = parse_attrs(match.group(1)).get("id", "")
        if _ID.match(ident):
            out.add(ident)
    return out


def owner_questions(body: str) -> set[str]:
    return _ids(_OWNER_QUESTION, body)


def owner_answers(body: str) -> set[str]:
    return _ids(_OWNER_ANSWER, body)


def parse_reverted(body: str) -> list[str]:
    """`<!-- agent-revert of=<sha>[,<sha>...] -->` written by revert-merge.sh."""
    for match in _REVERT.finditer(strip_code(body)):
        shas = parse_attrs(match.group(1)).get("of", "").lower().split(",")
        if shas and all(_SHA.match(s) for s in shas):
            return shas
    return []


def parse_review(body: str) -> dict[str, str] | None:
    """The LAST valid review marker in one comment (a comment is one verdict)."""
    found = None
    for match in _REVIEW.finditer(strip_code(body)):
        attrs = parse_attrs(match.group(1))
        if (
            attrs.get("verdict") in {"approve", "changes"}
            and _SHA.match(attrs.get("sha", "").lower())
            and _valid(attrs, ("reviewer", "session"))
        ):
            attrs["sha"] = attrs["sha"].lower()
            found = attrs
    return found


def risk_section_problems(body: str) -> list[str]:
    """Empty list when the Risk & rollback section answers all three questions."""
    text = strip_code(body)
    heading = _RISK_HEADING.search(text)
    if not heading:
        return ["no `## Risk & rollback` section in the PR body"]
    rest = text[heading.end():]
    following = _ANY_HEADING.search(rest)
    section = _HTML_COMMENT.sub("", rest[: following.start()] if following else rest)
    labels = sorted(
        ((m.start(), m.end(), name) for name, rx in RISK_FIELDS.items() for m in [rx.search(section)] if m),
    )
    problems = [f"Risk & rollback: missing '{name}'" for name in RISK_FIELDS if not RISK_FIELDS[name].search(section)]
    for i, (_, end, name) in enumerate(labels):
        stop = labels[i + 1][0] if i + 1 < len(labels) else len(section)
        answer = section[end:stop]
        # Drop the label's own trailing markup (`:**`, `?**`, list bullets) before judging content.
        answer = re.sub(r"[*_`>:?]|^\s*[-+]\s", " ", answer, flags=re.M)
        answer = re.sub(r"\s+", " ", answer).strip()
        if answer.lower() in PLACEHOLDERS or len(answer) < MIN_RISK_ANSWER:
            problems.append(f"Risk & rollback: '{name}' is not filled in")
    return problems


# --------------------------------------------------------------------------------------------
# Decision (pure)
# --------------------------------------------------------------------------------------------


@dataclass
class Inputs:
    number: int
    state: str  # "open" | "closed"
    draft: bool
    head_sha: str
    body: str
    comments: list[dict[str, Any]]  # {id, body, created_at, login, association}
    check_runs: list[dict[str, Any]]  # {id, name, status, conclusion}
    statuses: list[dict[str, Any]]  # {context, state} — latest per context
    unresolved_threads: int
    required_checks: list[str]
    ignore_checks: frozenset[str] = frozenset()
    reviewer_logins: frozenset[str] = frozenset()
    # True when the owner-approval label is on the PR and was last applied by a human account.
    owner_label: bool = False
    owner_label_name: str = "approved"
    changed_files: list[str] = field(default_factory=list)
    owner_approval_paths: tuple[str, ...] = ()
    # None: not a revert PR. Otherwise (verified?, detail) from verify_pure_revert().
    revert: tuple[bool, str] | None = None


@dataclass
class Decision:
    state: str  # "success" | "pending" | "failure"
    items: list[tuple[str, str]] = field(default_factory=list)  # (ok|pending|fail, text)
    notes: list[str] = field(default_factory=list)

    @property
    def description(self) -> str:
        if self.state == "success":
            return "All agent merge conditions met for this head SHA"
        blocking = [t for s, t in self.items if s == "fail"] or [t for s, t in self.items if s == "pending"]
        text = blocking[0] if blocking else self.state
        more = len(blocking) - 1
        if more > 0:
            text += f" (+{more} more)"
        return text if len(text) <= 140 else text[:137] + "..."


def trusted(comment: dict[str, Any]) -> bool:
    """A human-written comment from a repo owner/member/collaborator. Bots are never trusted: a PR
    controls its own `pull_request` workflows, which can comment as github-actions[bot]."""
    login = comment.get("login") or ""
    return comment.get("association") in TRUSTED_ASSOCIATIONS and not login.endswith("[bot]") \
        and REPORT_MARKER not in (comment.get("body") or "")


def latest_review(
    comments: list[dict[str, Any]], reviewer_logins: frozenset[str] = frozenset()
) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    """The newest trusted comment that carries a valid review marker. With `reviewer_logins`
    configured, only those accounts (e.g. a dedicated reviewer GitHub App) can post verdicts."""
    ordered = sorted(comments, key=lambda c: (c.get("created_at") or "", c.get("id") or 0))
    for comment in reversed(ordered):
        if reviewer_logins:
            ok = comment.get("login") in reviewer_logins
        else:
            ok = trusted(comment)
        body = comment.get("body") or ""
        if not ok or REPORT_MARKER in body:
            continue
        review = parse_review(body)
        if review:
            return review, comment
    return None, None


def family(model: str) -> str:
    m = model.lower()
    for name in ("claude", "gpt", "codex", "gemini", "grok", "llama", "mistral", "qwen", "deepseek"):
        if name in m:
            return "openai" if name in {"gpt", "codex"} else name
    if re.match(r"^o\d", m):
        return "openai"
    return m.split("-")[0]


def ci_items(inputs: Inputs) -> list[tuple[str, str]]:
    excluded = {GATE_CONTEXT, *GATE_JOB_NAMES, *inputs.ignore_checks}
    latest: dict[str, dict[str, Any]] = {}
    for run in inputs.check_runs:
        name = run.get("name", "")
        if name in excluded:
            continue
        if name not in latest or (run.get("id") or 0) > (latest[name].get("id") or 0):
            latest[name] = run
    seen: dict[str, str] = {}
    items: list[tuple[str, str]] = []
    for name, run in sorted(latest.items()):
        if run.get("status") != "completed":
            seen[name] = "pending"
            items.append(("pending", f"CI `{name}` is {run.get('status') or 'queued'}"))
        elif run.get("conclusion") in GREEN_CONCLUSIONS:
            seen[name] = "ok"
        else:
            seen[name] = "fail"
            items.append(("fail", f"CI `{name}` concluded {run.get('conclusion')}"))
    for status in inputs.statuses:
        name = status.get("context", "")
        if name in excluded:
            continue
        state = status.get("state")
        if state == "success":
            seen.setdefault(name, "ok")
        elif state == "pending":
            seen[name] = "pending"
            items.append(("pending", f"status `{name}` is pending"))
        else:
            seen[name] = "fail"
            items.append(("fail", f"status `{name}` is {state}"))
    for name in inputs.required_checks:
        if name in excluded:
            continue
        if name not in seen:
            items.append(("pending", f"required check `{name}` has not reported for this SHA"))
    if not items:
        items.append(("ok", f"CI green ({len(seen)} checks)"))
    return items


def owner_question_items(inputs: Inputs) -> list[tuple[str, str]]:
    asked = owner_questions(inputs.body)
    answered: set[str] = set()
    for comment in inputs.comments:
        if trusted(comment):
            asked |= owner_questions(comment.get("body") or "")
            answered |= owner_answers(comment.get("body") or "")
    open_ids = sorted(asked - answered)
    if open_ids:
        return [("fail", f"owner question(s) unanswered: {', '.join(open_ids)} — record the answer as "
                         "`<!-- owner-answer id=<id> -->`")]
    if asked:
        return [("ok", f"owner question(s) answered: {', '.join(sorted(asked))}")]
    return []


def review_items(inputs: Inputs, author: dict[str, str] | None) -> list[tuple[str, str]]:
    sha7 = inputs.head_sha[:7]
    review, _ = latest_review(inputs.comments, inputs.reviewer_logins)
    if review is None:
        return [("fail", f"no agent review — a separate reviewer session must approve sha {sha7}")]
    if review["sha"] != inputs.head_sha.lower():
        return [("fail", f"latest agent review is for {review['sha'][:7]}, head is {sha7} — re-review")]
    if review["verdict"] != "approve":
        return [("fail", f"latest agent review of {sha7} requests changes ({review['reviewer']})")]
    if author and review["session"] == author["session"]:
        return [("fail", "reviewer session equals the author session — use a separate reviewer")]
    return [("ok", f"approved at {sha7} by {review['reviewer']} session {review['session']}")]


def policy_files(inputs: Inputs) -> list[str]:
    return [f for f in inputs.changed_files if any(fnmatch.fnmatchcase(f, p) for p in inputs.owner_approval_paths)]


def owner_approval_items(inputs: Inputs, klass: str) -> list[tuple[str, str]]:
    touched = policy_files(inputs)
    if klass not in NEEDS_OWNER_APPROVAL and not touched:
        return [("ok", "quick fix: no owner approval needed (small correction, no open owner questions)")]
    why = f"class={klass}" if klass in NEEDS_OWNER_APPROVAL else f"touches policy path {touched[0]}"
    if inputs.owner_label:
        return [("ok", f"owner approval ({why}): `{inputs.owner_label_name}` label applied by a human")]
    for comment in reversed(sorted(inputs.comments, key=lambda c: (c.get("created_at") or "", c.get("id") or 0))):
        if trusted(comment):
            approval = owner_approval(comment.get("body") or "", inputs.head_sha)
            if approval:
                return [("ok", f"owner approval ({why}) recorded: \"{approval['quote'][:60]}\"")]
    return [("fail", f"{why} needs explicit owner approval: the `{inputs.owner_label_name}` label, or a "
                     "`<!-- owner-approval sha=<head|any> quote=\"...\" -->` comment quoting the owner's chat answer")]


def evaluate(inputs: Inputs) -> Decision:
    items: list[tuple[str, str]] = []
    notes: list[str] = []

    if inputs.state != "open":
        items.append(("fail", f"PR is {inputs.state}"))
    elif inputs.draft:
        items.append(("fail", "PR is a draft — mark it ready for review"))
    else:
        items.append(("ok", "PR is open and ready"))

    author = parse_author(inputs.body)
    klass = (author or {}).get("class", "")
    if author and klass in CLASSES:
        items.append(("ok", f"author {author['harness']}/{author['model']} session {author['session']} class {klass}"))
    elif author:
        items.append(("fail", f"agent-author marker needs class=<{'|'.join(CLASSES)}> (got {klass or 'none'})"))
    else:
        items.append(("fail", "PR body lacks a valid `<!-- agent-author harness=.. model=.. session=.. class=.. -->` marker"))

    risk = risk_section_problems(inputs.body)
    items.extend(("fail", p) for p in risk)
    if not risk:
        items.append(("ok", "Risk & rollback section filled"))

    items.extend(owner_question_items(inputs))

    verified_revert = inputs.revert is not None and inputs.revert[0]
    if klass == "revert":
        if verified_revert:
            items.append(("ok", f"verified pure revert ({inputs.revert[1]}); review and owner approval waived"))
        else:
            why = inputs.revert[1] if inputs.revert is not None else "no `<!-- agent-revert of=<merge sha> -->` marker"
            items.append(("fail", f"class=revert but not a verified pure revert ({why}) — re-class it and get a review"))
    else:
        if inputs.revert is not None:
            notes.append(f"Revert fast-track not applied (class={klass or 'none'}): {inputs.revert[1]}")
        reviewed = review_items(inputs, author)
        items.extend(reviewed)
        review, _ = latest_review(inputs.comments, inputs.reviewer_logins)
        if reviewed[0][0] == "ok" and author and review \
                and family(review["reviewer"].split("/")[-1]) == family(author["model"]):
            notes.append("Reviewer is the same model family as the author; a different provider is preferred "
                         "(acceptable when provider limits require it).")
        items.extend(owner_approval_items(inputs, klass))

    if inputs.unresolved_threads:
        items.append(("fail", f"{inputs.unresolved_threads} unresolved review thread(s)"))
    else:
        items.append(("ok", "no unresolved review threads"))

    items.extend(ci_items(inputs))

    states = {s for s, _ in items}
    state = "failure" if "fail" in states else "pending" if "pending" in states else "success"
    return Decision(state, items, notes)


def render_report(inputs: Inputs, decision: Decision, run_url: str) -> str:
    icon = {"ok": "PASS", "pending": "WAIT", "fail": "FAIL"}
    lines = [
        REPORT_MARKER,
        f"### agent-gate: **{decision.state}** for `{inputs.head_sha[:12]}`",
        "",
        *(f"- `{icon[s]}` {t}" for s, t in decision.items),
    ]
    if decision.notes:
        lines += ["", *(f"> {n}" for n in decision.notes)]
    lines += [
        "",
        "Merge only when this is `success`: "
        f"`gh pr merge {inputs.number} --merge --match-head-commit {inputs.head_sha}`.",
        f"Re-evaluated on push, body edit, review comment and CI completion ([run]({run_url})). "
        "After resolving threads, comment `/agent-gate` to re-run.",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------------------------
# Pure-revert verification (git, on trusted default-branch checkout; PR code is never executed)
# --------------------------------------------------------------------------------------------


def _git(repo: Path, *args: str, stdin: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args], input=stdin, capture_output=True, check=True, timeout=120
    ).stdout


def patch_id(repo: Path, old: str, new: str) -> str:
    diff = _git(repo, "diff", "--no-color", "--no-ext-diff", "--full-index", old, new)
    out = _git(repo, "patch-id", "--stable", stdin=diff).decode().split()
    return out[0] if out else ""


def verify_pure_revert(repo: Path, base: str, head: str, reverted: list[str]) -> tuple[bool, str]:
    """True only if head..base is exactly one non-merge commit per reverted merge, each the clean
    inverse of a `git revert -m 1` of a merge already on base. Conflict-resolved reverts differ in
    patch-id and fall back to a normal agent review."""
    try:
        commits = _git(repo, "rev-list", "--reverse", "--parents", head, f"^{base}").decode().split("\n")
        commits = [c.split() for c in commits if c.strip()]
        if not commits or len(commits) != len(reverted):
            return False, f"{len(commits)} commit(s) on the branch for {len(reverted)} reverted merge(s)"
        if any(len(c) != 2 for c in commits):
            return False, "branch contains a merge commit"
        wanted: list[str] = []
        for merge in reverted:
            parents = _git(repo, "rev-list", "--parents", "-n1", merge).decode().split()
            if len(parents) != 3:
                return False, f"{merge[:7]} is not a merge commit"
            if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", merge, base]).returncode:
                return False, f"{merge[:7]} is not on the base branch"
            pid = patch_id(repo, parents[1], merge)
            if not pid:
                return False, f"{merge[:7]} has an empty diff"
            wanted.append(pid)
        for sha, parent in commits:
            pid = patch_id(repo, sha, parent)  # inverse of the revert commit == the merge's change
            if pid not in wanted:
                return False, f"{sha[:7]} is not a clean inverse of a listed merge"
            wanted.remove(pid)
        return True, "reverts " + ", ".join(m[:7] for m in reverted)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return False, f"git verification failed: {exc}"


# --------------------------------------------------------------------------------------------
# GitHub I/O
# --------------------------------------------------------------------------------------------


class GitHub:
    def __init__(self, repo: str, token: str, api: str = "https://api.github.com"):
        self.repo, self.token, self.api_url = repo, token, api.rstrip("/")

    def request(self, method: str, path: str, body: Any = None) -> tuple[Any, dict[str, str]]:
        url = path if path.startswith("http") else f"{self.api_url}/{path.lstrip('/')}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return (json.loads(raw) if raw else None), dict(resp.headers)

    def get(self, path: str) -> Any:
        return self.request("GET", path)[0]

    def paginate(self, path: str, key: str | None = None) -> list[Any]:
        out: list[Any] = []
        url: str | None = path + ("&" if "?" in path else "?") + "per_page=100"
        while url:
            data, headers = self.request("GET", url)
            out.extend(data[key] if key else data)
            nxt = re.search(r'<([^>]+)>;\s*rel="next"', headers.get("Link", "") or headers.get("link", ""))
            url = nxt.group(1) if nxt else None
        return out

    def graphql(self, query: str, variables: dict[str, Any]) -> Any:
        data, _ = self.request("POST", f"{self.api_url}/graphql", {"query": query, "variables": variables})
        if data.get("errors"):
            raise RuntimeError(f"graphql: {data['errors']}")
        return data["data"]

    def unresolved_threads(self, number: int) -> int:
        owner, name = self.repo.split("/")
        query = """query($o:String!,$n:String!,$p:Int!,$c:String){repository(owner:$o,name:$n){
          pullRequest(number:$p){reviewThreads(first:100,after:$c){
            nodes{isResolved} pageInfo{hasNextPage endCursor}}}}}"""
        count, cursor = 0, None
        while True:
            threads = self.graphql(query, {"o": owner, "n": name, "p": number, "c": cursor})
            threads = threads["repository"]["pullRequest"]["reviewThreads"]
            count += sum(1 for t in threads["nodes"] if not t["isResolved"])
            if not threads["pageInfo"]["hasNextPage"]:
                return count
            cursor = threads["pageInfo"]["endCursor"]

    def owner_label(self, number: int, labels: list[str], name: str) -> bool:
        """The label is on the PR and its latest `labeled` event came from a human account. A PR's
        own workflow can add labels as github-actions[bot]; that must not count as the owner."""
        if name not in labels:
            return False
        events = self.paginate(f"repos/{self.repo}/issues/{number}/events")
        actor = None
        for event in events:
            if event.get("event") == "labeled" and (event.get("label") or {}).get("name") == name:
                actor = event.get("actor") or {}
        return bool(actor) and actor.get("type") != "Bot" and not (actor.get("login") or "").endswith("[bot]")

    def changed_files(self, number: int) -> list[str]:
        files = self.paginate(f"repos/{self.repo}/pulls/{number}/files")
        out: list[str] = []
        for f in files:
            out.append(f["filename"])
            if f.get("previous_filename"):
                out.append(f["previous_filename"])
        return out

    def ruleset_required_checks(self, branch: str) -> list[str]:
        try:
            rules = self.paginate(f"repos/{self.repo}/rules/branches/{urllib.parse.quote(branch)}")
        except urllib.error.HTTPError:
            return []
        return [
            c["context"]
            for r in rules if r.get("type") == "required_status_checks"
            for c in r.get("parameters", {}).get("required_status_checks", [])
        ]


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def gather(gh: GitHub, number: int, config: dict[str, Any], repo_dir: Path | None) -> Inputs:
    pr = gh.get(f"repos/{gh.repo}/pulls/{number}")
    head = pr["head"]["sha"]
    comments = [
        {"id": c["id"], "body": c.get("body") or "", "created_at": c["created_at"],
         "login": (c.get("user") or {}).get("login", ""), "association": c.get("author_association", "")}
        for c in gh.paginate(f"repos/{gh.repo}/issues/{number}/comments")
    ]
    runs = gh.paginate(f"repos/{gh.repo}/commits/{head}/check-runs", key="check_runs")
    statuses = gh.get(f"repos/{gh.repo}/commits/{head}/status?per_page=100").get("statuses", [])
    base = pr["base"]["ref"]
    required = list(dict.fromkeys([*config.get("required_checks", []), *gh.ruleset_required_checks(base)]))
    body = pr.get("body") or ""
    revert = None
    reverted = parse_reverted(body)
    if reverted:
        if repo_dir is None:
            revert = (False, "no git checkout available to verify the revert")
        elif pr["head"]["repo"] is None or pr["head"]["repo"]["full_name"] != gh.repo:
            revert = (False, "revert fast-track is for same-repository branches only")
        else:
            try:
                fetch = ["fetch", "--no-tags", "--quiet"]
                if (repo_dir / ".git" / "shallow").exists():
                    fetch.append("--unshallow")
                _git(repo_dir, *fetch, "origin",
                     f"+refs/heads/{base}:refs/remotes/origin/{base}",
                     f"+refs/pull/{number}/head:refs/remotes/pr/{number}")
                fetched = _git(repo_dir, "rev-parse", f"refs/remotes/pr/{number}").decode().strip()
                if fetched != head:
                    revert = (False, "PR head moved while verifying; will re-run")
                else:
                    revert = verify_pure_revert(repo_dir, f"refs/remotes/origin/{base}", head, reverted)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                revert = (False, f"git fetch failed: {exc}")
    label_name = config.get("owner_approval_label", "approved")
    labels = [lbl["name"] for lbl in pr.get("labels") or []]
    return Inputs(
        number=number, state=pr["state"], draft=bool(pr.get("draft")), head_sha=head, body=body,
        comments=comments,
        check_runs=[{"id": r["id"], "name": r["name"], "status": r["status"], "conclusion": r["conclusion"]} for r in runs],
        statuses=[{"context": s["context"], "state": s["state"]} for s in statuses],
        unresolved_threads=gh.unresolved_threads(number),
        required_checks=required,
        ignore_checks=frozenset(config.get("ignore_checks", [])),
        reviewer_logins=frozenset(config.get("reviewer_logins", [])),
        owner_label=gh.owner_label(number, labels, label_name),
        owner_label_name=label_name,
        changed_files=gh.changed_files(number),
        owner_approval_paths=tuple(config.get("owner_approval_paths", [])),
        revert=revert,
    )


def publish(gh: GitHub, inputs: Inputs, decision: Decision, run_url: str) -> None:
    gh.request("POST", f"repos/{gh.repo}/statuses/{inputs.head_sha}", {
        "state": decision.state, "context": GATE_CONTEXT,
        "description": decision.description, "target_url": run_url,
    })
    report = render_report(inputs, decision, run_url)
    existing = [
        c for c in inputs.comments
        if c["login"] in REPORT_BOTS and c["body"].startswith(REPORT_MARKER)
    ]
    if existing:
        if existing[-1]["body"].strip() != report.strip():
            gh.request("PATCH", f"repos/{gh.repo}/issues/comments/{existing[-1]['id']}", {"body": report})
    elif inputs.state == "open":
        gh.request("POST", f"repos/{gh.repo}/issues/{inputs.number}/comments", {"body": report})


def target_prs(gh: GitHub, event_name: str, event: dict[str, Any], explicit: str) -> list[int]:
    if explicit.strip():
        if explicit.strip() == "all":
            return [p["number"] for p in gh.paginate(f"repos/{gh.repo}/pulls?state=open")]
        return [int(n) for n in explicit.split(",") if n.strip()]
    if event_name in {"pull_request", "pull_request_target"}:
        return [event["pull_request"]["number"]]
    if event_name == "issue_comment":
        return [event["issue"]["number"]] if event["issue"].get("pull_request") else []
    if event_name == "workflow_run":
        sha = event["workflow_run"]["head_sha"]
        return [p["number"] for p in gh.paginate(f"repos/{gh.repo}/pulls?state=open") if p["head"]["sha"] == sha]
    return []


def main() -> int:
    env = os.environ
    gh = GitHub(env["GITHUB_REPOSITORY"], env["GITHUB_TOKEN"], env.get("GITHUB_API_URL", "https://api.github.com"))
    event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_text()) if env.get("GITHUB_EVENT_PATH") else {}
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.json")
    repo_dir = Path(env.get("GITHUB_WORKSPACE", here.parents[1]))
    run_url = f"{env.get('GITHUB_SERVER_URL', 'https://github.com')}/{gh.repo}/actions/runs/{env.get('GITHUB_RUN_ID', '')}"
    numbers = target_prs(gh, env.get("GITHUB_EVENT_NAME", ""), event, env.get("AGENT_GATE_PR", ""))
    if "--resolve" in sys.argv[1:]:
        # First workflow job: name the PR(s) this event concerns, so the evaluate job can key its
        # concurrency group on the PR number for every trigger (workflow_run carries only a SHA).
        prs = json.dumps(sorted(set(numbers)))
        print(f"PRs for this event: {prs}")
        if env.get("GITHUB_OUTPUT"):
            with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
                fh.write(f"prs={prs}\n")
        return 0
    if not numbers:
        print("No open pull request to evaluate for this event.")
        return 0
    summary = []
    for number in numbers:
        inputs = gather(gh, number, config, repo_dir if (repo_dir / ".git").exists() else None)
        decision = evaluate(inputs)
        if inputs.state == "open":
            publish(gh, inputs, decision, run_url)
        text = render_report(inputs, decision, run_url)
        print(text)
        summary.append(text)
    if env.get("GITHUB_STEP_SUMMARY"):
        with open(env["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write("\n\n".join(summary) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
