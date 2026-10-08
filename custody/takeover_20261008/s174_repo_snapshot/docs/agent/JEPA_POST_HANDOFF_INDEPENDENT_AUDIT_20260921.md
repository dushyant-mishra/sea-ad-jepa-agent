# JEPA post-handoff independent audit — FULL104 target / Audit-B preexecution

Date: 2026-09-21

Status: `OUTCOME_BLIND_INDEPENDENT_AUDIT__N1_UNOPENED__TD60_UNEXECUTED__TRAINING_OFF`

Audited scientific base:

`integrate/v5-full104-gpt-claude-20260921 @ 3bf6b659de9bdd2711face82b50b47ec567ea449`

Handoff checked separately:

`handoff/jepa-v5-full104-target-etl-20260921 @ 034be1949c389c93a26d8476ceedbcd402c55505`

The handoff is exactly one docs-only successor to the scientific head. The older
`48ea7a6752f330606e0505ac36af9e4f47901379` state is retained as historical
context but is superseded by the verified `3bf6b659...` scientific authority.

## Protected-state confirmation

This audit did not open or compute:
- Audit-B N1 burden outcomes;
- terminal masking outcomes;
- TD60 learned-teacher outcomes;
- D_shared protected outcomes;
- pathology-adaptive decisions;
- DEV/SEALED expression;
- G5 terminal margin;
- a terminal target panel;
- training.

## Repository / CI findings

At the audited scientific head all four hosted workflows are green:
- V5 runtime closure;
- V5 remaining-RNA and target-semantics successor;
- V5 Stage-A spillover firewall;
- V5 FULL104 masking runner.

The September-21 handoff manifest declares 178 current repository files and six
external heavy assets. The load-bearing current roots and the workflow-enforced
source/test paths were independently checked during this audit. A literal
178-file content replay is connector-rate limited; no mismatch was observed in
the audited load-bearing roots.

## Closed / supported findings

1. **Phase-I V2 real-data qualification remains PASS.**
   The content-addressed sufficient-statistics artifact is bound to
   `f77dff47...`; all 104 donor source-library totals and all 4,553,407 per-cell
   source assignments were verified.

2. **Phase-III estimability edge cases are closed.**
   Missing required groups, empty evidence, and materially negative
   sum-of-squares cannot silently become valid numeric evidence.

3. **Audit-B V1 remains permanently preexecution-only.**
   Naming a resolved precision scope cannot activate N1.

4. **RNG V3 semantic design is sound.**
   Target-panel choice cannot reroll masks; allowed keyed namespaces are closed;
   fold codes are restricted to the authenticated 0..3 range. The real V3 receipt
   is still a B3 materialization task.

5. **Target discovery must not restart.**
   TD56/TD57B/TD58/TD59 are the surviving relational evidence; TD60 remains the
   unexecuted learned-teacher continuity bridge.

6. **Target-qualification sampling is mechanically strong.**
   It is donor-capped (1,024), identity-only, expression/QC/class/pathology blind,
   and closes to the frozen 105,553-cell geometry in synthetic regression tests.
   The real sample has not been materialized.

## Finding A — Audit-B weighting choice was not genuinely open in V1 provenance

Severity: HIGH preexecution design issue; no outcome affected.

The handoff correctly says weighting is still a prospective scientific choice,
and distinguishes the donor-uniform base scientific population from a
source-balanced estimand. However, `AuditBScientificResolutionV1.validate()`
accepts only the existing source-balanced `TARGET_AGGREGATION_ID`. Thus a
future resolution could not actually record the donor-uniform alternative without
first changing implementation.

Outcome-blind hardening on this audit branch:
- added a donor-uniform target aggregator with complete donor/source guards;
- retained the original source-balanced V1 aggregator unchanged;
- added `AuditBScientificResolutionV2`, which can record either implemented
  weighting without selecting one;
- added regression tests proving the two estimands differ under source imbalance;
- V1 remains frozen and non-executable.

No weighting has been selected by this audit.

## Finding B — precision/RSE blocker is broader than exact zero mean

Severity: HIGH scientific choice; OPEN.

The current RSE is `SE / abs(mean)`. Exact zero is already fail-closed, but a
very small nonzero burden effect can also yield arbitrarily large RSE even when
absolute uncertainty is small. Therefore B2 cannot be considered resolved merely
by choosing:
- single-primary versus all 18 policy×rung cells; and
- STOP versus ESCALATE at exactly zero mean.

A reviewed decision must determine whether the frozen RSE formulation itself is
scientifically appropriate near zero, or whether a successor precision estimator
(e.g. a prospectively defined absolute/relative hybrid) is needed. This audit does
not choose such an estimator.

## Finding C — q95 rare-tail integer/tie semantics were underspecified

Severity: MEDIUM preexecution design issue; hardened prospectively on this branch.

The design froze q95 and selection-row tie breaking, but did not specify the exact
integer tail count or how non-finite Z isolation anchors enter the quantile. Those
choices can alter tail membership in small donor×operator strata.

Outcome-blind hardening on this branch:
- non-finite Z isolation is treated as missing support, not low isolation;
- q95 is implemented as the exact ranked top 1/20 of finite anchors:
  `ceil(n_finite / 20)`;
- integer arithmetic is used to avoid floating-point ceil drift;
- equal isolation is resolved by authenticated global `selection_row` ascending;
- no per-operator minimum is introduced;
- the existing >=5 pooled tail anchors per donor remains unchanged.

No rare-tail molecular outcome has been opened.

## Finding D — target-sample validation lacked independent full-source replay

Severity: MEDIUM hardening opportunity; CLOSED ON THIS AUDIT BRANCH.

The builder authenticates the Level-4 manifest and every metadata block, traverses
all 4,553,407 selection rows exactly once, and constructs a content-addressed
receipt. The original downstream validator rehashed the produced arrays and
builder source and checked geometry, but did not independently reconstruct the
sample from source metadata.

Outcome-blind hardening now adds an optional full-source replay mode to the
validator. When run on the GPU/full-data machine it:
- authenticates the Level-4 block manifest and every metadata block;
- independently reconstructs the frozen selection-hash preimage;
- traverses the 4,553,407 global selection rows exactly once;
- re-derives donor/source/fold identities from the authenticated split;
- independently rebuilds the donor-wise bottom-k sample;
- requires exact equality of selection rows, donor codes, row ranks, retained
  counts, full donor counts, folds and source codes;
- never opens expression/count matrices.

The real 105,553-cell package is still unmaterialized, so the heavy replay has not
yet been executed.

## Finding E — inherited donor-half naming drifted into the four-fold rare-tail design

Severity: MEDIUM semantic/provenance issue; CLOSED ON THIS AUDIT BRANCH.

The rare-tail authority uses the authenticated FULL104 four-fold split, but its
minimum measurable donor field was named `min_measurable_donors_per_half`, a
leftover from TD59's old donor-half evaluation. The threshold value 4 was correct,
but the label was semantically wrong for a future authority receipt.

The field/constant are now source-fold explicit:
`min_measurable_donors_per_source_fold = 4`.

## Remaining lawful next steps

### Audit-B
1. Keep N1 closed.
2. Resolve B2 scientifically, including near-zero precision behavior and weighting.
3. Build the real RNG-V3 receipt from current authenticated roots.
4. Issue a provenance-bearing successor execution contract.
5. Require exact-head green/no-skip CI.
6. Only then execute N1 exactly once under the frozen escalation rule.

### Target / rare biology
1. Materialize the real 105,553-cell target-qualification sample metadata-only.
2. Run the independent metadata-only source replay when the real sample is materialized.
3. Finish/freeze the exact rare-tail molecular evaluator and null/replay execution contract.
4. Only then execute the label-free molecular rare-tail prequalification.
5. Preserve any result as qualification evidence only.
6. Keep TD60 closed until a lawful teacher exists.
7. Keep training OFF until the complete training-authority graph closes.

## Terminal

`AUDIT_COMPLETE_TO_PREEXECUTION_BOUNDARY__WEIGHTING_PROVENANCE_HARDENED__Q95_MECHANICS_HARDENED__B2_B3_B4_OPEN__REAL_TARGET_SAMPLE_UNMATERIALIZED__RARE_TAIL_UNEXECUTED__TD60_UNEXECUTED__N1_UNOPENED__TRAINING_OFF`
