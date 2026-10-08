# JEPA new-chat handoff — V24 current state — 2026-09-24

Status: CURRENT / NO TRAINING OR N1 AUTHORITY.

## Read this first

This is the V24 successor to V23. It records the live September 24 experimental changes, independent red-team integration, and FULL104 adapter consolidation. Historical V23/V22 documents remain evidence but are no longer the startup snapshot.

## Immutable boundaries

TRAINING=OFF. AUDIT_B_N1=UNOPENED. PROTECTED_FULL104_OUTCOMES=UNOPENED. D_SHARED_G5=UNOPENED. RARE_TAIL_MOLECULAR=UNOPENED. THERAPEUTIC_RANKING=OFF.

Preserve the project order:
DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL.

Do not inspect confirmation data while open design choices could still change.

## Live integration state

- Experimental PR #77 is still draft and is the active experimental integration branch. Current head after independent red-team integration: c81ad41b485f16d4aa82dbe4cffca5d23aa93927.
- PR #101 was merged into #77 and made GSE178317 lane spread descriptive only: the four 10X lanes are not established independent biological replicates; biological uncertainty is NOT_ESTIMABLE from lane spread.
- PR #102 was merged into #77 and supersedes stale PR #100. It adds a matched-lane support gate: each usable target must have >=40 assigned cells total and >=10 target plus >=10 same-lane NTC cells in >=3 lanes; at least 30 targets must pass. The result scope is DEVELOPMENT only, not prospective confirmation or guide-identity validation.
- GSE178317 historical V1 effect producer is fail-closed. A new V2 descriptive producer requires the reviewed assignment receipt, recomputes matched-lane support, binds the reviewed GEX H5 SHA roots, refuses occupied output directories, and always reports biological_uncertainty_estimable=false.
- Full physical GSE178317 V2 assignment/effect results were NOT present in GitHub at the audited head. Do not promote smoke-run counts or the failed V1 10-cell assignment.
- PR #99 is stale relative to current #77 and must not be merged as-is.
- PR #100 is superseded by #102.
- FULL104 PR #83, including the #85 red-team child, is now merged into its parent branch at merge commit 64148023740d57777666faff15395262d4b0e3da. All five associated workflows were green. N1 remains explicitly unauthorized and all-104 raw-count reaggregation remains unproved.

## Eight-study status

GSE301119: physical identity/effect work PASS within stated two-donor limits; donor-aware transcriptome-wide effect work remains a physical next step.
GSE293118: PASS for the six currently measurable nominated engagements; broader regulatory-locus causality remains limited.
GSE311359: STOP for guide-level benchmark authority. The V1 producer collapsed three distinct BIN1 capture features under one name; needs authenticated feature-ID/protospacer/library/target mapping and a V2 physical rerun.
GSE254205: bulk arm usable; schema correction in PR #86 remains CPU-only until physical V2 rerun. Three other assays remain unprocessed.
GSE241858: qualified as clone-level design, two independent clones per genotype; within-clone replicates are not independent biological units.
GSE240609: authenticated descriptive 2x2 post-coculture microglia design with one sample per design cell; no biological uncertainty estimate. PR #94 physical V2 rerun pending.
GSE178317: guide reads recovered from SRA, but V1 caller failed. V2 caller is DEVELOPMENT only and now has matched-lane and biological-uncertainty guards. Full physical V2 result not yet qualified.
GSE175721: STOP. Guide reference exists, but no usable guide-to-cell assignment is deposited; the described tab-separated metadata file is missing.

## New reference/benchmark evidence

Claude acquired the CRISPRbrain catalog: 54 screens, including nine transcriptomic screens and 352 distinct perturbation targets. Treat these as externally processed reference/benchmark data, not independently re-derived truth. The GSE178317-related CRISPRbrain table is from the same experiment and is not an independent replication cohort.

A FULL104-vs-benchmark overlap receipt was produced. Gene-space support was measured, but donor/cell-line overlap and barcode overlap remain NOT_CHECKED. Therefore benchmark independence is not established yet.

## Feature identity

Cross-study feature contract now explicitly supports HGNC symbol, Ensembl gene ID and Entrez gene ID namespaces, with evidence-bound mapping and no synonym guessing. A genuine authenticated annotation release is still required before production cross-study mapping.

## Current live PRs that still matter

- #77 active experimental draft, current head c81ad41b485f16d4aa82dbe4cffca5d23aa93927.
- #86 GSE254205 V2 schema/assay-detection correction: physical V2 rerun pending.
- #91 GSE301119 lightweight SHA-bound guide/donor support audit.
- #92 GSE311359 duplicate-BIN1 STOP.
- #94 GSE240609 source-identity V2 gate: physical V2 rerun pending.
- #99 stale integration candidate; do not merge as-is.
- #100 superseded by #102.
- #83 closed/merged into its parent; N1 remains unauthorized.

## Immediate next work

1. Wait for/inspect the full physical GSE178317 V2 count/call result; independently verify count-stage receipt, NPZ binding, no overwrite, matched-lane support and assignment sensitivity before any effect execution.
2. Add a separate authenticated count-stage/input-binding gate for GSE178317 V2; current caller still accepts an NPZ and uses allow_pickle=True.
3. Finish donor/cell-line and barcode-overlap checks between FULL104 and benchmark datasets before calling the benchmark independent.
4. Finish the real frozen annotation release for HGNC/Ensembl/Entrez mapping.
5. Execute physical V2 reruns for GSE254205 and GSE240609 and process the remaining GSE254205 assays.
6. Keep GSE311359 and GSE175721 STOPs in force until the missing identity evidence is actually recovered.
7. Only after data/support/semantics/model-geometry authority is frozen may training authorization be reconsidered.

## Do not repeat

Do not restart historical T0/T1/C2, QID archaeology, Layer-2 shortcut discovery, corrected FULL104 source-repair archaeology, or prior synthetic anti-spoof reviews unless changed inputs require requalification.
