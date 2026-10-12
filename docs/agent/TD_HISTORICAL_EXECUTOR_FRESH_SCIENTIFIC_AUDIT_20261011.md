# Historical target-discovery executor fresh scientific audit — 2026-10-11

Status: `HISTORICAL_RELATIONAL_CHAIN_FRESHLY_AUDITED__TERMINALS_PRESERVED__CLAIM_STRENGTH_TIGHTENED__NO_CURRENT_TARGET_AUTHORITY`

## Scope and evidence classes

This audit reopens the **scientific mechanics and claim semantics**, not protected biological outcomes and not current corrected target discovery.

The historical relational chain is not equally recoverable at source-code level:

- **TD57B:** exact decision-bearing executor source is preserved in Git and was freshly reviewed line by line.
- **TD56S:** prospective screen + result and historical script/result SHA identities are preserved, but exact decision-bearing executor bytes are not currently present in the iteration directory. Fresh audit is therefore contract/result-level, not a new line-by-line source audit.
- **TD57C:** prospective screen + immutable failure result + exact original executor SHA are preserved; exact executor source bytes are not currently available in Git at the expected path. Fresh audit is contract/result-level only.
- **TD59:** original decision-bearing executor/result JSON bytes are not recovered. However, an explicitly labeled independent successor replay implementation is preserved and was freshly reviewed. It reproduces all 24 decision-bearing observed/p95/null-max case values exactly from the immutable inputs. This closes scientific-statistic replay, not original-byte provenance.

No historical terminal is changed by this audit.

## 1. TD56S — disjoint-gene relational geometry

Prospective object:
- two disjoint 512-gene molecular views from the all-operator common-scalar set;
- 2,048 fixed within-view pair-order coordinates;
- same-donor×operator cell-pair geometry only;
- donor-primary aggregation;
- wrong-cell Y identity null preserving donor/operator and depth/detection blocks;
- source PASS iff observed donor statistic > 0 and > matched-null p95;
- HVS → NPH52 → SEA_AD sequential kill.

Historical result:
- HVS PASS: observed 0.7975611 vs p95 0.5541568;
- NPH52 PASS: observed 0.8007195 vs p95 0.5990585;
- SEA_AD PASS: observed 0.8782250 vs p95 0.7526606.

Result self-audits additionally show:
- pair-hash preimage orientation ambiguity is terminal-invariant;
- coordinate-wide pair sign orientation cannot change the absolute relational distance;
- a second non-overlapping 2,048-pair subset also passes all three sources;
- optimized SEA_AD distance implementation matched the direct formula exactly in the recorded audit.

Fresh conclusion:
`TD56S` remains valid historical evidence that **disjoint measured RNA views encode concordant within-donor relational geometry beyond the matched wrong-cell null** on the historical 50k substrate.

It does not establish current corrected recurrence, donor-heldout recurrence, learned-teacher continuity, partial-evidence predictability, a production pair width, or target authority.

Source-audit limitation: the historical result records script SHA identities, but those exact decision-bearing script bytes were not freshly available here. Therefore this audit does not upgrade TD56S to a newly source-requalified execution.

## 2. TD57B — independent-gene scale-free triplet-order recurrence

Exact preserved executor reviewed:
`target_discovery/iterations/td57b_independent_triplet_recurrence/td57b_fixed_relational_recurrence.py`

Historical frozen local executor SHA:
`1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e`

### 2.1 Gene/view construction

The implementation matches the prospective screen:
- ranks common addresses by `SHA256("TD56S|gene|<address>")`;
- Panel 0 uses positions 1024..2047 split into disjoint X/Y 512-gene views;
- Panel 1 uses positions 2048..3071 split into disjoint X/Y views;
- both panels are disjoint from the earlier TD56 positions 0..1023;
- 2,048 deterministic pair coordinates/view are selected by full SHA256 ordering.

Pair sign orientation in code follows selected view positions rather than explicitly reordering expression subtraction by numeric `g0/g1`. This is **outcome-invariant for the tested distance**, because reversing a coordinate orientation flips that coordinate for every cell and preserves absolute inter-cell sign differences. The prospective screen explicitly recognizes this invariance.

### 2.2 Distance and triplets

The code implements the declared tie-aware concordance distance:
- sign coordinates in {-1,0,+1};
- informative iff not both zero;
- require at least 256 informative coordinates;
- distance = absolute sign difference / 2 averaged across informative coordinates.

Triplets:
- remain inside donor×operator strata with n>=4;
- population is `n * C(n-1,2)`;
- capped at 64/stratum by deterministic modulo-unbiased SHA256 rejection sampling;
- comparison cells are canonicalized by global row.

Important deliberate dependence:
- the triplet-sampling preimage excludes panel;
- therefore Panel 0 and Panel 1 use the same sampled cell triplets.

This is **not a defect**. The prospective screen explicitly freezes the same cell-triplet sample across panels so panel replication isolates molecular-view changes rather than a new cell sample.

### 2.3 Donor statistic and null

Observed:
- X defines the base measurable/non-tied triplet set;
- Y independently earns measurability/non-tie;
- require >=20 retained triplets/donor;
- donor statistic = X/Y triplet-order agreement;
- half statistic = median across measurable donors.

Null:
- reassigns Y identities only;
- stays inside donor×operator depth/detection blocks;
- uses deterministic nonzero cyclic shifts;
- X base triplets remain fixed;
- each null Y independently re-earns measurability/non-tie;
- does not precondition on observed-Y support;
- requires >=20 triplets/null donor, >=4 measurable donors/half;
- exactly 64 finite half-null statistics;
- p95 is sorted index 60;
- PASS iff observed >0.5 and observed > p95.

This matches the frozen prospective design.

### 2.4 Critical claim-strength correction: donor halves are not independent replicates

The prospective screen describes four source/panel half-cases from two deterministic donor splits.

Those four cases are **not four statistically independent biological replicates**:
- split 0 partitions the source donor pool into two halves;
- split 1 reorders and repartitions the *same source donor pool*;
- donors therefore recur across split 0 and split 1 cases.

The frozen 4/4 conjunction is still a legitimate robustness requirement: the result had to survive multiple deterministic donor partitions. But `24/24 PASS` across 2 panels × 3 sources × 4 cases must not be treated as n=24 independent samples or as 24 independent hypothesis tests.

Preferred language going forward:
- `24/24 frozen recurrence cases PASS`, or
- `survives all prospectively frozen donor-partition robustness cases`.

Avoid:
- `24 independent replications`,
- `24 independent donor tests`, or any inferential calculation that assumes independence among those 24 rows.

### 2.5 TD57B terminal

Historical TD57B survival remains scientifically interpretable as:
- fresh disjoint molecular views preserve scale-free relational ordering;
- donor is the primary aggregation unit;
- survival reproduces across all three source families and multiple frozen donor partitions;
- correct-cell Y alignment matters beyond the matched technical null.

It does not establish current corrected biology, fine-local geometry, learned-teacher continuity, partial-evidence predictability, or training authority.

## 3. TD57C — nearest-third three-view local recurrence

Exact historical executor SHA:
`530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c`

Fresh source-level limitation:
- the exact executor source bytes are not currently present at the expected in-repo path;
- therefore no new line-by-line executor qualification is claimed here.

The prospective contract is nevertheless unambiguous:
- fresh positions 3072..6143 across two panels;
- independent Z selector + tested X/Y views;
- nearest `ceil(M/3)` finite Z neighbors;
- frozen structural donor eligibility before outcome;
- X-defined base support;
- Y/null Y independently earn measurability;
- donor-primary medians;
- matched Y-cell null;
- 4/4 case requirement/source-panel;
- strict sequential stop.

Historical immutable result:
Panel 0 HVS only was opened:
- split0/half0 FAIL: 0.5370370 < p95 0.5555556;
- split0/half1 PASS;
- split1/half0 FAIL: 0.5416667 < p95 0.5806452;
- split1/half1 PASS.

HVS Panel 0 = 2/4 and therefore terminal FAIL.
NPH52, SEA_AD and Panel 1 remained unopened under the frozen sequential rule.

The same-X/Y unrestricted post-failure 4/4 diagnostic is correctly labeled forensic and cannot rescue TD57C.

Fresh conclusion:
`NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL` remains immutable.

The failure falsifies the **specific nearest-one-third independently selected local objective proposal on those frozen views**. It does not falsify unrestricted TD57B geometry or broader mesoscale relational information.

## 4. TD59 — nearest-half mesoscale locality frontier

Historical original executor SHA:
`3268486b3ccd002fe83d05fea25b16ff88cde85a0511255852ae6fc7dc12d9f0`

Original executor/result JSON bytes are explicitly recorded as not recovered.

Prospective anti-fishing evidence is strong:
`TD59_PREOUTCOME_BINDING_V1` freezes before expression outcome:
- exactly one locality fraction: 1/2;
- pair width 2,048;
- minimum informative coordinates 256;
- 64 triplets/stratum;
- 64 nulls;
- two donor partitions;
- fresh gene positions 6144..9215;
- structural donor counts HVS 29 / NPH52 16 / SEA_AD 46;
- exact six view gene/pair hashes;
- no additional locality fraction after TD59 regardless of outcome.

This is important: TD59 is not a hidden after-the-fact scan over 1/2, 2/3, 3/4, adaptive-k, etc. It is one prospectively frozen successor question after the TD57C nearest-third failure.

### 4.1 Successor replay implementation audit

Freshly reviewed successor:
`target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/td59_replay_closure_executor_v1.py`

Recorded successor SHA:
`870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085`

This is explicitly **not** the missing original executor.

The successor matches the prospective mechanics:
- exact fresh panel slices 6144..9215;
- exactly `LOCAL_DENOMINATOR=2` (nearest half);
- 2,048 deterministic pairs/view;
- tie-aware 256-coordinate concordance distance;
- Z-only nearest-half selector with `(distance, global_row)` tie break;
- structural donor eligibility from metadata geometry;
- panel-specific deterministic local-triplet sampling;
- X-defined base support and Y re-measurability;
- donor statistic requires >=20 resolved triplets;
- half statistic is donor median;
- matched Y-only donor/operator depth/detection cyclic-shift null;
- exactly 64 nulls and p95 index 60;
- PASS iff observed >0.5 and >p95.

The replay-closure record reports exact reproduction of all 24 historical decision-bearing rows for:
- observed median donor agreement;
- matched-null p95;
- matched-null maximum;
plus all six pair-address hashes and donor counts.

This closes scientific-statistic reproducibility, **not original executor byte provenance**.

### 4.2 TD59 evidence strength

Historical frozen screen:
- 24/24 prospective cases PASS;
- weakest observed-p95 margin +0.0011566307718604563;
- 22/24 cases beat null maximum;
- two Panel-0 HVS cases do not beat null max.

Thus TD59 is a valid p95-rule survival but a narrow one in HVS. The result document correctly records this limitation.

The same donor-partition dependence caveat as TD57B applies: four donor-half cases/source/panel are deterministic robustness partitions of the same donor pool, not four independent biological replicates.

TD59 therefore supports an **operational pilot locality bracket**:
- nearest-third failed on its own frozen fresh views;
- nearest-half survived on different prospectively frozen fresh views.

It does not estimate a precise monotone biological threshold at exactly 1/3 vs 1/2, because the molecular panels differ. The result document already states this correctly.

## 5. Cross-chain audit conclusion

### Historical terminals retained

- TD56S: historical relational-geometry survival retained.
- TD57B: historical independent-gene scale-free recurrence survival retained.
- TD57C: immutable nearest-third local recurrence FAIL retained.
- TD59: historical nearest-half mesoscale recurrence survival retained.

### Claim language tightened

Do **not** count deterministic donor partitions as independent biological replications.

Use:
- donor-primary recurrence;
- repeated prospectively frozen donor partitions;
- all frozen recurrence cases survived/failed as appropriate.

Do not use a nominal n equal to the number of case-table rows for inferential independence.

### Custody/source limitations retained

- TD57B exact source is freshly reviewable.
- TD56S and TD57C exact historical decision-bearing executor bytes are not freshly available here.
- TD59 original bytes remain missing; successor replay closes statistic reproducibility only.

### Current-authority limitation retained

All of these experiments were executed on the historical target-discovery substrate whose HVS/SEA_AD physical mapping was later shown corrupted for current authority purposes.

Therefore historical scientific outcomes remain useful evidence and design history but **cannot authorize a current target**. Corrected replay requires the separate current custody/value-read authority sequence.

## 6. Consequences for the current target tournament

The historical chain supports using relational geometry as a candidate family, but the current tournament must attack its historical weaknesses explicitly:

1. donor is the inference unit; source is explicit;
2. matched wrong-cell nulls preserve donor/operator/support/depth/detection;
3. repeated donor partitions are robustness checks, not independent-n multiplication;
4. C1 may include broad/mesoscale relational structure, but deepest/fine locality cannot be privileged from historical evidence;
5. locality scale cannot be inherited as a production 1/2 fraction;
6. corrected recurrence must be freshly established on the corrected substrate before any target selection;
7. learned representation/teacher continuity must be separately qualified before a relational objective is attributed to learned biology;
8. partial-evidence student predictability remains a separate gate.

## Authority boundary

This audit opens no corrected values and creates no authority for:
- G6/G7 execution;
- corrected biological replay;
- target selection;
- representation selection;
- TD60;
- Stage4;
- pathology;
- training.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Audit terminal:
`TD56_TD57B_TD57C_TD59_HISTORICAL_CHAIN_AUDITED__TERMINALS_PRESERVED__DONOR_PARTITIONS_NOT_INDEPENDENT_REPLICATES__CURRENT_TARGET_AUTHORITY_NONE`
