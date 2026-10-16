# JEPA PR #221 / PR #222 runtime convergence contract — 2026-10-06

## Decision

PR #222 remains the canonical reconciliation spine. PR #221 is donor-only. Do not merge both independently.

Reason:

- #222 has the stronger exact-V3 governance binding, same-shape scientific-spillover rejection, one-update authority surface, one-shot EMA/receipt semantics, and adversarial spillover tests.
- #221 contributes useful real PyTorch / inactive-consumer integration, checkpoint-envelope ideas, and CPU-PyTorch CI, but it also carries a parallel guard vocabulary and broader canonical project-surface edits that should not become a second runtime authority.

## Exact observed heads

- PR #222: `890f8800501909a8fad0564b7240bf8e8f7c069e`
- PR #221: `a87bcfea68fce44ad4b2056ac4a903b3d1f5ac2a`
- base main: `f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Both PRs remain draft/open. Training and Stage A remain OFF.

## What to keep from #222

Preserve as authoritative:

1. `PrefreezeMechanicalAuthorityV1` semantics.
2. Exact merged V3 governance digest binding; same-shape scientific mutation must fail closed.
3. Exact governance/receipt schema closure.
4. Concrete optimizer-object pre/post hook guarding rather than caller-supplied counters/probes.
5. Post-unscale gradient validation ordering.
6. Ambiguous optimizer/EMA failure poisoning.
7. One-shot EMA.
8. Exactly-one-update prefreeze boundary.
9. One-shot completed-checkpoint receipt and current-governance verification.
10. Explicit non-authorizing lane boundaries.

Do not weaken these contracts to accommodate #221.

## What to harvest selectively from #221

Treat the following as donor mechanics, not as authority:

1. CPU-PyTorch CI installation and focused real-optimizer tests.
2. Integration with `src/sea_ad_jepa/v5/inactive_update_reference.py`.
3. The idea of a thin guarded wrapper around the inactive one-update consumer.
4. Real parameter-mutation tests proving direct step rejection.
5. Interrupted/resumed inactive reference tests already present in `test_teacher_student_v5_inactive_update_reference.py`.
6. Checkpoint-envelope binding ideas, especially binding the premise state and runtime source identity.

Do not wholesale copy #221's startup/current-authority documentation rewrites or preserve a separate `InactiveReferenceOptimizerStepGuardV1` as a second canonical guard.

## Important #221 limitations discovered in convergence audit

1. #221 has its own independent guard type and therefore cannot remain alongside #222 as a peer authority.
2. `run_guarded_inactive_reference_update` temporarily replaces `modules.optimizer` with a proxy, restores the underlying optimizer afterward, closes/removes the guard, and therefore does not by itself establish process-wide mutation exclusivity after the call.
3. The wrapper proves optimizer completion before the inactive reference executes EMA, but EMA remains mutation logic inside `inactive_update_reference.py`, not an independently guarded ownership surface.
4. The checkpoint envelope hashes premise/runtime source and wraps the reference checkpoint, but it is still an in-memory proof object. It does not establish persisted-byte provenance, GradScaler state, all RNG/sampler/accumulation state, or a production restart schema.
5. #221 real-optimizer unit tests include a simple SGD hook test; the inactive consumer itself uses AdamW and provides stronger path evidence, but final qualification must exercise the exact final optimizer configuration.
6. #221 does not close AMP/GradScaler skip semantics.

## Convergence implementation rule

Create one implementation path on the #222 branch (or a direct successor branch from #222 if isolation is required). Do not merge #221 first.

Target path:

`exact merged V3 governance -> PrefreezeMechanicalAuthorityV1 -> canonical inactive V5 consumer -> backward -> unscale -> gradient validation -> guarded real optimizer/scaler transition -> physical completion proof -> one-shot EMA -> persisted checkpoint -> exact restart verification`

#222 authority/guard semantics must wrap/adapt the real inactive consumer; #221's separate guard should not survive as a second canonical implementation.

## RED-first convergence gates

Before donor code is transplanted, add RED tests on the #222 convergence branch for:

1. Real `torch.optim.AdamW` is bound to the #222 guard and direct `optimizer.step()` is rejected while owned.
2. The canonical inactive consumer performs exactly one guarded update through #222, not through a second guard/proxy authority.
3. If `backward()`, `unscale()`, or gradient validation throws after token arming, the authorization is unusable/poisoned and cannot later be salvaged.
4. Under AMP/GradScaler overflow/skip, no optimizer completion is recorded, EMA does not advance, and the lawful update cursor does not advance.
5. Optimizer provenance is derived/verified from the actual optimizer class/config rather than trusting a free string label.
6. No alternate reachable optimizer/EMA mutation route exists within the canonical consumer lifecycle.
7. Checkpoint-write failure cannot mint a completed checkpoint receipt.
8. The completed checkpoint digest is derived from the actual persisted bytes/object serialization being restored, not merely a caller-returned arbitrary digest.
9. Checkpoint includes all state required by the deterministic claim: online/student, predictor, EMA teacher, optimizer, scaler if used, authority/guard cursor, update/accumulation position, RNGs, sampler/data position and required config/provenance.
10. Uninterrupted bounded synthetic trajectory and checkpoint->reload->resume trajectory are equal to the exact deterministic strength claimed.

Only after REDs exist should #221 donor mechanics be adapted to satisfy them.

## PR disposition

- Keep #222 draft while convergence is in progress.
- Keep #221 open only long enough to preserve reviewable donor provenance.
- Once #222/successor contains the selected donor mechanics with provenance documented and tests green, mark #221 superseded/close it without merging.
- Do not independently merge #221 and #222 into main.

## Synthetic/V77 join

Claude/Macha is the same local GPU-laptop agent and should continue V77 adapter/target/checkpoint-ladder work in parallel. The synthetic adapter must join only at the canonical model-batch/consumer boundary. No synthetic-specific optimizer, EMA, or authority path may be created.

Actual synthetic optimizer mutation remains separately unauthorized until the bounded synthetic-rehearsal contract is explicitly approved.

## Merge criterion

Focused #222 pure-Python green is necessary but insufficient. Final runtime mechanics sign-off requires:

- one canonical consumer;
- exact V3 authority/spillover protections preserved;
- real PyTorch/AdamW evidence;
- physical AMP/GradScaler skip evidence;
- optimizer provenance/ownership closure;
- complete deterministic restart evidence;
- whole-diff/lane/historical-spillover self-audit;
- no Stage-A/training/protected-data authority introduced.
