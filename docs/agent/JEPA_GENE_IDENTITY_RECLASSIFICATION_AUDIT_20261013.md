# JEPA historical evidence reclassification after the gene-identity recovery

**Date:** 2026-10-13  
**Status:** historical evidence-quality audit; no new biological authority

## Why this exists

Several historical JEPA/target/teacher/student results were generated before the later authoritative gene-identity recovery. A future agent must not either:

1. ignore the later identity problem and use every old cross-source result as clean biological evidence; or
2. overreact and invalidate every old experiment, including source-native and semantics-free mechanics results that were never affected by the NPH identity ambiguity.

This audit defines the safe middle ground.

---

# What the later recovery established

Stage81A2R reconstructed authoritative gene identity across the heterogeneous source matrices and closed protected identity cases using source rowData, historical/current Ensembl/HGNC evidence and frozen-vocabulary provenance.

The current terminal accounting included an **identifier-poor remainder concentrated in NPH52** (2,009 NPH52 identities in the later closeout logic), while the corresponding terminal identifier-poor class was not present for SEA-AD/HVS. This is why NPH/cross-source pre-repair gene-semantic experiments need special handling rather than blanket reuse.

Relevant recovery/materialization code:

- `scripts/v4/stage81a2r_authoritative_gene_identity_recovery.py`
- `scripts/v4/stage81a2r_finalize_authoritative_mapping.py`
- `scripts/v4/stage81a2r_close_authoritative_identity_audit.py`
- `scripts/v4/foundation_materialize_nph_discovery_sample.R`

The repaired NPH discovery materializer uses the recovered mapping explicitly:

`source_feature_index -> molecular_address_index`

before constructing a sparse matrix with exactly 41,238 molecular-address columns. That repaired address registry is the relevant basis for the later 41K discovery/calibration assets.

Protected-identity review also showed why simple symbol matching is unsafe: some cases were exact aliases supporting the frozen biological gene, some were historical-ID ambiguities, and some were source-symbol / exact-Ensembl conflicts that could not justify silently rewriting the frozen identity.

---

# Evidence classes

## 1. `SOURCE_NATIVE_SAFE`

Use for historical experiments that stayed within a source-native dataset whose relevant feature identities were not part of the later NPH identifier-poor remainder.

Examples:

- SEA-AD MTG/DLPFC Stage64/68/69/70/71 rare-state and graph experiments.

**Rule:** preserve the original result and its original limitations. Do not upgrade it, but do not invalidate it because NPH later required identity repair.

## 2. `FROZEN_4K_IDENTITY_AUDITED`

Use for experiments based on the frozen 4,096 canonical Ensembl vocabulary whose protected identity cases were later reviewed in Stage81A2R.

Examples:

- hidden-gene anchor causal history;
- T0/T1/TCTX lineage;
- V6 mechanics and residual target work;
- core/halo and tier-hiding conclusions.

**Rule:** their original scientific conclusions remain subject to their original limitations and later supersession, not automatically invalidated by the 41K/NPH repair.

## 3. `REPAIRED_41K_ADDRESS_BOUND`

Use only when the result can be bound to the repaired 41,238 molecular-address namespace/materialization.

Examples:

- the August-24 41K discovery/calibration corpus used by the V44 proxy tournament;
- current PR #322 non-authorizing smoke probes;
- the local 50k x 41,238 discovery matrix and program-weight NPZ after explicit address-order verification.

**Rule:** these are acceptable for their stated exploratory/non-authorizing scope. This does not make historical pilot data production FULL104 authority.

## 4. `SEMANTICS_FREE_MECHANICS`

Use for experiments that test optimizer/AMP/EMA/checkpoint/custody behavior rather than gene biological meaning.

Examples:

- fixed and scheduled EMA lag/responsiveness sweeps;
- presentation-normalized EMA mechanics;
- historical T1 optimizer-moment/autocast defect;
- checkpoint/restart and GradScaler/EMA chronology tests;
- two-phase blind custody tests.

**Rule:** gene-ID scrambling does not invalidate these mechanics conclusions.

## 5. `GENE_IDENTITY_PROVENANCE_UNRESOLVED`

Use when an old biological conclusion depends on pre-repair per-gene semantics across NPH/cross-source data and cannot be bound to the repaired registry.

Example currently identified:

- old numerical preference for 2/4/8 teacher views. The decision registry already classified this result as provisional. Its old optimum should not be inherited.

**Rule:** this evidence cannot be `ACTIVE` biological architecture authority. If the question remains material, replay prospectively on repaired/bound FOUNDATION TRAIN; otherwise leave it historical.

---

# Reclassification of important historical lineages

| Lineage | Identity class | Current evidence status |
|---|---|---|
| Hidden-gene/CELL anchor | `FROZEN_4K_IDENTITY_AUDITED` | rejection stands |
| Core-only vs complementary halo | `FROZEN_4K_IDENTITY_AUDITED` | core-only insufficiency stands |
| Tier hiding/cascade | `FROZEN_4K_IDENTITY_AUDITED` | rejection stands |
| T0/T1/TCTX | `FROZEN_4K_IDENTITY_AUDITED` | no target winner; remains closed |
| V6R5B residual target | `FROZEN_4K_IDENTITY_AUDITED` | `RESIDUAL_TARGET_DOES_NOT_RESCUE` stands |
| Historical PROD41K T1 optimizer result | `SEMANTICS_FREE_MECHANICS` | defective-training conclusion stands |
| Stage69/70 rare auxiliary | `SOURCE_NATIVE_SAFE` | internal signal but no benchmark lock; negative prior only |
| Stage71 graph auxiliary | `SOURCE_NATIVE_SAFE` | randomized graph control beat real graph; negative prior only |
| V43 architecture proposal | `NOT_GENE_SEMANTIC` | design reference only |
| V44 original-RNA proxy | `REPAIRED_41K_ADDRESS_BOUND` | shared multi-head positive prior; no neural winner |
| EMA fixed/scheduled sweeps | `SEMANTICS_FREE_MECHANICS` | mechanics history valid; no production beta selected |
| presentation-normalized EMA | `SEMANTICS_FREE_MECHANICS` | retain as native runtime abstraction |
| old teacher-view-count optimum | `GENE_IDENTITY_PROVENANCE_UNRESOLVED` | replay required only if still material |
| PR #322 41K smoke tests | `REPAIRED_41K_ADDRESS_BOUND` | non-authorizing smoke evidence only |

---

# Local repaired-41K identity check performed in this lane

The uploaded 41K expression split and calibration bundle were inspected read-only during the PR #322 audit. The expression NPZ itself contains a sparse 50,000 x 41,238 matrix but no embedded gene labels; therefore column semantics are external and **must** be bound to the molecular-address registry.

The program-weight NPZ's 41,238 `molecular_address_id` order was checked against the calibration bundle registry and matched exactly. The repaired corpus is therefore acceptable for non-authorizing smoke probes. Older matrices lacking that exact address-order binding remain excluded from gene-semantic smoke work.

This check is deliberately weaker than production FULL104 authority: it establishes safe pilot feature identity, not production corpus representativeness.

---

# Rules for future agents

Before citing a historical biological architecture result:

1. identify its input substrate;
2. identify whether it needs gene semantics or only numeric/mechanics behavior;
3. assign one of the evidence classes above;
4. check later supersession independent of identity quality;
5. never promote an unresolved identity result into an active tournament arm simply because the result was historically interesting.

A result can be **identity-safe and still scientifically negative**. Stage70/71 are examples.

A result can be **mechanically valid and still non-authorizing**. EMA sweeps are examples.

A result can be **identity-bound and still only exploratory**. V44 and PR #322 smoke probes are examples.

A result can be **historically interesting but currently unusable** because identity provenance is unresolved. The old teacher-view optimum is the current example.

---

# Authority boundary

This audit does not reopen historical targets, select an architecture, authorize any real TD execution, open controller truth, select TD60, authorize Stage4 or authorize JEPA training.
