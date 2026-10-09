# ETL → synthetic reconciliation audit — 2026-10-08

Status: **DECISION-CHANGING AUDIT / NON-AUTHORIZING**

## Bottom line

The project did **not** fail to characterize the real data. The ETL/calibration work captured substantial real-data structure. The main loss occurred at the handoff from those calibrated summaries into the synthetic truth generator.

The key defect is that the real calibration explicitly extracts **broad cell-class composition** and states that it is intended to make "synthetic cell identity carry realistic dominance", but the active V73/V77 synthetic truth builders do not instantiate a broad-cell-class field or condition the biological latent programs on class. The resulting latent biology is mostly keyed to cell identity and donor streams, so class composition is measured and scored post hoc rather than physically generating the covariance structure.

Therefore the next step is **not** to invent a new class-aware simulator from scratch. It is to repair the ETL→generator propagation contract, preserving what is already correctly inherited and adding only the missing class-conditioned structure.

## Evidence reviewed

- `scripts/v77/build_v77_real_calibration.py`
- `scripts/v77/build_v77_topology_calibration.py`
- `scripts/v64/build_v73_sharded_master_truth.py`
- `scripts/v64/v73_full104_population_geometry.py`
- `scripts/v77/build_v77_extended_truth.py`
- `scripts/v77/build_v77_extended_rna_observer.py`
- `docs/agent/READER_FIT_DATA_GEOMETRY_PROFILE_V1.json`
- `docs/agent/READER_FIT_OPERATOR_SEMANTICS_PROFILE_V1.json`
- `docs/agent/READER_FIT_SCIENTIFIC_ESTIMAND_ANALYSIS_V2.json`
- `docs/agent/S174_REPLAY_SUMMARY.md`
- `docs/agent/S174_SYNTHETIC_REPLAY.md`

All source paths above refer to the exact S174 working snapshot preserved under `custody/takeover_20261008/s174_working_snapshot/` in PR #237.

## Crosswalk

| Real/ETL structure | What ETL established | Synthetic incorporation | Audit classification |
|---|---|---|---|
| Source composition | FULL104 empirical source counts for SEA_AD/NPH52/HVS | Hierarchical source quotas are reproduced by the population generator | **Implemented correctly** |
| Donor population geometry | 104 donors with highly unequal cell counts | Donor identities/counts are apportioned from authenticated FULL104 donor×operator geometry | **Implemented correctly** |
| Observation operators | 42 operators with source-specific semantics and ragged support | Operator assignments and support are inherited; zero-quota rescue preserves all operators at 2K | **Implemented correctly** |
| Donor×operator support | 1,400 observed groups, highly ragged | Synthetic assignments are generated from authenticated donor×operator triplets | **Implemented correctly** |
| Operator semantics | HVS/NPH52 operators are often class-pure; SEA_AD operators are multi-class; operator is not a universal scientific class axis | Operator is used as measurement/support identity, not falsely promoted to a cross-source cell-class axis | **Implemented correctly / appropriate restraint** |
| Measurement availability | Per-operator structural availability and support differ strongly | RNA observer computes gene availability from frozen operator model weighted by realised operator counts | **Implemented correctly** |
| Library depth / detection geometry | Real per-cell depth and detection are explicitly calibrated | Frozen World-A observer supplies empirical depth/support targets and exact-count realisation; later arms vary counting/dynamic range | **Implemented, but still mismatched in replayed arms** |
| Per-gene abundance | Real gene abundance distribution measured from TRAIN | Real calibration intended these as priors/targets; observer calibration includes abundance diagnostics | **Implemented as calibration/observer target, not fully matched** |
| Per-gene detection | Real gene detection rates measured from TRAIN | Used in calibration and observer design | **Implemented as calibration/observer target, not fully matched** |
| Global expression covariance shape | Median |r|, strong-pair fractions and eigenspectrum measured | Used as calibration targets; synthetic background was adjusted/tested against them | **Implemented as target** |
| Local correlation topology | Degree, communities, transitivity, substitutes | Explicit T1–T4 diagnostic/qualification targets | **Implemented as target** |
| Broad cell-class composition | `broad_cell_class` is present in TRAIN metadata; class counts are extracted. Real calibration explicitly says this should make synthetic cell identity carry realistic dominance | No `broad_cell_class` appears in V73 master truth. V77 extensions add generic states, donor factors, pseudotime, etc., but these are not conditioned on real broad class | **MISSING FROM GENERATIVE TRUTH — primary gap** |
| Class-conditioned correlation structure | T5 measures within-class vs pooled correlation and corrected real T5 is ~0.7435 | T5 is computed as a guard after generation; replayed arms remain ~1.02–1.21. Current substates are independent of annotated class | **Measured but not generated — primary gap** |
| Donor biology | Donor identity and donor imbalance are known | V77 B2 adds 3 generic donor-level biological factors keyed by donor | **Implemented generically, not empirically coupled to class** |
| Donor×class biology | ETL contains donor and broad class simultaneously; operator semantics show class/source relationships are nontrivial | No explicit donor×class biological program in current truth | **Missing / not propagated** |
| Source/cohort biology | Source identity and coverage are explicit | Source/operator geometry is generated. Corrected S149 shows coverage alone explains only ~3% of strong pooled detection dependence | **Geometry implemented; source coverage is not the missing biology** |
| Measurement×biology coupling | ETL established that observation process matters; V77 contains explicit tests of recoverability and C3 biology×operator coupling | C3 can create measurement dependence on a generic latent biological state | **Mechanism exists, but not tied to real class structure** |
| Regulatory/SCENIC-like structure | Project has prior regulatory/SCENIC+ work and real regulatory evidence | V77 D1/D3 uses a deliberately synthetic regulatory graph / random program content to avoid leakage | **Deliberate non-import of biological content; geometry-level use still needs separate review** |
| Disease/pathology effects | ETL project contains pathology work elsewhere | V77 real calibration is explicitly pathology-blind TRAIN-only | **Intentionally excluded in this lane, not an omission** |
| Sampling estimand | Reader-fit audit evaluates cell-uniform, donor-uniform, source-donor-uniform, source-uniform proposals and selects none | Synthetic population geometry reproduces the reader-fit population, but no production estimand is selected | **Correctly unresolved; do not smuggle into generator** |

## Decision-changing finding

`build_v77_real_calibration.py` says the calibration extracts:

- per-gene abundance,
- per-gene detection,
- gene-gene correlation shape,
- eigenspectrum,
- **cell-class composition**,

and explicitly lists cell-class composition as being used so that **synthetic cell identity carries realistic dominance**.

However, `build_v73_sharded_master_truth.py` writes only:

- cell identity,
- donor,
- source,
- operator,
- generic `z_global`, `z_query`, `z_reg_shared`, `z_reg_private`,
- technical latents.

`build_v77_extended_truth.py` adds B1–E2 components, but B1 state, B3 rare flags, B4 pseudotime, B5/B6 programs, C states and regulatory factors are generated from independent cell-identity streams (or donor for B2), not from a broad-cell-class variable.

So the calibration requirement exists, but there is no physical generative path that realizes it. T5 therefore became a **post-hoc guard against a structure the generator was never actually equipped to reproduce**.

This explains why the corrected replay shows every arm with T5 around 1.02–1.21 while real is ~0.7435: the arm family can change covariance strength and counting, but it lacks a mechanism that makes broad class contribute to pooled covariance while retaining within-class covariance.

## What the audit says NOT to change

Do **not** rebuild the following from scratch:

- FULL104 source/donor/operator geometry;
- 42-operator support rescue;
- donor×operator population apportionment;
- operator-specific structural availability;
- the existing measurement/counting observer for the first class-propagation experiment;
- q-safety/runtime machinery;
- corrected S174 real-data references;
- 353 gene-ID mappings;
- production estimand selection.

These are either already correctly represented or intentionally governed separately.

## Correct next action

Before inventing any new synthetic biological architecture, create a **prospective ETL→synthetic propagation contract** with the minimum new authority:

1. carry `broad_cell_class` into synthetic truth as an explicit variable;
2. reproduce the corrected TRAIN class composition using only pathology-blind TRAIN metadata;
3. define class-shared **random-content** program loadings — preserve the prior rule "real geometry, random content" so no real gene program is planted;
4. retain within-class continuous/state variation so T5 cannot be fixed by making classes deterministic blocks;
5. preserve donor identity and test a donor×class interaction as a separate ablation, not bundled into the first arm;
6. hold the observation/counting model fixed for the first comparison;
7. score the same corrected invariants together: expression geometry, detection topology, T5, abundance and depth;
8. do not use S159 bootstrap intervals as binary qualification gates until S159 is repaired;
9. do not tune an effect magnitude to make T5 equal 0.7435. Use preregistered small mechanistic arms and ask whether the real point is bracketed jointly across multiple invariants.

## Proposed minimal experiment family

- **E0 — existing generator:** unchanged control.
- **E1 — class composition only:** explicit broad class assignment with no class-dependent expression program. This isolates whether labels/composition alone alter anything (they should not materially alter expression if no program is attached).
- **E2 — class-shared program:** broad class drives randomly placed class-specific expression programs; within-class generic latents remain unchanged.
- **E3 — class-shared + within-class continuous biology:** E2 plus continuous within-class state.
- **E4 — class-shared + donor×class interaction:** separate final ablation if E2/E3 show that class propagation matters.

The first useful result is not "which arm wins". It is whether adding the missing ETL-derived class structure moves **T5 and the other corrected invariants in the expected joint direction without breaking the already-correct population/measurement geometry**.

## Governance

This audit creates **no training authority**, **no mutation authority**, and **no real-data training authorization**. It supersedes the prior wording that the next step was simply to invent a class-aware synthetic model. The next step is specifically an ETL→generator propagation repair with a prospective contract and ablations.
