# Protected target confirmation V1

Status: prospective target-discovery confirmation law only. No biological execution, target selection, representation selection, TD60, Stage 4, or training authority.

## Entry condition

Protected confirmation is entered only by either:

- exactly one foundation candidate surviving the complete tournament; or
- the unique leader from the complete protected head-to-head.

The candidate definition, target construction, hyperparameters relevant to the target, gate thresholds, and confirmation estimands must all be frozen before protected confirmation evidence is opened.

## Protected evidence firewall

Confirmation evidence must not have been used to create, tune, rank, rescue, or simplify the candidate. The confirmation receipt must bind:

- exact candidate ID and candidate-definition hash;
- exact confirmation protocol hash;
- exact protected evidence partition/manifest hash;
- exact analysis-code hash;
- explicit statement that the protected partition was not used for candidate selection/tuning;
- every required confirmation dimension.

Any identity mismatch or evidence reuse fails closed and is not confirmation evidence.

## Required confirmation dimensions

Each applicable dimension is exactly `PASS`, `FAIL`, or `NOT_ESTIMABLE`:

1. donor-primary biological recurrence/transfer;
2. applicable source/acquisition transfer;
3. shortcut/falsifier resistance;
4. supported coverage and abstention behavior;
5. biological-versus-measurement uncertainty behavior;
6. measurement/operator robustness;
7. candidate-specific increment claim for composite candidates where applicable.

A dimension may be marked not applicable only if the frozen candidate definition explicitly makes it inapplicable; it cannot be dropped after seeing outcomes.

## Adjudication

- any applicable `FAIL` -> `PROTECTED_CONFIRMATION_FAIL__NO_AUTOMATIC_RUNNER_UP_PROMOTION__NO_TARGET_AUTHORITY`;
- no FAIL but any applicable `NOT_ESTIMABLE` -> `PROTECTED_CONFIRMATION_NOT_ESTIMABLE__NO_TARGET_AUTHORITY`;
- all applicable dimensions PASS -> `PROTECTED_CONFIRMATION_PASS__SEPARATE_TARGET_SELECTION_AUTHORITY_REQUIRED`.

Confirmation PASS does not itself create a target winner or authorize training. A separate explicit target-selection decision is still required.

## No runner-up rule

If the protected candidate fails confirmation, no previously eliminated or second-ranked candidate is automatically promoted. Doing so would reuse protected evidence as a new selection set. Any alternative candidate must enter under a new prospectively frozen decision/confirmation plan with a genuinely protected evidence basis.

## Authority boundary

This confirmation law and its receipts are metadata-only evidence. They create no value-read authority, corrected-replay authority, target selection, representation selection, TD60, Stage 4, or training authority.
