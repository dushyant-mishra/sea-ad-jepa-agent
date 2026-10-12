# Unified synthetic TD rehearsal — self-audit

Date: 2026-10-12
Scope: PR #315 design at initial head `c6a7e7ee94f6b866a7ca3fa51567213e8fd16a1e`
Decision: **REVISE BEFORE APPROVAL OR IMPLEMENTATION**

## Summary

The initial PR #315 design corrected one major error — rare biology must be embedded in the same biological population rather than maintained as a separate rare dataset — and correctly kept Q00–Q11 immutable. However, a cold audit against project history and the current TD downstream contracts found several important omissions and one circularity defect. The initial design must not be treated as approved architecture.

## Critical findings

### A1 — Historical biological synthetic substrate was omitted

The initial design treated Q00–Q11 as the primary pre-existing synthetic foundation. That is incomplete.

Stage81A3 already contains a biological synthetic fixture in `src/sea_ad_jepa/v4/conditional_predictability.py` with:
- 32 latent biological factors;
- 12 causal/mechanistic factors connected by a fixed synthetic DAG;
- 20 additional independent factors;
- 4,096 genes with overlapping factor-linked gene modules;
- noise-free expected molecular state (`lambda_norm`);
- independent paired sequencing realizations;
- counterfactual interventions (`lambda_norm_cf`);
- explicit separation between true factors, expected state and observed counts.

The corrected architecture must extend/reconcile this biological lineage rather than recreate a latent manifold from scratch.

### A2 — Candidate-shaped latent truth is circular

The initial design directly wrote the latent state as `Z_shared ⊕ Z_query ⊕ Z_rel ⊕ Z_regulatory ...` and described C1/C2/C3/C6/C4/C5 analogues as planted factors.

That risks qualifying the TD candidate system against a universe constructed in the candidates' own image.

Correction:
- generate candidate-agnostic biological processes first;
- derive controller-only candidate truth objects from those processes;
- let C1/C2/C3/C6/C4/C5 remain competing representations/estimands over the same hidden biology.

Examples:
- C1 truth = global/shared subspace of the underlying programs;
- C2 truth = anchored relational ordering induced by the same latent manifold, not a separate `Z_rel` coordinate;
- C3 truth = query-conditioned information derived from the biological program/gene network, not a separate `Z_query` factor;
- C6/C4 increment truth = non-additive interactions prospectively planted in generic biological mechanisms, with matched additive/null mechanisms, not candidate-named latent variables;
- C5 truth = regulatory/mechanistic information available through the same programs and privileged modalities.

### A3 — No explicit controller/fit-side truth firewall

Known latent truth is useful only if it cannot leak into the fitted teacher/student or candidate tournament.

The corrected design must physically separate:
- **controller-only truth:** latent factors, program identities, rare-activity labels, interaction class, recoverability class, counterfactual truth, expected gate terminal;
- **fit-side data:** lawful RNA/ATAC/context observations, support masks, donor split, query identity when allowed, observation descriptors when allowed;
- **score-side data:** fit outputs plus controller truth after the relevant gates are frozen.

No model-fitting code may receive controller truth.

### A4 — Synthetic pipeline must execute the same downstream code path

A parallel synthetic-only tournament would not qualify the proposed real pipeline.

The corrected design must require:
- PR #313 candidate case-ledger/firewall/falsifier/tournament code reused directly wherever possible;
- the same candidate gate executors for synthetic and real data, with dataset adapters only;
- the canonical teacher/student/EMA runtime reused for model qualification, with synthetic data adapters only;
- hash binding of shared executor/runtime code so a PASS cannot be produced by a synthetic-specific substitute.

## Important findings

### A5 — Production-scale input contract was missing

The historical Stage81A3 fixture uses 4,096 genes. The current project address namespace is 41,238 universal molecular addresses and downstream teacher/student mechanics expect the modern canonical address/support semantics.

The corrected design must distinguish:
1. small deterministic unit fixtures for testing generator and gate logic;
2. a production-scale synthetic realization that conforms to the modern canonical reader schema/address namespace and can be consumed by the actual downstream pipeline.

The production synthetic population should mirror the 149 TRAIN-donor reader partition structure (104 fit / 22 validation / 23 oracle) unless a separately justified prospective authority changes it. Cell counts may be compute-scaled, but scientific mass remains donor-primary.

### A6 — Multi-lineage biology and program eligibility were underspecified

The rare-program work is microglia-focused, but the foundation/TD pipeline is not a rare-microglia-only system.

The corrected generator must include ordinary lineage/cell-state structure and define program eligibility/support. A STAT1-like rare regulatory program should occur inside the appropriate microglia-like lineage/state support, not across every synthetic cell.

### A7 — Source cannot cause biology, but sampling can create source–biology association

The initial design correctly prohibited source/operator/depth from directly creating biological truth, but simple random source assignment would make the problem unrealistically easy.

The corrected design must separate:
- latent biology generation;
- acquisition/sampling into source/operator strata;
- observation effects.

Source-specific sampling may oversample particular lineages/states/donors and therefore correlate with biology without causally altering the latent biological state. This is necessary to reproduce realistic shortcut pressure.

### A8 — Query truth must arise from biology, not an independent query latent

Query identity should select a biological question from the same generative network. The teacher must construct a target object from its lawful evidence; the student receives less evidence. The queried value cannot be smuggled into the student target or used as a disguised scalar target.

The corrected design must retain explicit q-value, q-address, wrong-q and query-agnostic falsifiers and teacher-target construction audits.

### A9 — Teacher truth and synthetic oracle truth were conflated

The controller's latent truth is **not** the teacher target.

A genuine teacher must construct its state from the evidence assigned to it. Synthetic truth is used to score whether that constructed teacher state preserves the planted biology.

The corrected pipeline therefore separates:
1. controller oracle truth;
2. teacher-side measured evidence;
3. learned/constructed teacher state;
4. student-side partial evidence;
5. student prediction;
6. controller scoring.

EMA remains a stabilization mechanism, not a source of biological truth.

### A10 — Uncertainty should not be planted as a scalar latent label

`U_bio` and `U_measurement` should be properties of the generative/inference problem, not arbitrary coordinates in the biological state.

Correction:
- biological/irreducible uncertainty is defined from the conditional distribution of hidden biology given lawful student evidence;
- measurement uncertainty is defined by repeat observation/resampling under the measurement operator;
- support/abstention is evaluated from structural support and identifiability;
- the student is scored for calibrated uncertainty against these controller-side quantities.

### A11 — Synthetic qualification cannot set real biological cutoffs by planted effect size

Synthetic fixtures can qualify:
- estimand implementation;
- sign/direction;
- invariance;
- positive/null behavior;
- shortcut/falsifier behavior;
- NOT_ESTIMABLE handling;
- decision-code correctness.

They must not automatically determine real-human effect-size thresholds. Any real numerical cutoff still requires a separate prospective real-data/outcome-blind calibration or error-control justification.

### A12 — PR #311 PASS language must be narrowed

PR #311 V1/V2/V3 results remain useful component-level geometry and engineering evidence. They do not qualify the final unified biological substrate because that substrate did not yet exist.

The corrected design should reuse those components while explicitly labeling the old separate-world results as historical component qualification/calibration evidence only.

## What remains correct from initial PR #315

- Q00–Q11 must remain byte-immutable and separately governed.
- Rare biology is a cross-cutting regime/property, not a separate dataset.
- Technical pseudo-rarity belongs in the same observed population.
- Same-nucleus and separate-nucleus multimodal semantics must remain distinct.
- Recoverable / stochastic / teacher-private / NOT_ESTIMABLE classes are essential.
- Portfolio convergence, interference, transport and block-specific learned-teacher continuity should mirror the real TD downstream sequence.
- No pathology or protected outcome may enter synthetic design/tuning.

## Required correction

A replacement V2 design must integrate three historical layers instead of creating a fourth disconnected system:

1. **Stage81A3 biological synthetic mechanics** — candidate-agnostic latent factors, expected molecular state, paired observations and interventions.
2. **V79 Q00–Q11 observation/statistical qualification** — measurement/support/donor/source/depth lessons, immutable as their own campaign.
3. **PR #311 rare/multimodal/context/perturbation components** — donor recurrence, STAT1-like specialist program, technical twins, same-vs-separate nucleus, spatial and perturbational controls.

These feed one production synthetic biological substrate whose outputs are passed through the **same PR #312/#313 downstream candidate and teacher/student pipeline interfaces** intended for real data.

Current terminal:

`INITIAL_PR315_DESIGN_REQUIRES_REVISION__NO_IMPLEMENTATION_AUTHORITY`
