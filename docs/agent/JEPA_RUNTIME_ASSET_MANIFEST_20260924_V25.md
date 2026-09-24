# JEPA V25 — current results, data, scripts and provenance manifest

As-of: 2026-09-24. **Source of truth for binaries is experimental PR #77 @ `67981c8ef6e158d865470e70bca81cbe289be3dd`, not `main`.** Re-fetch live heads before acting.

Repository: `dushyant-mishra/sea-ad-jepa-agent`.
Root for everything below: `analysis/therapeutic_perturbation_etl/`.

## Physically committed data — `outputs/gse178317/`

| file | bytes | SHA-256 (known prefix) | role |
|---|---:|---|---|
| `gse178317_cell_guide_umi_counts_v2.npz` | 3,121,266 | `170a16797d681124` | 58,302 x 81 legacy pickle-backed count artifact; exact full SHA below |
| `gse178317_cell_guide_assignments_v2.csv.gz` | 227,864 | `87d032b6a4b84367` | 11,775 lane-gated cell assignments |
| `gse178317_target_engagement_v2.csv` | 2,573 | `c6d6f0013d791147` | 39 targets, technical-well spread only |
| `gse178317_top_effects_v2.csv.gz` | 22,119 | `b55bd4b22c51fcf1` | top 25 up/down genes per target |
| `gse178317_vs_crisprbrain_engagement_v1.csv` | 2,231 | `fff45935c994d3fb` | 35 historically comparable targets (AARS and LSM6 fail matched-well support); SAME-experiment reference comparison; 33-target qualified result NOT YET CALCULATED |

**Integrity qualification:** This human-readable table contains abbreviated digests for several committed binaries and is **not** a standalone machine-verifiable manifest. Before claiming complete physical asset integrity, publish/locate a JSON or CSV inventory with full SHA-256, exact bytes, GitHub source commit and a runnable verifier for every committed binary. Do not reconstruct missing full digests from their prefixes.\n\nLegacy NPZ full SHA-256: `170a16797d681124a9083eb4170794b0f377b8a64ec3603e63b3435567fe3b4c`. It is NOT the new safe-format reissue.

## Physically committed CRISPRbrain data — `outputs/crisprbrain/`

| gzipped table | bytes | SHA-256 prefix | targets |
|---|---:|---|---:|
| `iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz` | 13,586,532 | `201e8fb28a63dfb9` | 39 |
| `iTF-Microglia-CROP-seq-CRISPRi.csv.gz` | 20,358,929 | `58c48fa4400d469a` | 31 |
| `iPSC-Microglia-CROP-seq-CRISPRi.csv.gz` | 16,133,002 | `818ae3c383811c94` | 31 |
| `iTF-Microglia-CITE-seq-CRISPRi.csv.gz` | 187,443 | `dcc204e858264e1e` | 31 |
| `iPSC-Microglia-CITE-seq-CRISPRi.csv.gz` | 188,965 | `d032364a457e1406` | 31 |

## Four neuron/iPSC reference tables — NOT committed, regeneration on demand

| raw CSV | bytes | full SHA-256 |
|---|---:|---|
| `Glutamatergic_Neuron-RNA-Seq-CRISPRa-2020.csv` | 86,055,877 | `bae3dee340bc24038f1e595c04a1eab98e35718f7c984622267110af9200e76f` |
| `Glutamatergic_Neuron-RNA-Seq-CRISPRi-2019.csv` | 49,409,869 | `976adc4bc08728f8c42b7f1624ed0093dede449e93cfe605cb532229e8e02dd0` |
| `Glutamatergic_Neuron-RNA-Seq-CRISPRi-2020.csv` | 163,362,857 | `cc50a1b837ed463cfd21e2b013f7b6dc82d07f57961b0218fde06edb6b8515fc` |
| `iPSC-RNA-Seq-CRISPRi-2019.csv` | 48,619,012 | `178dda2fbfcd00514003a8f702d4f5d7fe92fa89cb5e7afc249e590492e10955` |

Regeneration: `pip install crisprbrain && python analysis/therapeutic_perturbation_etl/scripts/acquire_crisprbrain_screens_v1.py --out-dir <new_dir> --full104-registry <path_to_stage81a2r_foundation_molecular_address_registry_candidate.csv>`. Verify all four full SHA-256 digests before use. Do not invent local paths to >30GB physical FULL104 arrays; they reside on Claude's GPU laptop/external disk.

## Producer and validation scripts

- `scripts/recover_gse178317_guide_assignments_v2.py`: SRA guide-UMI count stage; development-calibrated robust-z + Poisson caller; matched within-well support; full receipt binding and pickle-free new count outputs.
- `scripts/reissue_gse178317_safe_counts_v2.py`: authenticated conversion of known committed legacy NPZ to safe string/int arrays; no SRA re-extraction; new path only.
- `scripts/build_gse178317_intervention_effects_v2.py`: same-well target-vs-NTC descriptive pseudobulk, technical spread not biological SE.
- `scripts/build_gse178317_intervention_effects_v1.py`: intentionally FAIL-CLOSED, historical provenance only.
- `scripts/validate_gse178317_against_crisprbrain_v1.py`: SAME-experiment reference comparison, not independent replication.
- `scripts/acquire_crisprbrain_screens_v1.py`: 54-screen catalog acquisition, nine transcriptomic screens and overlap receipt; five microglia tables committed.
- `src/sea_ad_jepa/perturbation/cross_study_feature_contract_v1.py`: existing Ensembl/HGNC/Entrez identity + assay-mask contract.
- `src/sea_ad_jepa/perturbation/benchmark_domain_contract_v1.py`: cultured-vs-brain transport claim-scope gate; matching labels alone never authorize in-brain causal generalization.
- `src/sea_ad_jepa/perturbation/benchmark_target_holdout_v1.py`: reviewed target-heldout/donor-aware benchmark scaffold; only real donor units.
- `src/sea_ad_jepa/perturbation/outcome_exposure_ledger_v1.py`: frozen INSPECTED/DEVELOPMENT vs untouched outcome accounting.
- `src/sea_ad_jepa/perturbation/benchmark_screen_profile_baselines_v1.py` and `scripts/run_crisprbrain_target_profile_baselines_v1.py`: zero and other-target mean profile baselines, five target-disjoint folds, no own-target gene scoring.
- `BENCHMARK_BASELINE_INTEGRATION_20260924.md`: scope, provenance and stop conditions.
- `.github/workflows/perturbation-outcome-exposure.yml`, `perturbation-screen-profile-baselines.yml`, `perturbation-target-heldout-benchmark.yml`: integrated and green on audited experimental head.

## Receipts and authoritative interpretations

`evidence/gse178317_recovery/`: `gse178317_count_stage_receipt_v2.json`, `gse178317_guide_assignment_receipt_v2_lanegate.json`, `gse178317_intervention_effects_receipt_v2.json`, `gse178317_crisprbrain_validation_receipt_v1.json`, per-target engagement/reference CSVs. **The original V1 comparison receipt retains a superseded 'share no intermediate' assertion. Use `gse178317_crisprbrain_reference_comparison_receipt_v2.json` for machine-readable interpretation; V1 is historical only.**

Frozen count source roots: sgRNA library SHA `8de1e7e737c8c42ec9a7feff0d6e198b4f09808f09b6238e8b9dfbe276774942`; GEX L1 `0b1fd0ad00f3fabf170c4207ef3886c3bdc955256a59c10949dfa3b110cc82de`, L2 `6cb4df62065006d18cc3f0d3df42d7ac3ce875a41cbc59d7814e855862abb754`, L3 `1197f21919162472db9c7e998b1e16a422e18b86c78893d8fb669c6509a6b5f9`, L4 `9e9046e893c9f15e1697dcd55df8595890c38a407ea68a091286acaa28abfc86`.

## Automated test workflows on experimental head

At `67981c8ef6e158d865470e70bca81cbe289be3dd`, all **nine workflows completed SUCCESS**. Workflows present:
`Perturbation domain and gene-authority contracts`; `GSE178317 design-authority red-team`; `Cross-study feature-identity contract`; `GSE178317 authenticated safe count reissue`; `GSE178317 V2 lane-support independent red-team`; `Perturbation physical-authority red-team`; `Experimental outcome exposure ledger`; `Perturbation target-heldout synthetic benchmark`; `Perturbation screen-profile retrospective baseline`.

These are code/synthetic tests, not a physical safe-reissue receipt or scientific confirmation.

## Other existing project assets

See V24/V23 heavy-asset references and historical audit index. FULL104 heavy arrays and GPU execution live outside this chat; historical `stage81a3r_corrected_real_train.zip` is **not** FULL104. Uploaded calibration/checkpoint/expression archives may support offline checks, but must be authenticated by their manifests and must not silently override current frozen FULL104 lineage.
