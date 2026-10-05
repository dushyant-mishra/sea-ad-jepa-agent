# JEPA V29 gate-v4 validator: independent follow-up review

**Review snapshot:** Claude research PR #178 at `59e094d32d27c8bc024b94308bbe73bf38225de5` (2026-09-28 UTC), source `scripts/v5/gate_v4_receipt_validator_v1.py` (Git blob `108d031281d9b3baa7f643c6a3048c6f7a87925f`) and committed `results/v29/GATE_V4_RECEIPT_VALIDATION_V1.json`. The original generator and numerical receipt remain immutable. **This review is source inspection and independently constructed test-fixture work. It does not claim to have run Claude's validator against the original receipt or rerun the Monte Carlo on Claude's machine.**

## What the new validator establishes

The new receipt validator correctly rejects a parsed empty-regime result and checks the expected POS_COMP/POS_AMP ablation patterns in the published receipt. It recomputes Clopper–Pearson endpoints from each **aggregate regime–arm record** and records the useful historical caveats: sensitivity only at injected positive effect strength; C/D were inspected during iterative diagnostics; original Monte Carlo was not independently reexecuted. Its committed validation receipt reports 4 regimes, 16 cells, 48 channel observations, 26/960 negative false qualifications and 240/240 positive qualifications.

## Source-level assurance gaps to address before calling the validator fail-closed

1. **Producer and receipt digest binding are optional.** The CLI's `--expect-script-sha256` and `--expect-receipt-sha256` default to `None`. In the direct `validate()` function, `script_sha_matches_producer_field` is informational and its mismatch is not added to `failures`. Mandate the two expected digests for the *original-v4 historical validator*, refuse producer-field mismatches, and produce a separately versioned validator for any successor artifact. An unauthenticated, user-supplied expected hash does not by itself attest the execution environment.
2. **The 16-cell calibration census checks only length, not identity or arm polarity.** Substituting one fabricated key for one required `(regime, arm)` leaves length 16 and can yield PASS. Require the exact frozen Cartesian product, unique raw JSON keys, and each arm's expected positive/negative polarity.
3. **Aggregate calibration fields are insufficiently cross-checked.** `datasets_requested`, `datasets_used`, `complete`, `qualified`, `rate`, `required_qualification` and `binomial_upper95` should be mutually consistent, present and finite, with exact n=120 for each original-v4 negative cell and n=30 for each original-v4 positive cell. The source currently allows a missing CP field, a contradictory cached rate, and `complete=True` despite unequal counts. The original receipt **does not publish all per-dataset outcome records**; it cannot substantiate a claim that 960 individual outcome booleans were independently recounted. A prospective successor should publish a digest-bound per-dataset outcome/seed inventory.
4. **Type and model hygiene:** do not coerce arbitrary strings to bool. Require actual booleans, three exactly named `channels_run`, finite/range-checked p-values and donor fractions, p/threshold/qualification self-consistency, exact negative-binomial model-family provenance, an explicit zero Poisson-fallback counter, and the original 99 primary-sham request. The existing `math.isnan` check misses ±infinity. Note: the original receipt records `sham_draws_requested`, not each actually executed sham draw; this cannot be independently proven from its aggregates.
5. **Amplitude-control diagnostics are still nonbinding:** the validator enforces the one-shot ablation classification but not the POS_COMP nonlinear amplitude-leakage diagnostic. Require complete, finite diagnostic records. The v4 source does not provide an unambiguous precommitted numerical threshold for every nonlinear diagnostic, so do **not** invent an acceptance bound retroactively from the observed PASS. Obtain a prospective protocol amendment and test a deliberately planted cosh-style amplitude leak separately.
6. **Reject raw duplicate JSON keys before dict construction.** `json.load()` silently takes the last repeated property and cannot detect a duplicate regime erased by parsing. Separately, the corrected executor must reject duplicate `--regimes` arguments *before* converting them to a dict, and include argv/roster/attempt evidence in the receipt.
7. **Validate the overall reported gate flag against independently recomputed predicates.** Do not rely on the original `gate_pass` or treat an internally inconsistent status as a clean PASS. Calibration n increased after inspection of earlier pilot outcomes; do not label the current calibration as independent post-selection confirmation.

## Independent executable probe supplied

`JEPA_GATE_V4_VALIDATOR_ADVERSARIAL_PROBE_20260928.py` is read-only. It **statically compiles and self-checks in this environment**: 21 distinct nonvacuous JSON mutations and the 942 / 923 / 933 pair-denominator numerical witness. Its main mode must be run inside a checkout containing Claude's actual source, original frozen receipt and producer. It pins the original generator digest `648dee...` and receipt digest `09f66e...`, checks the baseline, applies each mutation independently, and reports `FALSE_GREEN`, `REJECTED_WRONG_REASON`, or `REJECTED_INTENDED_REASON`; raw-JSON duplicate-key rejection and cross-process SHA-derived seed replay have their own probes. **Until main mode actually runs against the checked-out GitHub files, the source-level vulnerabilities above remain identified by inspection rather than independently executed proofs.**

Run from repository root, copying the probe beside the checkout or adjusting its path:

```bash
python JEPA_GATE_V4_VALIDATOR_ADVERSARIAL_PROBE_20260928.py \
  --validator scripts/v5/gate_v4_receipt_validator_v1.py \
  --receipt results/v29/TEACHER_FIDELITY_SYNTHETIC_GATE_V4.json \
  --producer scripts/v5/teacher_fidelity_synthetic_gate_v4.py \
  --out-json gate_v4_independent_mutation_receipt.json
```

The probe exits nonzero on any false green, wrong-reason rejection, seed divergence, import error or duplicate JSON acceptance. Do not add it to required CI expecting green until the successor validator is repaired. Its reference-copy seed test intentionally uses two different `PYTHONHASHSEED` values.

## Reserved readouts and denominator decisions

Restore **all six originally frozen RNA readout identities** with an explicit exposure firewall; do not relabel CSF1R untouched. Retain the known CSF1R decoder-QC detection exposure, LPL structural-availability exposure and historical R7 attempted readout analyses on scrambled feature coordinates. The R7 values are biologically invalid under their named labels. Use a prospectively fixed sensitivity analysis that isolates any effect of exposed CSF1R and explicitly limit claims of independent previously unseen validation. Preserve the six original denominator exclusions regardless of evaluation exposure status. The new algebraic regression test is separate from a physical end-to-end decoder/denominator integration test.

## Authority boundary

The original four-regime numerical result remains reported evidence, not independent reexecution; do not retrospectively mutate its immutable receipt. The real count-based biological gate remains CLOSED until a corrected executor and real-gene sham design withstand independent hostile tests. `TRAINING=OFF`.
