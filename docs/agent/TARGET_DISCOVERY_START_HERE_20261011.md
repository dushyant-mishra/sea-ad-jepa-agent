# Target Discovery — START HERE — 2026-10-11

For a new agent taking over the **real target-discovery lane**, read in this order:

1. `docs/agent/TARGET_DISCOVERY_CURRENT_HANDOFF_20261011.md`
2. `docs/agent/TD_G6_REPLACEMENT_AUTHORIZATION_ff4a21f9_20261011.md`
3. `docs/agent/TARGET_DISCOVERY_CANONICAL_TAKEOVER_20261011.md`
4. `docs/agent/TARGET_DISCOVERY_CANONICAL_STATE_20261011.json`
5. `docs/agent/TD_G6_ATTEMPT0_EXECUTION_RECORD_20261011.md`
6. `docs/agent/TARGET_DISCOVERY_HISTORY_AND_AUDIT_LESSONS_20261011.md`
7. `docs/agent/TARGET_DISCOVERY_EVIDENCE_CODE_DATA_INDEX_20261011.md`
8. `docs/agent/MACHA_TARGET_DISCOVERY_AND_PARALLEL_LANE_RUNBOOK_20261011.md`
9. `docs/agent/TD_V2_GOVERNANCE_QUALIFICATION_20261011.md`
10. Fresh successful G6-successor qualification evidence at `qual/td-g6-global-row-successor-ff4a21f9-20261011@8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`
11. Failed predecessor qualification evidence at `qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`
12. `docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md`
13. `target_discovery/HANDOFF_CURRENT_20260907.md`
14. `target_discovery/iterations/td33_global_row_binding_guard/TD33_SUMMARY.json`
15. PR #282 exact successor code/diff, PR #277 historical custody qualification/evidence, and PR #259 G4/G5 value-blind evidence.
16. PR #275 V2 tournament governance only after the real G6/G7/corrected-replay critical path is understood.

Current hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Current executable successor

PR #282 branch:

`fix/td-g6-global-row-binding-successor-20261011`

Qualified exact head:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

Fresh qualification terminal:

`QUALIFIED_FOR_REPLACEMENT_G6_INTEGRITY_EXECUTION__NO_BIOLOGICAL_AUTHORITY`

Qualification evidence:

- branch `qual/td-g6-global-row-successor-ff4a21f9-20261011`
- commit `8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`
- focused suite: **219 passed / 0 failed**
- real Sample-A freeze: **PASS**, `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`
- 25,000 rows: SEA_AD 22,561; NPH52 1,310; HVS 1,129
- real PR #259 compatibility: **PASS**, `1 passed / 0 skipped / 0 failed`
- worktree clean before and after
- no H5AD value read during qualification
- no G6/G7 execution during qualification

Only two test files differ from failed qualification head `7e482cf5...`; production common/G6/G7 scripts are unchanged from that repaired implementation lineage.

## Fresh authority

Owner decision:

`custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json`

Physical SHA-256:

`3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`

Runtime authorization:

`custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json`

Physical SHA-256:

`28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Bound identities:

- common `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6 `8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d`
- G7 `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

## Immediate real-TD task

`EXECUTE_REPLACEMENT_G6_ONCE_AT_ff4a21f9__FRESH_NAMESPACE__STOP_FOR_EXTERNAL_AUDIT`

The first real G6 at `fafd4309` remains preserved as:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

It is not a biological failure. `G6_OUT_fafd4309` is immutable historical evidence.

Replacement G6 is now authorized exactly once under the fresh authority above. G7 is **not operationally authorized** until the replacement G6 output is externally audited and accepted.

## Parallel V2 governance state

PR #275 is separate synthetic/metadata-only governance. Current exact head:

`0cbe6244756df3d1b7ed1ef4e1643aae0f94e875`

Qualification terminal:

`PASS_FULL_SYNTHETIC_METADATA_ONLY_V2_AUTHENTICATED_REGISTRY_TO_ADJUDICATION_CHAIN_197_OF_197`

Evidence:

- GitHub Actions run `38183565983`
- job `114601031751`
- artifact `11718374988`
- artifact digest `sha256:585f7799e0aba4935b37b28319570025de67ecf73d9aa7523a5bf6abeb74de61`
- **197 passed / 0 failed / 0 errors**
- clean before and after.

Qualified chain:

`V2 contract + execution context + authenticated candidate×gate governance registry -> external V2 prefreeze pin -> exact case coverage -> gate evidence -> full candidate manifest -> receipt -> adjudication`

This qualification is governance/software-only. It does not authorize a real tournament, biological value reads, target selection, TD60, Stage4, or training. Full RED→GREEN lineage is in `TD_V2_GOVERNANCE_QUALIFICATION_20261011.md`.

Corrected TD56/57B/57C/59 remain blocked.
TD60 remains never qualifyingly executed and must never be called failed.
Target selection, representation selection in this lane, Stage4 and real training remain blocked.
V79 is a separate lane.
