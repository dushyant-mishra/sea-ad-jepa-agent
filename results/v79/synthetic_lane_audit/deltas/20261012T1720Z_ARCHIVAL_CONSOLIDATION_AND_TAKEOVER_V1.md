# V79 synthetic lane delta — archival consolidation and takeover

Timestamp: 2026-10-12 17:20 UTC
Lane: synthetic/V79 only

## Why this delta exists

This delta makes the lane cold-startable without redoing historical audits. It records only changes after the original #302/#303 consolidation and does not reopen earlier scientific decisions.

## Current immutable science / data authority

- Contract V2 SHA: `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`
- pairing amendment: `57d7478b148cf1cab8d50a597f303c727b1a1d2d51db408ad181eab383fa4cf5`
- environment lock: `5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782`
- realization head: `cd6425b29f3fbd70b6d93351feb7c188f8b17cc8`
- realization root manifest: `84949723305dc2211ebcd451b64dd9adc8518f3580d2122f5600fcf4b38de0de`
- realization directory digest: `40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286`
- blinded index: `8ea3e0cb6637c97b3e940eac54476622bd4f790febb07abee2e8ccdeea751e40`
- realization complete ledger: `4e65f213d2eeb2d66b8bd7a9031eeb47eadee5801a9bd0880bd3c78dae88cd65`
- realization audit receipt: `6bd05349516a969ac7e83fc991d03d6274335b22068f8c6577f5a9de11b3f9b3`

Q00-Q11 were realized exactly once and must never be regenerated to repair later software.

## Benchmark history now frozen

The original PR #299 one-shot benchmark authority at `2240fd82f1707399bb8b2b16d3d93fee23866067` was consumed once.

Frozen failure evidence:
- branch `evidence/v79-engineering-benchmark-attempt-2240fd82-20261012`
- commit `b94367c6`
- path `docs/agent/V79_ENGINEERING_BENCHMARK_ATTEMPT_2240fd82_20261012/`

Outcome: failed closed before fit 1 at `ResourceMonitor` / `GetProcessMemoryInfo`; no NUTS fit, no diagnostics, no runtime projection. This is infrastructure failure evidence only, not model/science/resource-performance evidence.

PR #308 repaired only the Windows monitor boundary:
- exact head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`
- exactly 3 changed files: monitor code, unmocked Windows test, executor workflow wiring
- RED run `38280964089`: real Windows path reproduced `2 failed / 117 passed`
- GREEN run `38281216579`: Windows PASS, Ubuntu PASS, fit-side firewall PASS
- repair PASS comment `6128864889`
- fresh one-shot rerun authority comment `6128881654`
- canonical Macha execution instructions `6129078915`

Exactly one fresh benchmark rerun is authorized from #308 head `559a1c10...`. It has not yet been reported. No automatic second retry exists.

## Engineering topology now frozen for takeover

Historical source lineages:
- #300 campaign runner `7172b201b13c61634b84b85254bf4406959b2b57`
- #301 historical scorer `7fe0204b2661f0d1492115c973a4da7a4a1646b6`

Do not restart their old divergence reconciliation.

Reconciled integration base:
- #305 `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`

Active controller-scoring engineering:
- #306 `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`
- executor CI `38282050314`: Windows/Ubuntu PASS; static fit firewall PASS
- scorer CI `38282050318`: Windows/Ubuntu PASS; static scorer firewall PASS
- includes planted held-out oracle, five non-gating descriptive families, calibration/prevalence aggregation, and initial scoring-runner custody/authorization/write-once primitives
- physical scoring remains OFF

## New locator

Added:
`results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_CODE_DATA_RESULT_INDEX_20261012.csv`

It points to the principal scripts, frozen data authorities, realization evidence, benchmark failure evidence, repaired benchmark head, campaign-runner components, scorer components and living audit/handoff files.

Large local expression/calibration/checkpoint artifacts remain SHA/size inventoried only; they are not promoted to V79 authority and were not duplicated into Git.

## Execution state at this checkpoint

- regenerate Q00-Q11: FORBIDDEN
- fresh engineering benchmark: ONE rerun authorized only at exact #308 head `559a1c10...`; not yet reported
- Q00-Q11 qualification fits: OFF
- qualification scoring: OFF
- real TRAIN posterior: OFF
- factorial science: OFF
- TEST/Morabito/pathology: OFF in this lane
- target discovery: separate lane
- JEPA training: OFF

## Takeover rule

A future agent should compare live heads only against this checkpoint. If unchanged, do not repeat historical audits. If changed, audit only the delta. First unresolved external dependency is the single repaired benchmark result. First unresolved engineering dependency is any work after #306 head `d4e10c82...`.
