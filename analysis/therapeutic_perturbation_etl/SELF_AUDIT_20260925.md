# Self-audit — repair lane and prior work, 2026-09-25

Findings this lane produced against **its own** work, by testing rather than
recollection. Two were already disclosed; five are new. None was reported by the
external auditor.

```
S1  frozen manifest is not an independent third source         NEW
S2  latent R/Python sort-collation hazard                      NEW, not a current defect
S3  P0-5 assertion binding is a PARTIAL fix                    NEW
S4  the "independent" reproduction is not independently AUTHORED  NEW (strengthens a known limit)
S5  WP3 outputs manifest still verifies                        no defect
S6  the 33-target V3 comparison rests on an unverified upstream NEW
S7  adversarial suites still absent for 4 producers            previously disclosed
```

---

## S1 — The frozen 16-asset manifest pins against my own measurement

`FROZEN_EXPECTED_16_ASSET_MANIFEST_V1.json` was **generated from my own v1
inventory run**. Measured:

```
frozen digests identical to my v1 inventory output : 16/16
frozen digests identical to ACQUISITION sidecars   : 16/16
```

The second line is what rescues it. The manifest's authority does not come from
being independent of me — it is not — it comes from agreeing with the
acquisition-time sidecars, which were written before any of this work. If v1 had
mis-hashed an asset, the frozen manifest would have enshrined that error, and
only the sidecar cross-check would have caught it.

**Correct reading:** the manifest is a *convenience pin over a three-way
agreement* (bytes on disk, acquisition sidecar, frozen record), not an
independent authority. The audit's phrase "independently pinned digests" is
satisfied only in that weaker sense.

## S2 — Latent sort-collation hazard between the two implementations

The R producer orders targets with `sort()`, which uses locale collation. The
Python reproducer uses `sorted()`, which uses codepoint order. These are not the
same function.

Measured: 206 targets, 0 non-ASCII, 0 non-alphanumeric characters — so the two
orderings coincide, and `target_order_matches` is genuinely `True`.

**This is a latent hazard, not a current defect.** A gene symbol containing an
underscore, hyphen or non-ASCII character could order differently between the
two, and the comparison would then report a spurious disagreement — or, worse,
compare mismatched columns if a future version indexed positionally instead of
by name. Recorded so it is not rediscovered as a mystery.

## S3 — P0-5 is a partial fix, not a complete one

The audit asked for a "source-bound, reviewable metadata contract (separate
computed columns from literature/curator assertions)".

What I delivered: the **output** is separated into two files, and each assertion
carries a `source` string. What I did **not** deliver: the assertions still live
hard-coded in `build_cross_study_comparability_matrix_v2.py`, not in a reviewable
digested contract file that can be signed off independently of the code.

**Status: PARTIAL.** Outcome exposure *is* properly externalised to the registry
— that part is complete, and it was the actual defect. The descriptive metadata
binding is not.

## S4 — The independent reproduction is not independently *authored*

This strengthens a limitation I disclosed earlier, and it is the most important
item here.

I wrote `build_gse301119_donor_aware_transcriptome_v2.R`, I wrote
`independent_reproduce_gse301119_v1.py`, **and** I wrote the algorithm
specification both follow (qualification contract §3).

**What the agreement does establish.** Two implementations, in different
languages, with different control structures — a per-target loop over donors in
R against vectorised group indexing in Python — compute the same numbers from
the same bytes to `1.776e-15` across ~22.7M cells, with matching target order,
feature order and support masks. That rules out transcription slips, indexing
errors, array-layout errors, and one-sided normalisation bugs. The comparator
was also shown to detect a sign flip before being trusted.

**What it does not establish.** That the *specified estimand* is correct. A
wrong specification — aggregating raw counts before CPM rather than averaging
per-guide ratios, say — would be reproduced faithfully by both. Same author
means correlated blind spots.

`INDEPENDENT_REPRODUCED` in the receipt should be read as
**IMPLEMENTATION_REPRODUCED**. A genuinely independent check requires a
different agent or person deriving the estimand afresh.

## S5 — WP3 outputs manifest still verifies

Re-ran after this session's work: **PASS, 14 files, 56,949,910 bytes**, all
sizes and digests match. No drift. Recorded because a stale manifest was exactly
the P0-2 failure mode, and it would be inconsistent to assume this one aged well
without checking.

## S6 — The 33-target comparison rests on an upstream I never recomputed

`gse178317_target_engagement_v2.csv` (39 rows) is produced by
`build_gse178317_intervention_effects_v2.py`, which came from PR #102. I
**executed** it; I did not author it and did not independently recompute its
output.

Every figure in the support-qualified V3 comparison — 33/33 direction agreement,
Spearman 0.7473, Pearson 0.6398 — therefore inherits an unverified upstream.
This is the same class of gap the audit raised as P1-6 for the bulk producers,
and it applies equally here. It does not make the numbers wrong; it means they
are `CODE_TEST_PASS` on my side and unverified on the producer's side.

## S7 — Adversarial suites still absent for four producers

Previously disclosed and still true. Covered: the inventory (14 adversaries, 0
skips) and the outputs manifest (4 tamper modes). **Not covered:** the
donor-aware R producer, the bulk V2 producers, the comparability matrix, and the
new GSE311359 ID-keyed producer.

The GSE311359 producer does carry an internal assertion that no unit may report
cells while holding zero counts — the V1 phantom signature — which fails closed
if the defect recurs. That is a guard, not a test suite.

---

## Net effect on claimed status

| claim | after self-audit |
|---|---|
| 16 assets authentic | stands; authority is a three-way agreement, not an independent pin |
| GSE301119 independently reproduced | downgrade to **IMPLEMENTATION_REPRODUCED** |
| P0-5 fixed | exposure fixed; assertion binding **PARTIAL** |
| 33-target comparison | stands as computed; upstream unverified |
| P0-1 | unchanged — still `CODE_TEST_PASS_ONLY`, inventory scope |

Nothing found here invalidates a measured number. Every finding concerns the
**strength of the evidence** behind a number, which is the part most easily
overstated.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
