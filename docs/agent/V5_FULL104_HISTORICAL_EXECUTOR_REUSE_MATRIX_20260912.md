# V5 FULL104 historical executor reuse matrix — 2026-09-12

Status: `HISTORICAL_MECHANICS_RECOVERY__REUSE_ONLY_AFTER_V5_REBINDING__NO_TRAINING_AUTHORITY`

## Purpose

Recover production-scale execution machinery already hardened elsewhere in this repository so V5 does not rebuild provenance, streaming, restart, publication and replay infrastructure from scratch.

This document imports **mechanics only**. It does not import historical biological estimands, T0/F1 targets, operator-specific constants, locality rules, thresholds, checkpoints, or execution authority.

## Recovered lineages

### A. FULL104 / Phase2 row-count authority mechanics

Primary hardened locus:

- commit `032ad149c76317466eae5f5e6b2fa8b451733fba`
- source `scripts/v4/t0_v20_row_count_authority_v1.py`
- red-team predecessor `760c68efdba022a14670fa5bcaa4c985e28b686d`

Reusable mechanics:

1. Authenticate the complete manifest before selecting any operator/subset.
2. Traverse every relevant block; no early exit after desired identities are first found.
3. Keep source/global/logical/block-local coordinates distinct and independently verified.
4. Couple authentication to consumption: capture bytes once, hash those bytes, parse those same bytes, then select/validate from that parsed payload.
5. Verify sparse payload format, shape, row bounds and integer/non-negative count semantics.
6. Bind membership and manifest parent identities into closure roots.
7. Reject membership/plan splicing after closure.
8. Require a physical read plan to restore the logical authority exactly.
9. Recompute closure/logical/physical roots from returned content and compare to externally expected roots.
10. Bind execution-path metadata and payload paths/digests into the authority object.

Historical constants such as operator 31, MTG source width, T0 membership, and T0-specific STOP names are **not reusable scientific authority**.

### B. F1 producer / independent replay mechanics

Primary hardened locus:

- commit `dd078625c3537f5ff2c3f8c0b382ba2803b24ee2`
- source `scripts/v4/f1_real_producer_v1.py`
- companion replay lineage `scripts/v4/f1_real_replay_v1.py`

Reusable mechanics:

1. Execution authorization is an external, pre-result, content-addressed artifact; no source boolean can be flipped to make a frozen producer runnable.
2. Authorization cannot contain produced roots, so result closure cannot retroactively authorize the run that produced it.
3. Lawful population is selected by frozen authority, not by treating adjacent labels as synonyms.
4. Atomic per-shard publication uses staging plus replace semantics.
5. Resume counts a shard complete only when its payload and required sidecars are complete and mutually bound.
6. Final roots are derived from produced bytes only.
7. Replay is intentionally independent: it must not import producer arithmetic merely to agree with it.
8. Producer may assert frozen geometry while replay independently derives the same geometry from source authorities.
9. Tracked source bytes and large untracked data bytes are different authority classes and must be hashed using the correct byte semantics.
10. Runtime object/module bindings are verified against what actually executes, not merely against caller declarations.

F1's evidence levels, query identities, matched-null scientific meaning, u0 checkpoint role, forward counts and biological readouts are **not** V5 authority.

## V5 porting decision

### Reuse directly as engineering patterns

- full-manifest authentication before selection;
- typed coordinate separation;
- payload-coupled authentication/parse/consume;
- closure and plan root recomputation;
- anti-splice parent binding;
- physical-plan-to-logical restoration;
- external pre-result run authorization;
- atomic shard publication;
- strict resume completeness;
- produced-byte closure roots;
- independent replay with no producer arithmetic imports;
- tracked-source versus untracked-data byte classes;
- runtime binding against actual loaded modules/assets.

### Re-derive under V5/FULL104 authority

- block-selection law over all 42 operators;
- reader-fit population geometry;
- native/ragged measurement support semantics;
- donor/operator proposal and weighting;
- finite relational triplet budget;
- common-core versus native-support relation view;
- V5 base-learning-step qualification evidence;
- V5 learned-teacher exposure milestone;
- TD60 geometry inputs;
- V5 anti-cheat attack identities and thresholds.

### Explicitly forbidden inheritance

- T0 pathology or donor-pseudobulk estimands;
- F1 QID/paired-wrong naming or matched-null semantics without V5 requalification;
- historical u10-u205 as biological teacher authority;
- operator-31-specific population constants;
- any historical training/execution authorization artifact;
- any historical biological threshold as a V5 threshold.

## Required V5 implementation order

1. Current-byte FULL104 closure using `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py` on the machine holding the >30 GB substrate.
2. Build a V5 execution-plan authority using the recovered provenance patterns over the FULL104 reader-fit population.
3. Add adversarial tests for manifest narrowing, coordinate substitution, payload swap, membership splice, read-plan relocation, truncation, duplicate rows and wrong byte class.
4. Add a separate bounded qualification-run authorization surface; do not grant production training authority.
5. Implement atomic shard/restart and independent replay for the bounded V5 learning-step qualification run.
6. Only after a valid `PASS_BASE_LEARNING_STEP_QUALIFICATION__NO_TRAINING_AUTHORITY` may a lawful exposure-defined base EMA teacher become eligible for TD60.
7. TD60, partial-evidence relational predictability and production relational training remain separate downstream gates.

## Current terminal

`PASS_HISTORICAL_EXECUTOR_MECHANICS_RECOVERED_FOR_V5_REBINDING__NO_EXECUTION_OR_TRAINING_AUTHORITY`

This terminal means the engineering patterns have been recovered. It does **not** mean the V5 executor exists yet, FULL104 has been rebound on current bytes, a qualification run is authorized, or training is authorized.
