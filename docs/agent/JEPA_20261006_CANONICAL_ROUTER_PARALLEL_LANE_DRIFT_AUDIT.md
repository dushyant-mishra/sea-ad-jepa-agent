# JEPA canonical router parallel-lane drift audit — 2026-10-06

Parent before write: `c7fab13d62f2e1ca8988c1a058869de308ea947d`
Scope: documentation-only Macha audit; no change to `main`.

## Finding

The live `main` startup surface still advertises the Oct-5 premise-qualification prefreeze as the single `current task`.

That is no longer a complete description of the active project frontier. Current work is split across at least:

- Macha/V77 synthetic-instrument audit;
- Stage-4/S149-aware scientific archaeology;
- PR #224 canonical V5 runtime convergence;
- PR #223 shared qualification interface;
- supporting/runtime predecessor reconciliation PRs.

The canonical startup files still preserve the important hard boundaries: training off, Stage 4 unauthorized, TEST sealed, Morabito protected, 500K unauthorized, no qualified production target.

Therefore the classification is:

`GOVERNANCE_ROUTER_STALE_FOR_PARALLEL_LANES__HARD_BOUNDARIES_STILL_VALID`

## Risk

A new agent following only `START_HERE.md` and `JEPA_LATEST_HANDOFF_POINTER.json` could restart or over-prioritize the Oct-5 prefreeze task and miss the newer lane-specific handoffs.

This is a routing/provenance risk, not a change in scientific authorization.

## Required future coordinated repair

When the lane owners coordinate a canonical-surface refresh, `main` should point to the current lane-specific handoffs and identify which lane owns which decisions.

This Macha lane does **not** edit `main`, because other agents are actively modifying runtime/shared-interface branches and a unilateral canonical rewrite would create cross-lane authority ambiguity.

## Authority unchanged

TRAINING=OFF; STAGE_A_EXECUTION=OFF; STAGE4=NOT_AUTHORIZED; TEST=SEALED; MORABITO=PROTECTED; 500K=NOT_AUTHORIZED; no target/representation/estimand winner.
