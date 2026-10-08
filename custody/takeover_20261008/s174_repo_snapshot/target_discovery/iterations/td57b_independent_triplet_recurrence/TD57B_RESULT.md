# TD57B result — independent donor-recurrent scale-free relational order survives

Status: `TD57B_INDEPENDENT_DONOR_RECURRENT_SCALE_FREE_RELATIONAL_ORDER_SURVIVES__NO_TARGET_AUTHORITY`
Date: 2026-09-08

Prospective freeze:
`dccf186868f5ff7070d7e6b32cbb0fef0a6d7cdb`

Panel-0 preserved before Panel-1 opening:
`a56398b2957ba2c263ec82f4715349ab77e79c86`

Case table:
`target_discovery/iterations/td57b_independent_triplet_recurrence/TD57B_CASE_TABLE.csv`

## Result

TD57B used two new independent disjoint-gene panels that do not overlap the TD56/TD57A ranking positions.

For each panel and source:
- cell-cell concordance distances were derived independently from X and Y gene views;
- anchored triplet relations compared only the **ordering** of distances;
- donor was the primary unit;
- two deterministic donor splits produced four half-cases/source;
- matched Y-cell nulls preserved donor/operator/depth/detection;
- null-specific Y measurability/ties were recomputed independently.

Final:
- Panel 0: HVS 4/4, NPH52 4/4, SEA_AD 4/4;
- Panel 1: HVS 4/4, NPH52 4/4, SEA_AD 4/4;
- total **24/24 PASS**.

Across all 24 cases:
- weakest observed - null_p95 margin: **+0.0375178074843**;
- weakest observed - null_max margin: **+0.0326836261591**;
- every case had identical observed vs null measurable-donor counts.

Observed median donor triplet agreement ranges:
- HVS: ~0.634 to 0.685;
- NPH52: ~0.656 to 0.697;
- SEA_AD: ~0.731 to 0.747.

## Artifact SHA-256

Panel 0:
- HVS result: `fbee6cef249533523ba97558f52f388a378c4e5aa86c5be630b0ed9d20085d2f`
- NPH52: `114cc044ae66fe5c530412c6ca2d9f469eaba048fe0b1f256e746fe0093a5557`
- SEA_AD: `d149a37c40c43d03c49c8e1783f87a233f64874ef920f8fabe0a9e3d0b846c1e`

Panel 1:
- HVS: `560e5fafc0844320e69854023c9a5b4f8728a463f95bb9fe4825b7593b01ff37`
- NPH52: `9b83565b2d6315c239f9a156bd90ae0cce4902cd5ed666a1cc24e08ef911ed98`
- SEA_AD: `110a3741b9f56030832fe8f003c2b4cd0dbc478416c2bdeb59b8f9b2deae01c6`

Exact local executor:
`1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e`

Exact fast wrapper:
`808fb293a87d0020adc0f332742f3fa9b99c9c8ec5a88e50504a719ad4183a70`

## Independent/self-audit checks

1. Vectorized concordance distance equals direct naive distance with max absolute difference **0.0** on synthetic and deterministic real-data checks in both panels/all sources.
2. HVS and NPH52 Panel-1 complete outputs are byte-identical under the slow base executor and fast wrapper.
3. SEA_AD Panel-0 and Panel-1 full replays are byte-identical to their first completed outputs.
4. Triplet populations and retained sample counts independently recompute exactly from donor×operator metadata.
5. Pair hashes were frozen before outcome.
6. Panel-1 outcomes remained unopened until Panel-0 three-source PASS and self-audit were preserved.
7. No labels/pathology/protected populations were used.

## Scientific interpretation

TD57B closes two important TD56 blockers on the 50k falsification archive:

### Donor-block recurrence
The relational signal is not an artifact of pooling all donors. It survives multiple deterministic donor halves in all three source families and two independent gene panels.

### Cross-source absolute scale is not required
The recurrent object can be expressed as **within-anchor ordering of relational distances**. This is invariant to strictly monotone transformations of the distance scale, so a relational objective does not need to assert that a numeric distance in HVS has the same absolute scale as one in SEA_AD.

This strengthens the case for local rank/affinity/neighborhood objectives rather than universal coordinate regression.

## What remains unresolved

TD57B does not establish:
- stable nearest-neighbor identity across disjoint views;
- that fine/local neighborhoods survive beyond coarse class structure;
- learned EMA-teacher geometry;
- partial-evidence student predictability;
- collapse resistance;
- production k/neighborhood size;
- full-reader qualification;
- JEPA training authority.

Therefore the next scientific gate is **local-neighborhood stability**, using fixed concordance geometry first, before any teacher-defined learned neighborhood is allowed to drive training.

Frozen terminal:
`TD57B_INDEPENDENT_DONOR_RECURRENT_SCALE_FREE_RELATIONAL_ORDER_SURVIVES__FREEZE_LOCAL_NEIGHBORHOOD_STABILITY_GATE_NEXT`
