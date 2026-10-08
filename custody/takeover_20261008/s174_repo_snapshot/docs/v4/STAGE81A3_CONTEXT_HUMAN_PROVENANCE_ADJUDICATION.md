# Stage81A3 SCP2167 Human Provenance Adjudication

## Chronology

The original automated UCDQ classified SCP2167 provenance as `UNKNOWN`, retained the dataset as `QUARANTINED_PENDING_GOVERNANCE`, and concluded `REAL CONTEXT QUALIFICATION NOT IDENTIFIABLE`. That result remains preserved. The original governance-compliant completion also remains `NO` because a generic `disease=normal` value was incidentally displayed before the audited reader ran. It was not used in qualification.

## Human publication adjudication

The human reviewer examined Russell AJ et al., *Slide-tags enables single-nucleus barcoding for multimodal spatial genomics.* Nature 2024;625:101-109 (DOI `10.1038/s41586-023-06837-4`, PMID `38093010`, PMCID `PMC10764288`). The primary publication describes the human prefrontal-cortex donor as neurotypical and identifies SCP2167 as the human-brain deposition.

This publication evidence changes SCP2167 provenance from `UNKNOWN` to `NEUROTYPICAL_DECLARED`. It does not use the incidental terminal value, modify the UCDQ contract, change a threshold, or relax an eligibility rule.

## Unchanged role-gate result

All previously computed non-provenance conditions remain unchanged: 36,601 source features, 4,096 frozen genes, raw UMI counts, nucleus entity type, physical XY coordinates with unknown units, 4,065/4,067 exact spatial matches, and no duplicated pairing identifiers. Applying the frozen gate changes the role from `QUARANTINED_PENDING_GOVERNANCE` to **`CORE_SAME_ENTITY_BROAD_CONTEXT`**.

## Post-adjudication identifiability

- **BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE: YES**
- **CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE: YES**
- **CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE: YES**

The broad anchor is one-donor Slide-tags SCP2167. Independent measured-subset replication is supplied by five eligible Fang STG MERFISH experiments across two donors. The five Fang MTG experiments remain quarantined and are excluded from the decision.

Final post-adjudication classification: **REAL CONTEXT VALUE + CROSS-DONOR + CROSS-TECHNOLOGY QUALIFICATION IDENTIFIABLE**.

Identifiable does not mean demonstrated. No context-benefit experiment, neighbor graph, masking, model training, optimizer update, or architecture change occurred.

ORIGINAL UCDQ GOVERNANCE-COMPLIANT COMPLETION: NO
UCDQ QUALIFICATION COMPUTATION COMPLETE: YES
HUMAN PROVENANCE ADJUDICATION COMPLETE: YES
CONTEXT BENEFIT DEMONSTRATED: NO
CONTEXT EXPERIMENT RUN: NO
STAGE81A3 FROZEN: NO
READY FOR STAGE81B: NO
