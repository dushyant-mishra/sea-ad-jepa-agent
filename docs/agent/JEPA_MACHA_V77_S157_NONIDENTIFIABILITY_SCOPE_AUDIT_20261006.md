# JEPA Macha/V77 — S157 non-identifiability scope audit

Date: 2026-10-06
Parent audit head before write: `6cb10f04383bb67bfd397577c8ee1f31e30cece4`
Macha head audited: `eb98ede1419adb48fec6b82bfdcbdaffa4ae54c1`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF`

## Finding

Register addendum 3 records:

`NON_IDENTIFIABLE from same-assay RNA`

and explains that the exact twin is non-identifiable under every context arm.

The exact-twin result is valid and important, but the headline is broader than the experiment proves.

What is established:

`THERE_EXISTS_A_TECHNICAL_CAPTURE_PROCESS_WITH_THE_SAME_ALLOWED_OBSERVABLE_LAW_AS_THE_PLANTED_BIOLOGICAL_PROGRAM__RNA_CANNOT_DISTINGUISH_THOSE_TWO_CAUSES`

This is a hard identifiability boundary: no better RNA-only statistic or model can recover a distinction absent from the observations.

What is not established:

- every technical artifact is non-identifiable from RNA;
- operator-linked nuisance is non-identifiable (it is context-separable under the preregistered raw-identity positive control, though not eliminated);
- the real class-associated structure behind S157 is biological or technical;
- a specific multimodal object is required or sufficient.

Correct compact wording:

`S157_ESTABLISHES_NON_UNIVERSAL_IDENTIFIABILITY_FROM_SAME_ASSAY_RNA__EXACT_SAME_LAW_TWIN_IS_NON_IDENTIFIABLE`

## Original biological question remains open

The real-data observation that within-class RNA topology differs from pooled topology remains `class-associated structure`, not identified biology. The paired challenge shows why RNA alone cannot settle the hardest same-law alternative, but it does not identify the mechanism generating the real T5 pattern.

Thus `S157 RESOLVED AS A QUESTION` should be read narrowly as resolving the existence of an RNA-only identifiability limit, not as resolving the biological cause of the real structure.

## Operator-twin wording

Addendum 3 says the operator twin is `separated only by raw identity`. That is correct under the preregistered context-share separation statistic, but raw identity leaves residual nuisance recoverability around R2 0.374. It therefore must not be read as nuisance elimination.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object or estimand winner.
