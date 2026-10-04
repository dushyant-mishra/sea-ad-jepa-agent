# Shard-size decision rule — frozen BEFORE the 512-motif pilot finishes

**Written and committed while the pilot is still running.** The scoring log shows fewer
than 100 of 512 motifs done and no non-scoring segment exists yet to look at. The point
is to fix what counts as a pass before the number arrives, so that the number cannot
choose its own threshold.

Lane: `claude/v74-blacklist-and-512pilot-20261002`.

---

## What is being decided

How many motifs go in one shard of the ~10,249-motif cisTarget build. 512 is currently
an **extrapolation** — the largest directly measured workload is 128 motifs. The
instruction under which this lane works is explicit that 512 must not be preserved merely
because it is already written in a recommendation.

## The quantity that decides it

`O(n)` — the **non-scoring seconds** of a shard of `n` motifs: wall clock minus the
tool's own reported Cluster-Buster scoring time. This is the segment paid **once per
shard**, so it is what multiplies when shards get smaller.

Measured so far, both on a verified idle machine:

| n motifs | wall s | cbust s | **O(n)** s |
|---:|---:|---:|---:|
| 16 | 486 | 222.4 | **263.6** |
| 128 | 1694 | 1479.3 | **214.7** |

Note that `O(n)` **fell** between 16 and 128. That is why the earlier fitted overhead
model produced a negative per-motif coefficient and was discarded as falsified (S28).
This rule therefore does not fit a model; it reads the measured value at 512 directly.

## The contention caveat, stated before the result

The pilot runs with four sibling lanes active. Contention can only make a run **slower**,
so the measured `O(512)` is an **upper bound** on its idle-machine value. Every branch
below is written so that a *low* measurement is decisive and a *high* one is not — which
is the correct asymmetry, because only the low direction is protected by the bound.

## Accept band — where the threshold comes from

The predecessor receipt accepted 512 at an estimated 4.6 % of total runtime and
**rejected** 256 at 8.6 %. The accept band already in force is therefore "overhead up to
roughly 7 % of the build". Against a ~33.5 h build over 21 shards that is
`0.07 x 33.5 x 3600 / 21 = 402 s` per shard.

**`O_MAX = 400 s`.** `CONVENTION`, but derived from a precedent this project already
applied, not invented here. `O_STOP = 800 s` is twice that and marks the point at which a
per-motif write cost clearly dominates.

## The rule

Evaluate in order. The first branch that matches decides.

**R0 — correctness gate, overrides everything.**
If `scripts/v74/laneE_shard_size_invariance_v1.py` reports anything other than
`PASS__OUTPUTS_ARE_INVARIANT_TO_SHARD_SIZE` — that is, if the first 128 motifs of the
512-motif pilot disagree with the standalone 128-motif run in scores **or** rankings —
then **STOP**. No shard size is recommended, at any runtime, until that is understood. A
shard-size-dependent database is not a database.
If the positive control does not fire, the result is `VOID`, not a pass.

**R1 — resource gate.**
If the pilot's peak container memory exceeds 8 GiB, or one shard's output exceeds 8 GB,
then shard size is capped by resources rather than by time: choose the largest size whose
projected per-shard output keeps three shards in flight plus the merged database inside
the 120–130 GB scratch budget, and say so.

**R2 — `O(512) <= 400 s` → KEEP 512.**
Overhead has not exploded. 21 shards cost at most 2.33 h, inside the accept band. The
upper-bound argument makes this branch safe under contention.

**R3 — `400 s < O(512) <= 800 s` → overhead grows materially with shard size.**
Larger shards then reduce *total* overhead while increasing crash loss. Report the
measured `O(512)`, compute `21 x O(512)` and `11 x O(1024)` by linear interpolation
through the three measured points, and recommend the size minimising
`total_overhead + 0.5 x one_shard_runtime` (the expected loss from a single crash
uniformly distributed within a shard). State explicitly that the 1024 point is
interpolated, not measured.

**R4 — `O(512) > 800 s` → per-motif write cost dominates.**
Recommend the largest size whose interpolated `O(n)` stays at or below `O_MAX`, and
require that size to be **measured** before the production build starts. Do not ship an
extrapolation to fix an extrapolation.

**R5 — a re-measurement trigger, not a branch.**
If the measured `O(512)` exceeds `O_MAX` *and* the sampled host CPU load averaged above
90 %, the result is consistent with either a real overhead growth or the contention. In
that case the recommendation is whatever R3/R4 give **plus** an explicit instruction to
re-measure on an idle machine before production. Contention may not be used to argue a
high number away.

## What this rule may not do

- It may not be widened after the measurement is seen.
- It may not be satisfied by re-running the pilot until a run lands in the accept band.
  One pilot, one reading.
- It may not substitute a projected `O(512)` for the measured one. If the scoring-time
  line is absent from the log, `O(512)` is `UNMEASURED` and the branch is R4 by default.
