# V69 SCENIC+ external regulatory architecture — self-audit lane

Defects in **my own** output on the V69 lane, including ones no external reviewer
raised. Numbered S1, S2, … and carried across cycles so items stay traceable.
An item that my own lane cannot close says so rather than being marked resolved.

Lane: `claude/v69-scenicplus-external-network-20261001`
Worktree: `D:/jepa_wt_v69_scenicplus_20261001`
Outputs: `D:/jepa_v5_outputs_20260925/v69_scenicplus`

---

## S1 — Motif annotation header parsed as data (CAUGHT BEFORE DAMAGE)

**Status:** CLOSED.
**Commit of fix:** see `scripts/v69/build_tf_annotation_supply_table_v1.py`.

**Defect.** The cisTarget motif-to-TF annotation table
(`motifs-v10nr_clust-nr.hgnc-m0.001-o0.0.tbl`) writes its header as a `#`-prefixed
comment line, so pandas reads the first column as `#motif_id`, not `motif_id`. My
first version of the supply producer required `motif_id` and so refused to run.

**Was it caught before it could do damage?** Yes — before any supply number was
produced, and therefore before control C1 could have been computed on a wrong
denominator. The producer's own required-column gate is what caught it; it
returned `FAIL__ANNOTATION_TABLE_COLUMNS_ABSENT` and named the columns.

**The fix, and what it deliberately is not.** I stripped the `#` marker from
column names. I did **not** relax the required-column check, and I did not fall
back to positional column access or to `skiprows=1` (which would have discarded
every column name). Four tests pin this distinction:

- `test_header_marker_is_parsed_not_ignored` — the `#`-prefixed and plain headers
  must yield identical digests.
- `test_genuinely_missing_column_still_fails_closed` — dropping a real column still
  raises, and names it.
- `test_hash_prefix_does_not_smuggle_in_a_wrong_column` — stripping `#` must not let
  `gene_name_typo` satisfy `gene_name`.
- `test_unstratifiable_supply_fails_closed` — if every TF has identical supply, the
  control has no stratification to offer and the run stops.

**Why this mattered more than a parsing nit.** Control C1 exists to stop a TF being
called "strong" merely because more motifs are annotated to it. Its denominator is
this table. A silently mis-parsed denominator would not have crashed anything
downstream — it would have produced a *plausible-looking* supply table and a
control that passed for the wrong reason.

---

## S2 — I froze a route comparison that could not isolate what it claimed (CAUGHT BEFORE DAMAGE)

**Status:** CLOSED by amendment.
**Artifacts:** `results/v64/V69_GSE214979_ROUTE_AB_PROSPECTIVE_FREEZE_V1.json`
(commit `500a8cfdba63a3f26193f3fb165aeb05f97aec34`) and
`..._AMENDMENT_1.json` (commit `0358639e644f04cb2b2b801d84089f5c02642770`).

**Defect.** My own prospective freeze had Route A scored against the generic
SCREEN-region cisTarget database and Route B against a custom database built over
its own consensus regions. Under that design, any Route-A/Route-B disagreement
would confound **two** causes — a different region universe *and* a different
motif-scoring database — so the comparison could not isolate region-definition
sensitivity, which is the only question Route B exists to answer. I had even
written the asymmetry into the freeze as a "known limitation", which is the wrong
response to a defect that was still fixable.

**Was it caught before it could do damage?** Yes. Found by re-reading my own freeze
against mandate item 7 before executing it, with zero eRegulons, zero route
statistics, zero control statistics and zero Stage-4 artifacts in existence. The
amendment records that exposure state explicitly, so a later reader can verify the
change could not have been outcome-driven.

**The fix.** Build a custom cisTarget database for **both** routes over each route's
own regions, with identical motif collection, identical cbust binary, identical
hg38 FASTA and identical parameters, leaving the region universe as the single
varying factor. Recorded as a numbered amendment quoting the original text verbatim,
not as a silent rewrite of the frozen file. Cost accepted: Route A is no longer
"fast" in wall-clock terms.

---

## S3 — The parallel lane's acquisition producer records Route B as optional (NOT MY DEFECT; RAISED)

**Status:** OPEN — not closable by my lane; it belongs to the other branch's owner.

`scripts/v64/acquire_gse214979_scenicplus_v1.py` on
`chatgpt/v64-privileged-information-recoverability-20260930` (commit
`84e10964b0a47d55a33170b1853905b77115d56c`) writes into its receipt:

> `"downloaded": false`, reason: "first-pass SCENIC+ route uses submitted filtered
> gene+peak matrix; fragment-level consensus-peak recaller remains an optional
> sensitivity route"

The owner mandate supersedes this: Route B is **required**, not optional. My
freeze adopts the mandate and says so by name. I am not editing the other branch.
Flagged here so the contradiction is visible rather than silently diverging.

---

## S4 — Route A and Route B share the same nuclei, so the comparison is narrower than "robustness" (DISCLOSED, NOT FIXABLE)

**Status:** OPEN by construction — my lane cannot close this, and should not pretend to.

Microglial identity is taken from the published multiome annotation for **both**
routes, because it cannot be re-derived from ATAC alone without circularity. So the
Route-A/Route-B comparison varies the region universe and holds the cell set fixed.
It therefore tests **region-definition sensitivity only** and must never be reported
as general robustness of the network.

This is written into `SECTION_0_SCOPE_AND_HONEST_LIMITATION` of the freeze rather
than left for a reader to infer. I am recording it here too because the natural
failure mode is for a later summary to compress "Route A and Route B agree" into
"the network is robust", which would be a materially stronger claim than the
evidence supports.

---

## S5 — The substrate is small, and the headline cohort size hides it (DISCLOSED)

**Status:** OPEN — a property of the data, not a defect I can fix; recorded so it is
not lost.

GSE214979 is a 15-donor, 105,332-nucleus multiome cohort. The **microglial** substrate
is far smaller: 3,179 nuclei across 15 donors, and 2,534 across 12 donors in the
default development population after the conservative donor exclusion. Donors are the
replication unit; the 2,534 nuclei improve per-donor measurement precision and do not
raise biological n above 12.

A prospective insufficiency rule is frozen in advance: fewer than 8 QC-passing donors
after Route-B ATAC QC means no program may be called donor-stable at all. That number
is labelled a CONVENTION in the freeze, not a calibrated operating point.

---

## What was examined this cycle and produced no finding

So that "nothing found" and "did not look" stay distinguishable:

- The acquisition receipts for all five acquired objects were checked against the
  server-declared `Content-Length`; all five match exactly and carry a computed
  SHA-256. The fragments file is still in flight and is deliberately **not**
  claimed as authenticated.
- The cohort freeze was checked for pathology leakage by a positive control that
  flips every pathology value in the frame and confirms both population digests are
  unchanged. No leak found.
- The Route-A substrate extraction was checked for the specific failure of
  returning the right *number* of cells but the wrong *cells*; a test compares the
  extracted columns against the full matrix by barcode. No defect found.
- The donor/barcode relationship was checked rather than assumed, and barcode
  suffixes turned out **not** to be one-to-one with donors (suffixes 5, 6 and 7 each
  carry two donors). This is recorded in the freeze as a fail-closed rule for Route B.
  It is listed here as an examination that changed a design, not as a defect in
  shipped output.
