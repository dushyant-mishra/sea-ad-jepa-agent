# V79 V2_CORE world-generator controller audit — 2026-10-11

Scope: synthetic/V79 lane only. No world realization, benchmark, Bayesian qualification fit, corrected-TRAIN posterior, factorial science, or JEPA training is authorized by this document.

## Canonical authority

- PR #290 head: `5394d036ccd423f9c61267fbdfeef6edd4912d37`
- Contract V2 SHA-256: `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`
- World-generation authorization: controller comments `6115053096` and `6115121455`
- PR #291 must use `scripts/v79/v79_v2_core_launch.py::require_launch_authority()` as the sole launch gate.
- Historical/superseded contract SHA `8be47cb2d36ec9ddfdf4fd820ed0d51adea871dc115c1414cbe4edfb9223ee1d` is not authority.

## Salvage rule for PR #291

Keep only generator engineering:
- `scripts/v79/v79_v2_core_planting.py`
- `scripts/v79/v79_v2_core_observation.py`
- `scripts/v79/generate_v79_v2_core_worlds.py`
- generator tests
- generator CI workflow
- Q10/Q11 pairing amendment semantics, rebound to canonical Contract V2.

Do not carry a competing contract envelope, finalizer, validator, launch authority, or deletion/replacement of PR #290 receipts/gate.

## Scientific audit findings before realization

### 1. Q10/Q11 paired counterfactual — retained

Q11 must inherit Q10 exactly for all non-operator truth and base noise. Only operator-offset streams 22/23 may differ. All Q11 gates remain hard FAIL.

The old pairing amendment was prospectively valid in semantics but bound to obsolete Contract SHA `8be47cb2...`; regenerate it against canonical Contract V2 `57e19295...` without changing the scientific semantics.

### 2. Structural support — retained

The generator's 5/44 structurally absent genes match the frozen composition:
- 1 single-source-measured gene;
- 3 genes fully unmeasured in one source, weighted HVS:NPH52:SEA_AD = 38:20:10;
- 1 partial NPH52 gene with 3 of 7 NPH52 matrices unmeasured.

Source code ordering is compatible with the existing sorted source encoding: HVS=0, NPH52=1, SEA_AD=2. Unmeasured entries remain outside the likelihood and are represented only by an audit poison value.

### 3. Blocking donor-effect rescaling integration defect

`build_donor_effects()` currently returns donor latent structure as `raw_centered` plus realized `effects`. `apply_world_modifications()` rescales nonzero donor effects only when a field named `donor_z` exists. The current production planting object does not naturally expose `donor_z`.

Therefore a physical emitter could change `donor_sd` for Q01/Q02 while accidentally leaving realized `donor_effects` at the baseline magnitude.

Required before realization:
- define one canonical donor latent field for the physical truth object;
- when donor SD changes, recompute `donor_effects = canonical_raw_centered * donor_sd` for every gene;
- Q07 donor-absent must set both donor SD and donor effects exactly to zero;
- add tests using the actual output of `build_donor_effects()`, not only a hand-built fixture containing `donor_z`;
- test Q01, Q02, and Q07 for both detection and positive parts.

This is an implementation repair of frozen semantics, not a scientific contract change.

### 4. Detection-intercept realization requirement

The frozen contract defines each gene's detection intercept by solving for its planted prevalence over structurally measured cells from the non-intercept predictor excluding donor effects.

The physical emitter must perform this solve **after** applying each world's modifications and support mask. This is especially important for Q03–Q08, where source/class/quadratic/prevalence terms may change.

Required tests before realization:
- for every world, recomputed non-donor mean detection probability over measured entries matches the world's planted target prevalence within a frozen numerical tolerance;
- Q08 actually realizes the sparse 0.005–0.05 prevalence target range rather than merely changing a metadata field;
- structurally unmeasured entries never enter the intercept solve.

### 5. Physical-emitter gate

Current `realize_worlds()` deliberately stops after validating an authorization receipt. Do not remove that stop until:
1. canonical authority rebind is complete;
2. stale competing finalization files are absent from the generator PR diff;
3. donor-rescaling and per-world intercept tests are RED then GREEN;
4. Linux and locked-Windows generator suites are green on the exact same head;
5. controller audits that exact head and issues a realization receipt.

## Current terminal

`V2_CORE_GENERATOR_SCIENTIFIC_AUDIT_COMPLETE__CANONICAL_REBIND_PLUS_DONOR_RESCALE_AND_INTERCEPT_REALIZATION_TESTS_REQUIRED__NO_REALIZED_WORLDS__NO_BENCHMARK__NO_QUALIFICATION_FITS__REAL_TRAIN_POSTERIOR_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF`
