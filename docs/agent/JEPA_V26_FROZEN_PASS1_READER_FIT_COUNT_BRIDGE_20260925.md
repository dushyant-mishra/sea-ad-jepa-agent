# V26 frozen-pass1 ↔ reader-fit donor-count bridge — independent CPU review

Date: 2026-09-25. Status: **CODE + SYNTHETIC CI REVIEW, PHYSICAL FROZEN PASS1 FILE NOT MOUNTED HERE.** This is a **separate, fast read-only consistency check** and not another pass1/full104 physical reconstruction.

## What already exists (do not duplicate)

- `src/sea_ad_jepa/v5/full104_pass1_physical_binding_v1.py` provides `verify_pass1_against_physical_full104`: when physically executed on the authenticated 8,915 blocks, it binds every selected row's donor code and strict-core support from original Level-4 counts/metadata to the pass1 arrays and fails on duplicates, missing rows, source disagreement or hash mismatch. It is a heavy **separate** physical source validator. Its receipt **does not** independently compare each donor's population size against the original frozen August 24 reader-fit metadata.
- PR #120 has an independent full raw-count 104×17,186 recomputation for **donor_umi and donor_nnz**, a distinct outcome-blind N1 *data-integrity* task. It is not this read-only histogram comparison, and neither check authorizes scientific N1 burden outcomes.
- PR #130 byte-verified the 410,278,055-byte Aug24 ZIP (SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`), exact 104/22/23 partition and 104 reader-fit count sum 4,553,407, with member and derived count SHA roots.

## What this incremental bridge verifies

`src/sea_ad_jepa/v5/frozen_pass1_reader_fit_count_bridge_v1.py` compares the **WHOLE-FILE hash-pinned frozen pass1 NPZ** from PR #120, SHA-256 `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`, against those frozen donor counts without opening 8,915 raw blocks. It loads only the pass1 `duniq` and `cell_donor` arrays using `allow_pickle=False`, after hashing the pass1 using the same open file descriptor. The calibration ZIP is independently rehashed and its two tiny allowlisted CSVs read through one descriptor. It rejects:

- historical reduced/94-donor or original T1 files substituted for frozen pass1; extra continuation/held-out donors; duplicate/padded donor IDs;
- the important silent failure **same 4,553,407 global cell count, incorrect cells per donor** (including donor-to-donor swaps);
- noninteger/out-of-range donor codes, corrupt/pass1 altered after a recorded old hash, a missing NPZ key or object-array metadata;
- stale or mismatching frozen metadata fingerprints.

A second adversarial control demonstrates its **scope limit**: an equal-count reciprocal exchange of two cells between donors leaves every donor histogram unchanged, so the histogram gate deliberately reports `balanced_reciprocal_cell_swaps=NOT_DETECTABLE_BY_HISTOGRAM` and `per_cell_donor_lineage_validation=NOT_PERFORMED_BY_THIS_GATE`. Only the existing physical pass1 binder's selection-row-level rederivation can detect that specific form of swapped identity. The whole-file pass1 SHA prevents unrecorded post-freeze swaps, but **does not replace a separate physical raw-source audit**.

No donor IDs appear in the machine-readable receipt. The helper exposing synthetic structure never emits a frozen byte-authority receipt; the full caller uses frozen source SHAs and is **not** a production input.

## Exact physical invocation, only when the genuine source file is available

The GPU-laptop operator or a separately authorized read-only reviewer can run this once against the **exact current PR120 frozen pass1** and previously SHA-bound Aug24 calibration ZIP, without streaming original SRA, running N1 or training JEPA. In a clean worktree at the review source commit:

```powershell
$env:PYTHONPATH = "src"
python -m sea_ad_jepa.v5.frozen_pass1_reader_fit_count_bridge_v1 `
  --pass1 "<EXACT_FROZEN_PASS1_NPZ_FROM_PR120>" `
  --calibration-zip "<SHA_VERIFIED_AUG24_CALIBRATION_ZIP>" `
  --out "<NEW_EMPTY_VERSIONED_RUNTIME_DIR>/V26_FROZEN_PASS1_READER_FIT_COUNT_BRIDGE_V1.json"
```

`--out` refuses to overwrite an existing report. On mismatch, it raises before writing a success receipt. Preserve the exact command, worktree commit, original full-file input SHA receipts and the report's own SHA-256. A valid physical report must say `BYTE_BOUND_PASS1_AND_METADATA_COUNTS_ONLY` and `per_donor_exact_count_match=true`; **never** translate this into `pass1_to_raw_level4_binding=PASS`.

## Authorization and scope boundary

- The archived calibration bundle is physically mounted and independently verified in this ChatGPT environment; the frozen pass1 NPZ (SHA `37f79...`) and all 8,915 raw blocks **are not** physically mounted here. CI runs use synthetic fixture NPZ files with test-scoped hash monkeypatches: tests **cannot** be mistaken for the required real 104-donor physical execution.
- Even a physical success proves **only** that the named hash-pinned pass1 has the right donor count vector. The existing `verify_pass1_against_physical_full104` or another separately reviewed raw lineage receipt must also have physically succeeded before claiming pass1→Level4 truth; this bridge does not consume a self-declared physical receipt as proof.
- No proposal `q_i` or exact realized `p/q` weighting is certified. No actual V5 training/update/checkpoint, evaluator, mask/target qualification, reader-validation/oracle/Foundation/Siletti or pathology outcome was accessed or authorized.
- Do not ask Claude to rescan all 8,915 blocks for this bridge or interrupt independently running N1/perturbation work. If a verified raw-binding receipt is already delivered by Claude, pair the **two independently sourced** receipts in a subsequent nontraining handoff and proceed only under an explicit scoped diagnostic authority.
