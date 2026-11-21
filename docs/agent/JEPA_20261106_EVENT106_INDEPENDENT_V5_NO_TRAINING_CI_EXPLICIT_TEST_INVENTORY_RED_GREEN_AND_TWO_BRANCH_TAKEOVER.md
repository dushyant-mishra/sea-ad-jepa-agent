# Event106 — Independent V5 implementation re-audit: unsafe wildcard CI collection → fixed non-stepping test inventories, RED→GREEN (NO TRAINING)

**Date:** 2026-11-06 (UTC). **Scope:** independent follow-on implementation safety review of the current combined stack. This is a *new* implementation finding, not another historical-science reconstruction and not certification of all inherited code or physical biology. The original Event90 complete curated source/data/results inventory and Event104/105 first-read records remain canonical and unmodified. The two permanent chronological custody branches are canonical historical [PR #322](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/322) and operational [PR #460](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/460), both draft and unmerged.

**Owner boundary remains** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`. NO actual V5 optimizer, backward, EMA, training, GPU/RT1–RT8, restricted human RNA, private V80 controller, target promotion, or Stage4.

## 1. Source-derived defect found on the second pass

At original combined [draft #590](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/590) head `a3a59eb934186a8ab329eb2b0b4385b3948d1f0a`, the new original-V5 U0 workflow did pre-collection AST checking of five explicit allowed test files. However **three other inherited workflows still discovered test filenames dynamically**:

1. `.github/workflows/jepa-v5-pipeline-identity-contract-macha-no-training.yml` ran `python -m pytest -q tests/test_jepa_v5_*.py tests/test_jepa_synth2048_*.py` after a broad grep-only scanning step.
2. `.github/workflows/jepa-v5-journal-v2-integration-macha-no-training.yml` ran shell `$(ls tests/test_jepa_synth2048_*.py tests/test_jepa_v5_full_state_readonly_audit_v1*.py tests/test_jepa_v5_structured_journal_preflight_v1*.py)` to construct pytest arguments.
3. `.github/workflows/jepa-v5-journal-v2-579-thread-completion-macha-no-training.yml` ran `tests/test_jepa_synth2048_attempt_journal_v2*.py` directly as an unbounded pytest filename glob.

These were **actual uncontrolled collection routes**, not proof that any completed hosted job performed a neural optimizer step. They risk future unreviewed tests entering CI merely because a filename matches a wildcard. The first workflow's grep does not prove indirect train/EMA calls absent. This is a separate gap from Event105's durable U0-only journal writer repair and is important because Event102 already disclosed one accidental local WSL wildcard execution of historical step-capable tests. Do not claim that incident was erased or repeat it.

## 2. Independent static-only RED and bounded GREEN

Opened [draft #592](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/592) **stacked on #591**, keeping #590/#591 unmerged. Static test-only head `a14ec64556208a48ac69a19d4091959cbd5581c3`; [RED hosted run 42248519185](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/42248519185) failed on **both Python 3.11.9 and 3.12.7**: three static unittest methods reported seven expected failing assertions/subtests per Python because workflow preflight/runner calls and manifest were missing. The RED workflow imported no Torch, never discovered pytest tests, and did not execute any optimizer/backward/EMA/model.

An initial GREEN attempt head `952e18685459f67d67ec98957f367176ef9dd51d` correctly refused test collection due to an **overbroad static rule that mistook `teacher.eval()` for Python built-in `eval()`**. That is preserved failing evidence, not a hidden success. Repair at final exact head **`7e4c45ae7991ed79d136922fd8d157ce847f9f47`** distinguishes the legitimate frozen teacher's `.eval()` mode switch from unsafe builtin `eval()`, while still rejecting actual optimizer-step/backward/EMA direct calls. New pure-static regressions test the distinction.

**Exact-head hosted GREEN at final #592:** **4/4 workflows, 8/8 jobs SUCCESS**, matrix Python 3.11.9 and 3.12.7. Runs `42249241987` journal integration, `42249241979` full canonical source/data contract with inherited non-stepping tests, `42249242012` thread/journal review, and `42249242013` no-torch/no-pytest static-only safety suite. No neural updates were authorized or added.

## 3. Implementation result and limitations

New `scripts/v5/jepa_v5_ci_explicit_nonstepping_allowlist_v1.py` binds fixed, literal reviewed path inventories: **40** files in the full canonical contract suite, **33** files in journal integration, **10** in thread/journal review. Before ANY pytest collection, each workflow invokes `--suite NAME --verify`; pytest execution then invokes `--suite NAME --pytest`, which reruns verification and launches a fixed path argv without shell glob expansion. Detection-only filesystem globs refuse if any newly matching test file appears unreviewed or an expected file disappears. Each allowlisted test source is AST-parsed and rejected for direct optimizer/backward/autograd/EMA/training entrypoints and executable builtin eval/exec/compile. The full suite now also triggers when new `tests/test_jepa_synth2048_*.py` files change. These are safety checks, **not** evidence of a qualified biological target or complete supply-chain integrity.

Exact new/changed Git blobs on #592 GREEN:
- `scripts/v5/jepa_v5_ci_explicit_nonstepping_allowlist_v1.py`: `1c742735c2f06c671d86ea7d5954f7a4e99d5442`
- `tests/test_ci_no_training_explicit_allowlist_v1.py`: `fecda5640df671420aa02aaae56fbeb58aef3a28`
- `.github/workflows/jepa-v5-explicit-nonstepping-inventory-static-audit-no-training.yml`: `19c5e1ea80a24860b1722b54c92d15c9ae7b9e69`
- `.github/workflows/jepa-v5-pipeline-identity-contract-macha-no-training.yml`: `7d05c59f14f5e49e47face9111bfcd3f79becb16`
- `.github/workflows/jepa-v5-journal-v2-integration-macha-no-training.yml`: `69fe230d69020c4c5ecb4272d8da17cf28013181`
- `.github/workflows/jepa-v5-journal-v2-579-thread-completion-macha-no-training.yml`: `4edfea1ef71d0ba52d856f63619e7cd2293e065f`

**Critical boundedness:** a fixed allowlist plus AST check prevents accidental automatic inclusion and listed direct call sites, but does NOT certify all indirect imports, dynamic subprocesses, Python binary wheels, private unsigned custody or any adversarially malicious reviewer. All other workflows must still be independently audited before claiming repository-wide execution security. Nothing now permits training. The original #591 genuine initialized U0 durable journal repair remains author GREEN 13/13 workflows 26/26 jobs at `ff1141fefa1377ac394be530c1236b682805e5e4`; independent reciprocal review #591 and #592 is pending, as is full Macha review of #590. The original 35-file V5 source/PR547 public FIT-only contract and dev-only authorization have not changed; no canonical source/rights hash or biology results were promoted.

## 4. Permanent future-agent handoff and two-branch update policy

Every new agent **MUST first read live PR #460's topmost first-read section**, current #322 chronology and no-repeat index, Event106 then Event105, Event104 and the original Event90 scientific source/data/result account. Confirm live SHA and reviewer status before working. **Do not reconstruct months of completed historical science or inspect owner-resolved V80 backup.** Implement only a truly new, owner-authorized engineering gap with bounded hostile RED→GREEN receipts. Append each confirmed new result as Event107+ to #322's chronology and no-repeat index **without modifying earlier events**, create identically byte-for-byte human Markdown and machine JSON on **both #322 and #460**, verify both blob SHAs, then prepend the latest first-read section on #460 and both PR descriptions using the exact verified #322 audit head. Link relevant source path/Git blobs, CI runs, failures, rights boundaries and independent review status. Never self-accept a substantive repair or merge unapproved drafts. Keep a readable new-agent implementation plan in the newest event, with no hypothetical training execution.

**Next engineering frontier:** independent cross-review of #590, #591, #592 exact heads and other remaining no-training workflows; external D1 ownership/rights/panel/teacher authority, full bitwise restore and genuine step-to-step V5 journal are **unimplemented and not authorized**. No target/representation winner and no clinical claim. Retain Event95 owner's resolved V80 backup and Event102 accidental local stepping-run disclosure verbatim. Research on physical FULL104/real RNA remains a separate permission boundary.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
