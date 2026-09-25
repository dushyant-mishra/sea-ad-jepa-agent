# Phase 1A — physical authentication of the frozen pass1 and calibration bundle

**Verdict: mixed. The frozen pass1 authenticates exactly. The calibration bundle
on this machine does not, so PR #132's donor-count bridge cannot lawfully run
here yet.** The bridge is correct to refuse; the defect is in the input, not the
code, and I did not change the expectation to make it pass.

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

A filesystem search for a copy at the recorded size and digest was launched; its
result is recorded separately. Until such a copy is found, Phase 1A's bridge
execution is **BLOCKED_BY_PHYSICAL_INPUT_MISMATCH**, distinct from an
authorization blocker.

## What this does and does not affect

**Does not affect:** the frozen pass1 itself is authentic, so anything keyed only
to `37f79e49…` is unaffected. PR #132's 51 synthetic tests remain synthetic-only
and are **not** relabelled as physical execution.

**Does affect:** the 104-donor ID and per-donor count equality check cannot be
performed, because the reader-fit membership and per-donor counts are read from
`splits/reader_donor_split.csv` *inside* that archive. A global total of
4,553,407 cells would not substitute for per-donor equality even if it matched —
reciprocal count swaps between two donors preserve the total exactly, which is
why the bridge checks identities and per-donor counts rather than the sum.

## Status

```
COMPLETED_AND_PHYSICALLY_EXECUTED : whole-file SHA-256 authentication of 4 candidate inputs
SYNTHETIC_TESTED_ONLY             : PR #132's 51 tests (unchanged, not promoted)
BLOCKED_BY_PHYSICAL_INPUT_MISMATCH: PR #132 donor-count bridge execution
NOT_EXECUTED                      : 104-donor ID and per-donor count equality
```

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
