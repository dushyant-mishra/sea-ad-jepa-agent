# JEPA current durable audit V6 — Task4 successor-6 review

**Current gate:** PR #425 is an immutable exact-head candidate `211375de57cc1f70d46c6eb3a4860d61a1aba0a6`. Its mechanics passed CI; **independent acceptance is absent**. No real training, Stage4, target or representation authority.

## New since V5
- PR #421 successor-5 `36e3b46f1ca44465864a11872b459b5d108d6a67` is rejected. PR #422 test-only RED `39084356745`/job `117547707249` demonstrated repeated campaign creation with identical ID/dependencies/genesis can reset already-spent exposures.
- PR #423 first ported that RED, then fixed in-process duplicate identity leases; its initial regression exposed benign fixture ID reuse across tests, corrected in test-only `conftest.py` without permitting within-test remint.
- Independent PR #424 test-only RED `39084723524`/job `117548785850` demonstrated simultaneous double-spend of the same realization. PR #423 ported the RED then serialized lifecycle check-and-advance.
- Additional hostile tests cover claimed-before-spend, garbage collection, canonical dependency aliases, concurrent duplicate creation, and simultaneous exposure spending.
- PR #425 exact head `211375de57cc1f70d46c6eb3a4860d61a1aba0a6`: Task4 run `39084913154`/job `117549328489`, focused **129 passed, 1 skipped**, projected100k **1 passed**, full unified **320 passed, 1 skipped**; Task2 `39084913157`, Task3 registry `39084913175`, unified synthetic integration `39084913173` PASS.
- Frozen Task0–3 production is unchanged; separate inherited missing-NumPy workflow failures are still historical environment issues.

**What is NOT closed:** cross-process no-reset, independently trusted actor/generator execution and FINAL authority. In-process checks are DEVELOPMENT mechanics only. Do not relabel them as durable external custody.

Read machine V6 state first, then PR #425 successor-6 review packet/state; PR #322 prior V4/V5 science, ETL, population, negative findings and local/private asset manifest remain unchanged and are NOT to be re-audited without changed inputs.

Next: independent hostile exact-SHA ACCEPT or REJECT. Keep PR #425 immutable and any new RED on its own branch.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
