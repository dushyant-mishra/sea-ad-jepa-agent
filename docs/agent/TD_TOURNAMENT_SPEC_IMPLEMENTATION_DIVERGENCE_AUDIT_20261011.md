# Target-tournament prefreeze/spec implementation divergence audit

Date: 2026-10-11

Status: `PREFREEZE_SPEC_IMPLEMENTATION_DIVERGENCE_CONFIRMED__REAL_TOURNAMENT_BLOCKED__NO_TARGET_AUTHORITY`

## Scope

This audit compares the prospectively frozen scientific design
`docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze.md`
with the executable synthetic scaffold contract and validator on draft PR #275.

No corrected biological outcome, matrix, G6/G7 value, TD56/57B/57C/59 corrected replay result, TD60 result, target result, representation result or training result was opened for this audit.

## Finding 1 — candidate identities drifted

The prefreeze design defines:

1. C1 — shared emergent state with relational continuity;
2. C2 — multiscale relational state built around C1;
3. C3 — q-conditioned measured contextual target;
4. C4 — structured shared + relational + q-context protocol;
5. C5 — optional regulatory/chromatin specialist.

The executable V1 scaffold instead declares:

1. `C1_RELATIONAL_SHARED`;
2. `C2_QUERY_MEASURED`;
3. `C3_LEARNED_SHARED`;
4. `C4_STRUCTURED_COMPOSITE`;
5. `C5_REGULATORY_SPECIALIST`.

This is not a naming-only difference. It removes the clean C1-versus-C2 comparison asking whether explicit relational structure adds value over a simpler shared-emergent target, shifts the q-conditioned arm from C3 to C2, and introduces a separate learned-shared arm not defined as a candidate family in the frozen prefreeze.

## Finding 2 — promotion-gate taxonomy drifted

The prefreeze declares twelve promotion-gate families:

- integrity/lineage;
- nontrivial biological content;
- correct-cell specificity;
- donor recurrence;
- source replication;
- teacher information advantage without leakage;
- evidence convergence;
- measurement robustness;
- learned-teacher continuity;
- collapse/shortcut resistance;
- transfer;
- coverage.

The V1 scaffold instead uses seven common machine gates:

- `G1_DONOR_PRIMARY`;
- `G2_SOURCE_REPLICATION`;
- `G3_SHORTCUT_DEFEAT`;
- `G4_INFORMATION_ASYMMETRY`;
- `G5_SUPPORT_ABSTENTION`;
- `G6_TRANSFER`;
- `G7_NO_POSTHOC`;

plus candidate-specific gates. The mapping is neither one-to-one nor documented as a prospective amendment. Several prefreeze promotion concepts therefore have no exact machine gate in V1.

## Finding 3 — C4 violates the frozen no-compensation rule

The prefreeze explicitly states:

> No component may compensate for another component failing its own mandatory gate.

The V1 `C4_STRUCTURED_COMPOSITE` gate list does not inherit the full applicable gate sets of its constituent programs. In particular it omits all three V1 relational C1-specific gates, `Q4_Q_COUNT_ONLY_DEFEAT`, and the V1 learned-shared evidence-response, measurement-depth-response and collapse/shortcut gates.

Therefore V1 can label C4 individually eligible without proving all constituent-applicable falsifiers. That contradicts both the prefreeze C4 rule and the selection rule that a richer family cannot rescue an unqualified component.

## Finding 4 — current synthetic qualification cannot cure scientific drift

The historical local green test counts on PR #275 establish software behavior only for the contract that was tested. They do not establish that the tested contract faithfully implements the scientific prefreeze.

The current PR #275 head is already marked pending fresh qualification for other semantic repairs. This divergence is an additional reason that V1 must not be used for a real target tournament.

## Adjudication

The V1 scaffold remains useful as historical software/custody evidence, but is **not the executable authority for a future real target tournament**.

Terminal:

`V1_SCAFFOLD_SCIENTIFICALLY_SUPERSEDED_FOR_FUTURE_REAL_TOURNAMENT__PRESERVE_HISTORY__BUILD_V2_PROSPECTIVELY__NO_REAL_TOURNAMENT_AUTHORITY`

## Required successor properties

A V2 successor must be frozen before corrected target-tournament outcomes and must:

1. restore an unambiguous candidate decomposition in which the simpler shared target, relational extension and q-conditioned measured target can be separately falsified;
2. encode every prefreeze promotion-gate concept explicitly or document a prospective, semantics-preserving mapping;
3. make C4 inherit every constituent-applicable gate plus an increment-over-constituents gate;
4. keep C5 specialist-only;
5. preserve `FAIL` versus `NOT_ESTIMABLE`;
6. require complete foundation-candidate adjudication before any tournament-level conclusion;
7. bind all gate evidence to the externally frozen prefreeze/decision-family identity;
8. preserve donor-primary statistical units and unique-donor accounting;
9. keep all execution/selection/training authority false.

No existing V1 file or historical qualification is to be rewritten as if V2 had always existed.
