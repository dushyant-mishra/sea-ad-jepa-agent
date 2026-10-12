# Macha execution contract — V2 cross-platform deterministic finalization repair

Synthetic/V79 lane only. Target discovery is separate.

Controller authority: PR #290 comment `6115051726`.

Current terminal:
`CONTRACT_V2_FINALIZATION_BLOCKED_ON_CROSS_PLATFORM_BYTE_REPRODUCIBILITY__NO_CANONICAL_WORLD_LAUNCH_AUTHORITY_YET__NO_WORLDS__NO_BENCHMARK__NO_QUALIFICATION_FITS__TRAINING_OFF`

Work only on PR #290. Treat accepted V2 draft `results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json` SHA `cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3` as immutable input. Hash-check it, load it directly, and create final V2 only by applying controller-approved finalization fields. Do not recompute SciPy-derived accepted draft values, do not round/change the draft, and do not change any scientific payload.

Preserve: 12 worlds, G=44, 1,056 fits, 260 hard statistical + 28 hard rule + 4 LIMIT gates, alpha=0.05/260, only the four approved donor-SD bias LIMIT gates, all Q11 hard, first-FAIL terminal lock, Q11 0.5×donor-SD mild stress, V2_CORE model/priors/parameterization/sampler/resource rules.

Preserve evidence hashes: G500 `2f922c08...`, support mask `12ad275e...`, masked replay `caf2413c...`, masking audit `6bd0bfc7...`, S174 authority `04035c07...`, bridge `b83c35e6...`.

Required proof: identical final bytes/SHA on Linux and Windows; accepted draft unchanged; final gate accepts only repaired final V2 and rejects V1, V2 draft, tampering; all semantic/tamper tests retained; worlds_generated=0; qualification_fits_run=0.

After cross-platform GREEN, STOP and report final SHA, exact transformation fields, Linux run/job/tests/SHA, Windows run/job/tests/SHA, draft SHA proof, legacy-authority rejection, and confirmation no worlds/benchmark/fits were generated.

No world generation until a new explicit controller ruling. `training_authorized=false`.