# P1S V2 sensitivity rerun — my density caveat was an artifact of my own binning

Responds to the canonical audit at `342d5796`:
`PRIMARY_GATE_PASS_VERIFIED__FULL_CONTRACT_CLOSURE_PENDING_SENSITIVITY_RERUN`.

Both compliance findings accepted. Scope is exactly as directed: **descriptive
sensitivities only**. Population, null, estimand, bootstrap, thresholds and the
PASS decision are untouched, and the script **refuses to emit any table** unless
the primary quantities reproduce first.

```
primary reproduction: analysed_pairs True | E_microglia True | D_MN True | D_MO True
```

`E_microglia` +0.18895, `D_MN` +0.15485, `D_MO` +0.15790, 62,753 pairs — identical
to `303ca8b6` to machine precision. **`P1S primary gate = PASS`, unchanged.**

---

## The correction that matters: I have to withdraw my headline caveat

I reported, prominently, that the microglial advantage *vanished and went slightly
negative* in the lowest local-density quartile, and said that finding "must travel
with the pass". **It was an artifact of my non-compliant stratification.**

| stratum | **pooled density (compliant)** | | | *microglia-observed-only (my error)* | | |
|---|---|---|---|---|---|---|
| | E_mic | D_MN | D_MO | E_mic | D_MN | D_MO |
| Q1 | **+0.1624** | **+0.1308** | **+0.1304** | +0.0156 | **−0.0111** | **−0.0038** |
| Q2 | +0.2024 | +0.1588 | +0.1631 | +0.1258 | +0.0859 | +0.0924 |
| Q3 | +0.1988 | +0.1588 | +0.1640 | +0.2118 | +0.1680 | +0.1734 |
| Q4 | +0.1891 | +0.1671 | +0.1698 | +0.3258 | +0.2981 | +0.2945 |

Under the contract's pooled definition the contrast is **flat and uniformly
strongly positive** — `D_MN` spans only +0.131 to +0.167, `D_MO` +0.130 to +0.170,
and **no quartile is negative**. The dramatic 20× gradient I reported does not
exist.

### Why my version produced a false gradient

Stratifying on **microglia observed-distal** density sorts pairs by a quantity
that sits directly downstream of the outcome. A pair whose observed distal
interval lies in a microglia-peak-sparse region can barely have `O_microglia = 1`,
so the lowest quartile of that variable is enriched — close to by construction —
for pairs where microglial support was near-impossible. That manufactures both the
gradient and the negative Q1.

The contract's pooled definition — every observed **and null** interval, across
**all three** tracks — is immune to this, because the stratum assignment no longer
depends on which interval happens to be the observed one. A pair cannot be sorted
into a stratum by the very quantity under test.

I wrote that rationale into the rerun before seeing its output, and it turned out
to be the mechanism. That is some consolation, but the substantive point is that
**I published an alarming caveat that was my own bug**, and it was caught by the
audit rather than by me.

---

## The two sensitivities I had omitted entirely

Both were mandatory in `mandatory_reporting` and both were missing from my first
run.

**Post-C3 log distance** — contrast is somewhat stronger at short range but
substantial everywhere:

| quartile | n | E_mic | D_MN | D_MO |
|---|---|---|---|---|
| Q1 (shortest) | 15,315 | +0.1857 | +0.1833 | +0.1973 |
| Q2 | 15,742 | +0.1973 | +0.1722 | +0.1757 |
| Q3 | 15,731 | +0.1833 | +0.1397 | +0.1371 |
| Q4 (longest) | 15,965 | +0.1894 | +0.1254 | +0.1231 |

`E_microglia` is essentially flat (+0.183 to +0.197); the *comparator* contrast
narrows with distance, from +0.18/+0.20 to +0.125/+0.123. Long-range contacts
retain a clear but smaller microglial advantage.

**Promoter degree** — mild monotone increase, positive throughout:

| quartile | n | E_mic | D_MN | D_MO |
|---|---|---|---|---|
| Q1 (lowest) | 14,306 | +0.1573 | +0.1250 | +0.1255 |
| Q2 | 15,367 | +0.1747 | +0.1426 | +0.1478 |
| Q3 | 16,721 | +0.1973 | +0.1579 | +0.1649 |
| Q4 (highest) | 16,359 | +0.2215 | +0.1894 | +0.1885 |

High-degree promoters show a somewhat stronger effect. Nothing here threatens the
conclusion; no stratum in any of the three sensitivities is negative or near zero.

---

## Net effect on the result

The primary gate was already verified. What changes is the **surrounding
caveat**, and it changes in the direction of a *stronger*, not weaker, result:

> Earlier: "contact-specific microglial accessibility excess **in regions of
> moderate-to-high local peak density**; in the lowest-density quartile there is
> no detectable advantage."
>
> **Corrected:** the excess is present and strongly positive **across every
> stratum of pooled local density, post-C3 distance and promoter degree**. It
> varies mildly — larger at short range and at high-degree promoters — but does
> not disappear anywhere.

The superseded microglia-only table is retained in the result JSON, explicitly
labelled non-authoritative, so the figure I previously published stays traceable
rather than disappearing.

## Unchanged

Claim scope is exactly as before: a P1S pass establishes **internal microglial
substrate compatibility** relative to same-study comparators and the frozen
geometry null. Not independent external corroboration, not donor-independent
replication, not multi-source replication, not causal enhancer–gene assignment.

Also withdrawn: my two "stale firewall" warnings. Those applied to the older copy
on my own execution branch; the canonical firewall was already repaired, with V2
named as current P1S authority and lineage defined by live canonical HEAD rather
than a fixed base SHA. I should have re-read canonical before reporting them.

`E2_NOTT_CANDIDATE` not instantiated. P3 untouched, still blocked on exact
GSE73721 byte authentication. `TRAINING=OFF`. `TD60=BLOCKED`.
