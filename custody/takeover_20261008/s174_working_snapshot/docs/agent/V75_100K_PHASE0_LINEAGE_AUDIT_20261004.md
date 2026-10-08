# V75 100K Phase-0 lineage audit — 2026-10-04

Base: `525611a8a70faf425c4f7f0f5d2354269beb3322` (`chatgpt/v74-synthetic-calibration-closure-20261003`).

This branch is independent of Macha reconciliation and is dedicated to the 100K FULL104-like architecture qualification.

## Phase-0 result

The existing V73/V74 synthetic implementation is not a simple winner-take-all lineage.

- V74 calibration closure carries the authenticated V2 RNA QC authority, empirical depth/detected-support consumption, QC binding in the promotion gate, restored `FULL104_N_CELLS`, and a successful hosted workflow that actually executed the 2,000-cell smoke.
- V73 stress-twin carries two pieces that V74 does not: the source-feasible zero-quota operator rescue and the independent fragment byte-linkage validator plus adversarial tests.

The V74 operator regression is smoke-scale specific: at 2,000 cells it realizes only 36/42 operators; at 10,000 it realizes 41/42; at 100,000, 500,000, and full 4,553,407 both lineages realize all 42. This matters because the 2K smoke is the authorization gate for the 100K run.

V75 therefore starts from V74 and must explicitly restore the two V73 protections before the 2K smoke can be authoritative.

## Known-defect disposition

1. Source-aware operator feasibility: **REGRESSED IN V74; V75 repair required.** The invalid global `n>=42` rule is gone, but V74 removed V73's within-source zero-quota rescue.
2. `FULL104_N_CELLS`: **PRESENT in V74.** Exact API behavior remains covered by the stress-twin tests.
3. QC payload digest/binding: **QUALIFIED in V74.** V2 compressed and canonical payload digests are checked before use, and the promotion gate binds the observer to the authority digest.
4. RNA observer consumes empirical QC: **behaviorally implemented in V74; mutation qualification required in V75.** Existing tests prove realized counts equal stored empirical depth/support targets, but do not yet prove that changing the consumed empirical QC distribution changes generated observations.
5. 2K smoke execution: **EXECUTED on hosted Actions run 37129241516.** The workflow generated 2,000 truth cells, RNA, paired multiome, fragments, resource receipt, and readiness receipt. However the gate did not require realized all-operator occupancy, so a successful smoke could authorize 100K while omitting six feasible operators.

## Claim boundary

The current stress ecosystem qualifies population/measurement simulation and scaling mechanics. It does **not** instantiate or qualify a 160-dimensional JEPA state representation. Current hidden biological truth contains constructed low-dimensional latent blocks and separate technical latents. V75 must not label 100K ecosystem success as 160-D JEPA-state stability.

A later state-model qualification must either identify an existing canonical JEPA state implementation and exercise it, or define a new state architecture prospectively under a separate authority contract.

## Governance

Training OFF. Stage 4 NOT AUTHORIZED. Real correspondence UNOPENED. Morabito PROTECTED. Recoverability TEST SEALED. No pathology variable is authorized as an observation operator or model input in this lane.
