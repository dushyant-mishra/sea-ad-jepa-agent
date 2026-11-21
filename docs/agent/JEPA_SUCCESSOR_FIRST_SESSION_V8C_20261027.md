# JEPA successor first session — V8c active read-first update (2026-10-27)

**This replaces V8b as the active first-session checklist, not as a historical record.** The V8b first-session file, V8/V8a/V8b audits and earlier RED source files remain unchanged.

- **Active handoff:** PR #460, this branch; this document is the operational front door.
- **Durable audit:** PR #322 exact V8c head `1a6e59d338906fa9da1cbbc4b93c918349a4a3c5`.
- **Historical-only handoff:** PR #323.
- **Historical index:** PR #322 `results/target_discovery/unified_qualification_v1/JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json` plus V8b supplement and V8c delta.
- **No-promotion authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## First reads — do not repeat history

1. This V8c document and `JEPA_SUCCESSOR_HANDOFF_V8_20261027.md` for navigation.
2. On PR #322, read `docs/agent/JEPA_POST_V8B_DELTA_V8C_20261027.md` and `results/target_discovery/unified_qualification_v1/JEPA_POST_V8B_DELTA_V8C_20261027.json`.
3. Read earlier V8b/V8a deltas and the complete V8a historical file index only for the needed subject; preserve all prior records.
4. Before work, fetch live heads of #457/#458/#459/#460/#461/#462/#463. PR titles, earlier lists and old CI are dated.

## What changed from V8b (exact historical heads)

- **#457** moved to `53ff7adc7eb01c84edb7abe623d67dfb848f408d`; latest E2G runs `40532275239` / `40532274784` GREEN. *Still only public reference context, not TF causality, biological qualification or Stage4.*
- **#459** Task4 X1 candidate remains `57e707149b46ca011eee096f01dc08b64aeb8f9f`. Its previous author-tested recovery cases were GREEN, but independent #462 **CONFIRMED TWO NEW RED**: positive-short-write write-ahead intent and event log durability. Preserve both earlier author successes and later adversarial failures.
- **#462** is reviewer-authored tests-only head `67d2336155624a8657d2ef3320c9bfff175951ee`. Linux run `40530824776`: 2 failed/199 passed/8 skipped; unified run `40530825628`: 2 failed/390 passed/8 skipped; Windows run `40531130624`: 2 failed/49 passed/7 skipped. **Task4 X1-S1/S2 incremental review REJECTED pending author repair; cumulative Task4 remains blocked.**
- **#461** `495350d477a0b7ba65c13dcab5032d443f939cd5` challenged the previously accepted Unified Task1 canonical encoder: run `40519155593` **8 failed / 27 passed**. Exact-type/fingerprint acceptance must be qualified for hostile inputs.
- **#463** is ChatGPT-authored scoped Unified Task1 repair stacked on Macha's unchanged #461 tests at initial exact SHA `84b05952112ca405436ee3ccf35cc1c0df53c14d`; initial focused CI `40533382517` GREEN. **Candidate only, not Macha/non-author accepted.** Re-fetch this head and its CI before acting. Do not auto-merge it into the frozen Task1–3 path.
- **#458** remains `3b08081d7fb3fa99cf1459b13cbe47d5b0962547`, 13 hostile Production Synthetic Task1/2 RED. **T2-D handwritten absence attestation cannot establish an authenticated scan.** Production Synthetic Task4 blocked.

## Ownership and next execution

1. **Macha:** address #462 X1-S1/S2 in #459, preserve reviewer tests unchanged; seek fresh independent incremental review and a separate non-author cumulative Task4 decision. X3 Windows/WSL and external issuer trust remain unqualified.
2. **Independent Macha/non-author reviewer:** adversarially review ChatGPT-authored #463 and run #461 tests unchanged, plus lawful fingerprints and any sibling-path hostile checks. Authorship independence applies; CI GREEN is not acceptance.
3. **ChatGPT/deciding lane:** resolve #458 PS canonicalization and T2-D authenticated issuance; Task3 dependency requalification follows only after accepted Tasks1–2.
4. **G7:** require physical observation/source/operator/address identities, authentic evidence rights and q-excluded depth with actual V3 deciding-row digest consumption. No pattern-heuristic substitutions.
5. **Downstream:** existing JEPA harness #326/#332/#351 and #451 narrow bridge; no new architecture, no Stage4, Tasks6–8 fixture-only.

## Local static verifier commands

On audit PR #322, current head:
```bash
python scripts/v5/verify_jepa_lane_audit_v8.py
python scripts/v5/verify_jepa_lane_audit_v8a.py
python scripts/v5/verify_jepa_lane_audit_v8b.py
python scripts/v5/verify_jepa_lane_audit_v8c.py
python -m pytest -q tests/v5/test_verify_jepa_lane_audit_v8c.py
```
V8c run `40532989787` verified **16 passed**; inherited V8/V8a/V8b and other exact-head audit workflows GREEN. These are static audit guards only.

On successor PR #460:
```bash
python scripts/v5/verify_jepa_lane_handoff_v8.py
python -m pytest -q tests/v5/test_verify_jepa_lane_handoff_v8.py
```

When a head moves, create the next **append-only** audit delta, qualify it, then refresh the successor pointer. Never overwrite frozen V8/V8a/V8b/V8c histories just to update a SHA. External ZIP/NPZ/PT files stay external; untrusted PyTorch checkpoint bytes must not be unrestrictedly unpickled. Windows and WSL locking is not yet cross-OS qualified.

**Never infer a target winner, representation winner, real training authorization, Task4/Task5 cumulative acceptance, authentic A7/G7, or biology from a fixture PASS, hash, or author CI.**
