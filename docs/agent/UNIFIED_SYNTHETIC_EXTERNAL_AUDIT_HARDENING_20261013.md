# Unified synthetic external-audit hardening — 2026-10-13

Status: `PASS_WITH_LIMITATIONS_REPAIRS_APPLIED__MECHANICS_FIXTURE_ONLY`

Independent audit source: draft PR #339, head `7e955445f938d24dec9cf177e27d60433b8ab97e`.

## Scope correction

PR #328 is a **qualified unified mechanics/interface fixture** derived from PR #315. It is not the complete PR #315 production synthetic substrate.

Implemented here: unified common/rare mechanics, V79 biology/observation primitives, qualitative PR #311 rare/context/multimodal semantics, support semantics, donor splits, controller-only target derivation, and downstream interface rehearsal.

Still separate future production work: full Stage81A3 mechanistic network, generic additive/non-additive interaction families, richer production query semantics, canonical 41,238-address realization, and full production-scale rehearsal.

## External-audit findings and repairs

### 1. Scope overclaim — repaired

Durable PR wording now explicitly calls this a `unified synthetic mechanics/interface fixture`. No claim remains that the full PR #315 production simulator is implemented.

### 2. Incomplete transitive code custody — repaired

Successor receipt V2 hashes all seven executable files in the fixture path:

- `scripts/v79/unified_synthetic_integration_v1.py`
- `scripts/v79/unified_synthetic_fit_view_v1.py`
- `scripts/v79/unified_synthetic_controller_truth_v1.py`
- `scripts/v79/finalize_unified_synthetic_integration_v1.py`
- `scripts/v79/v79_hierarchical_biology.py`
- `scripts/v79/v79_observation_operator.py`
- `scripts/v79/v79_rare_biology_generator_v1.py`

The three imported frozen dependencies additionally fail closed against exact Git blob identities:

- hierarchical biology: `08d74b02fb609a1e923f2adc906c2bf68b821b26`
- observation operator: `6ed165d33ea31616875064f0c7d95554a6a6abe8`
- rare generator: `2a2f0b2f5b48ed7b9cfd81a74ab7ec514053309f`

### 3. Runtime environment unpinned — repaired prospectively

Qualification runtime is now exactly:

- Python `3.11.9`
- NumPy `2.3.5`
- pandas `2.2.3`
- SciPy `1.17.0`
- pytest `9.0.2`

These are installed from `requirements/unified-synthetic-integration-v1.txt`, checked explicitly in CI, and bound into receipt V2.

### 4. Perturbation-null semantics under-specified — repaired

Frozen arm map:

- `0 = CONTROL`
- `1 = ACTIVE_RARE_PROGRAM_PERTURBATION`
- `2 = MATCHED_PERTURB_NULL`

Production construction remains exactly `perturbation_state = (arm == 1) & rare_activity`. Regression tests prove arms 0 and 2 can never activate the target perturbation mechanism. The exact semantic map is bound in the integration manifest, controller artifact, and receipt V2.

## Verification

TDD RED evidence: workflow run `38485411283` at test-only head `43ee596e48fdb7a78cb3ec7a446ad255229fbf58` failed before implementation, as intended.

GREEN evidence: workflow run `38485929906` on code/workflow head `8213bcbaf92454bf55ef57957010ea28890c8b8c` passed the pinned-runtime check, full integration/regression suite, deterministic receipt generation, and receipt artifact publication.

Generated receipt artifact:

- artifact ID `11859436393`
- artifact archive digest `sha256:825dd42c8467418045b7a3406cff190697a8abc0104c6203c8a425089bb4d1ef`
- exact receipt-file SHA-256 `0cc1bc599dd0e77ec46f603d8a7edbb7da58762020a68d703b403dc7bf0a4dad`

Receipt V2 identities:

- world: `dedd53c3b93eecdf28b73f229574a0cda4971371a3a6282f4b9e12fa44d09e66`
- fit view: `fc5fa5c071903460da8c0d4644a3b18022f45b178f2c60a727710cadc2fb350a`
- controller truth: `120c4e47bb7d667360c0786bb6004f02166d0f189c4a2b33b478545c7296c05f`
- manifest: `9b74681f57601225aa26037fa1eac439be067143bfb900cdcd5f73af0dbc8d3b`
- synthetic package: `9f2f3b7a53d5862a2a08bbd23c1d42f990f0f055616fbce7a1491493cda3fb41`

The world and fit-view hashes remain unchanged from the pre-hardening fixture. The controller hash changes because the controller artifact now binds the explicit perturbation-arm semantic map. The package identity changes because transitive source custody, runtime identity, perturbation semantics, and manifest identity are now included.

## Remaining limitation deliberately not changed

Controller separation remains artifact/logical separation inside this mechanics fixture. A future blinded qualification realization should use separate producer/fit/controller execution domains. That is not required to rewrite this already-qualified mechanics fixture and is not presented here as production blind custody.

Write-once semantics mean **writer-enforced write-once plus Git-frozen history**.

## Authority

No human biological, target, representation, TD60, Stage4, synthetic-training, or real-training authority is created.

Terminal:

`UNIFIED_SYNTHETIC_MECHANICS_FIXTURE_QUALIFIED__FULL_PR315_PRODUCTION_REALIZATION_INCOMPLETE__TRANSITIVE_CUSTODY_HARDENED__PINNED_RUNTIME__PERTURBATION_SEMANTICS_BOUND__V79_LAYER_A_SCORING_SEPARATE__TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
