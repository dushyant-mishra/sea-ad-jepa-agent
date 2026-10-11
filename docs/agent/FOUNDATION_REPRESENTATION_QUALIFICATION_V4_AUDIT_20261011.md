# Foundation Representation Qualification V4 — Independent Audit

Date: 2026-10-11

## Scope

This audit reviews PR #269 and the preserved Stage81A3 foundation-state evidence. It does not read protected pathology, TEST/Morabito, target-discovery values, or current Macha provisional outputs. It does not authorize training.

## Preserved evidence recovered from repository history

The archived Stage81A3 execution is substantive evidence, not a design-only document. Its report records 36 matrices, a 64,057-cell donor-balanced qualification substrate, 4,096 molecular features, and a 160-dimensional candidate state basis. It records a historical CPU peak RSS of about 6.39 GB and temporary-disk use of about 5.03 GB.

The preserved classifications are internally coherent with the underlying tables:

- `BALANCED_PCA160`: historically qualified candidate;
- state subspace: `STABLE`;
- individual axes: `ROTATING-WITHIN-STABLE-SUBSPACE`;
- coordinate uncertainty: `SUBSPACE-ONLY`;
- biological evidence response: `DISTINCT`;
- measurement-depth response: `SUPPORTED`;
- biology/measurement separation: `SUPPORTED`;
- two-axis domain support: `INFORMATIVE`;
- cross-dataset transfer: `STRONG`;
- cross-technology transfer: `STRONG`;
- cross-donor transfer: `WEAK`;
- cross-matrix transfer: `WEAK`.

The donor-transfer table confirms that the weakness is not a clerical label. For `BALANCED_PCA160`, balanced accuracy across the eight donor folds spans approximately 0.398 to 0.626 while nearest-neighbor purity remains approximately 0.942 to 0.971. This is consistent with a globally coherent subspace that does not yet provide uniformly strong donor-held-out label transfer.

The matrix-transfer table also shows a structural limitation: many held-out HVS matrices are marked `not_identifiable_incompatible_label_vocabularies`; several SEA-AD matrices are highly predictable where a shared label vocabulary exists. Therefore a single pooled matrix-transfer score would be misleading.

## Audit of PR #269

The current implementation does not duplicate the old Stage81A3 computation. It provides four fail-closed current interfaces:

1. historical-evidence requalification;
2. prospective hierarchical dataset/source→donor→cell sampling;
3. explicit dense-allocation/compact-cache resource planning;
4. an authenticated CLI that binds the source report SHA-256 and publishes an exclusive atomic receipt without overwrite.

The requalification code correctly refuses to promote a historical report if pathology blindness, no-optimizer-update status, TRAIN-only expression scope, DEV/SEALED exclusion, or non-frozen production basis status differ from the preserved contract.

The transfer ladder is ordered and conjunctive: strong dataset/technology transfer cannot erase weak donor/matrix transfer. Under the preserved Stage81A3 classifications, current representation freeze remains blocked.

The observation-operator boundary reuses the existing physical-descriptor policy and rejects provenance shortcuts such as donor, matrix and dataset identity.

The sampling module requires explicit sublinear exponents `0 < alpha < 1`; those exponents are inputs, not outcome-tuned parameters. It normalizes dataset/source mass, donor-conditional mass and per-cell conditional mass separately. A metadata-only audit has now prospectively frozen the primary exponents at `0.25`/`0.25` with fixed, non-adaptive `0.5`/`0.5` sensitivity; no expression outcome, pathology, target value or representation result was used to choose them.

The resource guard explicitly forbids full-registry dense authority and allows only a selected-gene dense cache after a declared memory budget check. For 4,000 cells × 41,238 addresses × float32, a single dense matrix is 659,808,000 bytes before any additional intermediates. A 4,000 × 3,000 float32 selected cache is 48,000,000 bytes.

## Verification

TDD was completed on the final implementation head `685ff5c2b7988907e09ce7dcdca75990f81821d3`:

- RED run `38150302135`: `2 failed, 12 passed`, both failures being the expected missing authenticated CLI entry point;
- GREEN run `38150355930`, job `114502345286`: **14 passed in 0.45 s**.

Earlier harness failures while making the dependency-light import path portable are preserved development evidence and were not scientific endpoint failures.

## Subsequent evidence addenda

The authenticated project-mounted calibration bundle adds a learned-representation shortcut result that is scientifically stronger than the old pre-learning technology result. See:

- `docs/agent/FOUNDATION_REPRESENTATION_T1_SHORTCUT_AUDIT_ADDENDUM_20261011.md`;
- `docs/agent/FOUNDATION_PROJECT_MOUNTED_DATA_CUSTODY_20261011.json`;
- `docs/agent/FOUNDATION_RESOURCE_PATH_AUDIT_20261011.md`;
- `results/v4/FOUNDATION_PRODUCTION_SAMPLING_AUTHORITY_V1.json`.

The learned T1 result means technology invariance is **not currently qualified**; source/operator/support remain strongly decodable on held-out TRAIN donors. Because these variables are partly aliased with donor and biological composition, the evidence is not labeled proof of a purely technical causal failure. A conditional technology-imprint/invariance gate is required.

## Scientific ruling

The recovered historical evidence substantially advances the project, but it does **not** justify a current production representation freeze.

Current ruling:

`FOUNDATION_REPRESENTATION_ENGINEERING_CLOSED__HISTORICAL_SUBSPACE_EVIDENCE_REQUALIFIED__LEARNED_T1_TECHNOLOGY_INVARIANCE_NOT_QUALIFIED__SAMPLING_AUTHORITY_FROZEN__CURRENT_REPRESENTATION_FREEZE_BLOCKED__TRAINING_OFF`

Consequences:

- use subspace/block uncertainty rather than axis-by-axis certainty;
- keep biological-evidence and measurement-depth response curves separate;
- retain separate biological-support and measurement-domain OOD axes;
- use the donor→matrix→dataset→technology escalation prospectively;
- do not freeze a representation until donor and matrix transfer are requalified under the current final substrate/vocabulary contract;
- require conditional technology-imprint/invariance analysis on the final representation;
- do not expose donor/dataset/matrix identity as model inputs;
- use the prospectively frozen metadata-only sampler (`0.25` primary, `0.5` fixed sensitivity) without outcome-adaptive selection;
- treat the historical 6.39 GB/5.03 GB runtime as historical evidence, not a production resource guarantee.

## Unchanged firewalls

`training_authorized=false`

`target_discovery_value_read_authorized=false`

`stage4_authorized=false`

No TEST/Morabito, pathology, SCENIC+/ATAC target evidence, target ranks, V78 retuning or provisional Macha parameters are consumed by this audit.
