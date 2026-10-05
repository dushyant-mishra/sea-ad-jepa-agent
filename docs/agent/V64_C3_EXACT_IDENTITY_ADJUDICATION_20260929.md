# C3 adjudicated under the frozen exact-identity rule — **PASS**

Rule: `V64_NOTT_C3_EXACT_IDENTITY_SUCCESSOR_RULE_V1`, frozen at
`38d789aceecfdc71beca8852fbb19ab1621fee55`.

**Prospectivity verified, not asserted.** The freeze is timestamped
`2026-09-29 13:33:44 -0400`; my descriptive result was committed at
`13:42:12 -0400` (`5131bc6c`). The rule precedes the numbers by ~8.5 minutes, and
that ordering is checkable from the commit graph.

**No threshold was chosen.** The rule sets tolerance to zero and asks only
whether a non-empty exactly-identical set remains. The +74,685 bp event and the
0.998836 figure are not debated — they are simply attrition.

---

## The attrition funnel, denominators preserved

**Forward hg19 → hg38, 209,604 anchor instances** (strict partition, one label
per anchor, reconciles exactly):

| disposition | anchors |
|---|---|
| **admissible** (single, same chromosome, length preserved exactly) | **207,283** |
| length changed | 2,239 |
| unmapped | 73 |
| chromosome changed | 6 |
| ambiguous / split | 3 |

→ **pairs forward-admissible: 102,702**

**Round trip hg38 → hg19**, re-run on exactly those 205,404 forward-admissible
anchors:

| disposition | anchors |
|---|---|
| **exact recovery** | **205,403** |
| unmapped on return | 1 |
| non-exact recovery | **0** |
| ambiguous on return | **0** |

→ **pairs C3-retained: 102,701** · identity violations among retained: **0**

### `C3_ADJUDICATION: PASS`

A non-empty set remains; every retained pair preserves exact anchor identity in
both directions; the full funnel is reported from the original denominator; no
rescue of any kind was applied.

## Two retention numbers that must never be conflated

| | definition | value |
|---|---|---|
| descriptive mapping retention | both anchors mapped *at all* — permissive | 104,728 / 104,802 = **0.999294** |
| **C3 exact-identity retention** | both anchors single, same chromosome, length exact, both round-trip exact | **102,701 / 104,802 = 0.979953** |

My earlier project summary said *"converting it to the modern genome build kept
99.93%"*. That is the **descriptive** figure and I should not have let it stand
unqualified — the qualified number is **97.9953%**, and the 2.04-point difference
is real attrition, not rounding.

## A reconciliation worth stating

The ambiguous count reads 3 here against 15 in the descriptive run. Both are
correct and neither is a contradiction: the descriptive run counted every anchor
appearing more than once under `-multiple`, including 12 that were *also* absent
from the single-mapping output and are counted here as `unmapped`. This
adjudication assigns each anchor exactly one disposition by priority
(unmapped → ambiguous → chromosome → length), so the five categories partition
all 209,604 anchors and sum exactly.

## What the round trip revealed about the rule itself

Once exact forward length preservation is required, the round trip is essentially
perfect: **205,403 of 205,404 anchors return exactly, with zero non-exact
recoveries**. The 17 non-exact returns seen descriptively were anchors that had
already changed length on the way out. The forward identity filter removes almost
everything that would have failed on return — which is a good property of the
rule, and an argument that the two conditions are not redundant so much as
correctly ordered.

## ATAC provenance — narrower wording adopted

I previously wrote that the mixed-provenance hazard was "eliminated outright".
The accurate statement is narrower and is the one now carried:

> **The tested FILER-vs-UCSC coordinate-provenance discrepancy is empirically
> absent for all three authenticated Nott ATAC tracks** — 50,199 / 55,932 /
> 38,476 rows, 100.0000% exact, zero discordant, zero unmapped, zero ambiguous.

That is what was demonstrated. It does not generalise to tracks not tested.

## Implementation recorded permanently

UCSC `liftOver` **archived build `linux.x86_64.v479`**, sha256
`80c77de53b8bbd5fec661242f24d4b2f0ac54446df6954d934d1a838927dd19c`,
19,779,328 bytes. `-minMatch=0.95`, no authoritative `-multiple`, `-multiple` used
only to detect and reject ambiguity, identical forward and reverse. Both chain
digests recorded.

> **C3 must not be re-run with a different `liftOver` executable and the outputs
> mixed without an equivalence audit.**

The frozen implementation contract specified UCSC command-line semantics but did
not pin an executable version, so using the newest build compatible with this
environment is within contract — and the ATAC audit supplies an unusually strong
empirical cross-check: v479 plus our chain reproduced FILER's coordinates exactly
for **144,607 intervals** across three tracks.

## Retained object

`V64_NOTT_C3_RETAINED_CONTACTS_HG38.tsv.gz` — 102,701 contact pairs, hg38
coordinates with hg19 provenance retained. **Coordinates only; no gene annotation
is joined.**

## Coverage caveat, carried from the rule

C3 PASS does not establish that the retained support is large or representative
enough for P1S or P3. Retention fraction and any geometry or composition shift
are downstream claim-scope evidence, deliberately not hidden inside the
coordinate gate.

`TRAINING=OFF`. `TD60=BLOCKED`. `E2_NOTT_CANDIDATE` not instantiated.
