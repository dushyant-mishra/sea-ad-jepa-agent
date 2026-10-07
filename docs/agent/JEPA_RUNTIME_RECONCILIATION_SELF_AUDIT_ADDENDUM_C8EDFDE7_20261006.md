# JEPA runtime reconciliation — exact-head self-audit addendum — c8edfde7 — 2026-10-06

This addendum supersedes the current-head section of `JEPA_RUNTIME_RECONCILIATION_FULL_SELF_AUDIT_20261006.md` where the branch has advanced since that document was written.

## Exact current runtime head audited

`reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

Head:

`c8edfde7f2a38a94472a891e48e18d2a9c83fc77`

Commit:

`Bind rehearsal authority to exact merged V3 governance digest`

## What materially improved

The runtime authority now carries a fixed canonical digest for the merged V3 prefreeze governance state:

`CANONICAL_V3_GOVERNANCE_DIGEST = ab0603b0a9c92c3680badc252205ddd27fa74ae83ef3ada4019b4dcf637b7611`

`_canonical_prefreeze_governance()` rejects a canonicalized supplied governance object unless its digest equals that exact approved digest.

This is the correct direction for the prefreeze contract because future scientific-governance changes must require an explicit successor rather than silently inheriting current rehearsal authority.

Therefore the prior same-shape semantic-spillover defect is now addressed in implementation intent.

## Current test-history contradiction

The exact head remains RED.

A stale reconciliation test still contains the superseded contract:

`test_entire_governance_object_is_digest_bound`

It mutates `claim_ladder`, then expects both the canonical and altered governance states to issue valid authorities with different digests.

That is no longer an acceptable contract.

The newer red-team test correctly requires a structurally valid scientific mutation to fail with the canonical-V3-governance-digest mismatch.

These two tests are mutually incompatible.

Do **not** remove or weaken exact canonical governance binding to satisfy the older test.

Replace the stale test with a test that proves the approved canonical state is accepted and a same-shape semantic mutation is rejected.

This is a direct example of historical test spillover: a previously useful invariant (`all supplied governance is digest-bound`) became weaker than the successor invariant (`only the exact approved governance may issue this authority`).

## Still-open runtime issues unchanged by c8edfde7

Exact governance binding does not close the remaining mutation-path work:

1. `optimizer_identity` remains a caller-supplied provenance label; object binding is stronger than provenance binding.
2. Focused CI still installs only `pytest`; real `torch.optim.AdamW` and GradScaler behavior are not qualified.
3. `GradScaler.step()` skip must physically prove no EMA and no lawful cursor advance.
4. `prefreeze_guarded_rehearsal.py` still needs REDs requiring callback exceptions in `backward`, `unscale`, and gradient validation to make the armed authorization unusable.
5. The focused guard only controls optimizer stepping while hooks own the optimizer; canonical consumer ownership/reachability remains required.
6. The checkpoint callback supplies a digest; persisted-byte provenance and deterministic restart completeness remain unproved.
7. The branch still needs integration into the canonical inactive/test-only V5 one-update path, not a second trainer.
8. Synthetic/V77 anti-cheat rehearsal must enter only through that canonical consumer after explicit bounded mutation authorization.

## Exact-head decision

`c8edfde7...` is **not merge-ready** until the stale contradictory test is repaired and exact-current-head CI is re-run.

Even after focused CI becomes GREEN, PR #222 is not yet a fully qualified canonical mutation boundary until the real PyTorch/AMP, canonical-consumer, ownership, and deterministic-restart work is physically demonstrated.
