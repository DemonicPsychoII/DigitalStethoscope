#!/usr/bin/env bash
# revert-last-merge.sh — one command to undo merged PR(s).
#
#   .github/agent-gate/revert-last-merge.sh [<pr-number>|<merge-sha>|last]... [--deploy] [--draft]
#                                [--title TEXT] [--reason TEXT]
#
# 1. Resolves each merge commit (a PR number, a SHA, or `last` = newest merge on integration).
# 2. In a throwaway worktree, branches `revert/<sha7>` from origin/integration and runs
#    `git revert -m 1` for each merge, newest first (the repo merges with merge commits, so -m 1
#    is exact).
# 3. Pushes and opens a PR whose body carries `<!-- agent-author ... class=revert -->`, a filled
#    Risk & rollback section and `<!-- agent-revert of=<sha>[,<sha>...] -->`. agent-gate verifies
#    that marker against git (clean inverse of those merges on integration, nothing else) and
#    waives the review, so a ready pure revert merges once CI is green:
#    `gh pr merge <n> --merge --match-head-commit <sha>`. Any other change on the branch turns it
#    into a fix: change class=, retitle, and it needs a normal review.
#    --draft opens it as a draft recovery PR (deploy.sh uses this after it restored production
#    itself): nothing merges until an agent decides a repository revert is really the fix.
# 4. --deploy (only where scripts/deploy/deploy.sh exists; elsewhere it errors out at once) rolls
#    production back NOW instead of waiting for the merge: the fast image rollback when exactly
#    the reverted merges run on top of the last deploy, otherwise a rebuild of the revert commit.
#
# Never touches the caller's checkout or the live checkout's branch except via --deploy.
# Exit codes: 0 ok, 1 usage/lookup error, 2 the revert conflicts (resolve by hand; the gate then
# requires a normal agent review because the result is no longer a pure inverse).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REVERT_REPO:-$(git -C "$HERE" rev-parse --show-toplevel)}"
# This script's path inside its own repository, for the generated PR body (differs per repo).
SELF="$(git -C "$HERE" rev-parse --show-prefix)$(basename "${BASH_SOURCE[0]}")"
BASE="${REVERT_BASE:-integration}"
REMOTE="${REVERT_REMOTE:-origin}"
GH="${REVERT_GH:-gh}"
DEPLOY="${REVERT_DEPLOY_SCRIPT:-$REPO/scripts/deploy/deploy.sh}"

targets=(); do_deploy=0; draft=0; reason=""; title_override=""
while (($#)); do
  case "$1" in
    --deploy) do_deploy=1 ;;
    --draft) draft=1 ;;
    --reason) reason="${2:?--reason needs text}"; shift ;;
    --title) title_override="${2:?--title needs text}"; shift ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 1 ;;
    *) targets+=("$1") ;;
  esac
  shift
done
((${#targets[@]})) || targets=(last)
if ((do_deploy)) && [[ ! -f "$DEPLOY" ]]; then
  echo "--deploy is not supported in this repository (no scripts/deploy/deploy.sh)" >&2; exit 1
fi

git -C "$REPO" fetch --quiet "$REMOTE" "+refs/heads/$BASE:refs/remotes/$REMOTE/$BASE"
base_ref="refs/remotes/$REMOTE/$BASE"

resolve() {  # target -> merge sha on $BASE
  local target="$1" merge
  if [[ "$target" == "last" ]]; then
    merge="$(git -C "$REPO" rev-list --first-parent --merges -n1 "$base_ref")"
  elif [[ "$target" =~ ^[0-9]+$ ]]; then
    merge="$("$GH" pr view "$target" --json mergeCommit,state --jq 'select(.state=="MERGED") | .mergeCommit.oid')"
    [[ -n "$merge" ]] || { echo "PR #$target is not merged" >&2; return 1; }
  else
    merge="$(git -C "$REPO" rev-parse --verify --quiet "$target^{commit}")" || { echo "unknown commit: $target" >&2; return 1; }
  fi
  [[ -n "$merge" ]] || { echo "no merge commit found on $BASE" >&2; return 1; }
  if [[ "$(git -C "$REPO" rev-list --parents -n1 "$merge" | wc -w)" -ne 3 ]]; then
    echo "$merge is not a merge commit; this tool reverts merged PRs only" >&2; return 1
  fi
  git -C "$REPO" merge-base --is-ancestor "$merge" "$base_ref" || { echo "$merge is not on $BASE" >&2; return 1; }
  echo "$merge"
}

wanted=()
for t in "${targets[@]}"; do m="$(resolve "$t")" || exit 1; wanted+=("$m"); done
# Newest first along integration's first-parent history, so each revert applies on top of the last.
mapfile -t merges < <(git -C "$REPO" rev-list --first-parent "$base_ref" | grep -xF -f <(printf '%s
' "${wanted[@]}") || true)
if [[ "${#merges[@]}" -ne "$(printf '%s
' "${wanted[@]}" | sort -u | wc -l)" ]]; then
  echo "every merge must be a PR merge on $BASE's first-parent history" >&2; exit 1
fi
merge="${merges[0]}"
short="${merge:0:7}"
of="$(IFS=,; echo "${merges[*]}")"
subject="$(git -C "$REPO" log -1 --format=%s "$merge")"
pr_number="$(sed -nE 's/^Merge pull request #([0-9]+) .*/\1/p' <<<"$subject")"
title=""
if [[ "${#merges[@]}" -eq 1 && -n "$pr_number" ]]; then
  title="$("$GH" pr view "$pr_number" --json title --jq .title 2>/dev/null || true)"
fi
title="${title:-$subject}"
if [[ "${#merges[@]}" -eq 1 ]]; then
  what="$short (\"$title\")${pr_number:+ from #$pr_number}"
  pr_title="Revert \"$title\""
  branch="revert/$short"
else
  what="${#merges[@]} merges: $(git -C "$REPO" log --no-walk=unsorted --format='%h (%s)' "${merges[@]}" | paste -sd ';' - | sed 's/;/; /g')"
  pr_title="Revert ${#merges[@]} merges ($(printf '%.7s ' "${merges[@]}" | sed 's/ $//'))"
  branch="revert/$short-and-$((${#merges[@]} - 1))-more"
fi
pr_title="${title_override:-$pr_title}"

existing="$("$GH" pr list --head "$branch" --state open --json url --jq '.[0].url // empty' 2>/dev/null || true)"
if [[ -n "$existing" ]]; then
  echo "revert PR already open: $existing"
  pr_url="$existing"
else
  wt="$(mktemp -d)"
  cleanup() { git -C "$REPO" worktree remove --force "$wt" >/dev/null 2>&1 || rm -rf "$wt"; }
  trap cleanup EXIT
  git -C "$REPO" worktree add --quiet --detach "$wt" "$base_ref"
  git -C "$wt" checkout --quiet -B "$branch"
  for m in "${merges[@]}"; do
    if ! git -C "$wt" revert --no-edit -m 1 "$m" >/dev/null; then
      git -C "$wt" revert --abort || true
      echo "git revert -m 1 ${m:0:7} conflicts with later changes on $BASE; revert by hand" >&2
      exit 2
    fi
  done
  git -C "$wt" push --quiet --force-with-lease "$REMOTE" "HEAD:refs/heads/$branch"

  harness="${AGENT_HARNESS:-script}"; model="${AGENT_MODEL:-revert-last-merge}"
  session="${AGENT_SESSION:-revert-$short-$(date -u +%Y%m%dT%H%M%SZ)}"
  body="$(mktemp)"
  recovery=""
  if ((draft)); then
    recovery="
## Recovery (draft)

Production was already restored to the last working runtime without a merge, and nothing here
merges automatically. Diagnose the failure, then either:

- push the fix to this branch, set \`class=quick-fix\` (or \`feature\`/\`policy\` with owner approval)
  in the agent-author marker, delete the agent-revert marker and retitle: normal review applies; or
- only if a repository revert is genuinely needed to restore service, mark this unchanged pure
  revert ready for review: agent-gate verifies it and it merges once checks pass.
"
  fi
  cat >"$body" <<EOF
<!-- agent-author harness=$harness model=$model session=$session class=revert -->
<!-- agent-revert of=$of -->

## Summary

Reverts $what with \`git revert -m 1\`.
${reason:+
Reason: $reason
}${recovery}
## Risk & rollback

- **What could break:** whatever the reverted change fixed or added is removed again; later PRs that build on it may need follow-up.
- **How verified:** agent-gate checks this branch is exactly the inverse of the listed merge(s) (git patch-id), and CI runs on the result.
- **How to revert:** revert this revert: \`$SELF <this PR number>\`.

## Verification checklist

- [x] Pure \`git revert -m 1\`, generated by \`$SELF\`
- [ ] CI green on the head commit

If agent-gate is still pending after CI finishes: \`gh workflow run agent-gate.yml -f pr=<this PR>\`.
EOF
  draft_flag=()
  if ((draft)); then draft_flag=(--draft); fi
  pr_url="$("$GH" pr create --base "$BASE" --head "$branch" --title "$pr_title" --body-file "$body" "${draft_flag[@]}")"
  rm -f "$body"
  echo "opened $pr_url"
  # GITHUB_TOKEN-authored pushes/PRs trigger no workflows; dispatch the ones the gate needs.
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    for wf in ${REVERT_DISPATCH_WORKFLOWS:-tests.yml}; do "$GH" workflow run "$wf" --ref "$branch" || true; done
    "$GH" workflow run agent-gate.yml -f pr="${pr_url##*/}" || true
  fi
fi

if ((do_deploy)); then
  revert_sha="$(git -C "$REPO" ls-remote "$REMOTE" "refs/heads/$branch" | cut -f1)"
  bash "$DEPLOY" --revert-of "$of" --ref "$revert_sha"
fi
echo "$pr_url"
