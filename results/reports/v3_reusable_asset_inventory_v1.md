# V3 Reusable Asset Inventory v1

## 1. Executive summary

- Inventory rows: 80
- Immediately usable assets: 43
- Missing/deferred assets: 37
- Minimum-v3 blockers: 7
- No training was run.
- No packages were installed.

## 2. Assets immediately reusable from v2

| asset_id | category | asset_name | v3_role | size_or_count |
| --- | --- | --- | --- | --- |
| CORE-001 | core_v2_asset | SEA-AD H5AD file | primary v3 expression input | 458239253 bytes |
| CORE-002 | core_v2_asset | 2,957-gene feature universe | canonical gene universe and node order | 2957 rows; 130488 bytes |
| CORE-003 | core_v2_asset | identity edge file / canonical gene-index map | no-graph control and node map | 2957 rows; 130488 bytes |
| CORE-004 | core_v2_asset | real graph edge file | v3 first typed graph source | 114029 rows; 6391002 bytes |
| CORE-005 | core_v2_asset | real graph edge index | legacy loader-compatible edge index | 114029 rows; 3697740 bytes |
| CORE-006 | core_v2_asset | no-graph identity edge file | matched no-message-passing control | 2957 rows; 130488 bytes |
| CORE-007 | core_v2_asset | strict shuffled graph edge file | zero-overlap degree-preserving graph control | 114029 rows; 8192186 bytes |
| CORE-008 | core_v2_asset | strict shuffled diagnostics | strict shuffled provenance | 18 rows; 1270 bytes |
| CORE-009 | core_v2_asset | donor-level fold definitions if saved | prior donor fold artifact/reference | 3 rows; 571 bytes |
| CORE-010 | core_v2_asset | pathology target table | donor pathology targets and environment covariates | 84 rows; 21982 bytes |
| CORE-011 | core_v2_asset | baseline comparison table | v2 baseline reference | 35 rows; 9330 bytes |
| CORE-012 | core_v2_asset | final ablation comparison table | v2 final graph-control benchmark | 30 rows; 18432 bytes |
| CORE-013 | core_v2_asset | v2 scorecard table | Discovery Atlas scorecard seed | 2676 rows; 1641085 bytes |
| CORE-014 | core_v2_asset | v2 final candidate shortlist | Discovery Atlas candidate reference | 149 rows; 206916 bytes |
| CORE-015 | core_v2_asset | targeted manifold QC table | manifold QC reuse | 45 rows; 57655 bytes |
| CORE-016 | core_v2_asset | internal evidence scorecard | evidence-level discipline reference | 149 rows; 119339 bytes |
| MOD-001 | module_asset | module membership definitions | module branch and module baselines | 3666 bytes |
| MOD-002 | module_asset | module-mean baseline table | module mean benchmark reference | 35 rows; 9330 bytes |
| MOD-004 | module_asset | WGCNA/TOM adjacency table | typed WGCNA/TOM graph source | 100000 rows; 3358645 bytes |
| MOD-006 | module_asset | module summary feature table | module feature reuse | 89 rows; 45190101 bytes |
| GRAPH-001 | graph_source_asset | STRING external links | STRING graph source | 83164437 bytes |
| GRAPH-002 | graph_source_asset | STRING external protein info | STRING graph source mapping | 1970090 bytes |
| GRAPH-003 | graph_source_asset | STRING graph build script | STRING graph regeneration | 7272 bytes |
| GRAPH-004 | graph_source_asset | WGCNA/TOM graph file | WGCNA/TOM typed graph source | 100000 rows; 3358645 bytes |
| GRAPH-005 | graph_source_asset | WGCNA/TOM graph build script | WGCNA/TOM graph regeneration | 7108 bytes |
| ... | ... | ... | ... | ... | ... |

## 3. Module/WGCNA availability

| asset_id | asset_name | expected_path_or_package | immediately_usable | notes |
| --- | --- | --- | --- | --- |
| MOD-001 | module membership definitions | src/sea_ad_jepa/gene_sets.py | True | Contains MICROGLIA_GENE_MODULES definitions. |
| MOD-002 | module-mean baseline table | results/tables/discovery_baseline_predictive_representation_comparison.csv | True | Module mean was v2 best absolute predictor. |
| MOD-004 | WGCNA/TOM adjacency table | results/tables/v2_graph_wgcna_edges.csv | True | Available according to input availability report/path scan. |
| MOD-006 | module summary feature table | data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv | True | Pseudobulk/module-preserved processed table. |

## 4. Graph-source availability

| asset_id | asset_name | expected_path_or_package | immediately_usable | notes |
| --- | --- | --- | --- | --- |
| GRAPH-001 | STRING external links | data/external/string/9606.protein.links.v12.0.txt.gz | True | Raw STRING data available. |
| GRAPH-002 | STRING external protein info | data/external/string/9606.protein.info.v12.0.txt.gz | True | Raw STRING mapping available. |
| GRAPH-003 | STRING graph build script | scripts/build_string_graph.py | True | Reusable builder. |
| GRAPH-004 | WGCNA/TOM graph file | results/tables/v2_graph_wgcna_edges.csv | True | Available graph source. |
| GRAPH-005 | WGCNA/TOM graph build script | scripts/build_wgcna_tom_graph.py | True | Reusable builder. |
| GRAPH-008 | coexpression graph file | results/tables/v2_graph_wgcna_edges.csv | True | WGCNA/TOM serves as current coexpression graph. |
| GRAPH-010 | edge source/type labels | results/tables/v2_graph_consensus_edges.csv | True | Columns include in_string, in_wgcna, support, string_score, wgcna_tom. |
| GRAPH-011 | graph node-name mapping file | results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv | True | One row per gene index. |

If a source-specific WGCNA/TOM or STRING derivative is missing in a future environment, Stage 24 should not fail automatically; generate it locally or use the current real graph as the first v3 typed-graph source.

## 5. Benchmark package availability

| asset_id | asset_name | exists_or_available | v3_role |
| --- | --- | --- | --- |
| PKG-001 | sklearn | True | PCA, TSNE, ridge, ElasticNet, tree baselines |
| PKG-014 | networkx | True | graph utilities and strict shuffles |

Unavailable PHATE, scVI, DoWhy, EconML, or diffusion packages should be marked unavailable; do not install them in this stage.
This package check used the current `python` executable. Prior model training used the `sea-ad-jepa` Conda environment, so Stage 24 should explicitly choose and record the benchmark runtime environment before treating package gaps as infrastructure blockers.

## 6. Benchmark baselines immediately runnable

| asset_id | asset_name | immediately_usable | notes |
| --- | --- | --- | --- |
| BASE-001 | PCA + ridge | True | PCA and Ridge available through sklearn. |
| BASE-002 | t-SNE + ridge/kNN | True | Runnable if fold-safe embedding harness is added. |
| BASE-007 | raw expression ridge | True | Already implemented in v2 baseline harness. |
| BASE-008 | raw expression ElasticNet | True | Available through sklearn; needs locked harness extension. |
| BASE-009 | raw expression tree/boosting | True | Can use sklearn tree ensemble immediately if boosting packages are absent. |

## 7. Causal inference metadata availability

| asset_id | asset_name | immediately_usable | notes |
| --- | --- | --- | --- |
| CAUSAL-001 | donor metadata usable as environments | True | Available columns: ['Donor ID'] |
| CAUSAL-003 | sex | True | Available columns: ['Sex'] |
| CAUSAL-004 | diagnosis | True | Available columns: ['Cognitive Status', 'Overall AD neuropathological Change'] |
| CAUSAL-005 | pathology strata | True | Available columns: ['Braak', 'CERAD score', 'Overall AD neuropathological Change', 'Thal'] |
| CAUSAL-008 | adjustment covariates | True | Available columns: ['APOE Genotype', 'Age at Death', 'Braak', 'Sex', 'Thal'] |
| CAUSAL-009 | candidate treatment/exposure definitions | True | Shortlist can seed causal-hypothesis candidates. |
| CAUSAL-010 | causal evidence schema | True | Created in Stage 22B. |
| CAUSAL-011 | causal inference layer spec | True | Created in Stage 22B. |

## 8. Perturbation-data availability

| asset_id | asset_name | exists_or_available | immediately_usable | notes |
| --- | --- | --- | --- | --- |
| PERT-001 | Perturb-seq files | False | False | Future extension unless real perturbation dataset is present and overlap is audited. |
| PERT-002 | CRISPRi/CRISPRa files | False | False | Future extension unless real perturbation dataset is present and overlap is audited. |
| PERT-003 | public perturbation dataset references | True | False | Future extension unless real perturbation dataset is present and overlap is audited. |
| PERT-004 | fake perturbseq generator | True | False | Future extension unless real perturbation dataset is present and overlap is audited. |
| PERT-005 | perturbation benchmark script | True | False | Future extension unless real perturbation dataset is present and overlap is audited. |

Perturbation-supervised calibration is future-only unless a real Perturb-seq, CRISPRi, CRISPRa, or related dataset is present and gene overlap with the 2,957-gene universe is audited.

## 9. Missing/deferred assets

| missing_asset | category | blocking_level | suggested_action | notes |
| --- | --- | --- | --- | --- |
| WGCNA module eigengenes | module_asset | future_extension | defer_to_future_extension | Not found; generate or defer. |
| module-to-gene mapping file | module_asset | future_extension | defer_to_future_extension | Can be generated from src/sea_ad_jepa/gene_sets.py. |
| pathway graph file | graph_source_asset | future_extension | defer_to_future_extension | Missing/deferred; Reactome/KEGG/GO source can be generated later. |
| Reactome/KEGG/GO membership files | graph_source_asset | future_extension | defer_to_future_extension | Missing/deferred. |
| GRN / TF-target file | graph_source_asset | future_extension | defer_to_future_extension | Missing/deferred. |
| umap | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| openTSNE | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| phate | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| pydiffmap | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| torch | benchmark_package | minimum_v3_blocker | generate_or_restore_before_stage_24 | Import availability in the current Python environment. |
| torch_geometric | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| scanpy | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| scvi | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| xgboost | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| lightgbm | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| econml | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| dowhy | benchmark_package | future_extension | defer_to_future_extension | Import availability in the current Python environment. |
| UMAP + ridge/kNN | benchmark_baseline | minimum_v3_blocker | generate_or_restore_before_stage_24 | Requires umap package and fold-safe harness. |
| supervised UMAP if leakage-safe | benchmark_baseline | future_extension | defer_to_future_extension | Must be blocked until leakage-safe fit protocol is written. |
| PHATE + ridge/kNN | benchmark_baseline | future_extension | defer_to_future_extension | Package-dependent; do not install here. |
| diffusion maps + ridge/kNN | benchmark_baseline | future_extension | defer_to_future_extension | Requires pydiffmap or scanpy diffusion-map equivalent. |
| expression-only MLP | benchmark_baseline | minimum_v3_blocker | generate_or_restore_before_stage_24 | Requires a locked no-graph neural baseline. |
| module-only MLP | benchmark_baseline | future_extension | defer_to_future_extension | Needs module feature extraction harness. |
| autoencoder latent | benchmark_baseline | minimum_v3_blocker | generate_or_restore_before_stage_24 | Can be implemented without graph inputs. |
| VAE/scVI-style latent | benchmark_baseline | future_extension | defer_to_future_extension | Future extension if scvi available/installed later. |
| graph-only GNN | benchmark_baseline | future_extension | defer_to_future_extension | Requires torch_geometric and locked GNN baseline. |
| v3 no-graph | benchmark_baseline | minimum_v3_blocker | generate_or_restore_before_stage_24 | Minimum v3 control. |
| v3 strict shuffled | benchmark_baseline | minimum_v3_blocker | generate_or_restore_before_stage_24 | Minimum graph-specific control. |
| v3 real graph | benchmark_baseline | minimum_v3_blocker | generate_or_restore_before_stage_24 | Minimum real graph model. |
| batch labels | causal_inference_asset | future_extension | defer_to_future_extension | Missing expected columns among ['Batch', 'Specimen ID', 'batch', 'library_prep'] |
| cell-state cluster labels | causal_inference_asset | future_extension | defer_to_future_extension | Dedicated table not found; may be derivable from H5AD obs in Stage 24. |
| microglia/PVM labels | causal_inference_asset | future_extension | defer_to_future_extension | Dedicated table not found; may be derivable from H5AD obs in Stage 24. |
| Perturb-seq files | perturbation_asset | future_extension | defer_to_future_extension | Future extension unless real perturbation dataset is present and overlap is audited. |
| CRISPRi/CRISPRa files | perturbation_asset | future_extension | defer_to_future_extension | Future extension unless real perturbation dataset is present and overlap is audited. |
| public perturbation dataset references | perturbation_asset | future_extension | defer_to_future_extension | Future extension unless real perturbation dataset is present and overlap is audited. |
| fake perturbseq generator | perturbation_asset | future_extension | defer_to_future_extension | Future extension unless real perturbation dataset is present and overlap is audited. |
| perturbation benchmark script | perturbation_asset | future_extension | defer_to_future_extension | Future extension unless real perturbation dataset is present and overlap is audited. |

## 10. Recommended Stage 24 plan

1. Lock and materialize explicit v3 donor folds before any benchmark expansion.
2. Build a benchmark harness that first runs immediately available PCA, raw expression ridge/ElasticNet, and module mean baselines in the current environment.
3. Select and record the Stage 24 runtime environment, then enable torch-dependent expression MLP, autoencoder, v3 real graph, v3 no-graph, and v3 strict shuffled controls.
4. Add UMAP/t-SNE only with leakage-safe fold-local fitting; supervised UMAP remains gated until the leakage protocol is explicit.
5. Treat PHATE, diffusion maps, scVI, DoWhy, and EconML as optional/deferred if unavailable.
6. Generate missing module-to-gene and WGCNA eigengene tables from existing module definitions/WGCNA outputs where useful.
7. Keep perturbation-supervised calibration as a future extension unless real perturbation data are added and overlap-audited.
