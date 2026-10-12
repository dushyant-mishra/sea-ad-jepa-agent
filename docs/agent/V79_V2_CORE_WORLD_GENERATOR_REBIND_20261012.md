# V79 V2_CORE world generator: canonical rebind and pre-realization repairs (PR #291)

Date: 2026-10-12

Terminal: `V2_CORE_WORLD_GENERATOR_CANONICALLY_REBOUND_AND_SCIENTIFICALLY_AUDITED__LINUX_WINDOWS_GREEN__DONOR_AND_PREVALENCE_GENERATOR_BUGS_FIXED__CONTROLLER_AUDIT_REQUIRED__NO_REALIZED_WORLDS__NO_BENCHMARK__NO_QUALIFICATION_FITS__REAL_TRAIN_POSTERIOR_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`

Not done: no Q00–Q11 world, no truth table, no manifest, no benchmark, no fit. `realize_worlds()` still fails closed. `training_authorized=false`.

## Authority

| item | value |
|---|---|
| canonical contract | PR #290 `V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json` `57e19295…`, through `v79_v2_core_launch.require_launch_authority()` only |
| immutable payload | V2 draft `cbfa332b…`. Verified as the contract's accepted draft, with identical worlds/seeds/gates/priors/model |
| obsolete | `8be47cb2…`, named once as `OBSOLETE_CONTRACT_SHA256`, refused by the amendment validator, the realization authorization and the manifest |
| pairing amendment | `results/v79/v2_core_qualification_amendments/V79_V2_CORE_Q10_Q11_PAIRING_AMENDMENT_V1.json` `57d7478b148cf1cab8d50a597f303c727b1a1d2d51db408ad181eab383fa4cf5`. Rebuilt by `build_v79_v2_core_pairing_amendment.py` (`--check` byte-identical). Semantics and flags are verbatim from `09f60d91…` (superseded) |
| rulings | 6115053096, 6115121455 (world-generation authorization), 6115340528 (rebind), 6114906562 (pairing semantics); controller audit at 312bb302 |

## Commit chain on PR #291

| commit | what |
|---|---|
| `89a161a7` | merge of 312bb302 + 5394d036, tree = canonical + the 7 ported files (unchanged); competing finalization layer dropped |
| `58ba86df` | RED (local: 9 failed, 13 errors, 21 passed) |
| `959f071b` | GREEN |
| evidence commit | this document, proofs, logs |

PR diff against canonical `5394d036`: generator engineering only (`PR291_DIFF_VS_CANONICAL_BASE.txt`). No PR #290 file is modified or deleted.

CI for `959f071b`: run 38187673238.
- Linux job 114613437023: 46 passed, Python 3.11.17.
- Windows job 114613437184: 46 passed, Python 3.11.9.
- Both jobs observed `57e19295…` and tested PR merge ref `9b61a4b2`, whose tree `c3acb8a8…` is identical to `959f071b`'s.

## Repairs (proof: `results/v79/development/v2_core_world_generator_rebind/GENERATOR_REBIND_PROOF_TEST_ROOT_4242.json`, test seed root, in memory only)

**Donor rescaling.** Realized effects = canonical latent field (`donor_raw_centered`) × SD. A truth object without the latent field is refused.

| world, part | realized effect SD | same world unmodified | planted SD |
|---|---|---|---|
| Q01, detection | 0.189 | 0.447 | 0.191 |
| Q01, positive | 0.043 | 0.154 | 0.044 |
| Q02, detection | 1.066 | 0.443 | 1.087 |
| Q02, positive | 0.499 | 0.152 | 0.515 |

Q07: exactly 0 nonzero effects in both parts. Effects equal latent × SD exactly (maximum deviation 0).

**Intercept re-solve.** The detection intercept is solved per gene after the modifications and the support mask, over measured cells only.
- Every world hits its planted prevalence to ≤ 2.2×10⁻¹⁶.
- Q08's targets span 0.0052–0.0489.
- Q03–Q06 intercepts change against their unmodified selves (mean |Δ| 0.087, 0.150, 0.034 and 0.013).

**Structure.**
- Every world has exactly 5 structural genes (1/3/1).
- Source codes come from canonical metadata (S174 bridge × design): HVS 0, NPH52 1, SEA_AD 2. Weights are applied by source name, giving identical draws.
- Q11's non-operator truth hash equals Q10's.

**Independent read-only review: PASS.**
- An AST comparison shows that only `_rescale_donor_effects`, `build_structural_support` (name-mapped weights) and `load_pairing_amendment` changed. The planting and observation modules are byte-identical.
- Old and new support masks are identical for all 12 worlds at three test roots.
- No live path accepts `8be47cb2`.

## Open items for the controller (not changed here: semantics preserved)

1. **Stream 24.** The contract's seed table declares gene stream 24 `structural_matrix_choice`. The generator, unchanged from PR #291, draws the 3 unmeasured NPH52 matrices from the world-level structural stream 1 instead. Before realization, either ratify this or require stream 24; changing it later alters every support mask.
2. **New-donor held-out replicate.** `generate_observation` implements `train` (streams 14/15) and `same_donor` (16/17) only. Streams 3 and 18–21 (new donors) are unused, but the contract scores new-donor held-out metrics. The physical emitter needs this. Also, Q11 noise pairing currently relies on the caller passing `pairing_parent_world`.
3. **Q11 intercept solve.** Operator offsets are excluded from the solve, as the pairing amendment's "identical non-operator truth" requires. The contract text "linear predictor without donor" read literally would include them. Including them would shift Q11's realized prevalence by up to 0.006 absolute at the test root. Please ratify explicitly.
4. **Minor.**
   - Truth-building functions do not validate their payload and amendment inputs themselves. A future emitter must route through `load_launch_contract` / `load_pairing_amendment`.
   - `SOURCE_CODES` is verified in tests, not at runtime.
   - Q07 zero effects include signed zeros (−0.0); they are deterministic.
