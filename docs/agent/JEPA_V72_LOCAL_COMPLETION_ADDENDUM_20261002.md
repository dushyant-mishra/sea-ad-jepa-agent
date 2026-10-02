# V72 local completion addendum — 2026-10-02

This addendum supersedes the V72 handoff's earlier statement that V71/V72 synthetic readiness had not yet been CI-qualified.

## Sol implementation branch

Branch:

`chatgpt/v72-synthetic-twin-successor-20261002`

Current head after qualification receipt:

`e3cf34835d36e2199aeeb0cdfb4d46616f560fc8`

Base:

`chatgpt/v64-privileged-information-recoverability-20260930 @ 4fd4305395c4da0c025f336006be7c9dbbe6dd70`

Draft PR:

`#200`

## Exact execution evidence

Qualified code head:

`2f410f883e877e1e3de412583cc5fd91ce3219ad`

GitHub Actions:

- workflow: `V64 privileged-information architecture smoke`
- run: `36970470574` / run #426
- job: `110723184448`
- conclusion: **success**
- pytest: **314 passed in 20.55 s**
- direct validator outputs:
  - `PASS: V71 synthetic pipeline R0/R1 interfaces present`
  - `PASS: V72 coupled multi-dataset synthetic fixture`
  - `PASS: V72 synthetic pipeline R0/R1 executable readiness`
  - CI-scale resource estimator executed

Qualification receipt commit:

`e3cf34835d36e2199aeeb0cdfb4d46616f560fc8`

The receipt-only head itself was then tested in GitHub Actions run `36970595190` / run #427 and also concluded **success**.

Machine-readable receipt:

`results/v64/V72_SYNTHETIC_R0_R1_QUALIFICATION_RECEIPT_V1.json`

## Work completed in this environment

1. V71 readiness validator now has behavioral tests and is wired into the architecture CI workflow.
2. An old V71 transpose-corruption validator crash was fixed to fail closed with explicit diagnostics.
3. V72 coupled hidden truth now emits:
   - FULL104-like RNA + structural missingness;
   - Stage4-like overlapping windows and matched controls;
   - SCENIC+-like paired multiome and raw fragments;
   - Morabito-like separate-nucleus RNA/ATAC;
   - perturbation-like guide/count data;
   - spatial limited-panel observations;
   - checkpoint twins.
4. Stage4 synthetic controls reproduce promoter-fixed matched-control semantics and all-overlap geometry.
5. S102 is preserved as an open G2 specification gap; no post-hoc threshold was selected.
6. Synthetic SCENIC+ enforces barcode→donor authority, ranking-seed/thread pins, route-union score reuse boundaries, route-specific rankings, immutable execution/shard/merge invariants.
7. Synthetic Route-B CI now consumes raw fragments, creates donor×subcluster pseudobulks, emits deterministic consensus regions and donor recurrence, and re-reads/digests outputs. It explicitly does **not** claim real MACS qualification.
8. Checkpoint twins are behavioral arrays for collapse, source shortcut, donor shortcut, private-state leak, overconfident unrecoverable state, and corrupt manifest.
9. The checkpoint evaluation cohort is source-stratified; the source-shortcut threshold was not weakened.
10. Ordinary pipeline validation is observable-only. Private-state leakage is assessed only in explicit final-unblind audit mode.
11. Stress/full-scale deterministic sharding and exact FULL104 source-count planning are implemented.
12. A measured-CI resource estimator exists; full-scale estimates remain planning-only.
13. A prospective Stage4 G2 specification-process contract exists without a numerical margin.
14. Macha Stage4 head `759bf0f2...` was independently audited.
15. Macha SCENIC+ head `f8dc4935...` was independently audited.
16. Route-B blacklist policy is prospectively frozen to Boyle/ENCODE hg38 blacklist v2 before consensus-peak agreement is observed.
17. Route-B successor provenance contract requires acquisition↔QC fragment digest binding plus SHA-bound chromsizes/blacklist inputs.
18. A successor SCENIC+ Docker recipe pins `create_cisTarget_databases` commit `304d5dc1b15e5c923908a50a1ec291c3faaccf9c`, while preserving the historical validated recipe unchanged. The successor deliberately fails closed until historical cbust/liftOver/bigWigAverageOverBed SHA-256 values are supplied.

## Independent Macha audit findings added by Sol

### Stage4

`results/v64/V72_MACHA_STAGE4_759BF0F2_INDEPENDENT_AUDIT_V1.json`

Key limitation: V2 aggregate arithmetic reconciles internally to 320 successful draws, but the audited repo directory does not carry a per-draw ledger from which a GitHub-only auditor can independently recount every draw.

### SCENIC+

`results/v64/V72_MACHA_SCENICPLUS_F8DC4935_INDEPENDENT_AUDIT_V1.json`

New findings:

- SCA7: Route-B pseudobulk producer needs cryptographic acquisition-receipt ↔ QC-receipt binding to the same fragment bytes, not merely the file size.
- SCA8: Route-B consensus producer needs SHA/byte binding for chromsizes and blacklist, not path-only provenance.

These are prospectively closed by the V72 successor contract but still need to be implemented/used by Macha before real Route-B freeze.

## What remains outside this environment / not qualified

The following were **not** promoted by this work:

- 100k/500k medium stress execution;
- full 4,553,407-cell synthetic materialization;
- real 63.6 GB Route-B pseudobulk extraction;
- real MACS/pycisTopic consensus peaks;
- complete worker-scaling/shard-size receipt from Macha if pushed later;
- full 10,249-motif custom cisTarget build;
- real Route-A/Route-B eRegulon networks;
- donor stability and network/program qualification;
- final Stage4 G2 decision rule;
- Stage4 real correspondence;
- protected Morabito;
- recoverability TEST;
- multimodal training.

## Current governance

- Stage4: NOT AUTHORIZED
- correspondence: UNOPENED
- training: OFF
- multimodal training: OFF
- Morabito: PROTECTED
- recoverability TEST: SEALED
- SCENIC+ network: NOT YET QUALIFIED

## First action for successor

Re-query Macha Stage4 and SCENIC+ branches. At the time of this addendum they remain exactly:

- Stage4: `759bf0f276307ad296e9a8669f39adccc1a7f83a`
- SCENIC+: `f8dc493516db079fd529e4a69f370d8b9db0dfad`

Do not redo V71/V72 R0/R1 work. Proceed to medium-stress execution when resources permit, and audit/consume Macha's next heavy-run receipts when they actually land.
