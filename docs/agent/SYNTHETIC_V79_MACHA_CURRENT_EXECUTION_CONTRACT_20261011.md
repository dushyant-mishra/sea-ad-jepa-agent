# Macha current execution contract — synthetic/V79 lane

Date: 2026-10-11

Current terminal:
`CANONICAL_CONTRACT_V2_AUTHORITY_REPAIR_PENDING__PR291_FROZEN_WITH_24_TESTS_GREEN__NO_REALIZED_WORLDS__NO_BENCHMARK__NO_QUALIFICATION_FITS__TRAINING_OFF`

## Immediate assignment
Repair PR #290 contract finalization only.

Do not continue PR #291 generator semantics and do not emit any world bytes.

## Required inputs
Immutable inputs:
- PR #288 controller ruling `6114753697`;
- PR #290 controller ruling `6115051726`;
- accepted V2 draft payload SHA `cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3`;
- V1 historical contract SHA `70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540`;
- masked replay SHA `caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`;
- masking audit SHA `6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41`;
- support mask SHA `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`;
- frozen counts: 12 worlds, G=44, 1,056 fits, 260 hard statistical, 28 hard rule, 4 LIMIT, alpha=0.05/260;
- V2_CORE decision `FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY`.

## Required repair
- hash-check/load the accepted V2 draft directly;
- apply finalization-only fields;
- do not recompute accepted draft statistical report values during finalization;
- preserve `scripts/v79/v79_v2_core_launch.py::require_launch_authority()` as the sole launch gate;
- reject V1, V2 draft, PR #289 provisional authority, tampered contracts/sidecars/evidence bindings;
- prove exact same final bytes and SHA on Linux and Windows;
- retain all frozen scientific rules;
- stop for controller audit.

Do not alter/round the accepted V2 draft payload.

## PR #291 hold
PR #291 is frozen by comment `6115054911`.
Preserve head `714a36f3ca4f8c01e65f1fb2d5d80741a5b0af27` and run `38183909388` / job `114602059598`: 24 passed. No realized worlds/truth/benchmark/fits exist.

After a sole canonical PR #290 final authority is ratified:
- rebind/rebase #291 to it;
- use #290 launch gate only;
- regenerate Q10/Q11 pairing amendment against the new SHA while keeping identical scientific semantics;
- rerun generator tests Linux + Windows;
- stop before world realization.

Q10/Q11 preserved semantics: Q11 inherits Q10 all non-operator scientific truth and base observation noise; differs only by operator-offset streams 22/23; all Q11 gates hard.

## Firewalls
No world realization, truth-table emission, benchmark, qualification fits, corrected-TRAIN posterior, factorial science, TEST/Morabito/pathology, target discovery, Stage4/500K, or JEPA training.

`training_authorized=false`
