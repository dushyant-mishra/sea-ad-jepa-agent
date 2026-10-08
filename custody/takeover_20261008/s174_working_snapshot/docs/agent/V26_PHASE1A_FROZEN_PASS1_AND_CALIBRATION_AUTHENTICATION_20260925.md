# Phase 1A — physical authentication and execution of the pass1 donor-count bridge

**Verdict: good news. Both inputs authenticate and the bridge ran, confirming
exact per-donor count equality across all 104 reader_fit donors.** Getting there
required finding the real calibration bundle, because the file sitting under that
name was a different artifact — and the right move was to find the authentic
bytes rather than relax the digest.

## What was measured

Whole-file SHA-256 computed over every candidate before any parsing.

| file | bytes | sha256 | verdict |
|---|---|---|---|
| `full104_pass1_v2_selection_row_keyed.npz` | 18,029,576 | `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1` | **AUTHENTICATED** |
| `full104_pass1_cleanhead.npz` | 18,029,576 | `37f79e49f113…90ba1` | **AUTHENTICATED** — byte-identical second copy |
| `pass1_SEPT17_INVALID_FOR_CURRENT_ROLE.npz` | 40,320,179 | `0e99d12b9b74e3cc6ae95ab436effa84c9e71c461496258653022ae56d396811` | correctly **does not** match; quarantined file stays quarantined |
| `exports/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` | **1,093,202,356** | `faa52d8e3a68839356c63b7be7f4df6318f7e0ea12a05814cba6dd26ae6281b2` | **MISMATCH** |

The two pass1 copies live at
`D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/` — one at the top level,
one under `cleanhead_a1de0340/`. That they are byte-identical is a useful
redundancy, not two independent confirmations.

## The calibration bundle mismatch

`JEPA_POPULATION_ACCESS_REGISTRY_V1_20260907.json` declares
`calibration_bundle_transport_sha256 = 07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`,
and the V26 evidence ledger records the bundle as **410,278,055 bytes**. The
file on disk under that name is **1,093,202,356 bytes** with a different digest —
not a corrupted copy of the expected bundle but a **different artifact**, 2.7x
the recorded size.

`src/sea_ad_jepa/v5/reader_fit_population_preflight_v1.py` hard-codes
`ARCHIVE_SHA256 = "07748d5b…"`, and
`frozen_pass1_reader_fit_count_bridge_v1.py` requires `--calibration-zip`
alongside `--pass1`. The bridge is therefore **fail-closed against this input**,
which is the correct behaviour.

**I did not relax the expectation.** Changing `ARCHIVE_SHA256` to the observed
digest would convert a genuine provenance failure into a green check, which is
precisely the failure mode the digest exists to prevent. The name of a file does
not establish its identity.

## The authentic bundle was recovered, not worked around

A filesystem search found a **seven-part split archive** in `C:/Users/dushy/Downloads/`:
`FOUNDATION_CALIBRATION_BUNDLE_20260824.zip.part001` … `part007`, six parts of
67,108,864 bytes and a final part of 7,624,871, totalling **exactly
410,278,055 bytes**. Concatenated in order to a new path — the 1.09 GB file was
left untouched — the result hashes to

```
07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444
```

which is the declared `calibration_bundle_transport_sha256` exactly. The bundle
is **AUTHENTICATED**.

Independently, `splits/reader_donor_split.csv` was found already extracted in two
places, and both copies hash to `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`,
matching the registry's declared digest and the preflight's `READER_SPLIT_SHA256`.

## Bridge execution

Run as a module from PR #132 head `1e9080caeeea`, clean worktree:

```
--pass1           full104_pass1_v2_selection_row_keyed.npz   37f79e49…90ba1
--calibration-zip reassembled bundle                          07748d5b…17444
exit 0    status BYTE_BOUND_PASS1_AND_METADATA_COUNTS_ONLY
```

| field | value |
|---|---|
| **per_donor_exact_count_match** | **True** |
| donor_count | **104** |
| cell_count | **4,553,407** |
| reader_fit_membership_sha256 | `9332e77c…d8e977` (matches `FIT_MEMBERSHIP_SHA256`) |
| reader_fit_donor_counts_sha256 | `b2da4aa9…4de875` (matches `FIT_COUNTS_SHA256`) |
| raw_level4_blocks_opened | **0** |
| protected_outcomes_opened | False |
| training_authorized | False |

Per-donor equality was checked donor-by-donor against the authenticated
membership, not by comparing the 4,553,407 total — a reciprocal count swap
between two donors preserves the total exactly, which is why the sum is not a
substitute.

## What the gate itself declares it does NOT do

The receipt is explicit about its own limits, and these are carried forward
rather than glossed:

* `balanced_reciprocal_cell_swaps = NOT_DETECTABLE_BY_HISTOGRAM` — a swap
  between two donors holding *identical* counts is invisible to a per-donor count
  comparison. Count equality is necessary, not sufficient, for identity.
* `pass1_to_raw_level4_binding = NOT_REVALIDATED_BY_THIS_GATE`
* `per_cell_donor_lineage_validation = NOT_PERFORMED_BY_THIS_GATE`
* `source_library_validation = NOT_PERFORMED`, `proposal_q_validation = NOT_PERFORMED`

This is a metadata-level count bridge, not a raw-count integrity proof. It opened
**zero** Level-4 blocks. PR #120's all-104 raw-count verification remains a
separate task under its own authority.

PR #132's 51 synthetic tests remain **SYNTHETIC_TESTED_ONLY** and are not
relabelled as physical execution; this receipt is the physical execution.

## Status

```
COMPLETED_AND_PHYSICALLY_EXECUTED : SHA-256 authentication of 4 candidates + bundle reassembly
                                    PR #132 donor-count bridge, 104/104 per-donor exact match
SYNTHETIC_TESTED_ONLY             : PR #132's 51 tests (unchanged, not promoted)
NOT_EXECUTED                      : per-cell donor lineage, pass1-to-raw-Level4 binding,
                                    source-library and proposal-q validation
```

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
