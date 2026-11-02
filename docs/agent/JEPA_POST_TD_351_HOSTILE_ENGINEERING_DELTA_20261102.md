# JEPA post-TD #351 adversarial engineering delta — 2026-11-02

**Classification:** `GPT_TESTS_ONLY__FIVE_EXPECTED_REDS__NOT_INDEPENDENT_ACCEPTANCE__NO_SCIENTIFIC_PROMOTION`.

This is a *new implementation-focused hostile probe*, not a historical re-audit or a rewrite of completed work.

## Exact source and custody

- Original code [PR #351](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/351) exact head `2abcb9fe156eac340ff12adff9426ed38d929e3e`; `scripts/v5/jepa_post_td_harness_contract_v1.py` blob `11b1b48e52883182db2889e78a75047011f23757`.
- Pre-existing scoped review [PR #447 comment 6444310613](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/447#issuecomment-6444310613) already described untrusted fixture PASS strings, lack of real Task7 source authority and lossy `int()` gene-address coercion. **Do not relabel these earlier findings as newly discovered.**
- Newly created **tests-only** [PR #517](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/517) at `d8602318b30fa8745ecf928c9e64f6c48e30c1b8`, based on unchanged #351 head; adds one five-attack test file and one CI workflow, modifies no original implementation/tests.
- [Hosted CI run 41496824671](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/41496824671): Ubuntu test job succeeded with **5 expected failures reproduced**; first Windows job failed at Git checkout, **before test execution**. Failed-job retry requested. Treat Windows as unverified until its test job completes. A green expected-failure runner **confirms RED behaviors, not a repair**.

## Five frozen counterexamples

| Witness | Existing source behavior | Interpretation |
|---|---|---|
| NaN trainable parameter count | `validate_matched_compute` at ~323–355 compares nonfinite relative differences with `> tolerance`; NaN comparison is false | Invalid matched-compute PASS at fixture scope |
| NaN teacher FLOPs | Same missing finite checks for FLOPs | Invalid matched-compute PASS at fixture scope |
| Mutated portfolio content | `build_synthetic_rehearsal_preflight` at ~479–513 accepts stale `portfolio_sha256` without recomputing current payload | Preflight integrity check is incomplete |
| Mutated architecture authority | Same function does not rehash/fully verify plan payload, even if input `training_authorized` is mutated to true | **Input** plan accepted; **output** remains training-off |
| Boolean query address | `derive_teacher_evidence_set` at ~174–220 applies `int(True)==1` | Noncanonical molecular identity accepted, already foreshadowed in #447 |

These five are deliberately `unittest.expectedFailure` and the reviewer runner requires exactly five expected failures. The reviewer PR's success must never be interpreted as #351 acceptance. GPT is part of the continuing author lane, so separate non-author review/repair adjudication remains necessary.

## Nonduplication and boundaries

- Retain original #332/#351 noncompensation and C4-requires-C6 fixture contract; do not build a new portfolio, EMA, trainer, issuer or Task5–8 pipeline.
- Retain #447 Tasks6–8 first-class NONE and deliberately blocked selected-target issuance; no caller-supplied status grants biological authority.
- #514/#515 remain untouched for Macha's independent security reviews.
- Fix candidates only in *existing* harness lineage on a separate repair head after this new RED evidence: finite positive typed compute values; exact gene-address type checking before coercion; recomputed canonical portfolio and architecture digest verification at preflight. Do not alter reviewer RED source to manufacture green.
- No protected expression, physical source authentication, Stage4, target/representation selection or real/synthetic training execution occurred.

## Permanent future handoff requirement

Every new GPT/Macha agent must treat **audit #322** and **live handoff #460** as distinct canonical surfaces. After every substantive science **or engineering** change: retain code/test/receipt on actual owner PR; append a source-pinned audit note and chronological event on #322; verify exact-head checks; prepend a dated current pointer on #460; verify handoff checks. Old frozen files must remain byte-identical, and old lower-section handoff text is historical/superseded. These requirements apply while building implementation, not only while recounting history.

**Authority unchanged:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
