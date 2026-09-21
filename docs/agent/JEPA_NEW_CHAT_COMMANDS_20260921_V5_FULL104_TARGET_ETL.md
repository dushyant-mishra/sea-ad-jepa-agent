# JEPA V5 new-chat takeover commands — 2026-09-21

## 1. Re-fetch before trusting this handoff

git fetch origin --prune
git rev-parse origin/integrate/v5-full104-gpt-claude-20260921
git show --no-patch --oneline origin/integrate/v5-full104-gpt-claude-20260921

Expected handoff scientific SHA:

3bf6b659de9bdd2711face82b50b47ec567ea449

If the live head differs, inspect the successor commits before acting. Do not reset or overwrite newer work blindly.

## 2. Recommended local scientific checkout

git checkout -B integrate/v5-full104-gpt-claude-20260921 origin/integrate/v5-full104-gpt-claude-20260921
git status --short

## 3. Read current authority in order

cat START_HERE.md
cat docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
cat docs/agent/JEPA_NEW_CHAT_HANDOFF_20260921_V5_FULL104_TARGET_ETL_CURRENT.md
cat docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260921_V5_FULL104_TARGET_ETL_CURRENT.json
cat analysis/v5_full104_dataset_etl_20260921/FULL104_DATASET_ETL_ATLAS_REPORT_20260921.md
cat analysis/v5_full104_information_channel_redteam_20260920/PHASE_IV_PREEXECUTION_AUDIT_REPORT_20260921.md
cat docs/agent/V5_FULL104_TARGET_DISCOVERY_HISTORY_TO_TD60_SUCCESSOR_20260921.md
cat docs/agent/V5_FULL104_RARE_BIOLOGY_PRESERVATION_PROSPECTIVE_20260921.md

## 4. Current CI evidence

Exact scientific-head runs:
- runtime closure: 35657896178
- remaining-RNA/target semantics: 35657896258
- Stage-A spillover firewall: 35657896169
- FULL104 masking runner: 35657896215

All four were SUCCESS at 3bf6b659de9bdd2711face82b50b47ec567ea449.

## 5. Safe local regression focus

python -m pytest -q   tests/test_v5_dataset_etl_guardrails_v1.py   tests/test_v5_evidence_estimability_contract_v2.py   tests/test_v5_score_term_evidence_contract_v2_edge_cases.py   tests/test_v5_audit_b_execution_contract_v1.py   tests/test_v5_audit_b_execution_contract_redteam_v1.py   tests/test_v5_audit_b_scientific_resolution_v1.py   tests/test_v5_audit_b_execution_preflight_v1.py   tests/test_v5_audit_b_production_burden_v1.py   tests/test_v5_masking_rng_replay_authority_v3.py   tests/test_v5_full104_target_qualification_sample_authority_v1.py   tests/test_v5_full104_teacher_relational_target_qualification_authority_v1.py   tests/test_v5_full104_rare_biology_preservation_authority_v1.py

## 6. Hard stop before expensive/full-data execution

DO NOT run Audit-B N1 yet.

First close:
- B2 scientific scope: precision/RSE scope, target weighting, zero-mean rule;
- B3 real RNG V3 receipt;
- B4 provenance-bearing successor execution contract.

Audit-B V1 is intentionally non-executable.

## 7. Target lane

The next legal target-lane work is pre-outcome only:
- materialize/validate the 105,553-cell target-qualification sample from authenticated metadata;
- finish and freeze the label-free rare-biology molecular evaluator/execution contract;
- keep pathology and rare/disease labels out of target construction;
- do not execute TD60 without a lawful learned teacher;
- do not turn training on merely to produce TD60 input.
