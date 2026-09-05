# Protected-program family independence audit

Terminal: `IMPLEMENTATION_COMPLETE_AWAITING_INDEPENDENT_VERIFICATION`

Diagnostic label: `PROTECTED_PROGRAM_FAMILY_RANK_DEFICIENT_AND_TAIL_NONSPECIFIC`. This is a **diagnostic measurement, not a gate verdict**. No protected-program family was selected, redefined, added or removed, and no F1 gate was changed.

## Authority

- program weights SHA-256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`
- program registry SHA-256 `8d29cfe86518882492ab8e878b8a2f79b8425a61b79710d5b74a0cbf654ba729`
- frozen decision arithmetic matches its declared SHA-256: `True`
- source digest convention: `lf_normalized_bytes`
- registry re-verification: 20 recorded digests independently recomputed, all match = `True`

## Headline measurements

- gated families: **8**
- independent directions actually spanned: **7**
- exact linear relations among gated families: **1**
- smallest singular value: `2.416976e-15`
- families participating in that relation: `local_core`, `local_halo`, `core_halo`
- gated families byte-identical to an ungated family: `innovation_tail`
- most diffuse gated family: `innovation_tail` (support 29319, N_eff 11243.55)

## Program geometry

| program | gated | support | N_eff | N_eff (registry) | uniform | type |
|---|---|---|---|---|---|---|
| `broad_common` | yes | 29319 | 2555.87 | 2555.87 | no | continuous |
| `weak_distributed` | yes | 29319 | 2926.15 | 2926.15 | no | continuous |
| `local` | yes | 29319 | 654.98 | 654.98 | no | continuous |
| `local_core` | yes | 8 | 8.00 | 8.00 | yes | sparse |
| `local_halo` | yes | 64 | 64.00 | 64.00 | yes | sparse |
| `core_halo` | yes | 72 | 48.00 | 48.00 | no | sparse |
| `sparse_marker_like` | yes | 32 | 32.00 | 32.00 | yes | sparse |
| `innovation_tail` | yes | 29319 | 11243.55 | 11243.55 | no | continuous |
| `recurrent_5pct` | no | 29319 | 11243.55 | 11243.55 | no | rare-state |
| `recurrent_1pct` | no | 29319 | 11243.55 | 11243.55 | no | rare-state |

N_eff is `1 / sum(w^4)` over the L2-normalised weights, the registry's own definition. Every recomputed value agrees with the recorded value to float64 round-off, and every support count agrees with `weighted_address_count`.

## Exact dependence

| family | residual L2 | exact at float32 precision | reconstruction |
|---|---|---|---|
| `broad_common` | `6.483e-01` | no | — |
| `weak_distributed` | `6.508e-01` | no | — |
| `local` | `6.485e-01` | no | — |
| `local_core` | `1.823e-15` | **yes** | 1.732051·`core_halo` − 1.414214·`local_halo` |
| `local_halo` | `2.764e-15` | **yes** | 1.224745·`core_halo` − 0.707107·`local_core` |
| `core_halo` | `2.946e-15` | **yes** | 0.577350·`local_core` + 0.816497·`local_halo` |
| `sparse_marker_like` | `9.907e-01` | no | — |
| `innovation_tail` | `5.907e-01` | no | — |

Rank deficiency is a property of the set, not of one family. Each listed family is exactly reconstructible from the others because they jointly satisfy one linear relation; the audit does not assert which family is the redundant one, since that is a modelling choice rather than a measurement.

## What this does and does not imply

Holm family-wise error control remains valid: `True`.

Holm step-down controls FWER under arbitrary dependence, so the measured dependence is not a false-positive-rate defect. It is a power and interpretation issue. With rank deficiency 1, exactly one of the eight gated slots contributes no independent direction, yet it still adds gate-failure surface because no_contextual_minus_direct_degradation and no_qid_v2_program_negative_margin each require all eight families to be estimable, and it still consumes Holm multiplicity. The innovation_tail byte-identity finding is a separate naming/interpretation issue and does not itself reduce the rank of the gated set.

Gates that require all eight families to be estimable:

- `protected_program_family_estimable`
- `no_contextual_minus_direct_degradation`
- `no_qid_v2_program_negative_margin`

## Rare/recurrent threshold representability

The rare/recurrent distinction recorded in the registry is a cell-level threshold on the innovation score, not a distinct weight vector. The current program estimand aggregates addresses through the L2 weight vector only, so no threshold is applied anywhere in the gated path. The gated innovation_tail slot therefore measures the dense innovation direction, not a rare or tail-restricted subpopulation.

Recorded thresholds: `rare1_threshold` = 67.90415161132812, `rare5_threshold` = 47.82950477600094.

## Upstream provenance note

- upstream basis status: `STAGE81A3R_GLOBAL_DIMENSION_RANGE_CLOSURE_COMPLETE_NOT_FROZEN`
- upstream basis asset: `stage81a3r_global_dimension_range_closure_ordered_basis.npz` (SHA-256 `5ddee92a83cd4f54ae61a6c9ed192847ac8f941f725e5a5678512460f5308b84`; local path not published)
- registry claim limit: These are frozen diagnostic programs, not pathway annotations or production-target qualification.

## Explicit non-conclusions

- This audit does not claim the contextual target fails or succeeds.
- This audit does not select a replacement protected-program set.
- Holm family-wise error control remains valid under the measured dependence.
- No statement is made about any real F1 outcome, which does not exist.

## Firewall

| check | value |
|---|---|
| `dev_sealed_or_pathology_accessed` | `False` |
| `expression_read` | `False` |
| `model_forward_executed` | `False` |
| `model_or_checkpoint_read` | `False` |
| `outcome_or_endpoint_read` | `False` |
| `training_or_ema` | `False` |

Audit semantic root SHA-256: `efc4f7813d1883bd1190eba53003ca0f2f788d3855811076cce976bffe6b9315`
