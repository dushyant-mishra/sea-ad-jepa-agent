# JEPA Scientific Blocker Execution

Date: 2026-09-17

Status: `V5_STREAMING_FULL104_MASKING_EXECUTOR_PARITY_READY__CANONICAL_GPU_QUALIFICATION_NEXT__NO_MASKING_AUTHORITY__TRAINING_OFF`

Working branch:

`impl/v5-remaining-rna-target-semantics-20260917`

Verified code anchor:

`8ee5d0a5be483e18819a6f6975efa183327b2158`

## Scientific semantic invariant

The foundation objective is **not** numerical reconstruction of a hidden gene.

Masking removes molecular evidence and asks whether the remaining RNA supports recovery of the underlying biological/cellular state, including query-local biological state associated with the supplied masked address.

Accordingly:

- the address identifies which local biological state must be inferred;
- hidden scalar expression is not the JEPA target;
- ridge/correlation/nonlinear expression predictors are anti-shortcut diagnostics only;
- suppressing expression-proxy predictability does not by itself establish biological-state recovery;
- the masking policy must preserve a state-inference task.

## Closed implementation state

Implemented and CI-verified:

- canonical current authority roots/closure V2;
- preexecution V2, receipt V2, explicit training-authority schema, optimizer V3 and checkpoint V2;
- numeric masking qualification parameter authority with no production defaults;
- frozen masking qualification run-contract schema;
- masking qualification execution authority V2 bound to the run contract;
- canonical primary in-memory masking qualification reference runner;
- authenticated Level-4 streaming/sufficient-statistics masking executor;
- exact `log1p(raw*10000/source_library)` normalization once in the streaming path;
- train-only TOP8/RIDGE8/PREFIX3 partner selection and same primary ridge attacker across arms;
- parity of streaming target x fold results to the canonical reference on controlled raw-count fixtures;
- hash-corruption and duplicate-selection-row fail-closed behavior;
- streaming executor included in Stage-A/current-source spillover inventory;
- current closure rejection of legacy masking execution V1;
- fail-closed no-skip CI for all current focused suites.

Verified workflow runs at code anchor `8ee5d0a5...`:

- runtime closure: `35278901437` — SUCCESS
- FULL104 masking runner + streaming parity: `35278901430` — SUCCESS
- remaining-RNA / target-semantics: `35278901433` — SUCCESS
- Stage-A spillover: `35278901569` — SUCCESS

## Current exploratory evidence state

September 17 discovery still supports RIDGE8 as the strongest broad candidate tested so far under matched comparisons, with TOP8 as comparator and PREFIX3 as a sparse/selective arm. Nonlinear challenges remain supporting evidence.

This is **not** a production masking decision and does not freeze cap 8, ridge alpha 0.01, mask fraction, PREFIX3 thresholds, target count or other exploratory values.

## Streaming FULL104 blocker — closed

Current reference:

`src/sea_ad_jepa/v5/full104_masking_qualification_runner_v1.py`

Current streaming executor:

`src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py`

The executor consumes authenticated Phase-2 Level-4 blocks and row metadata, normalizes raw counts once, and accumulates per-donor sufficient statistics. It does not require a monolithic 4,553,407 x 17,186 CSR.

Parity tests cover:

- normalization;
- donor identity;
- training-only screening;
- TOP8/RIDGE8/PREFIX3 targeted partners;
- common-random base masks;
- exact burden-preserving swaps;
- ridge fitting;
- donor-centered heldout prediction correlation squared;
- source-balanced aggregation;
- deterministic result parity;
- block hash failure;
- duplicate selection-row failure.

This closes the **implementation/parity** blocker only. The real terminal FULL104 qualification remains unexecuted.

## Primary blocker now: canonical GPU worktree freeze and execution

The next authoritative work must happen on the canonical GPU/full-data worktree because this connector environment cannot truthfully create the machine-bound work checkpoint or access the >30 GB substrate.

### Immediate sequence

1. Build and validate `docs/agent/CURRENT_WORK_CHECKPOINT.json` with `scripts/agent/work_checkpoint.py` on the canonical worktree.
2. Authenticate/bind the actual Level-4 root:
   `D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`
3. Bind current donor/source registry, outer split, target panel, address-universe ladder and support eligibility to the physical expression blocks.
4. Prospectively instantiate/freeze the actual masking qualification design.
5. Prospectively instantiate/freeze the actual numeric parameter authority. Do not inherit exploratory constants silently.
6. Bind the exact canonical reference source SHA in the design and exact streaming-executor source SHA used for execution in the run contract.
7. Freeze the run contract **before** inspecting terminal qualification outcomes.
8. Execute the address-universe ladder through terminal `FULL_COMMON_CORE_17186_V1`.
9. Run all required positive/negative/replay/no-privileged-metadata controls and target-clustered precision. Report nonlinear challenge without retuning.
10. Issue the real `MaskingQualificationExecutionAuthorityV2` and bind a selected policy only if the frozen contract passes.
11. Continue real-evidence closure: healthy-current-teacher remaining-RNA necessity, measurement robustness, production geometry + geometry-specific memorization, runtime provenance and critical-test closure.
12. Issue final explicit training authority only after the actual current graph closes.

## Heavy-data references

Current GPU/external-drive Level-4 root:

`D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Historical corrected-cache root:

`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Historical provenance branch:

`planning/v5-full-population-cheat-proofing-20260909`

Historical helper files:

- `scripts/v5_anticheat/build_full_reader_expression_identity_closure_v3.py`
- `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

Historical code is provenance/support, not automatically current authority.

## Performance guardrail

The current streaming executor is an exact parity reference for the heavy path. It may rescan Level-4 blocks multiple times and has not been performance-qualified on the full 4.55M-cell run.

If I/O becomes the limiting factor, optimize through an authenticated sufficient-statistics/memmap cache whose outputs are parity-tested against the current streaming reference. Do not retune scientific parameters or inspect terminal outcomes to decide the optimization.

## Hard boundaries

- Training remains OFF.
- No pathology labels in foundation representation learning.
- DEV/SEALED RNA remain closed unless separately authorized.
- No D_shared outcome inspection while upstream masking/design choices remain open.
- Terminal FULL104 successor outcomes must not be inspected before the prospective run contract is frozen.
- Hidden-gene numerical expression reconstruction must not substitute for biological/query-local state.
- Historical T1 remains failure/adversarial evidence and cannot serve as healthy-teacher authority.
- Do not silently promote exploratory mask burden, cap 8, RIDGE8, PREFIX3, alpha 0.01 or other exploratory hyperparameters into authority.
- Legacy `MaskingQualificationExecutionAuthorityV1` is superseded for current closure.
- Skipped critical regression tests are failures, not passes.
- Do not require a monolithic FULL104 matrix.
- Do not substitute a smaller or unauthenticated cache for FULL104 terminal authority.

## Governance note

`AGENTS.md` requires validator-built `docs/agent/CURRENT_WORK_CHECKPOINT.json`. This GitHub-connector environment cannot truthfully generate and validate that machine/worktree-bound checkpoint because it does not own the canonical Git worktree.

The canonical-worktree/GPU lane must build and validate that checkpoint before authority-bearing promotion or expensive FULL104 execution.
