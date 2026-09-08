# JEPA NEW CHAT HANDOFF — 2026-09-08

Status: **CURRENT PROJECT HANDOFF / NOT EXECUTION AUTHORITY**

Snapshot basis:
`main @ d8917ea3fedfd4b1de457b25e8e8be4cd0e6ea88`

This handoff is intentionally subordinate to the frozen scientific/execution
authorities named in `CURRENT_AUTHORITY_INDEX.md`. If this prose ever conflicts
with a newer frozen authority on `main`, the newer authority wins.

---

## 1. Start here

The project has now been consolidated.

**Canonical branch: `main`.**

Do not resume work from an old `planning/`, `candidate/`, `production/`,
`review/`, transport, or Stage81 branch just because its branch name looks
current. Those histories have been absorbed into main for provenance.

Read in this order:

1. `START_HERE.md`
2. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
3. `docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`
4. `docs/agent/memory-os/ACTIVE_STATE.md`
5. `docs/agent/CURRENT_SUPERSESSION_MAP.md`
6. `docs/agent/JEPA_GLOBAL_BLOCKER_LEDGER_20260908.json`
7. `docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json`
8. this handoff.

Project discipline remains fail-closed:

- reproduce defects before repair;
- tests are claims to attack;
- `NOT_MEASURABLE` is not PASS;
- skip is not run;
- authority/provenance failure is STOP, not donor exclusion;
- never invent production thresholds;
- no protected-population/pathology access except through exact frozen release
  authority;
- no production training, optimizer, checkpoint, or EMA writes before explicit
  training authority;
- all conclusion-bearing implementation is subject to the mandatory
  implementation verifier before expensive compute.

---

## 2. Consolidation / branch hygiene

The previous branch sprawl has been consolidated into main.

Current consolidation authority:

`docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json`

Key facts:

- main is the single current project lineage;
- historical/divergent heads were absorbed into main;
- the current V5 tree was explicitly reconciled from
  `c7b1663cc4390843978b973986edfe58f93320a3`;
- stale V5 trees were not reactivated;
- branch deletion itself has **not** been performed;
- 57 non-main branch refs are listed as verified safe-to-delete.

Safe-delete authority:

`docs/agent/JEPA_SAFE_BRANCH_DELETE_LIST_20260908.json`

Deletion is hygiene only. It does not remove commits, tags, package roots, or
scientific authority.

Use the fail-closed cleanup script on a real clone:

`scripts/agent/delete_verified_merged_branches_20260908.sh`

First dry-run:

```bash
git checkout main
git pull --ff-only origin main
bash scripts/agent/delete_verified_merged_branches_20260908.sh
```

Only if the dry run PASSes all exact-head and ancestor checks:

```bash
JEPA_CONFIRM_BRANCH_DELETE=YES_DELETE_VERIFIED_BRANCHES \
  bash scripts/agent/delete_verified_merged_branches_20260908.sh --apply
```

The script aborts before deletion if:
- any branch moved from the recorded SHA;
- any exact branch head is not an ancestor of current origin/main.

Do **not** delete tags or immutable package artifacts.

---

## 3. Current critical path

```text
T0: close 3 implementation/provenance STOPs
        +
V5: finish remaining pre-execution authorities
        +
F1-B/C3: final mechanics binding
        ↓
integrated V5 mechanics qualification
        ↓
full-reader exposure-defined teacher training
        ↓
TD60 learned-teacher relational continuity
        ↓
D1 / partial-evidence student downstream
```

This is primarily an execution-authority/integration problem now, not a lack of
biological hypotheses.

---

# 4. T0 — highest immediate P0 gate

## 4.1 Scientific specification

T0 V18/V20 science is accepted.

Do not reopen the accepted science unless a genuinely new defect is discovered.

Accepted design facts include:

- 18 confirmation donors;
- discovery >=18;
- state primary alpha = 0.025;
- sensitivity directional alpha = 0.05;
- tail primary alpha = 0.02;
- nuisance = `[1, age_c, age_c^2, sex]`;
- 9,999 state permutations;
- tail n in {17,18};
- tail cell floor 80 is tail-only;
- historical accepted V20 execution/spec package remains scientific authority.

The broad-IMMUNE T0 target remains the current target family. Do not silently
turn T0 into a multi-target tournament.

## 4.2 Current implementation source head

Absorbed source head:

`24b2c9ffc0ab2d63061c20af8829bcb86114b11a`

T0 production is still closed.

Current explicit state:

- production B2: **FORBIDDEN**
- donor-role gate: **SHUT**
- numeric confirmation AT8: **CLOSED**
- `real_execution_ready=False`

## 4.3 Three current hard STOPs

### T0-STOP-1 — B2 logical-root chain

Logical authority must bind:

- population closure root;
- feature root;
- logical row identity;
- all execution-used metadata/count identities;
- execution-used paths, or a deterministic reconstruction identity replacing
  those paths.

External verification must prove:

`stored logical root == recomputed logical root == externally expected logical root`

and separately bind the externally expected population-closure root.

Reviewer regression:

`tests/v4/test_t0_b2_logical_chain_external_red_v2.py`

### T0-STOP-2 — raw H5AD row is not actually authenticated

The current source-library proof is still too label-driven.

A production proof must:

1. authenticate exact frozen MTG H5AD identity;
2. open exact `layers/UMIs`;
3. extract exact logical `expression_row`;
4. verify source cell ID and donor ID from the same authenticated source;
5. require raw integer nonnegative width 36,601;
6. compute full source row sum from that extracted row;
7. prove that sum equals bound `source_library`.

Caller-supplied vector + provenance dictionary is not source authentication.

Reviewer regression:

`tests/v4/test_t0_b2_raw_source_external_red_v1.py`

### T0-STOP-3 — age/sex candidate-universe parent is detached

The age/sex source bytes are authenticated, but the T0 46-donor candidate
universe must not be a free caller list.

Preferred repair:

- accept authenticated broad-IMMUNE membership bytes + external expected
  membership SHA;
- derive candidate donors internally.

Alternative:

- freeze an external candidate-universe/donor-set root;
- verify exact donor list against it in builder and loader.

Reviewer regression:

`tests/v4/test_t0_age_sex_external_parent_red_v1.py`

## 4.4 T0 items already substantially closed

Do not waste time rebuilding these from scratch:

- V20 scientific design;
- B1 feature authority;
- complete-manifest internal op31 selection;
- block-local `row_index` vs H5 source `expression_row` distinction;
- authenticated NPZ bytes -> parse same bytes -> select bound block-local row;
- raw materialized matrix width/geometry checks;
- broad-IMMUNE membership;
- IMMUNE support-count authority;
- IMMUNE_FRACTION successor formula/provenance direction;
- exact Q formulas:
  - per-cell `qdepth=log1p(source_library)`
  - per-cell `qdetect=count_nonzero(A)/35076`
  - donor Qs are means over accepted donor cells;
- threshold-free technical-completeness semantics;
- AT8 structural-availability authority mechanics;
- pathology firewall and protected outcome discipline.

## 4.5 IMMUNE_FRACTION

Frozen successor formula:

`IMMUNE_FRACTION(d)=immune_n_donor(d)/total_op31_reader_fit_n_donor(d)`

Expected geometry:

- donors = 46
- numerator total = 20,804
- denominator total = 638,150

It is:
- composition-sensitivity nuisance;
- not eligibility;
- not technical_complete;
- not a target-selection variable.

## 4.6 T0 next legal sequence

1. repair all three current red defects on main;
2. verify each regression is red before repair and green afterward;
3. rerun targeted T0 suites;
4. rerun all current T0 active suites with exact collection/pass counts;
5. run compile/import and implementation verifier;
6. inspect exact diff/root identities;
7. external review the repaired implementation;
8. only after explicit external acceptance consider production B2;
9. derive technical completeness / eligibility / deterministic roles;
10. keep confirmation AT8 magnitude unopened until lawful unlock.

Do not run production B2 merely because unit tests become green.

---

# 5. Teacher/Student V5 — current prospective successor

## 5.1 Current source/materialization

Current V5 source head:

`c7b1663cc4390843978b973986edfe58f93320a3`

Decision-bearing materialization commit:

`71484ab99d276d7251836c109885d22ab4e7abb1`

Prototype root:

`9684f4c2b7eff1da863ae50124c6aad49d25f137a84898e05e98d2ae1f0c67ad`

Current evidence:

- V5 active suite: **66/66 PASS**
- V4 regression: **98/98 PASS**
- V5 training: **UNAUTHORIZED**
- V5 execution: **UNAUTHORIZED**
- successor-u0 materialization: **UNAUTHORIZED**
- TD60 execution: **UNAUTHORIZED**

## 5.2 What is now frozen prospectively

The project has progressed beyond the earlier “estimand entirely unset” state.

Current frozen scientific target V2:

Base JEPA:

`DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`

Relational:

`DONOR_UNIFORM__ELIGIBLE_ANCHOR_CELL_UNIFORM__SAME_OPERATOR_COMPARATOR_PAIR_UNIFORM_V2`

Current relational proposal V2 is direct-target:

`DIRECT_DONOR_ANCHOR_CELL_TRIPLET_TARGET_PROPOSAL_V2`

Thus the relational route proposal matches the relational target directly; the
finite triplet budget remains compute/variance, not scientific mass.

Donor-primary objective direction is current.

The old equal-operator-group scientific weighting is superseded.

## 5.3 Full-reader geometry that controls V5

Production reader-fit population:

- cells = 4,553,407
- donors = 104
- operators = 42
- molecular addresses = 41,238
- donor×operator groups = 1,400
- median donor×operator group size = 228
- max group size = 42,209
- 1,361/1,400 groups have >=3 cells
- those groups contain ~99.9987% of reader-fit cells

Source geometry:

- HVS: 198,718 cells / 41 donors / 24 operators
- NPH52: 236,476 / 17 / 7
- SEA_AD: 4,118,213 / 46 / 11

Common measured scalar core:

- 17,186 addresses measured in all 42 operators.

Historical 3,292-cell schedule samples the same 1,400 groups but only 1–5
cells/group. It is therefore mechanics geometry, not production learning
geometry.

## 5.4 Current V5 open blockers

### V5-1 — base-cell proposal q remains unfrozen

The scientific target p is donor-uniform, but base proposal q is still open.

Known descriptive tradeoffs for donor-uniform target:

- raw cell-uniform proposal:
  - ESS ~9.68%
  - importance-weight ratio ~2,149.5x
- source-uniform/cell-uniform-within-source:
  - ESS ~40.58%
  - ratio ~296x
- mixture/direct proposals may improve efficiency but can increase repeated
  exposure of cells from small donors/groups.

Do not choose q from post-training outcomes.

Final q may only be frozen after prospectively freezing:

- total presentation horizon;
- repeated-exposure constraint;
- importance-weight/proposal conditioning limits;
- minimum donor×operator coverage requirements.

### V5-2 — support-aware evidence/view/block schedule

Historical 40%-within-measured masking gives very different absolute information
doses across operators.

Current admissible families include:

- `COMMON_CORE_ANCHOR`
- `NATIVE_SUPPORT_COVERAGE`

But visible genes, target count, view-family weights, views/family, and block
geometry remain unfrozen.

Freeze these from full-reader support authority, not 3,292 mechanics or 50k
locality pilots.

### V5-3 — exposure horizon / repeat policy / EMA half-life

Do not reuse u40/u205 as biological time.

Production must prospectively freeze:

- total training presentations;
- repeat-exposure policy;
- biological checkpoint milestones in exposure/coverage units;
- EMA half-life in presentations.

### V5-4 — GPU Philox implementation

A single V2 keyed RNG contract exists and old conflicting proof RNGs are now
historical.

Still needed:

- optimized GPU implementation;
- exact parity against V2 reference/test vectors;
- packing/order invariance;
- training-mode equivalence.

### V5-5 — integrated production trainer

The current update path is intentionally inactive/reference mechanics.

Need one source-bound end-to-end trainer binding:

- data selection;
- proposal;
- p/q weights;
- evidence masks;
- target blocks;
- finite relational samples;
- packed execution;
- keyed RNG;
- objective reduction;
- optimizer;
- gradient gates;
- Adam moments;
- EMA;
- checkpoint;
- resume cursors;
- provenance.

### V5-6 — hardware packing calibration

Need real target-hardware calibration for:

- token/memory cost;
- microbatch budget;
- headroom;
- transfer/throughput if relevant.

Packing is downstream of scientific cell/sample weights.

### V5-7 — external V5 review

After all pre-execution authorities + integrated mechanics close:

- build self-contained V5 package;
- clean-room replay;
- V4 regression + V5 prospective suites;
- implementation verifier;
- fresh independent external review.

No training before that.

---

# 6. Mechanics qualification / F1-B/C3

Current mechanics evidence head:

`c0eaf2acc0a5edc837fb2a48f726b9d626772f06`

Its frozen attack suite is useful but it is not the final trainer.

Three current blockers:

1. hard-coded movement-over-decay 2x rule is not itself the final frozen
   movement authority;
2. predictor mandatory parameters are discovered dynamically rather than frozen
   as an exact registry;
3. protected-update mechanics are not a full end-to-end trainer.

Before Q40-style mechanics qualification:

- freeze movement-vs-decay formula/tolerance prospectively;
- freeze exact predictor mandatory registry;
- bind the exact end-to-end trainer source/root;
- re-run gradient, Adam, movement, EMA, checkpoint and replay attacks against
  that exact trainer.

Q40-style qualification proves mechanics only.

It does not qualify biological learning.

---

# 7. Target Discovery

Current target-discovery source head:

`26c3cfaba77bb8e5935e76473ab1fd5f90a562bf`

Do not restart fixed-coordinate target search.

Current real biological result:

### TD57B

Scale-free donor-recurrent relational ordering:
- 24/24 PASS
- all cases beat matched null max.

### TD59

Nearest-half mesoscale relational recurrence:
- 24/24 PASS under frozen p95 criterion;
- 22/24 beat null max;
- weaker than TD57B but real;
- exact replay closure exists by independent reconstruction.

### TD57C

Nearest-third local geometry failed in HVS:
- 2/4 HVS Panel-0 cases;
- later sources/panel correctly remained unopened;
- failure is preserved.

Interpretation:

- broad/mesoscale relational order is real;
- deep nearest-third mining is not robust enough for the primary objective;
- no more locality-fraction tuning on the 50k archive.

## TD60

The old TD60 wording used “successor u40 EMA teacher” as the decision-bearing
learned teacher.

That is now prospectively superseded at project-governance level:

- historical u40 may be a mechanics checkpoint;
- a decision-bearing learned teacher must be a **full-reader
  exposure-defined checkpoint** under the final V5 schedule.

No TD60 outcome has been opened, so this correction remains lawful and
prospective.

TD60 must wait for:

- lawful qualified V5 full-reader teacher;
- frozen exposure checkpoint identity;
- exact reused TD57B/TD59 panels/triplets/nulls;
- no new locality tuning.

---

# 8. F1

Current real producer/replay source head:

`a884f558970479278bc21f3f2274dc24bee89758`

F1 mechanics remain available as a parallel lane.

Real F1 biological sweep remains unauthorized.

It still requires its own:

- strict independent review with all external authorities;
- explicit execution authorization;
- real sweep;
- data-only closure.

Do not let older F1 startup prose override current T0/V5 project priorities.

---

# 9. D1

Current D1 V2 source head:

`c13c06c103a588fc95bb93174730bf26dd613884`

D1 has substantial infrastructure already:

- future-safe readout/qualification resolver;
- teacher-state archive;
- incremental resampling;
- discovery atlas;
- score archive;
- sparse expression reader;
- molecular sufficient-statistic store.

Do not repeat the old R1-R7 defect list as if all remain current; later D1 commits
repaired many of those classes.

Current real blockers:

- no lawful qualified full-reader teacher;
- no actual frozen canonical production teacher-readout contract for that
  teacher;
- no exact teacher qualification authority selecting it;
- no final independent closure terminal over the complete current D1 V2
  pipeline.

Current terminal remains effectively:

`WAIT_HEALTHY_TRAINED_TEACHER`

Real D1 remains forbidden.

---

# 10. Protected-population authority

Population/sealed-holdout source head:

`14c2d586239aa5af15ed7cd70fdfb196d1c99f5f`

Frozen population-access root:

`e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7`

Preserve this.

No access to:

- reader_validation;
- reader_oracle;
- foundation development/sealed;
- external holdout;
- pathology outside exact lane-specific release authority.

---

# 11. Key immutable data identities

## T0 pathology metadata

Path:

`data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv`

SHA-256:

`ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a`

Do not inspect numeric confirmation AT8 until lawful confirmation unlock.

## MTG source H5AD

Path:

`data/external/v4/sea_ad/mtg/SEAAD_MTG_RNAseq_final-nuclei.2026-06-22.h5ad`

SHA-256:

`e06000cb8fc83ebad88a52a0a7c772747c38fa92c97debcfe4f59de7cea60c79`

Raw integer matrix slot:

`layers/UMIs`

Source feature width:

36,601

## Foundation full reader-fit

- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 addresses

Foundation calibration bundle known SHA-256:

`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Foundation discovery expression archive known SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

These are large immutable inputs. Do not duplicate them into small handoff
packages unless necessary; keep their exact identities/locations.

---

# 12. Chat-local review artifacts worth carrying forward

The companion handoff ZIP created in this chat contains small generated review
and specification packages.

Important current/superseding artifacts include:

- `T0_760C68_EXTERNAL_REVIEW_DELTA_20260908.zip`
- `T0_EXTERNAL_REVIEW_SELF_AUDIT_R2_20260908.zip`
- `T0_EXTERNAL_REVIEW_SELF_AUDIT_R3_DELTA_20260908.zip`
- `T0_POSITIVE_PATH_WORK_PACKAGE_V2_20260908.zip`
- `T0_UPSTREAM_INTERFACE_SPECS_V1_20260908.zip`
- `T0_AT8_AVAILABILITY_REVIEW_PACKAGE_V3_20260908.zip`

V1/V2 availability packages and positive-path V1 are historical/superseded but
may be included for provenance.

Important reviewer-generated theory/spec files include:

- T0 external blocker ledgers;
- B2 red-attack specifications;
- technical_complete successor specs;
- eligibility/role-scoped authority spec;
- power/alpha correction audit;
- positive-path discovery qualification contract.

The handoff ZIP deliberately excludes very large immutable source/checkpoint
archives. Their hashes/locations are documented instead.

---

# 13. What the next chat should do first

## First 15 minutes

1. `git checkout main`
2. fetch/pull latest main;
3. verify main head against this handoff and newer commits;
4. read the startup files in Section 1;
5. inspect `git status`;
6. do **not** revive an old branch;
7. run the branch-cleanup script in dry-run mode if branch hygiene is still
   desired.

## Engineering work — parallel tracks

### Track A — T0

Highest priority.

- reproduce all three external red regressions on current main;
- repair logical-root/closure/path binding;
- implement actual authenticated H5AD `layers/UMIs` source-row extraction;
- bind age/sex candidate donors to authenticated parent;
- rerun targeted + full T0 suites;
- implementation verifier;
- external review;
- stop before production B2 until explicit acceptance.

### Track B — V5 pre-execution authority

Pathology-blind and safe to do in parallel.

- freeze total presentations + repeat-exposure limits;
- derive/freeze base proposal q under those constraints;
- freeze support-aware evidence/view/block schedule;
- freeze EMA half-life in presentation units;
- calibrate target hardware;
- finish optimized V2 Philox GPU parity;
- bind one integrated trainer.

### Track C — mechanics

- replace unreviewed hard-coded movement rule with frozen formula/tolerance;
- freeze exact predictor mandatory registry;
- run Q40-style mechanics qualification only after trainer is source-bound.

### Track D — governance/hygiene

- keep main canonical;
- branch deletion only through exact safe-delete dry-run/apply process;
- update authority index / blocker ledger only when blockers are actually closed.

---

# 14. Iterative working method expected by the project owner

Use an iterative/parallel approach:

1. decompose independent workstreams;
2. run several non-conflicting checks in parallel;
3. after every implementation, attack it from the opposite direction;
4. re-read the governing contract after green tests;
5. verify exact diffs;
6. verify exact test collection counts;
7. compile/import;
8. verify hashes/roots;
9. check that a green helper is actually called by the production path;
10. do not move to expensive compute until implementation-verifier PASS.

When a new producer/agent push appears:

- poll the exact head;
- diff commit-by-commit;
- do not inherit its PASS claim;
- rerun the external attack class;
- update the canonical blocker ledger only after independent evidence.

---

# 15. Explicit forbidden shortcuts

Do not:

- force T0 positive;
- open confirmation pathology early;
- change donor split after outcomes;
- use the tail 80-cell floor as eligibility;
- introduce Q_DEPTH/Q_DETECT QC thresholds;
- treat `NOT_ESTIMABLE` as PASS;
- copy 50k/3,292 mechanics constants into full-reader production values;
- use u40/u205 as biological-learning checkpoints;
- let operator-group size or triplet capacity determine scientific mass;
- let compute packing alter scientific sample weights;
- let an old branch name override main;
- delete unverified branch refs/tags;
- call a mechanics attack-suite PASS “training authority”;
- run TD60 or real D1 before a lawful full-reader learned teacher exists.

---

# 16. Recommended short-term milestone

A realistic near-term milestone is:

**PREEXECUTION_CLOSURE_PASS**

meaning all of the following are true:

- T0 three implementation STOPs externally closed;
- V5 base proposal/evidence/horizon/EMA authorities frozen;
- V5 GPU RNG parity + hardware calibration complete;
- final trainer binding complete;
- movement rule + predictor registry frozen;
- implementation verifier PASS;
- self-contained V5 package clean-room replay PASS;
- still **no biological training yet**.

Only then move to bounded mechanics qualification and later full-reader training.

---

# 17. Current authoritative project terminal

`STOP_JEPA_EXECUTION_AUTHORITIES_INCOMPLETE`

This is an engineering/governance STOP.

It is **not** a biological negative result.

The project remains scientifically viable:

- T0 science accepted but implementation blocked;
- donor-recurrent relational target exists;
- broad/mesoscale recurrence survives;
- V5 target and relational proposal are now substantially frozen;
- downstream D1 machinery exists but correctly waits for a lawful teacher.

Continue from main and close execution authority cleanly.
