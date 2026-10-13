# V79 scoring lane — custody disclosure record (2026-10-13)

**Classification:** `NON_CONTENT_PATH_NAME_EXPOSURE__NO_TRUTH_VALUE_EXPOSURE`

## Event

**When:** the read-only V79 pre-execution audit of 2026-10-13. It was carried out by an audit agent delegated from the Macha session, against detached worktree `D:/jepa_v79_scoring_audit_d4e10c82` at scorer head `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`.

**What happened:**
- **The command touched committed truth manifests.** The command was a `git grep -l` for the binding SHA-256 values. It pattern-scanned committed files, including the paths `results/v79/v2_core_realization_audit_freeze_v1/package/controller_truth/*/manifest.json`.
- **Only file names were printed.** The output listed the names of files that contained a matching hash.
- **No truth content or values were displayed.**
- **All later searches excluded `controller_truth`.**

Provenance of this record: the audit agent disclosed this in its own report. The exact command string was not preserved, so it is not reproduced here.

The event is **not** classified as a truth opening. No evidence has been found that truth values were displayed.

## Context

- Controller truth is committed in the repository by design: 350 files, bound by the realization ledger `4e65f213…`.
- At `d4e10c82`, the existing scorer CI workflow already loads that committed truth in `test_v79_v2_core_score_truth.py` and `test_v79_v2_core_score_quantities.py`.

## Macha orchestrator work (this lane), for completeness

**Read:**
- the realization audit receipt and the realization ledger (paths and hashes only);
- the controller-truth directory listing (opaque world IDs and file names);
- the root manifest, hashed only (`84949723…` confirmed) and never parsed.

**Never read or hashed:** any controller-truth file.

**Real data never touched by tests:** every orchestrator test runs on a synthetic universe. No real controller truth, no real fit output, no unblinded root-manifest content.

**Tests excluded from local runs because they read real truth or unblinding content** (not run by Macha):
- `test_v79_v2_core_score_truth.py`
- `test_v79_v2_core_score_quantities.py`
- `test_v79_v2_core_realization_audit_freeze.py`, which parses a truth-world manifest
- `test_v79_v2_core_seed_ledger.py`, which parses the root manifest

**CI:** no PR has been opened. The new `v79-v2-core-scoring-orchestrator-synthetic.yml` runs only synthetic and fixture suites. The truth-loading `v79-v2-core-controller-scorer.yml` triggers only on `pull_request` or dispatch, and was not triggered.
