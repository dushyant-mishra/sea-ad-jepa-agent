# JEPA v2 Translational Actionability Audit

This audit asks whether the 2,957-gene SEA-AD JEPA feature space contains real-world pharmacology and biomarker handles.

The goal is not to force the model to prefer druggable genes during representation learning. The biology model should remain honest. These annotations belong in the downstream intervention-ranking layer, where model-implied targets are filtered by practical translational constraints.

## Inputs

- JEPA feature space: `data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad`
- v1 gene hypotheses: `results/tables/v1_hypothesis_candidate_genes.csv`
- AT8 pseudobulk gene rankings: `results/tables/microglia_pvm_percent_AT8_gene_rankings.csv`
- Human Protein Atlas protein-class annotations:
  - FDA approved drug targets
  - predicted secreted proteins
  - predicted membrane proteins

## Summary

| Metric | Value |
|---|---:|
| JEPA genes | 2,957 |
| HPA FDA drug targets | 136 |
| HPA predicted secreted proteins | 105 |
| HPA predicted membrane proteins | 735 |
| FDA target and membrane protein | 66 |

## Category Counts

| Category | Genes |
|---|---:|
| biology_first_hard_target | 2,092 |
| surface_target_candidate | 669 |
| known_drug_target | 70 |
| actionable_surface_drug_target | 66 |
| secreted_biomarker_candidate | 60 |

## Highest-Priority Biology-Led Candidates

The strongest candidates that combine v1 SEA-AD biological signal with translational annotations are:

| Gene | Interpretation |
|---|---|
| PTPRG | Strong AT8-associated v1 candidate and predicted membrane protein; surface-target hypothesis, not currently marked as HPA FDA target. |
| CHI3L1 | Strong AT8-associated v1 candidate and predicted secreted protein; biomarker-oriented hypothesis, relevant to YKL-40-style CSF readout thinking. |
| MRC1 | Vascular/barrier myeloid candidate and HPA FDA/membrane target; practical intervention handle, but v1 biology is weaker than PTPRG/CHI3L1. |
| DRAM1 | AT8-associated candidate and predicted membrane protein; mechanistic surface-associated follow-up. |
| S100A4 | AT8-associated candidate and predicted secreted protein; biomarker/actionability follow-up. |
| P2RY12 | Homeostatic microglia candidate and HPA FDA/membrane target; especially attractive because it is microglia-relevant and pharmacologically tractable. |
| TNFRSF11B | AT8/inflammatory candidate and predicted secreted protein; candidate soluble inflammatory readout. |

## Caution

Rows with high translational bonus but weak v1 biological evidence should not be promoted as top AD mechanisms yet. They are useful as assay/drug-target handles only after the biology-led candidates are evaluated.

The correct use of this table is:

1. Keep JEPA/Graph-JEPA representation learning biologically unconstrained.
2. Use the translational matrix after model inference to rank model-implied interventions.
3. Prefer candidates that combine pathology-relevant model signal, membrane/drug-target status, and biomarker readout potential.
4. Validate prioritized candidates against external perturbation, spatial, IHC, or independent-cohort data before making causal claims.

## Outputs

- `results/tables/jepa_v2_translational_actionability_matrix.csv`
- `results/tables/jepa_v2_translational_actionability_summary.csv`
