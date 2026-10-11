# Macha execution contract — V2 cross-platform deterministic finalization repair

Lane: synthetic/V79 only. Target discovery untouched.

Controller authority: PR #290 comment `6115051726`.

Current terminal:
`CONTRACT_V2_FINALIZATION_BLOCKED_ON_CROSS_PLATFORM_BYTE_REPRODUCIBILITY__NO_CANONICAL_WORLD_LAUNCH_AUTHORITY_YET__NO_WORLDS__NO_BENCHMARK__NO_QUALIFICATION_FITS__TRAINING_OFF`

## Allowed work
Work only on PR #290 / branch `feat/v79-v2-core-contract-final-20261011`.

Required repair:
1. Treat accepted V2 draft as immutable required input:
   `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json`
   SHA `cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3`.
2. Hash-check the draft before any finalization.
3. Load accepted draft bytes/content directly.
4. Construct final V2 only by applying the controller-approved finalization-field transformation.
5. Do not recompute SciPy/statistical-library-derived values already accepted in the draft.
6. Do not round or change the accepted draft.
7. Retain the existing semantic/tamper/legacy-authority tests.
8. Add/retain Linux and Windows CI proving the same final bytes and SHA from the same accepted draft input.
9. V1 and V2 draft remain non-authoritative; PR #289 is closed and non-canonical.
10. Do not generate qualification worlds, truth tables, manifests, benchmark outputs, or fits during this repair.

## Frozen scientific payload — may not change
- 12 worlds Q00-Q11.
- G=44 genes/world.
- 1,056 planned fits.
- 260 hard statistical gates.
- 28 hard rule gates.
- 4 LIMIT statistical gates.
- alpha=0.05/260.
- LIMIT only Q01 detection donor-SD bias, Q01 positive donor-SD bias, Q08 positive donor-SD bias, Q09 positive donor-SD bias; coverage stays hard.
- all Q11 gates hard.
- first scientific FAIL irreversibly locks NOT_QUALIFIED.
- Q11 operator perturbation = 0.5×donor SD, mild stress only.
- model terms/priors/parameterization/sampler/resource rules unchanged.

## Frozen evidence hashes — may not change
- G500 cache: `2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62`.
- support mask: `12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab`.
- masked replay: `caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683`.
- masking audit: `6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41`.
- S174 authority: `04035c070095e290b9df1a1f1926a635cca528804e644d341df06b82a572d288`.
- operator bridge: `b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92`.

## Frozen model
Detection:
`detected ~ quadratic(log_library) + broad_class + source + donor_within_source`

Positive:
`log(count)|count>0 ~ Normal(quadratic(log_library) + broad_class + source + donor_within_source, sigma)`

Operator, donor×class, source×class, free matrix/dataset ID remain out.

Source wording must remain: predictive/acquisition-source structure among estimable measured comparisons; not universal biology, not causal, not a biological mechanism; single-source cross-source estimands are UNDEFINED.

## Verification required before report-back
- RED record for deterministic-finalizer/cross-platform tests if new tests are needed.
- Linux GREEN proving final SHA.
- Windows GREEN proving the identical final SHA.
- builder/finalizer check proving the accepted draft is not modified.
- launch gate accepts exactly the repaired final V2 and refuses V1/V2 draft/tampering.
- no scientific field differs from accepted V2 draft except controller-approved finalization fields.
- `qualification_worlds_generated=0` and `qualification_fits_run=0`.

## Stop condition
After cross-platform GREEN, STOP and report:
- final head;
- final contract path and SHA;
- exact transformation fields;
- Linux run/job/test count/SHA;
- Windows run/job/test count/SHA;
- proof draft SHA unchanged;
- proof legacy authorities rejected;
- confirmation no worlds/benchmark/fits generated.

Do not proceed to world generation without a new explicit controller ruling.

`training_authorized=false`