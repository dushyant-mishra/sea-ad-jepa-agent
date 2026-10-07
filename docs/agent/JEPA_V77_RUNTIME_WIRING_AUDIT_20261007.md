# JEPA V77 runtime wiring audit — 2026-10-07

Status: **IN PROGRESS — NON-AUTHORIZING**

Purpose: durable custody of the historical-spillover and end-to-end wiring audit requested before any V77 mutation rehearsal. This branch started from PR #228 head `a14e27793ec6ed57c63be44bee5621c51bd9ad04`; it remains documentation-only.

## Governing prior audit

Primary handoff: `docs/agent/JEPA_RUNTIME_INTERFACE_CUSTODY_AND_HANDOFF_20261007.md` on `handoff/jepa-20261007-runtime-interface-custody`.

Accepted runtime checkpoint: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`.

Accepted low-level lineage recorded there:

- student encoder: V5 `KeyedIPBEncoderV2Reference`;
- V4 IPB/predictor mechanics;
- V4 gene tokenizer mechanics;
- teacher initialized as a parameter-identical frozen copy of the authenticated student and advanced only by guarded EMA;
- fixed historical EMA `.996` is **not** current V5 authority;
- canonical rehearsal EMA is presentation-normalized; no production half-life is selected;
- optimizer completion must be proven before EMA;
- canonical checkpoint/reload binds online/predictor/teacher/optimizer/scaler/cursor state plus typed continuation/provenance.

Standing hard boundaries: `TRAINING=OFF`, `STAGE_A_EXECUTION=OFF`, `MULTIMODAL_TRAINING=OFF`, `500K=NOT_AUTHORIZED`, `STAGE4=NOT_AUTHORIZED`, `TEST=SEALED`, `MORABITO=PROTECTED`.

## Active integration ancestry

Active integration branch: `integrate/v77-qualified-zero-update-20261007`.

PR #228 base: audited shared-qualification head `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`.

At audit start, PR #228 head was `a14e27793ec6ed57c63be44bee5621c51bd9ad04`. Its changes did not modify inherited V5 runtime/teacher/student/EMA source; they added only V77 adapter/join/test/workflow/plan surfaces. This establishes source ancestry, not complete end-to-end execution.

## Historical-spillover constraints

The joined path must fail closed against:

- global-row versus block-local/reset-row substitution;
- correct digest paired with wrong selected row;
- correct metadata paired with wrong consumed values;
- correct logical row paired with wrong physical payload;
- unbound provenance/hash substitution;
- query leakage and hidden-value/full-library normalization leakage;
- raw source/operator identity or dataset-ID proxies in learnable inputs;
- legacy `.996` EMA inheritance;
- parallel optimizer/EMA/checkpoint implementations;
- V1 diagnostic proof being promoted as mutation authority.

## Runtime lineage audit

The inherited canonical runtime constructs V5 `KeyedIPBEncoderV2Reference` as the online/student encoder, deep-copies it into a frozen/eval teacher, uses the inherited V4 `BlockPredictor`, and places only online encoder + predictor parameters into AdamW. Teacher targets are evaluated under `torch.no_grad()`. The guarded mutation harness requires gradient validation and exactly one optimizer step before EMA.

The shared runtime-binding layer keeps V1 diagnostic-only and requires the typed presentation-EMA V2 continuation proof for mutation promotion. No duplicate runtime implementation has been found in the V77 adapter.

## Progress on PR #228

The audit found the original “joined” test was not end-to-end. Work then proceeded under RED→GREEN GitHub Actions evidence.

### Executed proof/status gates

- RED `0d393d296ea5168e739fc4c3a5768e22844852d7`: policy-only q-safety could not count as executed proof; failed because no execution-bound gate existed.
- GREEN `0618e639fb2f124790e5fa3bf206fca0c971ff3a`: added fail-closed policy-only rejection.
- RED `6d891e51eec5494441200c00940ad8f428edab7d`: bare `PROVEN_BY_BOUND_ADAPTER_RUNTIME` enum could spoof proof.
- GREEN `1a4f2e8ebca66ed0c63fa4b1b4f2bcf03dd86dcb`: required typed `BoundAdapterQSafetyProofV1`.
- RED `0ceac519e1bab1578a25e3f6d4ee800f41d978d0`: typed proof was replayable without exact adapter/batch/runtime binding.
- GREEN `74f2b99d827e16134bf02c1820958442b78c37ee`: bound proof to exact adapter identity/digest, batch scientific identity digest, and runtime source digest.

### V77 -> shared qualification batch

- RED `3fe29343bd415bd18a5d1c27f85ccd21eeed44a0`: actual V77 `SyntheticConversion` had no route to `QualificationBatchV1`.
- GREEN `8e631460f3c286f46e34139431c990ec687ecb52`: added the physical bridge.

The bridge binds exact feature order, structural measurement support, source/operator rosters and mapping, donor grouping, query/evidence masks, adapter digest, manifest digest, split identity, and target identity. Visibility separation is preserved: student expression/masks are model-visible; query counts/full library are readout-only; donor identity is split-only; raw source/operator identity is stripped before learnable context.

### Executed S167/S168 query-leak challenge

A new test constructs two physical V77 synthetic observer worlds that are identical except for the hidden query count. Both are passed through the real `build_from_world` adapter.

The executed challenge verifies:

- hidden query/readout value changes;
- model-visible digest remains bit-identical;
- lawful operator-context digest remains bit-identical;
- mask/support/observation identity remain fixed;
- query values remain readout-only.

This directly re-exercises the S167 repair: the adapter computes `visible_library = full_library - hidden query counts` and normalizes student evidence using that visible library, so changing only the hidden query value does not perturb student normalization.

CI coverage itself initially omitted the new test; this was caught before claiming RED. Workflow commit `74135e3036e117b388fbd3bcfaabb824abcf109e` added the test to the focused gate. That run then failed for the intended reason: the executed proof function did not exist.

- RED gate: `74135e3036e117b388fbd3bcfaabb824abcf109e` (test originally introduced at `e7d943112e4a461ebf4f3dc5ce058ea9b5c13201`, but it was not counted as RED until CI actually executed it).
- GREEN implementation candidate: `1e6e28d895d9c9d2b04d754b4154884b74b02b1c`.

At `1e6e28d...`, the focused test step passed. The proof is minted only from an actually executed hidden-query perturbation and creates typed per-channel evidence for all required q-safety channels while remaining `execution_authorized=False`, `training_authorized=False`, `production_promotable=False`.

## 2026-10-07 late update — canonical ZERO_UPDATE and physical adapter-source binding

PR #228 advanced to `7664ce758c86b021b8614768a274edcb40f40783` while this audit branch was behind. The current changed-file surface is still constrained to workflow/plan, the V77 adapter, qualification join/zero-update bridge, and integration tests; inherited canonical V5 runtime source remains untouched.

The canonical ZERO_UPDATE bridge now exists at `src/sea_ad_jepa/qualification/v77_zero_update.py`. It imports and executes the canonical V5 reference constructor/checkpoint path rather than defining a second teacher/student/optimizer/EMA implementation. It computes a source manifest over the exact inherited runtime modules, constructs student/teacher/predictor through `build_reference_modules`, executes forward mechanics under `torch.no_grad()`, and requires exact invariance of online parameters, teacher parameters, predictor parameters, optimizer state, checkpoint digest, optimizer step count and teacher presentation count. It explicitly records `optimizer_step_performed=False`, `ema_performed=False`, `training_authorized=False`, and `production_promotable=False`.

A subsequent RED gate `787915d67575501c6fd4629c2a1c0c555f62da1f` required the ZERO_UPDATE receipt to be bound not only to the canonical V5 source manifest but also to the physical V77 adapter source. GitHub Actions run `37663195693` executed the joined test step and failed, so this is a real CI RED rather than an unexecuted test.

The branch then added a narrow source-binding facade at `src/sea_ad_jepa/qualification/v77_bound_zero_update.py` and updated the workflow/dispatch surface through `7664ce758c86b021b8614768a274edcb40f40783`. This facade is intentionally non-owning: it hashes the physical V77 adapter source, rejects a batch whose adapter digest is not that exact source digest, and delegates to the canonical ZERO_UPDATE implementation. No canonical V5 runtime mechanics were modified. As of this audit update, GitHub has not yet returned a workflow run for `7664ce758...`, so this candidate is **verification pending**, not GREEN.

## Separate S174 real-data repair lane — relevant but not part of PR #228

Macha independently value-verified S174: the historical Stage81A3R TRAIN cache carries the HVS/SEA-AD feature-axis scramble. The full TRAIN cache was rebuilt on separate branch `claude/s174-train-cache-rebuild-20261007` by fresh gene-ID join, with the old cache left untouched.

At rebuild head `70a27edb68319020104dc722aef9e2ef886ba74c`, frozen gates G2-G6 pass, while frozen G1 fails narrowly on SEA-AD because the independent reread does not follow 897 pre-existing provenance remappings. The follow-up explanation accounts for every discrepancy: HVS is exact, all non-remapped SEA-AD addresses are exact, every remapped entry equals its physical source count, and 100% of G1 disagreements are confined to the remap set. The frozen G1 remains FAILED; it is not retroactively rewritten.

Owner guidance recorded here: define and freeze a successor G1b prospectively. G1b may authorize the rebuilt cache only if the existing explanatory checks rerun exactly, there are zero unexplained discrepancies, collision exclusions remain unchanged, and the rebuilt-cache hashes remain identical. The separate identity question involving 353 historical Ensembl-ID remappings to different symbols must not be tuned based on replay outcomes. S149 and other affected real-data conclusions remain suspended until corrected replay.

## Remaining blockers before any bounded mutation

1. Obtain fresh GitHub Actions evidence for PR #228 head `7664ce758...` and close the physical adapter-source binding RED→GREEN cycle.
2. Strengthen physical row/value binding to cover the full Sept-8 chain: payload location/digest, donor identity, matrix slot/feature-space identity, reset/global/local substitutions, correct digest/wrong row and correct logical row/wrong physical payload.
3. Run the inherited runtime-binding regression tests, proving V1 cannot promote and V2 remains the only mutation-promotion route.
4. Perform final changed-file/spillover audit, including no `.996` inheritance and no alternate optimizer/EMA/checkpoint route.
5. Confirm the correct 2K rehearsal lineage preserves all 42 observation operators before any later bounded rehearsal.

Only after those gates are GREEN may exact runtime/interface/adapter/join SHAs be frozen for the preregistered tiny **synthetic** mutation rehearsal. Production or real-RNA training remains unauthorized.
