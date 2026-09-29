# P1S structure only — and why I stopped before the outcome

Branch `claude/v64-frozen-execution-20260929`, descending from canonical
`2d6fa8a1`. `TRAINING=OFF`, `TD60=BLOCKED`. **No P1S outcome opened.**

---

## The governance finding that stopped me

`V64_NOTT_P1S_OPERATIONAL_SUCCESSOR_CONTRACT_V2` is fully specified and
executable — I built the executor and it is committed here. I did **not** run it
past the structural stage, for one reason:

> `V64_SPILLOVER_FIREWALL_MANIFEST_V1` labels it
> **`current_parallel_P1S_operational_authority_candidate`** — a *candidate* —
> and it does **not exist on the canonical authority branch** at `2d6fa8a1`.

The firewall's own fail-closed rule says to stop and adjudicate provenance before
computing outcomes when a declared role does not match the allowlist. More
importantly, the hazard here is one-way:

**Computing the ATAC support rates would irreversibly consume the contract's
prospectivity.** Once those numbers are seen, V2 can never again be revised
prospectively — any later amendment would be a threshold chosen after the result.
Executing a *candidate* contract silently promotes it to authority by making it
unrevisable. That is a spillover in its own right, and it is exactly the class the
firewall exists to prevent.

So I ran only what opens nothing: orientation, recomputed in source hg19
coordinates, and the population funnel. The parallel lane's own audit classifies
that work as `SOURCE_STRUCTURE_MEASURED__NO_P1S_OR_P3_OUTCOME_OPENED`.

**What unblocks it:** V2 adopted onto the canonical branch, or an explicit
adjudication that a candidate contract on the readiness branch carries execution
authority. Either is a one-line decision; neither is mine to make.

---

## Orientation, recomputed independently — matches on every count

Implemented from the frozen rule against the authenticated Table S5
(`81c99689…`), not copied from their result:

| class | mine | parallel lane | |
|---|---|---|---|
| PROMOTER_DISTAL, exactly one promoter anchor | **64,210** | 64,210 | match |
| PROMOTER_PROMOTER | **7,614** | 7,614 | match |
| NO_ACTIVE_PROMOTER_MATCH | **32,978** | 32,978 | match |
| PROMOTER_DISTAL_UNIQUE_ENSEMBL | **61,624** | 61,624 | match |
| GENE_AMBIGUOUS_PROMOTER_DISTAL | **913** | 913 | match |
| GENE_UNANNOTATED_PROMOTER_DISTAL | **1,673** | 1,673 | match |

PU.1-active promoter annotation rows: **11,793**, also matching. Two independent
implementations of the same frozen rule agreeing on all six counts is a
meaningful check on both.

## The population funnel — a number that needed both lanes

| stage | contacts |
|---|---|
| original microglia interactions | 104,802 |
| C3-retained (exact identity, my lane) | 102,701 |
| **C3-retained AND source-oriented promoter-distal** | **62,890** |
| fraction of original | **0.600084** |

This is the P1S analysis population and it existed in neither lane alone: it
needs my C3 exact-identity result crossed with their source-only orientation.
**60.01%** of the deposited interactions survive both gates.

Note the two attritions are largely independent — 64,210 oriented before C3, and
62,890 after, so C3 removes ~2.06% of the oriented set, close to its 2.04%
overall attrition. The coordinate gate is not preferentially destroying oriented
contacts.

---

## Spillover self-audit against the firewall's forbidden list

| forbidden class | status |
|---|---|
| same filename from a superseded branch | **clear** — used P1S **V2**; V1 is explicitly non-authoritative and was not read for mechanics |
| historical/exploratory output substituted for a frozen result | clear |
| smoke output described as the 18/24 decision run | **clear now** — I made exactly this error in prose earlier and corrected it; no smoke output was ever committed as a decision result |
| Corces substituted into the Nott lane | clear |
| Morabito protected correspondence opened | clear |
| NIH-CARD biological correspondence opened | clear |
| AD loci / JEPA targets used to rescue or tune P1S | clear |
| Kosoy or access-required artifact substituted | clear |
| FILER-prelifted treated as equivalent without the provenance audit | **clear** — the audit was run first: 144,607 intervals, 100.0000% exact |
| Nott neuron/oligo comparators relabelled as independent P1 replication | clear — the "not independent corroboration" wording is carried verbatim |
| coarse matching resurrected as primary estimator | clear |
| out-of-span nuisance added to the basis and called generalisation | clear — the failure stands unrepaired |
| raw cross-cell-type support rate as the P1S primary gate | **not applicable — no support was computed at all** |

**Binary allowlist:** all six scientific binaries verified against the firewall's
recorded SHA-256 before use — Table S5, the three ATAC tracks, both chains. All
matched.

**Branch provenance:** this branch descends from canonical `2d6fa8a1`; contracts
were read from `chatgpt/v64-parallel-execution-readiness-20260929`, which is not
on the firewall's non-authoritative list, and the candidate status of P1S V2 is
recorded rather than assumed away.

---

## Two corrections I accept from their audit of my work

Their independent audit returned
`PASS_NUMERICAL_AND_LINEAGE_EXECUTION__MINOR_REPORTING_REPAIRS_RECOMMENDED`, with
three LOW-severity findings. Two are wording overreaches of mine and I adopt their
phrasing:

**1. "Reading C is ruled out" was too strong.** The frozen contract never defined
a numeric threshold for "materially restored", so I cannot rule the reading out —
only observe that nothing supports it. Corrected wording:

> Reading C is not supported; no material restoration is evident at the observed
> scale.

**2. "the two depth features had essentially no predictive weight" over-infers.**
The ablation establishes *dispensability for the decision result*, not zero
fitted weight — redundancy or collinearity with the remaining twelve features
would produce the same ablation outcome. Corrected wording:

> Their removal had essentially no effect on the decision metrics. Individual
> fitted weight should not be inferred without a coefficient or
> partial-prediction diagnostic.

Both corrections tighten claims without touching any number, and neither affects
`A_pass_survives` or `B_outspan_fails_only`.

**3. Their third finding — that my result JSONs name contracts but do not bind
contract/code blob SHAs internally — is addressed going forward:** this
structure-only receipt binds the canonical commit, the branch, the candidate
status of P1S V2, and the Table S5 digest inside the JSON itself, rather than
relying on the firewall manifest to pin them externally.

---

## State

`E2_NOTT_CANDIDATE` not instantiated. P1S executor committed but **not executed
past the structural stage**. P3 remains blocked on GSE73721 byte authentication
and a prospectively frozen expression rule — untouched here, and promoter
chromatin activity was not substituted for measured expression.
