# Claude — Start Here: Pre-F1 Mechanism Repair

Date: 2026-09-05  
Branch base: `76fe7d63efe81451ef0fae3ef3eaf116be14f6be`  
Status: **NO REAL F1 BIOLOGICAL OUTCOME HAS BEEN OPENED. REAL F1 REMAINS FORBIDDEN.**

## Purpose

Consolidate the pre-F1 repairs and perform only the bounded mechanism work needed to decide whether the planned contextual-target training path is mechanically trainable.

Do **not** treat the historical T1 architecture, current F1 forward evaluator, and planned post-F1 architecture as the same thing.

They are three different paths:

1. **Historical T1 training**: IPB + historical `BlockPredictor` + graph-expanded block-mean targets + `block_jepa_loss`.
2. **Current F1-A evaluator**: frozen u0 online encoder + parameter-free `LayerNorm(h_q - mu_context)`; forward-only; no predictor; no optimizer.
3. **Planned post-F1 mechanism**: direct lawful-state route + nonlinear contextual residual + singleton/query-local predictor + directional pair context objective. The exact historical implementation exists only in a local handoff export and has never been production-imported/trained.

## Critical new forensic finding

Recovered checkpoints u10/u25/u50/u100/u200/u205 show:

- all query Adam first/second moments = exactly zero;
- all key Adam first/second moments = exactly zero;
- all value Adam first/second moments = exactly zero;
- attention output projection moments = nonzero;
- Q/K/V movement follows pure AdamW decay closely;
- routing remains essentially uniform across operators at u205.

A bounded local FP32 replay of the same JEPA loss produces nonzero Q/K/V gradients. Therefore the historical T1 CUDA production path had an optimizer/gradient-path failure that is **not yet localized**. Do not conclude the ELU+1 architecture is intrinsically incapable until the CUDA defect matrix is run.

## Permanent governance correction

Phase-E already existed as the mechanics gate and passed because it aggregated the entire six-block encoder as `IPB_shared`. It did not require parameter-wise gradient coverage.

Patch the mechanics contract permanently: every optimized parameter expected to receive loss signal must be checked for missing/exact-zero/nonfinite gradients and post-step optimizer moments. Attention Q/K/V must be reported separately from output projection.

## Exact execution order

1. Freeze/run the four-cell CUDA defect-localization matrix in `CUDA_DIAGNOSTIC_MATRIX_CONTRACT.md`.
2. Localize and mechanically repair the severed training path if the matrix reproduces it.
3. Build/authorize the miniature F1-B mechanism test.
4. Only after F1-B mechanics qualification may the expensive real F1-A biological execution occur.
5. Only after independently satisfactory F1-A and F1-B may the post-F1 contextual-target microtrajectory be considered.

F1-A contract/statistical repair can proceed in parallel. F1-A **execution** cannot.

## Important invariant

F1-A is forward-only on frozen u0 weights. Conditional on identical u0 bytes, forward bytes and evaluation design, its output is invariant to optimizer, AMP, gradient checkpointing, EMA, predictor trainability and all post-u0 training behavior.

Therefore:

> **F1-A PASS carries zero information about trainability.**

Its claim scope must say this explicitly.

## Historical planned source — exact-byte recovery required

The handoff identifies a historical file named:

`full104_model_components_v2.py`

containing at least:

- `DirectResidualStateHead`
- `SingletonQueryPredictor`
- `state_block_loss`
- `directional_pair_context_loss`

The exact file is **not present on current GitHub main or in this review packet**. Do not recreate it from prose. Recover the exact historical local bytes by filename, compute SHA-256, and add them to this review packet before treating the code as authority.

Also verify the reported absence of `DIRECT_INIT_MANIFEST.json`. Do not fabricate a direct basis.

## D_shared conflict

Closed FULL104 authority is `D_shared = null` at `TEACHER_BIOLOGY_LIMIT`.

The historical planned `Full104HeadConfig.validate()` reportedly rejects `shared_dim <= 0`.

Do not evade this by inventing a positive shared dimension. Treat it as an unresolved contract incompatibility.

### Minimal viable F1-B bridge

Until the direct basis exists and `D_shared=null` is resolved, the preferred minimal mechanism test is:

`IPBEncoder + SingletonQueryPredictor + directional_pair_context_loss`

This is not automatic production promotion. It is the smallest test of the query-local mechanism designed to defeat the global shortcut.

F1-B must have separate authorization because it performs optimizer steps, EMA updates and checkpoint writes.

## F1-B firewall

Gate only on mechanics. Biology-oriented quantities may be logged but must not select, tune, rescue or stop the run.

Required mechanics include:

- per-tensor gradient coverage;
- nonzero Adam moments;
- movement beyond pure decay;
- attention concentration;
- query-specific routing variation;
- optimizer/EMA correctness;
- finite numerical behavior.

Preserve a distinct outcome:

`HEALTHY_GRADIENTS_ROUTING_STILL_DIFFUSE`

That outcome is the one that would justify reopening attention architecture.

## Read these exact repository files at the base SHA

See `SOURCE_MANIFEST.md`.

Do not modify `main`. Work only on this review branch or an isolated worktree.

Do not open DEV, SEALED or pathology expression. Do not execute real F1.