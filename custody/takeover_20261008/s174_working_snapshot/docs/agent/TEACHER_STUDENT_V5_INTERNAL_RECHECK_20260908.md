# Teacher/Student V5 data-first internal recheck — 2026-09-08

Status: `PASS_TEACHER_STUDENT_V5_DATA_FIRST_INTERNAL_RECHECK__RELATIONAL_WEIGHT_REPAIRED_V2__DESIGN_ONLY__TRAINING_UNAUTHORIZED`

This is an internal planning/proof recheck, not an independent external review and not execution authority.

## Current combined regression

Rebuilt from the exact immutable V4 review-package ZIP and overlaid only the current V5 manifest payloads:
- immutable V4 active suite: **98/98 PASS**;
- repaired V5 prospective active suite: **66/66 PASS** across 11 exact test files;
- combined: **164/164 PASS**;
- V4 freeze audit: PASS;
- V5 data-first audit: PASS;
- Python compile: PASS.

## Data-first relational weighting repair

The full-reader operator audit found that `operator` is not a common scientific axis:
- HVS operators are native-class-pure reader-fit matrices;
- NPH52 operators are native-class-pure Astro/Endo/ExN/InN/MG/OPC/Oligo matrices;
- SEA_AD operators are multi-native-class matrices containing 17–26 native classes each.

Therefore V5 relational V1 equal-operator-group mass was an unjustified source-dependent scientific weighting. It is superseded by V2:

`DONOR_UNIFORM__ELIGIBLE_ANCHOR_CELL_UNIFORM__SAME_OPERATOR_COMPARATOR_PAIR_UNIFORM_V2`.

In V2, operator is an admissibility boundary only. Within each donor, group mass is proportional to eligible anchor-cell count and comparator pairs stay inside the anchor operator. O(n^3) triplet capacity never sets scientific mass.

Full reader-fit checks:
- 1,361 eligible donor×operator groups;
- 4,553,348 / 4,553,407 cells relationally eligible = **99.998704%**;
- minimum donor-specific eligible-cell fraction = **99.843628%**;
- old equal-group V1 could upweight a tiny group by **141.072×** relative to eligible-anchor prevalence;
- V2 direct-target group probabilities were independently recomputed on all 104 donors: every donor sums exactly to `1/104`, all 1,361 eligible groups sum to 1.0;
- base-proposal coverage profile replayed byte-identically, SHA-256 `9fe11b675f94d5f1d16d3c0a35f00b677b1733c635736134157e3891b7c1358e`; it leaves q unselected while quantifying source-balanced versus operator-coverage tradeoffs;
- `READER_FIT_OPERATOR_SEMANTICS_PROFILE_V1.json` replayed byte-identically from the frozen reader-fit metadata SQLite, SHA-256 `ccdc1299c80199394ecd814aa0736b562aa3f306345381a0997256a52b900472`.

TD57B/TD59/TD60 qualification is unchanged. Their exact frozen triplets/caps/statistics remain qualification authority; the historical <=64 triplets/stratum cap is not promoted into a production scientific group weight.

## Other closure retained

- reader-fit geometry profile replays byte-identically from frozen inputs;
- relational-support profile replays byte-identically;
- scientific-estimand profiles V1 and V2 replay byte-identically;
- donor-proposal Pareto profile replays byte-identically;
- support-overlap profile and exact 17,186-gene common-core CSV replay byte-identically;
- active-test selection and active-test manifest are deterministically regenerated from exact test bytes;
- prototype manifest/root are deterministically regenerated and checked against every included payload;
- V4 runtime contains no V5 import;
- base JEPA target remains donor-uniform/cell-uniform-within-donor;
- relational V2 direct-target proposal is frozen while base numeric proposal, evidence schedule, relational triplet budget, GPU kernel, production token budget, training horizon, and EMA half-life remain unfrozen;
- inactive checkpoint/resume continuation matches uninterrupted two-update execution exactly and fails closed on cursor/optimizer-step mismatch;
- the obsolete hash-based keyed-dropout helper is absent; Philox V2 is the sole prospective keyed-RNG reference;
- no V5 execution/training authority, successor-u0 authority, TD60 execution authority, or continuation authority is present.

The recheck explicitly preserves the numerical boundary discovered in packed execution: close dense/packed objectives and gradients do not imply statewise AdamW equivalence. V5 must be mechanically qualified as a new numerical implementation before any execution authority can exist.
