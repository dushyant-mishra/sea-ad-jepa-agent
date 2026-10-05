# NIH-CARD E2 design: three pre-execution repairs

**Written for: the auditor deciding whether Stage 4 can be authorised.**

All three audit findings accepted. Stage 4 remains **not authorised** and no
correspondence outcome was opened. Canonical parent `67a482df`.

---

## F1 — pairing. You were right, and the truth is worse than the finding

You flagged that C-2 (donor agreement) is tautological given a `(sample, barcode)`
join key, and that C-4 (cohort) is largely inherited. Both correct.

Reading the depositor pipeline at its tagged commit
`0ddde6e6b27e6116ce48a6a31066a16170801bea` showed the third check is worse.
`scripts/atac_annotate.py`:

```python
rna_annot   = pd.read_csv(snakemake.input.annot_csv)
celltype_bc = dict(zip(rna_annot['atlas_identifier', 'cell_type']))
adata.obs['cell_type'] = [celltype_bc[x] for x in adata.obs['atlas_identifier']]
```

**The ATAC `cell_type` is copied from the RNA annotation through the very key under
test.** My V1 called C-3 "the strongest check of the five precisely because the two
labels come from different modalities" and set a threshold of ≥0.99. It is a copied
label. It is definitionally **exactly 1.0** and carries zero evidential weight. I
named the weakest possible check as the strongest.

All three are now demoted to corruption tripwires — they can only reveal a broken
join, never confirm a correct one.

### What the pipeline does establish

`scripts/filter_rna_atac.py` subsets **both** objects to the intersection of
`atlas_identifier` before merging:

```python
rna  = rna[rna.obs['atlas_identifier'].isin(atac.obs['atlas_identifier'])].copy()
atac = atac[atac.obs['atlas_identifier'].isin(rna.obs['atlas_identifier'])].copy()
```

So the composite bridge is not an assumption *we* introduce — it is **the deposit's
own definitional identity relation**. That reframes the question. The residual risk
is not "does `(sample, barcode)` identify a nucleus here" but "does *our
reconstruction* reproduce the pipeline's `atlas_identifier`", since the deposited obs
no longer carry it.

### The new primary gate: exact key recovery, not corroboration

The deposited identifiers are deterministically related:

```
RNA   AAACAGCCACGTGCTG-1_HBCC-1193
ATAC  CCTATAGCAATATAGG-1_HBCC-1193_HBCC-1193
```

The ATAC name is the RNA name plus `_<sample_id>`. **R-1** strips exactly one
trailing `_<sample_id>` and requires a strict **bijection** over all 1,501,089
nuclei — first verifying no `sample_id` contains `_`. **R-1b** independently tests
whether `atac.obs['barcode']` equals the RNA name namespace; if both recoveries
resolve, they must agree on *every* nucleus or execution stops.

This recovers the pipeline's own carried identifier by exact string identity rather
than corroborating a composite we assemble.

### The one genuinely independent witness

**I-1** correlates RNA `total_counts` against ATAC `Unique_nr_frag` per nucleus,
within sample, against a **within-sample permutation null** (200 permutations, seed
`20260929`). Permuting barcodes inside a sample holds sample identity exactly fixed
and destroys only the nucleus-level component — which is precisely the failure mode
the canonical receipt warns about. Neither quantity is copied across modalities by
any script inspected.

Its interpretation asymmetry is **frozen before the value exists**: far above null
corroborates; indistinguishable from null is **inconclusive, not refutation**, since
RNA and ATAC depth need not correlate within a nucleus. No threshold is predeclared,
because no defensible one exists.

### Pipeline lineage, and the gap I will not paper over

| | |
|---|---|
| Zenodo record | 20834804, **v3**, published **2026-06-24**, CC-BY-4.0 |
| Zenodo software link | `https://github.com/NIH-CARD/scMAVERICS/tree/main` |
| Only tagged release | `PFC_Cell_Reports` → `0ddde6e6b27e6116ce48a6a31066a16170801bea`, 2026-01-02 |
| `main` HEAD today | `dd6e2dd7de98f0c32b3fe64a0d58980adc9ca2a7`, **2026-09-28** |

**Zenodo links a moving reference.** `main` has advanced more than three months past
the record's publication, so the link as published no longer resolves to the
producing state. The tag predates the record by roughly six months. The pairing logic
quoted above was read at the tag and matches the deposited identifier structure
exactly — but that is **strong circumstantial lineage, not proof**. Zenodo names no
commit and the deposit carries no workflow provenance. The verdict label is
`PAIRING_KEY_RECOVERED_EXACTLY__PIPELINE_LINEAGE_CIRCUMSTANTIAL`, and the caveat
travels with every downstream claim.

---

## F2 — Stage 3 is now actually implemented

`scripts/v64/nihcard_e2_outcome_blind_preconditions_v2.py` implements what V1
promised:

- **promoter-fixed matched controls** — placed in hg19 source space at the matched
  separation (±10% or 10 kb), excluded if they overlap any E2 distal partner, then
  lifted hg19→hg38 through the same frozen liftOver v479 / minMatch 0.95 / single
  mapping / exact-length rule, and required to carry ≥1 Nott PU.1 peak **and** ≥1
  NIH-CARD consensus peak. Every drop reason is counted.
- **all 14 frozen features** for linked and control pairs under the V1 observable
  mapping.
- **the synthetic span reference**, regenerated from the committed qualification
  lineage by replaying `T.make_world` and `E.build_features` under the frozen 18
  donors × 24 seeds. The estimator is imported unmodified; nothing about it changes.
- **the predeclared IN_SPAN / OUT_OF_SPAN verdict**, with per-feature ranges,
  centroid Mahalanobis distance and the fraction beyond the synthetic p99 radius.

**Smoke-tested now** (needs no NIH-CARD bytes): 138,240 synthetic pairs × 14
features, p99 Mahalanobis radius **7.2571**.

### A partial span indication, computable today

Two of the fourteen features come entirely from committed artifacts, so they can be
checked before any data arrives:

| feature | real median | real IQR | synthetic range | IQR inside | fraction outside |
|---|---|---|---|---|---|
| `log_distance` | 11.951 | [11.290, 12.578] | [9.210, 14.509] | yes | **0.0000** |
| `promoter_degree` | 4.000 | [2.000, 7.000] | [2.000, 11.000] | yes | **0.2429** |

Distance sits comfortably inside. Promoter degree does **not**: 14.76% of E2 edges
have degree 1, below the synthetic minimum of 2, and 9.53% exceed the synthetic
maximum of 11, reaching 29. **Roughly a quarter of E2 edges lie outside the
estimator's promoter-degree support**, while the frozen IQR criterion still passes.

That gap is reported, **not** repaired. Changing the verdict rule now, having seen
which way it leans, would be exactly the post-hoc retuning the contract forbids.

---

## F3 — metacell precision, quantified rather than re-thresholded

I did not raise the cutoff to 8 or 10. The decision rule was frozen in the V2
contract **before** the study ran, and the study is outcome-blind.

**Analytic** — `Var(Fisher z) = 1/(m−3)`, verified by 20,000-replicate Monte Carlo:

| metacells *m* | SE(z) analytic | SE(z) Monte Carlo | weight `m−3` | 95% band of *r* at ρ=0 |
|---|---|---|---|---|
| **4** | 1.0000 | 0.9013 | 1 | **[−0.947, +0.946]** |
| 6 | 0.5774 | 0.5635 | 3 | [−0.810, +0.814] |
| 8 | 0.4472 | 0.4377 | 5 | [−0.700, +0.703] |
| 10 | 0.3780 | 0.3768 | 7 | [−0.631, +0.636] |
| 20 | 0.2425 | 0.2448 | 17 | [−0.447, +0.445] |
| 50 | 0.1459 | 0.1456 | 47 | [−0.282, +0.273] |

**At m=4 with a true correlation of zero, the observed correlation lands anywhere in
[−0.95, +0.95] in 95% of draws** — essentially the entire admissible range. Your
concern is fully justified, and now has a number.

**The frozen handling rule: precision weighting, not a cutoff.** Each donor
contributes with weight `m−3`, the Fisher-z information. A donor with 4 metacells
gets weight 1; one with 20 gets weight 17. This is the correct inverse-variance
weighting for the statistic being combined, needs no arbitrary line anywhere, and
degrades smoothly. Low-*m* donors are not wrong, they are imprecise — weighting uses
them at their true worth instead of discarding them.

The estimability floor `m ≥ 4` is retained because `m−3` must be positive.

**Predeclared fallback**: if the empirical split-half variance for `m ∈ [4,7]`
exceeds the analytic `1/(m−3)` by more than **2×**, donors with `m < 8` move to a
separately reported stratum and the primary uses `m ≥ 8` with the same weighting. The
trigger, the factor, the value 8 and the weighting are all fixed in the V2 contract
— 8 is not chosen after seeing a curve; it is what the rule selects if the measured
instability exceeds expectation.

The empirical half runs on a **declared-spent calibration set** of 2,000 random
(gene, peak-set) pairs containing no E2 gene, no E2 distal interval and no candidate
control — permanently excluded from the primary. Measurement precision is a property
of the assay, not of E2, so it can be calibrated on disjoint material.

---

## Self-audit lane (continuing from S29)

**S30 — I called a copied label the strongest independent check.** Not merely
non-independent: `atac_annotate.py` transports the RNA `cell_type` across the key
under test, so C-3 must return exactly 1.0. I predicted ≥0.99 for a tautology and
built a battery in which all three checks were vacuous. Caught by your audit and by
reading the depositor code — not by me.

**S31 — V1's barcode derivation was wrong.** It used `obs_name.split("-")[0]`, which
truncates `AAACAGCCACGTGCTG-1` to `AAACAGCCACGTGCTG` and silently discards the `-1`.
It happened to be harmless because every barcode carries `-1`, but it was a
reconstruction of a key by guesswork. Replaced by the exact suffix-strip rule.

**S32 — the frozen IQR span criterion is insensitive to out-of-range tails.**
Promoter degree passes the IQR test while 24.29% of edges lie outside the synthetic
support. Recorded for a successor contract to consider; **not changed now**, because
the direction it leans is already visible.

**S33 — Zenodo's software link is a moving reference.** It points at `tree/main`,
which has advanced three months past the record's publication. Recorded as a
provenance gap rather than treated as a version pin.

---

## Artifacts

- `results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V2.json` — supersedes
  V1's pairing gate and donor-support clause only; everything else stands unchanged
- `scripts/v64/nihcard_e2_outcome_blind_preconditions_v2.py` — complete stages 0–3
- `scripts/v64/nihcard_metacell_precision_qualification_v1.py`
- `results/v64/V64_NIH_CARD_METACELL_PRECISION_QUALIFICATION_V1.json` — analytic
  component **executed**

**Not yet runnable end-to-end:** Stage 0 fails closed on the local ATAC copy, which is
truncated at 6,059,254,368 of 14,508,702,462 bytes. A complete re-download with
full-byte md5 verification is required before stages 1–3 execute.

`TRAINING=OFF`. `TD60=BLOCKED`. `Morabito=PROTECTED`. E2 closed. Stage 4 not
authorised.
