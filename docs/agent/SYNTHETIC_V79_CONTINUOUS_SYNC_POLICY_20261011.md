# Synthetic/V79 continuous audit/handoff synchronization policy — 2026-10-11

Standing controller rule for the synthetic/V79 Bayesian geometry lane.

The canonical audit and handoff surfaces must be updated continuously as material work proceeds, not only at final closeout.

Canonical surfaces:
- audit PR #260 / branch `audit/v79-bayesian-geometry-snapshot-20261010`
- handoff PR #261 / branch `handoff/v79-bayesian-geometry-takeover-20261010`

At every material checkpoint, synchronize both surfaces together. Material checkpoints include:
- new code or CI qualification evidence;
- a failed-closed execution or numerical failure;
- a new data/provenance defect;
- a controller ruling or model-structure decision;
- a new or amended prospective contract;
- a world-generation freeze;
- a qualification PASS/FAIL/LIMIT terminal;
- a change in Bayesian authority status;
- any change that affects downstream factorial eligibility.

Each synchronization should update, as applicable:
1. current terminal state;
2. exact PR/branch/head/commit authorities;
3. code/CI run and job identifiers;
4. input/data hashes and custody facts;
5. result/evidence artifact paths;
6. scientific interpretation and caveats;
7. next allowed Macha task;
8. explicit forbidden work/firewalls;
9. machine-readable controller/audit state;
10. artifact index when new authoritative files appear.

If Bayesian authority status changes, also synchronize downstream factorial audit/handoff state (#264/#265) before scientific factorial work can move.

Historical failures and superseded contracts remain preserved; do not rewrite them as passes or silently delete them.

Target discovery remains a separate lane and must not be modified from this instruction set.

Current immediate state at policy creation:
`V2_CORE_STRUCTURE_PROVISIONALLY_PRESERVED__STRUCTURAL_SUPPORT_EVIDENCE_CORRECTION_REQUIRED__Q11_DONOR_AND_PPC_HARD_GATES_REQUIRED__QUALIFICATION_WORLD_GENERATION_NOT_YET_AUTHORIZED__TRAINING_OFF`
