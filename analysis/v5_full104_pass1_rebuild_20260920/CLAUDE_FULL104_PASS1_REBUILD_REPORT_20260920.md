# FULL104 pass1 rebuild and physical substrate qualification — 2026-09-20

Status: `PHYSICAL_SUBSTRATE_QUALIFIED__PASS1_REBUILT_AND_VERIFIED__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF`

Predecessor evidence root (corrected inventory report):
`3aaa1509bf6c9987fd93677c9f53e3191d6def63ea8cb7e0e5132126bee7412d`

No terminal masking outcome, target-panel ladder, null-equivalence margin,
D_shared, protected, pathology, DEV or SEALED outcome was opened. No training.
No masking policy selected.

---

## 1. Why the previous pass1 was rejected

The September-17 `pass1.npz` was an ad-hoc scratchpad artifact. Its per-cell
vectors were indexed by **block iteration order**:

```python
cell_donor[pos:pos+n] = dcodes   # storage position
pos += n
```

The authoritative global cell identity is `selection_row` in the physical block
metadata. The current physical verifier rejected it:

```
ValueError: pass1 cell_donor does not rederive from physical metadata
  full104_pass1_physical_binding_v1.py:347
```

Decisive diagnosis over 12 blocks:

| indexing | blocks matching |
|---|---|
| by `selection_row` | **0 / 12** |
| by block position | **12 / 12** |

Block 0's first `selection_row` values are `140, 219, 248, 272, 281, 345` — not
block order, so the two indexings genuinely differ.

Reclassified `INVALID_FOR_CURRENT_ROLE__ROW_IDENTITY_KEYED_TO_BLOCK_ITERATION_ORDER`.
It was not requalifiable: the row-identity mapping was wrong, not stale.

### Scientific consequence

`cell_donor` is the join between the cell-level representation and the
donor-level outcome. Corrupting it means donor-held-out evaluation stops holding
anything out: cells physically belonging to the evaluation donor are relabelled
into training folds.

It **invalidates donor-held-out inference and can bias apparent cross-donor
performance upward**, because physical donor information leaks across the nominal
train/evaluation boundary. Upward bias is the dangerous expected direction, but
it is not a mathematical guarantee for every arbitrary permutation. Either way
the inference is void, and nothing downstream would have flagged it.

The donor axis was unaffected: `duniq` was `sorted(unique donor_id)`, a stable
storage-independent rule, and `donor_addr_nnz` was accumulated from each block's
own metadata. Only the per-cell vectors were wrong.

### Why the September-17 aggregates were still arithmetically right

Every statistic computed from that artifact was order-invariant — counts, means,
percentiles, and a donor×address matrix keyed by donor code. A row permutation
changes none of them. The summaries were blind to the defect by construction,
which is why their stability provided no assurance. They are retained as
`HISTORICAL_SUPPORTING_CROSSCHECK_ONLY`.

---

## 2. Canonical donor ordering — verified before rebuilding

Derived from hash-verified physical metadata only, before constructing anything:

| check | result |
|---|---|
| donors derived | 104, all unique |
| `duniq == sorted(unique physical donor_id)` | **True** |
| source split | 41 HVS / 17 NPH52 / 46 SEA_AD |
| every donor maps to exactly one physical source | **True** |
| **identical ORDER to September-17 `duniq`** | **True** |
| `donor_src` bitwise identical | **True**, zero mismatches |

The old ordering was reproducible by a stable storage-independent rule, so it is
**preserved explicitly** as `DONOR_ORDER_RULE = SORTED_UNIQUE_PHYSICAL_DONOR_ID_V1`
rather than re-invented. This matters because the source-stratified outer split
assigns folds by donor index; a new ordering would have changed the split.

---

## 3. New builder

`src/sea_ad_jepa/v5/full104_pass1_builder_v1.py`

Declares two storage-independent rules:

- `CELL_IDENTITY_RULE = GLOBAL_SELECTION_ROW_IDENTITY_V1`
- `DONOR_ORDER_RULE = SORTED_UNIQUE_PHYSICAL_DONOR_ID_V1`

Binds/verifies: FULL104 manifest SHA, canonical registry SHA, observation-state
SHA, every count-block hash, every metadata hash, complete `selection_row`
closure (in range, no duplicates within or across blocks, every one of the
4,553,407 positions filled exactly once), donor→source identity, and exact output
geometry. Refuses overwrite.

It **builds only**. `full104_pass1_physical_binding_v1.py` is unmodified and
remains the sole verifier.

### Tests — `tests/test_v5_full104_pass1_builder_v1.py`

11 new tests, plus the 7 pre-existing binding tests still green (18 total),
confirming the verifier is not weakened:

| test | proves |
|---|---|
| block-order scramble | arrays byte-identical |
| within-block row scramble | arrays byte-identical |
| both scrambles together | arrays byte-identical |
| **September-17 negative control** | block-position indexing **is rejected** by the unchanged verifier |
| correctly-built pass1 | accepted by the unchanged verifier |
| donor order rule | equals `sorted(unique)`, not file order |
| donor spanning two sources | fails closed |
| duplicate `selection_row` | fails closed |
| overwrite | refused |

---

## 4. Substrate provenance finding — `op37/block-00001`

The first shakedown attempt failed at `int(meta["source_library"])` on the string
`'61129.0'`.

| | |
|---|---|
| blocks with decimal-formatted `source_library` | **1 of 8,915** (`op37/block-00001`, NPH52, manifest index 8497) |
| affected rows | 512 |
| rows parsing as `int()` elsewhere | 4,552,895 |
| non-integral values | **0** |
| non-positive values | **0** |

Classification: `AUTHENTICATED_FORMATTING_ANOMALY_NOT_A_DATA_DEFECT`. The bytes
are hash-authenticated and all 512 values are positive integers.

**Open question, not blocking:** why `op37/block-00001` was serialised
differently from the other 8,914 blocks.

The failed attempt is preserved as
`evidence/FAILED_SHAKEDOWN_USB_ATTEMPT_20260919.json` and was not overwritten.

### Parser repair (PR #29, head `1fef4452`) — independently audited

`_parse_source_library` uses exact `Decimal` parsing. Adversarial test, 22 cases:

- accepts `61129`, `61129.0`, `  61129.0  `, `6.1129E+4`, `61129.00000`
- rejects `0`, `0.0`, `-5`, `-61129.0`, `0.5`, `61129.5`, `1e-3`, `nan`, `NaN`,
  `inf`, `Infinity`, `-inf`, `''`, `abc`, `0x10`, `None`
- accepts `1_000` as 1000 (Python underscore separators) — a correct integer
  reading, not a weakening

`Decimal` over `float` is correct in principle: at 2^53+1, `float()` silently
returns an off-by-one; `Decimal` is exact.

---

## 4a. Metadata/matrix row correspondence and `expression_row`

### Why the correspondence holds — construction lineage, not a runtime test

The primary provenance is the authenticated materializer lineage bound by the
materialization manifest:

| role | SHA-256 |
|---|---|
| Level-4 block manifest | `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29` |
| Python materializer | `575d02a4e7f7c5c6f3187eeed691a2eac7d3f1df9510621bc497b283806c270b` |
| NPH R materializer | `ca595536f6144a1f6fb2570fe24f58c5335ba31e43a1f9a4b660e18db58e7529` |

Both materializers construct the sparse matrix row and the metadata row from the
**same ordered `take` selection**. The Python/H5 path writes sparse row `local`
and metadata row `local`; the NPH R path builds matrix rows from `columns[take]`
and metadata from `requested[take]`. That construction is the reason metadata CSV
row *i* corresponds to sparse matrix row *i*.

### The runtime check is a necessary condition, not a proof

An earlier draft of this report said the sampled library-size test "proves" CSV
row order equals matrix row order. **That wording was too strong and is
withdrawn.**

The test — a row's summed raw counts cannot exceed that row's `source_library` —
is a *necessary-condition / adversarial diagnostic*. Over 8 blocks it gives 0
violations as built and 1,980 under a deliberate shuffle, so it has power to
detect misalignment and would refute the correspondence if it failed. Satisfying
a necessary condition does not establish identity.

It is retained as **defense in depth**, and uses the exact positive-integral
parser rather than loose `float()` parsing.

### `expression_row` — resolved

`expression_row` is **not** a block-local row identity, which is why values such
as 3471 appear inside a 512-row block.

| path | meaning |
|---|---|
| Python / H5 materialization | the original source H5 matrix row used to retrieve the cell |
| NPH R materialization | the zero-based original source matrix column/cell coordinate, `columns[take] - 1` |

It must never be used as a replacement for `selection_row`. **`selection_row`
remains the immutable global FULL104 cell identity.**

---

## 5. Execution environment

Canonical: conda env `sea-ad-jepa`.

| | BEFORE | CANONICAL |
|---|---|---|
| SHA-256 | `01bc18ab615c79fe0205188f2b4b0908d7b9555c4784f344770f63ed5bbf9b38` | `dba5f169160cfd7bb7c3e5c8d3070a56c6159667d3aacf996b692255b2d321c6` |

Python 3.11.15 · numpy 1.26.4 · scipy 1.15.3 · sklearn 1.5.2 · pandas 2.2.3 ·
torch 2.7.0+cu128 · CUDA 12.8 · RTX 3080 Laptop 17.18 GB.

Only change: `pytest 9.1.1` plus required deps `iniconfig`, `pluggy`, `Pygments`.
**Nothing removed, nothing up- or downgraded.**

### BLOCKER: this environment cannot run dense linear algebra

`np.linalg.solve` **kills the process** — Windows fatal exception `0xc06d007f`,
on a matrix as small as 4×4.

| env | numpy | 4×4 solve |
|---|---|---|
| `base` | 1.24.2 | works |
| `sea-ad-jepa` | 1.26.4 | **process killed** |

**Observed fact:** `np.linalg.solve` terminates the canonical interpreter with
Windows fatal exception `0xc06d007f`, even on a 4x4 system. Reproduced repeatedly.

**Current diagnosis (hypothesis, not established):** a broken BLAS/LAPACK
linkage. numpy reports `blas 3.9.0` with placeholder
`lapack: dep1473604930576`; the env holds a 108 KB `libblas.dll` shim alongside a
72 MB `mkl_core.3.dll`. The delay-load failure code is consistent with the shim
failing to forward, but this is **not proven** until subprocess-isolated backend
diagnostics establish it. The distinction matters: the symptom is certain, the
cause is not.

Surfaced via `full104_masking_qualification_runner_v1.py:277` (`_fit_ridge_weights`).

- **Does not block** shakedown, pass1 rebuild or census — none use dense solves.
- **Does block** the entire masking qualification, which is ridge solves end to end.

Not repaired: fixing it means changing a BLAS package, which exceeds the
"install pytest only" instruction. Repair will invalidate `dba5f169…` and require
a fresh canonical snapshot.

---

## 6. Storage staging

Level-4 **copied** (not moved) to `C:\jepa_full104_ssd\expression_level4`.
`D:` remains the untouched source-of-record.

| | |
|---|---|
| files | 18,764 / 18,764, **0 failed, 0 mismatch, 0 extras** |
| bytes | 66,264,337,295 both sides |
| independent recheck | 0 missing, 0 extra, 0 size mismatches |
| copy time | 8.9 min @ 139 MB/s |

All four roots re-authenticate on the copy, and `op37/block-00001` is
byte-identical with `61129.0` preserved verbatim — nothing rewritten or cleaned.

**Correction to an earlier claim of mine:** I predicted the SSD would
substantially speed up the full passes, inferring "I/O-bound" from 27% CPU
utilisation. It did not. The SSD shakedown took 131.4 min. Peak RSS of 195 MB and
the observed throughput indicate the cost is CPU-side — zlib decompression, CSR
conversion, and `log1p` over 23.7 billion nonzeros — not disk. The copy remains
worthwhile for independent byte verification and for leaving `D:` untouched, but
not for the reason I gave.

---

## 7. Results

### Physical shakedown — PASS

Receipt `56ffb8687275eb81f9e8119c6279d9ef4eb6d536f3bc055bc32e5945064a8722`

| | |
|---|---|
| status | `FULL104_PHYSICAL_SHAKEDOWN_PASS` |
| blocks / rows / donors / operators / addresses | 8,915 / 4,553,407 / 104 / 42 / 41,238 |
| total nnz | 23,690,278,596 |
| elapsed | 7,884.4 s (131.4 min), 577.5 rows/s |
| peak RSS | 195,403,776 B |
| GPU memory | 0.0 MiB |

`total_nnz` matches the independent manifest sum exactly
(866,810,687 + 958,526,621 + 21,864,941,288). Because it re-hashes all 18,764
files, this doubles as byte-integrity verification of the SSD copy.

### Rebuilt pass1 — verified

| artifact | SHA-256 |
|---|---|
| pass1 NPZ (18,029,576 B, **not committed**, on GPU machine) | `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1` |

### PR file counts — both figures are correct

| figure | meaning |
|---|---|
| **15 files** | the PR31-specific successor delta *relative to PR29* (`1fef4452`) |
| **19 files** | the GitHub PR #31 diff against its actual base `a51cdbe8`, which also contains the PR29 parser changes |

The total PR surface must not be described as 15 files without that
qualification.
| physical binding receipt | `4c44b89e91e85b762224a6c2cf7e5cd88956a1726f57a52c03ddcab4ad0c3602` |
| census summary V2 | `ebe31809e29c3462854e0ecebe9e3ad1af1ae21885a0dcca4ca3e3581425676d` |
| split receipt | `5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4` |
| target eligibility | `33539852932a8d71eea6984b9a3c946a22574e7fccfba5ed09bd59438e4aa2f9` |

Build: 29.4 min, 13,069,917,135 core nonzeros.

The binding receipt carries semantic digests for `cell_donor`, `cell_nnz_core`,
`donor_core_nnz`, `donor_ids`, `donor_source` and `strict_core_cols`, so the
arrays are content-addressed rather than merely declared.

### September-17 comparison — every quantity `REPRODUCED_EXACTLY`

| quantity | Sept-17 | rebuilt | class |
|---|---|---|---|
| cells | 4,553,407 | 4,553,407 | REPRODUCED_EXACTLY |
| donors | 104 | 104 | REPRODUCED_EXACTLY |
| strict core | 17,186 | 17,186 | REPRODUCED_EXACTLY |
| source cells | 198,718 / 236,476 / 4,118,213 | identical | REPRODUCED_EXACTLY |
| core measured-zero frequency | 0.832983 | 0.8329826626244999 | REPRODUCED_EXACTLY |
| core measured-zero count | 65,184,935,567 | 65,184,935,567 | REPRODUCED_EXACTLY |
| core-nonzero percentiles | 1/438/887/1840/2822/3773/5020/6547/11181 | identical | REPRODUCED_EXACTLY |
| fold sizes | 28/26/25/25 | 28/26/25/25 | REPRODUCED_EXACTLY |
| donor cells min/median/max | 81 / 14,749 / 174,111 | identical | REPRODUCED_EXACTLY |
| Kish ESS | 42.0 | 41.9867 | REPRODUCED_EXACTLY |
| per-fold estimable | (expected) | **17,070 / 17,071 / 17,072 / 17,060** | matches expected |
| all-fold eligible targets | (expected) | **17,053** | matches expected |

Nothing is `CHANGED_AFTER_IDENTITY_CORRECTION`. No hard-coded expectation was
modified to fit.

**Arithmetic/support consistency check:** the summary computes core nonzeros two
independent ways — summed from the per-cell vector and summed from the
donor×address matrix — and both give **13,069,917,135**. These accumulate through
different code paths, so the agreement is real evidence of arithmetic and support
consistency.

It is **not an identity check.** Both totals are invariant under row permutation,
so they would have agreed under the September-17 defect too. The actual identity
evidence is:

- `cell_donor[selection_row]` verified against physical metadata, per block;
- `cell_nnz_core[selection_row]` verified against the corresponding physical
  matrix row, per block;
- complete `selection_row` closure over all 4,553,407 positions;
- authenticated materializer row-order construction (see §4a).

Kish ESS is recorded with `kish_ess_is_inferential_donor_sample_size: False`
alongside `independent_donor_units: 104`. Independent donor N remains **104**.

---

## 8. Specific points for independent review

1. **The `1_000` case.** `Decimal` accepts Python underscore separators. I judged
   this benign (still a correct integer reading). Confirm that judgement.
2. **CSV-order ↔ matrix-row alignment.** Both the shakedown and the verifier
   assume metadata CSV row *i* corresponds to sparse matrix row *i*. Nothing in
   the code asserts it. I tested it: summed raw counts never exceed
   `source_library` when aligned (0 violations over 8 blocks), and break
   immediately when shuffled (1,980 violations). The assumption holds, but it
   should be an explicit assertion rather than an unwritten invariant.
3. **`expression_row` is read and validated but never used for alignment**, and
   its values exceed block row counts (e.g. 3471 in a 512-row block), so it
   indexes something other than the block. Worth confirming what.
4. **Builder/verifier symmetry.** The builder deliberately reimplements the
   physical traversal rather than sharing code with the verifier, so the two are
   independent. Confirm that is the intended posture.
5. **My own error rate this session.** Three probes of mine were vacuous on first
   attempt and produced clean, plausible, wrong output. Treat single numbers here
   as provisional until re-derived.

---

## 9. Not done, not claimed

`OPEN_NOT_EXECUTED`: census authority V2; control-calibration cache;
preterminal authorities.

**Status correction.** An earlier draft said Census Authority V2 was blocked on a
`--support-authority` input that was "not yet available". That was stale. The
support authority is checked in at
`docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json`, canonical semantic
digest `cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08`. No
replacement support authority is to be created; that existing one is to be bound.

Still open and **not** closed by this work: H3 (equivalence power), G5
(null-equivalence margin basis), G3 (stronger attacker), G4 (signal-preservation
criterion), F13 (`F13_WAITING_FOR_AUTHENTICATED_V0_V1_PARENT_BYTES` — V0/V1
parents absent from this machine), F14, F15.

No terminal masking outcome at any rung. No policy selected. No margin chosen.
No training authorization.

`TRAINING_OFF`
