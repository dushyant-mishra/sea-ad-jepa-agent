# Stage81A0 V4 Failure Registry and Design Contract

## Purpose

Stage81A0 freezes the scientific and engineering rules for a new Graph-JEPA v4 lineage. It is an audit and design stage only. No model is trained, no data are downloaded or transformed, and no v1-v3 or Stage75-79 artifact is changed.

The registry is deliberately source-grounded. A historical statement is marked confirmed, resolved, or documented risk only when a tracked repository source supports it. Missing evidence is recorded as `unresolved_from_current_repository_evidence` rather than inferred from general machine-learning expectations.

## Durable V3 Result

The v3 result to preserve is that self-supervised Graph-JEPA recovered disease-relevant microglial state geometry without training the foundation model as a disease-label classifier. Stage75-79 regulatory and perturbation outputs remain frozen calibration and provenance. Their technically valid perturbations produced extremely small latent shifts and did not establish regulatory control, biological rescue, or therapeutic relevance.

## Historical Lessons

The machine-readable registry covers data/preprocessing, leakage, representation learning, graph modeling, external pretraining, perturbation analysis, spatial risks, and engineering provenance. The central confirmed lessons are:

- anti-collapse losses must be evaluated on raw latents, with effective dimension and singular-spectrum telemetry on full datasets;
- pathology-supervised encoder tuning can damage the self-supervised manifold even when a supervised objective improves;
- expression-only is the required parent baseline because most v3 graph branches did not beat it, and the guarded positive graph gain was very small and internal;
- external pretraining did not close the Stage27C internal deficit under the tested domain, cell-type, gene-space, and normalization choices;
- feature-space omissions blocked regulators and targets from the v3 perturbation analysis;
- the 0.10 and 0.25 perturbation magnitudes were model-space inputs, not biological percentages or doses;
- Stage78 displacements were tiny and Stage79 retained graph-invariant and zero-variance control results;
- deterministic hashes, portable paths, separate implementation/freeze commits, and negative results are scientific requirements rather than packaging details.

Unresolved items are not all failures. They are decisions or audits that must be completed before the v4 stage that depends on them. Matrix/layer semantics, canonical gene identity, donor identity, seed stability, EMA stability, graph lineage, external equivalence, and all spatial-panel assumptions remain explicit unknowns.

## Frozen V4 Sequence

1. `v4A`: expression-only gene-token JEPA foundation model.
2. `v4B`: v4A plus a soft regulator-aware adapter and regulator-target masking.
3. `v4C`: spatial-panel teacher/student encoder plus section-local spatial context.
4. `v4D`: gated fusion of validated v4B and v4C branches.
5. `v4E`: native, biologically calibrated perturbation controller.

The multi-agent system is a post-model scientific council. It can inspect frozen results, maintain context packets, and propose experiments. It is not part of foundation training or checkpoint selection and cannot silently modify data, normalization, vocabulary, splits, thresholds, weights, or historical results.

## Pathology Firewall

Diagnosis, pathology burden, Braak, CERAD, GFAP, Iba1, NeuN, clinical status, and disease-state labels are forbidden from foundation-model training and self-supervised checkpoint selection. They may be used only after the foundation checkpoint and evaluation contract are frozen, in explicitly downstream analyses.

Donors are the biological split unit. Tissue sections are the spatial split unit. Test donors remain sealed until architecture, checkpoint selection, and self-supervised evaluation rules are frozen.

## Required Comparisons

Every branch must beat or justify itself against its simpler parent. Regulatory claims require no-prior, prior-weight-zero, TF-label-shuffle, edge-shuffle, and expression-matched random-target controls. Spatial claims require no-spatial, real section-local, shuffled section-local, distance-matched random-neighbor, and coordinates-only controls, with zero cross-section edges.

Pipeline integrity and biological value are separate pass criteria. A deterministic run that reproduces its inputs is not automatically biologically useful.

## Artifacts

- Contract: `configs/v4/stage81a0_v4_design_contract.yaml`
- Generator: `scripts/v4/build_stage81a0_failure_registry.py`
- Registry JSON: `results/v4/stage81a0_v4_failure_registry.json`
- Registry CSV: `results/v4/stage81a0_v4_failure_registry.csv`
- Compact report: `results/v4/stage81a0_v4_stage_report.json`
- Tests: `tests/v4/test_stage81a0_design_contract.py`

Run from the repository root:

```powershell
conda run -n sea-ad-jepa-v3 python scripts\v4\build_stage81a0_failure_registry.py --project-dir .
conda run -n sea-ad-jepa-v3 python -m pytest tests\v4\test_stage81a0_design_contract.py -q
```

## Scientific Boundary

This stage freezes a new self-supervised model-development contract. It does not establish improved biological representation, causal regulation, therapeutic validity, druggability, spatial interaction, or experimental validation.
