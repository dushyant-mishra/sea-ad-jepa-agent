# V74 Lane E — self-audit lane (continues the V69 numbering at S29)

Defects in **my own** output, including ones no external reviewer raised. Numbering
continues the V69 SCENIC+ lane, which ended at S28, so items stay traceable across
lanes. An item this lane cannot close says so rather than being marked resolved.

Lane: `claude/v74-blacklist-and-512pilot-20261002`
Worktree: `D:/jepa_wt_v74_laneE_20261002`
Outputs: `D:/jepa_v5_outputs_20260925/v74_laneE`
Scratch: `C:/jepa_scratch/v74_laneE`

---

## S29 — The 11-test merge suite SKIPS silently on the host; its claimed evidence could not be reproduced by the obvious command (CAUGHT BEFORE CITING IT)

`V69_CISTARGET_SPEED_BENCHMARK_RECEIPT_V1.json` states of the merge validator:
`"tests": "11, all driven to their failure state"`. Running the obvious command on the
host gives **`1 skipped`**, not 11 passed — `pytest.importorskip("pyarrow")` fires
because pyarrow is not in the host Python.

I was about to cite "11 tests pass" as inherited evidence. Instead I ran it where it can
actually run. Inside the SCENIC+ container, with pytest installed to a scratch
`--target` directory so the image is untouched: **11 passed**.

So the claim was true. The defect is that nothing in the repository records *how* to
reproduce it, and the default command produces a green-looking `1 skipped` that a
hurried reader scores as a pass. A skip and a pass must not be visually
interchangeable.

**Fix:** the exact container command is now recorded (below). **Status: CLOSED for the
reproduction gap; the underlying suite was never broken.**

```
docker run --rm -e PYTHONPATH=/scratch/pylibs \
  -v C:/jepa_scratch/v74_laneE:/scratch -v <worktree>:/wt:ro -w /wt \
  scenicplus:1.0a2-container.1 \
  micromamba run -n base python -m pytest tests/test_v69_shard_merge_validation_v1.py -q
```

## S30 — My 512-motif pilot was NOT run on an idle machine, unlike the 16- and 128-motif points it will be read against (DISCLOSED, PARTIALLY OPEN)

The worker-scaling table was deliberately held back until the machine was idle, and the
128-motif point inherited that condition. My pilot ran with four sibling V74 lanes
executing concurrently; the sampler recorded host CPU load between 83 % and 100 %.

Dropping my point into the same table as a third row would have manufactured a
like-for-like curve out of three different machine states — exactly the artifact the
V69 lane went to trouble to avoid.

**What survives and what does not.** Contention can only make a run *slower*. The
shard-sizing question is "does the per-shard non-scoring overhead explode at 512?", and
a contended measurement gives a valid **upper bound** on the uncontended value. An upper
bound answers that question. It does not support a per-motif scoring cost or a
like-for-like speedup claim, and none is made. Output digests, peak scratch bytes,
motif-axis verification, restart behaviour and plan tiling are unaffected by contention
entirely.

**Status: OPEN and not closable by this lane.** A like-for-like 512-motif point needs an
idle machine, which is not available while the other lanes run. Recorded in the
successor receipt under `CONTENTION_DISCLOSURE` rather than smoothed over.

## S31 — My own resource sampler perturbs what it measures, and its stated cadence was wrong (CAUGHT, CORRECTED BEFORE THE RECEIPT)

Two separate defects in the instrument I wrote:

1. **It costs what it measures.** Each sample spawns two `docker stats` calls and a
   PowerShell CIM query, on the very machine whose CPU contention I am recording. The
   sampler is a (small) contributor to the contention in S30.
2. **`sleep 15` is not a 15-second cadence.** The probes themselves take about nine
   seconds, so observed inter-sample gaps are ~24 s. Writing "sampled every 15 s" into
   the receipt would have put an **estimated** number into a provenance artifact. The
   receipt records the sample count and the measured values; it does not assert a
   cadence it did not measure.

**Status: CLOSED.** Caught before anything was written to a receipt.

## S32 — I chose the overlap rule; a wrong choice would have reconfounded the whole route comparison (CAUGHT, CLOSED BY MEASUREMENT)

The owner's decision was "blacklist ON". It did not specify *how* a region that
partially overlaps an exclusion interval is handled. I chose whole-region removal. Had
pycisTopic instead trimmed coordinates, Route A (excluded by my rule) and Route B
(excluded by pycisTopic inside the peak caller) would have been filtered by **different
rules**, and Amendment 1's guarantee that the region universe is the single varying
factor would have been destroyed — silently, since both routes would still report "the
blacklist was applied".

I verified rather than assumed: pycisTopic calls
`regions.overlap(blacklist, invert=True)` at `iterative_peak_calling.py:145` and
`cistopic_class.py:579`, which drops whole intervals. I then recomputed the attrition
with that identical pyranges call; both implementations return 263 regions and
211,953 bp.

**Status: CLOSED.** The rules coincide, and the agreement is between two
implementations rather than a producer and itself.

## S33 — The pilot's region FASTA is the PRE-blacklist one; the production FASTA must be rebuilt (OPEN, HANDED OFF)

The 512-motif pilot scored against
`ROUTE_A_SUBMITTED_PEAKS_regions_padded_bg.fa` (sha256 `b20e82c4…`), which was built
from all **150,561** regions. Under Amendment 3 the Route-A scoring universe is
**150,298**.

This does not invalidate the pilot — 0.17 % more sequence is far inside the noise of a
contended timing — but it does mean the production build must **not** reuse that FASTA.
A build that silently scored the pre-blacklist FASTA would produce a database whose
region axis contradicts the frozen policy, and nothing would crash.

**Status: OPEN.** Requires rebuilding the padded-background FASTA from
`ROUTE_A_REGIONS_RETAINED_AFTER_BLACKLIST.bed` and re-pinning its digest before the
full build. Named here so it cannot be forgotten.

## S34 — The Route-B producer's `--blacklist` still defaults to None, so the frozen policy is specified but not enforced (OPEN, OTHER LANE'S FILE)

`scripts/v69/routeb_call_peaks_and_consensus_v1.py` accepts `--blacklist` with
`default=None` and records `"applied": blacklist is not None`. A Route-B run that simply
omits the flag succeeds and reports `applied: false`.

That is the exact silent omission the owner's decision was taken to prevent. I did not
fix it: the file belongs to the lane doing Route-B custody repair, and editing another
lane's producer while it runs is the collision this project has already paid for once.

**Status: OPEN, handed off.** Until `--blacklist` is required and digest-checked,
Amendment 3 is **specified but not in force** on the Route-B path, and the amendment
says so in its own text rather than claiming coverage it does not have.

## S35 — I nearly reported "no shard size beyond 128 was measured" from the benchmark receipt alone (CAUGHT)

The predecessor receipt lists, under `NOT_MEASURED_AND_THEREFORE_NOT_RECOMMENDED`, the
item "Any shard size beyond 128 motifs". Its sibling key `status` says `SUPERSEDED`. Two
statements, same block, opposite meanings.

Rather than quote either, I listed the directory. `routeA/shardsize/SHARDSIZE_128_t8/`
exists with a complete `PASS__RUN_COMPLETE` bench receipt dated after the scaling table.
The project rule is that an absence claim requires an exhaustive listing, never a
keyword-filtered read — and here a keyword-filtered read of a self-contradicting file
would have produced a wrong status in both directions depending on which key I hit
first.

**Status: CLOSED**, and it is the reason Task 3 exists: a receipt with two statuses
makes every downstream reader's answer depend on reading order.
