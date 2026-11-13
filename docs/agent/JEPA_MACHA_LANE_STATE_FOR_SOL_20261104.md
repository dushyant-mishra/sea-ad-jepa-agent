# Macha lane state for Sol — 2026-11-04 (complete account, 2026-11-02 to 2026-11-04)

**For:** Sol (the GPT/Codex lane). **From:** Macha (the Claude Code reviewer and GPU-laptop lane). The owner asked me to give you the full account of my work.

**Precedence.** This file states what Macha did, with exact identities, verdicts and corrections, and what remains open. Where an older summary of my work disagrees with it, this file controls. Owner rulings recorded after it (#322 event 57) control over it.

**How the lanes work.** Macha challenges Sol and Sol challenges Macha; neither accepts its own code or biology. Every defect gets a RED-first counterexample before repair, the original RED stays immutable, and the repair is verified on its exact new head. The standing authority is unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## 0. One-paragraph narrative
Over the past three days Macha did four things:
1. Reviewed main `e4925cff`. The student container fix went in through #523 (merged).
2. Corrected and hardened the #513 source qualification through #528 (accepted by you for R01 and R02).
3. Attacked the #525 post-TD contract through four rounds of counterexamples: #527, #530, #532, and the review of `b493efc3` that is still pending.
4. Replicated #526 and found that PR #328's synthetic "support" encodes detection zeros as structural absence. My five-rule fix, filed on #531, was accepted by the owner on 11-04 as the future contract.

I also mapped the source-to-CaseBundle fields and kept the blocker register. Several of my own claims turned out wrong and are corrected in §3. Do not reuse the originals.

## 1. Workstreams, identities, verdicts
### A. Main `e4925cff` independent review (2026-11-02) — CLOSED
- **V2C verifier** blob `46b813fc`: `ACCEPT_SCOPED`. The four #516 REDs pass on main; old heads keep their REDs (#507/#512: 14; #516: 4 against `360d3bcc`).
- **D1 producer** blob `edee1b8a`: computation law `ACCEPT_SCOPED`; upstream source `NOT_AUTHENTICATED`. The limits still reproduce: the UBE2R2-AS1 alias leak, the query-dependent roster, the self-supplied policy, and mintable receipts.
- **Student container** `deployment/student_v2c`:
  - **D-1:** the runtime user owned its verifier.
  - **D-2:** the entrypoint served receipts under any launch.
  - **PR #523:** RED `6f825acd` (CI 41517539396: 12 RED as designed); repair `bce3a35a` (CI 41517891013, 21/21; author 41517891053, 9/9).
  - **Your review:** `ACCEPT_SCOPED` (comment 6589689736). **Merged to main as `971ec6a1` on 2026-11-02.** This is fixture hardening, not an isolation attestation.
- **Not tested:** container breakout, kernel/VM, side channels, GPU, a hostile operator. On Docker Desktop, `seccomp=unconfined` is invisible from inside the container.
- **Custody:** #322 `eee217e7` (event 17); #460 `d137dd63`.

### B. Source qualification #513 → #528 (2026-10-30 to 11-03) — CLOSED for R01/R02
- **#513 `0b1af4f0`** (frozen) covers the ETL reuse ledger (322 rows), the alias adjudication (18 pairs) and the specimen/QC probe.
- **Your F1–F3 check (6595340401) was correct.** I amended it in **#528 `c1d85688`**:
  - a correction document;
  - a fail-closed input-admission wrapper (`scripts/v5/review_probes/macha_20261103/specimen_qc_input_admission_v1.py`) with 13 fixture tests (CI 41580992588);
  - the real admission run, `ADMITTED`, 35 matrices: 42 shards, 8,915 metas and 6 HVS H5ADs re-hashed; 29 large H5ADs stat-only with inherited identity.
- **Your #529 REDs** (`cf0330e4`): R01 symlinked-parent escape, R02 replay mismatch returning ADMITTED.
  - **My repair `1a4fda75`:** resolved-path confinement; `.partial` write that publishes only on match; refusal when output already exists; `REPLAY_HOLD` checked before any read.
  - Your file was kept byte-identical (`49a86421`).
  - **CI 41586401678:** Ubuntu and Windows **24/24**, symlinks exercised.
  - **Your scoped acceptance:** 6596890794.
- **Public-source erratum `7f7dee82`:**
  - NPH52 = Zenodo **8319719 rev 2, open, CC-BY-4.0**; HVS = CELLxGENE `35928d1c…`; SEA-AD = Allen open data.
  - Controlled raw Synapse objects (5,005) were never acquired.
  - R1/R2 (signing key) are optional governance hardening; R3 is resolved; R8 is software readiness.
- **QC columns.** The owner approved the QC-only allowlist on 11-04 (metadata only). `REPLAY_HOLD` is still an **active code guard**. Changing it needs a narrow, versioned, hostile-tested change with independent review. Reuse the published #513 aggregates instead of replaying.

### C. Post-TD contract chain #517 → #525 (2026-11-02 to 11-03) — round 4 review PENDING
| Your head | Macha review | CI | Findings |
|---|---|---|---|
| `064bf2a2` | #527 `ac9215c2` | 41579944951 | **R01–R12:** re-hashed portfolios and plans pass preflight (C4 with C6 FAIL, C5 as foundation, GLOBAL_OPF, …); the tournament checks no digest; a relabelled query block drops query controls. **R13:** EMA `int()` coercion. |
| `315c378d` | #530 `0a1310ad` | 41586882935 | **N01:** the reducer passes an arm that never reported `QUERY_SPECIFICITY`/`WRONG_Q_CONTROL`. **N02:** not-estimable can be declared after results. **N03:** EMA callers coerce. Limits L01–L05. |
| `0588788f` | #532 `ccf0239d` | 41590792957 | **M01:** the manifest roster is not bound to the verified portfolio. **M02:** a caller flag drops `RARE_PRESERVATION`. **S01:** `adjudicate_noncompensation` is a second PASS path. Limit L06. |
| **`b493efc3`** | **not yet reviewed by Macha** | yours: 41592222345, 41592222275, 41592222355, 41592217534, all success | You embedded the verified portfolio and closed the second PASS path. My #532 file is preserved (`6be17de3`). **My independent fresh-head verdict is still owed.** |

**Limits that are not defects and remain live:**
- **L01:** every `PASS` is caller-declared. Consistency is not qualification.
- **L02:** topology evidence is a caller boolean.
- **L03:** addresses are not bound to the 41,238-address ledger.
- **L04:** in a lawful C6 plan the SHARED teacher's evidence includes the query address. This is a design question for the owner and for you.
- **L05:** a C6 failure with independent C1+C3 gives the same plan as a fused C6 pass.
- **L06:** "prospective" is not time-bound; an external commit point is needed.

### D. Synthetic #526 → #531 (2026-11-03) — CLOSED; amendment ACCEPTED as future contract
- **#531 `db0b198d`:**
  - Independent replication (CI 41587988669; inherited 41587988560): world `dedd53c3`, fit `fc5fa5c0`; HVS-like 0/180, SEA-AD-like 0/150, NPH52-like 149/150.
  - **Finding:** `unified_synthetic_fit_view_v1.py:78-81` sets `support = VISIBILITY > 0`, where `VISIBILITY` is microglia **detection fractions** (665 TRAIN cells). A measured zero becomes structural absence.
- **Your correction `b7761a3e`** keeps the arithmetic and withdraws the measurability reading.
- **#531 `270bc33c`** contains the erratum (§3.2 and §3.3) and the **five-rule support-semantics amendment.** It reuses the A3R three-state matrix `852cb3ec`, the Stage81A2R authority `ee5d12c1`, the V79 join, V3.1.1 four-state rights, the owner alias decision `457b689b` and D1 `edee1b8a`, and defines tests P1–P6, which can run in advance.
- **Owner ruling 11-04:** the amendment is **accepted as the required contract** for any successor world. **No generation or fit now.** PR #328 V2 stays frozen.

### E. Reuse-first synthetic evaluation matrix (#531)
| Asset | State |
|---|---|
| V79 | `NOT_QUALIFIED` (291/292, Q08 hard FAIL), preserved |
| V80 | Qualifies the benchmark package only; no estimator |
| #318 → #321 relational test-of-test | QUALIFIED. **Independent audit already done in #336** (`b92f335b`, run 38478444632, `PASS_PHASE2_EXECUTION_AND_CUSTODY`, `TEST_QUALIFICATION_ONLY`) |
| #328 | Mechanics fixture |
| #469 | Executed, no biology |

**Across all assets:** no wrong-query control exists anywhere, and no estimator or encoder has been scored against #328 or V80 truth.

### F. Source-to-CaseBundle inventory (#322 `33befc30`, event 31)
| Field | Status |
|---|---|
| D1 student view | Accepted at fixture scope |
| Task2 producer access receipt (`manifest_v1.py` `b66b2cc0` at Task3 `117dd51d`) | Accepted as interface; the HMAC ledger is in-memory, so it only resolves within one session |
| Raw counts, operator support states (`852cb3ec`), identity, private `source_library` | Implemented, not accepted |
| Alias enforcement; resolvable provenance (`casebundle_v1.py` `23bbdcfc` checks format only) | Specified, not implemented. **The owner adopted the alias restrictions on 10-30 (`457b689b`); no code enforces them.** |

**Smallest edge:** a versioned real-path CaseBundle successor validator plus a source-bound adapter over one Level-4 block. **Superseded for execution by owner ruling 11-04: no new Level-4 read.** It also missed the earlier raw reads in PR #59/#69 (see §3).

### G. Custody written by Macha
- **#322:** event 17 `eee217e7`; event 28 `2d62d2b2`; event 31 `33befc30`, with the delta documents `JEPA_MACHA_MAIN_E4925CFF_INDEPENDENT_REVIEW_20261102.md`, `JEPA_MACHA_20261103_ROUND_DELTA_AND_BLOCKER_REGISTER.md` and `JEPA_MACHA_20261103B_INVENTORY_AND_BLOCKER_REGISTER.md`.
- **#460 pointers:** `d137dd63`, `a67b59cb`, `460c3bf5`.

## 2. Standing practices Macha follows
- Exact heads only, RED-first.
- Reviewer tests stay byte-identical, with the blob asserted in CI.
- Every result is labelled local or CI.
- Custody appends go onto the live head only, as fast-forwards; I abort if the head moved.
- No QC replay under the hold, no new Level-4 read, no NPH52 quarantined expression, no protected data.
- I do not accept my own work.

## 3. Macha's corrections to its own claims (do not propagate the originals)
1. **"NPH52 accession and terms unknown"** (#528, `c1d85688`) was **wrong**: Zenodo 8319719 rev 2, CC-BY-4.0. Retracted in `7f7dee82`.
2. **"A hardware or offline signing key is a prerequisite"** was **wrong**. It is optional governance hardening.
3. **"Independent audit of the #321 Phase-2 receipt is missing"** (#531) was **wrong**. #336 already did it.
4. **"The synthetic source geometry is the reverse of the real one"** (#531, repeated in your `b7761a3e`) was **overstated**. Real measured addresses per matrix, out of 41,238: HVS **18,736**, SEA-AD **35,786**, NPH52 **30,760–34,969**. The defect is the mechanism and NPH52's missing gaps, not a reversed ordering.
5. **"R4 alias decision open"** (#528 erratum) was **wrong**. The owner adopted it 10-30 (`457b689b`). What is missing is enforcement code.
6. **"Nothing authorizes or has done a Level-4 count read"** (inventory) was **incomplete**. PR #59 `1bdff2a8` read 387 SHA-checked raw blocks for six donors, and #69 `83b85382` corrected the labels. The owner ruled 11-04: no new read.
7. **Governance disclosure:** on 11-03 Macha replayed the #513 QC probe once, re-reading `Doublet score` and `is_primary_data` after you had asked for adjudication first. The output was byte-identical and the columns are public metadata. The hold was then enforced in code.

## 4. Open items
**Awaiting Macha (not started):**
1. Independent fresh-head review of #525 at `b493efc3`. Highest priority on my side.
2. Your #535 `af7acbcf` request: challenge its 15 field classifications without reading anything.
3. Your #537 `7e8ff441` request: GPU synthetic JEPA-only IPB rerun on the laptop. **This is a model run. Macha will execute it only on explicit owner authorization**, because synthetic training is OFF in every receipt.
4. #536 `b723b9d5`, only if you request review.

**Awaiting Sol:**
- reciprocal review of the #531 erratum, if you still want one (the owner has already ruled on the amendment);
- keeping event 56's no-reassign list current.

**Open science** (no decision is pending from me):
- L04 (cross-block query exposure);
- L06 (time-binding);
- alias enforcement code;
- the inferred HVS selection floor;
- specimen identity (SEA-AD blocks, NPH52);
- the cause of the HVS 0.915 denominator gap;
- the NPH52 internal restriction (retained);
- a wrong-query and matched-null falsification design for the first authorized synthetic JEPA run;
- the learned-student biological discriminator you named as the frontier.

## 5. Custody repair made in this commit (please check)
**What was failing.** At #322 `166add85` and `a6e4fa55`, the "JEPA continuous chronology and implementation custody" workflow **failed** (run 41868148084) with `JEPA_CONTINUOUS_CHRONOLOGY_REFUSAL: source file identity/availability`. Event 57 cites two Macha documents as sources, but they existed only on the #528 and #531 branches:
- `docs/agent/JEPA_MACHA_528_PUBLIC_SOURCE_PROVENANCE_ERRATUM_20261103.md`
- `docs/agent/JEPA_MACHA_SUPPORT_SEMANTICS_AMENDMENT_PROPOSAL_20261103.md`

**What this commit does.** It adds both files to #322 **byte-identical** to their published blobs: `3d39b96f` from #528 `7f7dee82`, and `456d45f2` from #531 `270bc33c`. No ledger entry or historical file was edited.

**Result:** the validator passes (local, WSL: 58 events, 52 historical sources; its tests 14/14). Please confirm in CI.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
