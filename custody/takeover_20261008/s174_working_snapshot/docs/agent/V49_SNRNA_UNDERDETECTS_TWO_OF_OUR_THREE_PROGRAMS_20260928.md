# snRNA-seq systematically under-detects genes in two of our three programs

**Date 2026-09-28. Literature finding, independently verified. `TRAINING=OFF`.
Evidence class: LITERATURE — not confirmatory for our target, and not derived
from any project data.**

## The finding

Thrupp et al., *Cell Reports* 2020 — title literally
*"Single-Nucleus RNA-Seq Is Not Suitable for Detection of Microglial Activation
Genes in Humans."* Comparing microglia from single cells and single nuclei in
four human subjects, about **1% of genes are depleted in nuclei relative to
whole cells**, and that population is **enriched for microglial activation
genes — APOE, CST3, SPP1 and CD74 — comprising 18% of previously identified
microglial disease-associated genes**.

Verified by independent search, not taken from a single summary.

## Why it matters here specifically

FULL104 is **single-nucleus** data. Two of our three frozen programs contain
genes this paper names:

| program | named by Thrupp |
|---|---|
| Lipid / DAM (APOE, LPL, GPNMB, TREM2, APOC1, ABCA1) | **APOE** |
| Antigen presentation (HLA-DRA, HLA-DPA1, HLA-DMB, HLA-DMA, CD74, CTSS, IFI30) | **CD74** |
| Homeostatic (P2RY12, TMEM119, CX3CR1, GPR34, SALL1) | none named |

Both named genes are high-abundance anchors of their panels. CD74 is the most
abundant partner in the antigen program — the one the candidate-pool census
found unmatchable at the 99.6th–99.85th abundance percentile.

## The interpretive consequence, which cuts toward caution not pessimism

A weak or null result on the APOE/DAM or antigen programs **in single-nucleus
data is partly a measurement limitation and must not be reported as absence of
the biology.** This is the project's existing rule — do not upgrade "not
demonstrated" into "false" — with a concrete published mechanism behind it.

It also offers a candidate explanation for something already observed: the
count-based route's difficulty on exactly these programs, and the literature's
own inconsistency in recovering DAM signatures from human snRNA-seq.

## What it does NOT license

It does not rescue any failed test, and it is not evidence that the programs are
present. It is a reason a specific class of negative result is uninformative,
which is a different and weaker claim.

## Two companion findings from the same lane

**Handling artifacts reproduce "loss of the homeostatic program."** Marsh et al.
2022's ex-vivo activation (`exAM`) signature makes microglia lose homeostatic
markers, appears in human postmortem data, is induced by hours at room
temperature — and **does not correlate with recorded PMI**. Adjusting for PMI
and declaring the confound handled would be a false green. This is a real,
published instance of the NEG-2 nuisance class: a nuisance that the obvious
covariate does not capture.

**The cross-modal experiment we most need is unpublished.** No study tests
whether nucleus damage moves RNA and ATAC together in brain multiome. The
nearest measurement found ambient contamination near-independent between
modalities (Spearman 0.08) — in adipose, not brain. Separately, gene-activity
scores correlate only minimally with measured RNA within broad cell types, and
differential accessibility is depth-dependent. **Therefore a cross-modal test
built on gene-activity scores would be uninterpretable, and the defensible
route is peak-level and depth-matched.** That independently supports the
peak-level design choice in the Lane B probe.

## Source-quality caveat, carried from the lane

Only six sources were read in full; Cell, Nature, PubMed and medRxiv blocked
fetching, so most citations are search-snippet level. The Thrupp numbers above
were re-verified independently. Other figures in the lane report should be
re-checked at source before being used in a decision.

Full report and citations: `lane/laneH-literature-20260928` at `85625e23`.
