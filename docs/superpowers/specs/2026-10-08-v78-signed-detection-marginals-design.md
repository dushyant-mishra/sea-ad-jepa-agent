# V78 synthetic signed-detection + count-marginal repair design

Status: **PROSPECTIVE DESIGN / NON-AUTHORIZING / NO IMPLEMENTATION YET**  
Date: 2026-10-08  
Base implementation head: `f3a5d142d3e02b0650d6f52ef97a11232e0a4dc7`  
Design branch: `design/v78-signed-detection-marginals-20261008`

## 1. Purpose

Follow the completed E0–E3 class-propagation tournament without retuning any observed arm.

The prior experiment established two facts simultaneously:

1. explicit broad cell class is biologically relevant to the synthetic generator because E2 moved corrected T5 from `1.05047` to `0.91418` toward the corrected real descriptive point `0.7435`;
2. the E0–E3 family is not adequate because E2 worsened detection topology, abundance, depth and several expression statistics, while E3 moved T5 in the wrong direction.

The next experiment therefore asks:

> Can the already-supported broad-class hierarchy be retained while signed detection topology and count marginals are repaired as distinct mechanisms rather than by increasing one latent-expression scale?

This design does not authorize JEPA training, runtime/EMA/checkpoint changes, target-discovery changes, 353-ID remapping, TEST/Morabito access, 500K, Stage 4, E4 donor×class, production target/representation/EMA selection, or post-outcome parameter tuning.

## 2. Evidence motivating the decomposition

At the completed 2,500-cell tournament:

| metric | corrected real | E0 | E2 |
|---|---:|---:|---:|
| detection median |r| | 0.19456 | 0.18239 | 0.17010 |
| detection frac |r| > .3 | 0.13483 | 0.12779 | 0.09770 |
| detection mean degree | 404.36 | 383.24 | 293.01 |
| detection transitivity | 0.66724 | 0.47948 | 0.40938 |
| detection positive/negative high-correlation ratio | ~59 | ~1859 | ~1800 |
| abundance max/median nonzero | 2273.21 | 594.75 | 501.14 |
| median detected genes/cell | 4495.5 | 3300.5 | 3276.0 |
| T5 within / pooled | 0.7435 | 1.05047 | 0.91418 |

Several unsigned detection summaries are already near the real reference under E0, while transitivity, signed edge structure, abundance dynamic range and detected-gene depth remain badly wrong. Historical dynamic-range arms showed that increasing a shared latent-expression scale can raise graph density/transitivity but damages abundance/depth and still yields almost no strong negative detection correlations.

Therefore the next repair must separate:

- biological expression hierarchy;
- which supported genes are detected in a cell;
- how many counts detected genes receive.

## 3. Existing mechanics that constrain the design

The canonical full-scale observer currently does the following:

1. `build_eta(...)` creates log relative expression from registry abundance, background covariance and biological components;
2. `rel = exp(eta)`;
3. structural support is applied;
4. gene-specific detectability scales `rel`;
5. `depth_targets(...)` chooses per-cell library and detected-feature targets from measurement/QC geometry;
6. `sparse_counts(...)` uses `log(rel) + Gumbel noise` to choose exactly `det[i]` supported genes, then allocates the remaining library counts proportionally to `rel` among those selected genes.

This means one `rel` field currently controls both gene-selection topology and positive-count abundance. The V78 experiment will separate those roles prospectively.

## 4. Design principles

1. **Preserve the demonstrated broad-class mechanism.** E2 is the biological baseline. Its class scale stays exactly `0.55`; no tuning is allowed.
2. **One mechanism per causal step.** Detection selection and positive-count allocation become separately inspectable surfaces.
3. **Real geometry, random content.** Real pathology-blind TRAIN distributions may define geometry. Real gene identities, marker memberships, regulatory edges, pathology labels or target-discovery programs may not be planted.
4. **Do not fit the evaluation universe.** New marginal authorities must be derived from corrected full-registry TRAIN data, not tuned specifically to the 14,417-address scoring subset.
5. **Signed topology must be explicit.** `|r|` alone is insufficient; positive and negative high-correlation structure must be scored separately.
6. **Measurement semantics stay measurement semantics.** Source/operator may govern real measurement marginals, but they may not define synthetic biological or signed-module membership.
7. **No post-outcome magnitude search.** Every scale and family definition is frozen before F0–F3 outcomes are read.

## 5. F0–F3 family

### F0 — exact E2 reproduction control

F0 is the completed E2 arm reproduced under the same frozen conditions:

- World-B `B1–B6`;
- explicit broad-class program at scale `0.55`;
- background `v1`;
- generator seed `7302`;
- measurement seed `7302`;
- exact canonical registry and corrected evaluation-universe custody;
- existing full-scale observer/counting mechanics.

Requirement: the complete matched-score object must reproduce committed E2 within exact deterministic equality where the existing implementation is deterministic. If F0 does not reproduce E2, stop before scientific interpretation.

### F1 — E2 + existing BackgroundV2 ablation

F1 changes only the background covariance selection from `v1` to the existing `BackgroundV2` implementation already in the repository.

No `BackgroundV2` parameter is changed. Its existing broad/mid/narrow/paralog configuration is inherited as-is. E2 class scale remains `0.55`.

Purpose: test whether the pre-existing hierarchical expression-covariance successor can repair topology around the class-aware world without introducing the new detection mechanism.

F1 is an ablation, not the preferred final mechanism. If it improves topology only by worsening abundance/depth/sign structure, it is rejected under the same multi-axis rule used previously.

### F2 — E2 + separate signed detection-propensity field

F2 returns to background `v1` and adds a new detection-only latent field. It does **not** alter `eta`, `rel`, structural support, per-cell `lib` targets, or per-cell `det` targets.

#### F2 data flow

Current selection score:

`selection_score = log(rel) + gumbel_noise`

F2 selection score:

`selection_score = log(rel) + signed_detection_field + gumbel_noise`

Positive-count allocation remains based on the original `rel` among selected genes. Therefore F2 can alter which genes are detected together without directly changing the positive-count weighting model.

#### F2 signed field

The field is a sum of independent cell-level factors:

`D = Z_det @ W_det`

where:

- `Z_det` is generated from new disjoint stateless RNG streams keyed only by global cell identity and seed;
- `W_det` is allocated over canonical registry positions by seeded random permutation;
- factor families inherit the **geometry only** of the already-existing `BackgroundV2` hierarchy: broad, mid and narrow support fractions/counts;
- each factor's selected addresses are split deterministically into equal positive and negative loading sets (difference at most one address for odd support size);
- positive and negative sides have equal absolute loading magnitude within a factor;
- each factor loading is mean-centered over its selected addresses and normalized to its declared RMS scale;
- family scales are inherited unchanged from the existing `BackgroundV2` broad/mid/narrow scales (`0.85`, `0.55`, `0.45`) and are not tuned against V78 outcomes;
- the paralog component is excluded from F2 because it is designed for same-sign substitute structure rather than signed detection antagonism.

No factor membership or sign may depend on gene symbol, Ensembl ID, biotype, real expression rank, marker status, regulatory edge, donor, source, operator, pathology, target-discovery artifacts, broad class, or the corrected evaluation subset.

F2 is deliberately class-independent: it repairs detection dependence while preserving E2 as the only new broad-class biological hierarchy in this experiment.

#### F2 invariants

For each cell relative to F0:

- `library_target` must be identical;
- `detected_target` must be identical;
- structural support mask must be identical;
- E2 `eta` and `rel` must be identical before detection selection;
- selected gene identities may differ;
- total detected genes must remain exactly the target;
- total library counts must remain exactly the target.

### F3 — F2 + corrected positive-count / depth marginal authority

F3 keeps the F2 signed detection mechanism unchanged and adds a separately governed count-marginal repair.

F3 has two components derived from **corrected pathology-blind full-registry TRAIN** data.

#### A. Rank-scrubbed gene abundance geometry

Build a small authority containing the empirical distribution of per-address positive-count abundance across the full 41,238-address corrected TRAIN registry.

The authority stores sorted/quantile geometry, not an address→real-abundance map.

At synthetic-world construction time:

- assign the empirical abundance quantiles to canonical registry positions through a new deterministic seeded permutation;
- never assign a real gene's empirical abundance back to that same gene by identity;
- record the permutation seed/stream and authority digest;
- keep module membership independent of this assignment.

This replaces only the baseline abundance geometry used for positive-count weights. It does not change class programs or signed detection modules.

#### B. Corrected per-cell library / detected-feature geometry

Build pathology-blind TRAIN measurement-marginal authorities from the corrected full registry for the same observable measurement strata already allowed to affect observation: source/operator where supported by sufficient real cells, with a prospectively declared fallback hierarchy for sparse operators.

The authority may contain quantiles/correlation geometry for:

- total library count;
- total detected canonical addresses;
- their log1p correlation;
- support-limited clipping rules.

It may not contain biological labels, pathology fields, target-discovery labels, class programs or query identities.

F3 replaces the old depth-target marginal source with this corrected authority, but leaves F2 signed selection and all structural-support rules unchanged.

#### Sparse-stratum fallback

Before outcomes are read, the builder must use this deterministic fallback order:

1. operator-level authority if the corrected TRAIN operator has at least 50 cells;
2. source-family authority if the operator has fewer than 50 cells;
3. global TRAIN authority only if the source family itself has fewer than 50 cells.

No outcome-dependent regrouping is allowed.

## 6. Corrected-data authority boundaries

The corrected TRAIN cache may be read only by authority builders. Runtime synthetic generation consumes only compact derived authority artifacts.

Every new authority must record:

- exact corrected cache/source identifiers and SHA-256 bindings;
- fields read;
- explicit pathology-field denylist result;
- number of cells and addresses represented;
- derivation version;
- whether values were rank-scrubbed / identity-scrubbed;
- no TEST/Morabito access.

No real gene program membership is ever copied into synthetic biology.

## 7. Seed / stream freeze

Preserve generator and measurement seed `7302` for the first causal tournament so F0 reproduction is directly checkable.

Reserve new disjoint stream blocks prospectively:

- signed detection factor membership: `12000–12999`;
- signed detection cell factors: `13000–13999`;
- abundance-rank permutation: `14000`;
- any F3 marginal realization jitter not already supplied by the frozen measurement seed: `14100–14199`.

The exact stream IDs used must be emitted in manifests. No existing V77 stream may be reused.

## 8. RED requirements before implementation

Implementation starts with failing tests for the intended missing surfaces.

Required RED assertions:

1. the current observer has no independent detection-propensity field;
2. the current detection-selection score is exactly `log(rel) + Gumbel`;
3. F0 reproduction fails closed if the committed E2 receipt/reference is unavailable or mismatched;
4. F1 may change only background selection and must not alter E2 class configuration;
5. F2 must leave `eta`, `rel`, structural support, `library_target` and `detected_target` identical to F0 for matched cells;
6. F2 signed loading support/sign assignment must be deterministic and shard-invariant;
7. each F2 factor must contain both positive and negative loadings and have near-zero mean over selected addresses;
8. F2 module membership/signs must be invariant to gene-symbol/Ensembl/biotype metadata perturbation;
9. F2 module membership/signs must not key on donor/source/operator/class/pathology/query fields;
10. F2 must preserve exact per-cell detected-feature and library totals;
11. a proposed F3 marginal authority containing pathology-like fields is rejected;
12. F3 gene-abundance authority must not expose a real address→empirical-abundance mapping;
13. F3 rank-scrubbed abundance assignment must be deterministic, permutation-based and independent of synthetic biology modules;
14. F3 sparse-stratum fallback must follow the frozen operator→source→global rule exactly;
15. the 2K smoke must retain all 42 observation operators with minimum support >= 1;
16. F0–F3 manifests must bind source SHAs, authority SHAs, arm definition, seeds/streams, registry SHA and evaluation-universe SHA;
17. E4 and JEPA training remain fail-closed.

## 9. Frozen scoring panel

Use the same exact corrected 14,417-address evaluation universe and matched-scoring implementation as the completed E0–E3 tournament.

Retain all prior endpoints:

- expression median `|r|`;
- expression fraction `|r| > 0.3`;
- expression top-10-PC variance;
- detection median `|r|`;
- detection fraction `|r| > 0.3`;
- detection mean degree;
- detection transitivity;
- detection largest-community fraction;
- T5 within-class / pooled correlation ratio;
- abundance max / median nonzero;
- top-1% count share;
- median detected genes per cell.

Add signed detection endpoints prospectively:

- fraction of detection correlations `> +0.3`;
- fraction of detection correlations `< -0.3`;
- positive/negative high-correlation ratio;
- positive signed degree distribution summary;
- negative signed degree distribution summary;
- fraction of scored genes participating in at least one negative high-correlation edge;
- negative-edge participation by detected community.

Corrected real points remain descriptive references. Current S159 intervals remain non-binary diagnostics.

## 10. Prospective falsification rules

### F0

Must reproduce committed E2. Failure blocks the tournament.

### F1

BackgroundV2 is rejected as an adequate repair if topology improves by materially worsening abundance/depth or if signed detection structure remains grossly one-sided. A better transitivity value alone cannot qualify F1.

### F2

F2 supports the signed-detection hypothesis only if, relative to F0:

- negative high-correlation edges become materially nonzero;
- positive/negative ratio moves strongly toward the corrected real direction;
- detection transitivity improves without a gross collapse in detection mean degree / edge fraction;
- abundance and library marginals remain approximately unchanged, as expected from the isolation contract;
- E2's T5 improvement is not erased.

F2 is rejected if signed improvement comes from source/operator/class leakage or if selection destroys the already-near-real unsigned topology.

### F3

F3 supports the count-marginal hypothesis only if, relative to F2:

- abundance max/median moves toward the corrected real direction;
- top-1% count share moves toward corrected real;
- median detected genes/cell moves toward corrected real;
- F2 signed-topology gains are retained rather than erased;
- T5 remains consistent with the E2 broad-class mechanism rather than reverting toward E0/E3.

No arm is selected because one scalar is closest to real. The useful outcome is causal attribution across the F0→F1, F0→F2 and F2→F3 contrasts.

## 11. Shortcut / leakage audit

Before interpretation:

- rerun class×source/operator/donor association audit;
- verify signed-module memberships/signs are independent of source/operator/donor/class;
- verify F3 abundance permutation is independent of real identity and synthetic biology modules;
- preserve exact-twin / negative-control semantics where applicable;
- rerun 2K 42/42 operator support;
- compare F0 against the committed E2 receipt;
- report any accidental association rather than correcting it post hoc.

## 12. Implementation boundaries

The implementation successor may add only:

- compact corrected TRAIN marginal-authority builders/artifacts;
- a signed detection-propensity module;
- a successor sparse-count selection/allocation surface that cleanly accepts separate detection score and positive-count weights;
- F0–F3 arm configuration;
- RED→GREEN tests;
- frozen tournament/scoring receipts.

It must not change:

- E2 class scale or class assignment;
- canonical runtime / optimizer / EMA / checkpoint code;
- q-safety / physical provenance contracts;
- target-discovery artifacts;
- corrected real cache contents;
- 353 mappings;
- TEST/Morabito state;
- E4 authorization.

## 13. Execution sequence after written-spec approval

1. write an implementation plan mapping changes onto the existing observer/test files;
2. RED-test F0 reproduction and missing detection-separation interface;
3. implement F0 and F1 only; verify exact E2 reproduction and unchanged BackgroundV2 parameters;
4. RED-test F2 signed field and isolation invariants;
5. implement F2; run structural tests before scientific scoring;
6. self-audit F2 for identity/nuisance leakage;
7. RED-test F3 corrected marginal authority and rank-scrubbing/fallback rules;
8. implement F3;
9. rerun full structural/spillover suite and 2K operator regression;
10. execute one frozen 2,500-cell F0–F3 tournament on the exact corrected universe;
11. record exact SHAs, authority digests, arm manifests and a scientific ruling without retuning.

## 14. Completion criterion

This V78 step is complete when F0–F3 have been implemented under the frozen contract, structural/leakage tests are green, and the same corrected multi-statistic panel plus signed topology endpoints has been reported with no post-outcome tuning.

Completion does not imply any arm is production-qualified or that JEPA training is authorized.
