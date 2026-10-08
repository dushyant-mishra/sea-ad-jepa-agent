# Teacher/Student V3 Self-Containment Repair — 2026-09-08

## Classification

`PACKAGING_REPAIR__RUNTIME_NOT_INVALIDATED__TRAINING_STILL_UNAUTHORIZED`

The prior V3 workflow correctly ran the six active tests against the full repository, but its review ZIP copied only the integrated-source manifest, the six active tests, and selected review/governance files.

That meant the ZIP was not independently importable/replayable even though repository CI was green.

## Root cause

The package builder confused:

- **controlling source closure** — the 20 integrated-source rows;

with:

- **independent replay closure** — every local Python import and every authority/evidence file required by the active tests and their validators.

Importing `sea_ad_jepa.v4` executes its package initializer, so an independent package needs the relevant package import closure. The C2 active test also needs the preserved K0/K1 JSON bytes or its historical replay cases skip.

The healthy-teacher and population freeze roots likewise point at manifests whose members must be packaged if the reviewer is expected to reproduce those roots.

## Files absent from the old ZIP

The old ZIP omitted 51 files required by replay/authority closure or requested as the new prospective relational adjunct:

1. docs/agent/HEALTHY_TEACHER_TRAINING_AUTHORITY_RECOVERY_20260907.json
2. docs/agent/JEPA_POPULATION_ACCESS_AND_SEALED_HOLDOUT_CONTRACT_20260907.md
3. docs/agent/JEPA_POPULATION_ACCESS_REGISTRY_MANIFEST_20260907.csv
4. docs/agent/JEPA_POPULATION_ACCESS_REGISTRY_V1_20260907.json
5. docs/agent/POPULATION_ACCESS_REGISTRY_AUTHORITY_VALIDATION_20260907.json
6. docs/agent/TEACHER_STUDENT_RELATIONAL_EXTENSION_V1_20260908.md
7. outputs/c2_t1_gradient_forensic_20260906/v3_exact_path/C2_V3_K0_HISTORICAL.json
8. outputs/c2_t1_gradient_forensic_20260906/v3_exact_path/C2_V3_K1_BACKWARD_AUTOCAST_DISABLED.json
9. scripts/agent/__init__.py
10. scripts/agent/validate_healthy_teacher_training_contract_v1.py
11. scripts/agent/validate_population_access_registry_v1.py
12. scripts/v4/__init__.py
13. scripts/v4/c2_mandatory_gradient_gate_v1.py
14. src/sea_ad_jepa/__init__.py
15. src/sea_ad_jepa/v4/belief_geometry.py
16. src/sea_ad_jepa/v4/calibration.py
17. src/sea_ad_jepa/v4/checkpointing.py
18. src/sea_ad_jepa/v4/conditional_predictability.py
19. src/sea_ad_jepa/v4/context_entities.py
20. src/sea_ad_jepa/v4/context_ledger_query.py
21. src/sea_ad_jepa/v4/context_reader.py
22. src/sea_ad_jepa/v4/contextual_query_local.py
23. src/sea_ad_jepa/v4/foundation_domain_support.py
24. src/sea_ad_jepa/v4/foundation_heterogeneity.py
25. src/sea_ad_jepa/v4/foundation_measurement_masks.py
26. src/sea_ad_jepa/v4/foundation_observation.py
27. src/sea_ad_jepa/v4/foundation_state_basis.py
28. src/sea_ad_jepa/v4/foundation_state_stability.py
29. src/sea_ad_jepa/v4/foundation_transfer.py
30. src/sea_ad_jepa/v4/foundation_uncertainty_mechanics.py
31. src/sea_ad_jepa/v4/full_transcriptome_synthetic.py
32. src/sea_ad_jepa/v4/intrinsic_cell_package.py
33. src/sea_ad_jepa/v4/losses.py
34. src/sea_ad_jepa/v4/measurement_state.py
35. src/sea_ad_jepa/v4/observation_calibration.py
36. src/sea_ad_jepa/v4/observation_process.py
37. src/sea_ad_jepa/v4/oof_covariance.py
38. src/sea_ad_jepa/v4/pca_summary.py
39. src/sea_ad_jepa/v4/perceiver_encoder.py
40. src/sea_ad_jepa/v4/predictor.py
41. src/sea_ad_jepa/v4/prospective_relational_teacher_student.py
42. src/sea_ad_jepa/v4/rare_state_audit.py
43. src/sea_ad_jepa/v4/rbb_adaptive.py
44. src/sea_ad_jepa/v4/rbb_core.py
45. src/sea_ad_jepa/v4/reproducible_state.py
46. src/sea_ad_jepa/v4/rlc_causal.py
47. src/sea_ad_jepa/v4/subspace_uncertainty.py
48. src/sea_ad_jepa/v4/successor_candidate.py
49. src/sea_ad_jepa/v4/telemetry.py
50. src/sea_ad_jepa/v4/validation_covariance.py
51. tests/test_teacher_student_relational_v1.py

The prospective relational files are new requested review material rather than evidence that the old V3 runtime depended on them.

## Repair

The workflow now:

1. packages all 20 controlling integrated-source rows unchanged;
2. packages the exact six active tests unchanged;
3. expands the healthy-teacher base manifest into its complete authority closure;
4. expands the population registry manifest into its complete authority closure;
5. includes the complete `src/sea_ad_jepa/v4/*.py` import/replay package plus package initializers;
6. includes the C2 gate module and exact K0/K1 evidence bytes;
7. includes the prospective relational extension document, pure mechanics module, and test;
8. writes `TEACHER_STUDENT_REPLAY_DEPENDENCY_MANIFEST_V1.csv` distinguishing replay dependencies from prospective relational material;
9. compiles every staged Python file;
10. runs the V3 freeze audit **inside the staged directory**;
11. runs all six active tests **inside the staged directory**;
12. runs the prospective relational test separately;
13. removes Python/pytest caches before manifest/root/ZIP creation;
14. refuses to package if either healthy-teacher execution-authority file appears.

This makes package self-containment an executable property rather than a prose claim.

## Relational extension included for prospective review

The package now includes a non-active relational design covering:

- direct 160-D teacher/student `cell_state`;
- exact distance+angle relational loss;
- donor×operator relational grouping;
- fine-matched qualification null;
- variance/spread/effective-rank collapse metrics with separately frozen calibration ratios;
- 20/40/60/80/100 evidence qualification schedule;
- preservation of the current frozen 60% training condition;
- separate future scale-up gate from 3,292 mechanics cells to the 4,553,407-cell FULL104 reader-fit population.

The relational extension is **not** part of the current `production_update`, source manifest, or execution authority.

## Scientific/runtime effect

No V3 active teacher/student runtime byte, frozen F1-B attack authority, healthy-teacher base rule, population rule, optimizer rule, EMA rule, masking rule, or training horizon was changed by the packaging repair.

Current execution status remains:

`TRAINING_UNAUTHORIZED`
