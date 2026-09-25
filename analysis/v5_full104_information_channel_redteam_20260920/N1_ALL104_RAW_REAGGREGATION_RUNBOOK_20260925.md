# N1 corrected FULL104 all-104 raw-count reaggregation — prospective execution runbook

Date: 2026-09-25. **Prospective CPU/data-integrity gate only; no real N1 outcome opened.** Parent is exact PR #80 @ `64148023740d57777666faff15395262d4b0e3da`; PR #83 and #85's corrected physical adapter source is already in that lineage. Never restore PR #62's quarantined original-file authenticator as the positive gate.

## Why this is new work

Historical independent raw-count qualification recomputed entire strict-core rows for **six source-stratified donors** while authenticating metadata for all 4,553,407 cells; it did not read all 8,915 raw count blocks and compute every donor row. The corrected derivative subsequently received exact source-order repair and read-only adapter qualification. Those do **not** prove that its donor_umi/donor_nnz arrays match the physical Level-4 raw counts for **all 104 donors**.

The new `scripts/qualify_all104_corrected_raw_reaggregation_v2.py` requires:

- corrected physical derivative SHA-256 `4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b` and 363,053,057 bytes; explicitly never the quarantined `f77dff47...`;
- frozen pass1 whole-file SHA-256 `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`;
- frozen Level-4 manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`;
- canonical corrected source names HVS/NPH52/SEA_AD (41/17/46 donors), all 4,553,407 cells, strict-core ordered 17,186 addresses, 8,915 authentic metadata and **8,915 authentic raw count blocks**;
- exact cell→donor→corrected source consistency, each selection row exactly once, no negative/fractional/nonfinite or >2^53-1 raw counts, no loss of integer precision in weighted reduction;
- exact integer equality of **both** full `donor_nnz` and `donor_umi`, shape 104×17,186 (1,787,344 entries per array), no tolerance. Output file must not preexist.

The resulting receipt is `V5_FULL104_ALL104_CORRECTED_RAW_COUNT_AUDIT_V2` with a pass **only if both whole matrices match**. A mismatch is a signed failure, never qualification. The entire computation is an independent read-only reaggregation, no monolithic FULL104 matrix, no masks, burden, precision, teacher/student model or protected result.

## Exact GPU-laptop execution

On the existing fully authenticated GPU Windows machine, check out this review branch in a **separate clean worktree**. Resolve the exact corrected-derivative/pass1/Level-4 paths from the current asset manifest and PR #83's physical adapter receipt; never substitute an earlier smaller-run or a guessed similarly named file. Install only the existing numpy/scipy environment compatible with the frozen Level-4 sparse NPZ. Ensure sufficient disk to read the raw blocks and a *new* versioned output directory.

```powershell
python analysis/v5_full104_information_channel_redteam_20260920/scripts/qualify_all104_corrected_raw_reaggregation_v2.py --artifact "<CORRECTED_363053057_BYTE_DERIVATIVE.npz>" --pass1 "<FROZEN_PASS1_NPZ>" --level4-root "<AUTHENTIC_FULL104_LEVEL4_ROOT>" --out "<NEW_VERSIONED_DIR>/N1_ALL104_RAW_COUNT_REAGGREGATION_V2.json"
```

Before interpreting the PASS, independently rehash the three source inputs and confirm 8,915 **physically opened** count blocks, no skipped blocks and exact 104×17,186 equality. Have a second reviewer inspect row indexing, no duplicate cells, exact count accumulation and the resulting receipt. The six-donor V1 qualification remains historical supporting evidence, not a substitute for this full check.

## No authority promotion

Even a successful full reaggregation is **only** raw input integrity. A separate independent review must then bind the corrected physical adapter, its six whole-file receipts, exact planner/executor source, frozen target/mask policy and synthetic crash-safe resume equivalence. Do NOT run real N1 masks or expose N1 outcomes based on this script or any self-declared authorization. Keep `AUDIT_B_N1=UNOPENED`, `TRAINING=OFF`, `D_SHARED_G5=UNOPENED` until explicitly authorized by the existing governance chain.

`SYNTHETIC_UNIT_CI` tests use tiny three-donor toy blocks with monkeypatched expected roots; they confer zero physical-data authority.
