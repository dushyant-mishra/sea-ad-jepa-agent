# T0 V20 replay-equivalence V2 — independent review, 2026-09-10

Status: **PASS_T0_V20_REPLAY_EQUIVALENCE_V2_REPORTING_RECOVERY_REVIEW**

Scope: independent review of the pushed code, Git history, and published machine-readable artifacts at commit `17ab4f24023740c8da8e8db0394a185fe6cdaf60`. This review does **not** claim an independent re-execution of the multi-GB local-data run in this environment.

## Findings

1. **V1 preservation verified.** `scripts/v4/t0_replay_equivalence_v1.py` has identical Git blob identity at `5e8bee682520421c3a884fb513f0c76d40a415cd` and `17ab4f24023740c8da8e8db0394a185fe6cdaf60`: `7bc6c185279078bb4c07103c55b5f503d5fbd150`.

2. **V1 STOP artifact preservation verified.** `outputs/t0_sensitivity_recovery_v2_20260910/T0_V20_REPLAY_EQUIVALENCE_REPORT.json` has identical Git blob identity at those same two commits: `086d8d6671686ed8dd77948449574f649577cec2`.

3. **No frozen V20 file is changed in the V2 lineage from the V1 STOP commit.** The `5e8bee68..17ab4f24` compare contains only replay-policy/recovery code, tests, findings/docs, output records, and `.gitattributes` additions.

4. **The authorized V2 policy change is mechanically constrained to one field.** `scripts/v4/t0_replay_equivalence_v2.py` derives policy from V1 and `verify_single_policy_change()` requires:
   - the V1 float policy unchanged;
   - exact-array fields unchanged;
   - dtype rule unchanged;
   - all `state_primary` float/exact rules unchanged;
   - `final_trace_scale` alone leaves exact-scalar classification;
   - `final_trace_scale` alone enters the ULP class;
   - its budget is exactly one float64 ULP;
   - every pre-existing ULP budget remains unchanged;
   - the total classified-field set remains unchanged.

5. **Published recovery result is internally consistent with the frozen adjudication thresholds.** The artifact reports:
   - primary: beta 124.94507515835764, HC3 SE 65.48932245523241, t 1.9078694125102356, p_upper 0.021, residual df 13;
   - composition + IMMUNE_FRACTION: beta approximately 127.131, HC3 SE approximately 66.903, t approximately 1.9002, p_upper 0.019, residual df 12;
   - measurement + Q_DEPTH + Q_DETECT: beta approximately 137.172, HC3 SE approximately 81.835, t approximately 1.6762, p_upper 0.030, residual df 11;
   - sensitivity alpha 0.05 and 9,999 permutations for the sensitivity arms.

6. **Replay-equivalence publication requirements are represented in the pushed artifact.** Exact provenance is reported at both target-verification call sites; all 13 target-fit fields pass; `final_trace_scale`, `final_lambda`, and `response_residual_sd` are each at or within their one-ULP classes; `state_primary` beta/HC3 SE/t reproduce with reported relative difference 0; both terminal strings are exact; numeric environment is recorded; `training_authorized` is false.

7. **The wrong-store reconstruction is recorded as a caught input-resolution error, not as a changed analysis rule.** The initially reconstructed `expression_level0` path was not consumed by the V1 run because V1 stopped before that stage. Under V2, the frozen population authority refused it by manifest mismatch before confirmation-matrix materialization. The corrected `expression_level4` store was then verified against the pinned manifest/membership authorities before use.

8. **The `null_t` limitation remains explicit.** Only the committed truncated representation is available for exact replay comparison; no full 9,999-value null-array equality is claimed. Decision-relevant p-values and permutation count remain exact checks.

## Review conclusion

The reporting-only T0 V20 sensitivity recovery is accepted as a coherent V2 replay-equivalence result. The previously published T0 V20 science conclusion is unchanged. The V1 bit-exact verifier and V1 STOP remain preserved evidence rather than being weakened or rewritten.

This closes the **reporting-recovery blocker**. It does not authorize training and it does not waive reconstruction of the original numerical stack as a reproducibility task.

The project may now move the data-heavy execution focus to the V5 full-reader qualification lane, beginning with exact recovery and binding of the 42 corrected TRAIN counts/meta shard pairs.

`training_authorized: false`
