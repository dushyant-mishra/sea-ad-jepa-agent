# Outcome exposure declaration — Claude lane, 2026-09-24

Self-declaration of every perturbation outcome value this lane physically looked
at on 2026-09-24, so that no later confirmation design can claim them as
untouched. Written because only this lane knows what appeared on its screen.

Three families are already sealed in `KNOWN_EXPOSED_FLOOR` of
`src/sea_ad_jepa/perturbation/outcome_exposure_ledger_v1.py` by the review lane
on the same day. This document confirms those are correct and adds what is
missing.

## Already sealed, and correct

| study | arm | outcome family |
|---|---|---|
| GSE178317 | iTF_Microglia_Day8_CROPseq_CRISPRi | `target_engagement` |
| GSE178317 | iTF_Microglia_Day8_CROPseq_CRISPRi | `transcriptome_wide_DE` |
| CRISPRbrain | iTF_Microglia_Day8_CROPseq_CRISPRi | `published_DE` |

Confirmed against what was actually done. Per-target engagement log2FC for all
39 GSE178317 targets was printed, and 35 of them were joined value-by-value
against the CRISPRbrain published figures, including a rank correlation and a
separate analysis of the 18 targets carrying FDR >= 0.05 in the reference. These
are inspected at the individual-target level and can never be held out.

## Not yet in the ledger: summary-level exposure of eight further screens

Acquiring CRISPRbrain computed and displayed, **per screen**, the count of
targets whose own gene fell (`knocked_down_log2fc_lt_0`), the number of targets
with a self row, and the median self log2FC. Those are functions of the outcome
values. They were used to check that acquisition was correct — CRISPRi screens
showing knockdown and the CRISPRa screen showing the opposite — and not to
select, weight or tune anything.

Values seen, exactly:

| screen | seen |
|---|---|
| Glutamatergic Neuron-RNA-Seq-CRISPRa-2020 | 13 of 76 down |
| Glutamatergic Neuron-RNA-Seq-CRISPRi-2019 | 25 of 25 down |
| Glutamatergic Neuron-RNA-Seq-CRISPRi-2020 | 161 of 167 down |
| iPSC-RNA-Seq-CRISPRi-2019 | 23 of 23 down |
| iTF-Microglia-CROP-seq-CRISPRi | 27 of 30 down |
| iPSC-Microglia-CROP-seq-CRISPRi | 27 of 29 down |
| iTF-Microglia-CITE-seq-CRISPRi | no self rows |
| iPSC-Microglia-CITE-seq-CRISPRi | no self rows |

**No per-target value was displayed for any of these eight**, and no
transcriptome-wide effect for any target in them was read. The exposure is a
single aggregate count per screen.

Proposed classification: `DEVELOPMENT` for the `target_engagement` family of
those screens, not `INSPECTED`, since only an aggregate was seen. Their
`transcriptome_wide_DE` families remain `UNKNOWN` — genuinely unread — and
should not be downgraded on the strength of this document.

The review lane owns `KNOWN_EXPOSED_FLOOR`; this lane is declaring, not
amending. If the reviewing lane judges an aggregate count to be a full
inspection, the correct entry is `INSPECTED` and this lane does not contest it.

## What remains genuinely unread

No value was read from the transcriptome-wide differential expression of any
CRISPRbrain screen other than the Day-8 microglia screen. The tables were
downloaded, digested and row-counted; their contents were not opened. The
per-target effect tables for the neuron, astrocyte and iPSC screens are the
largest genuinely untouched outcome pool this project currently holds.

**That matters for benchmark design.** Because GSE178317 and the CRISPRbrain
Day-8 screen are now inspected at target level, they cannot serve as held-out
confirmation. Any prospective confirmation set has to be drawn from outcomes
this lane has not opened, and those are named above.

## Standing consequence

The value of this collection as a benchmark decays every time a lane looks at an
outcome. Acquisition and qualification necessarily consume some of it — checking
that CRISPRi produces knockdown requires reading knockdown — and that is a real
cost, not a free sanity check. Future acquisition should compute validation
statistics that are as coarse as the check allows, and declare them immediately,
rather than inspecting per-target values when a per-screen count would do.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_OUTCOMES=UNOPENED · THERAPEUTIC_RANKING=OFF
```
