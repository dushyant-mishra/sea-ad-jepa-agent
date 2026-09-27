# V46 addendum — independent static red-team of the reported V29 gate-v4 PASS
Date: 2026-09-27
Reviewed source: PR #178, commit `1eeed1ff6e7616a0594e2264aa614fb388879b43`; `scripts/v5/teacher_fidelity_synthetic_gate_v4.py`; `results/v29/TEACHER_FIDELITY_SYNTHETIC_GATE_V4.json`.
Review type: **source inspection and committed-receipt inspection only.** This addendum does not claim a full independent simulation rerun or any real-data readout execution.

## New P0: the verdict is vacuously PASS on an empty regime selection, and partial-regime runs can be labelled overall PASS

The script accepts `--regimes` and computes:
```python
regimes = [r.strip() for r in a.regimes.split(",") if r.strip()]
results, calib, incomplete = {}, {}, []
for reg in regimes:
    # run each arm and calibrate ...
arms_ok = all(v.get("arm_pass", False) for reg in results for v in results[reg].values())
cal_complete = all(c["complete"] for c in calib.values())
fp_ok = all(c["binomial_upper95"] <= FP_UPPER_LIMIT for c in calib.values() if c["required_qualification"] is False)
power_ok = all(c["rate"] >= POWER_LOWER_LIMIT for c in calib.values() if c["required_qualification"] is True)
no_fb = all(v.get("poisson_fallbacks", 0) == 0 for reg in results for v in results[reg].values())
gate = bool(arms_ok and cal_complete and fp_ok and power_ok and no_fb and not incomplete)
```
For `--regimes ""`, the list is empty, every `all([])` is `True`, `incomplete` remains empty, and `gate_pass` becomes `True` with **zero tested datasets**. A one-regime invocation may also return PASS with the other three frozen regimes unexecuted. This is a definite static fail-open. The published actual v4 receipt contains all four intended regimes and has **not** exploited this path; do not retrospectively withdraw its numerical counts on that basis. But the gate executor itself needs an adversarial fixture and a coverage-enforcing correction before it can be called fail-closed.

Required corrective invariant: reject unless the *set and multiplicity* of selected regimes exactly equal all four prospectively frozen regimes. At verdict time verify each regime has exactly the two named negative and two named positive arms, every required channel, every requested finite sham draw and every required calibration dataset. An empty, duplicate or partial selection must exit nonzero with an explicit INCOMPLETE receipt. A deliberate `--regimes A_tuning_sparse` smoke must never be allowed to issue production gate authority.

## New P1: POS_COMP/POS_AMP channel ablations are reported but not enforced by gate_pass

In the same script, `r["arm_pass"] = (r["qualifies"] == cfg["want"])`, where `r["qualifies"] = r["channels"]["full"]["qualifies"]`. The composition-only and amplitude-only results are printed and stored but `arms_ok` evaluates **full-model qualification only**. The nonlinear POS_COMP amplitude-leakage diagnostics are also printed and stored, not gate assertions.

The real committed receipt nevertheless has the *expected* one-shot channel pattern in all four regimes:
- POS_AMP: full and amplitude-only qualify; composition-only does **not**.
- POS_COMP: full and composition-only qualify; amplitude-only does **not**.
- POS_COMP `r2_gain_from_z_terms`: 0.00000684, 0.00000149, 0.00001407 and 0.00045117 in A/B/C/D respectively.

Therefore the data in the *current receipt* support the more limited descriptive ablation conclusion. But the automatic green gate could still approve a future run where the composition arm fires only through amplitude. Add required channel assertions and deliberately swapped-channel and nonlinear-amplitude-leakage fixtures. The mathematical generator itself now fixes total **expected** P abundance conditional on capture, not an exactly fixed *realized* molecule count; this distinction is fine and should remain explicit.

## Custody/transfer verification

The handoff branch publishes all 14 byte-identical original text/CSV files under `original_text/`, with remote tree blob hashes independently matched against the original Git SHA-1 inventory. The other 11 original files are **not** in GitHub: they remain SHA-256 authenticated in the downloadable full-custody ZIP. A connector limitation prevents passing local binary file handles into GitHub's string-only blob API; five original archives also exceed ordinary GitHub per-file size limits. This is partial GitHub transfer **plus complete local custody**, never full GitHub upload. Preserve the full downloadable bundle before starting a new chat.

Independent local second pass: all 25 original files matched their inventory SHA-256, every original appears in the full ZIP at the declared size, the full custody ZIP CRC passed, and the small portable ZIP CRC passed. Both ZIP hashes match `LOCAL_CUSTODY_BUNDLE_OUTPUTS_V46.json`.

## Qualification decision

**As-of pinned commit:** synthetic v4 has a physically reported full-regime PASS, with all 16 arm-by-regime outcomes, exact receipt arithmetic checked, but full Monte Carlo not independently rerun and two executor-level assurance gaps above. It is reasonable to preserve the observed synthetic result while marking the *gate software* **NEEDS_FAIL_CLOSED_COVERAGE_AND_CHANNEL_ASSERTION_TESTS**. Real teacher-fidelity gene extraction/evaluation remains closed pending these bounded fixes, independent review and a valid prospectively frozen real-gene sham design. No neural training.

Do not reopen already-audited earlier null tests, old invalid biology, the 187,909-cell masked artifact audit or the historical S9 environment false alarm to address these two new defects.
