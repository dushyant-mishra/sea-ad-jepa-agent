# V79 synthetic lane — current takeover pointer

Updated: 2026-10-12 16:58 UTC

Read first:

1. `docs/agent/V79_SYNTHETIC_LANE_AUDIT_HISTORY_20261012.md`
2. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
3. newest file under `results/v79/synthetic_lane_audit/deltas/`
4. `docs/agent/V79_SYNTHETIC_LANE_TAKEOVER_HANDOFF_20261012.md`

## STOP CONDITION FIRST — benchmark authority is spent

The single PR #299 engineering-benchmark execution authority was used once and is **SPENT**. The run failed closed after about 3 seconds, before any model fit, at the first Windows RSS/resource-monitor call. Evidence is frozen on branch `evidence/v79-engineering-benchmark-attempt-2240fd82-20261012` at commit `b94367c6`, under `docs/agent/V79_ENGINEERING_BENCHMARK_ATTEMPT_2240fd82_20261012/`.

Root cause is the Windows `ctypes` boundary in `scripts/v79/v79_v2_core_resource_monitor.py`: `GetCurrentProcess` had no `HANDLE` restype and `GetProcessMemoryInfo` had no typed argument signature. This defect is present in historical #300 and was also still present in #306 head `1be84ceb9e7f33f75c1c315f8a2e771b7185f214` when re-audited.

Repair is now isolated on PR #308, branch `fix/v79-windows-resource-monitor-20261012`, based on exact #300 head `7172b201b13c61634b84b85254bf4406959b2b57`. It adds a real unmocked Windows CI test before the production fix. **PR #308 does not restore benchmark authority.** A benchmark rerun requires a fresh controller ruling after the repair is green and independently audited.

## Preferred live lineage

- PR #305 reconciled scorer/executor successor remains the frozen integration base: `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`.
- PR #306 scoring-orchestrator successor is the active scorer engineering branch.
  - live head at this update: `1be84ceb9e7f33f75c1c315f8a2e771b7185f214`.
  - it still inherited the unfixed resource monitor at this head; do not execute benchmark or qualification from it.
- PR #308 is the active execution-path repair branch from #300.

Historical source lineages remain preserved:
- PR #300 campaign runner: `7172b201b13c61634b84b85254bf4406959b2b57`.
- PR #301 historical scorer: `7fe0204b2661f0d1492115c973a4da7a4a1646b6`.
Do not execute from either historical branch.

## Immediate engineering action

1. Complete PR #308 TDD repair and require Windows + Linux executor CI green, including the real Windows `_rss_bytes()` / `ResourceMonitor` test.
2. Port the exact repair bytes onto the current unified #306 lineage so the future scorer/executor successor cannot regress to the broken monitor.
3. Update #302/#303 with the green repair head and CI evidence.
4. Stop. Do **not** rerun the benchmark automatically.
5. Controller must issue a fresh, explicit benchmark-only ruling bound to the repaired exact head before any rerun.

The scoring-orchestrator work on #306 remains engineering-only and may continue structurally, but no physical fitting/scoring execution is permitted while the benchmark gate is unresolved.

## Current authority boundary

World regeneration is forbidden. The prior engineering benchmark authority is **SPENT / FAILED_CLOSED**. Benchmark rerun is OFF pending a new controller ruling after the monitor repair is green. Qualification fitting and scoring remain OFF. Real TRAIN posterior, factorial science, TEST/Morabito/pathology, target discovery in this lane, and JEPA training remain OFF.
