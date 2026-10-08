# P1S V2 sensitivity completion — my v1 "correction" was itself a one-operator artifact

Closes the local-density half of the canonical audit finding. Scope is exactly
what was authorised: **descriptive sensitivities only**. Population, null,
estimand, bootstrap, thresholds and the PASS decision are untouched, and the
script still refuses to emit any table unless the primary reproduces first.

```
primary reproduction: analysed_pairs True | E_microglia True | D_MN True | D_MO True
E_microglia +0.18894714  D_MN +0.15484519  D_MO +0.15790480  62,753 pairs
```

**`P1S primary gate = PASS`, unchanged, for the third time under a third
stratification scheme.**

---

## The headline: I have to withdraw my previous withdrawal

Three statements have now been made about local-density dependence, by me, in
sequence:

| version | claim | basis |
|---|---|---|
| v0 (`303ca8b6`) | "the microglial advantage vanishes and goes negative in the lowest-density quartile" | microglia **observed**-distal density only |
| v1 (`8b13939b`) | "flat and uniformly positive — the 20× gradient **does not exist**" | sum over all six measurements only |
| **v2 (here)** | **density dependence is real, its direction depends on which arm you stratify on, and no operator is authoritative** | all six operators, none selected |

The audit's point was that V2's phrase *"pooled quartiles of local peak
density"* never defines the map from the six per-pair density measurements
(observed/null × three ATAC tracks) to one stratum. I accepted that, and then
made the identical error one level up: I picked the sum-over-all-six, with P1S
outcomes already visible, and announced it as *the* contract-compliant answer.

Running all six shows why that was not safe.

## The panel (outcome-exposed, descriptive only, **none selected**)

`D_MN` by quartile, low → high:

| operator | Q1 | Q2 | Q3 | Q4 | Q4−Q1 |
|---|---|---|---|---|---|
| D1 sum, all six (my v1 pick) | +0.1308 | +0.1588 | +0.1588 | +0.1671 | **+0.036** |
| D2 sum, three tracks, **observed** only | +0.0802 | +0.1373 | +0.1730 | +0.2154 | **+0.135** |
| D3 sum, three tracks, **null** only | +0.1800 | +0.1847 | +0.1562 | +0.1021 | **−0.078** |
| D4 microglia, mean of obs & null | +0.0864 | +0.1516 | +0.1799 | +0.1857 | +0.099 |
| D5 max over all six | +0.0937 | +0.1166 | +0.1524 | +0.2100 | +0.116 |
| D6 microglia **observed** only *(superseded v0)* | **−0.0111** | +0.0859 | +0.1680 | +0.2981 | +0.309 |

**D1 is the only flat one, and its flatness is arithmetic cancellation.**
D1 = D2 + D3. D2 rises by +0.135 and D3 falls by −0.078; pooling them offsets the
two gradients into +0.036. Reporting D1 alone and concluding "there is no density
dependence" reads a cancellation as an absence. Those are different claims and I
conflated them.

### Why the direction flips

`E_c = O_c − N_c` — observed support minus null support. Stratifying on
**observed**-interval density selects on the first term: high strata have high
`O`, the null arm is unconstrained, so `E` is large (D2, D6). Stratifying on
**null**-interval density selects on the second term: high strata have high `N`,
the observed arm is unconstrained, so `E` is small (D3). Each is selection on one
arm of a difference, in opposite directions.

That is also the pre-stated argument for pooling both arms — I wrote it into the
v1 script before seeing any output, and it is still a real argument. What it
does **not** license is treating the resulting flatness as evidence that density
dependence is absent. It is evidence that the two selection effects are of
similar size.

### What survives regardless of operator

Across all 48 strata × statistics in the panel, **exactly two values are
negative**, both in D6 Q1 — the single most outcome-downstream stratifier, and
the one already superseded. Excluding D6:

- minimum `D_MN`/`D_MO` anywhere: **+0.0802** (D2 Q1)
- maximum: **+0.2155** (D5 Q4)

So the robust statement is: *the contact-specific microglial excess is positive
in every stratum of every defensible pooling operator, ranging roughly +0.08 to
+0.22, with a magnitude that depends on local peak density in a direction set by
which arm of the difference the stratifier is computed from.* That is weaker than
my v1 message and stronger than my v0 message, and unlike both it does not
depend on a choice I made after seeing outcomes.

**No operator is selected, and none may be.** Fixing this properly requires a
prospective freeze naming the operator before outcomes exist — a successor
contract action, not something this script or this branch may do.

---

## The two mandatory reports, now with independent-unit counts

Both were re-emitted with `number_of_distinct_promoters`, which the completion
spec required for the degree report. I added it to **all** tables, because the
bootstrap resamples promoters and a stratum's independent support is its promoter
count, not its pair count.

**Post-C3 log distance** — unchanged from v1, plus promoter counts:

| quartile | n pairs | distinct promoters | E_mic | D_MN | D_MO |
|---|---|---|---|---|---|
| Q1 (shortest) | 15,315 | 5,980 | +0.1857 | +0.1833 | +0.1973 |
| Q2 | 15,742 | 5,416 | +0.1973 | +0.1722 | +0.1757 |
| Q3 | 15,731 | 4,899 | +0.1833 | +0.1397 | +0.1371 |
| Q4 (longest) | 15,965 | 4,271 | +0.1894 | +0.1254 | +0.1231 |

**Promoter degree** — and here the added column matters a great deal:

| quartile | n pairs | distinct promoters | pairs per promoter | E_mic | D_MN | D_MO |
|---|---|---|---|---|---|---|
| Q1 (lowest) | 14,306 | 6,691 | 2.1 | +0.1573 | +0.1250 | +0.1255 |
| Q2 | 15,367 | 2,468 | 6.2 | +0.1747 | +0.1426 | +0.1478 |
| Q3 | 16,721 | 1,491 | 11.2 | +0.1973 | +0.1579 | +0.1649 |
| Q4 (highest) | 16,359 | **722** | **22.7** | +0.2215 | +0.1894 | +0.1885 |

The Q4 stratum's 16,359 pairs rest on **722 independent promoters**. Its point
estimate is the largest in that table, and it is also the least well supported —
a fact that was invisible in the v1 report, which showed pair counts only. This
is mechanical (degree quartiles sort by pairs-per-promoter by construction), but
it is exactly the kind of thing a reader would otherwise take at face value.

---

## Self-audit lane (continuing from S21)

**S22 — I replaced an under-specified choice with another unforced choice and
labelled it compliant.** Caught by the canonical audit, not by me, and the
consequence was a published claim ("the gradient does not exist") that the panel
contradicts. Root cause: when a contract is found to be ambiguous, the correct
response is to report the ambiguity, not to resolve it myself post-hoc. Fixed
here by reporting all six and selecting none. *Not fully closable on this branch*
— only a prospective successor freeze can actually resolve the operator.

**S23 — my v1 rationale was sound but I let it carry more weight than it could.**
The pre-stated argument for pooling both arms is genuine and I did write it
before seeing output. That made me treat the resulting number as validated rather
than merely as one of several. A correct prior reason to prefer an operator is
not the same as evidence that the other operators would have agreed — and here
they do not.

**S24 — the v1 sensitivity tables reported pair counts as if they were sample
size.** Under a promoter-level bootstrap they are not. Degree Q4 is a 22.7:1
clustering ratio. Fixed by emitting distinct-promoter counts on every table; the
underlying CIs were always computed correctly, so no published interval changes.

**Examined and clean:** the primary reproduction assertion still fires before any
table is emitted (verified by the `checks` dict printing all-`True` first); no
stratum was trimmed, reweighted or excluded; `M_MIN`, the estimator, OUTSPAN and
the C3 adjudication were not touched.

---

## Unchanged

Claim scope is exactly as before: a P1S pass establishes **internal microglial
substrate compatibility** relative to same-study comparators and the frozen
geometry null. Not independent external corroboration, not donor-independent
replication, not multi-source replication, not causal enhancer–gene assignment.

The contract forbids trimming, reweighting, rescuing or revising the P1S PASS on
the basis of any density stratum, and nothing here does so.

`E2_NOTT_CANDIDATE` not instantiated. P3 untouched, still blocked on exact
GSE73721 byte authentication plus a prospectively frozen expression rule.
`TRAINING=OFF`. `TD60=BLOCKED`.
