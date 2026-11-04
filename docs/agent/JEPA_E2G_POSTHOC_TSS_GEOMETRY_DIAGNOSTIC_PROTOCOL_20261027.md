# Follow-on sensitivity protocol (created after reading earlier Stage75/E2G results)

**Posthoc diagnostic, not preregistered biological inference.** This is only a
mechanics audit of source annotation and geometric confounding. No TF binding,
validated enhancer-to-gene link, new JEPA target, model selection or Stage4.

Inputs are the previously SHA256 verified stage75 ZIP (53 primary, 266 secondary,
91 peak scaffold), previously SHA256 verified seven external thresholded BEDPEs,
and local CSVs from the 2026-10-27 uploaded-bundle E2G interval audit.

## Source TSS compatibility

From the original Stage75C algorithm, `abs_distance_to_tss` is **absolute peak
midpoint minus its nearest GENCODE-v44 gene-level TSS**, not interval-to-TSS
distance. Use integer floor midpoint `(start+end)//2` and the E2G reported TSS
coordinate to calculate a comparable external `abs(midpoint - TSS)`; compare
the two values as an absolute discrepancy in bp. Neither gene identity nor
transcript origin is proven by coordinate similarity.

Collapse duplicated TF labels, E2G source rows and E2G regulatory predictions
when reporting physical-locus and gene-level disagreement. Classify discrepancies
at <= 500 bp, 501-2,000 bp, and >2,000 bp. These thresholds are descriptive,
chosen after seeing at least one PRDX1 mismatch. Recompute cross-context
recurrence with the >2kb discordant Stage75-peak/E2G-source annotations omitted
only as a sensitivity check, never as a retrospective selection gate.

## Motif-versus-other-peak geometry comparability

Analysis unit: each of the 85 unique Stage75 candidate peaks assigned to one of
the frozen 27 historical gene symbols. The exposure is `any Stage75 TF-motif
leading-edge hit` (56 versus 29), NOT actual TF occupancy. Outcome is the
previously defined binary same-symbol reciprocal >=50% overlap in all three
rE2G macrophage contexts and either scE2G macrophage reference.

Use deterministic one-to-one minimum-cost matching *within exact target gene*,
no replacement. Caliper each pair by width ratio <=2 and
`(TSS_midpoint_distance+1000)` ratio <=2, to avoid a spuriously precise near-zero
TSS ratio. Minimize sum of the two absolute log2 ratios; maximize number of
caliper-qualified pairs using explicit dummy-unmatched penalties. Report matched
coverage and residual geometry imbalance, not a p-value or biological effect.
If too few matches, state insufficient positivity; do not weaken calipers until
obtaining desired overlap counts. No cross-gene matching unless separately
labelled as a secondary nondeciding sensitivity design.

## Source dependency check

The E2G interval match does not query TF identity. Explicitly check that
assigning different TF names to a fixed gene+peak leaves every E2G overlap
feature invariant. Multiple TF labels at the same physical peak cannot count
as independent enhancer measurements. Preserve TF/motif class as historical
annotation only.