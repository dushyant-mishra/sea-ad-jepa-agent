# Unified synthetic/integration hostile audit — 2026-10-13

Status: `PASS_WITH_LIMITATIONS__MECHANICS_FIXTURE_QUALIFIED__PRODUCTION_SUBSTRATE_NOT_COMPLETE__NO_BIOLOGICAL_AUTHORITY`

This is a documentation-only hostile audit of PR #328 and its frozen source lineages. No production files, synthetic worlds, Q00-Q11 objects, scoring code, TD code, target contracts, or training authority are changed by this audit.

## Exact audited identities

- PR #328 current head: `2b974521f97d0f83c50f02b80ef7a1d135954304`
- PR #328 mechanics/CI source head: `8da8ed15bf5e7a6f42ae2f359b04a7d91cb00c83`
- GitHub PR merge checkout tested by CI: `6c861f1ead68c9d2fe8a56c8b95f2da403db1c72`; compare against source head shows zero file differences.
- CI run: `38475834418`; job `115566164685`; exact focused command collected 70 tests and reported `70 passed in 1.43s`, no skip/deselection line.
- PR #315 design base: `af03ef67d52651463944a6de3a08e101ad00e0ea`
- V79 PR #253 source: `1a0ab6e1108af924ca13e81caa3c70f3101d251c`
- PR #311 rare source: `2b6d3439105e087acdab53a318c57bbb468eae26`
- Stage81A3 lineage commit: `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`
- historical audit/handoff reviewed: PRs #322, #323, #325.

The current PR head is two commits ahead of the tested source head. Those two commits change only the execution ledger and frozen integration receipt; executable code/tests are unchanged.

## Independently verified implementation claims

### PASS — candidate leakage firewall in latent generation

The executable unified generator contains no candidate-specific C1/C2/C3/C4/C5/C6 branches or dimensions. `UnifiedBiologyConfig.extra_metadata` rejects candidate identifiers. Candidate semantics are created only in `unified_synthetic_controller_truth_v1.py` after the neutral world exists.

### PASS — one population carries common and rare activity

The base V79 hierarchical population and stochastic rare-program overlays are realized in the same cell/donor arrays. Rare activity is not packaged as a separate synthetic dataset.

Rare realizations are stochastic. The generator does not force a positive rare cell/regime after sampling; a regression explicitly tests zero realized positives under zero prevalence.

### PASS — observation-vs-biology separation

Source assignment and observation operator parameters are applied after world construction. Tests show balanced versus shifted source/operator settings alter observed hashes while preserving `world_hash`.

The imported V79 hierarchical biology and observation operator files are currently byte-identical, by Git blob identity, to PR #253:
- biology blob `08d74b02fb609a1e923f2adc906c2bf68b821b26`
- observation blob `6ed165d33ea31616875064f0c7d95554a6a6abe8`

### PASS — measured zero versus structural unmeasurement

Fit serialization includes both `values` and a separate `support` mask. Tests establish supported measured zeros and unsupported zero-valued slots coexist; unsupported addresses are not reclassified as measured zeros.

### PASS — same-nucleus versus separate-nucleus semantics

Same-nucleus mode uses identical RNA/ATAC entity IDs and shared focal rare state. Separate-nucleus mode gives distinct entity IDs, preserves donor identity, and resamples ATAC rare activity from donor prevalence rather than copying focal-cell state. Tests verify no same-cell pairing claim and stronger same-nucleus RNA/ATAC coupling.

### PASS — technical pseudo-rarity is observation-side

Technical pseudo-rarity modifies measured RNA only after biological world construction, is restricted to biologically non-rare cells, does not change `world_hash`, and its truth label is not serialized to the fit view.

Executable pseudo-rarity rate is an explicit synthetic stress preset `0.05`, not PR #311 `REGIMES[*].tail_fraction`.

### PASS — disputed STAT1/50K prevalence/tail moments are not executable rarity calibration

The unified generator does not import or call PR #311 `REGIMES` or `_donor_latent`. Executable rare donor-active/prevalence values come from explicit `SYNTHETIC_RARITY_PRESETS`. The manifest/receipt fail closed unless rarity and pseudo-rarity are labeled non-empirical synthetic stress presets and the 50K physical-row lineage remains `QUARANTINED_NOT_HARD_AUTHORITY`.

PR #311 `SIGNS`, `SOURCES`, and `VISIBILITY` remain reused for qualitative program/source-observation structure. That is not the disputed donor prevalence/tail calibration, but the distinction should remain explicit.

### PASS — context identity correction

Context enrichment is keyed to the literal `central` regime identity, not program position. A reordered-regime regression protects this property.

### PASS — donor-disjoint splits

Split is a deterministic donor function; tests verify one split per donor.

### PASS — fit serialization excludes controller truth

`serialize_fit_view()` excludes rare/program truth, expected molecular state, candidate mapping, recoverability, counterfactual truth and pseudo-rare labels. The fit-view module does not import the controller module. The synthetic package identity excludes controller bytes/hash; the separate integration receipt records controller truth hash for custody.

### PASS — deterministic audited fixture and 70/70 regression evidence

Run `38475834418` generated exactly the receipt values frozen later in-repo:
- world `dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66`
- fit view `fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a`
- controller truth `fbf053702440b73d385490e31ee99be3ee664549e4d790df9bef0027ba0ff6bf`
- manifest `15da98d9935621283c1a0d533c8da24e2b4fd247838554d3f45f55ec88446d07`
- synthetic package `87eac016cb29e1c9a21d64170dc4f1a386e5eea480644bfe66b1659785c878d1`

Q00-Q11 files are absent from the PR #315-to-#328 change set and therefore untouched by this integration branch.

## Claims that are only partially verified or over-stated

### MAJOR — PR #328 does not implement the full PR #315 production substrate

PR #315 V2 specifies a production-oriented substrate including Stage81A3 mechanistic/causal-network lineage, generic additive/non-additive interaction families, query semantics, production donor partition, and the modern 41,238-address input contract.

PR #328 instead implements a small deterministic mechanics fixture by default (`480` cells, `48` genes, `16` donors) using the V79 hierarchy plus PR #311-derived qualitative rare/source mechanics. Stage81A3 is source-commit bound as lineage but its historical mechanistic-network/intervention implementation is not imported or executed. C3/C4/C6 biological interaction/query truth is not materialized as the production design describes; controller mappings are lightweight derived rehearsal objects.

Therefore the defensible claim is: **unified mechanics/interface fixture implemented and qualified**, not **full PR #315 production synthetic substrate implemented**.

Minimal prospective repair: narrow PR #328 language/terminal to mechanics-fixture qualification and leave production realization as a separate, prospectively authorized implementation task. Do not retrofit extra biology into this frozen fixture merely to satisfy documentation.

### MAJOR — final receipt does not hash-bind all executable dependency bytes

`integration_source_sha256` covers only four new integration modules. Runtime behavior also executes:
- `scripts/v79/v79_hierarchical_biology.py`
- `scripts/v79/v79_observation_operator.py`
- `scripts/v79/v79_rare_biology_generator_v1.py`

All three are currently byte-identical to their frozen source lineages (`08d74...`, `6ed165...`, `2a2f0...` Git blobs), but those dependency bytes are not included in the frozen SHA-256 package identity. Source commit strings are recorded without an executable check in the finalizer that current dependency bytes equal the frozen commits.

Minimal prospective repair: extend a successor custody receipt to hash-bind every executable imported dependency and verify current bytes against the frozen source identities before receipt creation. This is custody hardening only; no synthetic biology should change.

### MAJOR — Python dependency environment is not pinned/bound

The CI installs unpinned `pytest numpy pandas scipy`; the successful run happened to use Python `3.11.17`, NumPy `2.4.6`, pandas `3.0.6`, SciPy `1.17.1`, pytest `9.1.1`. The receipt does not bind these versions.

The current run is reproducible evidence for that environment, but the stronger claim of environment-independent deterministic rebuild/custody is not established.

Minimal prospective repair: freeze exact runtime versions (or an immutable environment lock) and include environment identity in a successor custody receipt. Rebuild the same fixture once prospectively and require identical world/fit/controller/package hashes.

### MODERATE — controller separation is serialization/logical, not a physical execution-domain boundary

The final fit artifact is controller-free, which is verified. However fixture construction in CI creates `world`, `fit`, and controller truth in one Python process, and observation generation receives the full truth-bearing `UnifiedBiologyWorld` object. PR #328 therefore does not implement a strong process/filesystem custody separation comparable to the later two-phase TD controller design.

This is acceptable for mechanics-fixture qualification but must not be described as a sealed blind-fit custody system.

Minimal prospective repair: for any future blinded unified qualification realization, serialize a controller-free fit package in a producer stage and run fit-side consumers in a separate workspace/process that is never given controller artifacts. Keep this outside the frozen mechanics fixture.

### MODERATE — perturbation actual/null semantics are under-bound

The world has arms `0/1/2`, and only `(arm == 1) & rare_activity` changes latent expected state. The fit view exposes only numeric `perturbation_arm`; controller truth records arm counts but not an explicit frozen mapping such as control / actual / matched-null. Current tests verify three arms and hidden `perturbation_state`, but do not explicitly prove arm-2 matched-null semantics.

Minimal prospective repair: bind an explicit prospective arm-semantic mapping in manifest/controller truth and test that actual perturbation changes the intended mechanism while matched-null does not. Do not change the planted biology merely to produce a favorable result.

### MINOR — write-once is an API property, not immutable storage

`write_integration_receipt_once()` refuses to write over an existing path. It does not make the filesystem object cryptographically or permission-level immutable. Git history provides durable versioning once committed.

Use the phrase `writer-enforced write-once + Git-frozen receipt`, not absolute immutable storage.

## Historical rules assessment

No violation found for:
- Q00-Q11 immutability;
- candidate IDs influencing latent generation;
- source/operator directly altering latent biology;
- measured-zero/support separation;
- same-cell claims for separate-nucleus data;
- donor-first splitting;
- pathology/protected outcomes;
- TD60/Stage4/training authority;
- automatic promotion of synthetic mechanics to human biology;
- direct executable reuse of disputed STAT1 donor-frequency/tail moments.

The no-repeat ledger remains compatible: Stage81A3 is retained lineage, V79 Q00-Q11 remain frozen, PR #311 remains component evidence, PR #315 V2 remains the governing architecture, and real TD/target/training remain separate authority domains.

## Science-authority assessment

### Software mechanics

Qualified for the audited fixture and exact tested code: one-population rare/common mechanics, observation separation, support semantics, multimodal pairing classes, technical pseudo-rarity, context views, donor split, fit/controller serialization firewall, receipt generation and downstream no-authority smoke compatibility.

### Synthetic challenge geometry

Implemented for qualitative weak/central/strong/extreme rarity stress classes and context/perturbation mechanics, but not equivalent to the full PR #315 production biological substrate and not yet V79 Layer-A statistical qualification.

### Observation mechanics

Mechanically qualified for this fixture; V79 PR #253 biology/observation primitives are byte-preserved. This does not replace or complete separate V79 Q00-Q11 scoring.

### Real-human biology

No authority. The synthetic amplitudes/frequencies do not establish human effect sizes/prevalence. No STAT1 target claim, candidate winner, representation winner, architecture winner or causal biological conclusion follows.

## Downstream compatibility boundary

PR #328 does not bypass:
- the separate V79 statistical-scoring qualification lane;
- TD phase-2/controller qualification;
- real TD gate-executor materialization;
- repaired multi-block `TargetPortfolio` semantics;
- target selection;
- representation/EMA/TD60/Stage4/training authority.

The old imported post-TD harness smoke test proves only interface/no-authority compatibility and must not be interpreted as current downstream portfolio authority.

## Overall verdict

`PASS_WITH_LIMITATIONS`

The implemented unified synthetic mechanics fixture is internally coherent and its advertised 70/70 regression evidence is real. The primary defects are over-broad production-substrate wording and incomplete custody binding of transitive code/environment dependencies. These defects do not invalidate the observed mechanics fixture or create biological authority, but they prevent calling PR #328 a fully production-qualified, fully custody-complete synthetic substrate.

## Updated terminal

`UNIFIED_SYNTHETIC_MECHANICS_FIXTURE_QUALIFIED__FULL_PR315_PRODUCTION_REALIZATION_INCOMPLETE__TRANSITIVE_CUSTODY_HARDENING_REQUIRED__V79_LAYER_A_SCORING_SEPARATE__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
