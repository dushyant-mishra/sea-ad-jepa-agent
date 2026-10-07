# JEPA V77 runtime wiring audit — 2026-10-07

Status: **IN PROGRESS — NON-AUTHORIZING**

Purpose: durable custody of the historical-spillover and end-to-end wiring audit requested before any V77 mutation rehearsal. This branch starts exactly from PR #228 head `a14e27793ec6ed57c63be44bee5621c51bd9ad04` and is documentation-only at this checkpoint.

## Governing prior audit

Primary handoff: `docs/agent/JEPA_RUNTIME_INTERFACE_CUSTODY_AND_HANDOFF_20261007.md` on `handoff/jepa-20261007-runtime-interface-custody`.

Accepted runtime checkpoint: `9d00684e08ba34ef8d7b04e478b9c380cd36d537`.

Accepted low-level lineage recorded there:

- student encoder: V5 `KeyedIPBEncoderV2Reference`, unchanged through later audited V47/V48/V63 history;
- V4 IPB/predictor mechanics, unchanged through V63;
- V4 gene tokenizer mechanics, unchanged through V63;
- teacher encoder structurally initialized as a parameter-identical copy of the authenticated student and advanced only by guarded EMA;
- fixed historical EMA `.996` is **not** current V5 authority;
- canonical rehearsal EMA is presentation-normalized, with numerical half-life remaining an explicit non-production rehearsal input;
- optimizer completion must be proven before EMA; rejected/incomplete/non-finite-skipped optimizer steps cannot advance EMA;
- canonical runtime checkpoint/reload binds online/predictor/teacher/optimizer/scaler/cursor state plus typed continuation/provenance.

Standing hard boundaries remain: `TRAINING=OFF`, `STAGE_A_EXECUTION=OFF`, `MULTIMODAL_TRAINING=OFF`, `500K=NOT_AUTHORIZED`, `STAGE4=NOT_AUTHORIZED`, `TEST=SEALED`, `MORABITO=PROTECTED`.

## Active integration ancestry

Active integration branch: `integrate/v77-qualified-zero-update-20261007`.

Observed head at audit start: `a14e27793ec6ed57c63be44bee5621c51bd9ad04`.

PR #228 base: audited shared-qualification head `e83bb8d90bbabefdfe6bfa7c5dfff994d7a41005`.

GitHub compare `e83bb8d...a14e277...` reports exactly 8 commits ahead, 0 behind, and only five changed paths:

1. `.github/workflows/v77-qualified-zero-update-join.yml` (added)
2. `docs/superpowers/plans/2026-10-07-v77-qualified-zero-update-join.md` (added)
3. `scripts/v77/v77_synthetic_batch_adapter.py` (added)
4. `src/sea_ad_jepa/qualification/v77_join.py` (added)
5. `tests/integration/test_v77_joined_zero_update.py` (added)

Therefore this integration series does **not** modify the inherited V5 runtime/teacher/student/EMA source files relative to the audited shared-interface base. This establishes source ancestry only; it does not yet establish that the new execution path actually reaches the canonical runtime correctly.

## Historical-spillover constraints carried into this audit

The joined path must fail closed against previously identified failure classes:

- global-row versus block-local/reset-row substitution (TD23/TD33 class);
- correct digest paired with the wrong selected row;
- correct metadata paired with the wrong consumed values;
- correct logical row paired with wrong physical payload location;
- caller-supplied/unbound hash or provenance substitution;
- query leakage;
- full-library / hidden-value normalization leakage;
- raw source/operator identity or equivalent dataset-ID proxy reaching learnable inputs;
- legacy `.996` constant-EMA inheritance;
- direct/parallel optimizer, EMA or checkpoint implementations outside the canonical V5 runtime;
- V1 diagnostic runtime proof being promoted as mutation authority instead of typed V2 physical continuation proof.

## Evidence inspected at this checkpoint

### V77 join guard

`src/sea_ad_jepa/qualification/v77_join.py` currently adds:

- `PhysicalRowValueBindingV1`, which requires `source_row_index == expression_row`, selected block row equality, logical/source cell equality, valid SHA-256 strings, and `consumed_values_sha256 == authenticated_values_sha256`;
- `build_learnable_model_context`, which rejects raw measurement identity in model inputs, strips `source_index` and `operator_index` from lawful context, and fails closed on unreviewed operator-context fields.

This is directionally consistent with the recovered row/provenance and raw-identity constraints.

### V77 synthetic adapter

`scripts/v77/v77_synthetic_batch_adapter.py` explicitly declares itself runtime-agnostic and contains no trainer/optimizer/EMA/checkpoint loop. Its model/readout/oracle/split/operator structures are physically separated. It documents and guards prior S167/S168 hidden-value/full-library normalization leakage and S161 observer/truth identity leakage, and refuses pre-repair support/identity states rather than guessing.

This is evidence against duplicate runtime mechanics in the adapter, but the full executable join remains to be proven.

## Blocking finding: current “joined” test is not end-to-end

`tests/integration/test_v77_joined_zero_update.py` currently tests only:

- acceptance/rejection behavior of `PhysicalRowValueBindingV1`;
- removal of raw source/operator identity from learnable context;
- fail-closed rejection of an unreviewed operator-context proxy.

It does **not** instantiate/execute the advertised physical chain:

`repaired V77 synthetic world -> authenticated adapter -> QualificationBatchV1 -> shared qualification V2 -> canonical V5 runtime -> ZERO_UPDATE q-safety/row-value attacks`.

The workflow `.github/workflows/v77-qualified-zero-update-join.yml` only invokes that single test file. Therefore a green workflow at the current head would prove the local join guards, not that teacher/student/predictor/EMA/runtime/checkpoint surfaces are actually wired together through the V77 path.

This is a blocking audit gap. **No mutation rehearsal should be authorized from the current test surface.**

## Next repair sequence

1. Trace the exact exported shared-qualification APIs (`QualificationBatchV1`, executed q-safety proof, runtime-binding proof) and canonical public V5 runtime wrappers at the inherited base.
2. Add a RED end-to-end ZERO_UPDATE integration test that traverses those existing APIs without implementing a second trainer, optimizer, EMA or checkpoint path.
3. Add explicit assertions that the reached runtime provenance corresponds to the accepted canonical runtime lineage and that no private/legacy implementation can be substituted.
4. Exercise historical row/value, query-leakage and raw-identity attacks through the joined path, not only as isolated constructor tests.
5. Verify typed V2 proof is required for any mutation-status promotion; V1 remains diagnostic-only.
6. Run the focused workflow/tests on the exact resulting SHA, then perform a changed-file and historical-spillover audit.
7. Only after GREEN evidence, freeze exact adapter/interface/runtime SHAs for a small bounded **synthetic** mutation rehearsal. Production training remains unauthorized.

## Operational note

The local shell available to this audit could not clone GitHub because external DNS/network access is unavailable there. Repository inspection and any durable changes are therefore being performed through the authenticated GitHub connector. No conclusion is being inferred from a failed local clone.
