# Pre-Stage81A2 Virtual Harmonization

This layer references frozen SEA-AD, normal-reference and perturbation assets
without rewriting or physically concatenating them. It registers source hashes,
matrix semantics, exact feature namespaces, donor/specimen/section fields,
duplicate groups and candidate roles.

Full feature mappings are deterministic gzip sidecars under ignored
`data/processed/v4/pre_stage81a2/mappings`. Source identifiers are preserved.
Canonical symbols or Ensembl identifiers are populated only when present
exactly in the source; no fuzzy aliases or donor matching are permitted.
Unresolved identifiers remain explicit.

The virtual-concat manifest is a future execution contract, not a merged atlas,
gene-vocabulary freeze, donor split, or training matrix. Pathology-bearing
columns may exist in authoritative sources, but this builder never reads their
values.

## Non-equivalent modalities and roles

The 180-feature MTG MERFISH, 433-feature HIP/MEC MERSCOPE and 464-feature
Caudate Xenium panels are spatial measurements, not incomplete copies of the
36,601-feature RNA matrices. They require a dedicated spatial branch,
shared-feature projection, or explicit missing-modality mechanism. Zero-filling
them into the RNA vocabulary and presenting them as equivalent is prohibited.

The 218,882-feature MTG ATAC object is restricted to the regulatory-prior or
adapter pathway and is excluded from the RNA vocabulary. The Siletti object is
a clean holdout and may not influence training, vocabulary, architecture,
thresholds, checkpoint selection or hyperparameters. GSE243292 is restricted
to pathology-context validation; pathology fields cannot supervise the
pathology-blind foundation stage.

GSE301119 CRISPRa and CRISPRi have unequal feature universes. Later use must
align exact stable features and carry explicit measurement masks. The objects
must never be treated as identically measured matrices.

## Perturbation readiness gate

Acquisition provenance is not model readiness. Every perturbation asset must
separately resolve source archive members, matrix orientation, exact feature
identifiers, guide-to-cell assignments where applicable, controls, samples,
replicates and perturbation identities. Until those fields pass, the asset is
blocked from perturbation training even when its download and hash are valid.

## Stage-specific readiness

Readiness is evaluated separately for the foundation RNA review, regulatory
adapter review, spatial branch review and perturbation-controller review. A
spatial or perturbation blocker cannot by itself fail the foundation review.
The legacy `ready_for_stage81a2_review` field is retained only as a deprecated
alias for foundation-review readiness.

The foundation denominator is explicit: MTG foundation RNA, Immune
Microglia/PVM specialization, the three GSE97930 normal-training matrices and
the Siletti clean-holdout firewall. GSE243292 is represented only to verify its
pathology-context exclusion. Current source-integrity evidence means a valid
hash is present in a frozen acquisition ledger and the present path and size
match that ledger; the builder does not claim to recompute every large source
hash on each run.

Run:

```powershell
conda run -n sea-ad-jepa-v3 python scripts/v4/build_pre_stage81a2_harmonization.py
```

Stage81A2 review remains blocked while exact spatial section identity is absent
for any spatial source intended for section-aware evaluation. That blocker must
not be resolved by parsing partial identifiers or making fuzzy assumptions.
