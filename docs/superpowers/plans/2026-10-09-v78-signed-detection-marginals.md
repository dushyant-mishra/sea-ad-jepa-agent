# V78 Signed Detection + Marginal Repair Implementation Plan

> **Execution method:** native/current-session execution under RED→GREEN TDD. No subagent or parallel implementation lane is authorized for this plan.

**Goal:** Implement and prospectively evaluate F0–F3 without mutating the proven V77 E0–E3 implementation in place: reproduce E2, test existing BackgroundV2 as an ablation, add an isolated signed detection-propensity field, then add pathology-blind rank-scrubbed count/depth marginals.

**Base:** `f3a5d142d3e02b0650d6f52ef97a11232e0a4dc7`

**Spec:** `docs/superpowers/specs/2026-10-08-v78-signed-detection-marginals-design.md`

## Global constraints

- E2 remains the biological baseline; class scale stays exactly `0.55`.
- F0/F2/F3 use background `v1`; F1 changes only background to the existing unmodified `BackgroundV2`.
- Generator and measurement seed stay `7302` for the first tournament.
- New streams are restricted to membership `12000–12999`, cell factors `13000–13999`, abundance permutation `14000`, and optional marginal jitter `14100–14199`.
- Preserve structural support, 42-operator geometry, class allocation, q/provenance/runtime boundaries, and the exact 14,417-address corrected evaluation universe.
- Real gene identity/program membership may not enter F2/F3 synthetic content. Corrected TRAIN may feed only compact pathology-blind geometric authorities.
- S159 remains descriptive/non-binary. No post-outcome magnitude search.
- E4, JEPA training, optimizer/EMA/runtime changes, TEST/Morabito, 500K, Stage4, target/representation freeze, and 353-ID repair remain unauthorized.

---

## Task 1 — Freeze F0 reproduction and F1 background-only ablation

**Create:**
- `tests/test_v78_signed_detection_marginals_v1.py`
- `scripts/v77/run_v78_signed_detection_marginal_tournament.py`

**Reuse without modifying:**
- `scripts/v77/build_v77_class_aware_truth.py`
- `scripts/v77/build_v77_class_aware_fullscale_rna_observer.py`
- `scripts/v77/v77_background_v2.py`
- `scripts/v77/v77_matched_scoring.py`
- `results/v77/V77_CLASS_PROPAGATION_TOURNAMENT_V1.json`
- `results/v77/V77_CLASS_PROPAGATION_SCIENTIFIC_RULING_V1.json`

### RED

- [ ] Assert `ARMS == ("F0", "F1", "F2", "F3")`; reject `E4` and unknown arms.
- [ ] Assert F0 is bound to committed E2 reference, seed `7302`, class scale `0.55`, background `v1`, exact class-authority SHA, registry SHA and evaluation-universe SHA.
- [ ] Assert missing/mismatched E2 reference blocks F0.
- [ ] Assert F1 differs from F0 only by background selection `v1 -> v2`; class truth, class scale, seeds and measurement configuration remain identical.
- [ ] Assert the existing BackgroundV2 constants are inherited, not copied or retuned.
- [ ] Assert 2K support remains 42/42 operators with minimum support >=1.

Run:
`pytest -q tests/test_v78_signed_detection_marginals_v1.py -k 'f0 or f1 or support'`

Expected RED: V78 runner does not yet exist.

### GREEN

- [ ] Implement a thin V78 runner that calls the existing class-aware truth path with arm E2 for every F arm.
- [ ] F0 calls the existing full-scale class-aware observer unchanged with background `v1`.
- [ ] F1 uses a V78 successor observer hook that allows existing `BackgroundV2` while retaining the same E2 class contribution; do not relax the historical E0–E3 observer's background guard.
- [ ] Add exact score-object comparison against committed E2 for F0.
- [ ] Run Task 1 tests to GREEN and re-run the existing V77 focused tests.

Commit milestone: `test(v78): freeze F0 reproduction and F1 ablation`

---

## Task 2 — Add isolated signed detection-propensity mechanics (F2)

**Create:**
- `scripts/v77/v78_signed_detection.py`
- `scripts/v77/build_v78_fullscale_rna_observer.py`

**Modify:**
- `tests/test_v78_signed_detection_marginals_v1.py`

**Do not modify:** `build_v77_fullscale_rna_observer_v2.py` or the V77 class-aware observer. V78 must wrap/reuse them.

### Interfaces

`v78_signed_detection.py`:
- `loading_matrix(seed: int, n_addresses: int) -> np.ndarray`
- `cell_factors(seed: int, global_cell_index: np.ndarray) -> np.ndarray`
- `field(seed: int, global_cell_index: np.ndarray, n_addresses: int) -> np.ndarray`
- `summary() -> dict`

`build_v78_fullscale_rna_observer.py`:
- separate `selection_score` from positive-count `weight_rel`;
- F0/F1 pass zero signed field;
- F2/F3 pass signed field;
- positive-count allocation remains based on biological `rel` unless F3 supplies rank-scrubbed abundance weights.

### RED

- [ ] Prove current V77 `sparse_counts` selection is `log(rel) + Gumbel` and has no independent detection field.
- [ ] Assert factor geometry exactly inherits BackgroundV2 broad/mid/narrow counts, fractions and scales; exclude paralog factors.
- [ ] Assert each factor has both positive and negative support, sign counts differ by <=1, selected-support mean is ~0, and RMS equals the frozen family scale.
- [ ] Assert membership/signs are deterministic and invariant to shard partition.
- [ ] Assert changing symbol/Ensembl/biotype metadata cannot change loadings.
- [ ] Assert F2 field accepts only seed/global cell identity/canonical position; donor/source/operator/class/pathology/query changes cannot alter it.
- [ ] Assert F2 and F0 produce identical pre-selection `eta`, `rel`, support mask, `library_target`, and `detected_target` for matched cells.
- [ ] Assert F2 preserves exact per-cell detected-feature totals and library totals while permitting selected identities to differ.

Run:
`pytest -q tests/test_v78_signed_detection_marginals_v1.py -k 'signed or f2 or isolation'`

Expected RED: new signed module/successor observer absent.

### GREEN

- [ ] Implement deterministic factor membership in streams `12000–12999`.
- [ ] Implement cell factors in streams `13000–13999` keyed only by global cell identity.
- [ ] Refactor selection/allocation only in the V78 successor: `score = log(rel) + signed_field + identical Gumbel`; allocate positive counts from `weight_rel`.
- [ ] Emit factor geometry, signs policy and stream identities in the observable manifest.
- [ ] Run Task 2 tests GREEN, then all Task 1/2 tests and V77 spillover tests.

Commit milestone: `feat(v78): separate signed detection selection`

---

## Task 3 — Build pathology-blind F3 marginal authorities

**Create:**
- `scripts/v77/build_v78_marginal_authority.py`
- `tests/test_v78_marginal_authority_v1.py`
- after authenticated execution: `results/v78/V78_MARGINAL_AUTHORITY_V1.json`

### Authority contents

One compact artifact with two explicitly separated sections:

1. `rank_scrubbed_abundance`
   - empirical positive-count abundance distribution/quantiles over corrected full 41,238-address TRAIN;
   - sorted geometry only, no real address→abundance map;
   - assignment to synthetic registry positions happens via deterministic stream `14000`.

2. `depth_marginals`
   - pathology-blind library-size and detected-address quantiles plus log1p correlation;
   - operator-level when >=50 corrected TRAIN cells;
   - otherwise source-family;
   - global only when source-family itself has <50 cells.

### RED

- [ ] Reject source records that are not TRAIN-only/read-only/pathology-blind.
- [ ] Reject metadata/field names matching pathology/diagnosis/Braak/CERAD/disease/target/query-style denylist.
- [ ] Assert authority binds all 42 corrected shard digests and 41,238-address registry identity.
- [ ] Assert no field exposes `address_id -> empirical_abundance`, symbol->abundance, Ensembl->abundance, marker membership or regulatory membership.
- [ ] Assert abundance values are stored as sorted/quantile geometry and deterministic permutation assignment is identity-scrubbed.
- [ ] Assert abundance assignment is invariant to synthetic class/module membership.
- [ ] Assert fallback is exactly operator >=50 -> source -> global and cannot be regrouped based on outcomes.
- [ ] Assert runtime observer consumes the compact authority only; corrected real cache paths are not opened by generation code.

Run:
`pytest -q tests/test_v78_marginal_authority_v1.py`

Expected RED: authority builder/artifact absent.

### GREEN

- [ ] Implement builder with explicit source SHA list, fields-read ledger and pathology denylist receipt.
- [ ] If exact corrected TRAIN bytes are not available in the current execution environment, stop this task at a fail-closed custody blocker; do not reconstruct empirical distributions from summary envelopes.
- [ ] Build the artifact only from authenticated corrected TRAIN bytes.
- [ ] Implement deterministic abundance permutation helper using stream `14000`.
- [ ] Implement depth-marginal lookup and realization using existing measurement seed plus only predeclared `14100–14199` jitter if required.
- [ ] Commit exact authority JSON and a test asserting committed artifact == builder output when source bytes are available.

Commit milestone: `feat(v78): freeze corrected marginal authority`

---

## Task 4 — Integrate F3 without erasing F2 topology

**Modify:**
- `scripts/v77/build_v78_fullscale_rna_observer.py`
- `tests/test_v78_signed_detection_marginals_v1.py`
- `tests/test_v78_marginal_authority_v1.py`

### RED

- [ ] F3 must use exactly the F2 signed field/loadings/streams.
- [ ] Structural support must remain identical to F2.
- [ ] Class truth/class scale must remain E2-identical.
- [ ] F3 positive-count baseline must come from the rank-scrubbed abundance assignment, not real identity.
- [ ] F3 depth targets must come from the frozen operator→source→global authority lookup.
- [ ] Manifest must bind marginal-authority SHA and record which fallback stratum each operator used.
- [ ] E4/training controls remain fail-closed.

### GREEN

- [ ] Wire F3 rank-scrubbed weights and depth-target provider into the V78 successor observer.
- [ ] Preserve the F2 selection field exactly.
- [ ] Add deterministic unit/integration tests for totals, support and provenance.
- [ ] Run all V78 tests plus existing V77 class-propagation tests.

Commit milestone: `feat(v78): integrate count and depth marginals`

---

## Task 5 — Extend scoring prospectively for signed detection endpoints

**Create:**
- `scripts/v77/v78_signed_scoring.py`

**Modify:**
- `tests/test_v78_signed_detection_marginals_v1.py`

Do not change the canonical V77 matched scorer's existing statistics. The V78 wrapper calls `v77_matched_scoring.score_matched(...)` first, then adds signed diagnostics on the **same selected genes/rule**.

### RED

- [ ] Require prior V77 panel unchanged.
- [ ] Add fraction `r > +0.3`, fraction `r < -0.3`, positive/negative ratio.
- [ ] Add positive and negative signed-degree summaries.
- [ ] Add fraction of selected genes with >=1 negative strong edge.
- [ ] Add negative-edge participation by absolute-correlation community.
- [ ] Unit-test hand-built matrices with known positive/negative edges.

### GREEN

- [ ] Implement deterministic signed diagnostics without changing gene selection.
- [ ] Confirm F0 wrapper reproduces the complete historical E2 V77 score object for the legacy fields.

Commit milestone: `feat(v78): add signed topology diagnostics`

---

## Task 6 — Freeze and execute the F0–F3 tournament

**Modify/Create:**
- `scripts/v77/run_v78_signed_detection_marginal_tournament.py`
- `.github/workflows/v78-signed-detection-marginals.yml`
- after execution: `results/v78/V78_SIGNED_DETECTION_MARGINAL_TOURNAMENT_V1.json`
- after adjudication: `results/v78/V78_SIGNED_DETECTION_MARGINAL_SCIENTIFIC_RULING_V1.json`
- `docs/agent/V78_SIGNED_DETECTION_MARGINAL_TOURNAMENT_AUDIT_20261009.md`

### Pre-execution gate

- [ ] All V78 RED requirements are GREEN.
- [ ] Existing V77 class-propagation focused tests pass.
- [ ] Historical structural spillover audit passes.
- [ ] 2K support remains 42/42, min >=1.
- [ ] Exact corrected universe authenticates to `e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`.
- [ ] Registry authenticates to `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`.
- [ ] F3 marginal authority authenticates and is built from corrected TRAIN, not summary reconstruction.
- [ ] Executor tree is clean and every executor SHA is recorded.

### Execution order

1. F0 only. Exact comparison against committed E2; any mismatch stops.
2. F1 and record, with no tuning.
3. F2 and record, with no tuning.
4. Contract self-audit: confirm F2 isolation and leakage checks before F3.
5. F3 and record unchanged.

### Scientific ruling

Report causal contrasts, not a winner-by-distance:
- F0→F1: generic expression covariance ablation.
- F0→F2: isolated signed-detection mechanism.
- F2→F3: count/depth marginal repair.

Apply the preregistered falsification rules exactly. Keep real points descriptive and `s159_binary_gate=false`. Do not tune any factor scale, stream, support fraction, fallback threshold or marginal after viewing outcomes.

### CI

Dedicated workflow runs:
- `pytest -q tests/test_v78_signed_detection_marginals_v1.py tests/test_v78_marginal_authority_v1.py`
- existing V77 focused class-propagation tests
- historical structural spillover audit

Record exact workflow run ID, branch head and executor digests in the audit/ruling.

Commit milestone: `test(v78): adjudicate signed detection and marginal repair`

---

## Final verification

Before claiming completion:

- [ ] Compare implementation branch to `f3a5d142...`; verify no runtime/optimizer/EMA/target-discovery/353-ID/protected-data changes.
- [ ] Verify no TEST/Morabito references in any executor/authority provenance.
- [ ] Verify all new random streams are within frozen V78 ranges and do not collide with V77 streams.
- [ ] Verify E2 class scale remains `0.55` everywhere.
- [ ] Verify F0 reproduces committed E2.
- [ ] Verify raw scientific receipt, ruling and audit are mutually consistent and hash-bound.
- [ ] Run fresh GitHub CI on final head before any success claim.

## Stop conditions

Stop and report a major milestone/blocker rather than improvising if:
- corrected TRAIN bytes needed for F3 authority cannot be authenticated;
- F0 fails exact E2 reproduction;
- any V77 spillover test regresses;
- F2 cannot preserve the isolation invariants;
- a scientific result suggests a new parameter choice (that requires a new prospective design, not an edit to this tournament).
