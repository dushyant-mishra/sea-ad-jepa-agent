# Independent ChatGPT reviewer: PS Task3 Macha #437 numerical and parameter-namespace hostility — 2026-10-28

**Review target:** [Macha PR #437](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/437), frozen head `fd3242ada6f77ba09ff2d8a1c7716eb9725ced11`. Reviewer branch is **tests and source-specific report only**: original `scripts/production_synthetic/calibration_v1.py` and original tests are unchanged. All adversarial inputs are synthetic, no actual human calibration or protected donor data accessed.

**Independent exact-head verdict: `REPAIR_REQUIRED__R1_NUMERIC_ALIAS__R2_OBS_PARAMETER_SPOOF`; source calibration authority remains `NONE`.** [Reviewer run 40733195290](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40733195290) SUCCESS in expected-RED recording: **3 newly authored hostile cases FAILED as predicted, 1 unpromoted control PASSED**; unchanged Macha original tests **33 PASSED**. [Full inherited calibration run 40733195258](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40733195258) remains FAILURE **3 failed, 391 passed, 1 xfailed**, due to the new RED cases included in its broad pytest collection. This is neither a successful calibration gate nor a newly executed real source; the preserved source has not been repaired. The unchanged unified synthetic integration [run 40733195217](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40733195217) passed its existing scope.

## What is working and must be preserved

- `_AUTHENTICATED_CALIBRATION_REGISTRY = frozenset()` is genuinely empty, so a self-matched content SHA and asserted `AUTHENTICATED_EMPIRICAL_CALIBRATION` provenance produce only `CONSISTENT_UNAUTHENTICATED_FIXTURE`. No new real calibration issuer has been enrolled.
- Distinct protected VALIDATION/ORACLE/RESERVED/DEVELOPMENT split roles are required for the existing fixture firewall; original Macha hostile tests pin a useful fail-closed floor.
- Realism process-local state uses module-held snapshots and explicitly declares `COOPERATIVE_SAME_PROCESS_CALLERS__FIXTURE_ONLY__NO_HOSTILE_CALLER_PROTECTION`. It does **not** claim cross-process durable anti-retry or adversarial same-interpreter security, which remain STOP_B dependencies.
- Address-universe check always returns `FIXTURE_WITNESS_ONLY__CALIBRATION_INELIGIBLE`; even a false positive cannot be interpreted as authenticated 96→41,238 biological transfer.
- Historical August 2026 [PR #471](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/471) 97/97 SHA archive verification authenticates only the historical manifest's bytes relative to that manifest, not current post-correction TRAIN-only empirical statistic provenance. Original raw archive binaries are not GitHub-hosted.

## Newly identified scoped defects

### R1 — lossy numeric equivalence for universe witness (fixture claim integrity)

`validate_address_universe_agnostic` at `scripts/production_synthetic/calibration_v1.py` compares `float(value) != float(other)`. Exact Python integer inputs at `2**53` and `2**53+1` have **different values**, but both round to the same binary64 float. The code therefore reports a fixture-level invariant universe witness for a pair of scientifically unequal numeric statistics.

This is a *test of the validation law*, not an allegation that real read depth is 9 quadrillion or that current real 41,238-address calibration already passed. If values are restricted prospectively to a trustworthy finite exact range, that must be an explicit typed decision, not implicit float rounding.

**Repair requirement:** refuse unrepresentable integer values or compare exact numeric quantities without a lossy cast; pin a canonical numeric policy, then verify across integer/float, sign, near-boundary values and different universes. Do not reclassify the legacy non-authoritative witness as eligible.

### R2 — prefix-only realism tunable parameter permission (scientific target-control scope)

`RealismContract.__post_init__` accepts any caller-provided tunable parameter starting with `OBS_`. Thus `OBS_DISEASE_PREVALENCE` and `OBS_TARGET_WINNER` are legal strings for an otherwise fixture-valid frozen contract, despite the scientific V3.1.1 requirement that latent biological and target-outcome parameters **cannot** be tuned to pass observation realism. No actual biological generator is attached, and this finding **does not establish that a generator really tunes disease or target truth**. It establishes that the contract cannot enforce that prohibition using a prefix-only name check.

**Repair requirement:** explicitly bind tunable parameters to a closed, source-versioned observation-operator registry, with quantitative semantics and independent authority, rather than names alone. A hardcoded allowlist may be useful as a scoped mechanical repair but does not establish operator semantics or freeze a generator's biological parameterization. Do not infer a real biological issuer from the allowed string.

## Evidence / CI plan

- `tests/production_synthetic/test_calibration_v1_chatgpt_437_hostile_red.py`: R1 and two R2 adversarial cases intended RED, plus one GREEN control that the existing source firewall never authenticates a caller-pinned digest.
- `.github/workflows/ps-task3-chatgpt-437-independent-hostile-red.yml`: original Macha Task3 suites run unmodified; reviewer hostile suite is run separately and its **expected failures must be retained**, not xfailed/relabelled accepted. Exact raw pytest log attached as CI artifact.
- This is an independent, source-limited **review** stacked on #437, **not** a repair or an independently certified real TRAIN calibration issuer. If new tests show further failures, record the true results and adjust only test expectations about source behavior, not the production source or negative science.

## Next execution following reviewer verdict

1. Macha (author) or another assigned implementer may repair R1/R2 on a separately scoped PR, preserving this reviewer branch and tests. Independent reviewer must rerun original and new hostile cases on the exact repair head. Avoid approving the author's own fix.
2. Separately, source owners must supply an independently authenticated post-HVS/SEA-correction TRAIN observation-statistic issuer; correct feature map, donor/physical units, library-depth/query exclusions, protected split policy, sample selection and all measurement-right provenance. `_AUTHENTICATED_CALIBRATION_REGISTRY` must not be populated from self-pinned user hashes, old archival bundles or synthetic fixtures.
3. The PS Task4 candidate-neutral biological generator remains **absent** in reviewed branches and is not to be invented from PR328 gene blocks. Its STOP_B requirements and frozen V79/V80/realism law are independent of this fixture review.
4. Keep the current #479 fixture-only V2 observation contract and Macha #476/#477 pending reviews separate; the source-side physical whole-library and visible q-excluded depth remain distinct, G7 R1/R1D/R2 and PS T2-D source auth remain RED.

**Standing authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
