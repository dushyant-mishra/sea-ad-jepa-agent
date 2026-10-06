# Shared qualification interface V1 — whole-branch adversarial audit checkpoint — 2026-10-06

## Scope

This checkpoint records the ongoing adversarial audit of draft PR #223 (`shared-qualification-interface-v1-20261006`) after Tasks 1–8 and the S146/S147 measurement-binding repair.

The audit is deliberately RED-first. It does not authorize training, Stage A execution, protected-data execution, optimizer mutation, EMA mutation, or promotion of any scientific target/representation/estimand.

## Closed defects in this audit pass

### A1 — oracle truth realization was not bound to frozen outputs

Before repair, `unblind_oracle()` checked frozen state and run ID but did not prove that the oracle truth belonged to the synthetic realization that produced the frozen outputs. A truth payload from realization B could therefore be paired with outputs from realization A under the same run ID.

RED:
- `a2b2fd4fc7478d43063bd685800aed43df58e612`
- workflow `37544070447`: expected failure.

GREEN:
- `ac436ba5b1a383be00b384abf20a8afcbf9ccfeb` — frozen outputs carry synthetic realization identity and unblinding requires an exact match.
- `6b75ce7ce12857459da774ccb0f74488aaae730c` — zero-update pipeline propagates the authenticated batch realization into frozen outputs.
- workflow `37544242909`: SUCCESS.

### A2 — non-authorizing scientific authority still permitted callback execution

`ScientificExperimentAuthorityV1(evaluation_authorized=False)` is a valid representation of known-but-not-authorized state, but the execution boundary previously failed to check that boolean after structural authority validation.

RED:
- `75fc3b5a3172fdd98fa13ab9a9026d6c430071cf`
- workflow `37544421788`: `1 failed / 126 passed`; sole failure was the expected non-authorizing execution bypass.

GREEN:
- `1026e2f56ba6dc18bf0899da488f386eb330a817`
- runner now refuses callbacks unless scientific evaluation authority is affirmatively true.
- workflow `37544533744`: SUCCESS.

### A3 — development/calibration partition could be minted as prospective sealed challenge

Oracle unblinding previously hard-coded `PROSPECTIVE_SEALED_CHALLENGE`, ignoring the challenge partition bound into synthetic provenance.

Initial RED exposed missing partition identity on frozen outputs, then the RED was narrowed to the actual promotion defect:
- `e39cc47914d188dfcfcd6b690ba3b6d154f07632`
- workflow `37544824265`: `1 failed / 127 passed`; development partition was returned as prospective.

GREEN sequence:
- `b9ec0426b8e7e24eddd4b138f7483f52291552a9` — frozen outputs carry challenge partition and unblinding maps rather than invents status.
- `de3fe48c0a983c34fcbf37ab81a1c38f761d44fb` — pipeline propagates batch challenge partition.
- `9b7256bd83da1f06d0232f5974b331afe9a3dd82` — oracle tests migrated to the strengthened schema.
- workflow `37545078986`: SUCCESS.

## Architectural result — physical no-mutation is NOT proven by PR #223

A stronger RED demonstrated that the generic Python callback boundary cannot prove physical no-mutation. A callback can mutate state through a closure and return a benign dictionary; the existing payload-key defense does not see the side effect.

RED:
- `a0cae135c3b642a9108b5f2200d0ed0998886698`
- workflow `37545158463`: `1 failed / 128 passed`.
- exact failure: hidden callback side effect did not raise `ZeroUpdateViolation`.

This is not being hidden behind more string heuristics. PR #223 now makes the limitation explicit and machine-readable:

- `MutationProofStatus.NOT_PROVEN_BY_SHARED_INTERFACE`
- `MutationProofStatus.PROVEN_BY_BOUND_RUNTIME`

A provenance receipt cannot claim `PROVEN_BY_BOUND_RUNTIME` without a bound `runtime_successor_digest`.

Implementation:
- `cdffa4a902da035b1399741a6775855d6ff76f3d` — mutation-proof status added to qualification provenance; runtime-proven status requires runtime-successor provenance.
- `66c553efb099b162bcad383e168da242f9ad1dd6` — frozen outputs expose mutation-proof status.
- `07ce5b833a683ffea53e09ed0635f37e7e9aa740` — shared zero-update runner explicitly emits `NOT_PROVEN_BY_SHARED_INTERFACE` in provenance and outputs.
- `902de2ee46f62f0dc01122aa48970843a19662f7` — regression test verifies a hidden side effect is not falsely represented as physically proven no-mutation.
- workflow `37545418354`: SUCCESS.

### Consequence for runtime convergence

PR #223 may enforce:
- mutation is not authorized;
- execution mode is zero-update qualification;
- visibility and provenance firewalls;
- obvious mutation/EMA signals in callback payloads are rejected as defense-in-depth.

PR #223 may **not** independently claim:
- model parameters physically did not mutate;
- optimizer state physically did not mutate;
- GradScaler state physically did not mutate;
- EMA teacher physically did not mutate.

Those proofs must be supplied by the bound runtime successor during #221/#222 convergence. This is the same trust-boundary lesson as the caller-supplied optimizer-step probe defect already identified in PR #222: an arbitrary callback/probe cannot be treated as conclusive physical authority evidence.

## PR #223 merge status

Still draft / NOT READY TO MERGE.

Remaining whole-branch audit targets include:
- retry/child-run lineage identity;
- oracle demotion/current-status semantics;
- q-safety transformation enforcement boundary;
- final diff and CI/path-trigger audit;
- explicit runtime-convergence contract for future physical mutation proof.

## Scientific lane boundary

S149 still reopens the real-data calibration target question. This interface audit does not choose within-cohort vs mixture-weighted vs hierarchical vs conditional-residual calibration. That remains a prospective scientific/reviewer decision.

## Hard authority state

- TRAINING = OFF
- STAGE_A_EXECUTION = OFF
- MULTIMODAL_TRAINING = OFF
- 500K = NOT_AUTHORIZED
- STAGE4 = NOT_AUTHORIZED
- TEST = SEALED
- MORABITO = PROTECTED
- no optimizer/EMA mutation authority from PR #223
- no representation winner selected
- no target winner selected
- no estimand selected
- no deciding real-data threshold selected
