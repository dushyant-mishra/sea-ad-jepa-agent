# V5 FULL104 dataset issues -> target-design safeguards

Date: 2026-09-15
Status: `ACTIVE_DESIGN_AUDIT_NOT_FROZEN`

Purpose: make every known FULL104 irregularity explicit in the target design so that no dataset artifact is silently converted into biological target semantics.

This document creates no training authority.

`TRAINING_OFF` · `NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

## Governing principle

The design order is:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`

The target must describe an estimable scientific object on the authenticated FULL104 substrate. The model is not allowed to redefine the data problem by imputing away support differences, treating cohort labels as pure nuisance, or inheriting historical numerical geometry.

## Issue matrix

| Dataset issue observed in FULL104 | Risk to target design | Current design response | Status |
|---|---|---|---|
| Source/operator support is heterogeneous; not every molecular address is measured everywhere | Missingness can be mistaken for zero expression or biological absence; target difficulty can vary only because support varies | Keep explicit measurement support. Native support and comparable/common-core support are separate authorities. Never create a target outside measured support. Packing removes invalid tokens while retaining canonical gene IDs. | Mechanic exists; exact production support policy not yet frozen |
| 17,186-address common core is much smaller than the 41,238-address ledger | Forcing the whole 41K universe into a cross-source target can make technology-specific support the task | Use the common core for cross-source comparability/qualification where required; retain native/operator-specific support as evidence rather than pretending it is universally comparable. Do not let comparable support silently become the entire biological state. | Role separation exists; exact target role still open |
| The declared source library extends beyond the stored 41K ledger, with source-dependent outside-ledger fraction | Using the stored 41K count sum as the library denominator produces source-dependent normalization error | Bind normalization to the declared full source library where the historical/source contract requires it. The 41K ledger is not treated as the complete source library denominator. | Permanent data fact; carryover firewall required |
| Visibility channels are extremely predictive of Q_DEPTH/Q_DETECT | A target containing visibility can reward measurement state rather than molecular state | Current primary molecular candidate is VALUE_ONLY. Visibility is relegated to observation/QC control unless a future authority explicitly widens its role. Observation objectives are gradient-firewalled from z_bio. | Strong evidence; primary representation not yet formally frozen |
| Measurement depth/detection realization changes the same cell | Teacher/student can win by matching shared measurement state instead of molecular structure | Same-cell thinning intervention directly tested this. At the tested linear class, matched measurement state did not help and excess synergy was ~0-1% of full-depth cross-view R2. Therefore no default measurement-decorrelated target is introduced. Keep measurement robustness as a qualification gate. | `MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`; deep-model gate still required |
| Source/operator labels are strongly predictive but are confounded with cohort, tissue/region, donor composition, disease, platform and real biology | Treating source/operator as pure technical nuisance could erase biology; treating them as biology could reward shortcuts | Do not residualize source/operator from raw molecular input/target by default. Do not impose adversarial invariance. Characterize context explicitly. Residual-over-context remains an optional credit-assignment mechanism only if final objective-aligned qualification shows it is needed. | Context characterized; handling not frozen |
| Reconnaissance sampling over-represented HVS/NPH52 relative to FULL104 population | Apparent context dominance and molecular increment depend on sampling distribution | Keep scientific estimand separate from proposal/sample. Report empirical/FULL104, source-uniform and donor-primary/operator-balanced views separately. Training runtime must consume externally frozen scientific weights. | Estimand sensitivity demonstrated; production estimand not frozen |
| SEA_AD dominates cell count while HVS/NPH52 are much smaller | Pure empirical cell-uniform optimization can let SEA_AD dominate; pure source-uniform optimization answers a different scientific question | Target mass p, proposal q and compute packing are distinct authorities. Importance weighting and exposure constraints exist as algebraic mechanisms. No target mixture is selected from downstream representation quality. | Mechanisms exist; target estimand remains open |
| Donor-generalizable linear cross-view signal is strong in SEA_AD but weak in HVS/NPH52 at the tested class | A single pooled target can look successful while failing to transport within smaller/cohort-heavy sources | Require source-specific and donor-held-out reporting/gates. Do not translate HVS/NPH52 linear non-demonstration into absence. Do not force source invariance merely to equalize the result. | Characterized; explanation remains open |
| Within-donor molecular-view signal exists in all three sources but measured QC does not explain most of it | Temptation to call the unexplained remainder “biology” | Use the neutral label `PREDICTIVE_INFORMATION_BEYOND_MEASURED_QC`. Unmeasured technical state remains a live alternative. Target authority cannot rely on the claim that unexplained == biological. | Permanent interpretation rule |
| Random masking can leave highly correlated molecular partners visible | JEPA can solve hidden targets by local interpolation instead of learning broader cell state | Masking is a separate authority. Compare uniform, historical graph-expanded and recurrent/consensus dependency-aware hybrid masks under outcome-blind exposure/coverage metrics. Avoid pooled FULL104 covariance as automatic biological graph authority. | `MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED` |
| Target gene/address identity is stable and current inherited predictor uses the online trainable identity table for hidden target queries | Predictor/teacher can co-adapt through address identity; identity-only prediction may reduce loss without cell-specific molecular evidence | Target-address conditioning is now a separate authority. Leading candidate is a fixed/separate replay-stable address representation plus an identity-only shortcut audit. Do not remove target identity entirely unless evidence shows the teacher target itself is identity-dominated. | `TARGET_IDENTITY_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED` |
| Observation/reconstruction losses are themselves measurement-bearing | Auxiliary reconstruction can write technology/depth identity into the same state intended for biology | `BiologyObservationAdapterV2` detaches z_bio before observation conditioning/reconstruction, so observation-route gradients cannot train the biology path. Same-cell intervention and held-out biology qualification remain mandatory. | Reusable mechanic; dimensions/loss weights not frozen |
| Rare/common addresses and variable measured counts create unequal masking difficulty | A fixed fraction/block count can create very different evidence doses and starve rare addresses | V5 support geometry expresses evidence in absolute measured/visible counts and derives block geometry from support. Future masking authority must report rare-address coverage and mask-budget concentration. Historical 40%/16 blocks are forbidden defaults. | Mechanics exist; production evidence dose not frozen |
| Historical rank/width values (5, 96, 160, 224, 320, 512...) came from earlier studies | Old geometry can masquerade as biological dimensional authority | No historical width/rank is V5 authority. D_shared -> D_private -> D_obs chain remains the dimension authority path. Real D_shared stays sealed until the prospective design is frozen. | `D_shared` sealed; geometry open |
| Hardware-efficient dense batches historically assumed [128, 41238] | Compute convenience can silently redefine which cells/genes contribute and with what weight | Current V5 packing is downstream of frozen scientific selection/support. Operator-homogeneous/ragged packing must preserve cells, masks and scientific weights exactly. Hardware token budget is a separate authority. | Data-first packing mechanics exist |
| Historical EMA=.996 and optimizer-step schedule tied teacher dynamics to update geometry | Changing batch/packing alters effective teacher half-life | Preserve EMA mechanics but bind timescale in scientific presentation units: `m_u = exp(log(0.5) * p_u / H)`. No historical EMA scalar is V5 authority. | Timescale not yet frozen |
| Historical V4 runtime/preexecution code contains fixed 6-block/48-tensor/128x8 assumptions | Even a valid new target receipt could accidentally re-enter an old architecture | Carryover firewall: current-V5 runtime must consume explicit V5 authorities; do not simply unlock V4 `production_update`; replace V2 preexecution geometry assumptions with current-registry-derived validation. | Active carryover repair item |

## What this means for the target itself

The intended V5 target is therefore **not** “the normalized expression vector” and not “whatever the EMA teacher currently emits.” It must satisfy all of the following before it can be frozen:

1. **Support-valid** — every target component is estimable on the cell/support where it is used.
2. **Molecular-first** — measurement/visibility state cannot dominate the biological target path merely because it is easy to predict.
3. **Context-aware but not context-erasing** — source/operator structure is acknowledged, measured and gated without pretending it is purely technical.
4. **Estimand-explicit** — the target population and scientific weights are declared independently of the proposal sampler and hardware packing.
5. **Donor/source stress-tested** — transport is evaluated by source and held-out donor instead of inferred from pooled fit.
6. **Shortcut-resistant** — measurement-state, context, correlated-gene interpolation and target-identity shortcut families are separately qualified.
7. **Observation-separated** — measurement reconstruction may condition on biology but cannot write its gradients back into the biological state.
8. **Geometry-not-inherited** — rank, width, masking dose, block count, schedule, optimizer and EMA timescale are supplied by current V5 authority rather than historical defaults.
9. **Protected-outcome independent** — D_shared/protected confirmation cannot be used to tune the target after the fact.

## Current design direction

The most defensible current direction is:

- use VALUE_ONLY molecular evidence for the primary biology path;
- retain explicit measurement support rather than impute missing addresses as biology;
- use comparable/common-core evidence where cross-source teacher comparison requires it, while preserving native-support information separately;
- maintain a separate gradient-firewalled observation state for measurement-bearing information;
- keep context handling as qualification-first rather than hard-coded residualization;
- decouple target-address conditioning from the online trainable gene-identity table unless the shared version prospectively clears the identity audit;
- freeze dependency-aware masking independently;
- freeze the scientific estimand/weights independently;
- only after these are fixed, bind the EMA teacher target semantics and production geometry.

## Remaining target-design questions

The major unresolved questions are now narrower:

1. What exact teacher state is the target: final gene state, block mean, cell state, or another current-V5-defined object?
2. Which support family is authoritative for which target component: common-core only, native support, or an explicit multi-part target?
3. Which scientific estimand is primary for base learning?
4. What fixed/separate target-address representation clears the identity shortcut gate without imposing arbitrary geometry?
5. What dependency-aware mask construction removes local interpolation without encoding pooled cohort structure?
6. What prospective shortcut-superiority margins must be met before production training is legal?
7. What rank/model geometry is authorized after D_shared/D_private/D_obs qualification?

Until these are frozen, the correct state remains:

`TARGET_DESIGN_DATASET_DRIVEN_BUT_NOT_YET_FROZEN`

`TRAINING_OFF`
