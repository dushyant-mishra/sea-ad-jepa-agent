# JEPA V57 — relational alternatives and donor-power closeout

Date: 2026-09-28  
Base: V54 / PR #193 head `9d4194114cd52835457c2808e4032128941be26d`  
Governance: `TRAINING=OFF` · `TD60=BLOCKED` · synthetic/technical only · no real regulatory biological outcome opened

## Purpose

After V54 nearly but not fully separated the frozen nuisance class, V55 and V56 tested two scientifically motivated relational successors rather than adjusting the V54 threshold. Both were prospectively frozen and both failed. V57 then mapped the donor-count sensitivity of the unchanged V54 method.

The exact local eight-file bundle is:

`JEPA_V55_V57_SYNTHETIC_CLOSEOUT_ARTIFACTS.zip`  
SHA-256 `0b5c860ecb3f641341f92c1c49facf513b4c7245b727d6fd4524be0825f55f70`

This branch SHA-pins that chat-custodied bundle rather than claiming its ZIP bytes are mirrored into Git.

## V55 — within-donor gene ordering

V55 asked whether, for each confirmation donor, the frozen cis model reproduces the ordering of the 18 gene-state coordinates better than 100 matched pseudo-cis models.

Result:

`robust_margin = -0.17632013201320135`

Mandatory-positive medians:

- coherent: 0.5778
- mixed: 0.5424
- sparse: 0.5756

Negative medians remain close to 0.5.

A donor-pair derangement mutation collapses the mixed-positive median to ~0.5124, confirming that donor pairing matters. A gene-label derangement drops the median to ~0.3278. Nevertheless, the unmutated positive is not separated from negatives.

Interpretation: within-donor gene ordering is not the right relational object. A low-dimensional state can move many genes together without creating a distinctive ordering among the genes themselves.

## V56 — donor-neighborhood geometry

V56 then tested a closer analogue of the historical relational target.

For each confirmation donor:

1. compute its RNA-state distances to the other 17 donors in 18-gene ordinal state space;
2. compute the analogous distance ordering from the frozen true cis prediction;
3. compare the two neighborhood orderings by Spearman correlation;
4. rank the true geometry against 100 fully matched pseudo-cis geometries;
5. average the 18 donor-level ranks.

Result:

`robust_margin = -0.23294829482948304`

Positive medians were substantially above null:

- coherent: 0.7851
- mixed: 0.7525
- sparse: 0.7627

but their lower tails overlap broad donor-global/locus-technical null tails.

Donor-label derangement collapses the mixed-positive median from ~0.7525 to ~0.1819, confirming that the geometry signal depends strongly on correct donor correspondence.

Despite being biologically responsive, this statistic is too variable at n=18 and is therefore RED.

## Why V54 remains the strongest candidate

V54's gene-level transported empirical rank remains the closest to qualification:

`robust_margin = -0.014301430143014326`

The more relational V55/V56 statistics were materially worse. Therefore the next question was not another statistic but power: can the frozen V54 method separate at the donor counts actually available?

## V57 — confirmation-donor power curve

Frozen method:

- development n = 12;
- 18 genes;
- 5 cis peaks/gene;
- 100 fully matched pseudo-cis modules/gene;
- ridge lambda 8;
- rank/ordinal transport;
- program-excluded QC;
- same mandatory positives and technical negatives;
- unchanged robust-margin rule.

Fresh 48-seed diagnostic power curve:

| Confirmation donors | Robust margin | Frozen V54 rule |
|---:|---:|---|
| 9 | -0.18493 | fail |
| 12 | -0.14422 | fail |
| 15 | -0.09015 | fail |
| 18 | -0.05671 | fail |
| 24 | +0.01018 | nominal pass |
| 30 | -0.03020 | fail |
| 36 | -0.00930 | fail |
| 48 | +0.01408 | nominal pass |

The non-monotonic values around zero at larger n show Monte-Carlo/seed uncertainty. They must not be interpreted as a precise n=24 threshold.

The scientifically important part is that the **actual resource scale fails**:

- GSE272082-like n≈9: fail;
- SEA-AD paired-myeloid donor scale n≈15: fail;
- Morabito n=18: fail.

A synthetic larger-n pass does not retroactively qualify a smaller real cohort.

## Morabito-sized precision run

To tighten the n=18 conclusion without changing the method, V57 ran 192 additional fresh seeds at exactly:

- development n=12;
- confirmation n=18.

Result:

`robust_margin = -0.02871287128712885`

Key boundary:

- mixed mandatory-positive q10 = **0.57948**
- donor-global technical q90 = **0.60820**

Other positives remain strong:

- coherent q10 = 0.75154; median = 0.87706
- sparse q10 = 0.66837; median = 0.79483
- mixed median = 0.72167

This confirms that the n=18 failure is not merely a 48-seed accident.

## Decision

The current cis-transport route is **biologically responsive but not sufficiently specific at the donor counts of the currently planned confirmation cohorts** under the project's frozen stringent synthetic gate.

Do not:

- move the V54 threshold;
- increase decoy count until the margin turns positive;
- spend Morabito as if n=18 had already qualified;
- open SEA-AD biological outcomes to rescue the result;
- interpret this as absence of regulatory biology.

The next useful step is to reduce reliance on learning the regulatory object from ~12 paired-Multiome donors in the first place.

Claude's stronger proposal should now be taken seriously:

**define the cis regulatory object from an independently sourced regulatory map if a scientifically suitable one exists, then test its transport prospectively.**

Before selecting such a map, complete the R3 regulatory independence/exposure ledger so “independent” cannot be assigned by memory or convenience.

## Exact local artifact hashes

- V55 producer: `be99b2ad85dd0aa7db469d70f9e0067fb49124de7cbac97bc280d2fbc75344bc`
- V55 result: `828488600d490ed28a75c865377eb22b8bec7daf4ba45702f933de9e9bfb3d83`
- V56 producer: `463c159eedee55de173b1f10dbcd3e4f9bf87105f7f78a76ed4b06c20fcc62ff`
- V56 result: `1d233dd15c0bda72d6d28574628fae1a7f341bd49031e69db696d64fd6b49157`
- V57 power producer: `a0fbdaf1939abc7a281a6c5f8ef48e523cf221bee976976d52b9944c8bb5da24`
- V57 power result: `8cae4bcf57faebfe72d99255081f4b8b31af3792e10cc713f83bf8d135e62ee1`
- V57 n=18 precision producer: `57428c81f7641dcc29912f20d4da3e5add3f107dcec8468864c7bfd13aace4fe`
- V57 n=18 precision result: `134b8a5f50e30f81519f4eb163360eae3af5193782b5038bcb78ee185ee3d906`

No protected biological outcome was opened.
