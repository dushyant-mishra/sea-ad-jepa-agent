## 1. Overall verdict

**PASS WITH LIMITATIONS**

The unified synthetic lane is mechanically coherent for the **audited fixture**, and the claimed 70/70 regression run is real. But PR #328 overstates its scope if read as “the full PR #315 production synthetic substrate is implemented.” It is better characterized as a **qualified unified mechanics/interface fixture** with several custody hardening gaps before it should be treated as a production-grade synthetic qualification substrate.

I froze this first-pass audit in **draft PR #339**, head `7e955445f938d24dec9cf177e27d60433b8ab97e`, without changing production code.

## 2. Exact audited heads / branches

Primary audited state:

- PR #328 current head: `2b974521f97d0f83c50f02b80ef7a1d135954304`
- mechanics/CI source head: `8da8ed15bf5e7a6f42ae2f359b04a7d91cb00c83`
- CI run: `38475834418`, job `115566164685`
- PR #315 design base: `af03ef67d52651463944a6de3a08e101ad00e0ea`
- V79 PR #253: `1a0ab6e1108af924ca13e81caa3c70f3101d251c`
- PR #311: `2b6d3439105e087acdab53a318c57bbb468eae26`
- Stage81A3 lineage: `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`
- historical authority/handoff surfaces: PRs #322, #323 and #325.

The current #328 head is two commits beyond the tested source head, but those commits altered only the ledger and frozen receipt; executable code and tests did not move.

## 3. Claims independently verified

I independently verified the important mechanics claims.

Candidate semantics are not planted into latent generation. The generator remains candidate-agnostic, while C1–C6 mappings are derived controller-side only after the world exists. Rare and common biology coexist in one donor/cell population, and rare realizations remain stochastic rather than being forced positive.

Source/operator behavior is observation-side: changing the observation configuration changes measured output while preserving the same latent `world_hash`. The two imported V79 primitive files are byte-identical by Git blob to the frozen PR #253 sources: biology `08d74b02…` and observation `6ed165d3…`.

Measured zero and structural unmeasurement are separate. Same-nucleus RNA/ATAC uses shared entity identity; separate-nucleus uses distinct entity identities while preserving donor identity. Technical pseudo-rarity modifies observations only on biologically non-rare cells. The fit payload excludes rare/program truth and controller objects. The regression tests exercise all of those properties.

The disputed STAT1/50K donor-frequency and tail moments are **not** the executable prevalence calibration in PR #328. The old PR #311 source indeed contained empirical `REGIMES` values and tail fractions, but the unified implementation replaces those with synthetic stress presets and uses a synthetic pseudo-rarity rate of `0.05`.

The frozen receipt explicitly labels the STAT1/50K lineage `QUARANTINED_NOT_HARD_AUTHORITY`, rarity frequencies as synthetic non-empirical presets, and keeps every execution/selection/training authority flag false.

### Regression verification

The exact workflow ran the seven intended test modules plus deterministic receipt generation. The job completed successfully on head `8da8ed15…`.

The durable logs showed:

- **70 collected**
- **70 passed**
- no skips or deselections reported
- deterministic receipt generation completed.

The resulting world, fit, controller, manifest and package hashes match the receipt frozen in the repository.

## 4. Claims not verified

The largest unsupported claim is that #328 represents the **complete PR #315 production substrate**.

PR #315 specifies substantially more: Stage81A3 mechanistic/causal-network biology, generic additive/non-additive interaction families, richer query semantics, a production donor split, a canonical 41,238-address realization, and downstream rehearsal of the actual production path.

PR #328 defaults instead to a small fixture—480 cells, 48 genes and 16 donors—and does not execute the historical Stage81A3 mechanistic network. Stage81A3 is **lineage-bound**, not actually imported as executable biology. Therefore:

**Implemented:** unified V79 + rare/context/multimodal mechanics fixture.  
**Planned/documented:** full PR #315 production biological substrate.

I also did **not** verify V79 Layer-A statistical qualification, because that is a separate scoring lane and #328 itself says it remains pending.

## 5. Defects found

**Critical: none.**

### Major — scope overclaim

PR #328 should not be described as the finished PR #315 production simulator. That conflates a qualified mechanics fixture with a much richer production design.

**Minimal fix:** narrow the durable claim/terminal for #328; implement the full production realization separately rather than modifying this already-qualified fixture.

### Major — incomplete transitive code custody

The receipt hashes only the four new integration files. But the runtime also executes:

- `v79_hierarchical_biology.py`
- `v79_observation_operator.py`
- `v79_rare_biology_generator_v1.py`

Those files are currently equal to their frozen source blobs, including the rare generator blob `2a2f0b2f…`, but that identity is not part of the package’s SHA-256 custody object.

**Minimal fix:** successor receipt should hash every executable imported dependency and fail closed if it differs from its frozen source.

### Major — runtime environment is unpinned

The CI workflow does:

`pip install pytest numpy pandas scipy`

without version pins.

The successful run used a concrete environment, but those versions are not part of the frozen receipt. That prevents a strong claim of environment-independent deterministic reproducibility.

**Minimal fix:** freeze the Python/scientific-stack versions and bind them in a successor custody receipt; rerun the fixture once and require identical hashes.

### Moderate — controller separation is logical/artifact-level, not physical

The output package is controller-free, which passes.

But world generation, observation generation and controller truth derivation can occur in the same Python process. This is not the same custody isolation as the later two-phase TD blind-fit/controller design.

**Minimal fix:** only for a future blind qualification realization, construct the controller-free fit package in a producer stage and give the fit-side process no controller workspace.

### Moderate — perturbation null semantics are under-specified

There are three perturbation arms, but only arm `1` changes latent state. Arm identity is passed numerically; the manifest/controller do not explicitly bind a semantic map such as:

`control / active perturbation / matched perturb-null`.

The tests establish three arms exist, but not the full semantic contract required by the PR #315 design.

**Minimal fix:** prospectively bind arm meanings and add an invariant that the matched-null arm cannot alter the target mechanism.

### Minor — “write once” is writer-enforced

The helper refuses to overwrite an existing receipt, but the filesystem itself is not immutable. Git freezing supplies the durable history.

Call this **writer-enforced write-once + Git-frozen**, rather than absolute immutable storage.

## 6. Science-authority assessment

**Software mechanics:** qualified for this exact fixture.

That includes one-population common/rare behavior, source/observation separation, support semantics, multimodal pairing classes, pseudo-rarity, context views, donor splitting, controller-free fit serialization and non-authorizing downstream interface smoke tests.

**Synthetic challenge geometry:** partially qualified.

The qualitative rare/context/multimodal geometry is present, but it is not the entire production biological substrate described by PR #315. It also does not equal V79 Layer-A statistical qualification.

**Observation mechanics:** mechanically qualified for the fixture.

The V79 biology and observation primitives are frozen and byte-preserved.

**Real-human biology:** **none**.

This work establishes no human prevalence, human effect size, STAT1 biological validity, target winner, representation winner or causal conclusion. That boundary is consistent with the historical claim ladder, which explicitly forbids promoting planted synthetic truth recovery to real biological validity.

## 7. Custody / reproducibility assessment

Current custody is **good but incomplete**.

Strong points:

- exact source commits recorded;
- final manifest hash recorded;
- four integration source files SHA-256 bound;
- world/fit/controller/package hashes frozen;
- controller excluded from package identity;
- receipt committed after deterministic CI generation;
- executable code unchanged since the 70/70 run.

Weak points:

- transitive code dependencies are not included in the final SHA-256 code bundle;
- environment versions are not frozen;
- blind execution-domain separation is not implemented.

So I would call it **reproducible mechanics evidence**, not yet **complete sealed production custody**.

## 8. Historical-rule violations

I found **no direct violation** of the rules you listed for:

- Q00–Q11 immutability;
- candidate-shaped latent generation;
- source-caused biology;
- measured-zero collapse;
- separate-nucleus fake cell pairing;
- donor-first split semantics;
- pathology/protected outcome opening;
- synthetic-to-human threshold promotion;
- direct reuse of disputed STAT1 donor-frequency/tail calibration;
- TD60, Stage4 or training authority.

The PR #325 no-repeat ledger explicitly classifies Stage81A3 as retained lineage, V79 as immutable, PR #311 as component evidence, PR #315 V2 as governing architecture, historical thresholds as non-authority, and the 50K duplicated-`sample_row` issue as unresolved. #328 remains compatible with that classification.

## 9. Minimal required fixes

I would make only four prospective repairs, without redesigning the science:

1. **Narrow PR #328’s durable wording** to “qualified unified mechanics fixture.”
2. **Add transitive code hashes** for all executable imported dependencies.
3. **Freeze and bind the runtime environment** used for deterministic generation.
4. **Bind perturbation arm semantics explicitly** and test the matched-null arm.

A future production realization can separately implement the missing PR #315 Stage81A3/41K/query/interaction machinery under fresh authority. I would not mutate this frozen fixture to pretend that work already exists.

## 10. Updated terminal statement

`UNIFIED_SYNTHETIC_MECHANICS_FIXTURE_QUALIFIED__FULL_PR315_PRODUCTION_REALIZATION_INCOMPLETE__TRANSITIVE_CUSTODY_HARDENING_REQUIRED__V79_LAYER_A_SCORING_SEPARATE__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

The frozen first-pass audit is in **PR #339**.
