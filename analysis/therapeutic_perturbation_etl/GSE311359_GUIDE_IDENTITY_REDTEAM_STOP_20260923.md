# Independent GSE311359 guide-feature red-team — STOP pending physical feature-ID authority

Date: 2026-09-23
Baseline: PR #77 @ f34fae312a3006e9eefaa1dfb85749037de9dddd
Scope: **lightweight committed producer metadata and source-code review only**.
No RNA matrix, GPU experimental file, protected FULL104 outcome or JEPA model opened.

## Newly confirmed defect

The committed `GSE311359_perturbation_identity.csv` is SHA-256
`1eeb4e40f14ec2ebe7472d7bb80769ae35bdb8df8ccbf4308493c8441eb363b5`.
It has 381 feature entries but **379 distinct guide-name strings**; the
name `BIN1` occurs **three times**. All three entries nominate the
same target, but the source feature IDs and independent guide sequence/library
authority were not present in these lightweight evidence files.

The producer loops over the 381 *feature positions* but later constructs
`ident = {row["guide_id"]: row ...}`, `kindex = {guide_name||sample: row ...}`,
and `row_of = {guide_name||sample: ...}`. Thus distinct capture features
sharing a guide name collapse to one sample-level accumulator. A cell whose
highest guide-count feature is any of the three `BIN1` rows maps to the same
name-based pseudobulk row, which does **not** prove three independently
identified guide effects. Downstream `n_guides`, sample-level guide variance,
and selected guide-level BIN1 effects cannot be treated as independently
qualified until the physical feature-ID/library relationship is reconstructed.

The recorded 27,737 confidently assigned cells, 105,509 assayed cells and
seven-sample structural counts remain historical producer evidence; no
independent wholesale recalculation is claimed here. The producer's reported
61/63 TSS engagement and other target engagement are **not** independently
requalified by this review. All GSE311359 guide-level effect authority is
on hold for a versioned corrected physical rerun because the same label-based
indexing affects provenance of the output matrix.

## Corrective implementation in this PR

* Assert nonempty **unique guide names and feature IDs** before allocating
  pseudobulk or creating output files.
* Across all seven samples, compare exact feature IDs, names, feature types and
  order; comparing names alone is insufficient.
* Refuse to overwrite V1 results; require a new empty output directory.
* Keep collision detection fail closed, **even if distinct 10x feature IDs
  exist**. A newly obtained feature ID is not itself independent proof that a
  protospacer/guide target was assigned correctly. Require authenticated
  feature-ID→guide-library→target mapping, then a reviewed V2 producer that
  uses canonical independently verified IDs end-to-end instead of a mutable
  guide-name key.

This new early-stop guard **is expected to STOP on the existing physical
GSE311359 feature table** until a source-authorized mapping is supplied. That
is the correct result, not a reason to relax it.

## Next physical action on Claude's laptop

Read only the seven authenticated feature TSVs and the original experimental
library/protospacer reference. Produce a SHA-bound seven-sample inventory of
the exact three BIN1 feature IDs, original names, feature types, possible
protospacer sequences and library mapping authority. If the library mapping is
absent, retain STOP for distinct-guide effects; an explicitly qualified
target-level pooled-BIN1 analysis would require its own estimand/validation and
must not assert three independent guides.

Regenerate all affected identity, guide×sample pseudobulk, control-relative
effect and engagement outputs only in a new versioned directory. Reproduce
all unaffected results within predeclared tolerances; independently red-team
permutation, collision, guide-role changes and duplicate-feature cases before
restoring benchmark authority.

STATUS: `PR77_PRODUCER_RESULTS_HISTORICAL__GSE311359_GUIDE_IDENTITY_REQUALIFICATION_REQUIRED`
`TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_OUTCOMES=UNOPENED`
