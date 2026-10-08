# CONTEXTUAL TARGET V1 F0 — external-review handoff

Status: `PASS_CONTEXTUAL_TARGET_V1_F0_IMPLEMENTATION_AWAITING_EXTERNAL_REVIEW`

F0 implemented a new isolated, parameter-free query-local constructor. It owns the frozen encoder call, uses student-style evidence masking for both roles, constructs `LayerNorm(H_q - exact_mean(H_visible_context))` from one forward, detaches teacher-role output, and preserves student-role differentiation. It does not create or select a learned head.

## Review these first

1. `CONTEXTUAL_TARGET_V1_F0_UNIFIED_DIFF.patch`
2. `CONTEXTUAL_TARGET_V1_F0_CHANGED_SOURCE_SNAPSHOT/`
3. `CONTEXTUAL_TARGET_V1_F0_REFERENCE_PARITY.json`
4. `CONTEXTUAL_TARGET_V1_F0_METAMORPHIC_RESULTS.json`
5. `CONTEXTUAL_TARGET_V1_F0_FIREWALL_RESULTS.json`
6. `CONTEXTUAL_TARGET_V1_F0_RED_TEAM.md`
7. `CONTEXTUAL_TARGET_V1_F0_IMPLEMENTATION_MANIFEST.json`

Key results: 42/42 operator singleton parity PASS; safe `x_q` intervention and gradient exactly zero; unsafe rich control max change `1.7270266`; non-q `H_q` gradient `2.52016e-4`; non-q `H_q` intervention change `5.80549e-5`; 870,860 measured-zero context slots; 11,449 natural code2 slots; all protected firewall attacks zero payload reads; model SHA unchanged; optimizer/EMA/training counts zero.

The numerical rule was serialized before reference/adversarial interpretation. Exact semantics are required for identities, physical/evidence/hidden masks, query indices/addresses, context indices/counts, and provenance. Float intermediates report maximum absolute/relative error against that frozen rule.

The prior failed/superseded attempts remain in separate output directories as engineering provenance. They are not part of the current authority.

## Hold

External code review only. Do not run FULL104 F1, protected biology, learned prediction, optimization, EMA updates, budget derivation, or training from this status.
