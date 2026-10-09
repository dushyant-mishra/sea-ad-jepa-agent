# V61 — all 24 clusters: microglia are the **worst-matched** layer, and that is a decision point

**Date 2026-09-28. Branch `claude/v59-r3-audit-and-external-cis-20260928`, from
`476d229d`. `TRAINING=OFF`. `TD60=BLOCKED`. No regulatory molecular outcome
opened. No gene annotation joined.**

The five-cluster test said the enrichment was generic. The full 24-cluster sweep
says something sharper and worse.

---

## The result

165,891 candidate edges, identical for every mask. 1,658,910 distance-matched
null pairs, identical for every mask (common random numbers).

| rank | cluster | cell type | bins | both-acc | enrichment |
|---|---|---|---|---|---|
| 1 | 23 | Oligodendrocytes | 26,835 | 29.85% | **18.95×** |
| 2 | 10 | OPCs | 18,418 | 13.18% | 16.43× |
| **3** | **18** | **DOUBLETS — a technical artifact** | 24,430 | 22.64% | **15.84×** |
| 4 | 19 | Oligodendrocytes | 41,514 | 48.11% | 14.78× |
| … | | | | | |
| 21 | 15 | Astrocytes | 58,059 | 45.41% | 7.04× |
| **22** | **24** | **MICROGLIA** | **45,147** | **29.78%** | **6.35×** |
| 23 | 1 | Excitatory neurons | 64,877 | 43.19% | 5.77× |
| 24 | 2 | Inhibitory neurons | 74,884 | 45.74% | 4.93× |

**Microglia rank 22 of 24.** A **doublet** cluster — not a cell type, a technical
artifact of the assay — achieves **2.50× microglia's enrichment**.

### Controlling for mask size, which is the obvious objection

Enrichment is a ratio and falls with mask size: regressing enrichment on
`log(accessible_bins)` gives a slope of **−7.03**, so bigger masks score lower by
construction. Microglia's mask is mid-sized (45,147 bins, 13th of 24), so size
does not explain rank 22 — but the residual settles it:

| | residual |
|---|---|
| **Cluster24 MICROGLIA** | **−3.19 — the most negative of all 24** |
| Cluster3 Excitatory | −2.61 |
| Cluster4 Excitatory | −2.33 |
| … | |
| Cluster22 Oligodendrocytes | +3.24 |
| Cluster19 Oligodendrocytes | +4.65 |
| Cluster23 Oligodendrocytes | +5.75 |

**After size control, microglia are the single weakest cluster in the atlas —
rank 1 of 24 from the bottom.** Oligodendrocytes occupy all three strongest
positions.

### Abundance does not explain it

The tempting story is that bulk HiChIP reflects abundant cell types. It does not
survive: Cluster10 OPCs are **373 cells (0.5%)** and rank 2nd; Cluster18 doublets
are **419 cells** and rank 3rd; microglia are **4,655 cells (6.6%)** and rank
22nd. The ranking is not a headcount.

---

## What this means, stated no more strongly than the evidence allows

The earlier finding was "the enrichment is not microglia-specific." This is a
stronger and more specific statement:

> **Microglial accessible elements are the least well aligned with this bulk
> H3K27ac HiChIP contact map of any annotated cluster in the atlas, and the
> gap survives size control.**

I will not assert the mechanism. The most plausible benign reading — that
microglial enhancers are among the most cell-type-restricted in brain and are
therefore least likely to be captured in a bulk-tissue contact map — is
consistent with every number here, but it is a hypothesis, not a finding, and
this project's standard is not to assert mechanism ahead of evidence.

What *is* established is the operational consequence, and it is the one that
matters: **whatever the reason, the Corces HiChIP layer is the contact substrate
that fits microglia worst.**

## What this does to object `E`

`E` remains correctly constructed, fully public, DUA-free, contact-defined,
RNA-free and disease-locus-free. Nothing about the build is invalidated, and the
work order's design instinct — do not assume microglia-specific contact strength
— is vindicated twice over.

But the description has to narrow again:

- ~~a microglia-enriched contact map~~
- ~~the microglial slice of a generic regulatory contact map~~
- **the microglial slice of a contact map that fits microglia worst of all
  brain cell types**

`E`'s 49,401 edges are, by construction, the subset of microglial regulatory
elements that happen to sit in contact architecture the bulk assay could see —
which this sweep shows is the architecture microglia share *least* distinctively.
The selection bias is now quantified, not suspected.

---

## The decision this forces, which is not mine to take alone

The frozen stop conditions S1–S3 were about whether `E` could be *built*. It can,
and it was. They did not anticipate this question, because I did not anticipate
it when I froze them.

**My recommendation: do not build the benchmark's positives on `E`, and treat the
Corces contact route as answered in the negative — without opening Morabito.**

The reasoning:

1. The object exists and is clean, so this is not a failure of the acquisition,
   the freeze, or the construction. All of that worked.
2. But an instrument assembled to study *microglial* regulation, whose contact
   layer matches microglia worse than it matches a doublet artifact, is a poor
   instrument for that purpose — regardless of how correctly it was built.
3. Proceeding would mean planting synthetic positives on edges that are
   systematically the *least* microglia-distinctive available, then asking
   whether n=18 donors can detect microglial specificity through them. That
   stacks the deck toward a negative result for a reason that has nothing to do
   with the science being tested.
4. This is discoverable now, cheaply, before any of that effort — which is what
   the preterminal discipline is for.

**What I am not recommending:** abandoning the external-object strategy. The
strategy is sound and this sweep is evidence it works — it caught a substrate
mismatch before it could contaminate a result. What it argues against is *this
substrate for this cell type*, which is a much narrower conclusion than "no
public external object is usable."

**The honest alternative view**, which the user may prefer: `E` is exactly what
was specified, the work order explicitly disclaimed microglia-specific contact,
and the measured bias can simply enter the nuisance class and be carried. That is
a defensible position and I am not dismissing it. It requires accepting that any
result from `E` is conditioned on a substrate that disfavours the cell type of
interest.

---

## Self-audit

**Starting SHA** `476d229d`; ending SHA in the commit. **Changed files:** this
document, `results/v61/V61_CROSS_CLUSTER_SPECIFICITY_ALL24_V1.json` — classes
**docs**, **results**.

**The control that makes this credible.** Cluster18 is labelled `Doublets` in the
Corces cluster table — it is an assay artifact, not a biological population. It
was included because a comparison set should contain something that *ought* to
score badly. It scored 15.84×, third of 24. That is not a result I would have
predicted, and it is precisely why it belongs in the table: it shows the metric
is not simply rewarding biological coherence, and it gives the microglial number
a floor to be measured against that nobody can argue is special pleading.

**S-V61-3.** I froze S1–S3 around whether `E` could be built and not around
whether it would be *fit for purpose*. Both stop conditions I wrote were
satisfiable by an object that is useless for the question. A freeze should
contain at least one condition that tests the object against its intended use,
not only against its own internal coherence. That is a lesson about how I write
freezes, and it generalises beyond this object.

**Strongest criticism of this analysis.** The size control is a single linear fit
of enrichment on `log(bins)` across 24 points, which is a crude adjustment, and
the residual ranking depends on that functional form. The finding does not rest
on it alone — microglia rank 22 of 24 *before* any adjustment, and the matched
Cluster9 pair (44,358 vs 45,147 bins, 1.7% apart; 40.02% vs 29.78%) needs no
model at all — but the specific claim "most negative residual of 24" is
model-dependent and should be read as corroboration, not as the primary evidence.

**What remains unknown:** the mechanism behind the ranking; whether another
public contact substrate fits microglia better; the HiChIP donor key; UW/SEA-AD
donor-level overlap.
