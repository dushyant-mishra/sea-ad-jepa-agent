#!/usr/bin/env bash
set -euo pipefail

# Delete only branch refs listed in the verified JEPA safe-delete authority.
# Default is dry-run.  Actual deletion requires BOTH:
#   --apply
#   JEPA_CONFIRM_BRANCH_DELETE=YES_DELETE_VERIFIED_BRANCHES
#
# The script re-verifies:
#   1) each remote branch still exists at the exact recorded SHA;
#   2) that exact SHA is an ancestor of current origin/main.
# It aborts before deleting anything if any branch fails preflight.

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

LIST="docs/agent/JEPA_SAFE_BRANCH_DELETE_LIST_20260908.json"
if [[ ! -f "$LIST" ]]; then
  echo "STOP: missing $LIST" >&2
  exit 2
fi

APPLY=false
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=true
elif [[ "${1:-}" != "" ]]; then
  echo "usage: $0 [--apply]" >&2
  exit 2
fi

mapfile -t ROWS < <(python - "$LIST" <<'PY'
import json, sys
p=json.load(open(sys.argv[1], encoding="utf-8"))
assert p["canonical_branch"] == "main"
for row in p["branches"]:
    b=row["branch"]
    s=row["head_sha"]
    assert b != "main"
    assert len(s) == 40
    print(f"{b}\t{s}")
PY
)

if [[ "${#ROWS[@]}" -lt 1 ]]; then
  echo "STOP: delete list is empty" >&2
  exit 2
fi

echo "Fetching current origin/main..."
git fetch -q origin main
MAIN_SHA="$(git rev-parse origin/main)"
echo "origin/main = $MAIN_SHA"

echo "Preflighting ${#ROWS[@]} branch refs..."
for row in "${ROWS[@]}"; do
  IFS=$'\t' read -r branch expected <<<"$row"
  remote_ref="refs/remotes/origin/$branch"

  # Fetch exactly the named branch into its normal remote-tracking ref.
  if ! git fetch -q origin "refs/heads/$branch:$remote_ref"; then
    echo "STOP: cannot fetch remote branch $branch" >&2
    exit 3
  fi

  actual="$(git rev-parse "$remote_ref")"
  if [[ "$actual" != "$expected" ]]; then
    echo "STOP: branch moved: $branch" >&2
    echo "  expected $expected" >&2
    echo "  actual   $actual" >&2
    exit 4
  fi

  if ! git merge-base --is-ancestor "$actual" origin/main; then
    echo "STOP: $branch @ $actual is NOT an ancestor of origin/main @ $MAIN_SHA" >&2
    exit 5
  fi
done

echo "PASS: all ${#ROWS[@]} listed branch heads match exact SHAs and are ancestors of origin/main."

if [[ "$APPLY" != "true" ]]; then
  echo "DRY RUN ONLY: no refs deleted."
  echo "To delete after reviewing the list:"
  echo "  JEPA_CONFIRM_BRANCH_DELETE=YES_DELETE_VERIFIED_BRANCHES $0 --apply"
  exit 0
fi

if [[ "${JEPA_CONFIRM_BRANCH_DELETE:-}" != "YES_DELETE_VERIFIED_BRANCHES" ]]; then
  echo "STOP: --apply requires JEPA_CONFIRM_BRANCH_DELETE=YES_DELETE_VERIFIED_BRANCHES" >&2
  exit 6
fi

echo "Deleting verified remote branch refs..."
for row in "${ROWS[@]}"; do
  IFS=$'\t' read -r branch expected <<<"$row"
  echo "delete $branch @ $expected"
  git push --porcelain origin --delete "$branch"
done

echo "PASS: requested verified branch refs deleted. Tags and commit objects were not touched."
