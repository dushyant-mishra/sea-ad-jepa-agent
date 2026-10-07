# JEPA Macha/V77 — S161/S162/S167/S168 anti-cheat audit

Date: 2026-10-06
Branch: `handoff/jepa-20261006-macha-audit-successor`
Parent observed before write: `6c945a1846c27541559f1b78d31524294175871b`
Working Macha head audited: `a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF__NO_SCIENTIFIC_AUTHORITY_CHANGE`

## Bottom line

The current S161/S162/S167/S168 repair is structurally real, not merely a test-label change.

Biological interpretation:

- the model no longer receives hidden query expression through normalization;
- full expression is physically stored outside the model-facing batch;
- donor identity is split-only;
- source/operator metadata are lawful measurement context rather than biological input;
- producer-side source/operator identity is checked by name and impossible source/operator combinations are refused.

The main residual shortcut is now the **measurement mask itself**. Because studies/technologies measure different address sets, the mask can reveal study/source. That is expected observation-process information, but its predictive strength has not yet been measured and therefore remains an open anti-cheat diagnostic.

## S161 — producer-side source/operator identity

Verified in current adapter:

- `source_index`, `operator_index`, `donor_index` are required in observer shards;
- old worlds without producer-side identity are refused;
- manifest rosters must be present and unique;
- operator→source mapping must cover the operator roster;
- every cell's operator source must equal its declared source;
- producer copies are cross-checked against truth copies when truth copies exist.

This closes the old path where measurement identity had to be borrowed from hidden truth.

## S162 — visibility separation

Current structures are physically separate:

- MODEL_VISIBLE: gene ids, student expression, measurement mask, hidden-target positions;
- LAWFUL_OPERATOR_CONTEXT: source, operator, visible library size, measurable count;
- SPLIT_ONLY: donor;
- READOUT_ONLY: hidden query counts and full library size;
- ORACLE_ONLY: planted latent truth.

The PR223 bridge additionally exposes only the corresponding visibility classes to each stage.

## S167 — normalization leakage

Verified current calculation:

`visible_library = full_library - hidden_query_counts`

Student CPM/log1p normalization uses this visible-only denominator. Thus changing a hidden query value does not alter student-visible normalized expression.

The adversarial test explicitly changes only hidden target values and requires identical model and operator-context digests.

## S168 — full-expression leakage

The current `SyntheticModelBatch` has no full-expression tensor or readout value. Hidden query counts and full library size live in `SyntheticReadoutRecord`, a separate structure.

This is a physical separation rather than a convention saying 'do not look at this field'.

## Feature identity: scope qualification

The adapter itself records `feature_identity` in provenance but does not authenticate the manifest's registry/address-order digests.

The current PR223 bridge **does** authenticate them:

- registry SHA must equal the current V77 registry SHA;
- address-order SHA must equal the recomputed ordered address-id digest;
- the production bridge calls this with `registry_check=True`.

Therefore:

`CURRENT_BRIDGED_REHEARSAL_FEATURE_IDENTITY = AUTHENTICATED`

but:

`ADAPTER_USED_OUTSIDE_BRIDGE = REQUIRES_ITS_OWN_FEATURE_IDENTITY_GUARD`

This is a scope boundary, not evidence that the current bridged receipt is invalid.

## Test-suite qualification

The bridge tests verify:

- pinned PR223 interface commit;
- model/operator/readout/split visibility;
- tampered measurement mask is refused;
- source/operator mismatch is refused;
- wrong interface commit is refused.

The adapter tests verify S161/S162/S167/S168 directly with informative fixtures.

The bridge unit fixture sets `registry_check=False` because it uses fake address IDs; the production bridge path sets it to `True`. Therefore the unit test suite does not itself prove the production registry digest check. The production code path and committed receipt are the relevant evidence for that check.

## Residual anti-cheat issue

### M-AC-1 — measurement-mask study/source shortcut remains unmeasured

`measurement_mask` is MODEL_VISIBLE. Real and synthetic source families have different support patterns by design. A classifier may therefore recover study/source from the mask alone.

This is not automatically a defect: the mask is legitimate evidence about what was measured.

The unresolved scientific question is whether a representation carries **more study information than is necessary after accounting for the observation process**.

Required diagnostic before any representation claim:

1. predict source from measurement mask alone;
2. predict source from lawful operator context alone;
3. predict source from visible expression after conditioning on depth/support;
4. later, predict source from learned representation after conditioning on comparable biology and observation process.

Do not optimize the system to make source completely unpredictable. The goal is to distinguish legitimate observation-process information from an unnecessary shortcut.

## Authority state

No change:

- TRAINING OFF
- Stage A OFF
- Stage 4 NOT AUTHORIZED
- TEST sealed
- Morabito protected
- no target winner
- no representation winner
- no selected estimand
- current seed-7302 rehearsal remains development/calibration only
- shared interface still does not prove physical zero mutation or executed transitive q-safety
