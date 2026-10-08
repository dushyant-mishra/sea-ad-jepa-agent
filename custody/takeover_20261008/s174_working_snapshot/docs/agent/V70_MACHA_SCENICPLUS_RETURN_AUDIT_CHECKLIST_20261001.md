# V70 Macha SCENIC+/eRegulon return audit checklist

Date: 2026-10-01

This checklist is the acceptance interface for Macha's external regulatory-network work.
It is deliberately prospective and must be applied before any protected Stage-4 or Morabito outcome is opened.

## A. Acquisition and custody

For GSE214979 require:

- filtered feature matrix filename, bytes, SHA-256 and recovery URL;
- metadata filename, bytes, SHA-256 and recovery URL;
- ATAC fragments filename, bytes, SHA-256 and recovery URL;
- genome build documented from source/feature metadata;
- exact software/environment manifest;
- no raw multi-GB binary committed to Git;
- recovery instructions sufficient to reacquire exact public bytes.

Reject if:
- only filenames are supplied without digests;
- redirects/temporary URLs are treated as permanent recovery locators;
- matrix/fragments identity is inferred rather than authenticated.

## B. Development population

Require:

- published cell-annotation field explicitly identified;
- microglial selection rule recorded;
- donor/subject field explicitly identified;
- all-microglia population count;
- default development population count;
- prospective treatment of possible Morabito-overlap donors 1224/1230/1238;
- diagnosis/pathology fields excluded from network construction.

Reject if disease/pathology, Braak, CERAD, case/control or AD status is used to choose:
- cells,
- peaks,
- TFs,
- target genes,
- latent dimensions,
- network thresholds,
- Route A/Route B reconciliation.

## C. Route A — submitted peaks

Require a frozen versioned output before Route B is inspected for reconciliation:

- network version;
- TF list;
- target-gene list;
- region list;
- TF→region links;
- region→gene links;
- eRegulon/program membership;
- membership SHA-256 using V69 namespace rules;
- donor-stability report;
- control receipts.

Historical Stage75F cannot substitute for this network.

## D. Route B — fragments reconstruction

Require:

- fragment QC by donor/sample;
- peak-calling/region-construction method;
- consensus-region rule;
- donor recurrence/support of peaks;
- frozen region-universe digest;
- motif database construction on that universe or justified fallback;
- independent network version and membership digests.

Reject if Route-B peak parameters are selected because they maximize agreement with:
- Route A;
- Stage 4;
- FULL104;
- Morabito;
- perturbation outcomes.

## E. Motif / cisTarget resources

Require:

- exact official motif collection version;
- archive SHA-256;
- human annotation file SHA-256s;
- custom cisTarget database construction receipt where used;
- region-universe identity bound into motif database identity.

Require TF annotation-supply and TF-label controls.

## F. Donor stability

Donor is the biological unit.

Require at least one of:

- leave-one-donor-out network stability;
- donor bootstrap;
- equivalent prospective donor-resampling design.

Report separately:

- TF stability;
- edge stability;
- target-set stability;
- program/module stability.

If edges are unstable but modules stable:
- qualify program/module level only;
- do not force exact-edge interpretation.

## G. Negative controls

Every control must have physical distinctness proof.

Require:

1. TF-label permutation;
2. annotation-supply control;
3. matched region-gene permutation;
4. donor-fingerprint control;
5. broad-cell-class/lineage shortcut check where relevant;
6. Route-A/Route-B sensitivity control.

For graph/control mutations report:
- graph digest;
- changed-edge fraction;
- overlap/Jaccard;
- proof the mutation can actually fail the intended gate.

## H. Route A versus Route B

Freeze the reconciliation rule before protected outcome inspection.

Report:
- TF overlap;
- target-gene overlap;
- region overlap;
- TF-target overlap;
- program overlap;
- target-set Jaccard;
- region-set Jaccard;
- donor stability by route.

Do not simply choose whichever route agrees with later validation.

## I. Program namespace compliance

Every candidate program must validate against:

- `results/v64/V69_REGULATORY_PROGRAM_NAMESPACE_CONTRACT_V1.json`
- `results/v64/V69_REGULATORY_PROGRAM_CROSSWALK_SCHEMA_V1.json`

Changing membership requires a new version and digest.

No protected outcome may mutate a frozen version.

## J. Structural crosswalks

Require per-program structural crosswalks for:

- FULL104 HVS;
- FULL104 NPH52;
- FULL104 SEA-AD;
- NIH-CARD Stage 4;
- Morabito;
- SEA-AD public multiome;
- GSE272082 if acquired;
- perturbation atlas;
- spatial panels.

Coverage is structural only.

Reject any crosswalk containing a biological effect statistic.

## K. Stage-4 boundary

Macha must not:

- run real Stage-4 correspondence;
- inspect real Stage-4 Delta/LCB/p-values;
- modify Stage-4 estimand;
- use Stage-4 agreement to select eRegulons.

The external network must be frozen first.

## L. Teacher-candidate boundary

Use:

`results/v64/V70_TEACHER_REGULATORY_CANDIDATE_SELECTION_CONTRACT_V1.json`

Stage 4 alone is insufficient.

Structural coverage alone is insufficient.

RNA-predicted FULL104 transport is not independent biological evidence.

A program can only advance to teacher-feature-producer review under the prospective multisource rule.

## M. Required verdict

Return one of:

- `ACCEPT_EXTERNAL_REGULATORY_NETWORK_FOR_PROSPECTIVE_TESTING`
- `ACCEPT_PROGRAM_LEVEL_ONLY__EDGE_LEVEL_UNSTABLE`
- `REJECT_NETWORK__CONTROL_FAILURE`
- `REJECT_NETWORK__PROVENANCE_OR_LEAKAGE_FAILURE`
- `INCOMPLETE__DO_NOT_OPEN_PROTECTED_OUTCOMES`

No intermediate result should be silently promoted.
