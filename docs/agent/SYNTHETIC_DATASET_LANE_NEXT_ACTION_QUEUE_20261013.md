# Synthetic dataset lane next action queue — 2026-10-13/14

## Priority 0 — preserve current evidence
- Do not modify V79 or V80 historical/frozen identities.
- Do not duplicate closed historical audits.
- Do not merge synthetic stress presets with human prevalence/effect authority.

## Priority 1 — PR #344 V2 user review
Current design: `docs/superpowers/specs/2026-10-13-lineage-composite-production-synthetic-design-v2.md` at PR #344 head `f10d4f62b59a35cc443302ab8863c33d51b2b1de`.

Review questions:
1. Are ancestry classes correctly separated into reusable mechanics, narrow authority, negative priors and unfrozen diagnostics?
2. Does one-hidden-truth multi-dataset generation inherit V72-V75 without claiming their unresolved 500K authority?
3. Are A3R three-state support semantics preserved?
4. Are V78/Stage70/Stage71 prevented from becoming positive biology authority?
5. Are query-normalization leakage and wrong-query controls explicit?
6. Is producer/fit/controller physical separation mandatory for sealed qualification?
7. Is V79 sparse-positive stress included without copying V79 thresholds?
8. Are fragments, spatial/limited-panel, same-nucleus and separate-nucleus modalities represented?
9. Are biological and measurement uncertainty separate?
10. Are all downstream authority flags OFF?

If any answer is no, amend V2 prospectively before implementation. If all are yes and user approves, proceed to Priority 2.

## Priority 2 — implementation plan
Create a new plan under `docs/superpowers/plans/` and a fresh implementation branch stacked on approved PR #344 V2. Do not expand PR #328.

Required implementation units:
1. historical component recovery / custody map;
2. candidate-neutral master hidden population;
3. canonical 41,238-address compatibility + three-state support;
4. multi-view observation system;
5. common + rare + interaction biology;
6. query / relational / regulatory / perturbation truth;
7. biological-vs-measurement uncertainty and recoverability truth;
8. development package;
9. independently seeded sealed qualification package;
10. hostile qualification + deterministic final receipt.

Every unit uses RED -> GREEN -> hostile audit -> fix -> regression. Preserve failed audits and rulings in an append-only ledger.

## Priority 3 — historical component recovery
Before writing new generator logic, authenticate the exact reusable source bytes and classify each dependency:
- Stage81A3/A3R: ancestry/support semantics only where allowed;
- V72-V75: population/sharding/allocation/measurement mechanics;
- V79: hierarchical biology/observation and blinding mechanics, not qualified estimator authority;
- PR #311/#328: rare/multimodal/context fixture mechanics with STAT1 numerical-frequency quarantine;
- PR #318-#321: sealed packaging mechanics.

If exact historical implementation is unrecoverable, write a new prospective implementation and label it new. Never reconstruct hidden historical algorithms from memory and call them inherited authority.

## Priority 4 — master biology and population
Build one candidate-neutral hidden population. Requirements:
- donor-first generation and donor-disjoint split support;
- broad class/state physically generative;
- common and rare programs coexist in one population;
- additive and non-additive interactions;
- no candidate IDs, C1-C6 labels, downstream winner labels or pathology variables in generation;
- source/operator cannot alter latent biological truth.

## Priority 5 — support, address and observation
Implement 41,238-address compatibility and preserve three support states:
- `STRUCTURALLY_UNMEASURED`
- `MEASURED_SCALAR`
- `MEASURED_COLLISION_UNRESOLVED`

Measured zero remains distinct from both unsupported states.

Observation system should cover RNA, same-nucleus RNA+ATAC, separate-nucleus multimodal views, fragments where required, limited-panel/spatial view, context views, perturbation/control/null arms, source/operator acquisition, donor observation effects and sparse-positive stress.

## Priority 6 — truth families and leakage controls
Controller-only truth should include latent programs, interactions, relational geometry, regulatory mechanism, interventions/counterfactuals, query-specific truth, support truth and uncertainty decomposition.

Required controls:
- no query value in normalization/QC descendants;
- own-query vs wrong-query exchangeability;
- capacity-matched query-agnostic control;
- regulatory nuisance and semantic twins;
- randomized relational/graph controls;
- perturbation matched-null remains mechanistically null.

Do not preassign recoverability winners or target winners during generation.

## Priority 7 — package architecture
Maintain two realizations:
- development realization with truth accessible for generator debugging;
- independently seeded sealed qualification realization.

For the sealed realization, producer, fit and controller outputs must be physically separate. Fit custody must exclude hidden truth, estimability truth, expected molecular state, challenge roles, candidate labels and held-out outcomes.

## Priority 8 — hostile audit suite
At minimum attack:
- candidate-ID dependence;
- controller leakage;
- source-to-biology leakage;
- forced rare-positive injection;
- measured-zero/support collapse;
- support poison-value dependence;
- donor split leakage;
- same-nucleus/separate-nucleus conflation;
- perturbation-null contamination;
- query-normalization leakage;
- outcome/estimability leakage;
- dependency/source mutation;
- runtime drift;
- nondeterministic package generation.

Each discovered defect gets a failing regression test before repair.

## Priority 9 — final synthetic freeze
Freeze only after exact-head CI and independent byte regeneration are green. Receipt must bind source hashes, transitive dependencies, runtime, world/package identities and authority flags.

Final synthetic qualification may establish generator/package mechanics only. It does not establish human biology, human thresholds, real target authority, representation authority, Stage4 or training authority.

## Separate estimator-owner queue
V80 benchmark work is complete. If another agent owns the successor inference estimator, hand them PR #348 and require a prospective one-shot qualification against immutable V79 + frozen V80. Synthetic lane should not tune their estimator or benchmark based on results.