# Unified Task 4 successor-5 — regeneration-provenance review packet

Status: `CANDIDATE_ONLY__EXACT_HEAD_GREEN_AND_INDEPENDENT_REVIEW_REQUIRED`.
This packet supersedes the *current-state interpretation* of the historical
successor-4 packet. It does not delete or rewrite that evidence.

## Frozen authority
- Task 0 `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1 `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2 `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 3 `117dd51dea827e734b299982da93991b934bdc8f` (`ACCEPT_UNIFIED_TASK3`)

## Immutable RED lineage
1. `b31371d62f3270c965d321e61c35898ca6be3721` — rejected caller-self-minted authority roots.
2. `c537db4e7b5b916cb3ddee1872fd4afa623a9b33` — rejected post-seal substitution.
3. `b5ed724cbc6a39d4f2cd68103c5367c2cfafcff3` — rejected fabricated advanced campaign lifecycle.
4. `d41720be93db27801fdac1ae62cfd608084dce25` — rejected post-reveal terminal accounting.
5. `56b864e2b944956746771fb5d26040835d093dd5` — superseded mechanically-green review pin with stale artifacts.
6. `068880822bca8036e605e3c5264770ce89057fee` — rejected after PR #417 replayed rows falsely qualified as regeneration: RED run `39000234158`, job `117301422733`.

## Successor-5 RED-first and repair sequence
- From exact predecessor `06888082...`, PR #418 first ported the PR #417 failing attack in commit `d1635b46...`.
- `e60689c5fe6b8319e2d40037bc25a7a62ab421dd`: first DEVELOPMENT-only deterministic fixture-generation repair. It removed caller-supplied row acceptance, checked pinned generator source/policy/RNG identities, and preserved FINAL fail-closed.
- Independent PR #419 then exposed a second bypass: an attacker substituted a new Python function with the same code object/source but a different `__globals__` row-hash helper. A copied-output replay reached `REGENERATION_VERIFIED`. RED run `39083015888`, job `117543716134`.
- PR #420 retained the RED test and closed that specific DEVELOPMENT bypass by checking original generator object/code and helper binding. Exact code/test head `441b24971668a6ea916205f79fd5f6abec4f0abc` passed read-only CI:
  - Task 4 run `39083139869`, job `117544081882`: focused **121 passed, 1 skipped**, projected 100k replay **1 passed**, full unified Task 0–4 **312 passed, 1 skipped**.
  - Task 2 `39083139883` PASS; Task 3 registry `39083139871` PASS; unified synthetic integration `39083139868` PASS.
- The repair was fast-forwarded into PR #418 with an exact expected-head lease, preserving both RED reviews and the mechanical GREEN.
- The code/test head above precedes this review-packet addition. The *final review head* must be pinned separately after CI passes against the final source SHA. Do not substitute this earlier code/test SHA for the final review SHA.

## What this does and does not prove
- An ordinary DEVELOPMENT caller cannot obtain regeneration status merely by replaying sealed rows or swapping a generator function with different bound globals. A fresh pinned synthetic generator invocation is required.
- DEV receipts and lifecycle registries remain **process-local** and **non-authorizing**; they do not constitute external execution attestation. Direct malicious mutation of module-private internals remains an open C9 process-isolation limit.
- FINAL remains fail-closed without independently authenticated external authority context, durable cross-process execution provenance, and reviewed C1–C9 controls.
- No real hidden biological challenge or training execution is authorized.

## Required independent review
Review exactly one immutable green candidate SHA on a separate branch. Attack echo, deep-copy, same-source/different-globals, generator code/policy/RNG replacement, sealed definition/root swap, before-reveal and post-reveal mutation, campaign fork, stale execution event, receipt replay, process restart/rehydration, direct construction and C1–C9 authority boundary. The reviewer must return `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE` tied to that SHA. Do not infer acceptance from CI alone.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
