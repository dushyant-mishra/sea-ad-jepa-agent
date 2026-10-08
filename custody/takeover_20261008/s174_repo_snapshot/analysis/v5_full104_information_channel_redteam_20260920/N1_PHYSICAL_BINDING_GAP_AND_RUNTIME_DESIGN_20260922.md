# N1 physical-data binding: the gap, and the runtime that must close it

Date: 2026-09-22
Scope class: **`CURRENT_FULL104_AUTHORITY`**

```
branch   gpu/v5-full104-n1-physical-burden-preflight-20260922-claude
parents  PR #58  601cccf4fff98a471fa0cf2595374efa9ef9be59  (N1 CPU burden assembler)
         PR #50  e4b7e9f46842d66cd7db71b1df9de60fc037f971  (N1 authority parent)
```

**N1 was not executed. No mask was generated. No burden was computed. No outcome
was opened.**

---

## B1 — what the heavy NPZ actually contains

Verified against the physical artifact, not against its reputation:

```
path   D:/jepa_full104_redteam_20260920_external/core_sufficient_statistics_v1.npz
bytes  242,087,519                                        (expected: match)
sha256 f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae   MATCH
```

### The headline correction

> PR #58's module docstring states: *"the current qualified heavy NPZ alone
> supplies donor_nnz, not donor_umi."*

**Against the physical asset that is not accurate.** `donor_umi` is present:

| key | shape | dtype | bytes |
|---|---|---|---|
| `donor_nnz` | (104, 17186) | int64 | 14,298,752 |
| **`donor_umi`** | **(104, 17186)** | **int64** | **14,298,752** |
| `donor_nsum` | (104, 17186) | float64 | 14,298,752 |
| `donor_nsq` | (104, 17186) | float64 | 14,298,752 |
| `core` | (17186,) | int64 | |
| `duniq` | (104,) | object | |
| `donor_src` | (104,) | int64 | |

**But PR #58's conclusion is right, for a sharper reason than it gives.** The V2
qualification receipt contains **zero references to `donor_umi`**. It verifies
`donor_nnz` geometry, `libraries`, `src_of_cell`, `donor_cells`, `core` size and
`duniq` sortedness — and never touches `donor_umi` at all.

So an array that the N1 assembler depends on has been sitting inside a file
stamped `HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE` while carrying no qualification of
its own. **An unqualified array inside a qualified file is not authenticated
data**, and the file-level verdict makes it look as though it were. That is the
more dangerous form of the defect, because the reassurance is misleading rather
than absent.

**The gap is a qualification gap, not a materialization gap.** The correct repair
is therefore to authenticate the array that exists, not to spend a full
8,915-block rebuild producing a second copy of it. Task B3 says to build a
producer *"only if it does not already exist"*; it does exist, so this lane
qualifies it instead.

### The six B1 questions, answered

1. **What `donor_nnz` represents.** `donor_nnz[d, a]` = the number of cells of
   donor `d` whose **raw count at strict-core address `a` is > 0** — a detected
   -token count, not a sum. Recovered from the frozen producer
   `build_core_sufficient_statistics_20260920.py`, where it is
   `np.bincount(flat)` with no weights over entries filtered by
   `keep = (pos >= 0) & (data64 > 0)`. Not guessed.
   `donor_umi[d, a]` is the same accumulation **weighted by the raw integer
   count**, so it is the raw UMI mass at that donor × address.
2. **Exactly 104 × 17,186?** Yes, both, int64.
3. **Address order.** `pass1["core"]` — 17,186 ledger column indices, **strictly
   increasing**, spanning [0, 40475]. Identical in pass1 and the artifact. Order
   digest `7affd20f8a6781ed7288e208d97a7f9323545320f995291aaebfce70c7317d04`.
   *(Note for readers of the producer: the `sorted(range(core.size), key=sha256(salt|core[i]))`
   at line ~114 is the Audit-E pool selector, a different object. It is not the
   core order.)*
4. **Donor order.** `pass1["duniq"]` — sorted unique donor-ID strings
   (`H15.03.003`, `H15.03.005`, …), identical in pass1 and the artifact. Order
   digest `306e8f7f0c51f0650daf2ee8561bf6056a61bc037d1b5139ff9953884af1e8e1`.
5. **Are those orders receipt-bound?** **Only partly.** The V2 receipt binds
   `duniq` sortedness and length and `core` *size*; it does **not** bind the
   `core` value/order digest, and it does not bind `donor_umi` at all. Both
   digests are therefore recorded here so a successor receipt can pin them.
6. **Do raw donor × address UMI totals already exist?** **Yes** — `donor_umi`.
   They needed authentication, not construction.

---

## B2 — the binding gap, stated precisely

`assemble_n1_from_authenticated_stream(...)` accepts `donor_nnz`, `donor_umi`,
`donor_source_code`, `fold_by_donor` and `stream` **from its caller**.

Its internal checks are genuinely strong — 256 targets, 17,186 addresses, 104
donors, source counts 41/17/46, fold counts 28/26/25/25, exact target IDs,
policy/rung/donor coverage, duplicate and missing consumption, `raw UMI >=
detected`, and the full 256 × 3 × 6 × 104 geometry.

**None of that is provenance.** Every one of those checks is a statement about
*internal consistency of whatever was handed in*. The assembler cannot tell an
authenticated FULL104 aggregate from a consistent fabrication, because:

- source counts `41/17/46` are satisfied by **any** permutation that preserves
  the multiset — including one where the source vector and the stream were
  altered **together**;
- fold counts `28/26/25/25` are likewise permutation-invariant;
- `raw UMI >= detected` is a property any plausible synthetic pair satisfies;
- the 256 target IDs are checked against a frozen list, but nothing binds the
  *rows* those IDs index to the physical substrate.

The failure mode is not a caller who passes garbage — the checks catch that. It
is a caller who passes a **coherently wrong** set of inputs. Internal consistency
is exactly the property a coordinated substitution preserves.

**The fix is not another command-line argument.** An unchecked `--donor-umi`
path would reproduce the same defect one level out. The physical runtime must
require a **receipt**, and must recompute the digests that receipt claims:

| input | must be bound to |
|---|---|
| `donor_nnz`, `donor_umi` | the heavy-artifact SHA-256 **and** the new donor-UMI qualification receipt |
| strict-core address order | `strict_core_order_sha256`, recomputed from the array actually loaded |
| donor identity/order | `donor_order_sha256`, recomputed from the registry actually loaded |
| `donor_source_code` | the authenticated split receipt's canonical digest, not a count |
| `fold_by_donor` | the same split receipt, by **value**, not by histogram |
| `stream` | the planner/executor source hashes named in the B4 contract |

Each of these is a digest over the bytes the runtime *actually used*, compared
against a frozen receipt — never a shape or a count.

---

## B3/B5 — independent qualification of `donor_umi`

`qualify_donor_umi_independent_v1_20260922.py` recomputes `donor_nnz` and
`donor_umi` for a deterministic, source-stratified donor subset directly from raw
Level-4 count blocks, along a route sharing no code with the producer, and
requires **exact integer equality** — no tolerance, because raw integer
aggregation needs none.

Guards enforced during the pass: manifest hash, every block's metadata SHA and
every consumed block's count SHA, no duplicate `block_key`, no `selection_row`
consumed twice, donor identity checked against pass1 for every row, non-integer
counts rejected, negative counts rejected, and all 4,553,407 cells accounted for
exactly once.

The donor subset is chosen by `SHA-256("V5_DONOR_UMI_INDEPENDENT_QUALIFICATION_20260922|<donor_id>")`
stratified by source — a rule fixed before any comparison, so the subset cannot
have been picked to make the check pass. Each donor's **entire 17,186-address
row** is compared, which covers low, median and high detection addresses by
construction rather than by hand-picking three of them; the receipt additionally
reports those three probe addresses per donor for readability.

Results are in `evidence/phase_i/DONOR_UMI_INDEPENDENT_QUALIFICATION_V1.json`.

---

## Task C — what the N1 runtime must still provide

None of this is built here, and **N1 is not executed**. This is the specification
the successor must satisfy.

| # | requirement | binding |
|---|---|---|
| 1 | source-bound runtime CLI | own normalized-source SHA recorded in its receipt |
| 2 | N1 execution authority | `eb3293720c54ae10023a90b73c1bf35b46b6cacfda70632522014d988ebb0096` |
| 3 | B4 contract | `c68231e53ee08990949688013261c957fc205f9599bbc446780a12ba4d276927` |
| 4 | physical donor burden aggregate | heavy SHA `f77dff47…` **+** the donor-UMI qualification receipt |
| 5 | frozen 256-target order | prefix of the frozen sample; order compared by value |
| 6 | RNG-V3 bridge | authority `775aba50…`, `global_seed` 1267387626254385975 |
| 7 | 104 donor source/fold identities | split canonical `5d616c9c…`, compared **by value** |
| 8 | crossfold planner source hash | recomputed at runtime |
| 9 | cached planner source hash | recomputed at runtime |
| 10 | burden estimator source hash | `7f589f54…` |
| 11 | deterministic execution order | target → fold → rung → policy, lexicographic on frozen IDs |
| 12 | crash-safe resumability | append-only journal keyed by `(target, fold, policy, rung)` |
| 13 | no duplicate target consumption | journal key uniqueness enforced on replay |
| 14 | no partial result accepted | terminal requires the full 256 × 3 × 6 × 104 census |
| 15 | atomic final commit | write to a temp path, fsync, then a single rename |
| 16 | byte-hashed result arrays | SHA-256 per array, recorded in the receipt |
| 17 | `AuditBN1ResultReceiptV1` | binds every root above plus the array digests |
| 18 | precision decision blocked | the precision rule must refuse until that receipt exists |

### Restart-equivalence test, on synthetic data only

A clean uninterrupted synthetic run and a deliberately interrupted-and-resumed
synthetic run must produce **byte-identical** final arrays and an identical
receipt digest. Interruption should be injected at several points, including
mid-journal-write. **No real N1 outcome may be used for this test** — restart
equivalence is a property of the runner, and testing it on real data would open
the outcome to prove a mechanical claim.

---

## Remaining N1 execution blockers

1. **The physical runtime does not exist.** PR #58 is an assembler, not a
   runtime; nothing connects the authenticated aggregate to it.
2. **Caller-supplied inputs are not provenance** (B2). Must be receipt-bound.
3. **`core` order and `donor_umi` are not bound by the V2 receipt.** The digests
   are recorded here; a successor qualification receipt must pin them.
4. **No `AuditBN1ResultReceiptV1` exists**, so by design the precision decision
   is correctly blocked.

```
AUDIT_B_N1                = UNOPENED
MASKS EXECUTED            = NONE
BURDEN CALCULATION        = NOT RUN
N1 TARGET SELECTED        = NONE
PRECISION CALCULATED      = NO
TRAINING                  = OFF
```
