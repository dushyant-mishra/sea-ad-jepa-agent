# Macha review and readiness delta — 2026-10-27 (append-only)

**Author:** Macha (independent reviewer for ChatGPT increments; author of the items marked "Macha-authored").
**Base:** audit PR #322 at `be27535854`. This file adds a record and edits nothing earlier.
**Machine mirror:** `results/target_discovery/unified_qualification_v1/JEPA_MACHA_REVIEW_AND_READINESS_DELTA_20261027.json`.
**Probes:** `scripts/v5/review_probes/macha_20261027/` (synthetic values only).
**Evidence labels:** every number is labelled **CI** (exact-head GitHub run) or **local** (Windows Python 3.11.15 with NumPy 2.4.6 or 1.26.4; WSL with NumPy 1.26.4).

Authority is unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## 0. Heads verified live before acting
| PR | head | note |
|---|---|---|
| #470 | `2e173fa48895` | reviewed |
| #467 | `180b550e96b7` | reviewed |
| #464 | `f6ee226c146c` | reviewed |
| #465 | `3b86b9467506` | Macha-authored; ChatGPT `ACCEPT_INCREMENTAL_WITH_LIMITATIONS` (V8e) |
| #449 | `062bfe369348` | my RED; unchanged |
| #469 | `7a6477244dfc` | unreviewed by me |
| #322 / #460 | `be27535854` / `b9d8414152` | both moved during this session (ChatGPT chat-exclusive takeover records); not edited |

## 1. Independent verdicts on ChatGPT increments
| PR | verdict | new RED (tests only) | CI on the RED | key finding |
|---|---|---|---|---|
| **#470** G7 E3 R3–R5 | **`REPAIR_REQUIRED`** ([comment](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/470#issuecomment-6452013488)) | **#472** `98a893f2` | [40571069907](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40571069907): inherited 45 passed / 10 deselected; review 9 failed / 7 passed | Closed: R3 (exhaustive 19,110 rosters, bound collisions 9 → 0), R4, and R5's recursion part. Open: **R5X** (6 routes where a payload chooses the exception) and **R6** (validate in place: a hostile row key or `level_id` gets a **BOUND receipt for forged support**, and V3 goes NOT_ESTIMABLE → **PASS**). **R1D** joins R1/R2 (one donor's 8 specimen IDs bound as 8 donors; V3 PASS). All pre-existing at `062bfe36`. |
| **#467** Unified Task 1 V1/V2 | **`ACCEPT_INCREMENTAL_WITH_LIMITATIONS`** ([comment](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/467#issuecomment-6451979345)) | none | author [40543388869](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40543388869) | Differential 20k: **0 asymmetric** on Windows (np2 and np1.26) and WSL (was 542). The KAT matches. Consumer overlay on `3b86b946`: Windows 402 passed; WSL 400 passed + 2 B5 (local, not a committed head). |
| **#464** PS Task 1/2 | **`REJECT_INCREMENTAL`** ([comment](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/464#issuecomment-6452244879)) | **#473** `48453e4d` | [40573969293](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40573969293): Linux 7 failed; Windows np1.26 / np2 9 failed each | The 12 mechanical #458 cases are closed and **T2-D is correctly preserved RED**. **V1 was introduced**: the PS exact-type whitelist omits `intc`/`uintc`, giving 811 of 20k payloads asymmetric on Windows (all explained), 0 on Linux. V2 (`__name__` in six refusal messages) has been pre-existing since `ff597faf` (my code). |

**Correction (append-only).** My 2026-10-27 requalification comment on #437 ([6444309187](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/437#issuecomment-6444309187)) says "Macha authored Task 3 (#432/#437)". That is wrong. ChatGPT authored #432; Macha authored the #437 repair; ChatGPT (the #432 and #439 author) accepted #437 at `fd3242ad`. The conclusion still stands: the requalification needs a reviewer other than Macha.

## 2. R1/R2 physical-provenance feasibility (source-backed)
Method: I read code, contracts, manifest headers and receipts only. No array, protected partition or outcome value was opened. A read-only survey helper's claims were spot-verified against source; the key lines are cited.

### 2a. Already evidenced
| fact | source | limit |
|---|---|---|
| Source bytes authenticated at download | `ASSET_AUTHENTICATION.csv` (`d8bccf6c…`, 42 assets); NPH52 Zenodo md5 checked | SEA-AD and HVS have a local SHA only (no vendor checksum); nothing upstream of the processed objects |
| Each Level-4 row is one row of an authenticated source matrix | `scripts/v4/materialize_full104_phase2_expression.py:215-217`: string equality of `canonical_cell_id`/`donor_id` to the source row; contract `612b4574…`; block manifest `66f589e5…` | establishes "deposited matrix row", not one physical nucleus |
| Raw integer counts per address | same script, line 220 (H5 path) | the NPH52 R path has no integer check |
| **The physical total contains the queried gene** | line 222: `libraries.append(int(np.rint(values).sum()))` over the **whole source row, before address mapping** | so `source_library` includes q, plus off-ledger mass: pooled 3.82%; HVS 0; NPH52 1.4%; SEA-AD 3.99% (max 25%) (`NORMALIZATION_DENOMINATOR_SUMMARY.json` on `origin/review/n1-all104-physical-raw-count-execution-20260925`) |
| Per operator × address measurement state, codes 0/1/2 | `src/sea_ad_jepa/v4/contextual_query_local.py:19-21`; `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` `852cb3ec…` (not opened) | no per-cell × gene mask; `WITHHELD_BY_EVIDENCE_RIGHTS` exists only in design and fixtures |
| Feature identity | Stage81A2R: 41,238 injective addresses (`e80ddfe6…`) | genes only; 2,010 NPH52 non-universal features are excluded from addresses but their counts remain in `source_library` |
| SEA-AD acquisition keys exist | source obs `sample_name`/`load_name`/`method`; `results/v4/stage81a1b_*crosswalk*.csv`; 12 library-swap corrections (8 compatible, 4 absent, 0 conflicts) | `candidate_only_not_frozen`; not carried into Level-4 or the CaseBundle |
| No duplicate cell keys | `FOUNDATION_METADATA_ANOMALY_AUDIT.json` (`040b938d…`) | string-level only |
| Multimodal pairing | SEA-AD MTG exact RNA–ATAC barcode links (144,023 / 138,118 nuclei); PR #182 GSE214979 same-nucleus (105,332/105,332); PR #164 GSE174367 **separate nuclei** (barcode overlap at null level) | pairing is by ID equality, not physical proof |

### 2b. Cannot be reconstructed from what we hold
1. **One deposited row = one physical nucleus.** Doublets, ambient RNA and barcode collisions can only be ruled out with BAM/FASTQ or Cell Ranger outputs, and project policy forbids downloading them (`FORBIDDEN_DOWNLOAD`). This is an **irreducible external assumption**.
2. **Read- or UMI-level lineage:** same blocker.
3. **SEA-AD specimen / tissue-block identity:** it would need Allen specimen metadata, which has not been acquired.
4. **Donor identity across namespaces** (HVS / NPH52 / SEA-AD): only string comparisons exist.
5. **R5 producer code:** absent from git and disk; only reports remain. The R5 precedent cannot be reproduced.
6. **Off-ledger aliases:** whether any off-ledger source feature carries molecules of an addressed gene is not attested.
7. **Depositor-derived quantities:** cell inclusion (QC on whole-transcriptome totals) and obs fields (n_genes, cluster labels, embeddings) were computed with q present.

### 2c. Least invasive credible repair
**R2.**
- **The law.** Depth = whole-row raw total − every measured count whose right lies outside the **base** level. It is **invariant across the rights ladder**: it satisfies G7 E3 byte invariance and V3.1.1 E3 ("rights change evidence, never depth"). A collision address outside the base rights is NOT_ESTIMABLE.
- **Implemented at fixture scope as #474** (§4). On real Level-4 data the depth is computable exactly from data already held: `source_library` − stored counts of outside-base addresses. No download is needed.
- **Consumer contract change, for the deciding lane.** CaseBundle `Σcounts ≤ library` and G7 `count ≤ library_size` assume a physical total. The G7 pooled-total equality screen is a heuristic: it misses #449's offset and scaled leaks, and it falsely refuses lawful depths. The recommendation is to separate the depth covariate from the physical total.
- **Still needed:** a reviewed source producer, plus attestations for off-ledger aliases and depositor-derived features.

**R1.**
1. Coordinate atom identity bound to `(asset SHA, matrix row, address)`. This makes within-matrix splits and copies impossible by construction, since there is one integer per row × feature.
2. Freeze the SEA-AD acquisition keys (`sample_name` + barcode) into the observation stream, so cross-matrix duplicates of a physical barcode-in-library are detectable. Read only non-outcome obs columns.
3. A per-source donor registry with a library→donor map, including the 12 swap corrections. This closes R1D within a source.
4. Scope every physical claim to "deposited count-matrix row" and keep G7 physical identity **BLOCKED** for anything stronger.

**External dependencies:** Allen specimen metadata (item 3); BAM/FASTQ (items 1–2), which need explicit authorization.

## 3. Production-synthetic V3.1.1 implementation and acceptance matrix
**Sources:**
- design: #344 `847fe734`, `docs/superpowers/specs/2026-10-14-…-v3-1-consolidated-corrective-amendment.md` + `…-v3-1-1-erratum.md`; design accepted by Macha (#344#issuecomment-6160919216);
- plan: #356 `2c2723a1`.

The "Task 4" PRs #413–#465 are **Unified** Task 4 (custody publisher), not PS Task 4.

| PS task (per #356) | implementing PRs / heads | independent status |
|---|---|---|
| 1 `canonical_v1.py` | `ff597faf` (Macha) → #453 `8641a62a` → #464 `f6ee226c` (ChatGPT) | #453 REJECT_INCREMENTAL; **#464 REJECT_INCREMENTAL (V1)**; cumulative pending |
| 2 `custody_v1.py` | `ff597faf` → #456 `3b42b6c1` → #464 | #456 ACCEPT_INCREMENTAL_WITH_LIMITATIONS; **T2-D open** (no authenticated scan issuer) |
| 3 `calibration_v1.py` | #432 (ChatGPT) → #437 `fd3242ad` (Macha repair) | #437 `ACCEPT_PS3_FIXTURE_MECHANICS_WITH_LIMITATIONS…` by ChatGPT; requalification at `3b42b6c1` pending a non-Macha reviewer |
| 4 `biology_v1.py` | **none** (0 commits on any remote) | **not started; blocked** (gate: Tasks 1–3 each independently accepted) |

Sequencing deviation: PS Task 3 (#432) started on 10-26 before Tasks 1–2 had independent acceptance, contrary to the #431 condition. It is recorded here; no action beyond requalification is needed.

| V3.1.1 requirement | status | evidence |
|---|---|---|
| 1 candidate-neutral mechanisms | DESIGN_ONLY | V3.1 §4.1/§4.3; no `biology_v1.py` |
| 2 overlap, heterogeneity, novelty, out-of-basis | DESIGN_ONLY | V3.1 §4.2/§5/§18 |
| 3 physical sparse RNA/ATAC operators, authenticated calibration | DESIGN_ONLY | PS Task 5 absent. The calibration firewall is fixture-accepted, its registry is empty and `calibration_eligible` is always False. #471 (historical 97-file intake) has 0 reviews |
| 4 evidence vs depth separation | DESIGN_ONLY (PS); the **depth law is implemented at fixture scope in #474** | V3.1.1 E3; real G7 E3 is RED |
| 5 same- vs separate-nucleus handling | DESIGN_ONLY (PS) | only in the #328 fixture (`multimodal_mode`), which is barred as production |
| 6 default-deny custody, withheld challenges | IMPLEMENTED with an **open hostile RED (T2-D)**; not accepted | `custody_v1.py` `record_withheld_commitment`/`scan_secret_absence` @ `f6ee226c`; fit packaging (Task 9) design-only |
| 7 committed seeds, realism rules, support thresholds, stopping | PARTIAL | RNG/seed commit pending cumulative acceptance; `RealismContract` stop is fixture-accepted at `fd3242ad` (O2: uncapped `max_iterations`); E4 minimum support not implemented |
| 8 V79 terminal lock, V80 conflict, negative priors | EXTERNALLY_BLOCKED | `PREMERGER_UNRESOLVED_WORK_LEDGER_V1.json:249` @ `e37a22b8`; no V79/V80 reference in PS code |

**#328 is confirmed as a limited mechanics fixture:**
- 48 genes / 480 cells / 16 donors, with contiguous signed gene blocks;
- controller-side C1–C6;
- receipt `SYNTHETIC_STRESS_PRESET(S)_NOT_EMPIRICAL_CALIBRATION`;
- every authority flag false.

**Tensions to watch:**
- #469's table calls it a "Qualified limited unified synthetic generator/fit";
- #468 maps biological-state claims onto `PR328_*` cases.

Neither may be read as production evidence.

## 4. Known-truth execution readiness
The chain: candidate-neutral biology → physical observations → CaseBundle → measured target producers → gate executors → decisions → external truth adjudication.

| link | state | first blocker |
|---|---|---|
| **1 biology generator (PS Task 4)** | **ABSENT** | gated by PS Tasks 1–3: #464 V1 and T2-D open; Task 3 requalification pending |
| 2 observation operators (PS Task 5) | absent | needs authenticated current calibration sources (#471 is historical, unreviewed) |
| 3 CaseBundle | fixture validator only (#440 → #451 narrow) | no production adapter; no q-exclusion law (now #474, fixture); the library-semantics conflict |
| 4 measured target producers (teacher constructs, not predicts) | none in production | R5 code missing; the #460 guard (comment 6450069779) applies |
| 5 gate executors | G7 V3 historical; E3 binder **REPAIR_REQUIRED** | R1/R2/R1D; R5X/R6 |
| 6 TruthBundle adjudication | fixture `validate_truth_separation` only | external adjudicator not built |

**The first missing genuine connection is link 1.** A lawful pair of cases (one identifiable, one no-winner) cannot be built without candidate-neutral mechanisms. Building them is PS Task 4, which is **not authorized**. Hand-built C1/C3 labels are forbidden. Sealed qualification is therefore **not possible**.

**Nonpromoting increment delivered now: #474** (Macha-authored; independent review required). It is a query-excluded depth producer at the observation → CaseBundle / G7 edge, which lies on the critical path of both the synthetic and the real routes. Laws are tested by same-cell counterfactuals:
- RED `36a6d522`: 93 failed (CI `40576364421`);
- GREEN `4520e4eb`; head `e7635e79` (workflow history fix): CI [40577079947](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40577079947) **101 passed** and full `td_unified` **386 passed**; Task 2/3/5/integration workflows all success;
- three RED-first self-audit rounds;
- local G7 conformance probe: 172/200 accepted, and the 28 refusals are both consumer-semantics findings.

## 5. Records created by this session
- **RED (tests only):** #472 (G7), #473 (PS Task 1/2).
- **Verdicts:** #470, #467, #464.
- **Implementation:** #474 (draft).
- **This delta.**

Not done:
- #460's pointer file is untouched; a comment links this delta. Pointer changes are coordinated with ChatGPT.
- #469 is not reviewed.
