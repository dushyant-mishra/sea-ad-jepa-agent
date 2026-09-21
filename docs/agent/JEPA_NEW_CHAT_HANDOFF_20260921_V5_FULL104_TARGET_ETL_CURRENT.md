# JEPA new-chat handoff — FULL104 ETL, target continuity and Audit-B preexecution

Date: 2026-09-21

Status: CURRENT_V5_FULL104_ETL_TARGET_CONTINUITY_AUDIT_B_PREEXECUTION__TRAINING_OFF

This is the current comprehensive handoff. It supersedes the September 17 START_HERE/pointer routing but does not delete older historical handoffs.

## 1. Exact repository state

Current scientific branch:

integrate/v5-full104-gpt-claude-20260921

Verified scientific head:

3bf6b659de9bdd2711face82b50b47ec567ea449

Current draft integration PR: #38
- head: 3bf6b659de9bdd2711face82b50b47ec567ea449
- base safe-lane head: 0c2f5fb8419ea7d1572479e6ef1b13768e52f3c5
- mergeable at handoff time
- current integration includes the PR #35 safe-lane/ETL work, Claude Phase I-III evidence, Phase-IV preexecution hardening, the independent PR #39 audit artifacts, and the new target-history/rare-biology successor work.

Supporting lanes:
- PR #35 safe-lane + ETL: 0c2f5fb8419ea7d1572479e6ef1b13768e52f3c5
- PR #39 independent Claude preexecution audit: 885c307583f9a773aebe2f9acf9885bbce30473c
- PR #33 information-channel base: ae5dc5c624fff341b8ef30c5359c55528383920a
- main remains historical/stale for current V5 work: c8898923fc10ffa5ef0662b04908b0d94bcb158b

Do not wholesale merge PR #39 onto integration. Its substantive corrected script/evidence/test content is already consolidated; the remaining value of the PR is independent-review provenance.

## 2. Exact CI at the scientific head

All four hosted workflows are green at 3bf6b659de9bdd2711face82b50b47ec567ea449:

- V5 runtime closure — run 35657896178 — SUCCESS
- V5 remaining-RNA and target-semantics successor — run 35657896258 — SUCCESS
- V5 Stage-A spillover firewall — run 35657896169 — SUCCESS
- V5 FULL104 masking runner — run 35657896215 — SUCCESS

The masking runner includes the consolidated Claude execution-contract red-team test under the current stronger semantics: Audit-B execution contract V1 remains permanently preexecution-only.

## 3. Permanent scientific firewall

Keep these invariants visible before every decision:

DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL

IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK

TRAINING_OFF

NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION

Current protected state:
- Audit-B N1 burden outcomes unopened;
- terminal masking outcomes unopened;
- P1/P2/P3/P4 not selected as terminal policy;
- D_shared sealed;
- pathology cannot adapt terminal design;
- DEV/SEALED expression sealed;
- G5 margin unselected;
- terminal target panel unselected;
- training unauthorized.

## 4. FULL104 substrate and ETL state

Lawful reader-fit population:
- 4,553,407 cells;
- 104 donors;
- 42 operators/matrices;
- 41,238 canonical addresses;
- 17,186 measured-scalar addresses common to all 42 operators;
- 8,915 Level-4 blocks.

Key content roots:
- Level-4 block manifest SHA-256: 66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
- canonical address registry SHA-256: 7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd
- source-stratified split receipt SHA-256: 5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4
- heavy core sufficient-statistics artifact SHA-256: f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae

Reader-fit source composition:
- HVS: 198,718 cells, 41 donors, 24 operators;
- NPH52: 236,476 cells, 17 donors, 7 operators;
- SEA_AD: 4,118,213 cells, 46 donors, 11 operators.

The crucial ETL lesson is that SEA_AD is about 90.44% of cells but only 44.23% of donors. A cell-uniform estimand would therefore let source/cell-count mass dominate very differently from the current donor-uniform scientific population.

Operator is not a universal nuisance:
- HVS operators are native-class-pure;
- NPH52 operators are class-pure and named by class;
- SEA_AD operators are region matrices with many classes.

Native cell-class taxonomies are not harmonized across the three sources. NPH52 broad_class is absent in the lawful reader-fit metadata. Do not silently use literal labels as a cross-source biological ontology.

Support geometry is also source-identifying. Measured zero, structural unmeasurement and collision-unresolved remain distinct states.

The reproduced ETL V3 outputs remain immutable. Successor guardrails now:
- reject unknown matrix IDs rather than defaulting them to SEA_AD;
- validate support-pattern-to-source uniqueness directly.

## 5. Audit A/B/C and Claude-lane reconciliation

### Phase I

Claude's original Phase-I heavy-statistics qualification was audited. A stronger V2 successor was run on the real GPU artifact.

Result: PASS.

It verifies:
- all 4,553,407 rows;
- the exact bound heavy artifact SHA;
- all 104 donor source-library totals;
- the complete per-cell source vector;
- zero recorded qualification failures.

The heavy artifact may therefore be reused by content address. Do not rebuild it unless a bound invariant changes.

### Phase II

Real source/fold geometry confirmed the frozen score defect: non-estimable correlations had been mapped to numeric zero in the old scorer. The defect is scientific because zero is a valid good score while undefined is not evidence.

The Phase-II evidence remains current. Do not reinterpret undefined terms as model success.

### Phase III

The integrated six-state evidence contract distinguishes:
- ESTIMABLE;
- TARGET_NONVARIABLE;
- PREDICTION_NONVARIABLE;
- TARGET_AND_PREDICTION_NONVARIABLE;
- MISSING;
- INVALID_NUMERIC.

Additional audited edge cases are closed:
- absent required group cannot silently disappear;
- empty evidence cannot become ESTIMABLE NaN;
- materially negative sum-of-squares is INVALID_NUMERIC;
- undefined is never converted to numeric zero.

P1/P2/P3/P4 are consequence policies, not selected authority. No terminal policy has been chosen.

### Phase IV / Audit B

The original target sample ladder is frozen:
- N1 = 256;
- N2 = 1024;
- N3 = 4096.

N1 has NOT been executed.

The original sample freeze did not fully cryptographically bind the scientific execution interpretation. The integration branch therefore adds:
- Audit-B burden estimator semantics;
- outcome-blind scientific-resolution schema;
- RNG V3 design;
- preflight/contract binding;
- held-out-fold guards;
- fixed mask-key namespaces.

Audit-B execution contract V1 is now deliberately and permanently PREEXECUTION ONLY. Merely naming a precision scope cannot authorize it.

Remaining blockers before N1:

B2 — scientific execution scope:
- decide prospectively what "RSE of the primary burden statistic" means;
- decide target/source/donor/fold weighting;
- decide zero-mean RSE handling;
- record who resolved it, when, why, and that no burden outcome was viewed.

Important: the ETL atlas says donor-uniform is the current base scientific population and source-balanced weighting is a distinct estimand/diagnostic. Do not silently replace donor-uniform production weighting with source-balanced weighting.

B3 — real RNG V3 receipt:
- build from the actual current FULL104, registry, split, masking-parameter and burden-ladder roots;
- verify target-panel choice cannot reroll masks;
- keep fixed mask namespaces and authenticated fold range.

B4 — resolved successor execution contract:
- after B2 and B3, issue a provenance-bearing successor contract;
- V1 must remain non-executable.

Only after B2-B4 may N1 be opened.

## 6. Target-discovery history: do not restart the search

The project has already performed extensive target discovery. The current historical synthesis is:

docs/agent/V5_FULL104_TARGET_DISCOVERY_HISTORY_TO_TD60_SUCCESSOR_20260921.md

Key conclusions:

1. Stage27C/41C/53-62 pathology-prediction performance is evidence that biological heterogeneity matters, but pathology performance is not self-supervised target authority.
2. Stage64-71 found real rare/high-tail microglial biology, but the auxiliary/graph approach did not earn a locked production target.
3. Stage81 showed that biological state can be more stable as a subspace/geometry than as fixed coordinates; axes rotate.
4. TD13-TD55 tried many loadings, dependencies, subspaces, coordinates, pair inversions, ordinal targets, references and proxies. Many failed donor recurrence/cross-source replication, and some apparent positives were later invalidated by row aliasing or better technical nulls.
5. Strong surviving evidence:
   - TD56: disjoint-gene relational geometry across all three sources;
   - TD57B: independent scale-free triplet recurrence, 24/24;
   - TD58: partial-evidence relational recurrence, 24/24;
   - TD59: nearest-half mesoscale relational recurrence, 24/24;
   - TD57C nearest-third locality failed.
6. TD60 was prospectively designed to ask whether a lawful learned EMA teacher preserves the already-qualified global and mesoscale relational objects. It has no result.

Therefore: DO NOT start another handcrafted gene/module/PCA/coordinate target search.

## 7. Current target semantics and successor

Current semantic target:

BIOLOGICAL_CELLULAR_LATENT_STATE_V1

Forbidden objective:

hidden-gene scalar reconstruction.

Current prospective successor:

src/sea_ad_jepa/v5/full104_teacher_relational_target_qualification_authority_v1.py

The teacher's direct cell-state representation may become a JEPA target only if it preserves previously qualified relational biology. Loss reduction or visually structured embeddings are not sufficient.

This is a qualification bridge, not a training authority.

TD60 cannot execute because there is no lawful learned teacher under the current training-off state. Do not enable training simply to manufacture TD60 input.

## 8. Rare biology and heterogeneous cell programs

The current design does not make disease-associated or rare microglial labels supervised targets.

Historical evidence says rare biology can be diluted by averages, but rarity alone is not authority. Rare structure should earn confidence through donor recurrence and molecular/relational preservation.

Current prospective rare-biology design:

docs/agent/V5_FULL104_RARE_BIOLOGY_PRESERVATION_PROSPECTIVE_20260921.md

It uses a label-free q95 molecular-isolation tail derived from the independent TD59 Z view and asks whether X/Y relational order recurs across source×fold cases above matched wrong-cell nulls.

No pathology, disease labels, native-class labels or module labels enter tail selection.

No outcome has been opened. The exact molecular tail evaluator and execution contract still need to be frozen before execution.

A PASS would only qualify a label-free donor-recurrent rare-tail molecular object for a later teacher-preservation gate. It would not prove disease identity, define a new subtype, or set a training weight.

## 9. Target-qualification sample

To prevent SEA_AD/cell-count dominance while remaining outcome-blind, the integration branch implements:

src/sea_ad_jepa/v5/full104_target_qualification_sample_authority_v1.py

and:
- scripts/agent/build_full104_target_qualification_sample_v1_20260921.py
- scripts/agent/validate_full104_target_qualification_sample_v1_20260921.py

Sampling rule:
- scientific unit remains donor-based;
- retain all cells from donors with <=1,024 cells;
- otherwise retain exactly 1,024 cells using deterministic donor-code + authenticated global selection-row hashing;
- expression, library size, nnz, operator, region, class and pathology are forbidden selection inputs.

Authenticated geometry implies:
- 103 donors at 1,024;
- one donor with 81 cells retained completely;
- 105,553 qualification cells.

The authority/builder/validator are implemented and CI-tested.

The real 105,553-cell sample has NOT yet been materialized. Materialization is a legal next step because it is metadata-only, but validate every receipt/hash before downstream use.

## 10. Current files and evidence

The detailed manifest is:

docs/agent/handoff_artifacts/20260921/V5_FULL104_TARGET_ETL_DATA_RESULTS_SCRIPTS_MANIFEST.json

It contains the current ETL package, information-channel/Phase-I-IV evidence, surviving TD56-TD60 lineage, current source modules, builders/validators, tests, workflows and external heavy-asset references.

Important current reports:
- analysis/v5_full104_dataset_etl_20260921/FULL104_DATASET_ETL_ATLAS_REPORT_20260921.md
- analysis/v5_full104_information_channel_redteam_20260920/PHASE_I_HEAVY_STATISTICS_QUALIFICATION_REPORT.md
- analysis/v5_full104_information_channel_redteam_20260920/PHASE_II_C2_SOURCE_FOLD_ESTIMABILITY_REPORT.md
- analysis/v5_full104_information_channel_redteam_20260920/PHASE_III_NON_ESTIMABILITY_EVIDENCE_CONTRACT.md
- analysis/v5_full104_information_channel_redteam_20260920/PHASE_IV_PREEXECUTION_AUDIT_REPORT_20260921.md
- analysis/v5_full104_information_channel_redteam_20260920/PHASE_IV_INTEGRATION_RECONCILIATION_20260921.md
- analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_i/HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2.json
- analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/AUDIT_B_FROZEN_TARGET_SAMPLE.json

## 11. Immediate next sequence

Masking/Audit-B lane:
1. keep N1 closed;
2. resolve B2 outcome-blind;
3. build/verify B3 RNG V3 receipt;
4. issue B4 successor execution contract;
5. rerun exact-head CI/no-skip;
6. only then execute N1 and apply only the prospectively frozen escalation rule.

Target lane:
1. materialize/validate the 105,553-cell target-qualification sample from authenticated metadata;
2. freeze the exact rare-biology molecular evaluator, null/replay authority and execution contract;
3. only then execute the label-free molecular rare-tail prequalification;
4. preserve the result as a qualification object, not a supervised disease target;
5. leave TD60 closed until a lawful teacher exists;
6. do not turn training on until the actual current training-authority graph closes.

## 12. Historical traps

Do not:
- use smaller/historical caches as FULL104 substitutes;
- let old 50K target-discovery artifacts become production authority;
- inherit historical 160/224-D dimensions as biological truth;
- use pathology prediction as target selection;
- call operator a pure technical nuisance;
- treat structural unmeasurement as zero;
- treat undefined correlation as zero;
- let SEA_AD's cell mass silently define the scientific population;
- harmonize cell classes by literal labels without reviewed ontology;
- choose P4 or any other consequence policy after seeing masking outcomes;
- reroll masks when the final target panel changes;
- modify the frozen Audit-B target sample after outcome access;
- rerun TD13-TD55 target searches without a materially new hypothesis.

## 13. Handoff terminal

Current terminal state:

FULL104_ETL_AND_TARGET_HISTORY_AUDITED__RELATIONAL_TEACHER_TARGET_SUCCESSOR_PROSPECTIVE__AUDIT_B_PREEXECUTION_BLOCKERS_B2_B3_B4_OPEN__N1_UNOPENED__TRAINING_OFF
