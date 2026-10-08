# V64 held-out evidence-family validation contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE VALIDATION CONTRACT — no held-out biological evidence opened

## 1. Purpose

A representation that reconstructs evidence used to build it has demonstrated fit, not necessarily transferable biology.

The preferred validation pattern is therefore:

`construct from evidence families A/B/C -> lock representation -> evaluate on mechanistically distinct family D`

The held-out family must not influence:
- representation construction;
- factor rank;
- basis rotation;
- feature selection;
- matching tolerances;
- thresholds;
- hyperparameters;
- evidence weights.

## 2. Evidence-family identity

Evidence-family identity is defined by measurement/causal mechanism, not software package name.

Examples:

- SCARlink and SCENT on the same NIH-CARD RNA+ATAC cells are one paired-observational measurement family with different estimators.
- Nott PLAC-seq / other contact evidence belongs to a structural-contact family.
- eQTL/caQTL belongs to a genetic-association family.
- CRISPR perturbation belongs to an interventional family.

A new estimator on the same measurements is not a held-out evidence family.

## 3. Valid held-out-family tests

Preferred examples:

- construct regulatory representation without structural contact; test against held-out contact evidence;
- construct without genetic association; test against held-out eQTL/caQTL;
- construct from observational evidence; test against held-out CRISPR perturbation;
- construct from one dataset's paired RNA+ATAC evidence; test in an independent paired dataset when lawful and available.

## 4. Development/validation separation

The held-out family may be inspected for:
- predeclared data integrity;
- coordinate harmonization;
- support/coverage census;
- missingness.

Do not inspect the biological correspondence outcome before representation and scoring rules are frozen.

If the held-out family has already materially influenced architecture selection, reclassify it as development evidence and choose another held-out family.

## 5. Population support

Before interpretation, report the intersection population between:
- the locked representation's eligible objects;
- the held-out family's measurable objects.

Do not treat NOT_MEASURED as negative.

Report:
- eligible count;
- measurable count;
- measured-and-supports count;
- measured-and-does-not-support count;
- not-measured count.

## 6. Activity/detectability bias

Held-out family status does not automatically imply independence.

A structural or genetic family can still be enriched for highly expressed/open/highly studied genes.

Therefore every validation report must include the relevant activity/detectability/support diagnostics and cannot narrate cross-family agreement as fully independent without sensitivity analysis.

## 7. Decision hierarchy

A future execution contract must predeclare:
- primary held-out-family metric;
- population/coverage rule;
- uncertainty procedure;
- minimum support;
- multiplicity handling;
- failure/abstention states.

This contract intentionally does not set numerical biological thresholds.

## 8. Interpretation

Passing a held-out-family test supports transferable biological structure across evidence mechanisms.

Failing may mean:
- the representation is not transferable;
- the held-out family measures a different biological layer;
- support is inadequate;
- measurement reliability is inadequate.

Failure must not automatically be interpreted as absence of biology.

## 9. Morabito / protected evidence

Morabito remains protected and is not authorized by this contract.

Any future protected-validation source must be explicitly opened under its own authority.

## Governance

TRAINING OFF.
Phase B STOPPED.
Stage 4 NOT AUTHORIZED.
No protected biological outcome opened.
