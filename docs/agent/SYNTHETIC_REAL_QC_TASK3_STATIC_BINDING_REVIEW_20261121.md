# Historical V74/V77 real-QC to Task3 parameter static binding check

Source-only review of unchanged historical bytes from [V74 #205](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/205), [V77 #239](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/239), and [Task3 #493](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/493). It does **not** reopen RNA, synthetic worlds, calibration payloads or controller truth.

The implemented V74 source already loads SHA-checked 50k-sample operator QC (real library depth, detected features and within-operator depth/detection association). `build_v73_full104_sharded_observer.py:139–147` calls `Q.by_operator`, `empirical_targets`, `operator_availability`, then `exact_counts`; `empirical_targets:83–97` uses frozen operator quantiles. The 96-feature panel is a projection from 41,238 real addresses, **not** a biologically qualified 41K synthetic world. `build_v77_extended_rna_observer.py:280–292` reuses these frozen functions. `v73_full104_population_geometry.py:55–106` has already implemented source/operator/donor-group quotas. `build_v77_real_calibration.py:68–122` measured class composition, gene abundance/detection and covariance, but does not prove class biology was instantiated. See completed reconciliation #239.

**New bounded finding:** the later Task3 calibration firewall at #493 has seven registered observation parameter families but still declares `OBSERVATION_PARAMETER_SEMANTICS_BOUND=False` and an empty authenticated issuer registry. None of the historical V74/V77 RNA generator sources checked here directly references a registered Task3 parameter name. This is **not** proof that a newly developed generator elsewhere cannot exist. It means **no trusted Task3 parameter-to-historical-producer binding has been demonstrated** at these pinned sources.

| Task3 parameter | Earlier physical analogue | Current cross-version verdict |
|---|---|---|
| OBS_DEPTH_SCALE | sampled library-size quantiles -> panel count | historical use verified; Task3 parameter unbound |
| OBS_DETECTION_SCALE | sampled detected-feature quantiles -> panel detection | historical use verified; Task3 parameter unbound |
| OBS_SUPPORT_RATE | operator available-address projection | partial structural support, not five-state rights; unbound |
| OBS_MISSINGNESS_RATE | per-operator unmeasured fraction | only historical 96-panel analogy; unbound |
| OBS_DONOR_OPERATOR_ALLOCATION | source/operator/donor quotas | historical population implementation; unbound |
| OBS_FRAGMENT_MULTIPLICITY | not checked in RNA-only producer | unbound; no claim about other modalities |
| OBS_MODALITY_AVAILABILITY | not checked in RNA-only producer | unbound; no claim about other modalities |

### Reproduce safely

`python -m unittest -v tests.production_synthetic.test_synthetic_observation_binding_static_v1`

`python scripts/production_synthetic/synthetic_observation_binding_static_v1.py`

The script only parses exactly pinned source files and the public-facing V74 authority *manifest*, verifies Git blob identities, and refuses stale or unrecognized changes. It never imports the inspected producer/calibration modules or decompresses real-data QC payloads. Tests use mutated source *strings*, not biological arrays. A passing test is **not** model, realism, calibration or production authority.

Next novel engineering scope requires separately reviewed semantics mapping in the actual future authorized generator, independent authenticated issuer, and five-state support/rights law from #531. No generator refit, new synthetic realization, V78/V79/V80 rerun, pilot or training authorized.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
