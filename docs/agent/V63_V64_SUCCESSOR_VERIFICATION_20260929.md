# V64 successor — verification from the V63 lane, and three gaps

**Verified, not accepted on report.** Branch
`chatgpt/v64-e2-single-source-successor-20260929` @ `003ad549a158ebf44093d9771cb7c2aabd240d05`.

| claim | check | result |
|---|---|---|
| contains V63 head `e96d2285` | `git merge-base --is-ancestor` | **YES** |
| 6 commits ahead | `git rev-list --count` | **6** |
| 6 added files | `git diff --name-status` | **6, all `A`** |
| no source/test modification | diff filtered to `src`, `tests` | **no `M` or `D`** |
| Table S5 digest consistent | searched their receipt for my sha256 | **absent — correctly** |

That last row is the right outcome, not a discrepancy: Table S5's authentication
lives in my `e96d2285` and their receipt covers the other five binaries, exactly
as stated. No digest is claimed twice and none conflicts.

## The P1 ruling is correct, and correct in the way that matters

My raised gap was that C4/P1 requires **cross-source** concordance and only one
admissible source exists. The V64 ruling:

> `P1_cross_source_contact_concordance: NOT_APPLICABLE_ON_SINGLE_SOURCE_PATH`
> `explicitly_not: PASS`
> "Same-study neuron/oligodendrocyte concordance is not independent source
> replication and must not be relabelled as P1."

That is the distinction I was worried would get blurred, stated more sharply than
I stated it. The replacement `P1S_SINGLE_SOURCE_SUBSTRATE_QUALIFICATION` carries a
different name, a weaker claim ("supports MICROGLIA_SUBSTRATE_FIT... does not
establish cross-source replication"), and the object is renamed
`E2_NOTT_CANDIDATE` with an explicit `must_not_be_called` list. Nothing here
launders a missing precondition into a satisfied one.

## One thing genuinely improves versus the Corces path

**Nott's PLAC-seq is performed on PU.1+ SORTED nuclei.** Corces's HiChIP was bulk
tissue, and the V61 all-24-cluster sweep found microglia were the *worst*-matched
layer — beaten 2.5× by a doublet artifact. A sorted contact map should not
reproduce that failure mode.

Should not, and is not yet shown not to. P1S's same-study
microglia-vs-neuron-vs-oligodendrocyte substrate-fit test is exactly where that
gets demonstrated rather than assumed, and the contract requires it before the
object becomes load-bearing. That is the correct placement.

---

## Gap 1 — liftover provenance is mixed, and it is cheaply checkable

The ATAC tracks come from
`filer2.niagads.org/.../hg38_lifted/Nott_2019/ATAC-seq/bed3-lifted/hg38/` — i.e.
**already lifted to hg38 by FILER/NIAGADS**, under a chain and procedure that are
not recorded. The Table S5 interactome will be lifted by us with the UCSC
`hg19ToHg38.over.chain.gz`.

So two independent lift procedures meet in hg38, and a peak and a contact anchor
could disagree because of differing liftover rather than biology. On a design
whose whole content is *contact ∩ accessibility*, that is not a cosmetic concern.

**It is directly testable and cheap.** The receipt records the ATAC schema as
"first triplet hg38 lifted coordinates; second triplet source-coordinate
provenance" — the source hg19 coordinates are retained in columns 4–6. So:
re-lift columns 4–6 with the UCSC chain and compare to columns 1–3. Agreement
rate and disagreement magnitude close the question outright. Proposed as an
addition to the C3 round-trip qualification rather than a separate step.

## Gap 2 — C12 asks for bytes **and terms**; only bytes are recorded

C12 item 4: *"verify the chosen accessibility source bytes and terms."* The
receipt verifies bytes thoroughly — size, MD5, SHA-256, row counts, zero
malformed rows, FILER MD5 agreement. **No licence or terms field appears
anywhere** in the receipt or the custody manifest; searching both for
licence/terms/CC-BY/open-access returns nothing.

This is the same discipline that made me record Kosoy ATAC as `UNKNOWN` terms and
therefore fail-closed. The situation here is much more favourable — the
underlying Nott data is published and FILER/NIAGADS is a public annotation
resource — so this is a gap to close by writing the terms down, not a blocker.
But "we did not check" and "it is open" must not be recorded identically.

## Gap 3 — on this path, contact and accessibility are **not independent layers**

Both come from Nott 2019, both from **PU.1-sorted** microglia, and in all
likelihood from the same donors.

On the Corces path these were independent: different assays, different
processing, and only 3 of 13 donors shared between the contact and accessibility
layers. That independence was a weakness for donor matching and a *strength* for
evidential separation. Here it inverts. A PU.1-sorting or donor-panel artifact —
anything that makes a region look both contactful and accessible in sorted
microglia specifically — would appear in **both** layers, and their intersection
would not be two lines of evidence.

The `must_not_be_called` list already bars "independently replicated contact set"
and "multi-source supported contacts". It does not yet bar the closely related
overclaim that contact and accessibility independently corroborate each other.
**Proposed addition to claim scope:**

> contact and accessibility on this path share study, sorting strategy and
> probably donors; their intersection is a *conjunction of two measurements on
> the same material*, not independent corroboration.

---

## What the V63 lane owes next

C12 item 6 assigns it: *"verify the continuous-adjustment estimator's V64 leakage
and out-of-span qualifications before using it for validation-cohort
correspondence."*

That is the same follow-up I flagged myself when reporting classification A —
the frozen feature set (log-distance, degree, and their interaction) spans
`NEG_TECH_2`'s simulated latent `(degree/10) × (1e5/distance)` almost exactly, so
reading A's scope is *"within the span of the frozen adjustment model"*. An
out-of-span geometry-keyed nuisance is the test that would either widen that
scope or bound it.

Because such a negative would be constructed **after** seeing A, it needs the
same prospective freeze everything else here has had: specify the mechanism, the
arms and the pass rule, commit them, then run. That is the next piece of work
from this lane, and it should not begin until its own contract is committed.

`TRAINING=OFF`. `TD60=BLOCKED`. `E2_NOTT_CANDIDATE` not instantiated.
