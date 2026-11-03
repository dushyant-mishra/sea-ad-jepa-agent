# Macha 2026-11-03 (second round): #525 fresh-head verdict, #531 erratum, source-to-CaseBundle inventory, blocker register

This delta is append-only. Every report below gives its commit, tests and limits.

## 1. Deliverables
| # | Deliverable | Identity | Tests / CI | Status |
|---|---|---|---|---|
| 1 | #525 fresh-head verdict | Reviewer PR [#532](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/532) `ccf0239d861bab9686fdfa3d863e8c81ef14e4bf`, tests only, on `0588788f` | CI 41590792957, Python 3.11 and 3.12. Preserved #527 (`123e6c92`) and #530 (`577944c0`) asserted byte-identical. #517 replay: 5 unexpected successes. Existing suite 98/98; guards and limit 4/4; REDs 6/6 failing sub-cases by design. Local results identical. | **`REPAIR_REQUIRED`.** M01: the manifest roster is not bound to the verified portfolio, so dropping or relabelling the query block or flipping the rare flag still gives PASS. M02: a caller flag drops `RARE_PRESERVATION`. S01: `adjudicate_noncompensation` is a second PASS path. L06: prospective declarations are not time-bound. A compatible repair keeps #527 and #530 green (local 7/7). |
| 2 | #531 erratum | [#531](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/531) `270bc33c291e1934d9fcfb32138bff298c64f5cb` | Documentary; facts re-verified | PR #336 Phase-2 audit **already done** (run 38478444632, `PASS_PHASE2_EXECUTION_AND_CUSTODY`). GPT's #526 correction reconciled. **Self-correction:** "reverse geometry" was overstated (real HVS 18,736, SEA-AD 35,786, NPH52 30,760–34,969 of 41,238 addresses). |
| 3 | Source-to-CaseBundle inventory | §2 below | Read-only code inventory (helper), spot-checked by Macha | The smallest remaining production edge is identified |
| 4 | Support-semantics amendment proposal | #531 `270bc33c`, `JEPA_MACHA_SUPPORT_SEMANTICS_AMENDMENT_PROPOSAL_20261103.md` | — | Five rules over existing records (A3R `852cb3ec`, Stage81A2R `ee5d12c1`, V79 join, V3.1.1 four-state rights, owner alias decision). Six consequences testable in advance. |
| 5 | Blocker register | §3 below | — | Replaces the 2026-11-03 register in event 28 where they conflict |

## 2. Source-to-CaseBundle field inventory
Read-only: code, git objects and manifest headers. No expression values were opened. "Accepted" means acceptance by the reciprocal reviewer.

| # | Field | Status | Where | Missing |
|---|---|---|---|---|
| 1 | Raw counts on verified addresses | IMPLEMENTED_NOT_ACCEPTED | `main:scripts/v4/materialize_full104_phase2_expression.py` (blob `98d8bd23`); Level-4 `MATERIALIZATION_CONTRACT.json`; block manifest `66f589e5…` (8,915 blocks; 4,553,407 cells; 42 operators). Writes only `MEASURED_SCALAR` addresses. | Reciprocal producer acceptance. GPT recorded `SOURCE_DOCUMENTATION_REVIEWED__PHYSICAL_REPRODUCTION_NOT_PERFORMED` (6583708392). Outputs are git-ignored and local only. Blocks counted, not re-hashed. |
| 2 | Operator × address support states | IMPLEMENTED_NOT_ACCEPTED | `main:scripts/v4/package_foundation_calibration_bundle.py:80` → `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` (`852cb3ec…`, uint8 [42, 41,238], 3 states); cross-check `stage81a2r_…measurement_support_candidate.csv.gz` (`ee5d12c1`, at `95d2cafe`) | Acceptance as support authority. Collision blocking per matrix lives in separate ledgers. |
| 3 | Cell, donor, specimen and library identity | IMPLEMENTED_NOT_ACCEPTED | `main:scripts/v4/build_full104_production_adapter_metadata.py` (blob `a92f9ec3`); 42 lineage shards; block meta | No per-cell library key in any artifact (#513 derives it from `exp_component_name`). Specimen UNAVAILABLE for SEA-AD and NPH52; HVS specimen = donor rests on the publication. Adapter count 50 against 47 unreconciled. |
| 4 | Query and alias restrictions | **SPECIFIED_NOT_IMPLEMENTED** | Owner **adopted** the 3 provisional conservative restrictions on 2026-10-30 (`457b689b`, `JEPA_512_513_DECISION_AND_ISSUER_ROLE_20261030.json`). Table in #513 (`0b1af4f0`). | **No code enforces it** (pickaxe search over all refs). The main D1 composed RED (`test_limit_a…`) still shows the alias leak. **Correction:** #528 erratum §4 "R4 open" is wrong. The decision exists; enforcement does not. |
| 5 | Private physical library size | IMPLEMENTED_NOT_ACCEPTED | `source_library` (whole source row before address mapping) in block meta. V2C excludes it (`_DEPTH=…NOT_PHYSICAL_TOTAL`). | No real-path code routes it into a private producer or teacher domain. It contains the query, NPH52 off-ledger mass and SEA-AD collision mass, so it must never reach the student. |
| 6 | Redacted D1 student view | IMPLEMENTED_AND_ACCEPTED (fixture scope) | main `28cbe3b2`: D1 `edee1b8a`, V2C `46b813fc`; Macha `ACCEPT_SCOPED` (#518; 6587639614); GPT #523 `ACCEPT_SCOPED` (6589689736) | No real-source invocation; schema `FIXTURE_ONLY` |
| 7 | Task2-compatible producer access receipt | IMPLEMENTED_AND_ACCEPTED (interface) | `scripts/v5/td_unified/manifest_v1.py` blob `b66b2cc0` at Task3 `117dd51d`, `validate_producer_access` lines 562–597; Macha `ACCEPT_UNIFIED_TASK3` (review `c33f2bd2`, #401); CI 38843717395 / 38843717378 / 38843717386 | No real producer calls it. The HMAC ledger is in memory, so it only resolves within one harness session. Donor-level only. Not on main. |
| 8 | Independently resolvable provenance | SPECIFIED_NOT_IMPLEMENTED | `casebundle_v1.py` blob `23bbdcfc` (#451 `bbdf9a90`) checks digest **format** only and returns `externally_authenticated=False`; GPT accepted fixture mechanics (6426554595) | Consumer-side resolution of manifest, policy and address-universe parents and of the access receipt (R7 partial, R8 specified) |

**Invariant check:** student D1 is the sum of base-right mapped counts and is never `source_library`. That holds in code (`edee1b8a`, V2C exclusion).

**Smallest remaining production edge:** one versioned **real-path CaseBundle successor validator plus a minimal source-bound adapter**. For one FULL104 Level-4 block it would:
1. verify the block's counts and meta SHAs against the `66f589e5` manifest;
2. join the lineage rows;
3. take each address's state from `852cb3ec`;
4. apply the three adopted alias restrictions;
5. put `source_library` only into the private `library_size` field;
6. produce student D1 with the accepted `edee1b8a` law;
7. attach the Task2 `ProducerAccessReceipt` over reader-fit donors;
8. resolve every parent digest;
9. return `NOT_ESTIMABLE` for NPH52 and for unsupported queries.

It reuses frozen `b66b2cc0`, `23bbdcfc`, `edee1b8a` and `46b813fc`, with no new issuer, target architecture or parallel CaseBundle.

**Can it be built now?** As code with synthetic, real-geometry tests, yes, it is small. **Running it on real values is blocked by three prerequisites:**
- **(a) Value-read authority.** Nothing authorizes reading Level-4 count values into a CaseBundle; the existing value-read gate covers TD Sample-A only.
- **(b) Selection and QC decisions.** The QC-only allowlist decision, the inferred HVS floor and NPH52 abstention are all open.
- **(c) Alias enforcement code.** None exists.

**Design limit:** the in-memory Task2 ledger means producer and consumer must validate within one session. Making it resolvable across processes would be a protocol change, so it is out of scope for "minimal". I therefore stop at identifying this edge and do not build an authenticated producer.

## 3. Remaining-blocker register (replaces the event-28 register where they conflict)
**Completed (within stated scope):**
- Public source access: SEA-AD, HVS, NPH52 (Zenodo 8319719 revision 2, CC-BY-4.0).
- #528 R01/R02 repair, GPT scoped acceptance (6596890794).
- #530 N01–N03 repaired at `0588788f`.
- Phase-2 relational test-of-test audit (#336).
- #526 arithmetic replicated and interpretation withdrawn (`b7761a3e`).
- Owner alias-restriction **decision** (`457b689b`).
- D1/V2C fixture law accepted (scoped).
- Task2/Task3 access interface accepted.
- #523 container fail-closed hardening: GPT `ACCEPT_SCOPED` (6589689736), merged to main as `971ec6a1` on 2026-11-02. This is fixture hardening, not an isolation attestation.

**Implementation readiness:**

| ID | Item | Status |
|---|---|---|
| I1 | #525 M01, M02, S01 | `REPAIR_REQUIRED` (#532) |
| I2 | Alias-restriction enforcement code | Missing |
| I3 | Real-path CaseBundle successor and source-bound adapter (§2) | Code is small; real use blocked by (a)–(c) |
| I4 | Consumer-side parent resolution (R7/R8) | Specified |
| I5 | Task2 receipt only resolvable in-process | Design limit |
| I6 | Adapter count 50 against 47 | Unreconciled |

**Scientific qualification:**

| ID | Item | Status |
|---|---|---|
| S1 | Alias identity (span is not feature model) | Restriction adopted; identity unproven |
| S2 | Depositor selection and QC: HVS floor inferred; SEA-AD rules unrecorded; NPH52 imported annotation selection | Open; #513 §4 protocol refused 10-30 |
| S3 | Specimen identity, SEA-AD and NPH52 | Unavailable |
| S4 | Cause of the HVS 0.915 denominator gap | Open |
| S5 | Teacher-target qualification: no qualified target; PASS values are caller-declared | Open |
| S6 | SHARED teacher sees the query in C6 (#530 L04) | Design question |
| S7 | Synthetic support semantics | Proposal in #531 `270bc33c`; successor not authorized |
| S8 | V79 207-row against V80 291-row conflict | Prospective ruling needed |
| S9 | Wrong-query falsification design | Not frozen; no asset has one |
| S10 | NPH52 internal restriction | Retained (scientific grounds) |
| S11 | Value-read authority for Level-4 counts into a CaseBundle | Absent |

**Optional governance hardening and owner decisions:**
- **Optional:** an off-machine signing key or trust root; branch protection on main; separate GitHub identities for the agent lanes.
- **Owner decisions:** the QC-only allowlist (`Doublet score`, `is_primary_data`; replay held in code); whether to authorize a #328 successor under the amendment.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
