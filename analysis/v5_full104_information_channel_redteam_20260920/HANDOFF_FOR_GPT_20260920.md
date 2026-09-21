# Handoff — FULL104 information-channel red-team

**Date:** 2026-09-20  
**Active branch:** `audit/v5-full104-information-channel-redteam-20260920`  
**PR:** #33 (draft)  
**Stable base:** `impl/v5-full104-pass1-review-repairs-20260920` / PR #32  
**Rule:** always re-fetch the live PR #33 head before acting. Do not trust a SHA
written in a handoff after the branch has advanced.

This handoff supersedes the earlier `82934c76` snapshot and incorporates the
valid parts of supporting handoff PR #34 without merging that diverged branch.

---

## 0. Standing boundaries

```
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED                  = SEALED
PATHOLOGY / DEV / SEALED  = SEALED
MASKING_POLICY_SELECTED   = NO
G5_MARGIN_SELECTED        = NO
TRAINING_OFF
```

No current authority has been changed.

Closed FULL104 foundation still includes:

- pass1 SHA:
  `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`
- physical binding:
  `4c44b89e91e85b762224a6c2cf7e5cd88956a1726f57a52c03ddcab4ad0c3602`
- Census Authority V2:
  `7a090d4078239e9bc161ae60c289b7f1a5bbb02e7cf3e6bcc0ae9c284b89ee21`
- address registry:
  `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- observation-state:
  `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- 4,553,407 cells / 104 donors / 42 operators / 41,238 ledger addresses
- 17,186 strict core / 17,053 current globally eligible targets
- strict-core measured-zero frequency:
  `0.8329826626244999`

The old selection-row pass1 and old “BLAS broken” diagnosis remain historical
and invalid for current role.

---

## 1. Scope firewall — mandatory

Read `FULL104_SCOPE_AND_HISTORICAL_FIREWALL.md` before using any result.

Every result must be classified as one of:

- `CURRENT_FULL104_AUTHORITY`
- `CURRENT_FULL104_RECONNAISSANCE`
- `REDUCED_POOL_DIAGNOSTIC`
- `FIXTURE_ONLY`
- `HISTORICAL_SUPPORTING_ONLY`
- `WITHDRAWN`

A smaller run, historical checkpoint, 512-address pool, fixture, placeholder,
stale handoff value, or withdrawn claim may motivate a test, but may not set a
current FULL104 threshold, equivalence margin, policy, target universe, expected
effect, or terminal verdict.

Heavy cached artifacts may be reused after code changes only with an explicit
equivalence proof or a new heavy run.

---

## 2. Audit G withdrawal remains controlling

Earlier claims that the control-calibration cache was biased toward HVS/high
complexity were wrong. They used the population marginal as the reference even
though the cache is explicitly equal-donor weighted.

Correct state:

- 103/104 donors at 1,024 rows;
- one NPH52 donor has only 81 total rows and is fully retained;
- HVS observed 39.7753% vs donor-uniform target 39.4231%;
- mean core nonzeros 3371.6 vs equal-donor expectation 3370.1 (+0.05%);
- low-tail observed 403 vs expected 420, ratio 0.959;
- `AUDIT_G_OUTCOME = NO_ISSUE_FOUND`.

Hosted CI no longer tries to access the Windows path. It validates a committed
Audit G fixture and the selector implementation. Physical cache qualification is
a separate fail-closed script:
`scripts/qualify_audit_g_physical_artifact_20260920.py`.

Do not restore the withdrawn cache findings.

---

## 3. Audit A — real normalization channel, recoverability still open

Established on all 4,553,407 cells:

- source-library mass: 122,517,308,792
- ledger mass: 117,838,742,268
- outside-ledger mass: 4,678,566,524
- pooled outside-ledger fraction: 0.0381869841
- 95.63% of cells have some outside-ledger mass
- HVS mean outside fraction = 0
- NPH52 mean ≈ 0.0140
- SEA_AD mean ≈ 0.039857

Current status:

```
A1_OUTSIDE_LEDGER_MASS_EXISTS_AND_IS_SOURCE_STRUCTURED = ESTABLISHED
A2_CAUSAL_NORMALIZATION_ROUTE_EXISTS                   = ESTABLISHED
A3_MODEL_CAN_RECOVER_SOURCE_FROM_THIS_ROUTE            = OPEN
SCOPE_CLASS                                             = CURRENT_FULL104_RECONNAISSANCE
```

The old headline “the denominator identifies source perfectly” is too broad.
The 104/104 result used audit-only denominator fractions, not direct model
features, and `fraction_inside = 1 - fraction_outside` is redundant.

Useful causal bound for outside fraction `f`:

`0 <= x_ledger_only - x_actual <= -log(1-f)`.

This establishes a real route; it does not prove a trained JEPA exploits it.

Audit D interaction is also narrowed: the current score discards pure
between-donor/source location-scale structure, not every source-modulated
cell-varying channel.

The source-versus-disease magnitude question remains **unopened**. Do not use
pathology to choose among repairs unless explicitly authorized prospectively.

---

## 4. Audit B — full burden heterogeneity, reduced-pool selection evidence

FULL104 per-address burden heterogeneity is real:

- detected-token median 260,522; p95 3,053,046; max 4,198,103
- UMI median 577,996; p95 15,396,228; max 3,545,668,963

The 512-address diagnostic shows screening-preferred addresses with roughly:

- 2.02× detected-token burden
- 5.36× UMI burden
- 1.38× detection entropy

But those ratios are **not** actual production TOP8/RIDGE8/PREFIX3 burden.
Current B selects within a deterministic 512-address pool, uses non-production
screening geometry, and compares to the pool baseline.

Status:

```
FULL104_PER_ADDRESS_BURDEN_HETEROGENEITY  = ESTABLISHED
REDUCED_POOL_SCREENING_BURDEN_ENRICHMENT  = ESTABLISHED
ACTUAL_FOLD_SPECIFIC_POLICY_BURDEN        = OPEN
SCOPE_CLASS_SELECTION_RATIOS              = REDUCED_POOL_DIAGNOSTIC
```

Next B must use authenticated training donors per outer fold and the exact
production planner on a prospectively frozen target sample/full universe.
Held-out realized zero/nonzero patterns may not choose masks.

---

## 5. Audit C — fold-aware instrument repaired; execution still pending

Current all-donor reconnaissance found:

- 14,526 / 17,053 with >=5 supported donors in all three sources under the simple
  descriptive benchmark;
- 2,527 with at least one weak source;
- all-zero donor×target pairs:
  HVS 887, NPH52 6,220, SEA_AD 23,344;
- 75 targets are all-zero for every SEA_AD donor.

Do **not** call these the fold-specific terminal estimability result.

The scorer currently maps `rss_y <= EPS` to `r=0` and therefore `r²=0`.
Downstream finite matrices cannot distinguish undefined target correlation from
a genuinely estimable zero correlation.

The C2 script has now been repaired to:

- bind the authenticated FULL104 split receipt by its canonical semantic digest;
- verify donor order and source codes;
- report available train/held donors by source×fold;
- report supported and scorer-variable donors per target;
- report how many current score terms would contain undefined-target zeros;
- introduce **no new per-source threshold**.

Authenticated donor geometry:

| fold | HVS train/held | NPH52 train/held | SEA_AD train/held |
|---|---:|---:|---:|
| 0 | 30/11 | 12/5 | 34/12 |
| 1 | 31/10 | 13/4 | 34/12 |
| 2 | 31/10 | 13/4 | 35/11 |
| 3 | 31/10 | 13/4 | 35/11 |

Therefore global `train>=20 / heldout>=5` thresholds must not be transplanted
per source after seeing the data.

**Critical execution gate:** the existing 242 MB B/C/E sufficient-statistics
artifact was produced before the audit builder adopted the exact production
`source_library` parser. It may be reused only if
`audit_source_library_parser_equivalence_20260920.py` proves exact old-vs-current
parser equality over all 4,553,407 authenticated metadata rows. Otherwise rebuild
the heavy statistics.

Terminal evidence-schema treatment of non-estimability must be frozen only after
C2 is quantified.

---

## 6. Audit E — estimand mismatch explicitly scoped

Current 512-pair diagnostic:

- pooled E1 detection association mean ≈ 0.1424
- pooled E2 conditional quantitative correlation mean ≈ 0.2600
- screening-shaped E3 mean ≈ 0.0760
- corr(E3,E1) ≈ +0.1774
- corr(E3,E2) ≈ -0.0721

These compare different estimands: E1/E2 are pooled, while E3 is
source-balanced/within-donor.

Status:

```
SCOPE_CLASS                      = REDUCED_POOL_DIAGNOSTIC
PRODUCTION_ALIGNED_E1_E2_VS_E3  = OPEN
```

Next E must select partners training-side per authenticated fold and compute
E1/E2 within donor with the same source/donor aggregation as E3.

---

## 7. Audit F — scalar fixture demoted to historical mechanism only

Current V5 authority is:

- `QUERY_LOCAL_BIOLOGICAL_LATENT_STATE_V1`
- `HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1`
- `QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1`
- `SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1`

Therefore the old scalar zero/detection fixture does not define the desired V5
target.

Future real-teacher F must decompose:

1. address identity;
2. cell/context main effect;
3. query×context interaction;
4. technical-decoy explanation;
5. query-scalar invariance as a negative control;
6. remaining-RNA necessity.

The real teacher is multivariate; use a prospective vector-valued variance
definition and scalable grouped/fixed-effect residualization.

```
SCALAR_ZERO_STRATIFIED_FIXTURES       = HISTORICAL_MECHANISM_ONLY
REAL_V5_QUERY_LOCAL_LATENT_DECOMPOSITION = DESIGN_OPEN
```

---

## 8. New G3 fit-objective gap integrated from PR #34

Current production scientific mass is:

`DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`

with authenticated:

`primary_row_weight = 1 / (104 * donor_cell_count)`.

But the current full-data ridge attacker validates then discards that weight and
fits ordinary cell-weighted Gram/RHS statistics.

Keep three objectives distinct:

1. `CURRENT_CELL_WEIGHTED`
2. `PRODUCTION_OBJECTIVE_MATCHED`
3. `SOURCE_DONOR_BALANCED_DIAGNOSTIC`

No replacement is selected.

See `G3_ATTACKER_FIT_OBJECTIVE_CONTRACT_GAP.md`.

---

## 9. H3 donor-vs-target precision design integrated from PR #34

Equal source weight means a held-out NPH52 donor carries 6.67% of total score in
fold 0 and 8.33% in folds 1–3.

Prospective H3 comparison:

- `TARGET_ONLY`
- `DONOR_ONLY_WITHIN_SOURCE`
- `PAIRED_TARGET_AND_DONOR_WITHIN_SOURCE`

This determines whether more targets can meaningfully improve precision or the
floor is finite donors.

Do not run H3 on matrices where undefined target correlation has already been
serialized as zero.

See `H3_TARGET_VS_DONOR_PRECISION_DECOMPOSITION_DESIGN.md`.

---

## 10. G4 now requires a technical-only decoy

Historical T1/u0/support findings remain supporting-only and do not set a
threshold.

Their valid use is as motivation for a prospective falsification control:
`F-technical-only-decoy`.

Any future G4 biological-content functional must outperform a lawful
pathology-blind baseline using source/operator/depth/sparsity/support geometry
alone. Source-correlated donor composition must not impersonate biology.

This requirement has been integrated into the upstream G4 design.

---

## 11. Heavy artifact provenance

`EXTERNAL_ARTIFACTS.json` now uses immutable producer provenance.

### Audit A per-cell denominator

- SHA-256:
  `9ff45071fb09f5d89340a7cca76ab77ab826533f29e9dd80b33a821645283cd1`
- producer commit: `abcea57c...`
- producer script semantics unchanged;
- content-addressed reuse allowed if bytes match.

### B/C/E sufficient statistics

- SHA-256:
  `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae`
- producer commit: `abcea57c...`
- producer script has since changed to the production-exact parser;
- reuse state:
  `REQUIRES_METADATA_ONLY_STRICT_PARSE_EQUIVALENCE_CHECK_BEFORE_REUSE`.

A manifest rebuild must never overwrite producer commit/script hashes with the
current checkout merely because the old artifact still exists.

---

## 12. PR #34 supporting handoff branch audit

Supporting branch:
`handoff/jepa-v5-gpt-parallel-audit-20260920` / PR #34.

It diverged from active PR #33 and must **not** be merged wholesale.

Valid material already integrated into PR #33:

- G3 fit-objective contract gap;
- current source/fold donor geometry;
- H3 target-vs-donor precision design;
- technical-only G4 decoy requirement.

Not promoted:

- governance pointer/START_HERE edits tied to an older audit head;
- historical 50K/T1 numbers as current constants;
- the suggested per-source `train>=20 / heldout>=5` requirement.

Historical 50K/T1 material stays `HISTORICAL_SUPPORTING_ONLY`.

---

## 13. CI/provenance repairs made after the earlier handoff

- audit shared-statistics builder now imports the production-exact
  `source_library` parser;
- adversarial parser tests cover fractional tokens, invalid syntax, and float
  precision spillover;
- C2 is canonical-split-bound and tested against split mismatch;
- B/E machine-readable outputs carry explicit reduced-pool/estimand-mismatch scope;
- Audit G hosted tests no longer fail because a Linux runner cannot access
  `D:/...`;
- separate physical Audit G qualification is fail-closed;
- evidence-manifest builder excludes Python bytecode;
- external heavy-artifact producer provenance is immutable;
- committed `__pycache__` entries were removed from the evidence manifest.

---

## 14. Current next actions

In order:

1. run FULL104 metadata-only parser equivalence against all 4,553,407 metadata
   rows;
2. if exact equivalence passes, reuse the content-addressed 242 MB statistics;
   if not, rebuild those statistics with the current parser;
3. run fold-aware C2 and commit the new C2 summary/detail evidence;
4. execute production-aligned Audit B burden on a prospectively frozen target
   sample/full planner;
5. execute production-aligned Audit E;
6. settle the primary shortcut estimand and the G3 fit-objective comparison;
7. freeze G4 only after the technical-only decoy discriminates;
8. justify G5 from consequence rather than historical/null noise;
9. H3, H4/G2, G4 execution, G3 capacity challenge;
10. real V5 latent-state F and remaining F13/F14/F15;
11. terminal masking;
12. training authority last.

The SHA evidence manifest is regenerated **only after** code/reports/handoff are
stable, so it cannot silently lag the evidence it claims to bind.

```
TRAINING_OFF
```
