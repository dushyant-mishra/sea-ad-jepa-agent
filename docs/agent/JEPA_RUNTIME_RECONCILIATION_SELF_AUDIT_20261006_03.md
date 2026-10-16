# JEPA runtime reconciliation self-audit 03 — 2026-10-06

Audited implementation head:

`de36481409773b7396d536602ec6d1048ee247a4`

PR:

`#222`

## Scope of this self-audit

This pass checked whether the current optimizer-bound guard supports the claims now being made about identity, exclusivity, and historical-spillover protection.

## Finding 1 — optimizer object binding is real; optimizer identity provenance is not yet exact

`PrefreezeOptimizerGuardV1` is installed on a concrete optimizer object and observes that object's step hooks. This materially improves on the superseded caller-counter design.

However, `optimizer_identity` remains a caller-supplied string stored in the authority. The guard verifies that callers repeat that string, but does not prove that the string truthfully describes the optimizer object.

Therefore:

- `optimizer object bound at mutation boundary` = supported by focused design/tests;
- `exact optimizer identity/provenance bound` = OPEN.

Required future RED: an authority labeled for AdamW must not be able to silently guard an incompatible optimizer implementation merely because it exposes compatible hooks.

The local canonical consumer should derive/verify optimizer provenance from the actual configured optimizer/adaptor, not trust a free label.

## Finding 2 — guard ownership is not process-wide optimizer ownership

While the guard hooks are installed, direct/wrong-token optimizer stepping is rejected.

`guard.close()` removes those hooks. If another caller still holds the underlying optimizer object, it can subsequently call the optimizer directly.

Therefore the guard module by itself does not establish global exclusivity of mutation.

This is not necessarily a defect in the one-update guard abstraction, but it is a hard integration requirement:

- the canonical consumer must own optimizer reachability/lifecycle;
- no alternate caller may retain an unguarded mutation handle;
- post-guard direct mutation must be unreachable in the real rehearsal/trainer composition.

Required future bypass test at canonical-consumer level: after the guarded update boundary is consumed/closed, no reachable execution path can mutate the same optimizer/model outside authority.

## Finding 3 — exact governance shape is still not exact governance semantics

Recorded in the live supplement and remains OPEN.

At this head, same-shape changes to legitimate governance values/lists can still be hashed into a new valid authority unless separately rejected.

This remains a historical-spillover risk. Strict canonical-governance digest/reference binding is preferred for the prefreeze adapter unless controlled variation is explicitly specified and tested.

## CI state at this audited head

GitHub Actions at `de364814...`:

`2 failed, 46 passed`

Both current failures are diagnostic-precedence issues:

1. V64 schema substitution is rejected by exact-field mismatch before schema-specific rejection;
2. a second optimizer attempt after the first update is rejected by exactly-one-update before the more specific pending-EMA reason.

Do not weaken fail-closed behavior to satisfy these diagnostics; reorder checks if preserving the test semantics is still desired.

## Self-audit verdict

Do not merge or describe PR #222 as a fully qualified canonical mutation boundary yet.

Current supported claim is narrower:

> The focused prefreeze adapter now binds mutation to a concrete guarded optimizer object for one rehearsal update and adds meaningful fail-closed state-machine controls, but canonical governance semantics, truthful optimizer provenance, process-wide optimizer exclusivity, real AMP/GradScaler behavior, canonical-consumer integration, and deterministic restart remain unqualified.

Hard boundaries remain unchanged: training OFF, Stage A OFF, TEST sealed, Morabito protected.
