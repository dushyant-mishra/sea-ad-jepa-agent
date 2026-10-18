# Unified Task 4 successor-6 — finite-exam anti-reset review packet

Status: `CANDIDATE_ONLY__INDEPENDENT_EXACT_SHA_REVIEW_REQUIRED`.
This is a non-authorizing qualification-mechanics review; no biological inference or training authorization.

## Inherited accepted code
Task0 `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`; Task1 `799d2e235901dfad9ce3b305c767a1c989e362f6`; Task2 `c7dfff1cee608e4a101855d42cf0af08491c2aaf`; Task3 `117dd51dea827e734b299982da93991b934bdc8f` (`ACCEPT_UNIFIED_TASK3`). Frozen Task0–3 production code is unchanged.

## Rejected/superseded lineage, never rehabilitated by prior GREEN CI
- `b31371d62f3270c965d321e61c35898ca6be3721` — rejected caller-self-minted trust roots;
- `c537db4e7b5b916cb3ddee1872fd4afa623a9b33` — rejected sealed-object substitution;
- `b5ed724cbc6a39d4f2cd68103c5367c2cfafcff3` — rejected advanced campaign-state fabrication;
- `d41720be93db27801fdac1ae62cfd608084dce25` — rejected post-reveal terminal-accounting mutation;
- `56b864e2b944956746771fb5d26040835d093dd5` — superseded review pin with stale packet;
- `068880822bca8036e605e3c5264770ce89057fee` — rejected caller-supplied regeneration replay, PR #417 run `39000234158`;
- `e60689c5fe6b8319e2d40037bc25a7a62ab421dd` — successor5 first repair superseded by PR #419 copied-code/altered-globals RED `39083015888`;
- `36e3b46f1ca44465864a11872b459b5d108d6a67` — successor5 exact GREEN later rejected by independent PR #422 public duplicate-campaign remint, RED run `39084356745`, job `117547707249` (`1 failed, 122 passed, 1 skipped`).

## Successor-6 RED→repair→hostile RED→repair
- PR #423 first ported the PR #422 RED test on commit `870d614d6eac7845e13232c196c82179f20cfab1`.
- First repair `98b788d3ba74ab6c53d64e0d310487d5c7061370` atomically leases campaign identity so re-running `create_campaign` with exact same campaign ID/dependencies/genesis cannot mint a fresh zero-budget-spent state. Inherited focused regression exposed test-fixture reuse across separate synthetic tests (13 fails). An explicit test-only fixture reset in `conftest.py` isolates each test as a fresh process but does NOT relax identity leases within a test. After repair `2d5288d5b8d20863709d99edfffacd62dcbebc6f`, focused **123 passed, 1 skipped**, full unified **314 passed, 1 skipped**.
- Hostile sibling tests for pre-spend re-mint, GC deletion, canonical input aliases and simultaneous same-identity creation passed at `e951bcf806634f20029e5d4e584f7b18513a7c86`: focused **127 passed, 1 skipped**, full **318 passed, 1 skipped**.
- Separate independent PR #424 then forced two parallel public `issue_exposure` calls onto the same lawful realization. Exact RED run `39084723524` / job `117548785850`: **1 failed, 127 passed, 1 skipped**. Both issued ordinal 1 because lifecycle check and state update were not atomic.
- PR #423 ported the independently observed race RED in commit `3f68ae905a4c22b4098a73320d346167446a028f`. The follow-on repair `671447eecb49cd2b91db109016e38753c52e573f` atomically locks the decisive lifecycle recheck and state advance.
- Exact code/test head `671447eecb49cd2b91db109016e38753c52e573f`: read-only Task4 CI `39084780439` job `117548950260`, focused **128 passed, 1 skipped**, projected 100k **1 passed**, full unified Task0–4 **319 passed, 1 skipped**. Task2 `39084780493` PASS; Task3 registry `39084780483` PASS; synthetic integration `39084780506` (verify completion independently). This head precedes the review packet, so a final exact review SHA must be checked again and pinned separately.

## Mechanistic scope and review gate
- Process-local DEVELOPMENT only: campaign identity lease and lifecycle transition lock prevent known duplicate and concurrent spend routes in the same Python process. They are not durable, authenticated, external custody. Multi-process restart and hostile mutation of module-private Python objects remain outside their enforcement scope; FINAL is separately fail-closed until independently trusted external authority and custody exist.
- No Task4 mechanical GREEN or independent ACCEPT itself authorizes targets, representations, biological truth, Stage4 or real training.
- Attack identity re-creation, alias, fork, stale copy, concurrency, restart, all previous regeneration/global-helper/reveal/root routes, legacy registry promotion, signer/root fabrication and C1–C9. An independent reviewer must return an exact-SHA `ACCEPT_TASK4_CUSTODY_CANDIDATE` or `REJECT_TASK4_CUSTODY_CANDIDATE`, with a clear non-authorizing scope.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
