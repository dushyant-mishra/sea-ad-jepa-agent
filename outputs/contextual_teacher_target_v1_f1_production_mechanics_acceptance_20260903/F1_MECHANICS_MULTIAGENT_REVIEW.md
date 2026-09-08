# F1 Production Mechanics Acceptance — Specialist Review

Exactly three scoped specialist reviews were run after all result artifacts existed. The permanent Implementation Verifier was a separate veto gate.

## 1. Implementation / Topology

**VERDICT: PASS**

- Independently confirmed 474,188 unique forward identities: 43,108 teacher, 215,540 correct-student, and 215,540 matched-null.
- Confirmed compute-only dedup preserves all 44,496 assignments, with 43,108 unique `(cell,q)`, 1,388 dedups, and 222,480 unique effect rows; missing/extra/ambiguous are zero.
- Independently matched shard, forward, and effect roots and confirmed concrete-membership attacks fail closed.

Blocker/falsification: none substantiated.

## 2. Executor / Resume / Systems

**VERDICT: PASS**

- Confirmed exact 1,400-shard membership, portable physical IDs, byte-identical interrupted resume, and attack rejection.
- Confirmed the verified implementation commit is an ancestor and the current conclusion-bearing runner blob is byte-identical to the verified implementation blob.
- Confirmed the 1,200.8-second CUDA soak had zero swap, stable model/output/FD/CUDA behavior, and a runtime projection with components counted once.

Blocker/falsification: none substantiated after the test-only commit-binding repair.

## 3. Scientific Red-Team

**VERDICT: PASS**

- Confirmed mechanics-only scope and deterministic synthetic endpoint records.
- Confirmed only the accepted bounded technical fixture was opened during soak.
- Confirmed no real F1 biological result, scientific/statistical semantic change, training, backward, optimizer, EMA, protected/DEV/SEALED/pathology, or reader-validation/oracle access.

Blocker/falsification: none substantiated after the independently verified test-only repair.

## Dissent and resolution

Systems and Red-Team initially issued STOP because a verifier test incorrectly required the frozen implementation commit to equal the later report commit. The test-only repair now requires ancestry plus exact conclusion-bearing runner-blob equality. The focused WSL suite passed 50/50 and the permanent verifier independently reissued `PASS_IMPLEMENTATION_VERIFIER`. No scientific or runner bytes changed. Both critics then returned PASS.

Final specialist vector: `PASS / PASS / PASS`.
