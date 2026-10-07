# JEPA Macha/V77 — S157 separation-scope audit

Date: 2026-10-06
Parent audit head before write: `73551bf50bb0578895d2c167e59def9235dc28f6`
Macha head audited: `74ef9dad7f370338471c1f19023f8b56a50e1b48`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## Finding

The S157 preregistration defines BIO vs TWIN_OPERATOR as `SEPARABLE` when the bootstrap intervals for `module_context_share` do not overlap.

Under ARM3 (raw source/operator identity), that rule is satisfied:

- BIO module-context share R2 is about -0.043;
- TWIN_OPERATOR module-context share R2 is about 0.417;
- their intervals do not overlap.

Therefore the committed `SEPARABLE` label is correct **under the preregistered statistic**.

However, this is not equivalent to saying raw identity removes the nuisance.

After residualizing on raw identity, the operator-linked nuisance is still recoverable from the module readout at R2 about 0.374. This is reduced substantially from about 0.872 with no context, but it remains a strong residual signal.

Correct scope:

`RAW_IDENTITY_MAKES_CONTEXT_ASSOCIATION_SEPARABLE__BUT_DOES_NOT_ELIMINATE_OPERATOR_NUISANCE`

## Biological meaning

Knowing which experiment measured the cell explains a large part of the technical program, but substantial technical signal remains in the RNA itself. Dataset identity is therefore neither a complete correction nor an acceptable biological solution.

## Lineage wording correction

The current Phase-4 commit message says raw identity `removes` the operator twin. Read fail-closed, this should be narrowed to `substantially reduces and context-separates` the operator-linked nuisance.

This does not invalidate the exact-twin result. BIO and TWIN_EXACT remain byte-identical and score identically, correctly demonstrating that identical observed RNA cannot reveal whether the hidden cause was labelled biological or technical.

## Additional statistical scope

The diagnostic principal components are computed on all cells in each world before the even/odd readout split. They are unsupervised and use no challenge labels, so this is not label leakage. But it is a transductive diagnostic, not a train-only representation-generalization test. It must not be cited as evidence that a learned representation generalizes to unseen cells/donors.

## S149 implication

The challenge intentionally has biology independent of operator. Real S149 confounding therefore remains outside this realization. Any claim that raw identity or lawful measurement context preserves real biology under study-composition confounding remains untested.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation or estimand winner.
