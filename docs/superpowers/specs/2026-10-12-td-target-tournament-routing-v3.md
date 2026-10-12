# Target-discovery tournament routing V3

Status: prospective design freeze only. No biological execution, target selection, representation selection, TD60, Stage 4, or training authority.

## Why V3 exists

The V2 tournament froze useful candidate definitions and gate sets, but its global routing language can incorrectly make the entire foundation tournament depend on survival of a relational route, and its V2 adjudicator only reaches the candidate-selection terminal when all four foundation candidates pass. Those rules are too restrictive for a tournament intentionally containing independent alternatives.

V3 does not rewrite V2 history. It prospectively amends routing and survivor adjudication before corrected TD56/57B/57C/59 outcomes are opened.

## Candidate dependency graph

- `C1_SHARED_EMERGENT` is independent of the corrected relational route.
- `C2_RELATIONAL_SHARED` depends on the corrected relational route.
- `C3_QUERY_MEASURED` is independent of the corrected relational route.
- `C4_STRUCTURED_COMPOSITE` depends on both C2 and C3; therefore it inherits C2's relational dependency.
- `C5_REGULATORY_SPECIALIST` is optional specialist evidence and cannot rescue or redefine the foundation-target conclusion.

## Corrected relational replay routing

Input status is exactly one of `PASS`, `FAIL`, `NOT_ESTIMABLE`.

### PASS

C1, C2, and C3 remain active. C4 may remain active subject to C2 and C3. No target is selected.

### FAIL

C2 is eliminated by the relational result. C4 is blocked because a mandatory constituent failed. C1 and C3 remain active and independently testable. The foundation tournament must not terminate merely because the relational route failed.

### NOT_ESTIMABLE

C2 remains unresolved, not failed. C4 remains unresolved/blocked on C2. C1 and C3 remain active and independently testable. Synthetic evidence cannot convert the relational result to PASS.

## Survivor adjudication

Mandatory gate failure eliminates a candidate. Aggregate score cannot rescue a failed mandatory gate.

After candidate-specific evidence and any applicable synthetic falsifiers are combined:

- zero eligible foundation candidates, with no unresolved foundation candidate: `NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION`;
- exactly one eligible foundation candidate, with no unresolved foundation candidate: `SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY`;
- multiple eligible foundation candidates, with no unresolved foundation candidate: `MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY`;
- one or more unresolved foundation candidates: `FOUNDATION_CANDIDATE_UNRESOLVED__CONTINUE_TESTABLE_ROUTES__NO_TARGET_AUTHORITY`. Active/eligible independent candidates may continue testing, but no final target winner may be declared while an unresolved candidate remains in the foundation comparison set.

C4 cannot be eligible unless C2 and C3 are both eligible. C5 is reported separately as an optional specialist and never changes the foundation terminal.

## Synthetic evidence boundary

The separate V79 synthetic lane may be consumed only through the frozen target-discovery synthetic crosswalk. Synthetic evidence may falsify an applicable claim where truth is explicitly planted. Missing truth is `NOT_ESTIMABLE`. Synthetic PASS cannot override real-data FAIL or NOT_ESTIMABLE and cannot itself select a target winner.

## Authority boundary

V3 routing is metadata-only logic. It creates no corrected replay authority, biological PASS, target winner, representation winner, TD60 authority, Stage 4 authority, or training authority.
