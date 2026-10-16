# JEPA runtime reconciliation — full iterative self-audit — 2026-10-06

This document audits the runtime-reconciliation work from its beginning through the current PR #222 state. It is intentionally stricter than a progress summary: it records what was established, what was later superseded, where tests or wording lagged implementation, what historical-spillover risks remain, and what must be physically proven before merge or any mutation authorization.

## Operating rule

Do not advance a claim merely because an earlier head was green. Every substantive step must pass:

1. exact-head verification;
2. claim-vs-evidence review;
3. historical-spillover review;
4. lane-boundary review;
5. surrogate-vs-real-behavior review;
6. handoff checkpoint.

Training, Stage A, multimodal training, 500K, Stage 4, TEST opening, and Morabito opening remain unauthorized.

## Agent identity correction

`Claude` and `Macha` are the same local agent on the GPU laptop. Earlier chat framing that treated them as separate workers was wrong and was corrected. The separate third lane is the other GPT agent doing real-data premise/qualification.

## Lineage audit

Authoritative runtime branch:

`reconcile/v64-runtime-core-onto-prefreeze-main-20261006`

Base:

`main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`

Open PR:

`#222 — Reconcile V64 runtime safety core onto prefreeze main`

Current exact head at this checkpoint:

`3cd78b95b44262cd4dd1673ce3123aefbf4273ca`

The branch is a direct selective-reconciliation lineage from post-PR-220 main. It does not whole-merge historical PR #219/V64.

Whole-diff scope from base to the current branch remains limited to seven files:

- `.github/workflows/v64-runtime-core-reconciliation.yml`
- `docs/agent/JEPA_V64_RUNTIME_CORE_RECONCILIATION_20261006.md`
- `src/sea_ad_jepa/v5/prefreeze_guarded_rehearsal.py`
- `src/sea_ad_jepa/v5/prefreeze_runtime_authority.py`
- `tests/test_v5_prefreeze_guarded_rehearsal.py`
- `tests/test_v5_prefreeze_runtime_authority_reconciliation.py`
- `tests/test_v5_prefreeze_runtime_authority_redteam.py`

No model, dataset, target-selection, or scientific-result file is modified by this PR.

## Development-history audit

The branch began RED-first and progressively tightened the runtime boundary. That direction is sound.

Key evolution:

- initial pure-Python rehearsal authority/guard;
- callback/caller-counter proof identified as too weak;
- replaced by optimizer-object pre/post hook binding;
- direct/wrong-token stepping rejection;
- post-unscale gradient-validation ordering;
- optimizer/EMA exception poisoning;
- one-shot EMA;
- exactly-one-update prefreeze boundary;
- one-shot completed-checkpoint receipt;
- exact receipt-field schemas;
- current-governance replay checks;
- explicit RED for same-shape scientific-governance mutation.

Several intermediate statements and documents became stale while the branch moved. Those older GREEN/RED counts remain evidence for those exact SHAs only and must not be propagated as current status.

## Current CI state

At exact head:

`3cd78b95b44262cd4dd1673ce3123aefbf4273ca`

GitHub Actions run:

`37532112006`

is RED.

The new head deliberately adds a RED requiring a structurally valid but scientifically altered V3 governance state to be rejected at authority issuance.

Do not merge this head and do not weaken the RED merely to regain green.

## Historical-spillover audit

### Closed / materially improved

The current code does not import the historical target/E2 authority graph and does not re-expose historical `CurrentTrainingAuthorityV2` / `OptimizerGuardV4` names as current authority.

Unknown/missing governance fields and unknown/missing receipt fields are being forced closed.

Old V64-style authority structures are rejected.

The whole V64 branch remains rejected as a merge strategy.

### Still open — exact canonical governance semantics

Schema closure is not the same as semantic closure.

A structurally valid supplied V3 object can still differ scientifically in fields such as:

- `claim_ladder`;
- `representation_families`;
- `source_documents`;
- `transport_axes`;
- `ood_axes`;
- `estimand_candidates`;
- observation-operator descriptor lists;
- representation-stability lists/strings.

The current RED at `3cd78b95...` correctly requires this class of mutation to fail at issuance.

The preferred prefreeze contract is exact binding to the approved canonical V3 governance state/digest, not merely self-consistency of a caller-supplied state.

A caller-supplied `governance_state` is not by itself a trust anchor. Reload/verification must not be satisfiable simply by supplying the same altered state that created a receipt.

## Optimizer-boundary audit

### Established in the focused surrogate

The guard is installed on a concrete optimizer object using step pre/post hooks.

Direct stepping without the correct armed token is rejected while those hooks own the object.

Wrong-token stepping is rejected.

Optimizer exceptions poison the guard.

A missing post-hook completion is treated as ambiguous and cannot authorize EMA.

Exactly one update is permitted by the prefreeze guard.

### Still open — optimizer provenance

`optimizer_identity` is still a caller-supplied string such as `adamw:v1`.

Therefore distinguish:

- optimizer object binding at the focused mutation boundary: supported;
- truthful optimizer identity/provenance binding: unproved.

The canonical consumer should derive or verify optimizer provenance from the actual configured optimizer/adaptor rather than trusting a free label.

### Still open — real PyTorch / AMP

The dedicated CI installs only `pytest`; it does not install or exercise PyTorch.

Therefore current CI cannot prove:

- actual `torch.optim.AdamW` hook behavior;
- `GradScaler.step(optimizer)` skip semantics;
- overflow/no-update behavior;
- scaler-state continuity.

A physical skipped scaler update must not authorize EMA or advance the lawful update cursor.

## Guard lifecycle / reachability audit

The focused guard protects direct optimizer stepping while its hooks are installed.

`guard.close()` removes those hooks. The underlying optimizer then remains a reachable object unless the canonical consumer controls ownership/reachability.

Therefore the guard alone does not prove process-wide mutation exclusivity.

The final canonical consumer must own the optimizer/scaler/EMA mutation surface and prevent alternate reachable mutation routes.

## Rehearsal callback audit

`prefreeze_guarded_rehearsal.py` remains deliberately one-update and callback-composed. It has not become a trainer.

However, callback failures before the optimizer boundary need stronger fail-closed treatment.

Current sequence arms a token and then invokes:

- `backward()`;
- `unscale()`;
- `validate_gradients()`.

A `False` validation result explicitly rejects the step, but exceptions raised by `backward`, `unscale`, or `validate_gradients` are not explicitly converted into rejection/poisoning by the rehearsal wrapper.

RED tests should require any such exception to make the authorization unusable and prevent later salvage/replay of the token.

## EMA audit

EMA ordering is correctly constrained in the focused state machine:

- no EMA before optimizer completion;
- optimizer/EMA failure does not yield a completed receipt;
- EMA authorization is one-shot.

Still open:

- actual teacher-parameter ownership in the canonical V5 consumer;
- prevention of direct/out-of-band EMA mutation outside the guard;
- physical behavior under GradScaler skip.

## Checkpoint/restart audit

Current checkpoint receipts provide digest lineage and authority/governance linkage.

This is useful but is not deterministic restart qualification.

The checkpoint callback currently supplies a digest; the guard does not itself prove that the digest was computed from successfully persisted checkpoint bytes.

Still required:

- online/student state;
- teacher/EMA state;
- predictor state;
- optimizer state;
- GradScaler state;
- runtime authority/guard cursor state;
- update/accumulation position;
- Python/NumPy/PyTorch/CUDA RNG as applicable;
- sampler/data order;
- exact registry/config/mask/view/provenance identities;
- interrupt/resume continuation equivalence.

A callback-returned digest is not sufficient evidence of persisted restart completeness.

## Current-main canonical consumer audit

Current main exposes `src/sea_ad_jepa/v5/inactive_update_reference.py`, an inactive one-update PyTorch mechanics reference.

It is explicitly not a trainer and already embodies important mechanics:

- real AdamW;
- gradient gate;
- exact single optimizer step check;
- EMA after optimizer step;
- in-memory reference checkpoint/replay mechanics.

The reconciliation branch still uses a separate pure-Python callback rehearsal. The endpoint should be integration into/adaptation of the inactive V5 one-update path, not creation of another trainer.

Repository search at audit time did not find current `ProductionTrainLoader` or `block_jepa_loss` symbols. Earlier claims that the synthetic adapter could simply plug into a current production trainer under those names were therefore not supported by current repository evidence.

## Synthetic/V77 integration audit

Calibration and anti-cheat rehearsal answer different questions and should remain separate.

Claude/Macha should continue in parallel on the GPU laptop:

- V77 generator dynamic-range qualification under frozen canonical evaluation universe;
- sign/community qualification after dynamic range;
- CSR -> model-visible synthetic adapter;
- hard separation of oracle-only truth;
- non-production synthetic rehearsal target;
- frozen checkpoint ladder and anti-cheat PASS/FAIL rules;
- zero-update end-to-end rehearsal.

But no synthetic-specific optimizer/EMA loop should be created. Synthetic rehearsal must enter through the same eventual canonical guarded V5 consumer.

No new IPBEncoder optimizer/EMA mutation is authorized yet.

## My own chat-side errors / corrections

1. I initially treated Claude and Macha as separate agents. Wrong; corrected.
2. I initially repeated an intermediate counter-probe design after the branch had already advanced to optimizer-object hooks. Corrected by exact-head refresh.
3. I allowed prior GREEN counts to appear too prominently before rechecking moving heads. The operating rule now requires exact-SHA status every time.
4. I initially focused on field-shape spillover before recognizing same-shape semantic mutation as the deeper governance problem. That deeper issue is now an explicit RED.
5. I described optimizer identity too strongly before separating object binding from provenance-label truth. Corrected.
6. I described checkpoint lineage carefully later, but earlier summaries risked sounding closer to restart qualification than the evidence allowed. The distinction is now explicit.

## Current status classification

### Established

- selective recovery strategy;
- lane separation;
- non-authorizing exactly-one-update rehearsal intent;
- optimizer-object hook binding in the focused surrogate;
- direct/wrong-token rejection while guard owns optimizer hooks;
- post-unscale validation ordering;
- optimizer/EMA failure poisoning;
- one-shot EMA;
- one-shot completed receipt;
- receipt/governance schema closure direction;
- no whole-V64 merge;
- training/Stage-A/protected-data boundaries remain closed.

### Open / RED / unproved

- exact approved canonical V3 semantic binding at authority issuance;
- trusted governance source rather than caller self-consistency;
- optimizer provenance binding;
- real PyTorch optimizer proof;
- AMP/GradScaler skip proof;
- pre-optimizer callback-exception poisoning/rejection;
- canonical V5 one-update consumer integration;
- process-wide optimizer/EMA reachability control;
- checkpoint-byte provenance;
- deterministic restart completeness;
- interrupt/resume equivalence;
- synthetic anti-cheat integration through canonical consumer;
- explicit bounded synthetic mutation authorization.

## Merge decision

PR #222 is **not merge-ready at this checkpoint**.

Reasons:

- exact current head is RED;
- exact canonical-governance issuance is still under RED test;
- real PyTorch/AMP behavior is unproved;
- canonical consumer integration is incomplete;
- restart completeness is incomplete.

Do not reinterpret this as a failure of direction. The branch has substantially improved the mechanical contract; it simply has not yet reached the evidence threshold required for merge or execution authority.
