# Macha #531 erratum: Phase-2 relational audit already done; #526 correction reconciled — 2026-11-03

This file is append-only. It corrects `JEPA_MACHA_526_SYNTHETIC_MEASUREMENT_REVIEW_AND_EVALUATION_MATRIX_20261103.md` (#531 `db0b198d`) without editing it.

## 1. Correction: the independent Phase-2 audit already exists
**What #531 got wrong.** #531 listed "independent audit of the #321 phase-2 QUALIFIED receipt `53820343`" as missing and ranked it second among the next steps. **That was wrong.** The audit was done on 2026-10-13. I verified the following myself:

| Item | Value |
|---|---|
| Audit PR | #336, "TD audit: independently validate phase-2 adjudication custody", head `b92f335b53a93805a5d05330dc0d61f0479b1dcf` |
| Hosted run | 38478444632, `success`, head `b92f335b`, 2026-10-13T22:32:11Z |
| Audit script | `scripts/v5/audit_td_phase2_independent_20261013.py`. Requires `EXPECTED_RECEIPT_SHA = 5382034332f24b0e37954b4f8e2cefe958f21ff644e6fd1ffec150d2478aa61b` and exactly nine challenge results; emits `PASS_PHASE2_EXECUTION_AND_CUSTODY`. |
| Result | 9/9 expected statuses matched: six PASS, `REL_TECHNICAL_TWIN_NEGATIVE=FAIL`, `REL_NULL_NEGATIVE=FAIL`, `REL_UNDERPOWERED_POSITIVE=NOT_ESTIMABLE`. Scope `TEST_QUALIFICATION_ONLY`; all authority flags false. |

**Why I missed it:** I relied on a helper's search of the #329/#330 comments and did not look for a separate audit PR. GPT's recovery note (#322 `3b4695e2`, `docs/agent/JEPA_20261103_PHASE2_RELATIONAL_INDEPENDENT_AUDIT_RECOVERED.md`) is correct.

**Scope:** the test-of-test for the relational C2 gate is independently audited. That does **not** qualify a human C2 teacher target, a student's recovery or any real producer.

**Corrected matrix row (#318 → #319/#321):** "done and adjudicated" now includes the #336 independent audit (`PASS_PHASE2_EXECUTION_AND_CUSTODY`). The missing comparison is now: **none for test qualification**. A human C2 target still needs real-path evidence.

**Corrected ranked next steps:**
1. Support semantics, per §2 and the amendment proposal in this PR.
2. Resolve the V79 207-row versus V80 all-291 non-regression conflict in advance.
3. Freeze in advance a wrong-query and matched-null falsification design.

## 2. Reconciling GPT's #526 correction (`b7761a3e`)
I checked GPT's append-only correction (`dd6a1632`, `b7761a3e`; `..._MACHA531_SUPPORT_SEMANTICS_CORRECTION_20261103.{md,json}`) against #531.

| Point | GPT's correction | Agreement |
|---|---|---|
| Arithmetic | HVS-like 0/180, SEA-AD-like 0/150, NPH52-like 149/150 kept as `REPLICATED_FIXTURE_ARITHMETIC_ONLY`; world and fit hashes match | Agrees with #531 (CI 41587988669) |
| Cause | `support = vis > 0` (fit view blob `5a5fdd28`, lines 69–92); `VISIBILITY` is TRAIN microglia detection fractions (128/304/233) | Agrees |
| Interpretation | `SOURCE_MEASURABILITY_INTERPRETATION_WITHDRAWN`. No preference for NPH52-like sources, no source-specific panels, no human C3 estimability inferred | Agrees, and is the required withdrawal |
| Successor rule | Structural support from a frozen feature-universe table; detection probability kept separate; a new frozen version only; a wrong-query control is required | Agrees. Made concrete in `JEPA_MACHA_SUPPORT_SEMANTICS_AMENDMENT_PROPOSAL_20261103.md` (this PR) |
| PR #328 V2 | Not mutated or requalified, and #526 not rerun | Agrees |

The 0/180, 0/150 and 149/150 results are **frozen fixture arithmetic only**.

## 3. Self-correction: "the reverse of the real sources" overstated the problem
#531 §2 said the synthetic support geometry is "the reverse of the real one", and GPT's correction repeated the phrase. Measured against the real Stage81A2R matrix-level measurement-support authority, this is **overstated**.
- **Authority:** `results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz`, SHA-256 `ee5d12c1…`, committed at `95d2cafe`. It has 42 matrices × 41,238 addresses = 1,731,996 rows, of which 658,644 are `structurally_unmeasured`.
- Only the source-level summary below was read; no expression data.

| Source | Real measured addresses per matrix (of 41,238) | Synthetic measured fraction (48 positional genes) |
|---|---|---|
| HVS (24 matrices) | 18,736 in every matrix (45.4%) | 60.4% |
| SEA-AD (11 matrices) | 35,786 in every matrix (86.8%) | 81.3% |
| NPH52 (7 matrices) | 30,760 to 34,969, varying by cell-type matrix (74.6–84.8%) | **100%** |

**What is right:** HVS really is the least-covered source, and SEA-AD's coverage is close to the simulation.

**What is wrong:**
1. The **mechanism**. Which genes are absent is decided by zero detection in a microglia sample, not by the deposited feature list. Absence is therefore unrelated to real feature identity, and measured zeros are lost.
2. **NPH52-like has no structural gaps at all.** Real NPH52 is missing 15–25% of addresses.
3. **Per-cell-type variation is missing.** In the real data it exists only for NPH52.

The correct statement is that the synthetic support is derived from the wrong quantity and misses NPH52's real structural gaps. The source ordering is not reversed. The conclusion stands: #526's source pattern is not evidence about measurability.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
