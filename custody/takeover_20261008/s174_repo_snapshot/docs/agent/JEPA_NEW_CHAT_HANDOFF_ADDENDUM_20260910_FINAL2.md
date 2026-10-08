# JEPA new-chat handoff — FINAL2 addendum

Date: 2026-09-10
Status: `HANDOFF_ONLY_NO_TRAINING_AUTHORITY`

This addendum supplements, but does not replace, the detailed canonical handoff:
`docs/agent/JEPA_NEW_CHAT_HANDOFF_20260910_FINAL_CURRENT.md`.

## Live lane state at addendum preparation

Re-fetch every ref before acting. Observed immediately before this addendum was written:

- `main`: `d0dbf7d5b3fa942ad747af81844ea7bf5488b81f`
- frozen T0 V20: `d5d67e21398da92e39095afd864b4fb9ebe3da02`
- T0 V21 draft: `e770f6dc83c44a36232d15541d3529e71c7611c9`
- T0 Step 4: `4d95355e9f3b176bd4e0166185e4fcc95eab4b2f`
- V5 live branch: `495e88971909ad5aeb8c93639af85000481a8f41`
- V5 engineering-content state: `5668e3d71c720219ec823d5ff089f246091f2be2`; the only later V5 commit is the branch-local current-state pointer.

Branches:
- `t0/v20-pathology-blind-materialization-20260908`
- `t0/v21-prospective-design-20260910`
- `planning/v5-full-population-cheat-proofing-20260909`

## T0 — exact next boundary

V20 is immutable. Its terminal remains:
- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- `training_authorized: false`

Step 4 established that 1:1 Q_DEPTH/Q_DETECT matching successfully removed the observed imbalance but simultaneously destroyed the held-out coherence statistic's power. A size-matched confound-retaining control collapsed similarly. Therefore the Step-4 null result is uninformative about whether the held-out biology was confounded; it is evidence that rejection-capable QC gates require power/detectability calibration at the exact geometry they create.

V21 is still `DRAFT_FOR_REVIEW_NOT_FROZEN`; nothing V21 has executed.

The next T0 action is exactly:
`PATHOLOGY_BLIND_FRESH_DONOR_FEASIBILITY_AUDIT_ONLY`

Rules for that audit:
- inspect pathology availability/eligibility only, never AT8 values;
- determine which AT8-available donors outside frozen V20 membership actually have authenticated MTG immune cells and satisfy the unchanged V20 eligibility predicate;
- do not fit an estimator, run weighting, power analysis, or another confirmation diagnostic;
- if fresh donors are usable, create a new prospectively frozen V21 population authority; never extend or rewrite V20;
- standing design rule: if looking at confirmation data could change a design choice, do not look.

V21 design direction already agreed for review:
- broad state remains primary;
- rare biology moves away from a hard binary tail toward a continuous/neighbourhood formulation;
- estimator selection is discovery-only and requires both same-cell measurement robustness and preservation of independent held-out biology;
- matching/weighting are sensitivity analyses, not primary rejection gates;
- every rejection-capable gate requires an explicit power/detectability control;
- V20 ridge `+2.0` endpoint is a well-posedness issue, not evidence that the state p-value was materially fragile; V21 should use prospectively frozen discovery-only bracketing with endpoint/interior STOP logic rather than an arbitrary wider grid.

## V5 — current engineering state

The V5 framework now structurally includes:
- representation firewall separating biological and observation routes;
- cross-cell QC association as warning-only;
- complete same-cell technical-intervention qualification family;
- pre-execution vs learned-checkpoint/postqualification phase separation;
- exact design-context and checkpoint binding;
- parent-child/cross-artifact dependency closure so compatible-looking artifacts from different runs cannot be mixed;
- two-sided rejection-gate power calibration: the exact gate must accept a prospectively defined minimally-valid control and reject a prospectively defined minimally-invalid control at the exact adjudication geometry;
- shortcut-superiority and student/teacher collapse gates;
- proposal-weight, packing/order/restart and GPU authority separation;
- all qualification components remain incapable of independently granting production training authority.

The dominant production-data blocker remains:
`STOP_FULL_READER_EXPRESSION_LOCATION_BINDING_MISSING`

Production closure still requires exact binding of all 42 corrected TRAIN counts/meta shard pairs from the authenticated corrected cache, then:
`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Production dimensions remain unresolved and must be derived from the real FULL104 substrate; historical pilot dimensions are not authority.

### Small real-data V5 smoke

A small real-data run is allowed as the next V5 execution step only under the label:
`REAL_DATA_SMOKE_NON_AUTHORITY`

It must be tiny, deterministic, read-only with respect to project authority, and may test only data-path/reader compatibility, observation/firewall/masking semantics, forward/update mechanics, same-cell perturbation wiring, packing identity, and checkpoint/telemetry mechanics.

Before the smoke, every required input must pass the recorded hash/manifest/provenance checks. Any mismatch must STOP. In particular:
`/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
is currently `PROVENANCE_MISMATCH_DO_NOT_USE` and must not be used until reconciled.

A smoke may NOT:
- set production dimensions or thresholds;
- establish biology or shortcut-superiority conclusions;
- substitute for FULL104 expression closure;
- satisfy postqualification;
- authorize a production or qualification training run.

## Heavy/runtime assets

Use `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json` and `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md` rather than duplicating heavy immutable bytes.

Key runtime paths include:
- `/mnt/data/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `/mnt/data/checkpoints.zip`
- `/mnt/data/t1_checkpoint_u0200.zip`
- `/mnt/data/expression.zip`
- `/mnt/data/WSL execution issue.txt`

Known authoritative/hash-verified asset digests are recorded in the runtime asset status and heavy-asset ledger; do not infer authority from filenames alone.

## New-chat first actions

1. Read `START_HERE.md`, `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`, the canonical FINAL CURRENT handoff, this addendum, the machine-readable state, and runtime asset status.
2. Re-fetch all live branch heads before writing.
3. Keep T0 V20 immutable and training OFF.
4. T0: do only the pathology-blind fresh-donor feasibility audit unless the user changes direction.
5. V5: continue structural self-audit and, if exact runtime provenance checks pass, execute only the tiny deterministic `REAL_DATA_SMOKE_NON_AUTHORITY`; do not promote its result to production authority.
6. Do not send Claude to V5 until the user says T0 has been sufficiently resolved.

## Permanent authority boundary

A decreasing loss, passing unit test, branch name, smoke test, mechanically healthy checkpoint, or convenient data subset is not biological or training authority.

`training_authorized: false`
