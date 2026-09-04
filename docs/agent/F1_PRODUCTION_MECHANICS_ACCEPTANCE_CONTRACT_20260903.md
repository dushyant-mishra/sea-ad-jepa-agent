# F1 production mechanics acceptance contract

Status: `FROZEN_PROSPECTIVE_PRE_RESULT_ENGINEERING_AUTHORITY`  
Date: 2026-09-03

This final cheap gate tests production-shaped identity, record, shard, resume, finalizer, and bounded WSL/CUDA mechanics only. It does not authorize real F1, biological endpoint calculation or inspection, final 11-gate adjudication, training, backward, optimizer, EMA, or changes to model, query, mask, null, inference, threshold, or scientific semantics.

## Accepted base

- branch: `f1-real-reader-forward-preflight-20260903`
- accepted repaired-preflight commit: `c533fdda40eb23e6a775277e98cbdfcee568ee8b`
- accepted package root: `52691e7d58ecc9c6460c7e2a7d9ae7350eea17be11e8c6e2242e18c21b46bbd2`
- origin/main must remain: `76fe7d63efe81451ef0fae3ef3eaf116be14f6be`
- assignment SHA-256: `12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617`
- compute-dedup SHA-256: `3fcd11908723e2cc80db0f5a0f017ad382bd1ed9be522f97081587ae989c2423`
- matched-null SHA-256: `aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6`
- accepted real-forward root: `007bc6f182354a133a2ec49ce0ef5966831d4995a0a2a5f004bb845772469ad3`
- permanent verifier: `MANDATORY_IMPLEMENTATION_VERIFIER_V1`, veto-bearing and required before GPU soak.

## Frozen topology

Evidence levels are ordered `20,40,60,80,100`. Assignment order is the frozen assignment CSV row order. Unique `(canonical_cell_id, selected_query_address)` compute order is first appearance in that order.

| Quantity | Exact count |
|---|---:|
| statistical assignments | 44,496 |
| unique `(cell,q)` | 43,108 |
| compute-only dedups | 1,388 |
| teacher identities | 43,108 |
| correct-student identities | 215,540 |
| matched-null-student identities | 215,540 |
| total expensive identities | 474,188 |
| assignment × evidence effect rows | 222,480 |
| logical donor×operator shards | 1,400 |

Each unique `(cell,q)` has one teacher identity, then one correct and one frozen-null student identity at each ordered evidence level. Teacher identity is evidence-invariant. Student identity includes evidence and role; null identity additionally includes the exact matched-null source. Correct/null, different query, and different recipient identities may not collide. The complete ordered identity root is SHA-256 over canonical compact sorted-key JSON identity records separated by LF.

All 44,496 assignments remain inferential records. Deduplication is compute-only. Every assignment retains program, draw, assignment key, cell/donor/source/operator, query, and five evidence mappings.

## Synthetic known-answer records

The acceptance run uses no real neural outcome. It constructs 222,480 deterministic float64 sufficient-statistic records from SHA-256 of `(assignment_key,evidence,field)` mapped to stable bounded values. The exact production record schema and downstream organization are exercised; an independent implementation reconstructs each value without calling production endpoint helpers. Synthetic values must vary with donor, program, draw, assignment, evidence, and query. They are never interpreted as biology or passed to a biological PASS/STOP gate.

## Shards, resume, and finalizer

Logical shard identity is the frozen `(donor_id,operator_index)` pair, lexicographically ordered. All 1,400 shard identities are exercised with tiny synthetic sufficient-statistic payloads through `AtomicShardStore`. Uninterrupted and interrupted/resumed final ordered bytes and semantic roots must match. Valid committed shards are reused.

The following attacks must fail closed: stale membership root; wrong forward root; wrong implementation/root commit; wrong dtype; wrong shard ID; reordered payload; missing, duplicate, or extra shard; corrupted payload; wrong assignment membership; wrong global order; missing/extra forward identity; missing/duplicate effect row.

The finalizer must require exactly 1,400 shards, 474,188 forward identities, and 222,480 ordered effect rows under bound roots.

## Bounded WSL/CUDA soak

After `PASS_IMPLEMENTATION_VERIFIER`, use the authenticated WSL environment and accepted fixed mechanics: batch 4, reader block 4, workers 4, prefetch 4, pinned memory off. Run repeated accepted technical-fixture forward cycles for a target 1,200 seconds, acceptable 900–1,800 seconds. Record at least five evenly spaced windows.

Hard safety limits remain: CUDA reserved ≤85% detected total; process RSS ≤80% start MemAvailable; zero `pswpin` and `pswpout` delta; unchanged model-state hash; no OOM/corruption/parity failure; no persistent unexplained RSS, CUDA-reserved, or file-descriptor trend plausibly exhausting the machine during the projected run. Do not retune.

Runtime projection uses exact role counts and measured stable role-rate windows. Unique physical block I/O is counted once. Report point estimate and the range obtained from the minimum/maximum eligible soak-window role throughput, with each nonoverlapping timing component counted once.

## Firewall

Expression may be opened only through the already accepted bounded 51-record technical fixture during the soak. Protected expression, DEV, SEALED, pathology, reader-validation/oracle, original mixed NPH, and full real-F1 expression are forbidden. Biological effects, training, backward, optimizer, and EMA must remain false.

## Promotion and terminals

Conclusion-bearing mechanics code requires an independent verifier report with terminal `PASS_IMPLEMENTATION_VERIFIER` before soak. After all artifacts exist, exactly three scoped critics review topology, systems/resume, and scientific firewall. Any substantiated dissent blocks PASS.

Success: `PASS_F1_PRODUCTION_MECHANICS_ACCEPTANCE_AWAITING_EXTERNAL_REVIEW`. This does not authorize real F1. Failure uses the controlling `STOP_F1_MECHANICS_*` or `STOP_IMPLEMENTATION_VERIFIER_*` terminal without weakening this contract.
