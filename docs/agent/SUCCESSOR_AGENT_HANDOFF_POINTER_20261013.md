# Audit-branch pointer to operational successor handoff — 2026-10-13

The operational takeover instructions live on the companion handoff branch:

- branch: `handoff/td-synthetic-crosscert-takeover-20261013`
- PR: #324
- file: `docs/agent/SUCCESSOR_AGENT_HANDOFF_TD_SYNTHETIC_20261013.md`
- handoff head at pointer creation: `afd807d8e942425fbc4afeed4d2b9e7827bea643`

This audit branch remains the independent custody/error-lineage companion. Its authoritative audit surfaces are:

- `docs/agent/TD_SYNTHETIC_HISTORICAL_CUSTODY_AUDIT_20261013.md`
- `docs/agent/TD_SYNTHETIC_HISTORICAL_NO_REPEAT_LEDGER_20261013.md`
- `docs/agent/CURRENT_LANE_GIT_OBJECT_INDEX_20261013.json`
- `docs/agent/PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`
- exact non-secret receipts under `archive/td_synthetic_crosscert_20261013/final/`

Current science boundary remains:

`READY_TO_EXECUTE_BLIND_FIT__PHASE1_ONLY_NEXT__AUDIT_BLIND_RECEIPT_BEFORE_CONTROLLER_TRUTH__REAL_TD_AND_TRAINING_OFF`

Do not repeat repository-wide historical audits simply because custody changed agents. Reopen only a concrete unresolved/contradicted item or changed byte/question.
