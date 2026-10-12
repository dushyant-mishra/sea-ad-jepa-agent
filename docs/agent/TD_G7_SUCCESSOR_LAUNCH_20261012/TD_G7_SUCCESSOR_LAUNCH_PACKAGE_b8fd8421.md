# TD G7 successor: launch package for the exact launch audit

Date: 2026-10-12

Terminal: `TD_G7_SUCCESSOR_LAUNCH_PACKAGE_QUALIFIED_AT_b8fd8421__R1_SCOPE_LOCKED__R2_PRESTART_REPLAY_PASS__G7_NOT_RUN__LAUNCH_AUDIT_ACCEPTANCE_REQUIRED`

G7 has not been run. No G7 start marker, receipt or output exists (`G7_OUT_8d41fb98` is absent). G6 was not run. No
corrected biological replay, TD56/57B/57C/59, TD60 or training. `training_authorized=false`.

## 1. Exact package

| item | value |
|---|---|
| authority commit (launch from a clean checkout of exactly this) | `b8fd8421b3ad0e1a4e80c7054aa4d41375966dd4`, branch `authority/td-g7-successor-launch-8d41fb98-20261012` (parent `9d466960`, then `8d41fb98`) |
| qualified implementation (execution worktree) | `8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27`: common `23be96f8`, G6 `8e6504e0`, G7 `275dad00` |
| owner decision `custody/owner_decisions/20261012/TD_G6G7_OWNER_DECISION_8d41fb98.json` | `c1bac85b4da9f447590b9f7172fc69f612b878a7ad851fc29f4efd87f2f0eaf1` |
| runtime authorization `…/TD_G6G7_RUNTIME_AUTHORIZATION_8d41fb98.json` | `be097fb21f58cbccea6b88cfad531eae4c8fbf3dc05582029f3d7dcc710bf1fa` |
| G7-only operational authorization `…/TD_G7_OPERATIONAL_AUTHORIZATION_8d41fb98.json` (schema V2) | `c171b91b853e9e136c28c3051cd3baae4e74a1be337f70b3d6ecdb175dd643ed` |
| launcher `scripts/v5/run_td_g7_successor_once.sh` | `c87fc4a299493fe9610765d559fbc0238ca7ab2854c2de92c6e49ceef14bb8e6` |
| launch checks `scripts/v5/td_g7_successor_launch_checks.py` | `dc832156756003c4bc117afb7e41950350082e1e78eac2a69ce02c7075955bac` |
| G6 predecessor | `ff4a21f9`, receipt `2edaa2d2`. Acceptance `89932183` is materialized from `17a68667`. |
| fresh G7 namespace | `D:/jepa_td_real_g6_20261011/G7_OUT_8d41fb98` (absent) |
| qualified environment | `C:/Users/dushy/anaconda3/python.exe` (SHA `a1685ca0…`): Python 3.9.7, numpy 1.24.2, pandas 1.5.3, scipy 1.10.1, h5py 3.2.1 |

All three records carry an explicit boolean `g6_execution_authorized=false` and every no-biology, TD60 and training flag set to false. They reference PR #296 review `5486851355`. The operational authorization pins:
- the owner and runtime SHAs;
- the accepted G6 (commit, acceptance and its source, five artifacts, receipt path);
- the fresh namespace;
- the launcher, the checks and the environment;
- the pre-start requirements;
- the launch-acceptance schema and path.

## 2. How the launch conditions are met

**R1 scope lock.**
- `td_g7_successor_launch_checks.py authority` refuses any record whose `g6_execution_authorized` is missing, true or non-boolean.
- It refuses any operational authorization that is not G7-only or that authorizes anything else.
- It refuses the spent ff4a21f9 authority (`3d457d4d`, `28b3a0c8`, `19a50126`).
- The launcher's only Python entrypoints are G7 and the checks. G6 is never invoked; a test enforces this.

**R2 pre-start replay.** `prestart` loads G7's own module from the exact execution worktree and runs, read-only, everything `main()` does before `begin_g7_attempt`:
- `bind_execution` with the fresh authority, which runs the code-consumed `load_owner_decision` and `load_runtime_authorization`;
- `expected_authority_trace`, producer continuity, `load_inputs`, and the accepted-G6 bridge.

It then replays the post-marker metadata prerequisites:
- G1b authority load;
- all 35 S174 shard hashes;
- all 34 HVS/SEA matrices covered;
- the matrix → stem → shard join, with each meta index loaded and each counts shard present;
- physical sources present at their frozen sizes;
- provenance identifiers unique per family.

Any failure stops before the marker.

**Fail-closed launcher** (`QUALIFY|EXECUTE`):
1. Pure checks run before any filesystem change; failure exits with code 64 and writes nothing:
   - arguments;
   - the launcher checkout is HEAD and clean, including ignored files;
   - the audited operational SHA, and in EXECUTE the acceptance SHA, are read straight from git objects;
   - the output namespace is absent;
   - the Python environment is the qualified one.
2. Every scratch path is timestamped, so a stop before the marker never blocks a corrected launch. The one-shot identity is only `G7_OUT_8d41fb98` plus G7's exclusive-create marker.
3. Every consumed file is pinned. Pins are repeated after the prestart, immediately before G7, and the materialized copies are made read-only.
4. **EXECUTE additionally requires your committed launch-audit acceptance** (section 4).
5. QUALIFY stops before G7. EXECUTE invokes the G7 entrypoint once, records an interrupt, preserves and hashes every record, and never repairs or reruns.

## 3. Qualification evidence (local, Windows)

- **Unit tests:** `tests/v5/test_td_g7_successor_launch_package.py`, **68 passed** (Python 3.9.7). They cover:
  - the committed records;
  - the code-identity constants against the git blobs;
  - the owner parser;
  - R1, with each record missing, true or non-boolean;
  - G7-only scope, bindings, cross-binding, launcher and check pins;
  - refusal of spent authority;
  - launch-acceptance positive and negative cases;
  - every R2 stop branch, using a stub G7 module;
  - launcher syntax, G7-only invocation, text ordering, timestamped paths, pure checks before any mkdir, re-pins after the prestart, and the trap.
- **Real QUALIFY at `b8fd8421`** (`qualify_b8fd8421_20261012T061713Z/`): `QUALIFY_PASS__STOPPED_BEFORE_G7__NO_MARKER__NO_G7_INVOCATION` in 1 min 44 s.
  - The authority check passes.
  - The G7 pre-marker path passes under the fresh authority, with trace 8d41fb98 / c1bac85b / be097fb2 / 275dad00 and accepted G6 receipt `2edaa2d2`.
  - The R2 replay passes: G1b result `c450815c` and freeze `0513421e`, **35/35 shards**, **34/34 HVS/SEA matrices** joined, and 23,690 HVS/SEA Sample-A rows.
  - 35 pin matches, covering both rounds.
  - The accepted G6 namespace is unchanged, the execution worktree is clean including ignored files, and there is no G7 output.
- **Negative pure-check runs** (`NEGATIVE_PURE_CHECK_RUNS_b8fd8421.txt`; console output, packaged after the run):
  - wrong operational SHA;
  - EXECUTE without acceptance;
  - EXECUTE with a nonexistent acceptance.
  - All three exited 64 with no new directory, worktree or output.
- **Superseded runs, preserved:**
  - `9d466960` QUALIFY (`superseded_qualify_…055955Z`): it passed, but its launcher had the stranded-path and no-re-pin defects;
  - its negative run (`superseded_negative_…055826Z`) stopped only after creating its scratch paths. That is the defect fixed in `b8fd8421`.
- **Independent read-only review of `9d466960`: VERDICT CONCERN.**
  - It found no path to the marker with a check skipped or with different inputs.
  - The must-fix items (stranded paths, re-pin before G7, enforced release, R2 stop-branch tests) are all fixed in `b8fd8421`.

## 4. What releases EXECUTE (yours to create; this package never creates it)

Commit a file at `custody/owner_decisions/20261012/TD_G7_LAUNCH_AUDIT_ACCEPTANCE_8d41fb98.json`, on any branch fetched into the local repository, with exactly this content (key order is free):

```json
{
  "schema": "JEPA_TD_G7_LAUNCH_AUDIT_ACCEPTANCE_V1",
  "disposition": "ACCEPT_G7_SUCCESSOR_LAUNCH_PACKAGE__EXECUTE_G7_ONCE",
  "implementation_commit_sha": "8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27",
  "authority_commit_sha": "b8fd8421b3ad0e1a4e80c7054aa4d41375966dd4",
  "operational_authorization_sha256": "c171b91b853e9e136c28c3051cd3baae4e74a1be337f70b3d6ecdb175dd643ed",
  "launcher_sha256": "c87fc4a299493fe9610765d559fbc0238ca7ab2854c2de92c6e49ceef14bb8e6",
  "launch_checks_sha256": "dc832156756003c4bc117afb7e41950350082e1e78eac2a69ce02c7075955bac",
  "fresh_g7_output_namespace": "D:/jepa_td_real_g6_20261011/G7_OUT_8d41fb98",
  "single_g7_attempt": true,
  "g6_execution_authorized": false,
  "biological_replay_authorized": false,
  "target_selection_authorized": false,
  "td60_authorized": false,
  "training_authorized": false,
  "corrected_biological_replay_authorized": false,
  "stage4_authorized": false
}
```

The launch is then this single command, run from a fresh clean detached checkout of `b8fd8421`:

```
bash <checkout>/scripts/v5/run_td_g7_successor_once.sh EXECUTE b8fd8421b3ad0e1a4e80c7054aa4d41375966dd4 \
  c171b91b853e9e136c28c3051cd3baae4e74a1be337f70b3d6ecdb175dd643ed <acceptance commit> <acceptance SHA-256>
```

## 5. Residuals for the auditor

- **R1 is launcher-enforced only (inherent).** Frozen G6 and G7 at `8d41fb98` cannot read `g6_execution_authorized`.
  - G6 `main()` would accept `c1bac85b`/`be097fb2` for any `--output-dir`.
  - G7 `main()` accepts any `--out`, so the code-consumed pair could support further G7 attempts outside this launcher.
  - Closing this needs a common, G6 or G7 change, which would break continuity with the accepted producer and the qualified successor.
  - Mitigation: after the single attempt, whatever its outcome, record `c1bac85b`, `be097fb2` and `c171b91b` as spent. Add them to the spent set used by any later launch check.
- **The window between pre-start and G7.**
  - Physical H5AD files are size-checked before the marker. G7 hashes each overlapping source after its marker (the same accepted residual as the ff4a21f9 launch; the accepted G6 authenticated all 34 on 2026-10-11).
  - H5 obs row identity is checked only after the marker, because checking it earlier would mean reading H5AD content.
  - A byte change to a cache shard or source between the pre-start and G7 would spend the attempt as a G7 STOP. It would not produce a false PASS.
- **Exit codes.**
  - The launcher's STOP is 64. G7 uses 0 for PASS, 3 for NOT_ESTIMABLE, 2 for a mismatch or stop, and 1 for an exception. An argparse error inside G7 would also exit 2.
  - The marker and receipt, not the exit code, are authoritative.
- **R4/R5 (from qualification):** non-blocking for this run, as you ruled.

STOP. Returned to the external auditor for the exact launch audit.
