# T0 → V5 EXPANDED CROSSWALK

Date: 2026-09-12
Status: `READ_ONLY_ORIENTATION__NO_DESIGN_CHANGE_NO_EXECUTION_NO_AUTHORITY_TRANSITION`
Supersedes: `docs/agent/T0_V5_ORIENTATION_AND_CROSSWALK_20260912.md` (`5e01e549`)

This is the §42 deliverable. It is read-only with respect to the systems under
review: nothing in V5 or T0 was modified, no S0–S4 step was executed, no
protected partition was opened, no training or optimizer path was run.

`5e01e549` is superseded rather than amended because it predates
`a68fb8a8`/`f7e61f34` on `planning/v5-dataset-first-production-closure-20260912`.
Those two commits close gaps that `5e01e549` reported as open, and its
experimental-unit row and its `G2` finding are both wrong at today's heads.

---

## 0. Evidence classes used throughout

Per `docs/agent/JEPA_REVIEW_EVIDENCE_PROMOTION_FAILURE_CONTRACT_20260911.md`,
every claim below carries one of:

| class | meaning here |
| --- | --- |
| `SOURCE_CODE_CONFIRMED` | I read the named file at the named commit and the stated behaviour follows from the code I read |
| `PRODUCER_CLAIM` | asserted by whoever produced the artifact (including me), not independently re-executed |
| `REVIEWER_REPRODUCED` | executed and reproduced by a reviewer other than the producer |
| `REAL_DATA_EVIDENCE` | measured on authenticated real data |
| `NOT_YET_VERIFIED` | stated somewhere, checked nowhere |

**Nothing in this document is `REVIEWER_REPRODUCED`.** No V5 test suite was
executed for this crosswalk. My own previously reported T0 counts — 128 tests /
0 skipped on the V21 executor, 50 mutations / 47 caught / 3 unreachable /
0 survived — remain `PRODUCER_CLAIM` and are cited as such.

---

## 1. Refs verified against the live remote

| ref | head | note |
| --- | --- | --- |
| `main` | `ba3f2a12` | matches supplied |
| `governance/integrated-target-discovery-v5-handoff-20260911` | `dac11696` | matches supplied |
| `planning/v5-dataset-first-production-closure-20260912` | **`f7e61f34`** | **moved** from the supplied `79feb8d6` |
| `repair/v5-installed-target-root-binding-20260912` | `bb974896` | matches supplied |
| `planning/v5-full-population-cheat-proofing-20260909` | `1de20b1c` | matches supplied |
| `t0/v20-pathology-blind-materialization-20260908` | `d5d67e21` | immutable, untouched |

The two commits added since the refs were supplied:

- `a68fb8a8` `feat(v5): add fail-closed base learning-step qualification validator`
  — `scripts/v5_anticheat/validate_base_learning_step_qualification_v1.py`, 155 lines
- `f7e61f34` `test(v5): red-team base learning-step qualification gate`
  — `tests/test_validate_base_learning_step_qualification_v1.py`, 120 lines, 11 cases

Evidence class: `SOURCE_CODE_CONFIRMED`.

---

## 2. Crosswalk

Rendered as one block per area rather than an eight-column table, which does not
survive at readable width. The field order is the requested schema.

---

### 2.1 Data authentication

- **V5 mechanism** — byte-digest binding of every substrate authority, with the
  full-population closure as a hard terminal.
- **Source** — `planning/v5-full-population-cheat-proofing-20260909 @ 1de20b1c`:
  `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`,
  `build_full_reader_expression_identity_closure_v3.py`,
  `bind_corrected_train_cache_v1.py`. Terminals in
  `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260911_CURRENT.json` @ `dac11696`.
- **Problem it solves** — a file that is present is not a file that is
  authoritative. Required terminal is
  `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`; the 4,726-row
  corrected TRAIN cache is explicitly barred from satisfying it
  (`TRAIN_CACHE_PASS_IS_NOT_FULL104_PASS`).
- **Authority class** — validators `SOURCE_CODE_CONFIRMED`; the closure itself is
  an open blocker, `STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`,
  class `NOT_YET_VERIFIED`.
- **T0 reuse unchanged?** — partially. The digest discipline transfers. The
  binders themselves do not: T0's authority root is a pathology CSV plus a donor
  role registry, not an expression block store.
- **AT8 adaptation required** — yes. T0 needs (a) a text-authority digest rule
  that is line-ending invariant, and (b) binding of the *endpoint column*
  identity inside an authenticated file, not just the file.
- **T0 lesson that tests it** — I bound the wrong pathology source. I assumed
  `data/raw/metadata/sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv`
  (`20c444d0…`); the frozen guard refused; the real authority was
  `data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv` (`ebbe9bc0…`).
  Separately, `t0_stage2b_discovery_at8_v1._raw_digest` hashes raw bytes while
  the repo checks text out with `core.autocrlf=true`, so a correct file can fail
  its own digest on a clean clone.
- **Remaining gap** — V5 has no line-ending-normalized digest rule for text
  authorities, and no column-level identity binding. **C.**

---

### 2.2 Experimental unit

- **V5 mechanism** — two layers. A **donor-uniform sampling estimand** enforced
  in code, and mandatory declaration of both analysis levels on the
  learning-step receipt.
- **Source** — sampling layer, `1de20b1c` / `f7e61f34`:
  `src/sea_ad_jepa/v5/data_first_geometry.py` defines the per-cell target
  probability by named mode, with `donor_uniform` = `1/(D·n_donor)` and
  `raise ValueError('unsupported scientific estimand; no default is permitted')`
  — there is no silent fallback;
  `src/sea_ad_jepa/v5/dimension_authority_guard_v{1,2,3}.py` refuse any receipt
  whose `estimand` is not `EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR` with
  `STOP_D_AUTHORITY_ESTIMAND_MISMATCH`;
  `scripts/v5_anticheat/derive_support_family_mass_v1.py` records the rule
  "weight family losses by expected eligible address mass under
  `p_i = 1/(D*n_donor)`, not raw cell frequency" and labels the raw-cell-mass
  contrast `DIAGNOSTIC_ONLY__RAW_CELL_MASS_IS_NOT_THE_DONOR_EQUAL_ESTIMAND`.
  Declaration layer, `a68fb8a8`:
  `scripts/v5_anticheat/validate_base_learning_step_qualification_v1.py`, the
  `analysis_level` block — `representation_observation_unit_missing`,
  `statistical_generalization_unit_missing`,
  `aggregation_sets_effective_n_without_estimand_justification`. Red-teamed at
  `f7e61f34` by `test_aggregation_that_sets_effective_n_requires_estimand_justification`.
  Prose requirement at `dac11696`,
  `JEPA_NEW_CHAT_HANDOFF_20260911_TARGET_DISCOVERY_V5_INTEGRATED_CURRENT.md` §8B.
- **Problem it solves** — the weighting half of the pseudoreplication failure,
  properly. A donor with many cells does not thereby acquire more influence:
  `p_i = 1/(D·n_donor)` makes cell mass irrelevant to donor weight, and the
  guards refuse any other estimand rather than defaulting. Many cells improve
  measurement of donor biology; they do not multiply independent donor-level
  pathology outcomes.
- **Authority class** — `SOURCE_CODE_CONFIRMED`. The red-team test is
  `PRODUCER_CLAIM` (read, not executed).
- **T0 reuse unchanged?** — yes, the receipt schema applies as written.
- **AT8 adaptation required** — the T0 receipt must declare
  `representation_observation_unit = cell`,
  `statistical_generalization_unit = donor`, and carry n = 46 donors
  (28 discovery / 18 spent / 12 sealed / 10 oracle), never 638,150 cells.
- **T0 lesson that tests it** — my claim that the design "throws away four
  orders of magnitude of sample size" and that statistics should move to where
  the dataset is large. AT8 is one value per donor; every cell of a donor
  inherits it. The recommendation pointed a successor design straight at
  pseudoreplication and was withdrawn.
- **Remaining gap** — the two layers between them cover weighting but not
  inference. The sampling estimand governs how much a donor's cells count
  *during exposure*; it says nothing about the sample size of a donor-level
  outcome in a downstream statistic. And the declaration layer checks that the
  units were *declared*, not that the computation *obeyed* them: a producer that
  writes `aggregation_sets_effective_n: false` passes with nothing checked, and
  `aggregation_justification` is free text. **B, upgraded from the C in
  `5e01e549`.**

---

### 2.3 Target characterization

- **V5 mechanism** — a hash-bound frozen target receipt that V5 must accept and
  cannot recompute.
- **Source** — `f7e61f34` / `bb974896`:
  `src/sea_ad_jepa/v5/qualified_teacher_target_receipt_v1.py`
  (`KIND = v5_qualified_teacher_target_receipt_v1`,
  `TARGET_KIND = t0_v21_target_freeze_receipt_v1`,
  `MODE = BOUNDED_QUALIFICATION_ONLY`,
  `STOP_V5_QUALIFIED_TARGET_RECEIPT_INVALID`);
  `scripts/v5_anticheat/full_reader_relational_target_preflight_v1.py`.
- **Problem it solves** — post hoc target substitution or redefinition after
  downstream evidence is seen.
- **Authority class** — `SOURCE_CODE_CONFIRMED` for the sealing/validation
  surface; the receipt contents for any real T0 target are `NOT_YET_VERIFIED`
  because no target has been frozen.
- **T0 reuse unchanged?** — yes as an identity carrier.
- **AT8 adaptation required** — yes, and this is the substantive one. The
  receipt binds *which* target; nothing requires a scientific characterization
  of *what* the target is.
- **T0 lesson that tests it** — AT8 percent-positive-area in grey matter is a
  right-skewed single-reader morphometric whose measurement reliability was never
  characterized in V20. Attenuation bounds any achievable correlation at roughly
  `ρ_observed ≈ ρ_true · √reliability`, so an uncharacterized endpoint silently
  caps the power calculation that depends on it.
- **Remaining gap** — no V5 requirement for endpoint distribution, dynamic
  range, reader/section/replicate variance, or floor/ceiling behaviour. **C.**

---

### 2.4 Measurement-model qualification

- **V5 mechanism** — same-cell counterfactual technical intervention plus a QC
  authority whose thresholds may only come from prospective or independent
  calibration.
- **Source** — `1de20b1c` / `f7e61f34`:
  `src/sea_ad_jepa/v5/same_cell_technical_intervention_probe_v1.py`,
  `same_cell_qc_bridge_v3.py`,
  `qc_qualification_authority_v3.py`
  (`_ALLOWED_THRESHOLD_PROVENANCE = {PROSPECTIVE_PREMODEL, INDEPENDENT_CALIBRATION}`),
  `docs/agent/V5_QC_MEASUREMENT_CONFOUNDING_GOVERNANCE_V1.md`.
- **Problem it solves** — the right question. Changing only the measurement
  process for the same cell must not change the biological conclusion. This
  avoids demanding independence between biology and observed QC, which would
  reject genuine activated or injured states.
- **Authority class** — `SOURCE_CODE_CONFIRMED`. The `_cosine_rows`
  zero-denominator defect — a zero norm on *either* row is reported as cosine
  1.0, so asymmetric `(nonzero, zero)` pairs pass — is `SOURCE_CODE_CONFIRMED`
  by the external reviewer at `1de20b1c`; its repair is `NOT_YET_VERIFIED`.
- **T0 reuse unchanged?** — for the predictor side, yes. For the endpoint, no:
  AT8 has no same-cell counterfactual. It is a stain on tissue, not a
  resampleable observation.
- **AT8 adaptation required** — yes. T0 needs an outcome-side reliability model,
  which is a different construction from the predictor-side intervention probe.
- **T0 lesson that tests it** — the V20 rare-tail QC veto. Tail membership
  derives from an expression score computed from the same raw counts that
  `Q_DETECT` summarises, and the two gate metrics are redundant (r = 0.9232;
  nuisance-design condition number rising ~310 → ~37,671 when both are
  appended). The conservative refusal was right, but the gate was built around
  two collinear readouts of one measurement process.
- **Remaining gap** — V5 qualifies the measurement of the *predictor*. Nothing
  qualifies the measurement of the *outcome*. **C.**

---

### 2.5 Candidate selection

- **V5 mechanism** — full-curve publication, boundary diagnosis before grid
  expansion, and dimension authority derived from production data.
- **Source** — `a68fb8a8`: `validate_base_learning_step_qualification_v1.py`
  (`winner_only_without_full_curve`,
  `boundary_selected_without_limiting_object_diagnosis`,
  `grid_expanded_before_boundary_diagnosis`); `f7e61f34`:
  `src/sea_ad_jepa/v5/dimension_authority_guard_v4.py`,
  `dimension_execution_firewall_v1.py`,
  `scripts/v5_anticheat/derive_full_stream_dimension_family_v1.py`.
- **Problem it solves** — publishing a winner without the curve it came from,
  and rescuing a boundary selection by widening the grid after seeing it.
- **Authority class** — `SOURCE_CODE_CONFIRMED`.
- **T0 reuse unchanged?** — yes. This is the cleanest direct transfer in the
  whole crosswalk.
- **AT8 adaptation required** — minimal. The T0 curve is the 17-point ridge grid
  over exponents −6.0…+2.0; the receipt must carry all 17 points.
- **T0 lesson that tests it** — V20 selected at index 16 of 17, the grid
  boundary, and published the winner alone. Under this validator V20 could not
  have been published: `boundary_selected_without_limiting_object_diagnosis`
  fires unless the limiting object is diagnosed first, and expanding the grid
  before that diagnosis is itself a refusal.
- **Remaining gap** — no V5 analogue of a declared deterministic tie rule. V20's
  frozen rule is `choices[-1]` within `tol = 1e-12·max(1,|minloss|)`, i.e. the
  largest exponent among near-ties. An undeclared tie rule is a silent degree of
  freedom. **C, narrow.**

---

### 2.6 Nuisance comparator

- **V5 mechanism** — three comparator classes are mandatory, and the limiting
  object must be published.
- **Source** — `a68fb8a8`:
  `REQUIRED_COMPARATOR_CLASSES = {NO_LEARNED_SIGNAL_OR_LIMITING_OBJECT,
  TECHNICAL_ONLY_OR_IDENTITY_ONLY, RANDOMIZED_OR_MATCHED_NULL}`, plus
  `limiting_or_null_comparator_not_published`. Related:
  `src/sea_ad_jepa/v5/relational_shortcut_increment_guard_v1.py`,
  `relational_shortcut_superiority_guard_v2.py` — learned relational biology
  must beat a frozen shortcut family.
- **Problem it solves** — the exact V20 failure. A model was reported as
  selected without the value its CV curve was descending toward.
- **Authority class** — `SOURCE_CODE_CONFIRMED`.
- **T0 reuse unchanged?** — yes.
- **AT8 adaptation required** — the T0 limiting object is the λ→∞ nuisance-only
  LOO comparator: V20's folds, per-fold nuisance refit, training-fold response
  standardization and squared-error loss, with the expression contribution set
  identically to zero.
- **T0 lesson that tests it** — measured, `REAL_DATA_EVIDENCE`:
  `L_∞ = 1.877862` against V20's best grid point `1.882992`, difference
  `−0.005130`. The selected model was *worse* than contributing nothing from
  expression. Two implementations agreed bitwise;
  `docs/agent/evidence/t0_v21_null_comparator_20260912.json`, producer
  `scripts/v4/t0_v21_null_comparator_probe_v1.py` (`7e4b25b5`).
- **Remaining gap** — the gate forces *disclosure* of the limiting object and a
  digest for it, but never compares the winner against it numerically. A
  receipt reporting `limiting_object_published: true` with a limiting loss below
  the winner's still passes. Disclosure would have caught V20; it does not by
  itself force the decision. **B.** (`5e01e549` recorded this as gap `G2`,
  entirely open. That is now wrong.)

---

### 2.7 Nested donor validation

- **V5 mechanism** — none executable. Requirement stated in prose.
- **Source** — `dac11696`,
  `JEPA_NEW_CHAT_HANDOFF_20260911_TARGET_DISCOVERY_V5_INTEGRATED_CURRENT.md` §8G:
  for each of 28 outer folds, model selection must see only the other 27 donors,
  with inner donor-level CV, and exactly one OOF prediction per held-out donor.
- **Problem it solves** — stated, not solved.
- **Authority class** — `NOT_YET_VERIFIED`; the state file's own permanent rule
  `PROSE_DESIGN_CLOSURE_IS_NOT_EXECUTABLE_CLOSURE` applies to it.
- **T0 reuse unchanged?** — inverted. T0 is the side that has the executable
  artifact; V5 is the side that needs it.
- **AT8 adaptation required** — none; the T0 implementation already matches the
  V5 prose.
- **T0 lesson that tests it** — `scripts/v4/t0_v21_selection_and_power_v1.py`
  carries one canonical `validate_cross_fit_structure` called by both
  `seal_cross_fit` and `verify_cross_fit_artifact`, enforcing 28 outer LODO
  predictions with every donor held out exactly once, ridge selection nested
  strictly inside each 27-donor training fold, and exactly one HC3 regression
  over the assembled 28 OOF rows with df = 28 − 5 = 23. Its 128 tests / 0
  skipped and 50-mutation audit are `PRODUCER_CLAIM`.
- **Remaining gap** — V5 cannot refuse a forged or mis-nested cross-fit
  artifact. It has no validator for one. **C.**

---

### 2.8 Influence / stability

- **V5 mechanism** — none executable. Prose at §8K: "A target driven by one or
  two donors is not adequate merely because aggregate cell counts are large."
- **Source** — `dac11696`, §8K.
- **Problem it solves** — stated, not solved.
- **Authority class** — `NOT_YET_VERIFIED`.
- **T0 reuse unchanged?** — inverted again; T0 holds the machinery (28
  leave-one-donor influence refits, directional consistency with
  `STOP_EFFECT_DIRECTION_NOT_CONSISTENT`, jackknife lower envelope).
- **AT8 adaptation required** — none.
- **T0 lesson that tests it** — this is where the V20 question actually became
  undecidable, and it is `REAL_DATA_EVIDENCE`. In the L_∞ fold losses the single
  largest donor contributes 33.5% of the total and the top three contribute
  58.6%; median/mean = 0.47; the leave-one-out range 1.2954–1.9474 contains
  1.882992; and removing the top donor moves the comparison by a factor of 114.
  The verdict was `UNRESOLVED`, not "V20 failed" — and it was influence
  analysis, not the point estimate, that established that.
- **Remaining gap** — V5 has no influence or stability requirement it can
  enforce, and no rule about what an influence-dominated result licenses. **C.**

---

### 2.9 Effective complexity

- **V5 mechanism** — a named capacity diagnostic whose threshold must be
  production-derived, with a hard ban on importing T0's number.
- **Source** — `a68fb8a8`, the `effective_capacity` block:
  `effective_capacity_diagnostic_missing`,
  `threshold_authority == PRODUCTION_DERIVED_OR_MODEL_DEFINED`,
  `t0_numeric_threshold_import_forbidden`. Red-teamed at `f7e61f34` by
  `test_t0_numeric_capacity_threshold_cannot_be_imported`.
- **Problem it solves** — a historical number becoming a production constant.
  This is the standing project rule — dataset geometry determines scale-sensitive
  parameters; outcomes must not — enforced in code.
- **Authority class** — `SOURCE_CODE_CONFIRMED`.
- **T0 reuse unchanged?** — yes, and it correctly *refuses* the T0 number.
- **AT8 adaptation required** — T0 must publish its own capacity diagnostic
  rather than reusing V5's, and must not export its value as a threshold.
- **T0 lesson that tests it** — `edf = Σdᵢ/(dᵢ+λ) ≤ trace/λ = n/10^e = 28/100
  = 0.28`, verified across spectra (measured 0.24–0.28), assumption-free. The
  correction that matters: this describes *the fitted V20 solution at its
  selected λ*. It says nothing about the intrinsic dimensionality of the true
  biological signal, and `p ≫ n` by itself does not preclude learning. The
  import ban is precisely the right response to a number with that narrow scope.
- **Remaining gap** — `diagnostic_name` is any non-empty string. The gate
  requires that a diagnostic be named and that its threshold have the right
  provenance; it does not constrain what the diagnostic is or recompute it.
  **B.**

---

### 2.10 Anti-cheat

- **V5 mechanism** — schema-level representation firewall, collapse guard,
  relational shortcut guards, and a recorded measurement-shortcut attack set.
- **Source** — `1de20b1c` / `f7e61f34`:
  `src/sea_ad_jepa/v5/representation_firewall_v2.py`
  (`FORBIDDEN_DIRECT_MODEL_FIELDS`, `ALLOWED_DIRECT_Z_BIO_FIELDS`,
  `EXPECTED_OBJECTIVE_GRADIENT_TARGETS`, `validate_routing_manifest_v2`),
  `representation_collapse_guard_v1.py`,
  `relational_shortcut_increment_guard_v1.py`,
  `relational_shortcut_superiority_guard_v2.py`,
  `target_discovery/independent_checks/20260909_measurement_shortcut_attack/`
  (`TD57B`, `TD59`).
- **Problem it solves** — donor / specimen / batch / library / dataset / row-ID
  / label / depth fields reaching the backbone representation interface.
- **Authority class** — `SOURCE_CODE_CONFIRMED` for the schema firewall; the
  empirical nuisance-recovery attack suite is `NOT_YET_VERIFIED` and recorded as
  open in the handoff state (`nuisance_recovery_attack_suite_closed: false`).
- **T0 reuse unchanged?** — partially. The field ban transfers; the shortcut
  guards are about relational training, not target discovery.
- **AT8 adaptation required** — yes. T0's dominant shortcut risk is different in
  kind: the V21 broad target is *AT8-supervised inside the 28 discovery donors*.
  That is legitimate, but §8D is explicit that it must not then be described as
  pathology-blind.
- **T0 lesson that tests it** — the frozen V20 state is
  `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL` with
  `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`, i.e. an internally supported claim,
  not an externally confirmed one. Conflating the two is the shortcut that
  matters here.
- **Remaining gap** — the external review's finding stands: expression itself
  can encode donor, library, batch, source and depth structure, and a
  nuisance-rich representation can be noncollapsed and still pass a schema
  firewall. Donor-held-out nuisance-recovery attacks are required and not
  closed. **B.**

---

### 2.11 Negative controls

- **V5 mechanism** — controls as first-class immutable artifacts, plus a JUnit
  execution guard that refuses empty, missing or skipped critical tests.
- **Source** — `1de20b1c` / `f7e61f34`:
  `src/sea_ad_jepa/v5/rejection_gate_power_calibration_v3.py`
  (`_CONTROL_SIDES = ("valid","invalid")`, provenance restricted to
  `PROSPECTIVE_PREMODEL` / `INDEPENDENT_CALIBRATION`);
  `src/sea_ad_jepa/v5/critical_test_execution_guard_v1.py`
  (`STOP_CRITICAL_TEST_AUTHORITY_EMPTY`, `STOP_CRITICAL_TEST_MISSING`,
  `STOP_CRITICAL_TEST_SKIPPED`, `STOP_CRITICAL_TEST_DUPLICATE`);
  `scripts/v5_anticheat/validate_v5_critical_test_execution_v1.py`. Families and
  required bindings enumerated in the handoff state at `dac11696`.
- **Problem it solves** — two things. Controls that are not immutable artifacts,
  and suites that report success without having run.
- **Authority class** — `SOURCE_CODE_CONFIRMED`.
- **T0 reuse unchanged?** — yes; the JUnit guard is directly reusable by T0.
- **AT8 adaptation required** — T0's control families differ: permutation of AT8
  across donors, nuisance-only limiting object, technical-only predictors,
  random-gene modules.
- **T0 lesson that tests it** — my own vacuous sensitivity check. The guard file
  did not exist on the branch under test, pytest collected nothing, and the run
  **exited 0**. `validate_junit_critical_tests` closes exactly that: it matches
  an expected-ID list, raises `STOP_CRITICAL_TEST_AUTHORITY_EMPTY` on an empty
  expectation set, `STOP_CRITICAL_TEST_MISSING` on any expected ID absent from
  the report, and `STOP_CRITICAL_TEST_SKIPPED` on any skip at all.
- **Remaining gap** — the confirmed external-review finding on
  `rejection_gate_power_calibration_v3`: it validates report-level booleans such
  as `gate_rejects_invalid_control` and `used_actual_frozen_gate` rather than
  necessarily recomputing the verdict from raw control outputs, which is
  self-attestation. **B.**

---

### 2.12 Protected confirmation firewall

- **V5 mechanism** — the learning-step receipt refuses any protected access, and
  cannot claim training authority.
- **Source** — `a68fb8a8`, the `access` block:
  `forbidden_protected_or_endpoint_access` on any of
  `protected_partition_used`, `pathology_used`, `confirmation_endpoint_used`;
  `receipt_must_not_claim_training_authority`. Red-teamed at `f7e61f34`.
  Governance: `IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`.
- **Problem it solves** — a discovery-stage receipt silently carrying protected
  reads.
- **Authority class** — `SOURCE_CODE_CONFIRMED`.
- **T0 reuse unchanged?** — yes, and T0 additionally has real enforcement rather
  than declaration.
- **AT8 adaptation required** — none. `t0_stage2b_discovery_at8_v1.load_role_numeric_at8`
  already skips confirmation rows *before* their values are touched, refuses any
  donor outside the frozen set, refuses unless the loaded set reproduces the
  frozen donor-set digest, and reports
  `confirmation_rows_present_and_skipped` alongside
  `confirmation_numeric_at8_accessed`.
- **T0 lesson that tests it** — the L_∞ measurement ran against real AT8 and
  reproduced V20's frozen `endpoint_values_sha256`
  (`4cfb5727…`) while the 12 protected donors stayed closed. That is the
  firewall working under load. The standing corollary also applies: the 18
  "spent" development donors already informed method development and are
  therefore no longer a valid holdout.
- **Remaining gap** — V5's access block is self-declared booleans with nothing
  behind them; the enforcement lives on the T0 side. **A on the T0 side, B on
  the V5 side.**

---

### 2.13 Authority roots

- **V5 mechanism** — a single current-authority index, a supersession map, a
  latest-handoff pointer, and an installed-target-root binding with its own
  regression test.
- **Source** — `bb974896` (`repair/v5-installed-target-root-binding-20260912`):
  `tests/test_v5_installed_target_root_binding_v1.py`,
  `tests/test_v5_guard_wrong_cursor_v1.py`; `f7e61f34`:
  `docs/agent/CURRENT_AUTHORITY_INDEX.md`,
  `docs/agent/CURRENT_SUPERSESSION_MAP.md`,
  `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`, `START_HERE.md`.
- **Problem it solves** — branch names do not confer scientific authority, and
  the target root actually installed at runtime must be the frozen one.
- **Authority class** — `SOURCE_CODE_CONFIRMED` for the file inventory;
  `NOT_YET_VERIFIED` for behaviour, since neither test was executed here.
- **T0 reuse unchanged?** — the pattern, yes.
- **AT8 adaptation required** — T0's roots are the pathology source, the donor
  role registry, the age/sex registry and the frozen V20 module tree.
- **T0 lesson that tests it** — `9f98320f` on the V21 lane truncated
  `t0_v21_authority_v1.py`, deleting every `seal_*` function, four `validate_*`
  functions and `decision_capable_power_gate`. **18 of its own 22 tests fail on
  its own head.** A head can be self-inconsistent and still look like authority
  from the outside. Separately, `stage2a._frozen` once resolved `FROZEN_V20` to
  a session scratchpad directory: the suite was green and would have failed on
  any clone.
- **Remaining gap** — two. Nothing in V5 runs an authority root's own test suite
  at its own head before treating it as a root; and nothing checks that a
  validator resolves its dependencies inside the tracked tree rather than an
  ambient path. **B.**

---

### 2.14 Artifact identity

- **V5 mechanism** — canonical-JSON sealing with parent digests, plus mandatory
  evidence digests on the learning-step receipt.
- **Source** — `f7e61f34`: `src/sea_ad_jepa/v5/artifact_binding_v1.py`
  (`canonical_json_bytes`, `artifact_sha256`, `seal_artifact(schema, payload,
  parent_sha256)`, `validate_artifact`), `tests/test_artifact_binding_v1.py`;
  `a68fb8a8`: required `evidence_sha256` keys `full_curve`, `comparators`,
  `capacity`, `geometry`, `negative_controls`, each validated against
  `^[0-9a-f]{64}$`. Red-teamed at `f7e61f34` by
  `test_missing_evidence_digest_is_rejected`.
- **Problem it solves** — evidence referenced by prose rather than by digest,
  and lineage that cannot be walked backwards.
- **Authority class** — `SOURCE_CODE_CONFIRMED`.
- **T0 reuse unchanged?** — yes, for JSON artifacts. This is a clean transfer.
- **AT8 adaptation required** — T0's evidence set maps onto the five keys
  directly: 17-point ridge curve, L_∞ comparator, capacity diagnostic, donor
  geometry, permutation controls.
- **T0 lesson that tests it** — the CRLF hazard again, from the other side:
  `_git_blob_sha` hashed worktree bytes (34,463) rather than blob bytes
  (33,824). Canonical-JSON sealing is immune to this; raw text digests are not.
- **Remaining gap** — `artifact_binding_v1` canonicalizes JSON only. The text
  and CSV authorities that T0 actually depends on are outside its coverage, which
  is the same gap as §2.1. **B.**

---

### 2.15 Transport

- **V5 mechanism** — **none.**
- **Source** — no file. I searched `src/sea_ad_jepa/v5` and
  `scripts/v5_anticheat` across `1de20b1c`, `bb974896` and `f7e61f34` for
  `transport`, `estimand`, `noncentral`, `partial_correlation` and
  `detectable_effect`. Every `transport` hit is **file** transport — a
  hash-locked discovery archive in `run_real_data_smoke_non_authority_v1.py` —
  and every `estimand` hit is the **sampling** estimand of §2.2
  (`EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR`, `p_i = 1/(D·n_donor)`), which governs
  exposure weighting, not the carriage of an effect magnitude across designs.
  `noncentral`, `partial_correlation` and `detectable_effect` do not occur at
  all. There is no mechanism governing the transport of an effect measured under
  one design to a different design or n.
- **Problem it solves** — nothing, because nothing addresses it.
- **Authority class** — not applicable.
- **T0 reuse unchanged?** — no; T0 must supply this itself, and currently does so
  by refusing.
- **AT8 adaptation required** — the entire mechanism.
- **T0 lesson that tests it** — this is the sharpest one. The V21 executor sets
  `EFFECT_TRANSPORT_STATUS = "OPEN"`, its `power_gate` fails closed with
  `STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND`, its
  `planning_power_projection` deliberately returns **no** `clears_gate` key, and
  `FORBIDDEN_TRANSPORT_BASES` names four bases that must never carry an effect
  across designs: `assembled_hc3_t_over_sqrt_n`,
  `whole_pipeline_permutation_significance`, `observed_null_sd_correction`,
  `measured_null_spread_rescaling`. The reason each is forbidden is measured:
  `t/√n` is n-dependent and design-dependent; the cross-fit null SD ratios are
  1.304 (fixed ridge) and 1.477 (inner selection), so a "correction factor" read
  off the measured null spread is a free parameter, not an estimand. The
  candidate that survives is a partial correlation `ρ = Corr(ỹ, s̃)` — n-free,
  scale-invariant, carrying no standard error of its own.
  A related trap is documented in the same executor: the sample identity
  `t = r√(n−p_Z−1)/√(1−r²)` is not the population noncentrality
  `λ = ρ√(n−p_Z)/√(1−ρ²)`, and conflating them inflates by
  `√(24/23) = 1.021`.
- **Remaining gap** — everything. **C, and the most consequential C in this
  document.**

---

### 2.16 Power

- **V5 mechanism** — `rejection_gate_power_calibration_v3` measures the power of
  an *anti-cheat gate* to reject invalid controls. There is no V5 mechanism for
  the *scientific* power to detect a biological effect at a given confirmation n.
- **Source** — `1de20b1c`:
  `src/sea_ad_jepa/v5/rejection_gate_power_calibration_v{1,2,3}.py`.
- **Problem it solves** — gate sensitivity. Not study power. The two share a
  word and nothing else.
- **Authority class** — `SOURCE_CODE_CONFIRMED` for what it is; the handoff
  state records `rejection_power_independent_execution_evidence_closed: false`.
- **T0 reuse unchanged?** — no. Different quantity.
- **AT8 adaptation required** — all of it.
- **T0 lesson that tests it** — measured, and decisive.
  For 80% power at the frozen n = 12 confirmation cohort, the required
  correlation is **ρ ≥ 0.7563** under the current design, **0.6643** with the
  nuisance frozen, and **0.6083** at α = 0.05 with frozen nuisance. The V20
  anchor is **ρ ≈ 0.481**. The required n at that anchor is **22 to 33**.
  Freezing the nuisance design moves type I from 0.0455 against a nominal 0.050
  while lifting power 0.269 → 0.554 — real, and still not enough. A related
  geometry constraint: `P(a fresh 12 has ≤1 minority-sex donor) = 0.060`, and at
  1/11 the HC3 leverage for that donor is exactly 1.0000, which is why the
  confirmation sex-minority grid starts at 2.
  The governing lesson is about *when*: this arithmetic must be run at the
  design stage, against the frozen confirmation cohort, before the work — not
  discovered afterwards.
- **Remaining gap** — no V5 requirement that a design declare its detectable
  effect size at its actual confirmation n before the confirmation set is
  opened. **C.**

---

### 2.17 Training authorization

- **V5 mechanism** — a resident deny-by-default optimizer guard bound to a
  verified target receipt, behind a fail-closed pre-execution dependency
  contract.
- **Source** — `f7e61f34` and `bb974896` (byte-identical on both lanes):
  `src/sea_ad_jepa/v5/qualified_optimizer_guard_v1.py`
  (`QualifiedOptimizerStepGuard`, `STOP_V5_OPTIMIZER_TARGET_AUTHORITY_NOT_ARMED`,
  `CURSOR_KWARG = "v5_guard_schedule_cursor"`, `arm_for_step`,
  `disarm_uncompleted_step`, `_pre_step` / `_post_step` hooks,
  `assert_step_completed`, `install_qualified_optimizer_guard`);
  `trainer_preexecution_contract_v4.py`, `preexecution_dependency_guard_v1.py`,
  `postqualification_dependency_guard_v1.py`,
  `pretraining_qualification_bundle_v1.py`. Also `a68fb8a8`: the learning-step
  receipt returns `td60_authorized: false`,
  `relational_target_activation_authorized: false`, `training_authorized: false`
  even on `PASS`.
- **Problem it solves** — a parameter update happening without a current,
  hash-bound authorization tied to the frozen target.
- **Authority class** — `SOURCE_CODE_CONFIRMED`.
- **T0 reuse unchanged?** — not applicable; T0 does not train.
- **AT8 adaptation required** — none.
- **T0 lesson that tests it** — my own CUDA red-team of this guard. Unarmed
  direct and AMP steps were both refused with parameters **and** optimizer state
  unchanged, but I found two residual holes: an **AMP-skipped step left the
  authorization live**, and nothing bound the teacher target actually in use.
  **The first is now closed.** `arm_for_step` requires the cursor to be
  re-presented at step time through the private kwarg, and its docstring names
  the exact case: "prevents an authorization left live by an AMP skipped step
  from being consumed by a later ordinary optimizer step that did not present
  the current schedule cursor." `disarm_uncompleted_step` gives the trainer an
  explicit clearing path. A mismatched cursor disarms rather than merely
  refusing.
- **Remaining gap** — the second hole is narrowed but not proven closed. The
  guard binds `receipt_digest` and `target_package_root` at install time, so a
  step cannot proceed under an unverified receipt; nothing yet demonstrates that
  the tensor actually consumed as the teacher target is the artifact that
  receipt names. The handoff state still records
  `optimizer_path_non_bypassability_proven: false`. **B, upgraded from C.**

---

## 3. T0 lessons classified against V5

A = V5 already prevents this. B = V5 partly prevents this. C = V5 currently does
not prevent this. Every `C` is a V5 framework finding and is **not** patched
here.

| # | T0 lesson | class | V5 mechanism, or absence |
| --- | --- | --- | --- |
| 1 | A winner was published without the limiting object its curve descended toward (`L_∞ = 1.877862` vs `1.882992`) | **A** | `NO_LEARNED_SIGNAL_OR_LIMITING_OBJECT` + `limiting_object_published` (`a68fb8a8`) |
| 2 | Selection sat at the grid boundary (index 16 of 17) and was published anyway | **A** | `boundary_selected_without_limiting_object_diagnosis`, `grid_expanded_before_boundary_diagnosis` |
| 3 | A winner was published without its full curve | **A** | `winner_only_without_full_curve` |
| 4 | Toy simulation geometry (G = 12, p/n ≈ 0.43) used to reason about a real design (p/n ≈ 875) | **A** | `toy_geometry_cannot_be_production_authority`, `production_matched_simulation_or_adversarial_geometry`, exact FULL104 geometry match |
| 5 | A negative learning result read as "the biology is absent" | **A** | `failure_semantics_must_not_claim_biological_null`; `t0_role` must be `METHODOLOGICAL_EVIDENCE_ONLY__NOT_BIOLOGICAL_TARGET` |
| 6 | A T0 numeric threshold (`edf ≤ 0.28`) becoming a production constant | **A** | `t0_numeric_threshold_import_forbidden` |
| 7 | A sensitivity test collected nothing and exited 0 | **A** | `STOP_CRITICAL_TEST_AUTHORITY_EMPTY` / `_MISSING` / `_SKIPPED` in `critical_test_execution_guard_v1` |
| 8 | An AMP-skipped step left the optimizer authorization live | **A** | cursor must be re-presented at step time; `disarm_uncompleted_step` (`qualified_optimizer_guard_v1`) |
| 9 | A design document treated as a runnable implementation | **A** | permanent rule `PROSE_DESIGN_CLOSURE_IS_NOT_EXECUTABLE_CLOSURE`; blocker chain requires implementation + adversarial test |
| 10 | Protected confirmation values read during discovery | **A** (T0 side) / **B** (V5 side) | T0 loader enforces; V5 `access` block is self-declared booleans |
| 11 | Cells treated as independent donor-level outcome observations | **B** | donor-uniform sampling estimand `p_i = 1/(D·n_donor)` is enforced with `STOP_D_AUTHORITY_ESTIMAND_MISMATCH` and no default, which fixes *weighting*; the declaration layer covers *inference* only by assertion |
| 12 | The winner must actually beat the limiting object | **B** | disclosure is forced; the numerical comparison is not |
| 13 | A capacity diagnostic must be a real diagnostic | **B** | name and threshold provenance required; content unconstrained, never recomputed |
| 14 | Nuisance recovered as a learned proxy rather than a forbidden column | **B** | schema firewall blocks columns; donor-held-out recovery attacks not closed |
| 15 | Control evidence attested in a report rather than recomputed | **B** | `rejection_gate_power_calibration_v3` accepts report-level booleans |
| 16 | An authority head whose own tests fail on itself (`9f98320f`: 18 of 22) | **B** | installed-root binding exists; nothing runs a root's own suite at its own head |
| 17 | The teacher target actually consumed may not be the one the receipt names | **B** | receipt digest and package root bound at install; tensor-level binding unproven |
| 18 | Digest authority for text artifacts under CRLF checkout | **B** | canonical JSON sealing is immune; text/CSV authorities are outside its coverage |
| 19 | A holdout that informed method development is no longer a holdout (the 18 spent donors) | **B** | donor hierarchy is governance prose; no mechanism tracks which partitions have been spent |
| 20 | Effect transport across designs and n | **C** | no V5 mechanism exists |
| 21 | Scientific power at the actual confirmation n, declared before opening it | **C** | `rejection_gate_power_calibration` is gate power, a different quantity |
| 22 | Nested LODO structure; one HC3 after assembly, never one per fold | **C** | prose at §8G only; no validator, no forgery refusal |
| 23 | Influence and stability (top donor 33.5%, removing it moves the comparison 114×) | **C** | prose at §8K only; nothing enforceable |
| 24 | Endpoint measurement reliability and attenuation | **C** | V5 qualifies the predictor's measurement, never the outcome's |
| 25 | Endpoint *column* identity inside an authenticated file | **C** | file-level digests only |
| 26 | A declared deterministic tie rule in selection (`choices[-1]`, tol `1e-12`) | **C** | no V5 analogue |
| 27 | A validator resolving its dependencies to an ambient path outside the tracked tree | **C** | no portability check anywhere in V5 |

Count: **10 A, 9 B, 8 C.** Against `5e01e549` this is +4 A and −5 C, almost
entirely attributable to `a68fb8a8` and `f7e61f34`.

---

## 4. The eight V5 framework findings, consolidated

Recorded, not patched, per §42.

- **F1 (transport)** — no mechanism, and nothing prevents an n-dependent
  statistic being carried across designs. Highest consequence; T0 currently
  compensates by refusing.
- **F2 (scientific power)** — no requirement to declare a detectable effect size
  at the real confirmation n before opening it.
- **F3 (nested validation)** — the §8G requirement has no executable validator;
  a forged or mis-nested cross-fit artifact cannot be refused.
- **F4 (influence/stability)** — the §8K requirement is unenforceable, though
  influence analysis is what decided the V20 question.
- **F5 (outcome measurement model)** — measurement qualification covers the
  predictor only.
- **F6 (column identity)** — authentication stops at the file.
- **F7 (tie rule)** — an undeclared tie rule is a silent degree of freedom in
  selection.
- **F8 (portability)** — nothing checks that a validator resolves inside the
  tracked tree.

F3, F4 and F7 are the unusual ones: T0 holds executable machinery that V5 lacks,
so the transfer runs T0 → V5 rather than the reverse.

---

## 5. Two observations from reading the heads

**5.1 The two V5 lanes have diverged and neither carries the union.**
`repair/v5-installed-target-root-binding-20260912 @ bb974896` carries
`tests/test_v5_installed_target_root_binding_v1.py` and
`tests/test_v5_guard_wrong_cursor_v1.py`, which
`planning/v5-dataset-first-production-closure-20260912 @ f7e61f34` does not.
The closure lane carries six tests the repair lane does not
(`test_artifact_binding_v1`, `test_derive_full_stream_dimension_family_v1`,
`test_dimension_metric_artifact_v1`,
`test_full104_binding_dimension_interface_v1`,
`test_full_reader_relational_target_preflight_v1`,
`test_validate_base_learning_step_qualification_v1`).

This matters specifically because `qualified_optimizer_guard_v1.py` is
**byte-identical on both lanes**, yet `test_v5_guard_wrong_cursor_v1.py` — the
regression test for the cursor mechanism that closes the AMP-skip hole — exists
only on the repair lane. The closure lane ships the fix without its test.
Evidence class: `SOURCE_CODE_CONFIRMED`.

**5.2 The new validator is a direct encoding of the T0 postmortem.**
`validate_base_learning_step_qualification_v1.py` reads as though written
against the T0 findings: the limiting-object comparator (F on the old list),
boundary diagnosis before grid expansion, the observation-unit /
generalization-unit split, the ban on importing T0's capacity number, the ban on
toy geometry as authority, and the requirement that failure semantics say
`LEARNING_DESIGN_NOT_ESTABLISHED__NOT_BIOLOGY_ABSENT`. Six of the ten `A`
classifications above rest on this one 155-line file. That concentration is
itself worth noting: it has never been executed by a reviewer, and its red-team
suite is `PRODUCER_CLAIM`.

---

## 6. What this deliverable did not do

- No V5 file was modified. No `C` finding was patched.
- No test suite was executed; nothing here is `REVIEWER_REPRODUCED`.
- No S0–S4 step, power gate, reader-validation, oracle or partition was opened.
- No training, optimizer step, checkpoint or EMA update was run.
- V20 remains immutable at `d5d67e21`. Fresh-12 and reader-oracle remain sealed.
- Authority state is unchanged: `S0_S4_SELECTION_AUTHORIZED = FALSE`,
  `FRESH_READER_VALIDATION_OPEN_AUTHORIZED = FALSE`,
  `READER_ORACLE_OPEN_AUTHORIZED = FALSE`,
  `V5_PRODUCTION_TRAINING_AUTHORIZED = FALSE`. Training remains OFF.
