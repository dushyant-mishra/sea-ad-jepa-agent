# JEPA V18 — exact new-chat takeover instructions (2026-09-22)

## 0. Read authority and confirm live state
```bash
git fetch origin --prune
git show origin/handoff/jepa-v5-full104-b4-n1-rare-tail-20260922-v18:START_HERE.md
git show origin/handoff/jepa-v5-full104-b4-n1-rare-tail-20260922-v18:docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
git show origin/handoff/jepa-v5-full104-b4-n1-rare-tail-20260922-v18:docs/agent/JEPA_NEW_CHAT_HANDOFF_20260922_V18_B4_N1_RARE_TAIL_CURRENT.md
git show origin/handoff/jepa-v5-full104-b4-n1-rare-tail-20260922-v18:docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260922_V18_CURRENT.json
git show origin/handoff/jepa-v5-full104-b4-n1-rare-tail-20260922-v18:docs/agent/JEPA_V18_DATA_RESULTS_SCRIPTS_MANIFEST_20260922.json
git show origin/handoff/jepa-v5-full104-b4-n1-rare-tail-20260922-v18:docs/agent/JEPA_HISTORICAL_AUDITS_INDEX_20260915.md
```
Do not assume the named refs are still current. Inspect GitHub PRs #47–#51, exact commits and Actions first. Do not merge two parallel descendant PRs blindly.

## 1. Masking lane: CPU static review before any N1

Expected green PR #50 `e4b7e9f46842d66cd7db71b1df9de60fc037f971`; its parent #48 `979cacbc924c45e55ad57e239a2ed4b0429e88ef` is the B4 GPU read-only preflight PASS.

```bash
git switch --detach e4b7e9f46842d66cd7db71b1df9de60fc037f971
python -m pytest -q \
  tests/test_v5_audit_b_n1_cached_planner_v1.py \
  tests/test_v5_audit_b_n1_crossfold_planner_v1.py \
  tests/test_v5_audit_b_n1_execution_authority_builder_v1.py \
  tests/test_v5_audit_b_n1_execution_authority_v1.py \
  tests/test_v5_audit_b_n1_result_contract_v1.py \
  tests/test_v5_audit_b_n1_runtime_rng_bridge_v1.py
python scripts/agent/build_full104_audit_b_n1_execution_authority_v1_20260922.py --help
```
Inspect frozen JSON under `analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/`. Rebuild to a **new temporary path** only after inspecting builder CLI; compare canonical authority digest `eb3293720c54ae10023a90b73c1bf35b46b6cacfda70632522014d988ebb0096`. Audit exact 256-target sample, full 104 donor/4-fold x 3 policies x 6 rung coverage, no train/test leakage, deterministic RNG identity and no reroll by panel, full source/donor robustness reports, single predeclared RIDGE8@5% precision gate, N2 receipt only after N1 failure. Check full heavy executor integration separately. **Do not run N1** until end-to-end mechanics are independently reviewed and user authorizes its single execution.

## 2. Target lane: repair failing #51 CI before read-only preflight

**Update:** original PR #51 is historically red; use reviewed green test-only PR #52 exact head `213552a46903cd92b8a0338df185f0fce9655832`, workflow `35739933731` including no-skip SUCCESS. Read V18 PR52 addendum. Original #51 `f8718b66f1c8bf39787408582fbbc85d5ada97d5`, parallel base #49 `5503cd8c99506d172616b1e2edd8090eeaa41a05`. The structural sample has NPH52 fold 1–3 exactly four eligible donors; preserve them.

```bash
git switch --detach 213552a46903cd92b8a0338df185f0fce9655832
python -m pytest -q \
  tests/test_v5_full104_rare_tail_molecular_authority_v1.py \
  tests/test_v5_full104_rare_tail_molecular_execution_contract_v1.py \
  tests/test_v5_full104_rare_tail_molecular_primitives_v1.py \
  tests/test_v5_full104_rare_tail_molecular_runner_v1.py
```
Three original PR51 failures (fixed in test-only PR52; preserve audit history):
1. undefined `ROOT` in frozen TD59 strict-core hash regression test;
2. synthetic panel materialization test has fewer than 42 operators and triggers correct production fail-closed gate; fix fixture, not gate;
3. JSON list-vs-tuple comparison of the exact three NPH52 zero-slack cases; normalize representation without changing cases.
After changes, rebuild/freeze any source-hash-bound authority and contract **only if required**, keep previous JSON immutable in history, rerun all hosted normal and fail-on-skip suites on the new exact SHA. Verify proposed authority `0b5629ca5e7087b1535e006021ec35d24a981986d5096eb4c99f001294c4c000` and contract `e834285f652d35fe335d16c0e58eadf7ee2b0ffc11fb11035c4ba17a94b80c02` against the original source before repair. Do not run the molecular CLI on real RNA while CI is red. The next lawful GPU action after green CI and independent review is **read-only runtime preflight**, not opening molecular outcome.

## 3. Frozen heavy-data rules

On GPU machine, resolve Level-4 manifest, registry, heavy NPZ, frozen sample vectors and code sources **by receipt role and physical SHA**; never trust remembered path or substitute historical/partial ZIPs. Level-4 manifest SHA `66f589e5...`; registry `7d61ed7b...`; heavy NPZ `f77dff47...`; target sample canonical `72206542...`; Audit-B B4 canonical `c68231e5...`; structural receipt canonical `f0d71c9b...`. See V18 manifest for exact hashes and paths.

## 4. Stop and report

Do not open N1, masks, burden, terminal P1–P4, rare-tail molecular X/Y/Z, TD60, pathology/DEV/SEALED, D_shared/G5, or training. Return live heads, code diff, full test counts with **zero skipped**, exact receipt SHA and bytes, negative controls, open blockers, and whether an outcome was opened. Distinguish green CI from scientific PASS.
