# JEPA Macha/V77 — Phase-5 paired-multiome dataset correction

Date: 2026-10-06
Parent audit head before write: `f525bfdf1046ddd59956550257150ab3c4a577a9`
Macha head audited: `eb98ede1419adb48fec6b82bfdcbdaffa4ae54c1`
Status: `DOCUMENTATION_ONLY__NO_EVIDENCE_OBJECT_SELECTED`

## Finding

The Phase-5 handoff lists `GSE272082` as an example under same-nucleus paired RNA+ATAC evidence.

Later authentication in PR #182 does not support treating GSE272082 as a verified paired microglia resource yet:

- pairing is only `PAIRED BY CONSTRUCTION, UNVERIFIED`;
- matrices were not acquired in that lane;
- microglia census is not deposited and remains unknown;
- effective donor n is 9;
- disease-label inconsistencies were found for 2/9 donors.

Therefore GSE272082 must not be used as an authenticated same-nucleus exemplar at this point.

## Verified same-nucleus example

PR #182 did verify GSE214979:

- 105,332 / 105,332 nuclei have nonzero RNA and ATAC on the same row;
- depositor states paired RNA/ATAC counts from the same cells;
- single 10x ARC matrix over one barcode list;
- 3,179 microglia across 15 donors before exclusions.

However, it is only `CONDITIONAL`, not qualified:

- two donors have demographic identity conflicts;
- after the frozen exclusions and >=50-microglia rule, n=12 donors remain (6/6);
- donor-level power is weak for moderate biological effects;
- person-level non-overlap with FULL104 is inferred rather than proved.

Correct classification:

`GSE214979 = VERIFIED_SAME_NUCLEUS_PAIRING__CONDITIONAL_DATASET__NOT_SELECTED_OR_QUALIFIED`

`GSE272082 = PAIRED_BY_DESIGN__PAIRING_AND_MICROGLIA_CENSUS_NOT_YET_AUTHENTICATED`

## GSE174367 / Morabito distinction

GSE174367 is authenticated and heavily exposed historically, with separate RNA and ATAC nuclei from the same brains. PR #164 was readiness/reconnaissance only and explicitly states every biological evaluation was `NOT_EXECUTED`.

Therefore its existing coverage/accessibility summaries are exposure and assay-readiness information, not a biological validation result.

Under the current authority state Morabito remains PROTECTED, so this audit does not open new biological outcomes from it.

## Biological meaning

Same-nucleus pairing is valuable because RNA and chromatin are measured from the same physical nucleus. But pairing alone does not create enough independent donors or remove technical confounding.

Separate-nucleus donor-matched ATAC is weaker for cell-level attribution, but can sometimes be stronger as an independent measurement replicate because the RNA and ATAC are not the same nucleus.

These are complementary evidence designs, not a simple ranking.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object, calibration target or estimand winner.
