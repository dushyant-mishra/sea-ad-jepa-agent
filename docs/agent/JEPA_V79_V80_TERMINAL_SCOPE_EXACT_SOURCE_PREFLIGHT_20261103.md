# V79/V80 successor-selection contract conflict — exact-source, non-authorizing preflight

**Date:** 2026-11-03. **Role:** independent GPT implementation and science-law reconciliation proposal, **not** a controller's approved replacement for the frozen contract. No estimator was fitted, no synthetic world regenerated, no hidden controller output opened, and no target/model/training authority granted.

## Why a new bounded preflight was needed, not a new framework

Macha [#531](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/531) correctly identified the old V79 **207 confirmatory vs V80 all-291** conflict as blocking the first successor-estimator fit. Unlike its initially mistaken claim of a missing #321 independent audit (already done by [#336](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/336)), this conflict is real and remains prospectively unresolved.

The controlling [V3.1 PR #344 §21](https://github.com/dushyant-mishra/sea-ad-jepa-agent/blob/847fe734b15e52f204f18903a124e1cfd3bf111d/docs/superpowers/specs/2026-10-14-lineage-composite-production-synthetic-v3-1-consolidated-corrective-amendment.md) already ruled: 207 confirmatory rows can bind successor selection; 85 post-terminal rows are **non-blind forensic** and cannot select, reject or qualify a variant. Macha independently accepted that *design ruling* (PR #344 comments [6160860703](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/344#issuecomment-6160860703) and [6160919216](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/344#issuecomment-6160919216)). Yet the qualified frozen [V80 PR #348](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/348) still says **all 291** previously passing V79 rows are mandatory non-regression selectors. The no-silent-rewrite rule is binding; the existing package and V79 history remain immutable.

## Exact source inputs, not inferred labels

All three raw files are read from original PR #348 frozen final head **`e99d1f214e76a5e3911eea438c32a1e60f70754f`** and verified against their original SHA-256:

| Input | Source file | Raw SHA-256 |
|---|---|---|
| V79 immutable original prospective Contract V2 | `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json` | `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26` |
| V80 non-regression binding | `results/v80/sparse_positive/V80_V79_NONREGRESSION_BINDING_V1.json` | `b83d7e0becbe5480353db657b553b7bb65251d3b88136be1d6c3cdda365c4819` |
| V80 frozen qualified package receipt, **benchmark only** | `results/v80/sparse_positive/V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json` | `346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32` |

The original V79 `scripts/v79/v79_v2_core_score.py:59–74` explicitly first-hard-fail-locks the terminal and classes subsequent results as `POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION`. The frozen Contract V2's gate list alone, without any controller-outcome values, establishes the Q08 positive convergence gate's identity and its row index.

## Structural reconciliation, source-derived

The Q08 `positive` component's `CONVERGENCE_ALL_FITS_DIAGNOSED` is **zero-based index 206** in the 292-row frozen gate list. The historical frozen V80 binding identifies it as the **only** failed gate, with three failed fits. Gate lists + the terminal-lock rule therefore imply:

| Segment of frozen V79 gate list | Rows | Hard FAIL-class gates | Nonhard LIMIT gates | Permissible authority |
|---|---:|---:|---:|---|
| Index **0–205**, before the first hard failure | 206 | **204** | **2** | Historical confirmatory, subject to original hard-vs-LIMIT law |
| Index **206**, terminal Q08 failure | 1 | **1** | 0 | Future successor must repair the **same** hard failure; original V79 stays NOT_QUALIFIED |
| Indices **207–291**, after the terminal lock | **85** | 83 | 2 | **Non-blind forensic only**; may not select/reject/qualify |
| Total | 292 | 288 | 4 | *292 is not 292 hard gates* |

**The 207-row confirmatory segment includes the terminal failed gate.** It is incorrect to count 207 *previously passed hard* gates: there are 204 previously passing hard gates, two nonhard LIMITs, and the one terminal hard FAIL. It is also incorrect to call the 291 historical passes `hard passes`; the frozen gate roster has four separately classified LIMIT gates.

This precision changes the prospective rule's required scientific semantics. A new estimator must preserve the preterminal 204 hard passes, resolve the terminal Q08 hard convergence failure on the same frozen estimable world, treat the original two preterminal LIMITs under their own nonhard law, and **cannot** be selected/rejected on any of the 85 post-terminal forensic gates. This paragraph is a **proposal derived from §21**, not an operative amendment to V80.

## Executable preflight

- `scripts/v5/audit_v79_v80_terminal_selection_preflight_v1.py` accepts only exact original raw artifacts and verifies the original V80 receipt, its binding and original V79 contract recursively at their recorded identities. It derives the 207/85 and 204/1/2 gate classes directly from the immutable original gate list.
- `tests/v5/test_audit_v79_v80_terminal_selection_preflight_v1.py` has seven tests: authentic contract split; fail-closed authority; mutated V79 bytes; reissued 207-row V80 binding; changed/truncated V80 receipt; reordered V79 terminal gate; preserved original LIMIT class.
- `.github/workflows/v79-v80-terminal-selection-preflight-v1.yml` fetches the pinned **exact PR #348 Git head** into GitHub Actions without copying those large/historical artifacts into `main`; tests on Python 3.11 and 3.12, zero external scientific data.
- It **always returns** `BLOCKED_EXTERNAL_V79_TERMINAL_LOCK_VS_V80_291_NONREGRESSION_SELECTION`, and all real, target, representation, Stage4, estimator-qualification and training authorities false. It does **not** implement a new selector, correct either old contract, adjudicate a candidate, or change any gate threshold.

## What actually resolves the blocker

An authorized controller must issue a **new, prospectively frozen, versioned successor-selection law** before any successor-estimator output is inspected. The new law needs independent hostile review and exact content/row bindings (preterminal 207, forensic 85); it must specify that post-terminal outcomes cannot influence estimator development or choice, and implement the original LIMIT class correctly. It must preserve and cite frozen V79/V80 history and the original benchmark's identity without silently claiming the new selection law was part of V80's historic qualification receipt.

Do not create a model-selection implementation or run one-shot successor fitting until a *reviewed* law and its selector/executor enforcement are authorized. This preflight is **evidence locating the exact conflict**, not a request to rerun V79, retune V80, or reopen spent science. Existing Task0–3/unified architecture and V3.1.1 STOP gates still apply.

**Independent reviewer requested:** Macha should attempt to falsify the derivation, original frozen SHA custody, 207/85 segmentation, LIMIT semantics and the strict `BLOCKED` authority boundary. A CI green on GPT-owned source is not independent acceptance.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
