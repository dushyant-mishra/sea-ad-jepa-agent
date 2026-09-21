# Superseded test: `test_teacher_student_v5_support_geometry_v1.py`

Date retired: 2026-09-20

## Identity of the retired artifact

| field | value |
|---|---|
| original path | `tests/test_teacher_student_v5_support_geometry_v1.py` |
| SHA-256 | `0c81f62ddabbccb8ef584936b8a2a5f46a882f720233bb41ea4b6e28acdecd64` |
| bytes | 2,844 |
| exact bytes preserved at | `source_snapshot/test_teacher_student_v5_support_geometry_v1.py` |
| superseded at commit | `1db33ff0faead3edbdcee6d1ac0fe4fd43b4381b` |
| that commit's subject | `reconcile: restore current V5 data-first tree onto consolidated main` |
| that commit's date | Tue Sep 8 16:06:16 2026 -0400 |
| active successor | `tests/test_teacher_student_v5_support_schedule_v1.py` |

The snapshot is a byte-for-byte copy; its SHA-256 equals the original's.

## Why it was retired rather than repaired

The test imports two APIs from `sea_ad_jepa.v5.support_geometry_v1`:

```python
max_fixed_visible_for_support
validate_fixed_visible_across_support
```

Both were **deliberately removed** by `1db33ff0`. They are not restored, and this
record exists so that decision stays legible rather than looking like an
accident.

Those two functions computed a *frozen feasible visible-gene budget* across the
operator support distribution — for example asserting that a measured support of
`[18_736, 30_294, 32_445, 34_405, 35_076]` admits at most `18_224` visible genes
given a 512-gene minimum hidden-target requirement, and that a proposed 17,186
visible genes leaves a minimum realized hidden support of 1,550.

**Current V5 numerical evidence scheduling is intentionally unfrozen.** The
project no longer commits to a fixed visible-gene budget derived at contract
time. Evidence dose, block geometry and schedule parameters are meant to be
derived from the real dataset geometry at the point of use and frozen with their
own justification, not inherited from a constant baked into a helper function.
Restoring those APIs would reintroduce exactly the frozen budget the reconcile
removed, and would make an unfrozen design look settled.

Because the removal was a scientific design decision and not a bug, the test is
retired. It is not skipped and not marked `xfail`: a skipped test advertises a
check that is not running, and an `xfail` implies the code is expected to be
fixed. Neither is true here.

## What the retired test asserted, and where each assertion now lives

| retired assertion | disposition |
|---|---|
| universe-relative visible fraction equalizes across supports | carried forward in the successor |
| within-measured visible fraction differs across supports | carried forward in the successor |
| measured fraction of universe is ordered by support size | **not carried forward** — depends on the removed return key `measured_fraction_of_universe`; its *absence* is now pinned instead |
| block count derives from hidden support (15 and 28 blocks) | carried forward in the successor |
| block sizes never exceed the per-block target | carried forward in the successor |
| block sizes sum exactly to the hidden count | **added to the successor** in this change |
| `balanced_block_sizes` has no implicit budget | carried forward in the successor |
| `fixed_visible_evidence` has no implicit visible budget | **added to the successor** in this change |
| visible budget exceeding measured support fails closed | carried forward in the successor |
| `max_fixed_visible_for_support` feasibility arithmetic | **not carried forward** — removed API |
| `validate_fixed_visible_across_support` joint fail-closed | **not carried forward** — removed API |

## A third piece of removed API surface

The retirement instruction named two removed functions. Carrying the regressions
forward surfaced a third: `fixed_visible_evidence` no longer returns the key
`measured_fraction_of_universe`. It was added in `c6af0c58` and removed by the
same commit `1db33ff0`. It was **not** restored.

So the stale test depended on three removed pieces of API surface, not two. Two
regressions that did not depend on any of them were missing from the successor
and have been added. The assertion that depended on the removed key is not
reconstructed; instead the successor now pins the key's **absence**, so a silent
reintroduction of a frozen universe-fraction notion would fail the suite.

## Effect on collection

Before this change, `tests/test_teacher_student_v5_support_geometry_v1.py` was
one of five files that could not be collected in the FULL104 regression run,
failing with:

```
ImportError: cannot import name 'max_fixed_visible_for_support'
from 'sea_ad_jepa.v5.support_geometry_v1'
```

It had been uncollectable since `1db33ff0` on 2026-09-08 — silently, because the
file was ignored rather than investigated. After this change that collection
error is gone.
