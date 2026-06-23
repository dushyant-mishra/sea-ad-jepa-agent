# Stage 30 graph controls report v1

## 1. Executive summary

Best condition: `stage27c_module_pca_ridge_reference` (`0.3267`).
Real graph: `0.3205`. Graph-specific pass: `False`.
Controlled interpretation: `real_topology_beats_strict_shuffle_but_identity_no_graph_remains_best`.

## 2. What was run

- Stage 27C module PCA-ridge reference loaded from frozen OOF outputs.
- Real consensus STRING/WGCNA graph smoothing.
- Identity/no-graph smoothing control.
- Zero-overlap degree-preserving strict-shuffled graph smoothing control.
- Matched 15-module, 8-component PCA-ridge readout under locked folds.

## 3. What was not run

- No external matrices or validation.
- No clean holdouts.
- No high-capacity GNN or architecture search.
- No in silico ablation validation.
- No manuscript claim update.

## 4. Locked benchmark policy

Pooled donor-level OOF Spearman; locked Stage 24 folds; five targets; threshold 0.3228; target degradation floor -0.02.

## 5. Stage 27C reference baseline

`stage27c_module_pca_ridge_reference = 0.3267`.

## 6. Graph assets used

```csv
condition,edge_file,n_nodes,input_edge_rows,self_loop_rows,mean_nonzero_neighbors,median_nonzero_neighbors,max_nonzero_neighbors,smoothing_alpha,notes,n_module_features,module_overlap_summary
v3_real_graph,results\tables\v2_graph_consensus_edges.csv,2957,114029,0,77.21981738248225,26.0,692,0.5,row-normalized one-hop adjacency; undirected symmetrization except identity control,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10
v3_no_graph,results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv,2957,2957,2957,1.0,1.0,1,0.5,row-normalized one-hop adjacency; undirected symmetrization except identity control,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10
v3_strict_shuffled_graph,results\tables\ablation_edge_sets\strict_shuffled_graph_edges_v1.csv,2957,114029,0,77.21981738248225,26.0,692,0.5,row-normalized one-hop adjacency; undirected symmetrization except identity control,15,antigen_presentation:10; at8_associated_first_pass:10; chemokine_migration:10; complement:9; disease_associated_microglia:13; homeostatic_microglia:10; inflammatory_signaling:11; interferon_response:10; lipid_metabolism:9; lysosome_phagocytosis:10; oxidative_stress:9; plaque_response:12; senescence_stress:10; synapse_pruning:9; vascular_barrier_myeloid:10
```

## 7. Graph-control construction

Fixed one-hop row-normalized smoothing with alpha `0.5`. Non-graph genes remain unchanged. Identity adjacency returns the original expression exactly. Module construction and PCA-ridge capacity are matched across controls.

## 8. Leakage and holdout controls

All scaling, PCA, and ridge fitting occur within training folds. No held-out target, external matrix, clean holdout, or model-selection dataset was used.

## 9. Mean pooled OOF results

```csv
condition,mean_pooled_oof_spearman,min_target_pooled_oof_spearman,n_targets
stage27c_module_pca_ridge_reference,0.3267024400121495,0.016077756403766325,5
v3_no_graph,0.3267024400121495,0.016077756403766325,5
v3_real_graph,0.32047382808545105,0.17454692720461681,5
v3_strict_shuffled_graph,0.2986088893388681,0.16223549660828185,5
```

## 10. Target-level results

```csv
condition,target,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse
stage27c_module_pca_ridge_reference,6e10/Aβ,percent 6e10 positive area_Grey matter,84,0.3347372684013365,0.3163520312175891,0.09975961956193147,0.5908527814398361,0.6954113538288077
stage27c_module_pca_ridge_reference,AT8,percent AT8 positive area_Grey matter,84,0.5284398096588033,0.6623974952216051,0.4280899577385401,0.35143710200981665,0.4386596361996292
stage27c_module_pca_ridge_reference,GFAP,percent GFAP positive area_Grey matter,84,0.30229826870507237,0.27877065050186,0.07752413383312962,0.4963336075201987,0.5980483240374914
stage27c_module_pca_ridge_reference,Iba1,percent Iba1 positive area_Grey matter,84,0.016077756403766325,-0.042985908308886815,-0.09295916718496233,0.359161712235905,0.459580488795249
stage27c_module_pca_ridge_reference,NeuN,percent NeuN positive area_Grey matter,84,0.4519590968917688,0.47243591481850106,0.20964454842080216,0.3896968592871398,0.4861320000855132
v3_no_graph,6e10/Aβ,percent 6e10 positive area_Grey matter,84,0.3347372684013365,0.31635203121758926,0.09975961956193147,0.5908527814398361,0.6954113538288077
v3_no_graph,AT8,percent AT8 positive area_Grey matter,84,0.5284398096588033,0.662397495221605,0.42808995773853986,0.3514371020098168,0.4386596361996293
v3_no_graph,GFAP,percent GFAP positive area_Grey matter,84,0.30229826870507237,0.2787706505018599,0.0775241338331295,0.4963336075201987,0.5980483240374915
v3_no_graph,Iba1,percent Iba1 positive area_Grey matter,84,0.016077756403766325,-0.042985908308886885,-0.09295916718496233,0.35916171223590504,0.4595804887952489
v3_no_graph,NeuN,percent NeuN positive area_Grey matter,84,0.4519590968917688,0.4724359148185012,0.20964454842080216,0.38969685928713993,0.48613200008551316
v3_real_graph,6e10/Aβ,percent 6e10 positive area_Grey matter,84,0.2953933380581148,0.23243842291455352,0.0483692737410536,0.6047455327869282,0.7149847197218108
v3_real_graph,AT8,percent AT8 positive area_Grey matter,84,0.4533967803989066,0.5468081619078683,0.29634088512046075,0.39217843638073807,0.486569600252171
v3_real_graph,GFAP,percent GFAP positive area_Grey matter,84,0.24108534980257165,0.21040214775236554,0.039886420845181014,0.5064758512850706,0.6101267652951509
v3_real_graph,Iba1,percent Iba1 positive area_Grey matter,84,0.17454692720461681,0.15380861404578391,0.0034502520962116368,0.338046606809809,0.4388429299536851
v3_real_graph,NeuN,percent NeuN positive area_Grey matter,84,0.43794674496304553,0.46597238787594714,0.2121409998542021,0.3949204488662029,0.4853636339162291
v3_strict_shuffled_graph,6e10/Aβ,percent 6e10 positive area_Grey matter,84,0.24094360635820594,0.2453485520413973,0.06013410268660857,0.6015909251867383,0.7105513651513441
v3_strict_shuffled_graph,AT8,percent AT8 positive area_Grey matter,84,0.4563126455401438,0.5378397412262182,0.283693826345206,0.3960315052365917,0.4909227518780778
v3_strict_shuffled_graph,GFAP,percent GFAP positive area_Grey matter,84,0.221666497924471,0.1741675131104464,0.02103925294671416,0.5112723438710453,0.6160860999351349
v3_strict_shuffled_graph,Iba1,percent Iba1 positive area_Grey matter,84,0.16223549660828185,0.12671080842774549,-0.014027373202098792,0.34123126565865125,0.4426744471125303
v3_strict_shuffled_graph,NeuN,percent NeuN positive area_Grey matter,84,0.4118862002632378,0.43589480019647014,0.18041900941636113,0.39719687275610677,0.4950384379270079
```

## 11. Pairwise graph-control deltas

```csv
comparison,left_condition,right_condition,left_mean_pooled_oof_spearman,right_mean_pooled_oof_spearman,delta_mean_pooled_oof_spearman
v3_real_graph_minus_stage27c_module_pca_ridge_reference,v3_real_graph,stage27c_module_pca_ridge_reference,0.32047382808545105,0.3267024400121495,-0.006228611926698435
v3_real_graph_minus_v3_no_graph,v3_real_graph,v3_no_graph,0.32047382808545105,0.3267024400121495,-0.006228611926698435
v3_real_graph_minus_v3_strict_shuffled_graph,v3_real_graph,v3_strict_shuffled_graph,0.32047382808545105,0.2986088893388681,0.021864938746582963
v3_no_graph_minus_v3_strict_shuffled_graph,v3_no_graph,v3_strict_shuffled_graph,0.3267024400121495,0.2986088893388681,0.028093550673281398
```

## 12. Bootstrap confidence intervals

```csv
condition,target,target_alias,n_bootstrap_resamples,spearman_ci_low,spearman_ci_median,spearman_ci_high,uncertainty_status
stage27c_module_pca_ridge_reference,6e10/Aβ,percent 6e10 positive area_Grey matter,500,0.12680542466465225,0.32524764100310166,0.49675646321070166,complete
stage27c_module_pca_ridge_reference,AT8,percent AT8 positive area_Grey matter,500,0.34312369549418287,0.5235017912110476,0.6869246495300898,complete
stage27c_module_pca_ridge_reference,GFAP,percent GFAP positive area_Grey matter,500,0.10183125205611307,0.303103517645933,0.4780124635702778,complete
stage27c_module_pca_ridge_reference,Iba1,percent Iba1 positive area_Grey matter,500,-0.20612358330901698,0.0067463137594792255,0.21946199220248874,complete
stage27c_module_pca_ridge_reference,NeuN,percent NeuN positive area_Grey matter,500,0.2623977942737456,0.454560178553151,0.6176853840344527,complete
v3_no_graph,6e10/Aβ,percent 6e10 positive area_Grey matter,500,0.12232498814640384,0.33573098378331123,0.5133201533284483,complete
v3_no_graph,AT8,percent AT8 positive area_Grey matter,500,0.31646020085529014,0.5284763571761436,0.7006598423068677,complete
v3_no_graph,GFAP,percent GFAP positive area_Grey matter,500,0.09425095766372245,0.2941611725100814,0.47255266451157246,complete
v3_no_graph,Iba1,percent Iba1 positive area_Grey matter,500,-0.2088136062855599,0.017525530009951232,0.2638092115982217,complete
v3_no_graph,NeuN,percent NeuN positive area_Grey matter,500,0.27055231724853324,0.4519148208726095,0.6126734343319151,complete
v3_real_graph,6e10/Aβ,percent 6e10 positive area_Grey matter,500,0.0665261022055579,0.288606854392912,0.4923389557456008,complete
v3_real_graph,AT8,percent AT8 positive area_Grey matter,500,0.2592050589327761,0.4490467858518943,0.6270637215442213,complete
v3_real_graph,GFAP,percent GFAP positive area_Grey matter,500,0.03433509600726094,0.23468149118049556,0.430454982117552,complete
v3_real_graph,Iba1,percent Iba1 positive area_Grey matter,500,-0.04316776811612432,0.17930561600940198,0.3868156635759838,complete
v3_real_graph,NeuN,percent NeuN positive area_Grey matter,500,0.25000686319407267,0.4221844019873755,0.6156384837972643,complete
v3_strict_shuffled_graph,6e10/Aβ,percent 6e10 positive area_Grey matter,500,0.03336224564519423,0.23424988545890618,0.4310704777602878,complete
v3_strict_shuffled_graph,AT8,percent AT8 positive area_Grey matter,500,0.2505981020452133,0.4546256081337001,0.6387965779192281,complete
v3_strict_shuffled_graph,GFAP,percent GFAP positive area_Grey matter,500,0.021023106154284446,0.22911330043542188,0.4244230865619026,complete
v3_strict_shuffled_graph,Iba1,percent Iba1 positive area_Grey matter,500,-0.0714452168242082,0.15555306831311688,0.36942847168584647,complete
v3_strict_shuffled_graph,NeuN,percent NeuN positive area_Grey matter,500,0.21019991622160078,0.39866388796074465,0.5675791561339858,complete
```

## 13. Pass/fail decision

```csv
condition,real_mean_pooled_oof_spearman,stage27c_reference_mean,official_threshold,real_minus_stage27c_reference,real_minus_no_graph,real_minus_strict_shuffled_graph,real_meets_stage27c_reference,real_meets_official_threshold,all_five_targets_reported,target_degradation_gate_pass,no_heldout_donor_leakage,no_clean_holdout_use,no_external_matrix_use,real_beats_no_graph,real_beats_strict_shuffled,graph_construction_audit_pass,graph_specific_pass,controlled_interpretation
v3_real_graph,0.32047382808545105,0.3267024400121495,0.3228,-0.006228611926698435,-0.006228611926698435,0.021864938746582963,False,False,True,False,True,True,True,False,True,True,False,real_topology_beats_strict_shuffle_but_identity_no_graph_remains_best
```

## 14. Interpretation boundary

This stage tests internal graph-topology contribution only. It does not establish causality, validated targets, therapeutic relevance, external validation, or in silico ablation validity.

## 15. Recommendation for next stage

Graph-specific evidence did not pass. Preserve the controlled failure and do not promote graph-topology claims.

## Graph audit

```csv
check_id,status,passed,details
canonical_node_count_2957,pass,True,nodes=2957
all_conditions_same_node_count,pass,True,"{'v3_real_graph': (2957, 2957), 'v3_no_graph': (2957, 2957), 'v3_strict_shuffled_graph': (2957, 2957)}"
no_graph_identity_edge_count,pass,True,edges=2957
real_graph_nonempty,pass,True,edges=114029
strict_graph_edge_count_matches_real,pass,True,real=114029; strict=114029
strict_degree_sequence_preserved,pass,True,True
strict_zero_overlap,pass,True,0.0
strict_no_self_loops,pass,True,True
strict_safe_for_training,pass,True,True
```

## Real-graph target summary

```csv
condition,target,target_alias,n_donors,pooled_oof_spearman,pooled_oof_pearson,r2,mae,rmse
v3_real_graph,6e10/Aβ,percent 6e10 positive area_Grey matter,84,0.2953933380581148,0.23243842291455352,0.0483692737410536,0.6047455327869282,0.7149847197218108
v3_real_graph,AT8,percent AT8 positive area_Grey matter,84,0.4533967803989066,0.5468081619078683,0.29634088512046075,0.39217843638073807,0.486569600252171
v3_real_graph,GFAP,percent GFAP positive area_Grey matter,84,0.24108534980257165,0.21040214775236554,0.039886420845181014,0.5064758512850706,0.6101267652951509
v3_real_graph,Iba1,percent Iba1 positive area_Grey matter,84,0.17454692720461681,0.15380861404578391,0.0034502520962116368,0.338046606809809,0.4388429299536851
v3_real_graph,NeuN,percent NeuN positive area_Grey matter,84,0.43794674496304553,0.46597238787594714,0.2121409998542021,0.3949204488662029,0.4853636339162291
```
