# PR #526 scientific interpretation correction after independent Macha #531 — 2026-11-03

**Class:** AUTHOR ACKNOWLEDGMENT OF INDEPENDENT SCIENTIFIC FALSIFIER. Append-only to PR #526; **no** generator, fit, world, target arithmetic, receipt, frozen threshold or random seed modified. Independent review source: [Macha PR #531](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/531) `db0b198dbd00ec13d40052324d18a8d5c3f2fdc3`, original #526 source `0e1c539a8fa5aa2f5e117b6224b535980ed728cb`, original PR328 `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`.

## Binding corrected reading of the old numerical result

Macha independently replicated frozen world hash `dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66` and fit hash `fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a`. The panel's **exact arithmetic** remains: HVS-like 0/180 calculable, SEA-AD-like 0/150, NPH52-like 149/150, one zero-denominator cell. Query-count perturbation leaves the target unchanged and software correctly distinguishes zero denominator vs structural support under the supplied fixture semantics. **That does not establish biological/source-specific measured-target support.**

The original PR328 fit source `scripts/v79/unified_synthetic_fit_view_v1.py`, Git blob `5a5fdd2862dc558683231ed4ef7946efc30c62f1`, lines 69–92, sets `vis = _tile_visibility(n_genes)` and **`support = vis > 0`**. The upstream `VISIBILITY` comes from empirical *detection fractions* among only 665 TRAIN microglia (HVS 128, NPH52 304, SEA-AD 233), not a source's measured feature-list presence. **Zero detected cells is not the same as an unassayed feature.** A gene measurable but zero observed in 128 cells becomes *structurally absent for every source-like cell* by this simulated rule. This violates the scientific distinction `MEASURED_SCALAR with count 0` vs `STRUCTURALLY_UNMEASURED`, and reverses real source geometry: HVS/SEA-AD use deposited fixed gene feature matrices while NPH52 has per-cell-type feature sets.

The observed toy panels were chosen after viewing the visibility code, with indices 1 and 8 absent for HVS-like and 7 for SEA-AD-like; hence the 0/180, 0/150 results follow directly from constants. **Do not prefer NPH52-like, disparage HVS/SEA-AD support, select source-specific target panels, or infer current human C3 estimability from PR526.** It remains a **software-mechanics observation**, and nothing more.

## Scientific decision / successor implementation rule

For every future *source-representative* observed synthetic world:
1. Define **structural measurement support** from a frozen explicit source/operator feature-universe/cell-type assay-availability table. A feature present in the measured matrix remains measured even if its count equals zero in every sampled cell. Distinguish measured zero, structural absence, collision-unresolved, and withheld rights.
2. Define **detection probability** (including rarity, acquisition propensity and program-induced positives) separately from structural support; never use `empirical_detection_fraction > 0` as evidence that a feature was assayed or `==0` as proof it was not. The PR311 detection vector may remain an observation-process parameter in that *separate* role only.
3. Use original #349/#513 source operator and feature evidence to predeclare available experimental support at the next lawful scale. If a source/operator feature table is genuinely missing, emit `NOT_ESTIMABLE` or an explicit *fixture-only unconstrained support* label, not a false biological structural mask.
4. Any change must be a **new prospectively frozen version**, with its own initial observation design and new world/fit hashes. Do not mutate or requalify frozen PR328 V2 or rerun #526 to rescue its source pattern. Follow controlling #344/#356/#379 and STOP_A/B/C and nonretuning law.
5. Independent hidden-truth evaluation must include a **wrong-query** negative control (absent across the reviewed synthetic assets), program-vs-matched perturb-null, donor-isolated evaluation, and comparators predeclared before fit. No learned test until the relevant controller and science gates authorize it; this document grants none.

**Status by claim:** `ARITHMETIC_REPLICATED__FIXTURE_MECHANICS_ACCEPT_SCOPED__SOURCE_MEASURABILITY_INTERPRETATION_WITHDRAWN__SUCCESSOR_VERSION_NOT_AUTHORIZED`. This is GPT's scientific adjudication of Macha's direct falsifier; Macha's original review remains independently immutable. Macha #531 also records open audits of #321 phase2 receipt, the V79 207-vs-291 historical nonregression rule, and wrong-query comparison; do not reorder those based on target preference.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
