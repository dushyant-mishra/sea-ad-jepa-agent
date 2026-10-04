# The cisTarget runtime projection was built on the cheapest corner of the motif collection

**Bottom line: this is bad news for the schedule and good news for the method.** The
~33.5 h estimate for the full 10,249-motif cisTarget build is wrong by roughly a factor
of two, and the reason is not shard size, not worker count and not machine contention.
Every benchmark this project has run used a **prefix** of an alphabetically sorted motif
collection, and that prefix is made of unusually short motifs.

Nothing scientific is invalidated. No network exists, no biological claim depends on
this, and the databases produced are correct. What changes is how long the build takes
and what a receipt may assert about it.

---

## What was measured

A controlled comparison. Two runs, 128 motifs each, **identical** region FASTA
(`b20e82c4…`), identical `cbust`, identical bench runner (digest `aada3842…` — the same
script that produced the original 128-motif point), identical 8 workers, identical
pinned seed 20261001, identical thread pinning, both on a machine with every other lane
held. **The only thing that differs is which 128 motifs are in the batch**, and the two
sets share zero members.

| | motifs 1–128 (the prefix every benchmark used) | 128 drawn at random from the 10,249, seed 20261001 |
|---|---:|---:|
| wall clock | 1,694 s | 2,658 s |
| Cluster-Buster scoring | 1,479.3 s | 2,361.2 s |
| **seconds per motif** | **11.56** | **18.45** |
| non-scoring segment O(n) | 214.7 s | 296.8 s |
| mean PWM positions | 9.19 | 17.30 |
| max PWM positions | 17 | 167 |

**A random sample costs 1.60× as much per motif as the prefix.** Cluster-Buster scans a
sequence against a position-weight matrix, so cost rises with matrix length, and the
prefix is short: mean 9.19 positions against 17.30 for the random sample.

## Why the prefix is unrepresentative

The collection is sorted alphabetically. Its first entries are `bergman__*` — a
*Drosophila* set with very short matrices — followed by early `cisbp__M0…` entries.

| slice | n | mean PWM positions | max |
|---|---:|---:|---:|
| motifs 1–16 (`bench16`) | 16 | 8.31 | 12 |
| motifs 1–128 (`bench128`) | 128 | 9.19 | 17 |
| motifs 129–512 | 384 | 9.20 | 15 |
| motifs 1–512 (the pilot) | 512 | 9.20 | 17 |
| random 128 | 128 | 17.30 | 167 |
| **whole collection, 1–10,249** | **10,249** | **21.57** | **1,480** |

The whole collection averages **21.57** positions per motif and runs to **1,480**. Every
benchmark point this project has ever taken sits at about **9**. A prefix of a sorted
list is not a random sample, and nobody checked.

## What the build actually costs

Two estimates, and the difference between them is honest uncertainty rather than a
choice.

**A measured floor.** The random-128 run's own rate, applied to the whole collection:
10,249 × 18.45 s = 189,100 s ≈ **52.5 h** of scoring. This is a floor, not a central
estimate, because the random 128 sample still averages 17.30 PWM positions against the
collection's 21.57.

**A two-point interpolation in PWM length.** Fitting a straight line through the only two
matched points available — cost per motif 11.56 s at 9.19 positions, 18.45 s at 17.30 —
gives a fixed 3.75 s per motif plus 0.850 s per PWM position. Applied to the
collection's 221,071 total positions: **≈ 62.9 h** of scoring.

Add the per-shard non-scoring segment — 21 shards × ~300 s ≈ 1.8 h — and the build is
somewhere around **54–65 h**, against the 33.5 h in the superseded receipt.

**The interpolation is labelled as such and should not be read as precise.** It has two
points. The PWM distribution is heavy-tailed, with a maximum of 1,480 positions against a
maximum of 167 in the largest batch measured, so the longest motifs in the collection sit
far outside the range any measurement covers. A representative measurement at production
scale would pin this down; none has been made, and no number here is presented as one.

## What this does NOT mean

- **It is not a shard-size effect.** Per-motif scoring cost is paid for every motif
  however the motifs are grouped. No shard size changes it, and shrinking shards would
  add serial segments while leaving the dominant term untouched.
- **It is not contention.** The random-128 run was executed with every other lane held
  and `docker ps` showing only its own container.
- **It is not a reason to shrink the motif collection.** 110 of 1,605 TFs have zero
  directly annotated motifs and the median direct supply is 6; cutting the collection
  would gut the annotation-supply control. The build is more expensive than believed,
  not optional.
- **It changes no output.** Scores and rankings are unaffected; only the clock is.

## Consequences that must be carried

1. **The 33.5 h figure may not be cited again without the measurement beside it.** A
   projection a direct measurement has contradicted should not survive in a receipt as
   though it were current.
2. **Future cisTarget benchmarks must use a random sample, not `head -n`.** The frozen
   random-128 list (`random128.motifs.lst`, sha256 `05a9f15e…`, seed 20261001) is the
   first such artifact in this project.
3. **Shard crash exposure is larger than believed.** At the representative rate a
   512-motif shard costs roughly 2.6–3.1 h rather than 1.6 h, so a lost shard forfeits
   proportionally more. This is an argument for restartability working correctly, which
   is tested separately, not for a different shard size.
4. **Route B's build sits on the same curve.** Its region universe does not exist yet, so
   its cost is `UNMEASURED`; it will scale with its own region count against the same
   per-motif rate.

## Provenance

- `RANDOM128_t8` bench receipt: `C:/jepa_scratch/v74_laneE/random128/RANDOM128_t8.bench.json`,
  status `PASS__RUN_COMPLETE`, 2,658 s, motif list sha256 `05a9f15e2f255d750b0971fdd7c896c4d306b3a8b1654190fb99d410c3f5d0fe`.
- `SHARDSIZE_128_t8` bench receipt (the prefix point, unchanged and not re-run):
  `D:/jepa_v5_outputs_20260925/v69_scenicplus/routeA/shardsize/SHARDSIZE_128_t8/SHARDSIZE_128_t8.bench.json`.
- PWM position counts are read from the `.cb` files of the authenticated motif collection
  (`v10nr_clust_public`, sha256 `70dab427…`), counting non-header lines per file.
