# PR #73 GPU/Windows metadata-only requalification — 2026-09-23

**Execution gate:** begin only after exact final code head has successful hosted masking + current-V5 workflows, including BOTH runs of `tests/test_v5_canonical_source_derivative_v1.py`, zero skipped, and the code/receipt patch is independently reviewed. This document itself grants no experimental authorization.

## Safe scope

- Original frozen heavy artifact **never overwritten**, old original quarantine and PR #69 receipts **never rewritten**.
- Existing corrected derivative `core_sufficient_statistics_canonical_source_v2_20260923.npz` is **read-only input** to the new V2 qualifier.
- Level-4 **metadata** only: all 8,915 meta SHA records; **no count matrices, no target choice, no mask, no burden, no precision, no real N1, no rare-tail molecular, no D_shared, no training**.
- The synthetic end-to-end producer/successor tests now run in the explicit no-skip hosted masking workflow. The actual physical run below is still required and cannot be simulated by CI.
- PR #63 and #66 remain separate.

## Reviewed reference identifiers (full hex required)

```text
original NPZ         f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae
original NPZ bytes   242087519
Level4 manifest      66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29
corrected NPZ        4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b
corrected NPZ bytes  363053057
PR69 array manifest file SHA    9517b95446013c7f803df0b63b662d24f2e1df81f0b4917a2af41dae1df2b1ee
PR69 array manifest canonical   4f55158c59d2ee6cdb3ad9276e887126ae78b5b9305021c8c607b524c61293a5
original 6-donor receipt file   bbd2b95b882f52c313a3623bab55e5d7ff6562cdba27e48f9c84009075cf713d
frozen split receipt file      56f045d7dc80fde7e30c97632c1d109286e4b8f9f033b77476521c2822980585
PR67 metadata cell-donor digest 3d56cda1d1d4ec228351b1f29197c9bce00ac8d7f12687430490fe7c6192a607
```

## A. Fetch and test reviewed HEAD

```powershell
git fetch origin --prune
gh pr view 73 --json headRefOid,baseRefName,state,isDraft
git switch --detach <EXACT_VERIFIED_FINAL_PR73_HEAD>
git status --porcelain
$env:PYTHONPATH = 'src;.'
python -m pytest -q -p no:randomly --strict-markers -rs tests/test_v5_canonical_source_derivative_v1.py tests/test_v5_audit_b_n1_source_lineage_v1.py tests/test_v5_audit_b_n1_physical_binding_v1.py
```

Ensure the active worktree has **zero uncommitted changes and zero skipped tests**; read PR #72 independent review and its downstream-consumer addendum. Check PR #73's two GitHub Actions runs are successful on this exact head; a green ancestor does not count.

## B. Identify physical inputs — placeholders below are NOT real paths

```powershell
$original = '<ACTUAL_GPU_ORIGINAL_CORE_SUFFICIENT_STATISTICS_V1_NPZ>'
$derivative = '<ACTUAL_GPU_CANONICAL_SOURCE_V2_NPZ>'
$level4 = '<ACTUAL_GPU_AUTHENTICATED_LEVEL4_ROOT>'
$pass1 = '<ACTUAL_GPU_AUTHENTICATED_FULL104_PASS1_NPZ>'
$arrayManifest = '<PR69_ORIGINAL_CANONICAL_SOURCE_DERIVATIVE_MANIFEST_V1_JSON>'
$originalSix = '<ORIGINAL_PR59_DONOR_UMI_INDEPENDENT_QUALIFICATION_V1_JSON>'
$split = '<ORIGINAL_FROZEN_FULL104_SPLIT_RECEIPT_V1_JSON>'
$outRoot = '<NEW_SEPARATE_METADATA_ONLY_REVIEW_OUTPUT_DIRECTORY>'
```

Before work, recompute physical SHA-256 and byte sizes of original and derivative, and SHA-256 of Level-4 manifest, PR69 array manifest, original six-donor receipt and frozen split. Abort on any mismatch. Do NOT use the smaller Stage81A3, 50K, discovery ZIP, calibration bundle or an old historical NPZ as replacements.

## C. Independently re-run the repaired producer WITHOUT overwriting existing derivative

Use the new PR #73 producer, which compares all 4,553,407 authenticated metadata donor IDs to the exact pass1 cell-donor vector and validates **all 35 NPZ members before publication**. Produce a **separate temporary candidate**, not the currently qualified derivative:

```powershell
python analysis/v5_full104_information_channel_redteam_20260920/scripts/build_canonical_source_derivative_v1_20260923.py `
  --original $original `
  --level4-root $level4 `
  --pass1 $pass1 `
  --out-derivative "$outRoot/independent_candidate_canonical_source_v2.npz" `
  --out-manifest "$outRoot/independent_candidate_manifest.json"
```

The independently produced candidate **must** have full SHA-256 `4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b`, or STOP and compare member-level digests *without* rebinding/rewriting current authority. The newly generated manifest includes the candidate's distinct absolute path; it is **not** a replacement for the PR69 reviewed manifest. Verify both remain metadata-only and original bytes unchanged.

If the independent producer fails at a source/donor/metadata check, report the first failure and leave N1 unopened. If candidate bytes differ due to container serialization despite identical member values, STOP for separate container reproducibility adjudication; do not silently promote a new file SHA.

## D. Independently requalify EXISTING corrected derivative with V2 successor checker

Use the original PR69 reviewed array manifest, not the newly produced candidate manifest. All 35 member values/dtypes/shapes must be independently reloaded and compared, and all inputs must match frozen physical SHA references; pass1 donor vector must match the independently authenticated PR67 full metadata digest. New receipt paths MUST NOT already exist.

```powershell
python analysis/v5_full104_information_channel_redteam_20260920/scripts/qualify_canonical_derivative_successor_v1_20260923.py `
  --derivative $derivative `
  --parent $original `
  --array-manifest $arrayManifest `
  --original-six-donor-receipt $originalSix `
  --split-receipt $split `
  --pass1 $pass1 `
  --out-six-donor "$outRoot/SIX_DONOR_SUCCESSOR_QUALIFICATION_V2.json" `
  --out-preflight "$outRoot/N1_PHYSICAL_PREFLIGHT_SUCCESSOR_V2.json"
```

Expected receipt schemas: `V5_FULL104_SIX_DONOR_SUCCESSOR_QUALIFICATION_V2` and `V5_FULL104_N1_PHYSICAL_PREFLIGHT_SUCCESSOR_V2`. The latter is **independent-review evidence**, NOT execution authority. Capture each receipt's full file SHA and canonical receipt digest; independently recalculate canonical digests from the JSON bodies. Verify `numeric_rows_unchanged_from_parent=true`, six distinct identities exactly 2/source, full all-member proof, full donor identity digest, mandatory fold digest and `source_invariant_violations=0`. Also rerun the original #62 binder negative test on the unchanged original; report it separately rather than writing an unconditional assertion into V2.

## E. Exact report

Return PR73 Git head; native OS/Python/numpy; physical full SHA+size of parent, existing derivative and independent candidate; 8,915 metadata SHA results; 4,553,407 exhaustive donor-identity match count; 35-member per-array comparison summary; existing vs candidate file digest comparison; focused native test counts/zero skips; newly versioned six-donor and preflight full file/canonical hashes; any failure and whether an incomplete stage remains; physical original file SHA unchanged; and all opened-state flags below.

**STOP after V2 receipts.** Do not run N1, #63 physical adapter, rare-tail molecular, TD60, D_shared/G5, pathology/DEV/SEALED, or training. Commit only scripts/test changes and **small** receipts to a distinct evidence PR, never 242MB/363MB/30GB files.

`AUDIT_B_N1=UNOPENED | MASKS=NONE | BURDEN=NOT_RUN | RARE_TAIL_MOLECULAR=UNOPENED | TD60=UNEXECUTED | PATHOLOGY_DEV_SEALED=UNOPENED | D_SHARED_G5=UNOPENED | TRAINING=OFF`
