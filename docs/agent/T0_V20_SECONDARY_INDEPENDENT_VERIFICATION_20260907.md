# T0 V20 secondary independent verification — 2026-09-07

Status: `PASS_T0_V20_SECONDARY_VERIFICATION__NO_AUTHORITY_CHANGE`

This note independently re-verifies the already-bound external review outcome in DEC-016. It does not modify T0 code, contracts, constants, manifests, estimands, thresholds, hierarchy, claim scope, pathology access, or real-execution authority.

## Exact candidate
- ZIP SHA-256: `a069cad258d278bf8d97e20ba1317ccc62b93265e7f93208a2ae1a4848561947`
- package root / PACKAGE_MANIFEST.csv SHA-256: `896dce257b8ed7330cfe9ac9a561e6d87090903485236dbf37f389d6432cb9e7`
- manifest rows: 154
- V20 contract: `b8e5a38f9a158d0436d38e6846a51692f9a949580c899768c7d7507ab8646f62`
- implementation manifest: `1f55741e83bf1b504c052975649ec3a8978428b311251c9b0bd5271cf20c6b9d`
- active-test manifest: `99b9aeacea525ff06d6ab6d64aaed2fd74167795c2da21c02ef912f867fb0d6b`
- API map V3: `4aa3a3d11d7f851b106b8a2f33e1b4b345eddbcdd1f2baaab9f30b0aff1bec2c`
- superseded registry: `ef54a8d0cc2f2e9c160e459bd8e239c20c10a0e052a369cc2ec3688096de909c`
- V20 constants: `d15a1773469f67140de199ddcaf784b3c811c92ae7ed3f8bc4d6ab9f90252833`
- changed studentized FL: `3b04f20f695e392d8193aac53efc7973f1df23dc8fb3e148ab01ab353d6a2fa2`
- inference-safe wrapper: `7404f7d610865c5646c3a7e4e86d980c8858cf0c601e8cd8a67b10aedcc25cb6`

## Package and chronology
- 154/154 manifested members matched size and SHA-256.
- package root reproduced exactly.
- only structurally unmanifested files: `PACKAGE_MANIFEST.csv` and `PACKAGE_ROOT_SHA256.txt`.
- preserved V19 ZIP matched `4ba8d3362ee05efe363e254f11a45db468a3e44d234ddd4dd58091640ba7a52e`.
- preserved V18/V4 ZIP matched `f25806dd68c576832d51ef998712f56b4add4481388852e4b22636fbc1624fa9`.
- preserved V18 scientific contract matched `0851b47d2351ded1be35a772bb9d7c05ed57d4bbbe551d81c7845a87ace85050`.

## Independent behavioral repair-A probe
Using the same aliased predictor design against V19 and V20:
- well-formed integer permutations: both return legitimate `estimable=False` alias result.
- float dtype: V19 absorbed; V20 raises `ValueError`.
- malformed width: V19 absorbed; V20 raises `ValueError`.
- 1-D permutation: V19 absorbed; V20 raises `ValueError`.
- zero rows: V19 absorbed; V20 raises `ValueError`.
- out-of-range index: V19 absorbed; V20 raises `ValueError`.
- repeated index: V19 absorbed; V20 raises `ValueError`.
- negative index: V19 absorbed; V20 raises `ValueError`.

Thus 7 malformed classes are behaviorally discriminated in the repaired direction. `safe_studentized_fl` still catches only `NotEstimableError`, so structural `ValueError` propagates.

`t0_tail_hc3_t_v1.py` validates y/reduced-design/predictor shape, length and finiteness before `ols_hc3_last`; no second absorber was found on the canonical tail path.

## Repair-B / authority checks
- independent AST enumeration found 157 top-level public functions in `current/code/*.py`.
- V3 API map has 157 rows and exact set equality.
- only two public classes are methodless `NotEstimableError` definitions; no public callable is unmapped.
- all 8 superseded registry entries hash exactly at archived paths and are absent from active paths.
- clean V19->V20 source diff, excluding cache artifacts: 8 removals, 5 additions, 2 modifications.
- the only modified source implementation is `t0_studentized_fl_v1.py`; the only modified test is `test_t0_inference_safe_v1.py`.
- execution-input authority, adjudicator V2, canonical freeze V2, target-family V3, technical-registry V3, 18-attack test, and safe wrapper are byte-identical to V19.

## Tests
All 224 collected tests were rerun in bounded groups in the secondary environment:
- 99 non-heavy tests: PASS, with the two known pandas FutureWarnings.
- 102 remaining non-heavy tests: PASS.
- 18/18 execution-binding attacks: PASS.
- 5/5 canonical-chain tests: PASS, including full raw adjudication.

Reconstructed total: **224/224 PASS**, same 2 warnings.

Static V20 contract audit: PASS on all 22 checks.
STOP-A targeted: 11/11 PASS.
STOP-B/governance targeted: 6/6 PASS.

## Non-blocking observations independently confirmed
1. `t0_studentized_fl_v1_reference_before_opt.py` retains V19 malformed-input precedence, while its equivalence test covers well-formed numerics only. This is off the canonical path and does not invalidate V20; add error-semantics equivalence in a future hardening cycle.
2. The archived V18 audit contained explicit canonical import-hygiene checks that are not present in the V20 audit. Current V20 wiring is correct: family V3 + tail authority V1; V1 adjudicator is imported only as the non-authoritative donor-table helper. Restore the guard in a future hardening cycle.
3. Two pandas FutureWarnings come only from fixture assignments of 100.5 into int64 columns. Hygiene only.

## Authorization check
Both execution-authority builders hard-set `real_execution_ready=False`; verifiers require False. Production paths require True and raise `STOP_T0_V19_EXTERNAL_INPUT_AUTHORITY_NOT_MATERIALIZED`.

Therefore the secondary verdict agrees with DEC-016:

`PASS_T0_V20_INDEPENDENT_REVIEW`

Meaning, and only this:

`T0_V18_SCIENTIFIC_SPECIFICATION_PRESERVED__V20_EXECUTION_BINDING_AND_INVALID_PRECEDENCE_ACCEPTED__REAL_T0_STILL_UNAUTHORIZED`

No pathology, DEV, SEALED, reader-validation, reader-oracle, or real T0 execution is authorized.
