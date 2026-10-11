# Macha current execution contract — synthetic/V79 lane

Date: 2026-10-11

Current terminal:
`CANONICAL_CONTRACT_V2_AUTHORITY_REPAIR_PENDING__PR291_FROZEN_WITH_24_TESTS_GREEN__NO_REALIZED_WORLDS__NO_BENCHMARK__NO_QUALIFICATION_FITS__TRAINING_OFF`

## Immediate assignment
Repair PR #290 contract finalization only.

Do not continue PR #291 generator semantics and do not emit any world bytes.

## Required inputs
Treat these as immutable inputs, not generated outputs:

- controller masked-replay ruling: PR #288 comment `6114753697`;
- controller reproducibility ruling: PR #290 comment `6115051726`;
- accepted V2 draft payload:
  `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json`
  SHA `cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3`;
- V1 historical contract SHA `70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540`;
- masked replay SHA `caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`;
- masking audit SHA `6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41`;
- support mask SHA `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`;
- existing accepted draft rule counts: 12 worlds, G=44, 1,056 fits, 260 hard statistical, 28 hard rule, 4 LIMIT, alpha=0.05/260;
- V2_CORE decision `FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY`.

## Repair requirement
The final launch-authority generator must:

1. hash-check the accepted V2 draft bytes against `cbfa332b...`;
2. load that accepted object directly;
3. apply only controller-approved finalization fields;
4. never recompute the accepted draft's SciPy/statistical derived-report values during finalization;
5. preserve the accepted draft payload byte-for-byte as an immutable required input/reference;
6. use `scripts/v79/v79_v2_core_launch.py::require_launch_authority()` as the sole downstream launch gate;
7. reject V1, the draft itself, renamed legacy/draft authority, altered SHA sidecars, semantic mutations and evidence-hash mutations;
8. reproduce the exact same final Contract V2 bytes and SHA on Linux and Windows;
9. retain all substantive/frozen rules unchanged;
10. STOP for controller audit after GREEN.

Do not solve the cross-platform problem by modifying/rounding the accepted draft payload. The accepted payload is historical prospective evidence and must not change.

## TDD/CI
Use RED->GREEN.

Required cross-platform GREEN:
- Linux runner;
- Windows runner;
- same final SHA on both;
- same final bytes on both;
- semantic/tamper/legacy authority suite green;
- builder/finalizer check green;
- zero worlds and zero qualification fits.

Report every intermediate failure; do not hide earlier failed CI.

## PR #289 authority collision
The controller-side #289 authority SHA `8be47cb2...` is historical/provisional only after PR #290 ruling `6115051726`. Do not allow it to coexist as a second canonical authority.

The repaired and controller-ratified PR #290 final SHA must become the sole canonical launch authority before downstream generator work resumes.

## PR #291 hold
PR #291 is frozen by controller comment `6115054911`.

Preserve its completed engineering evidence:
- current head `714a36f3ca4f8c01e65f1fb2d5d80741a5b0af27`;
- latest observation-generator run `38183909388`, job `114602059598`: 24 passed in 0.33 s;
- zero realized worlds, truth tables, benchmark outputs or qualification fits.

Do not add further generator semantics while the authority repair is pending.

## After PR #290 becomes sole canonical authority
Only after controller ratification:

1. rebase/rebind PR #291 to the canonical final Contract V2 SHA;
2. replace its old `8be47cb2...` binding;
3. use the PR #290 launch gate as the sole gate;
4. regenerate the Q10/Q11 pairing amendment prospectively against the new canonical final SHA;
5. preserve the accepted pairing semantics exactly:
   - Q11 inherits Q10 design;
   - same structural-support mask;
   - same core planted parameters;
   - same donor effects/factors;
   - same factor-loading assignment;
   - same base detection/positive observation-noise streams;
   - Q11 differs only by operator-offset streams 22/23;
   - all Q11 gates remain HARD FAIL;
6. rerun all generator tests on Linux and Windows;
7. STOP again for controller authorization before physical world realization.

Do not silently reuse the old pairing amendment authority SHA `09f60d91817a041badaa4fc5108125f02a02d1ebbe8242a0f012aa6978d56f7c`; its scientific semantics are preserved, but its contract binding is obsolete once the final canonical Contract V2 SHA changes.

## World realization remains separately gated
Even after generator engineering is green, do not emit Q00-Q11 worlds until the controller explicitly authorizes realization.

When realization is eventually authorized:
- generate deterministic realized worlds under frozen seeds;
- structural measurement support is part of truth;
- unmeasured entries are not zeros;
- commit/hash-bind world truth and manifests before any benchmark or fit;
- no adaptive regeneration after inspecting outcomes;
- benchmark is still a later gate;
- qualification fitting is a still-later gate.

## Hard firewalls
Do not run or generate:
- realized qualification worlds now;
- truth tables/manifests now;
- benchmark;
- NUTS qualification fits;
- corrected-TRAIN posterior inference;
- factorial H0/H1/H2/H3/C_OBS/C_BIO science;
- old 18-fit campaign;
- Bernoulli V2/V3 rescue;
- TEST/Morabito/pathology;
- target-discovery work under this instruction;
- Stage4/500K;
- JEPA training/checkpoints.

`training_authorized=false`

## Required report back
Return with:
1. repair commit/head;
2. RED evidence;
3. Linux GREEN run/job/test count/final SHA;
4. Windows GREEN run/job/test count/final SHA;
5. proof the final SHA is identical across OSes;
6. proof accepted draft SHA stayed `cbfa332b...` unchanged;
7. proof finalization did not recompute/alter accepted draft derived values;
8. proof V1/draft/#289 authority are refused as current launch authority;
9. proof final launch gate accepts only the repaired final authority;
10. confirmation worlds=0, benchmark=false, fits=0;
11. STOP for controller audit.
