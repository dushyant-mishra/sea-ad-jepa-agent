# Macha — TD real-data qualification and hostile external review

Date: 2026-10-14.

**Final verdict:** `EXTERNAL_REVIEW_COMPLETE__REAL_SUPPORT_MAPPED_AND_AUTHENTICATED__NO_HUMAN_TD_GATE_EXECUTABLE__CONTRACT_AND_IMPLEMENTATION_REPAIR_REQUIRED__NO_CANDIDATE_OUTCOMES_OPENED`

Authority throughout: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This file is non-controlling (V3.1.1 E7). Every decision-bearing finding below is a candidate for the owning contract lane; none is adopted here.

## Bottom line

The news is mixed, and it is mostly protective.

**Good: the real data are clean and fully authenticated.**
- Every one of the 4,553,407 reader-fit nuclei has hash-verified integer raw counts.
- Counts sit only on measured addresses, and measured zeros are intact.
- Population identity matches the frozen registry exactly.

**Bad: none of the human gate surfaces audited here can lawfully run yet.** The surfaces are G2, G6, G8, G9/S1/S2 and R1.
- **G6, G2, R1 and the geometry engine can be steered to PASS or FAIL.** In each, a caller-typed token or label decides the verdict, rather than a computed, identity-bound quantity:
  - G6 accepts a zero margin and literal qualification tokens.
  - G2 and the geometry engine accept caller-labelled support and caller-chosen strata.
  - R1's null cannot tell library size from biology.
- **G8 cannot be calibrated as specified.** The calibration unit is undefined, and as written its 599-realization requirement can only be met by pseudo-replication.

**Structural population fact.** NPH52 has 0 reader-validation and 2 reader-oracle donors. The exact sign test needs at least 7. So:
- no donor-primary test of NPH52 on a held-out partition can be estimated with this split;
- any non-compensating source-stratified gate that requires NPH52 is `NOT_ESTIMABLE`.

This is a support fact, not a biological failure. It must not be removed by shrinking claim scope.

## 1. Custody — exact heads

| PR | surface | head | movement |
|---|---|---|---|
| #343 | G8 reference | `82d17bfb` | at expected |
| #345 / #352 | G6 probe / decision | `f16ba70f` / `bb1e35d3` | at expected |
| #349 | population registry | `1ab453e5` | at expected |
| #350 / #353 | R1 manifest / stress | `9b9078c1` / `1df20029` | at expected |
| #351 | C4 requires C6 | `2abcb9fe` (expected `b9774be4`) | `BRANCH_MOVED`, not `SCIENTIFIC_EXECUTABLE_CHANGED` |
| #354 | G7 terminal | `d9004730` | at expected |
| #355 | G9/S1/S2 engine | `6e5182e2` | at expected |
| #357 | G2 decision | `c174d052` | live head; appeared after the brief |

**#351 in detail.** The move is a 3-line edit of `tests/v5/test_jepa_post_td_harness_contract_v1.py`. Two inherited tests built C4 without C6, which the new rule forbids; adding `C6: PASS` keeps each test's purpose, since the rescue test still requires the error to name the failed constituent. All three checks pass at `2abcb9fe`. The harness failure is understood and repaired. C4 still has no downstream authority: C6 is unqualified and the V3.1 §15 TargetPortfolio gaps remain.

## 2. Population and support

Inputs:
- metadata SQLite `a771f08b…`;
- split `efe43e63…`;
- operator×address observation state `852cb3ec…`.

Only metadata was read.

| fact | value |
|---|---|
| identity closure | 6,351,753 cells, 149 donors, 42 operators, 3 sources, 2,028 donor×operator strata, 104/22/23 — all exact |
| donors crossing sources / partitions | 0 / 0 |
| operators spanning partitions | 42 of 42 (operator is not confounded with partition); operators nest inside source |
| donors with one operator | 1 |
| held-out donors by source | HVS 10 val / 11 oracle; **NPH52 0 / 2**; SEA_AD 12 / 10 |
| addresses measured in all 42 operators | 17,186 (strict core) |
| addresses measured in one source only | HVS 730, NPH52 4,894, SEA_AD 4,710; 289 never measured |
| support lost in reader_validation | 4,894 NPH52-only addresses are never measured there (no NPH52 operator) |
| class labels | NPH52 cells carry no broad class; SEA_AD subclass strata have 4–5 held-out donors each; 50 of 224 native-class strata have fewer than 7 donors |

Donor resolution is reported, not chosen. The exact one-sided sign test at family α = 0.01 needs `n ≥ ⌈log2(m/0.01)⌉` donors for a Bonferroni family of size m: 7 (m=1), 8 (m=2), 9 (m=3–5), 10 (m=6–10), 11 (m=11–20).

## 3. Raw-count census

The census covers the reader-fit Level-4 store, 8,915 blocks, against block manifest `66f589e5…` (75 GB).
- Every block was hash-verified.
- 4,553,407 unique `selection_row`s.
- 0 negative entries, 0 explicit zeros, and 0 entries outside `MEASURED_SCALAR`.
- One NPH52 block (512 rows) stores the library as integer-valued text such as `61129.0`, parsed strictly.
- Raw counts exist only for reader-fit donors. Reader-validation and reader-oracle RNA is not materialized, and was not opened.

**Observation-operator finding.** The normalization library is the full-source library.
- For HVS it equals the stored-address sum exactly.
- For NPH52 the stored addresses hold 96.0–99.9% of it; for SEA_AD, 75–100%.
- So an exact p-thinning must also thin the unmaterialized off-address mass: `L_p = Σ thinned stored + Binomial(L − S, p)`, cell-keyed.
- Keeping `L` fixed shrinks every normalized value by a factor of p, a pure artifact of about log(1/p) in log1p space.

Thinning drops detection but never structural support. Detected entries retained per donor:

| depth | median | range |
|---|---|---|
| 25% | 46% | 34–51% |
| 50% | 70% | 60–74% |
| 75% | 87% | 81–89% |

About 1.5 SEA_AD nuclei are expected to thin to all-zero at 25%.

## 4. G8 — human technical calibration (priority)

Status (refining the controller label):
`CONFORMAL_BOUND_ARITHMETIC_QUALIFIED__THINNING_MECHANICS_REPAIR_REQUIRED__CALIBRATION_REALIZATION_AND_ENDPOINT_SEMANTICS_OPEN__HUMAN_G8_NOT_EXECUTABLE`

All 894 donor×depth×endpoint units are tabulated in `g8/G8_DONOR_DEPTH_ENDPOINT_FEASIBILITY_V1.csv`. The 624 reader-fit units are `CONTRACT_GAP`. The 270 held-out units are blocked: raw counts are not materialized and RNA access is not authorized. No envelope was emitted, no draw made and no namespace consumed.

Available calibration observations per required unit (599 needed), reported without choosing a granularity:

| realization granularity | available | note |
|---|---|---|
| donor | 104 per depth (fit); 149 in the whole cohort | 599 is unreachable at any scope |
| donor × operator | 1,400 fit strata | clustered within 104 donors |
| cell | 4,553,407 fit cells; 103 of 104 donors and 492 of 1,400 donor×operator strata have ≥ 599 cells | clustered; valid only if the candidate state is per-cell and cells are the sampling unit |
| RNG thinning of fixed counts | unbounded | **pseudo-replication.** Every thinning reuses the same nuclei and molecules: exchangeable given the counts, but one biological sampling unit |

Every candidate that requires G8 needs a candidate-specific displacement before any score exists:
- C1 needs a representation-invariant state metric.
- C2 needs the R1 relational metric, ruler and tie law.
- C3 needs the query set, a per-query error metric, and a rule for queries whose detection changes under thinning.
- C6 and C4 need their block metrics plus a composition rule.
- C5 does not require G8.

#343 mechanics findings (local probes, `hostile_probes/g6_g8/g8_probe.*`):
- The conformal ranks are exact (599 at 0.01/6; upper rank 599, lower rank 1 at n = 599). The `−1e-12` epsilon rounds anti-conservatively at crafted α.
- `thin_integer_counts` uses one random stream per call, over the matrix in row-major order. So a cell's thinned counts depend on its row position. Two blocks thinned with the same seed get identical draws.
- There is no observation-state input: a masked structurally-unmeasured entry is thinned as if measured.
- There is no thinned library (see §3).
- `validate_seed_namespaces` is never called and has no refit slot (SA2 §7 needs four namespaces).

Inputs for the deciding lane's G8 contract, for its use only:
- key thinning randomness by cell identity and draw index;
- thin only `MEASURED_SCALAR`;
- freeze the thinned-library law;
- take the support-fraction denominator from units prospectively required before thinning;
- note an exchangeability point. A deciding thinning `T_p` is exchangeable with calibration thinnings by construction, so it passes at rate 1−α for any candidate. The full-count state is not a p-thinning, so the conformal guarantee does not cover the informative full-versus-thinned comparison.

## 5. G6 — feasibility

| candidate | teacher target / evidence rights | classification |
|---|---|---|
| C1, C2, C3, C6, C4 | not frozen (#349: `BLOCKED_EVIDENCE_CONTRACT` on all 2,028 strata) | **blocked on contract** |
| C5 | G6 not a required gate | not applicable |

Once contracts freeze, support can carry the probe:
- Leave-one-donor-out over 104 fit donors (HVS 41, NPH52 17, SEA_AD 46) resolves every source at m=1.
- Held-out NPH52 does not resolve.
- Sources measure different address sets (HVS 18,736, NPH52 35,098, SEA_AD 35,076). An evidence matrix over the union would contain structurally unmeasured columns, which ridge cannot take without imputation. The evidence universe per comparison is a contract decision.

**Decision layer (#352): STOP.**
- Ridge is closed-form, so U_refit ≡ 0. #352 accepts a 0 margin (`:143`), which makes the decision direction-only.
- Qualification is checked by literal schema strings (`:63-79`), and the decision layer qualifies itself with a literal `True` (`:260`).
- The qualification world is 1-D and noise-free. Planted-positive worlds FAIL 24/24 at b = 0.2, yet a human FAIL can still be emitted.
- Loss is in raw target units, so rescaling one component flips 11 of 16 verdicts.

Classification: `NOT_ESTIMABLE_BY_CONSTRUCTION` as a substantive-margin decision until a non-degenerate, produced and bound margin exists.

## 6. G9/S1/S2 — geometry feasibility

| object | real support |
|---|---|
| disjoint donor-balanced fit views | constructible: HVS 20/21, NPH52 8/9, SEA_AD 23/23 |
| held-out donor geometry | HVS 10/11, SEA_AD 12/10, **NPH52 0/2** → NPH52 `NOT_ESTIMABLE_IN_THIS_REAL_STRATUM`; held-out RNA also not materialized |
| null draws | 100 per donor (#355 `⌈1/α⌉`) is computationally cheap; distinct-permutation count limits small rare-class strata |
| same-metric references | none exist |
| required source strata | non-compensating; NPH52 makes any NPH52-requiring gate `NOT_ESTIMABLE` on held-out partitions |

**Engine (#355): STOP**, verified at the lines cited.

What holds:
- The engine is invariant to rotation, axis permutation and sign flips.
- It uses the adverse lower bound, not the median.
- It subtracts U_refit.
- Sources do not compensate for each other.

What breaks:
- The decision consumes displacements computed by the caller. The leakage guard compares only ID lists, a non-orthogonal map is accepted, and identical fake receipt hashes PASS.
- One donor short of null draws makes the whole source `NOT_ESTIMABLE` before stability is evaluated (`:331-338`). An estimable stability FAIL is lost.
- Rows from sources not listed as required are silently dropped (`:313`).
- Relabelling unstable donors as abstained turns FAIL into PASS.
- 3-cell donors become a biological FAIL, because the identity permutation is in the null.
- There is no eigengap guard.

## 7. R1 — feasibility

**Support.**
- Triplets are not limiting at donor level (every fit donor has ≥ 81 nuclei); they are limiting in rare class strata.
- Address-disjoint views on the same cells are constructible within each source's measured set.
- A cross-source common ruler needs the 17,186-address strict core.

**Executor (#350/#353): STOP.** It is a static manifest only, with no distance, triplet, null, U_refit or decision executor.
- The relation-label null is matched on donor/source/operator/support, but not on depth or detection.
- A world with only per-cell library-size variation beats it in 8 of 8 donors (+0.144, above planted biology's +0.087). A depth-block null closes this: 0 of 8 technical, 7 of 8 biology.
- #353 contains no adversarial world.
- Eligibility and ties are caller-controlled, and both-tie counts as agreement.

**Smallest repair:**
- a depth/detection-matched null;
- a mandatory technical-only negative that must FAIL;
- a frozen tie tolerance with provenance;
- a frozen view rule and digest.

## 8. G2 — audit

#357 decision arithmetic is correct. But:
- the baseline family, required strata, α, qualification and margin are all caller-supplied;
- the metric is a generic literal;
- support is caller-labelled.

Failing inputs:
- Passing only `constant_train_mean` turns the five-baseline FAIL into PASS.
- Dropping a failing stratum gives PASS.
- A zero margin gives PASS at +0.001.

Status semantics are wrong in both directions:
- 9 of 10 donors positive (p = 0.021, not significant at the family level) is emitted as **FAIL**, but the law allows FAIL only when the contrast is estimably nonpositive (`:184-187`);
- equal-to-baseline gives `NOT_ESTIMABLE`;
- a NaN raises instead of returning `NUMERICAL_FAILURE`.

Baseline inputs (operator, support fingerprint, library) are constructible from the audited real support.

## 9. Reference artifacts

| artifact | state | reason |
|---|---|---|
| population/support receipts | `REFERENCE_ARTIFACT_QUALIFIED` (support-resolution class) | identity-bound and replayed byte-identically |
| raw-count depth-support census | `REFERENCE_ARTIFACT_QUALIFIED` (support-resolution class) | same |
| G8 per-unit feasibility table | `REFERENCE_ARTIFACT_QUALIFIED` (support-resolution class) | same; emits no envelope |
| `U_measurement` | not generated | realization unit, displacement, denominator and library law are open; #343 RNG keyed to storage |
| `U_refit` | not generated | no frozen candidate estimator; ridge U_refit is degenerate |
| adverse-null calibration | not generated | no null producer exists; R1's null design fails the technical negative |

No universal noise threshold was created.

## 10. Hostile-attack matrix

| attack | result |
|---|---|
| support disappearing read as robustness | **open.** The G8 support-fraction denominator is undefined. #355 and #357 abstention is caller-labelled, so relabelling turns FAIL into PASS. |
| reference from the wrong realization | **open.** #355 and #357 check receipt hash format only; identical fake hashes PASS. |
| same metric name, different definition | **open.** #355 compares metric name strings; #357 uses a generic literal. |
| wrong donor roster | #355 and #352 require an exact roster match, but the roster is caller-labelled |
| source pooling rescues a failed source | non-compensation holds in #355 and #357; #355 silently drops non-required sources; R1 pools sources |
| operator confounding | operators span all partitions; operators nest inside source; source is an observation family, not a replicate |
| inadequate null tail resolution | #355 counts draws, not distinct permutations; R1 has no executor |
| duplicate or colliding identities | 0 donors crossing sources or partitions; 4,553,407 unique selection rows |
| outcome leakage into calibration | none: no outcomes or pathology read, and the Level-4 store certifies their exclusion |
| held-out data used to fit alignment | **open in #355.** The guard compares only ID lists; fitting alignment on held-out cells turns FAIL into PASS. |
| post-hoc claim-scope shrinkage | **open.** Abstention relabel (#355, #357); dropping a required stratum (#357); NPH52 must stay in mandatory envelopes as `NOT_ESTIMABLE`. |
| query scalar leakage | not exercisable: the C3 query contract is not frozen |
| synthetic threshold promoted to human | none found; G6 qualification is a toy world |
| branch drift taken as supersession | #351 `BRANCH_MOVED` is test-only; #356 plan cites the stale head (review P5) |
| FAIL where NOT_ESTIMABLE is required | **found.** #357 "not demonstrated" → FAIL; #355 3-cell donors → FAIL. The reverse also occurs: #355 one null-short donor turns an estimable FAIL into `NOT_ESTIMABLE`. |

## 11. Stop conditions reached (reported to controller)

1. Target/evidence contracts are not frozen for C1–C6 and the G8 realization. Reference generation stopped at support resolution.
2. No reference can yet be bound to its deciding metric or input.
3. Insufficient support prevents donor resolution for held-out NPH52 and for SEA_AD subclass strata. Reported as `NOT_ESTIMABLE_IN_THIS_REAL_STRATUM`; never FAIL, never scope-shrunk.
4. Held-out (validation/oracle) RNA is not materialized as raw counts and is not authorized here. Any held-out G8, G9 or R1 reference needs a separate controller decision on whether technical calibration on hold-out RNA spends the hold-out.
5. The held-out definition per gate is not uniformly frozen: within-fit cross-fitting versus reader validation/oracle. This decides whether NPH52 is resolvable.
6. The G8 contract is owned by the deciding lane, and no G8 contract text was written here. There was no concurrent modification.

## 12. Artifacts

| item | location / identity |
|---|---|
| branch | `audit/td-real-data-qualification-macha-20261014` |
| receipts | `results/target_discovery/real_qualification_macha_20261014/`; all bound in `QUALIFICATION_RECEIPT_INDEX_V1.json`, whose SHA-256 sidecar records the hash |
| hostile probe evidence | `hostile_probes/`, copied from the critics' worktree-scratch directories; local execution evidence, not CI |
| environment | Python 3.11.15, numpy 2.4.6, scipy 1.15.3 (`sea-ad-jepa-v3`), Windows 11 |

All executor test counts are local runs, not CI:

| PR | tests passed |
|---|---|
| #343 | 11/11 |
| #345 | 10/10 |
| #350 | 10/10 (23/23 including V1) |
| #352 | 23/23 |
| #353 | 8/8 |
| #355 | 18/18 |
| #357 | 9/9 |

Authority: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
