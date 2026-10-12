# V79 synthetic lane — current takeover pointer

Updated: 2026-10-12 17:05 UTC

Read first:

1. `docs/agent/V79_SYNTHETIC_LANE_AUDIT_HISTORY_20261012.md`
2. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
3. newest file under `results/v79/synthetic_lane_audit/deltas/`
4. `docs/agent/V79_SYNTHETIC_LANE_TAKEOVER_HANDOFF_20261012.md`

## Execution state first

The original PR #299 one-shot engineering benchmark authority was consumed and failed closed after about 3 seconds, before any model fit, because the Windows resource monitor passed an incorrectly typed process handle into `GetProcessMemoryInfo`. Frozen failure evidence remains immutable on branch `evidence/v79-engineering-benchmark-attempt-2240fd82-20261012`, commit `b94367c6`.

That bug is now repaired and independently qualified on PR #308:
- repair head: `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`;
- base: exact PR #300 head `7172b201b13c61634b84b85254bf4406959b2b57`;
- diff: exactly monitor code + real Windows regression test + executor CI wiring;
- RED run `38280964089`: Windows reproduced the failure (`2 failed / 117 passed`);
- GREEN run `38281216579`: Windows PASS including real `_rss_bytes()` / `ResourceMonitor`; Linux PASS; static fit-side firewall PASS.

Fresh controller ruling on PR #308 comment `6128881654` authorizes **exactly one fresh engineering benchmark rerun** from clean exact head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`, using fresh package/custody/result directories only. The old failed outputs must never be overwritten or reused. If the fresh attempt fails closed, there is no automatic second retry.

Q00-Q11 qualification fits and scoring remain OFF.

## Preferred live engineering topology

- PR #300 remains the historical campaign-runner engineering head: `7172b201b13c61634b84b85254bf4406959b2b57`.
- PR #305 remains the reconciled scorer/executor integration base: `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`.
- PR #306 is the active scorer-orchestrator engineering branch.
  - current head after monitor repair forward-port: `33efb404caf81a47f976fb39f472c7537aed8f52`;
  - executor CI `38281486760`: Windows PASS, Linux PASS, static fit-side firewall PASS;
  - monitor bytes/test are now carried forward exactly.
  - scorer CI is currently RED for a **pre-existing TDD step**: `tests/v79/test_v79_v2_core_score_runner.py` imports missing `run_v79_v2_core_scoring`. This is unrelated to the monitor repair and should be continued under TDD.
- PR #308 is the narrow benchmark-path repair and the only head currently authorized for the fresh benchmark rerun.

## Immediate actions

1. Execute the single fresh engineering benchmark rerun only from exact PR #308 head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`, locked Windows environment, fresh directories, Contract V2 engineering seed root `31999999`, 2 genes x 2 parts, never scored.
2. Preserve and report all benchmark receipts/hashes. If projected qualification runtime exceeds 72 h, STOP with no setting changes. If any failure occurs, preserve evidence and STOP; no automatic retry.
3. In parallel engineering only, continue PR #306 scoring-orchestrator RED→GREEN by implementing `run_v79_v2_core_scoring` without crossing the fit/controller trust-domain firewall.
4. Keep #302/#303 updated after either benchmark outcome or material #306 milestone.

## Authority boundary

- regenerate Q00-Q11: **FORBIDDEN**
- fresh engineering benchmark rerun: **AUTHORIZED ONCE ONLY at PR #308 head `559a1c10…`**
- Q00-Q11 qualification fits: **OFF**
- qualification scoring: **OFF**
- real TRAIN posterior: **OFF**
- factorial science: **OFF**
- TEST/Morabito/pathology: **OFF in this lane**
- target discovery: **SEPARATE LANE**
- JEPA training: **OFF**
