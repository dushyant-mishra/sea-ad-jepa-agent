# JEPA observation-depth contract decision: D1 / D2 — October 28, 2026

**Decision authority:** successor deciding lane only.  
**Scientific/training authority:** NONE.  
**Parent successor freeze:** PR #460 exact head `da5c3909bbab0a615d88ae48e11ddab913dd3ec0`.  
**Parent audit freeze:** PR #322 exact head `bae9ce01ffabb7e96cd0987921d7cd979e8814a7`.

This decision resolves the governance question left open by the final takeover freeze. It does **not** claim that a current real-data issuer is qualified.

## Decision

### D1 — ACCEPT as the versioned released normalization-depth contract

The released observation contract shall use:

`depth_rule = VISIBLE_BASE_MAPPED_SUM_V1`

with

`normalization_depth(cell, query) = sum(count)`

over exactly those released rows for the same cell that are:

1. `state == MEASURED_SCALAR`; and
2. whose evidence right is in the prospectively issued base-right set for that query.

The query itself must be outside base rights. The same D1 value is used in student and richer teacher views for the same cell/query. Adding richer evidence may reveal more rows, but may not change D1.

**Why D1 is accepted as the contract:**

- it is computed from the released base-visible evidence itself and therefore needs no private physical total;
- withheld query/non-base mass cannot enter the denominator by arithmetic;
- the consumer can recompute an exact equality law from released rows;
- it is invariant across the rights ladder for a fixed cell/query;
- it remains defined when real source rows contain off-ledger residual mass;
- #488 independently repaired and cross-platform qualified the fixture consumer law and student-right binding without weakening physical `library_size`.

This is a **semantic contract decision**, not current execution authority.

### D1 is NOT yet qualified for real production execution

A real issuer must still prospectively bind and independently review:

- source row / canonical cell identity;
- source feature-to-address mapping;
- query-specific evidence rights;
- in-ledger alias closure sufficient to prevent query molecules from appearing under a base-visible address;
- operator/source support and collision state;
- QC / row-selection leakage, including query classes entangled with depositor QC;
- required specimen/donor grouping where downstream inference uses biological replication.

The current #479/#488 fixture producer's conservation rule is **not** the production D1 producer. Its `physical_total == mapped_count_sum` requirement rejects genuine residual-mass rows and must not be inherited. Only its consumer-verifiable D1 equality and bounded fixture rights logic are reusable.

### D2 — REJECT from the current released observation contract

The candidate

`base_excluded_physical_depth = D1 + authenticated_residual_mass`

is **not admissible in the current released student/teacher contract**.

Reasons:

- the released consumer cannot independently recompute or verify the residual term;
- off-ledger source features have not been closed against query aliases per query/operator;
- it reintroduces dependence on a private physical-source quantity;
- the existing residual evidence is source-dependent and material (SEA-AD and NPH52), so treating it as harmless is not justified.

D2 is therefore not merely “default off”; it is **rejected for this contract version**.

A future lane may reopen D2 only as a **new versioned proposal**, after prospectively reviewed per-query/per-operator residual decomposition, off-ledger alias closure, authenticated issuer provenance and a demonstrated reason that D2 adds value beyond D1 without creating a hidden information channel. Even then D2 may not silently replace D1.

## Physical-total semantics are frozen

Existing CaseBundle V1 and G7 E3 V1 `library_size` semantics remain physical-total semantics. Their physical mass inequalities are not renamed, weakened, or retrofitted to mean D1.

The new released field is explicitly distinct:

- `normalization_depth`
- `depth_rule = VISIBLE_BASE_MAPPED_SUM_V1`

No adapter may implement this decision by renaming D1 to `library_size`.

## G7 consequence

The current G7 E3 V1 content schema is not compatible with the D1 released-view schema. The prior naive rename probe accepted only 6/200 worlds and conflated normalizer and physical-total semantics.

Therefore any common scientific producer/gate that consumes D1 requires a **versioned G7 E3 V2 law** with cell-scoped identity and an explicit D1 equality rule. G7 E3 V1 remains frozen for its historical physical-total fixtures. The terminal V3 decision law is not changed by this decision.

## Evidence boundary

This decision relies on the frozen audit facts that:

- whole-row `source_library` is computed before address mapping and therefore includes the query and off-ledger mass;
- blocked collision features are excluded from measured-address mapping;
- residual mass is material for SEA-AD and NPH52;
- off-ledger alias identity is not authenticated;
- depositor QC rules are not fully recorded.

The #488 and #489 repairs improve mechanics only. They do not supply the missing real source issuer or source semantics.

## Next implementation requirements

1. Implement a new versioned production D1 issuer from reader-fit source rows without requiring physical-total equality.
2. Carry an authenticated/prospectively frozen base-right policy and exact cell/source/operator identity.
3. Implement G7 E3 V2 around cell-scoped D1; do not alter G7 E3 V1.
4. Add reader-fit residual decomposition and off-ledger alias audit for source understanding, but do not expose residual as model input under this contract.
5. Add QC/selection-leakage and specimen/donor grouping audits before real C2/C3 qualification.
6. Preserve all current target/training stop states.

## No-promotion statement

This decision authorizes **contract implementation and hostile qualification only**. It does not authorize real target qualification, target selection, representation selection, Stage4, or JEPA training.

Standing project stop:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
