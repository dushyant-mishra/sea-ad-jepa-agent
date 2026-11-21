# Macha round of 2026-11-03: #528 erratum and repair, #525 new-head review, #526 review, blocker register

Append-only Macha delta. No historical file is overwritten. GPT's events 26 and 27 already record the #529 RED and GPT's public-source correction, and this delta does not repeat them.

## Deliverables
Each deliverable lists its commit, changed paths, CI, tests, limitations and review status.

**1. #528 public-source provenance erratum**
- **Commit:** `7f7dee82a264ec2e7780c5849154be4074d759ec`.
- **Paths (4):** `docs/agent/JEPA_MACHA_528_PUBLIC_SOURCE_PROVENANCE_ERRATUM_20261103.md`; its JSON companion; two public metadata snapshots under `public_source_metadata_20261103/`.
- **CI:** custody-audit [41586401638](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41586401638) at `1a4fda75`, PASS.
- **Content:** NPH52 is Zenodo 8319719 revision 2, open, CC-BY-4.0, with md5 checksums verified at acquisition. HVS is the public CELLxGENE collection `35928d1c`. Controlled raw Synapse objects were never acquired. R1/R2 become optional hardening; R3 is resolved; R8 is software readiness. The NPH52 internal restriction is retained. The QC-only allowlist is proposed, with the decision pending.
- **Review:** awaiting GPT.

**2. #528 QC admission repair (GPT #529 R01, R02)**
- **Commit:** `1a4fda758936a3cc3868948b44d25694de216bd9`.
- **Paths (4):**
  - `scripts/v5/review_probes/macha_20261103/specimen_qc_input_admission_v1.py`;
  - `tests/v5/test_macha_528_gpt_admission_hostile_red.py` (GPT's file, byte-identical, blob `49a86421`);
  - `tests/v5/test_macha_528_admission_repair_v1.py`;
  - `.github/workflows/macha-513-qc-input-admission.yml`.
- **Tests:**
  - **CI** [41586401678](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41586401678): ubuntu and windows **24/24**, symlinks supported on both runners.
  - **Local:** WSL 24/24. On Windows, 21 pass, 2 are skipped and GPT's R01 errors, because this host cannot create symlinks.
  - **Mutation (local):** 7/7 new and 11/11 original safeguards killed.
- **Limitations:** the 29 large H5ADs stay stat-only with inherited identity. Real-probe replay is held in code (`REPLAY_HOLD`).
- **Review:** awaiting GPT.

**3. #525 new-head review**
- **PR / commit:** [#530](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/530), `0a1310adb4df24a50422d3c60dc27b0f6e4fa28a`, tests only, on `315c378d`.
- **Tests (CI [41586882935](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41586882935), Python 3.11 and 3.12):**
  - #517 replay: 5 unexpected successes;
  - inherited suites plus #527: **86/86**;
  - guards and limits: **8/8**;
  - REDs: **11 failing sub-cases by design**.
- **Verdict: `REPAIR_REQUIRED`.**
  - **N01:** the evidence reducer ignores the manifest, so an arm whose query controls were never reported still reduces to PASS.
  - **N02:** not-estimable can be declared after results exist.
  - **N03:** the EMA callers still coerce with `int()`.
- **Limits L01–L05**, including that a caller-declared PASS is not qualification.
- **Satisfiability:** a throwaway reference repair gives 97/97.

**4. #526 synthetic review and reuse-first evaluation matrix**
- **PR / commit:** [#531](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/531), `db0b198dbd00ec13d40052324d18a8d5c3f2fdc3`.
- **Paths (4):** the review document, an independent replication script, the local replication JSON, and a workflow.
- **CI:** [41587988669](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41587988669) SUCCESS (numpy 2.3.5, equal to the local numpy 2.4.6 run and to GPT's aggregates); inherited PR #328 run [41587988560](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41587988560) SUCCESS.
- **Verdict:**
  - arithmetic **REPLICATED** (0/180, 0/150, 149/150);
  - software **ACCEPT_SCOPED**;
  - interpretation **CORRECTION_REQUIRED**. PR #328 sets `support = VISIBILITY > 0` from microglia detection fractions, which turns a measured zero into structural absence and reverses the real source geometry.
- **Matrix covers:** V79/V80, #318→#321, #328, #469 and #526.

## Remaining-blocker register
Each entry gives its status, evidence and owner. A blocker belongs to exactly one class. "Resolved" means resolved within the stated scope only.

## A. Source accessibility
| ID | Item | Status | Evidence |
|---|---|---|---|
| A1 | SEA-AD, HVS and NPH52 processed data | **RESOLVED.** Public: Allen open data; CELLxGENE collection `35928d1c`; Zenodo 8319719 revision 2, CC-BY-4.0. | #528 erratum `7f7dee82`; Stage81A1D records |
| A2 | Controlled raw releases (Synapse, 5,005 objects) | **NOT NEEDED.** Never acquired; raw reads are prohibited by project policy. | Stage81A1D Synapse audit |
| A3 | HVS licence string | Optional record-keeping. It is not in the CELLxGENE API payload. | erratum §2 |

## B. Data integrity
| ID | Item | Status | Evidence |
|---|---|---|---|
| B1 | QC-probe input admission | **REPAIRED; awaiting GPT review.** The #529 R01 and R02 REDs are green on Ubuntu and Windows. | #528 `1a4fda75`, CI 41586401678 |
| B2 | 29 large H5ADs (about 323 GB) | **Inherited scope.** Size and mtime checked; identity comes from `ASSET_AUTHENTICATION.csv`, not a fresh hash. | #528 |
| B3 | Level-4 count blocks (`.npz`) | Counted, not hashed. The 8,915 meta CSVs were hashed. | #513 ledger; #528 |
| B4 | Adapter inventory: 50 entries against 47 named | Reported, not reconciled. | #513 §0 |
| B5 | Unkeyed V2C receipts | Consumers must re-verify the bytes. A receipt is not evidence of validation. | #516 |

## C. Scientific qualification
| ID | Item | Status |
|---|---|---|
| C1 | Alias closure. Span overlap is not feature-model identity (UBE2R2-AS1, MIR4307HG, LINC02588; each binds 11 SEA-AD operators). | OPEN; provisional conservative restriction |
| C2 | Depositor selection and QC. HVS 1,000-gene floor inferred; SEA-AD rules unrecorded; NPH52 imports an annotation-based selection (22,715 quarantined). | OPEN; the #513 §4 protocol is not approved |
| C3 | Specimen identity: SEA-AD tissue-block keys; NPH52 specimen. | UNAVAILABLE |
| C4 | Cause of the HVS 0.915 denominator gap | OPEN |
| C5 | Teacher-target qualification. No qualified production JEPA target winner. Portfolio qualifications are caller-declared `PASS` (#530 L01). | OPEN |
| C6 | Cross-block query exposure: in a lawful C6 plan the SHARED teacher sees the query (#530 L04). | DESIGN QUESTION |
| C7 | Synthetic realism. PR #328's support mask turns zero detection in a microglia sample into structural absence, so its source geometry is the reverse of the real sources. | NEW FINDING (#526 review) |
| C8 | V79 `NOT_QUALIFIED` (291/292; Q08 hard FAIL); V80 qualifies a benchmark package, not an estimator. | PRESERVED |
| C9 | NPH52 internal restriction on real query issuance and quarantined-expression analysis | RETAINED; criteria for lifting are in the erratum §5 |

## D. Software readiness
| ID | Item | Status | Evidence |
|---|---|---|---|
| D1 | #525 post-TD contract | **REPAIR_REQUIRED** (N01 query controls unenforced at reduction; N02 post-hoc not-estimable; N03 EMA caller coercion) | #530, CI 41586882935 |
| D2 | #523 student container fail-closed entry | Proposed; awaiting GPT review | #523 |
| D3 | Release object with field-binding receipts and consumer re-verification (R8) | Specified, not built | #528 erratum §4 |
| D4 | Input custody for every released view (R7) | Partial (QC probe only) | #528 |
| D5 | Task 4–8 qualification; trainer | Not authorized | standing |

## E. Optional governance hardening and owner decisions
| ID | Item | Class |
|---|---|---|
| E1 | Independent signing key and trust root (R1, R2) | Optional hardening; not required by any data provider |
| E2 | Branch protection on `main`; separate GitHub identities for the agent lanes | Optional hardening |
| E3 | `JEPA_QC_ONLY_ANALYTIC_ALLOWLIST_V1` (`Doublet score`, `is_primary_data`) | **Owner decision pending.** The replay hold is enforced in code. |
| E4 | Alias table adoption (C1); approval of the #513 §4 protocol (C2) | Owner decisions |

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
