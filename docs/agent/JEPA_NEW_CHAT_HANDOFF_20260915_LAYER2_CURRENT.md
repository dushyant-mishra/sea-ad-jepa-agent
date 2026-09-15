# JEPA NEW-CHAT HANDOFF — 2026-09-15 — LAYER-2 CURRENT

This is the current handoff for future chats/agents. It supersedes earlier same-day/current-state summaries where they conflict.

## Startup checklist

1. Re-fetch live GitHub heads before any current-state claim.
2. Start from branch `handoff/jepa-current-ledger-layer2-20260915` for the latest consolidated documentation.
3. Read `START_HERE.md`.
4. Read `docs/agent/JEPA_CURRENT_WORK_LEDGER_20260915.md`.
5. Read `docs/agent/JEPA_HISTORICAL_AND_CURRENT_FINDINGS_20260915.md`.
6. Read `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260915_CURRENT.json`.
7. Read `docs/agent/LOCAL_LAYER2_RECONCILIATION_WITH_CLAUDE_20260915.md`.
8. Read the historical 20260914 discovery ledger and closed-invariant registry before proposing heavy work.
9. Keep D_shared/protected outcomes sealed and training OFF.

## One-paragraph state

V5 now has a genuine K=2 disjoint common-core molecular partition and a strong case for using VALUE_ONLY rather than visibility-augmented features. The same-cell thinning screen showed that VALUE_ONLY is measurement-sensitive, but a direct Layer-2 fixed-target audit did not demonstrate a large measurement-realization shortcut at the tested simple model class. The much larger pooled issue is coarse source/operator/context collinearity; however, source-specific and donor-centred analyses corrected the initial pessimistic interpretation by showing substantial within-donor V0<->V1 molecular-view signal in HVS, NPH52 and SEA_AD that measured Q_DEPTH/Q_DETECT do not explain well. Donor-held-out transfer is strong in SEA_AD but not yet demonstrated in HVS/NPH52 at the tested linear model class. A second shortcut class is now open from CorrMask-style literature: uniform masking may let the model solve hidden genes from correlated visible partners. Historical JEPA graph-expanded masking already addressed a similar risk, but current V5 uses graph-free uniform target blocks and the historical graph cannot be blindly restored because pooled covariance can encode cohort structure. Current architecture candidates are residual-over-context prediction plus recurrence-audited hybrid dependency-aware masking, but neither is production authority. The biggest upstream blocker remains the current dataset-derived V5 teacher-target definition.

## Do not repeat these mistakes

- Do not jump from cell-level measurement sensitivity to donor averaging as a training-safety test.
- Do not treat source/operator covariance as purely technical.
- Do not call within-donor residual cross-view signal proven biology.
- Do not treat a negative ridge shortcut probe as proof that a deep model is safe.
- Do not residualize source/operator out of the molecular input just because it predicts well.
- Do not restore historical graph masking blindly.
- Do not select masking ratios or thresholds from protected/confirmation outcomes.
- Do not let the training sampler silently choose among empirical, source-uniform and donor-primary scientific estimands.

## Current major findings

### Measurement shortcut

`MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS`

Matched measurement-state predictor did not beat a cleaner predictor at any tested thinning level. Largest excess matched-state synergy was ~0.0051 R2 at p=.25.

### Pooled context shortcut exposure

On BASE mechanics, donor-held-out:

- context (source+operator+QC) -> V1: 0.4671 R2;
- V0 -> V1: 0.4666;
- both: 0.4982.

This is a real shortcut available to a pooled learner, but it is not a causal technical decomposition.

### Within-donor recurrence

Donor-centred, cell-held-out V0->V1 R2:

- HVS: 0.1906;
- NPH52: 0.2646;
- SEA_AD: 0.2487.

Measured-QC-only R2 is much smaller (0.0535, 0.0690, 0.0575 respectively), and QC adds only ~0.003 after V0.

Safe interpretation:

`WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES`

### Donor transport

Operator-centred donor-held-out V0->V1 R2:

- HVS: 0.0437;
- NPH52: 0.0530;
- SEA_AD: 0.2402.

SEA_AD currently shows donor-generalizable simple-model cross-view signal; HVS/NPH52 do not yet.

### Loss geometry

Layer-normalized target proxy preserves the same qualitative picture. This is `MECHANICS_ALIGNED_PROXY_ONLY`, not a current V5 objective result.

### Masking shortcut

CorrMask literature establishes a plausible second shortcut class: hidden genes can be reconstructed from correlated visible partners under independent random masking. Historical JEPA contains Pearson-graph expanded target masking; current V5 fail-closed path uses uniform graph-free target blocks.

Terminal:

`MASKING_SHORTCUT_AUTHORITY_NOT_YET_RESOLVED`

## Current architecture candidates — not frozen

Leading concept:

`prediction = stop_gradient(frozen_context_baseline) + molecular_increment`

with loss against the full teacher target.

The molecular increment is not called biology; it is `PREDICTIVE_INFORMATION_BEYOND_FROZEN_CONTEXT_BASELINE`.

Masking candidate:

hybrid random + recurrence-audited dependency-aware structural masking, with explicit coverage and context-dependence audits.

Generic bottleneck is secondary because low-dimensional source/operator identity may survive compression better than subtle biology.

## Current blockers

1. Current V5 teacher-target authority not established.
2. Context shortcut handling not frozen.
3. Masking shortcut authority not resolved.
4. HVS/NPH52 donor transport unresolved.
5. Scientific training estimand not frozen.
6. Prospective shortcut comparator family not frozen.
7. Primary representation authority not frozen.
8. Rank support not frozen.
9. Measurement robustness decision rule not frozen.
10. V3 null not frozen.
11. FULL104 measurement procedure not qualified.
12. D_shared remains sealed.

## Immediate work order

Heavy-machine/Claude lane should finish, on frozen arrays only:

- independent reproduction of context decomposition;
- estimand-weight sensitivity under explicit empirical/source-uniform/donor-primary views where valid;
- donor-level recurrence distribution;
- full-refit donor-generalization uncertainty where feasible.

Then stop before training.

Design/local lane should:

- resolve the current V5 teacher/student target;
- audit historical graph-masking lineage and current uniform-mask shortcut exposure;
- design outcome-blind masking diagnostics and a frozen context shortcut family;
- sandbox residual-over-context and hybrid masking before any production trainer change.

## Hard boundaries

`TRAINING_OFF`

`NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION`

`NO_PROTECTED_DATA_USE_FOR_DESIGN`

`NO_TD60`

`NO_RELATIONAL_TARGET_ACTIVATION`

