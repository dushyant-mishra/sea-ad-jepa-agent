# Amendment 3 to the V69 Route-A / Route-B prospective freeze — exclusion list ON

**Status: FROZEN, PROSPECTIVELY.**
**Written while zero eRegulons, zero route statistics, zero control statistics and zero
Route-B regions exist. No downstream biological network has been inspected by anyone in
this lane.**

Lane: V74 LANE E.
Worktree: `D:/jepa_wt_v74_laneE_20261002`, branch `claude/v74-blacklist-and-512pilot-20261002`.
Base: `claude/v69-scenicplus-external-network-20261001` @ `d5b76230c1d2837dfbf643e205c5b2780831d8f9`.

Supersedes nothing. Extends the V69 prospective freeze and its Amendments 1 and 2
(`docs/agent/V69_SCENICPLUS_LANE_STATUS_AND_HANDOFF.md`, "Prospective freeze").

---

## 1. The decision

The project owner decided that the ENCODE GRCh38 exclusion list is **ON**. The reasoning
recorded with the decision was that an explicit prospective amendment is better than a
silent omission.

This document does not revisit that decision. It makes it auditable: it binds the
decision to specific bytes, states the rule that locks it, and reports what it costs.

## 2. What is frozen

| Item | Value |
|---|---|
| Policy | `BLACKLIST = ON` |
| Artifact | ENCODE accession **ENCFF356LFX** |
| Annotation dataset | ENCSR636HFF, "DAC Exclusion List Regions", annotation type `exclusion list` |
| Genome build | **GRCh38** (asserted by ENCODE and checked in the acquisition receipt) |
| Source URL | `https://www.encodeproject.org/files/ENCFF356LFX/@@download/ENCFF356LFX.bed.gz` |
| Bytes (gzip) | **8,211** |
| SHA-256 (gzip) | `a9d086ce90ca67f933b29adfbff56ea768bbce2ec4b0d51e2d405e5a1d61bb56` |
| MD5 (gzip) | `393688b4f06c9ce26165d47433dd8c37` |
| SHA-256 (uncompressed BED) | `5d214c58c07f33a4fa1d6bcfe61ff00c666510e8fee5520fc1015c5d3ef16f3b` |
| MD5 (uncompressed BED) | `e18ece427a686932268efbb4fc759d99` |
| Content | 910 intervals, 71,570,285 bp, 24 contigs, UCSC `chr*` spelling |
| Acquired (UTC) | 2026-10-03T01:33:47Z → 01:33:48Z |
| Overlap rule | `ANY_OVERLAP_DROPS_THE_WHOLE_REGION` |
| Applies to | **Route A and Route B, identically** (see §5) |

Acquisition receipt:
`D:/jepa_v5_outputs_20260925/v74_laneE/receipts/ACQ_ENCODE_BLACKLIST_ENCFF356LFX_V1.json`.

### Why three identities and not an exit code

`curl` returning 0 is not evidence that a file is complete; acquisition tools report
success on truncated downloads. Three identities published by ENCODE were reproduced
locally and all three agree:

1. the server-declared `Content-Length` (8,211) equals the bytes on disk, and equals the
   `file_size` in ENCODE's own metadata record;
2. the S3 `ETag` equals the local MD5 of the gzip, and equals ENCODE's published
   `md5sum`;
3. ENCODE's published `content_md5sum` equals the local MD5 of the **uncompressed**
   BED. This is the strongest of the three, because it survives re-compression.

A `HEAD` request could not be used: the portal answers 307 to a presigned S3 object that
returns 403 to `HEAD`. The authoritative length was therefore taken from the `GET`
response headers and cross-checked against the metadata record. That substitution is
recorded in the receipt rather than papered over.

### Licence — `downloadable != licensed`

Read off the portal at acquisition time and quoted verbatim in the receipt:

> Data Use Policy for External Users. External data users may freely download, analyze
> and publish results based on any ENCODE data without restrictions. This applies to all
> datasets, regardless of type or size, and includes no grace period for ENCODE data
> producers, either as individual members or as part of the Consortium.

No registration, access control or data-use agreement was presented at any stage.
ENCODE requests citation of the Consortium publications and of the accessions used
(ENCSR636HFF / ENCFF356LFX); the underlying method is Amemiya, Kundaje & Boyle,
*Sci Rep* 2019;9:9354 (PMID 31249361). All of this is recorded in the receipt.

## 3. The locking rule

> **The exclusion-list policy — on/off, the accession, the digest and the overlap rule —
> may not be changed after any downstream Route-A or Route-B biological result has been
> inspected.**

If the policy is ever changed, the change must be a dated successor amendment that
states what was already seen at the time of the change, and every result produced under
the old policy must be re-derived or explicitly retracted. A policy that can be revised
after looking at the network is not a policy; it is a tuning knob, and it would make
"we excluded the artefact regions" unfalsifiable.

This lane has inspected no eRegulon, no route statistic, no control statistic and no
network. There is none to inspect: Route B's region universe does not exist yet.

## 4. Attrition on Route A — a structural count

Measured, not estimated, by `scripts/v74/laneE_blacklist_attrition_v1.py` against the
frozen Route-A region universe
(`V69_ROUTE_A_SUBMITTED_PEAKS_REGION_UNIVERSE.bed`,
sha256 `dd0d2d00904345c1b6489de99f62d95581b82fed7946cefa3254ca815a73be32`).

| Quantity | Before | Removed | After |
|---|---:|---:|---:|
| Regions | 150,561 | **263** (0.175 %) | 150,298 |
| Base pairs | 126,142,895 | **211,953** (0.168 %) | 125,930,942 |

Of the 211,953 bp that leave the universe, **187,762 bp actually intersect** an exclusion
interval and **24,191 bp are collateral** — base pairs removed only because the
any-overlap rule drops a region whole rather than trimming it. Both numbers are reported
because only the first is a property of the exclusion list and only the second is a
property of the rule.

Sensitivity to the rule (how many regions would be dropped at a higher overlap
threshold) is tabulated in the attrition receipt, so the chosen count does not look more
inevitable than it is.

Receipt:
`D:/jepa_v5_outputs_20260925/v74_laneE/receipts/V74_LANEE_BLACKLIST_ATTRITION_ROUTEA_V1.json`.
Per-region lists:
`blacklist/ROUTE_A_REGIONS_EXCLUDED_BY_POLICY.bed` (column 5 carries the literal label)
and `blacklist/ROUTE_A_REGIONS_RETAINED_AFTER_BLACKLIST.bed`.

**Route B attrition is `UNMEASURED`.** Its region universe does not exist. No number is
asserted for it, and none may be extrapolated from Route A: the two universes are built
by different procedures and their overlap with the exclusion list is an empirical
question.

### Semantics — three classes that must not be merged

| Class | Count on Route A | Meaning |
|---|---:|---|
| `EXCLUDED_BY_POLICY` | 263 | The project decided in advance not to scan these. Not biological zeros, not absent signal, not unmeasured. |
| `STRUCTURALLY_UNSCOREABLE` | 53 | No reference sequence exists under the source's contig spelling, so a scanner could never score them. Dropped at region-universe construction, before this amendment. |
| measured zero | — | A region that was scanned and scored zero. Remains measured evidence. |

Any downstream artifact carrying these regions must carry the label with them. Collapsing
`EXCLUDED_BY_POLICY` into zero would turn a policy decision into a biological claim.

## 5. The amendment applies to BOTH routes — this is not optional

Amendment 1 exists so that the **region universe is the single varying factor** between
Route A and Route B. Applying the exclusion list to Route B and not to Route A would
reintroduce exactly the confound Amendment 1 removed: an observed Route-A/Route-B
difference could then be caused by the exclusion policy rather than by the peak
definition, and the comparison would no longer test what it claims to test.

Therefore: the same accession, the same digest and the same `ANY_OVERLAP` rule are applied
to both region universes, and each route's attrition is reported separately. Route A's is
above; Route B's is pending its universe.

## 6. Enforcement — fail-closed, and tested

The producer authenticates **both** the exclusion list and the region universe by SHA-256
before it computes anything. A mismatch is a refusal: non-zero exit, no receipt written,
stderr naming the input and the reason.

`scripts/v74/test_laneE_blacklist_attrition_v1.py` — 19 assertions, 0 failures. The cases
that matter:

- a wrong digest is refused and **no receipt is written** (a refusal that still emitted a
  receipt would be worse than no gate, because the receipt would look authoritative);
- a **well-formed substitute** exclusion list is refused — the dangerous input is not a
  corrupt file but a plausible alternative;
- a file of **identical byte length** with one coordinate changed is refused, so the gate
  cannot be passing on size;
- an **absent** file is a refusal, not silently "nothing to exclude";
- an **authenticated empty** file is accepted and excludes zero — the opposite of the
  previous case, and the two must stay distinguishable;
- overlapping exclusion intervals are merged before bp arithmetic, with a negative
  control showing the unmerged answer differs (800 vs 600), so the test can detect the
  defect it targets.

**Evidence the tests can fail.** Two mutants were built from copies of the producer
outside the worktree and the suite run against each:

| Mutant | Change | Result |
|---|---|---|
| M1 | digest comparison replaced by `if False` | 6 of 19 assertions FAIL (T2, T3, T4, T5) |
| M2 | interval merging replaced by `if False` | 1 of 19 assertions FAIL (T8) |

A gate test that passes against a disabled gate would be worthless; these do not.

## 7. Operational requirement for Route B — and an open defect

`scripts/v69/routeb_call_peaks_and_consensus_v1.py` already accepts `--blacklist`, but it
**defaults to `None`**, and its receipt records `"applied": blacklist is not None`. Under
this amendment that default is a hazard: the policy can be omitted simply by not passing
the flag, and the run still succeeds. That is precisely the silent omission the owner's
decision was meant to prevent.

**Required repair (owner: the lane that owns the Route-B producer — NOT this lane, which
must not edit another lane's files):**

1. `--blacklist` becomes required, or absence becomes a hard failure;
2. the producer verifies the supplied file's SHA-256 against
   `5d214c58c07f33a4fa1d6bcfe61ff00c666510e8fee5520fc1015c5d3ef16f3b` (uncompressed) or
   `a9d086ce90ca67f933b29adfbff56ea768bbce2ec4b0d51e2d405e5a1d61bb56` (gzip) and refuses
   on mismatch;
3. the receipt records the accession and digest, not just a path and a boolean;
4. regions removed are emitted as a labelled `EXCLUDED_BY_POLICY` list with counts, never
   folded into the retained universe as zeros.

Until items 1–3 are in force, this amendment is **specified but not enforced on the
Route-B path**. A contract that the executor does not enforce is not in force, and this
document does not claim otherwise.

## 8. What this amendment does not do

- It does not authorise Stage 4, any training, or any network construction.
- It does not open DEV, SEALED or Morabito data. None were read.
- It makes no biological claim. 263 regions leaving a 150,561-region universe is an
  infrastructure number, not a result.
- It does not change the motif collection, the region-to-gene design, any threshold, any
  control, or the 10,249-motif universe.
