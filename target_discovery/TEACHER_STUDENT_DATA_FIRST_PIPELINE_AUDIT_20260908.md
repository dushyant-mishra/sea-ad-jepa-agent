# Teacher/Student data-first pipeline audit — 2026-09-08

Status: DATA_FIRST_DESIGN_AUDIT__NO_TRAINING_AUTHORITY

This audit applies the principle: **compile the pipeline from the dataset and the scientific unit, rather than forcing the dataset through historical mechanics constants.**

It does not modify the frozen Teacher/Student V4 review package or authorize training.

## Data facts that must shape the successor

Reader-fit population:
- donors: 104
- cells: 4,553,407
- operators: 42
- addresses: 41,238

Reader-fit cells by source:
- HVS: 198,718 (4.364%)
- NPH52: 236,476 (5.193%)
- SEA_AD: 4,118,213 (90.442%)

Reader-fit donor counts represented by the frozen fit inventory:
- HVS: 41
- NPH52: 17
- SEA_AD: 46

Per-donor cell count:
- min 81
- median 14,749
- max 174,111
- max/min ratio ~2,149x

Measurement support:
- HVS operators: 18,736 measured scalar addresses (45.434%)
- NPH52 operators: 30,294..34,405 (73.461%..83.430%)
- SEA_AD operators: 35,076 (85.058%)
- addresses measured by all 42 operators: 17,186
- addresses measured in all three source families: 17,346
- addresses measurable by at least one operator: 40,949
- unobserved/collision-only across all operators: 289

Historical small-corpus mechanics:
- T1 fit inventory: 3,292 cells / 104 donors
- historical schedule: 26,240 presentations through u205
- 26,240 / 4,553,407 = 0.5763% of one full reader-fit pass
- at effective batch 128, one full reader-fit pass is ~35,574 updates
- u40 exposes only 5,120 presentations = 0.1124% of the full reader-fit cells

Therefore u40 and u205 are valid historical/mechanics clocks but cannot automatically serve as biological-learning or full-training clocks for the 4.55M-cell corpus.

## Shortcut evidence already present in the calibration bundle

The frozen teacher-shortcut atlas shows that technical/support identity is extremely recoverable from historical representations:
- rich_CELL source balanced accuracy = 1.0 at u0 and u205
- rich_CELL support_measured_count R2 ~0.9995
- rich_H source balanced accuracy = 1.0
- H address/operator decomposition explains >99.9% of rich_H variance, leaving very small residual cell-varying variance

This does not by itself invalidate the representation, but it proves that measurement footprint/source is an easy shortcut and must be treated as a first-class design constraint rather than left implicit.

## What V4 already gets right

Preserve:
- global 41,238-address identity authority
- structural-unmeasured versus measured-zero distinction
- scale-free anchored relational target
- no production locality/k/loss-weight defaults from the 50k pilot
- teacher gradient isolation and fail-closed mechanics
- exact source/checkpoint/RNG authority
- population/pathology firewalls
- per-group collapse adjudication with no pooled rescue

## Data-shaped successor changes

### 1. Census -> compiler -> runtime

Do not hard-code a production schedule and then reject the data.

Create a metadata/support-only full-reader census authority that compiles:
- donor counts
- donor x operator/support-stratum counts
- source/operator counts
- measurement-support hashes
- measured-address counts
- address-recurrence classes
- library/detected-gene/support distributions when lawfully available
- GPU token-budget estimates

The runtime should validate the compiled authority, not duplicate dataset assumptions as constants.

### 2. Separate mechanical time from data-exposure time

Keep a bounded mechanical qualification (for example the historical 40-update style gate) only for optimizer/AMP/EMA/checkpoint health.

Do not use fixed u40 as the learned-biology checkpoint and do not call u205 full training on the full corpus.

Define outcome-blind scientific checkpoints from data exposure/coverage, for example a frozen coverage milestone based on donor/operator/support participation or reader-fit passes. Exact milestones must be prospectively compiled before biology is opened.

### 3. Replace the 3,292-cell training schedule with a full-reader schedule compiler

The 3,292-cell cap-8 schedule remains historical/mechanics evidence.

The production scheduler must operate on all 4,553,407 eligible reader-fit cells and explicitly control the extreme imbalance:
- 90.4% of cells are SEA_AD
- donor volumes vary >2,000x
- source donor counts are much less imbalanced than source cell counts

The scientific unit is donor recurrence. Therefore cell-uniform sampling must not be the silent default. A prospective scheduling objective should specify donor/source/operator coverage and replay limits, then solve quotas from the actual counts.

### 4. Make evidence/masking support-aware

A universal 40% of measured genes is not a universal information dose:
- HVS hides ~7.5k measured addresses
- SEA_AD hides ~14.0k
- the fraction of the universal 17,186-address core among measured genes is ~91.7% in HVS but ~49.0% in SEA_AD

Use the address-recurrence atlas to define target strata such as:
- pan-operator recurrent core
- cross-source recurrent addresses
- operator/source-specific extras

Compile a target mixture from the full support census. Do not let uniform masking make each source solve a different semantic task accidentally.

A strong data-shaped view is support perturbation: for richer operators, hide lawful measured genes to emulate poorer/intersection support patterns. This creates same-cell measurement-footprint perturbations without inventing unmeasured values.

### 5. Make relational batching variable-group and donor-normalized

Current V4 relational mechanics require externally supplied equal donor x operator groups and the raw loss averages all triplets.

For full-reader use:
- support variable group sizes
- deterministic bounded triplet sampling rather than complete O(n^3) enumeration
- normalize contribution per group/donor, not by raw triplet count
- compile triplet budget from full-data group counts and compute budget
- consider grouping by donor x validated measurement-process/support stratum rather than raw file/operator name when the data prove operators are equivalent

No K/group size should be inherited from the pilot.

### 6. Pack measured tokens instead of processing structural-unmeasured tokens

Current runtime constructs all 41,238 gene IDs for every cell even when an operator structurally measures far fewer addresses.

A production successor should preserve global address IDs but pack only the operator's measured addresses (measured zeros remain meaningful and must remain represented). Grouping batches by support mask can make this efficient and deterministic.

This is a direct data-shaped optimization:
- HVS need not process 22,502 structurally unmeasured positions per cell
- SEA_AD need not process 6,162 structurally unmeasured positions per cell

### 7. Express optimizer/EMA timescales in data-exposure units

Fixed per-update LR/weight-decay/EMA values inherited from a 205-update regime change meaning radically at ~35,574 updates per full-data pass.

Example:
- EMA momentum 0.996 has a half-life of ~173 updates, ~22,136 presentations at batch 128, only ~0.486% of the full reader-fit corpus.
- AdamW lr=1e-4 and weight_decay=0.01 gives a direct decay multiplier of ~0.999795 across 205 steps but ~0.965 across 35,574 steps, before considering gradient-driven changes.

Future authority should define desired timescales in cells/passes/coverage units and derive per-update parameters from the compiled schedule.

## Recommended governance consequence

Do not discard V4. Keep it immutable as the mechanically reviewed kernel and relational-target reference.

However, do not treat V4 + the historical 3,292-cell/u205 base contract as the final full-reader training pipeline.

Before asking an external reviewer to bless the final production design, build a data-first successor authority that binds:
1. full-reader census,
2. full-reader schedule compiler,
3. support-aware masking/target policy,
4. data-exposure clock,
5. variable-group relational sampler,
6. packed measured-token execution plan,
7. schedule-derived optimizer/EMA timescale policy.

The V4 package may still be independently reviewed as a mechanics kernel, but a PASS must not be interpreted as review of the eventual full-reader training design.

Terminal:
DATA_FIRST_AUDIT_COMPLETE__V4_MECHANICS_PRESERVED__FULL_READER_SUCCESSOR_REQUIRED__NO_TRAINING_AUTHORITY
