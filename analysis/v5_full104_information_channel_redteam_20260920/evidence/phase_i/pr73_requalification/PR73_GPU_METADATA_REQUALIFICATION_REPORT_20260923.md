# PR #73 GPU/Windows metadata-only requalification — result

Date: 2026-09-23
Branch: `gpu/v5-pr73-metadata-requalification-20260923-claude`
Reviewed head executed: **`f2e227f4f379f637d676c9768acb38bc14151a84`** (PR #73)

**The independently rebuilt candidate is byte-identical to the existing corrected
derivative.** Full reproducibility, including the exhaustive 4,553,407-cell donor
identity check that PR #72's F2 asked for.

Metadata only. No count matrix opened, no target selected, no mask generated, no
burden or precision computed, no N1, no molecular RNA, no training.

---

## A. Reviewed head and native tests

```
git head    f2e227f4f379f637d676c9768acb38bc14151a84
worktree    clean (git status --porcelain empty)
os          Windows-10-10.0.26200-SP0 (AMD64)
python      3.9.7   numpy 1.24.2   scipy 1.10.1
```

Both hosted runs confirmed **on this exact head**, not on an ancestor:

| run | workflow | conclusion | head_sha |
|---|---|---|---|
| 35896224120 | V5 remaining-RNA and target-semantics successor | success | `f2e227f4…` |
| 35896224102 | V5 FULL104 masking runner | success | `f2e227f4…` |

Focused native suites:

```
tests/test_v5_canonical_source_derivative_v1.py
tests/test_v5_audit_b_n1_source_lineage_v1.py
tests/test_v5_audit_b_n1_physical_binding_v1.py
  -> 48 passed, 0 failed, 0 skipped
```

## B. Physical inputs — all verified before any work

| input | SHA-256 | bytes |
|---|---|---|
| original NPZ | `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae` | 242,087,519 |
| corrected NPZ | `4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b` | 363,053,057 |
| Level-4 manifest | `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29` | 2,372,002 |
| PR69 array manifest (file) | `9517b95446013c7f803df0b63b662d24f2e1df81f0b4917a2af41dae1df2b1ee` | — |
| PR69 array manifest (canonical, recomputed) | `4f55158c59d2ee6cdb3ad9276e887126ae78b5b9305021c8c607b524c61293a5` | — |
| original six-donor receipt | `bbd2b95b882f52c313a3623bab55e5d7ff6562cdba27e48f9c84009075cf713d` | — |
| frozen split receipt | `56f045d7dc80fde7e30c97632c1d109286e4b8f9f033b77476521c2822980585` | 4,429 |
| pass1 NPZ | `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1` | 18,029,576 |

**pass1 is frozen-bound after all.** F2 noted it was read "without a frozen file
SHA". The frozen split receipt already pins `pass1_npz_sha256` = `37f79e49…`,
which matches the physical file exactly. That is a binding that existed but was
not being *checked*; it is recorded here so a successor can enforce it.

No substitution: Stage81A3, 50K, discovery ZIP, calibration bundle and historical
NPZs were not used.

## C. Independent candidate rebuild — byte-identical

```
candidate  D:/jepa_full104_pr73_metadata_review_20260923/independent_candidate_canonical_source_v2.npz
sha256     4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b
bytes      363,053,057
existing   4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b   363,053,057
BYTE-IDENTICAL: true
```

Produced at a separate path; the existing qualified derivative was untouched, and
the original remains `f77dff47…` unchanged.

| | |
|---|---|
| metadata blocks SHA-verified | 8,915 |
| cells accounted exactly once | 4,553,407 |
| exhaustive donor-identity comparison | **all 4,553,407** metadata donor IDs vs `pass1.cell_donor` |
| `src_of_cell` mismatch in parent → candidate | 4,354,689 → **0** |
| members total / changed / unchanged | 35 / 2 / 33 |
| candidate manifest canonical | `dcba868a2dc43a4af7b461140a8c50162003d487a46a9a16ca21f8cd8e140bfe` |

The candidate manifest's canonical digest differs from PR #69's because it records
the candidate's distinct absolute path. It is **not** a replacement for the
reviewed PR #69 manifest, and it was not used as the authority in step D.

No container reproducibility adjudication is required: the bytes match, so the
`savez` vs `savez_compressed` question raised in PR #72 does not arise for this
artifact.

## D. V2 requalification of the **existing** derivative

Run with the **PR #69 reviewed** array manifest, not the candidate's.

```
SIX_DONOR_SUCCESSOR_QUALIFICATION_V2.json
  schema     V5_FULL104_SIX_DONOR_SUCCESSOR_QUALIFICATION_V2
  file       384572b1d52218f08712ba8fc663e746d1c4c1844d87dc233a24863c06c4fb65   5,810 B
  canonical  7046fd3591a06029a87c6c8d51952d092358a34388c1f602a9778bae15453cfb   (recomputed, matches)

N1_PHYSICAL_PREFLIGHT_SUCCESSOR_V2.json
  schema     V5_FULL104_N1_PHYSICAL_PREFLIGHT_SUCCESSOR_V2
  file       28dc18d2c7f9876c6b93cce318ecc0bb6fac42068e819b9047099a63eeaad91c   3,177 B
  canonical  cf068ff48dd9af4e5894945dca6a1fce58903363ed41a1a1b440a01406fd5c76   (recomputed, matches)
  state      NEW_PHYSICAL_N1_INPUTS_QUALIFIED_FOR_INDEPENDENT_REVIEW
```

Both canonical digests were recomputed independently from the JSON bodies, not
read back from the field they certify.

| requirement | observed |
|---|---|
| `numeric_rows_unchanged_from_parent` | **true** |
| six distinct donor identities | 6 |
| exactly 2 per corrected source | [2, 2, 2] |
| all-104 raw reaggregation claimed | **false** (scope preserved) |
| `source_invariant_violations` | **0** |
| all-member proof | 35 members, 2 changed, independently reloaded |
| donor order digest | `59867cb9246127bfb75483c75461118c23f607d2e76f4941d8407b7ecb8f8f2e` |
| donor source vector digest | `797afbff00c6d2e53907297916d4cbcd9d6d3cefb2256ef792be72f7c814328c` |
| canonical `src_of_cell` digest | `a315ac2ca62f2e1a8a0ddee665109345d15ab3f06bea5c0a086437ef872712e0` |
| **mandatory fold digest** | `7b472a0fd34dfc27360632f58bb9a4007f759320b6e251f5d5d9c444b2adf7e9` |

The fold digest is a real value, not the `... if False else None` placeholder F5
flagged.

### #62 binder regression — run separately, reported separately

```
$ preflight_full104_audit_b_n1_physical_v1_20260922.py  --heavy-artifact <ORIGINAL>
ValueError: source-name ordering differs from frozen HVS/NPH52/SEA_AD
exit 1
```

The original binder **still rejects the unchanged original**. Confirmed by
execution, and the V2 receipt no longer carries the unconditional
`pr62_still_rejects_parent` / `all_physical_files_reloaded_and_hashed_here`
assertions that F5 objected to — both fields are now **absent** rather than
asserted.

## PR #72 findings — status as observed here

| finding | status |
|---|---|
| F1 per-member independent comparison | repaired; V2 reloads both NPZs and recomputes all 35 member digests, dtype/shape, change flags and dispositions |
| F2 sampled donor provenance | repaired; `require_full_metadata_donor_identity` compares **every** cell, not a stride sample. Also: pass1 *is* frozen-bound via the split receipt (above) |
| F3 overstated control count | fair, and I accept it about my own PR #69 tests — several asserted local inconsistency rather than invoking the production gate, and test 2 contained a vacuous `or good[0] == 0` escape. PR #73 adds 401 lines of end-to-end fixture tests; at this head the focused suites are 48 passed / 0 skipped |
| F4 stale artifact on postwrite failure | repaired; the NPZ is written to an exclusive stage, the stage is reloaded and audited, and publication happens only after every gate passes |
| F5 conclusions written instead of observed | repaired; the two unconditional booleans are gone and the fold digest is real |
| F6 downstream consumer inventory | confirmed by PR #72's own static inventory; not re-derived here |

## Limitations

* This is metadata and artifact integrity only. It does not qualify any N1
  runtime, and the preflight terminal is review evidence, **not** execution
  authority.
* The six-donor scope is unchanged: six donors, two per source. Raw reaggregation
  for all 104 donors is still **not** proved.
* F6 is accepted from PR #72's static inventory rather than independently
  re-derived; it is not a proof about future adapters.

## Remaining blockers

1. Independent review of these V2 receipts.
2. PR #63 crash-safe integration — separate, unmerged, and gated on that review.
3. Rare-tail molecular execution remains barred pending reapproval against the
   new gateway source SHA.

```
AUDIT_B_N1=UNOPENED | MASKS=NONE | BURDEN=NOT_RUN | RARE_TAIL_MOLECULAR=UNOPENED | TD60=UNEXECUTED | PATHOLOGY_DEV_SEALED=UNOPENED | D_SHARED_G5=UNOPENED | TRAINING=OFF
```
