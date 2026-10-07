# JEPA target-candidate triage after TD34 genealogy audit

Date: 2026-10-06
Branch: `audit/td34-genealogy-s149-20261006`
Status: `MOVE_FORWARD_TO_LATER_RELATIONAL_LINEAGE__TD34_REMAINS_HISTORICALLY_INDETERMINATE__NO_TARGET_AUTHORITY`

## Decision

TD34 panel genealogy remains unresolved and must not be retroactively called S149-safe. The original TD34 producer corresponding to the preserved local script hash has not yet been recovered from Git history or Project sources.

However, TD34 is no longer treated as a mandatory scientific bottleneck because a later, cleaner relational lineage independently recreated the key relational hypothesis using prospectively hash-selected gene views from the exact 17,186 all-42-operator common-scalar intersection.

### TD56

TD56 prospectively defined two disjoint 512-gene views by ranking common-scalar gene address `g` with:

`SHA256("TD56S|gene|<g>")`

The first 512 addresses formed X and the next 512 formed Y. Gene membership therefore did not depend on expression, source, cohort, covariance, detection, phenotype, or outcome statistics.

### TD57B

TD57B used the same fixed hash ranking, but deliberately selected later, disjoint ranking positions:

- Panel 0 X: 1024..1535
- Panel 0 Y: 1536..2047
- Panel 1 X: 2048..2559
- Panel 1 Y: 2560..3071

Thus its four 512-gene views are mutually disjoint and disjoint from TD56/TD57A positions 0..1023. This is structurally S149-safe with respect to gene-panel selection: pooled study/cohort expression or topology did not choose panel membership.

TD57B historically passed 24/24 donor-half/source/panel cases, but this remains historical reproducibility evidence only.

## Critical later falsifier: V47

The old relational qualification used matched wrong-cell nulls. V47 later demonstrated that these controls are insufficiently specific for biology because wrong-cell reassignment destroys both:

1. true same-cell biology, and
2. residual same-cell technical/capture state not fully measured by QC.

A latent same-cell technical factor could therefore pass the historical relational gate. This means the TD56/TD57B/TD58/TD59 family is **not biologically qualified**, despite its cleaner panel provenance and strong recurrence.

The correct interpretation is:

- relational geometry is the strongest empirically replicated target *candidate family*;
- TD34 provenance no longer needs to block evaluation of that family;
- historical 24/24 passes cannot be promoted to biological target authority;
- the next qualification must discriminate biology from latent same-cell technical/capture structure.

## S149 implication

S149 adds a second independent constraint: study/cohort and observation process can dominate pooled geometry. Therefore the successor qualification must not pool across studies and call recurrence biological.

Any new relational adjudication must require, prospectively:

- donor-primary inference;
- explicit source/operator strata;
- within-study biological signal;
- transport across studies/operators;
- comparison against the strongest technical/capture shortcut;
- negative controls with hidden technical state, not only measured-QC controls;
- no panel selection using pooled expression/covariance/topology;
- no protected pathology or sealed outcomes.

## Current target ranking

1. `TD56 -> TD57B -> TD58 -> TD59 relational geometry`: strongest surviving empirical candidate family, clean later panel provenance, but biologically unresolved because of V47 technical-identifiability failure.
2. PR #163 value-blind `T_A/T_B1/T_B2/T_C`: still live for S149-aware real-RNA re-adjudication, but has less direct empirical support and the historical synthetic comparison was non-informative.
3. TD41/TD43: useful historical pair-order reliability evidence; no longer the highest-priority candidate because its TD34 upstream panel genealogy remains unresolved and later TD56/57 panels remove that dependency.
4. Historical named-program / fixed-coordinate / static/global families: remain closed or component-only according to prior audits.

## Next action

Resume at the later relational candidate, not TD34 outcome analysis.

Specifically: reconstruct and audit the post-V47 technical-twin / cross-modal identifiability work that was intended to distinguish biological relational state from latent same-cell technical state, then determine whether any already-completed successor gate resolves that identifiability problem. Do not rerun TD56/TD57B/TD58/TD59 and do not tune thresholds on their historical outcomes.

Training remains OFF. No target or representation winner is selected.
