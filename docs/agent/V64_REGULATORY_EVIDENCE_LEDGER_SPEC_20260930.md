# V64 regulatory evidence ledger specification

**Date:** 2026-09-30  
**Status:** PROSPECTIVE SCHEMA — no atlas built

The regulatory atlas must preserve the hierarchy:

`gene -> candidate promoter/TSS -> regulatory element -> evidence records`

and must keep distinct:

1. **candidate existence**
2. **measurement availability**
3. **support**
4. **evidence family**
5. **estimator**
6. **common support / trimming**
7. **incremental support under observed adjustment**
8. **sensitivity to shared/unmeasured drivers**
9. **RNA recoverability**
10. **access/licensing provenance**

## Core rule

No single confidence score is authoritative at ingestion.

The ledger exists so later analyses cannot silently collapse:
- missing into negative;
- multiple estimators into multiple evidence families;
- multiple correlated resources into independence;
- downloadable into openly licensed;
- privileged-private into biologically invalid.

## Evidence record example

A single enhancer/promoter/gene relationship may have multiple records, e.g.:

- Nott PLAC-seq: structural-contact family;
- NIH-CARD + SCARlink: paired-observational family, estimator SCARlink;
- NIH-CARD + SCENT: same paired-observational family, estimator SCENT;
- SCENIC+: inferred-network family;
- eQTL: genetic family;
- CRISPRi: interventional family.

SCARlink and SCENT are separate estimator rows but share an evidence family when run on the same NIH-CARD measurement object.

## Missingness

Use explicit state:

- MEASURED_AND_SUPPORTS
- MEASURED_AND_DOES_NOT_SUPPORT
- NOT_MEASURED
- UNRESOLVED

Do not coerce NOT_MEASURED to 0.

## Recoverability

If a regulatory state is later used to construct a teacher factor, the ledger links to its recoverability class:

- RNA_RECOVERABLE
- PARTIALLY_RNA_RECOVERABLE
- PRIVILEGED_PRIVATE
- UNQUALIFIED

Only the qualified recoverable subspace can become compulsory universal RNA-student supervision.

## Provenance

Every source record must carry:
- version;
- recovery locator;
- digest;
- access status;
- license/terms status;
- mapping receipt when coordinate conversion occurred.

The source being publicly downloadable does not establish an open license.

## Governance

Schema only. No promoter atlas, regulatory atlas, Phase B, Stage 4, Morabito, or training is authorized.
