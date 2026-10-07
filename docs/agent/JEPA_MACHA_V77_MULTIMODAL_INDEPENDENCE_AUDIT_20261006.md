# JEPA Macha/V77 — multimodal evidence independence audit

Date: 2026-10-06
Parent audit head before write: `4fbdcfbf09e4c5e17ddf29c84092f5810e43101c`
Macha head audited: `eb98ede1419adb48fec6b82bfdcbdaffa4ae54c1`
Status: `DOCUMENTATION_ONLY__REQUIREMENTS_ONLY__NO_EVIDENCE_OBJECT_SELECTED`

## Bottom line

The Phase-5 handoff is directionally sound: an external object is useful only when it removes an alternative explanation that the RNA itself cannot remove.

The evidence objects differ materially in independence. They must not be counted as equivalent independent confirmations.

## GSE174367 RNA/ATAC

PR #164 provides the strongest authenticated independence result found in this pass.

It reports:

- authenticated snRNA and snATAC matrices and metadata;
- 18 shared donors between RNA and ATAC;
- no cell-level RNA/ATAC pairing: separate nuclei from the same brains;
- zero GSE174367 donors in FULL104;
- the microglial ATAC fragment matrix was not read by the historical Stage75F scripts;
- Stage75F TF-target edges were built from the same 18-sample microglial snRNA pseudobulk.

Therefore:

`GSE174367_ATAC_MEASUREMENT = CONDITIONALLY_INDEPENDENT_MEASUREMENT_LAYER`

but

`STAGE75F_TF_TARGET_EDGES = NOT_INDEPENDENT_OF_THE_RNA_THEY_WERE_DERIVED_FROM`

Biological meaning: ATAC can provide a separate chromatin observation, but the old RNA-derived TF-target hypotheses cannot be used as an independent answer key for that same RNA.

Because RNA and ATAC come from separate nuclei, this route supports donor/state-level regulatory evidence, not exact single-nucleus RNA↔ATAC causality.

## Stage75F / SCENIC-related evidence

Historical Stage75F result tables are appropriately bounded. They explicitly mark:

- `validated_regulation = False`;
- `validated_grn_claim = False`;
- `causal_validation_pass = False`;
- `therapeutic_target_claim = False`.

These results are motif/co-activity candidate evidence, not validated regulatory truth.

PR #179 is explicitly `INCOMPLETE_STOPPED` and says no number from that branch is citable as evidence. It therefore cannot repair or upgrade Stage75F authority.

Current classification:

`SCENIC_STAGE75F = HYPOTHESIS_GENERATION_AND_MOTIF_SUPPORT_ONLY__NOT_INDEPENDENT_RNA_VALIDATION`

A future SCENIC+ object can become more useful only when built on data independent of the RNA being explained and when motif/annotation-supply controls are passed prospectively.

## Nott enhancer-promoter contacts

The Phase-5 requirements treat Nott Table S5 as an authenticated physical-contact candidate. Earlier V63 PR #198 explicitly records that Table S5 was not retrieved in that lane and access was not bypassed, so V63 itself is not the authentication source.

This audit did not independently reconstruct the later exact custody receipt from primary repository files during this pass. Therefore the current fail-closed statement is:

`NOTT_CONTACTS = CANDIDATE_PHYSICAL_WIRING_EVIDENCE__AUTHENTICATION_CLAIM_REQUIRES_LATER_CUSTODY_RECEIPT_WHEN_USED`

Even when authenticated, enhancer-promoter contact shows possible physical wiring. It does not show that the enhancer is active in the current cell/state, that the TF is active, or that the contact causally drives the RNA program.

Nott therefore contributes a different type of evidence from ATAC rather than an additional replicate of the same claim.

## Morabito

Morabito remains PROTECTED in the current authority state and is not opened or used here.

Historical project work has already exposed some Morabito-derived coverage information, so any future use must preserve that exposure history. It cannot simply be relabelled as a pristine untouched external benchmark.

## Independence should be counted by alternative explanations removed

Do not count `RNA + motif + SCENIC + ATAC + contact` as five independent confirmations by default.

Examples:

- RNA co-activity and a SCENIC network built from the same RNA share the same RNA noise/capture path;
- motif and SCENIC motif annotation can share annotation-supply biases;
- same-donor RNA and ATAC can share nuclear quality and donor-level confounding even when the molecular assays differ;
- Nott contact and H3K27ac/contact-selection can share regulatory-activity selection biases.

The correct question is: `which alternative explanation becomes impossible after adding this object?`

## Current useful hierarchy without selecting a winner

- **GSE174367 ATAC:** strongest currently authenticated independent measurement layer found here; separate nuclei / donor-level, not same-cell.
- **Nott contacts:** physical wiring candidate; activity/causality not established and exact later custody should be rebound when invoked.
- **Motifs:** sequence support; constant across cells and not activity evidence by itself.
- **SCENIC+/Stage75F:** useful hypothesis structure, but circular when built from the RNA under explanation.
- **Morabito:** protected; no use here.

This is an independence classification, not an evidence-object selection.

## Authority unchanged

TRAINING=OFF; Stage A OFF; Stage 4 NOT AUTHORIZED; TEST sealed; Morabito protected; no target, representation, evidence-object, calibration target or estimand winner.
