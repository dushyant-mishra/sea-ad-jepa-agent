# JEPA GSE214979 paired-multiome fidelity-asset reconciliation

Date: 2026-10-07

Status: `AUTHENTICATED_PAIRED_MULTIOME__CONDITIONAL_FUTURE_FIDELITY_ASSET__BIOLOGICAL_CORRESPONDENCE_UNOPENED`

This is a historical/prospective audit only. It does not authorize biological endpoint execution, Stage A, target selection, multimodal training, or production training.

## Chronology repaired

The Sept-26 scientific decision record correctly described GSE214979 as still unverified at that time. PR #182 subsequently closed several of those structural questions. Therefore the older `processed-file authentication / pairing / microglia census unverified` state is superseded for those specific items.

PR #182 (`lane/paired-multiome-authentication-20260926`, head `423ca3c27e77d805473b465de4dd077e7c7462f5`) established:

- GSE214979 is a subseries of GSE214637, not an independent replication cohort;
- 105,332 nuclei across 15 people;
- 3,179 microglia before frozen exclusions;
- true same-nucleus RNA+ATAC pairing verified for 105,332/105,332 rows;
- a single 10x ARC HDF5 / barcode list with nonzero RNA and ATAC on each paired row;
- five donors have replicate libraries, so library count must not replace donor count;
- donor assignment comes from cellSNP/vireo demultiplexing across three pooled lanes and its misassignment rate is not reported.

## Identity defects and frozen exclusions

Two donors, `HCT17HEX` and `HCTZZT`, have sex/age values transposed between GEO sample records and series cell metadata. They are the two occupants of pooled GEM lane 6, and their RNA/ATAC records also disagree on brain region. This is structurally compatible with a donor-label/join error and is not a biological-outcome judgment.

A prospective frozen eligibility rule from PR #182:

1. drop the two identity-conflict donors;
2. require at least 50 microglia per donor.

The support rule additionally excludes donor `4313` (17 microglia); `HCTZZT` also has only 26 microglia, so the two criteria overlap on one donor.

The union therefore leaves:

- 12 donors;
- 92,957 all-type paired nuclei;
- approximately 2,872 paired microglia.

The reported 6 AD / 6 control balance is descriptive only. Diagnosis must not be used to choose the exclusion rule, representation, peaks, statistic, nuisance treatment, threshold or gate.

## Why the exclusion is prospectively defensible

The exclusion criteria depend on structural metadata / identity integrity and minimum cell-type support, not on RNA–ATAC biological correspondence. They can therefore be frozen before real biological correspondence is opened.

Allowed method-development fields should remain limited to:

- exact pairing/barcode identity;
- donor and library identity;
- cell type;
- RNA QC;
- ATAC QC;
- other prospectively allowed measurement descriptors.

Pathology/diagnosis and target-specific cross-modal outcomes remain forbidden for gate tuning.

## Independence status

- From FULL104: operationally independent by study/ID namespace and brain-bank provenance, but person-level non-overlap is inferred rather than cryptographically proved because no shared person identifier exists.
- From Morabito: independence is not fully established. PR #182 flags GSE214979 donors `1224`, `1230`, `1238` from UCI while Morabito is also a UC Irvine cohort with pseudonymized donor IDs. Any later claim relying on agreement between both cohorts must either exclude those three GSE214979 donors prospectively or carry the unresolved-overlap caveat.
- Prior exposure at PR #182: zero tracked project files/commits for GSE214979 before that authentication lane; therefore it was substantially cleaner than Morabito for future biological correspondence.

## Scientific role

Recommended current role:

`CONDITIONAL_EXTERNAL_SUPPORT__SAME_NUCLEUS_RNA_ATAC__OUTCOME_UNOPENED`

This makes GSE214979 one of the strongest available public assets for a later claim transition beyond RNA-only representation, because RNA and ATAC are paired in the exact same nucleus.

However, same-nucleus pairing does **not** by itself prove biological identity. Shared technical/handling/cell-quality state can drive coherent RNA and ATAC changes. Therefore real biological correspondence must remain unopened until a prospectively qualified cross-modal specificity/identifiability gate distinguishes, to the extent observationally possible:

- biology-absent null;
- measured technical correspondence;
- latent shared technical/capture state;
- handling/exAM-like shared nuisance;
- planted biological cross-modal state.

If a plausible technical latent is observationally indistinguishable from the biological world, the correct terminal is an identifiability limitation, not a tuned threshold.

## Claim ceiling

GSE214979 can potentially contribute to:

- `TRANSFERABLE_BIOLOGICAL_STATE` support;
- later `REGULATORY_SUPPORT` when the endpoint is independently frozen and appropriately regulatory/chromatin based.

It cannot by itself establish causal regulation or realistic AD donor effects. With only 12 frozen-eligible donors, disease-effect power is especially limited; disease labels should not be the immediate fidelity endpoint.

## Current boundaries

`BIOLOGICAL_CORRESPONDENCE = UNOPENED`
`TRAINING = OFF`
`STAGE_A_EXECUTION = NOT_AUTHORIZED`
`MULTIMODAL_TRAINING = OFF`
`TARGET_WINNER = NONE`
`REPRESENTATION_WINNER = NONE`
