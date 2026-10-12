# C6 shared + query composite — prospective candidate extension V1

Status: prospective target-discovery design freeze only. No biological execution, target selection, representation selection, TD60, Stage 4, or training authority.

## Why C6 is required

The frozen candidate set contains:

- C1: shared emergent state;
- C2: C1 plus relational constraints;
- C3: measured query-conditioned contextual target;
- C4: C2 plus C3.

That set is missing the simpler composite **C1 + C3 without relational constraints**. If corrected relational evidence eliminates C2 while both C1 and C3 survive, the existing C4 is correctly blocked, but the tournament has no prospectively defined way to test whether shared state and measured query context are complementary. Redefining C4 after seeing outcomes would be post-hoc and is forbidden.

C6 closes that hole before corrected biological outcomes are opened.

## Candidate definition

`C6_SHARED_QUERY_COMPOSITE`

Components:

- C1 shared emergent biological state;
- C3 measured query-conditioned non-q contextual target;
- explicit support/abstention;
- biological and measurement uncertainty kept distinct.

C6 contains **no relational constraint**. It is therefore independent of corrected TD56/57B/57C/59 relational viability.

## Gate inheritance

C6 inherits the exact union of the currently frozen C1 and C3 mandatory gate sets, plus:

`C6_INCREMENT_OVER_C1_C3`

The increment gate requires prospectively thresholded evidence that C6 adds donor-primary biological information or robustness beyond the stronger qualified constituent while not worsening transfer, shortcut dependence, supported coverage/abstention, or uncertainty separation.

Neither constituent may compensate for failure of the other. If C1 or C3 fails an applicable mandatory gate, C6 is blocked.

## Factorial interpretation

Adding C6 makes the main target family interpretable as component ablations:

- C1 = shared;
- C2 = shared + relational;
- C3 = query;
- C6 = shared + query;
- C4 = shared + relational + query.

This enables two clean incremental questions that the old set could not separate:

1. Does query context add value to shared state? C6 versus C1.
2. Does relational structure add value once shared + query context already exist? C4 versus C6.

C4 cannot win merely because it has more components; its relational increment must survive these comparisons.

## Relational routing

- Relational PASS: C1, C2, C3, C6 remain active; C4 active subject to C2+C3.
- Relational FAIL: C2 eliminated; C4 blocked; C1, C3, **C6 remain independently testable**.
- Relational NOT_ESTIMABLE: C2/C4 unresolved on relational evidence; C1, C3, **C6 remain independently testable**, but C6 still requires both C1 and C3 to qualify.

## Synthetic evidence

The existing V79 crosswalk V1 remains immutable history and does not contain C6. A prospective crosswalk extension is required before synthetic evidence can be consumed for C6.

C6 synthetic qualification may inherit applicable nuisance/support/operator falsifiers from the C1 and C3 designs only after they are explicitly rebound to C6 execution. Constituent synthetic PASS cannot be copied into C6. Current V79 has no planted truth for the biological increment of shared + query composition, so `C6_INCREMENT_OVER_C1_C3` is `NOT_ESTIMABLE` synthetically unless a future generator extension plants that truth prospectively.

## Protected head-to-head complexity

For complexity comparison, C6 component set is `{SHARED, QUERY}`. Therefore:

- C1 is structurally simpler than C6;
- C3 is structurally simpler than C6;
- C6 is structurally simpler than C4;
- C2 and C6 are incomparable by component-subset complexity.

## Authority boundary

C6 is a prospectively frozen candidate definition only. It creates no corrected replay authority, biological PASS, target winner, representation winner, TD60 authority, Stage 4 authority, or training authority.
