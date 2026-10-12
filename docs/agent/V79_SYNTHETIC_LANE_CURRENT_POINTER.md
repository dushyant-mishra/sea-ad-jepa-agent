# V79 synthetic lane — current takeover pointer

Updated: 2026-10-12 17:08 UTC

Read first:

1. `docs/agent/V79_SYNTHETIC_LANE_AUDIT_HISTORY_20261012.md`
2. `results/v79/synthetic_lane_audit/V79_SYNTHETIC_LANE_AUDIT_INDEX_V1.json`
3. newest file under `results/v79/synthetic_lane_audit/deltas/`
4. `docs/agent/V79_SYNTHETIC_LANE_TAKEOVER_HANDOFF_20261012.md`

## Execution state first

The original PR #299 one-shot engineering benchmark authority was consumed and failed closed after about 3 seconds, before any model fit, because the Windows resource monitor passed an incorrectly typed process handle into `GetProcessMemoryInfo`. Frozen failure evidence remains immutable on branch `evidence/v79-engineering-benchmark-attempt-2240fd82-20261012`, commit `b94367c6`.

That bug is repaired and independently qualified on PR #308:
- repair head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`;
- RED run `38280964089`: real Windows monitor tests reproduced the failure (`2 failed / 117 passed`);
- GREEN run `38281216579`: Windows PASS including real `_rss_bytes()` / `ResourceMonitor`; Linux PASS; static fit-side firewall PASS.

Fresh controller ruling on PR #308 comment `6128881654` authorizes **exactly one fresh engineering benchmark rerun** from clean exact head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`, using fresh package/custody/result directories only. Old failed outputs must never be overwritten or reused. If the fresh attempt fails closed, there is no automatic second retry.

Q00-Q11 qualification fits and scoring remain OFF.

## Preferred live engineering topology

- PR #300 historical campaign runner: `7172b201b13c61634b84b85254bf4406959b2b57`.
- PR #305 reconciled scorer/executor integration base: `e976d0c1a03f6a54dadcbf7fe3086f832fd319d8`.
- PR #306 active scorer-orchestrator engineering branch:
  - current head: `d4e10c821847078bac6d4043b18b09bdfb6c5ef1`;
  - executor CI `38282050314`: Windows PASS, Linux PASS, static fit-side firewall PASS;
  - scorer CI `38282050318`: Windows PASS, Linux PASS, static scorer firewall PASS;
  - monitor repair + real Windows regression test are carried forward;
  - first controller scoring-runner primitives are now GREEN: exact fit-ledger hash verification, canonical scoring-authorization validation, write-once JSON custody, frozen Q10/Q11 held-out model-metric convention, and downstream-off scoring-run receipt bindings.
  - there is still **no enabled physical scoring CLI**; qualification scoring remains OFF.
- PR #308 is the narrow benchmark-path repair and the only head currently authorized for the fresh benchmark rerun.

## Immediate actions

1. External/local Windows agent: execute the single fresh engineering benchmark rerun only from exact PR #308 head `559a1c104c8f1f56d2c05509eecf6b9dc05846a5`, locked Windows environment, fresh directories, engineering seed root `31999999`, 2 genes x 2 parts, never scored.
2. Preserve/report exact benchmark receipts/hashes. If projected qualification runtime exceeds 72 h, STOP with no setting changes. On any fail-closed error, preserve evidence and STOP; no automatic retry.
3. Controller engineering may continue #306 from `d4e10c82…` toward full composition of existing scorer modules, but must not enable physical scoring without a post-campaign scoring authorization.
4. Update #302/#303 after the benchmark outcome or the next material #306 milestone.

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
