# FULL104 Dimension Project-Asset Audit Addendum — 2026-10-11

## Purpose

Record what can and cannot be completed from the current project-mounted assets after the prospective dimension-precision work in PR #270.

## Engineering state

PR #270 already provides the prospective Monte-Carlo precision authority and fail-closed metric-receipt validator. The existing frozen selector `scripts/v5_anticheat/derive_full_stream_dimension_family_v1.py` remains the downstream selection authority once lawful full-stream rank rows exist.

The required physical expression binder remains `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`, with required success terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

## Current project assets

The project provides substantial compact calibration, metadata, 41K discovery-expression material and T1 checkpoints. These are useful for representation diagnostics and were used in PR #276, but they are **not** the production FULL104 expression block store.

The required FULL104 substrate is approximately 4,553,407 cells × 41,238 addresses over 8,915 historical blocks and >30 GB of physical bytes. Those physical bytes are not mounted in the current runtime. The smaller 50K discovery archive must not be substituted.

## Consequence

No honest computation of full-stream D_shared, D_private or D_obs can be performed here. The remaining sequence is physical rather than conceptual:

1. authenticate the exact FULL104 blocks and cell identity with the binder;
2. require terminal `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`;
3. execute the frozen rank-metric protocol with the PR #270 precision authority;
4. validate every returned rank row against exact physical-binding and precision-authority SHA-256 identities;
5. apply the frozen shared/private/observation selectors;
6. independently audit the numerical result before any downstream production-width use.

No historical width (including 5/96/160/224/320/512) is dimension authority.

## Audit terminal

`FULL104_PRECISION_AND_RECEIPT_ENGINEERING_GREEN__CURRENT_PROJECT_RUNTIME_LACKS_PHYSICAL_FULL104_BYTES__NUMERICAL_DIMENSIONS_UNAVAILABLE__TRAINING_OFF`
