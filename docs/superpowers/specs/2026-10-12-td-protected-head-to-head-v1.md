# Protected target head-to-head V1

Status: prospective design freeze only. No biological execution, target selection, representation selection, TD60, Stage 4, or training authority.

## Purpose

This law applies only if more than one foundation target candidate has already survived every mandatory candidate-specific gate and applicable synthetic falsifier under the target-discovery tournament. It prevents choosing a winner by aggregate score or by post-hoc preference.

## Candidate component sets

For complexity comparisons only:

- `C1_SHARED_EMERGENT`: `{SHARED}`
- `C2_RELATIONAL_SHARED`: `{SHARED, RELATIONAL}`
- `C3_QUERY_MEASURED`: `{QUERY}`
- `C4_STRUCTURED_COMPOSITE`: `{SHARED, RELATIONAL, QUERY}`

Candidate A is structurally simpler than B only when A's component set is a strict subset of B's. No total complexity order is imposed between incomparable component sets such as C1 and C3.

## Protected comparison dimensions

Each pairwise comparison must report all of the following prospectively thresholded dimensions as exactly one of `BETTER`, `NONINFERIOR`, `WORSE`, or `NOT_ESTIMABLE` from A relative to B:

1. `BIOLOGICAL_INFORMATION` — held-out biological information beyond the appropriate simple baselines.
2. `DONOR_TRANSFER` — donor-held-out/new-donor transfer.
3. `SOURCE_TRANSFER` — source/acquisition transfer where estimable.
4. `SHORTCUT_RESISTANCE` — q-count/q-address/identity/technical/wrong-cell/wrong-q resistance as applicable.
5. `COVERAGE_ABSTENTION` — useful supported coverage without forced prediction on unsupported observations.
6. `UNCERTAINTY_BEHAVIOR` — biological and measurement uncertainty behave in the expected direction.
7. `MEASUREMENT_ROBUSTNESS` — robustness to measurement/operator perturbation, including frozen synthetic tests where applicable.

No aggregate score may substitute for any dimension.

## Dominance law

A may dominate B only when:

- no protected dimension is `WORSE` or `NOT_ESTIMABLE` for A relative to B; and
- at least one protected dimension is `BETTER`.

If every dimension is `NONINFERIOR`, A may be preferred over B only if A is structurally simpler by the strict component-subset rule above. This is the only simplicity tie-break.

A `NOT_ESTIMABLE` dimension prevents pairwise dominance; it is never treated as equality or noninferiority.

## Multi-candidate adjudication

- A unique candidate that dominates every other survivor may advance to protected confirmation as the unique head-to-head leader. This still does not create target authority.
- If no candidate dominates every other survivor, return an incomparable/multiple-survivor terminal; do not force a winner.
- Cyclic dominance, conflicting pairwise evidence, or missing pairwise comparisons fail closed as unresolved/incomparable.
- A composite candidate cannot win merely because it contains more components. Its increment gate must already have passed before entry, and it must satisfy the same pairwise law.
- An optional specialist C5 never enters the foundation head-to-head and cannot change its terminal.

## Outcome terminals

- unique dominator: `UNIQUE_HEAD_TO_HEAD_LEADER__PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY`
- no unique dominator with complete estimable comparisons: `MULTIPLE_QUALIFIED_TARGETS__INCOMPARABLE__NO_TARGET_AUTHORITY`
- any required dimension or pair is unresolved/not estimable: `HEAD_TO_HEAD_UNRESOLVED__NO_TARGET_AUTHORITY`

## Authority boundary

The head-to-head adjudicator is metadata-only. It cannot authorize real-value reads, corrected replay, target selection, representation selection, TD60, Stage 4, or training.
