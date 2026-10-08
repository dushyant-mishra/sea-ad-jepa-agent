# Teacher/Student V5 — data-first successor design

Date: 2026-09-08

Status: `SCIENTIFIC_TARGET_FROZEN__MECHANICS_PROTOTYPE_PASS__NO_TRAINING_AUTHORITY`

## Governing principle

The dataset defines support and estimability. The pipeline may select, pack, mask, weight, or decline to estimate, but it may not require unsupported observations or mechanics-sample geometry to exist.

V5 preserves V4 as an immutable audited baseline. V5 is a successor data-interface, objective, stochasticity, and schedule design; it is not a mutation of V4 review bytes and it is not a statewise continuation claim.

## Frozen reader-fit data authority

The design uses reader-fit-only descriptive authorities from the foundation calibration bundle:
- metadata SQLite SHA-256 `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`;
- operator support SHA-256 `1814a22c8ae01ee94a6fe132546a029af01a7d762384d53c152f37cb545787c1`;
- 3,292-cell mechanics inventory SHA-256 `7ac13973162a46cafa5baa24c5bea14beb64bd5859e8f58900801eee07083a30`;
- operator observation-state SHA-256 `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`;
- support recurrence SHA-256 `8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da`.

No pathology, reader-validation, oracle, DEV, or SEALED outcome is opened by these profiles.

## What the full data says

Reader-fit contains 4,553,407 cells, 104 donors, and 42 operators:
- HVS: 198,718 cells / 41 donors / 24 operators;
- NPH52: 236,476 / 17 / 7;
- SEA_AD: 4,118,213 / 46 / 11.

Raw cells are ~4.36% HVS, 5.19% NPH52, and 90.44% SEA_AD, while donor shares are ~39.42%, 16.35%, and 44.23%. Raw cell count therefore cannot be allowed to choose the scientific estimand implicitly.

There are exactly 1,400 reader-fit donor×operator groups. Their sizes are ragged: min 1, p5 4, p25 46, median 228, p75 3,169, p95 ~16,498, max 42,209. 1,361/1,400 groups have at least three cells and contain 99.9987% of reader-fit cells.

The historical 3,292-cell mechanics inventory spans the same 1,400 groups but contains only 1–5 sampled cells/group. Its median group size 2 is a subsampling artifact, not production geometry. V5 forbids inheriting production group size, replay cap, batch shape, or relational estimability from that mechanics sample.

## Measurement support and evidence semantics

Measured scalar support is operator-dependent:
- HVS 18,736 addresses/operator;
- NPH52 30,294–34,405, median 32,445;
- SEA_AD 35,076.

The historical 40%-hidden rule therefore exposes 11,242 HVS addresses (27.26% of the 41,238 universe) versus 21,046 SEA_AD addresses (51.04%). “60% evidence” is only a within-support statement. V5 reports both within-support and universe-relative evidence.

Exactly 17,186 canonical addresses are MEASURED_SCALAR in all 42 operators. This exact common core is an admissible `COMMON_CORE_ANCHOR` view family, aligned with the common-support basis used by TD59. It does not replace native support: `NATIVE_SUPPORT_COVERAGE` remains a distinct admissible view family. Visible counts, target counts, view weights, views/family, and block geometry remain unfrozen.

## Model/scientific invariants retained

- canonical 41,238-address identity namespace;
- continuous measured scalar semantics and structurally-unmeasured != measured zero;
- IPB width 160 / 6 blocks / 4 heads unless separately re-qualified;
- EMA teacher has no gradients and moves only after a proved optimizer step;
- direct 160-D `cell_state` for learned-geometry qualification;
- scale-free anchored triplet ordering rather than absolute-distance matching;
- no learned locality selector, no nearest-third hard-local objective, and no production nearest-half fraction inherited from TD59;
- protected populations remain closed.

## Qualification mechanics are not production geometry

Historical values 128 cells/update, microbatch 8, four masked views, 40% hidden, 16 blocks, replay cap 8, and u40/u205 horizons remain historical/bounded qualification mechanics only. V5 `ProductionScheduleAuthorityV2` has no defaults and requires explicit separately frozen values.

## Scientific target, proposal, and compute are three authorities

### Scientific target p

Frozen base target:

`L_base = mean_donor(mean_cell_within_donor(mean_view(block_JEPA_loss)))`

Policy: `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`.

Frozen relational target:

`L_rel = mean_donor(mean_eligible_anchor_cell_within_donor(mean_unordered_comparator_pair_within_anchor_operator(scale_free_order_loss)))`

Policy: `DONOR_UNIFORM__ELIGIBLE_ANCHOR_CELL_UNIFORM__SAME_OPERATOR_COMPARATOR_PAIR_UNIFORM_V2`. Operator is an admissibility boundary; eligible group mass is proportional to eligible anchor-cell prevalence inside donor, never equalized by operator identity or weighted by O(n^3) triplet capacity.

Group combinatorial capacity receives no scientific weight. Source is a mandatory domain/robustness diagnostic, not automatic equal objective mass.

### Proposal q

Proposal remains unfrozen. When `q != p`, exact `p/q` correction is required. Frozen reader-fit diagnostics show why proposal must not be confused with target:
- raw cell-uniform q for donor-uniform p: ESS ~9.68%, max/min weight ratio ~2,149.5×;
- source-uniform/cell-within-source q: ESS ~40.58%, ratio ~296×;
- mixtures with donor-uniform q improve ESS further but increasingly repeat cells from very small donors.

No mixture alpha is selected because the appropriate repeat/variance tradeoff depends on the prospectively frozen presentation horizon and exposure constraints.

### Compute packing

Compute packing receives an already selected scientific cell set and weights. It may only partition/reorder execution according to deterministic support/token rules; it may not change target mass, proposal probability, or selected cells. No production token budget is supplied by V5 design code.

## Packed canonical-token path

Teacher execution can process only structurally measured canonical IDs; student execution can process only visible measured IDs. Gene identities stay canonical 0..41,237; there is no biological-ID remapping. Target-block query identities remain canonical, and teacher block gather uses an explicit canonical-ID to packed-position map.

Eval-mode dense/packed attacks reproduce valid teacher/student states, predictor outputs, and block-JEPA loss to numerical precision. This establishes algebraic admissibility, not V4 statewise continuation.

## Packing-invariant stochastic identity

Ordinary PyTorch dropout is intentionally retained as a negative control: tensor removal/reordering changes its RNG stream.

The current **reference-only** V2 contract uses Philox4x32-10 with an injective scientific address within declared ranges:
- key[0] = uint32 `run_seed`;
- key[1] = uint32 `update_index`;
- counter0/1 = low/high 32 bits of the stable 64-bit cell key;
- counter2 = `(feature_uint16 << 16) | (canonical_token_key + 1)_uint16`;
- counter3 = `domain_uint8<<24 | site_uint8<<16 | layer_uint8<<8 | view_uint8`.

The observed reader-fit stable-key range, including values near 2^63, fits the declared 64-bit field. Tensor position, packed position, microbatch ordinal, and device do not enter the random address. The reference passes the Random123 known-answer vector, address-injectivity attacks, real stable-key tests, and train-mode dense/packed state+gradient attacks.

The CPU scalar implementation is deliberately not a production kernel. An optimized GPU kernel must be independently checked against exact V2 test vectors before authorization.

## Weighted accumulation and numerical implementation boundary

Unequal microbatches cannot be averaged equally. V5 accumulates local weighted means using their exact scientific/target weight mass so partitioning cannot change the intended global mean.

Even with keyed stochasticity, floating reduction order can perturb gradients near exact zero by ~1e-8 or less. AdamW can amplify a tiny sign change near zero into a visibly different first update. Consequently packed V5 is a **new numerical training implementation** and must receive its own mechanical qualification. Close objective/gradient agreement is not used to claim bitwise/statewise V4 continuation.

An inactive CPU one-update V5 harness already proves the intended chronology on frozen synthetic inputs: no sampling, deterministic support-aware packing, weighted accumulation, teacher no-grad, one AdamW step, then exact in-place EMA. Its purpose is mechanics proof only; execution/training flags remain false.

## Ragged relational support and finite triplets

A group with <3 selected cells is `RELATIONAL_NOT_ESTIMABLE` for anchored triplets but may still contribute to base JEPA. Fine-null strata with <2 cells become `NULL_NOT_ESTIMABLE`; no implicit cross-stratum fallback is invented.

Exhaustive full-group triplets are prohibited: a median n=228 group has 5,848,428 anchored relations; n=42,209 exceeds 37 trillion. The finite sampler works by exact rank/unrank over canonical stable-cell ordering and samples unique ranks without enumerating capacity. Triplet budget has no default and controls Monte Carlo precision/compute only, not group scientific weight.

TD57B/TD59/TD60 qualification retains its exact frozen triplets/nulls and is not replaced by the production sampler.

## Exposure-aware schedule and EMA

Update count alone is not portable when update size changes. V5 therefore represents training horizon in presentations and defines the prospective EMA timescale by a half-life in presentations:

`m_update = exp(log(0.5) * presentations_this_update / half_life_presentations)`.

This makes cumulative EMA decay depend on exposure rather than arbitrary microbatch/update partition. No production presentation horizon or EMA half-life is selected here.

## Remaining gates before an external-review candidate

1. Freeze proposal `q` after presentation horizon/repeat constraints are specified prospectively.
2. Implement and cross-check a production GPU keyed-dropout kernel against exact Philox V2 reference semantics.
3. Promote the inactive mechanics into a bounded V5 qualification runtime and repeat mandatory gradient, optimizer, EMA, checkpoint/resume, replay, and attack suites under a new V5 source identity.
4. Calibrate/freeze GPU token budget independently of scientific sampling.
5. Freeze common-core/native-support view counts, visible/target dose, and block schedule from reader-fit support—not 50k locality or 3,292-cell mechanics geometry.
6. Freeze relational triplet budget/presentation policy independently of target weighting.
7. Freeze training presentation horizon and EMA half-life.
8. Build/CI/clean-room replay a self-contained V5 package and request independent external review only after all prior gates pass.

## Current authority

`training_authorized = false`

`execution_authorized = false`

`successor_u0_materialization_authorized = false`

`td60_execution_authorized = false`
