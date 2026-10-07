# JEPA b642dce6 decoder and 50K scope reconciliation — 2026-10-07

Status: `FULL104_DECODER_VERIFIED__50K_HVS_SEAAD_STILL_UNREBUILT__NPH52_AXES_VERIFIED__TRAINING_OFF`

This docs-only checkpoint corrects the immediately preceding contamination-boundary notes by incorporating the Sept-27 V29 repair lineage that was not fully folded into the first takeover pass.

## Verified historical sequence

- `b2231e9e`: retracted gene-level results after the HVS/SEA-AD Level-4 gene-axis failure was recognized.
- `5a217f92`: established that the counts themselves were intact and the defect was the gene axis.
- `b642dce643251b8b16117936da45efaf8af86e13`: identified the exact root cause and implemented a verified closed-form decoder for affected FULL104 Level-4 HVS/SEA-AD blocks.
- `9d30ef62`: established that NPH52 does not share the same `_COMMON`-family axis defect.
- `490d0ffdeba1d9b2bbb25eac98644141740dfce7`: proved that `foundation_materialize_discovery_expression.py` uses the same defective HVS_COMMON / SEA_AD_COMMON positional assumption, so the historical 50K HVS/SEA-AD discovery materialization is also affected.
- `778706f113814ff6b5f87d821fe5bc1c69d89862`: audited all six count-producing provenance consumers and classified the two HVS/SEA-AD `_COMMON` consumers as affected while independently verifying all four NPH52 per-object paths.
- `91b9725e`: later corrected myeloid panels using the decoder lineage; this remains a scoped corrected analysis rather than a general 41,238-address reader.

## What b642dce6 actually proves

The Level-4 root cause is exact:

`source_feature_index` for HVS_COMMON / SEA_AD_COMMON is a harmonized Ensembl-ID-order rank, while the physical H5AD `var` axis is in genomic order. The historical materializer applied the former as though it were the latter.

The decoder recovers the true canonical address represented by each existing Level-4 block column from authenticated source feature identity. It verifies decoded values against authenticated source cells before accepting them.

Verified receipt scope in `FULL104_LEVEL4_COLUMN_DECODER_V1.json`:

- HVS `c5e9db26-...`: 18,736 decoder entries, zero ambiguous, decoded agreement 1.0.
- HVS `19cd530b-...`: 18,736 decoder entries, zero ambiguous, decoded agreement 1.0.
- SEA-AD MTG: 34,242 decoder entries, 682 ambiguous columns excluded, decoded agreement 1.0.
- SEA-AD PFC/A9: same decoded scope and ambiguity rule, decoded agreement 1.0.
- SEA-AD caudate: same decoded scope and ambiguity rule, decoded agreement 1.0.
- NPH52 was not decoded by this H5 path because it uses a separate R/.qs lineage.

Therefore the prior statement that FULL104 necessarily requires physical rematerialization before any corrected use was too strong. For the matrices covered by the verified decoder, corrected interpretation/extraction can be performed from the existing Level-4 blocks without rebuilding them, provided ambiguous SEA-AD columns are excluded fail-closed and the exact decoder authority is bound.

## NPH52 disposition

The later provenance-consumer audit independently verified both NPH52 feature axes used by discovery and FULL104 consumers:

- TRAIN MG derivative: 33,441 object features, 32,176 provenance rows, 32,176/32,176 zero-based positional agreement.
- reader-fit MG derivative: independently verified on its own derivative rather than inferred from TRAIN.

The four NPH52 count-producing paths are classified `SOUND_VERIFIED` for this feature-axis issue.

## 50K discovery disposition

The historical 50K HVS/SEA-AD discovery materializer is confirmed affected by the same contract defect (`490d0ffd`). Its code consumes many HVS/SEA-AD operator/matrix objects beyond the five matrices explicitly listed in the FULL104 decoder receipt.

No general 41,238-address rebuilt discovery reader is established by `b642dce6` itself. The decoder mathematics may be reusable, but each 50K source matrix still requires authenticated matrix-specific feature-axis binding and verification before corrected 50K HVS/SEA-AD values can be treated as qualified.

Current classification:

- `FULL104_HVS_SEAAD_DECODER_SCOPE = VERIFIED_FOR_RECEIPT_LISTED_MATRICES`
- `FULL104_CORRECTED_EXTRACTION = AVAILABLE_WITH_DECODER_AND_AMBIGUITY_EXCLUSION`
- `NPH52_FEATURE_AXIS = VERIFIED_FOR_ALL_FOUR_AUDITED_COUNT_PATHS`
- `50K_HVS_SEAAD_DISCOVERY = DEFECT_CONFIRMED__GENERAL_41K_CORRECTED_READER_NOT_ESTABLISHED`
- `50K_NPH52_DISCOVERY = FEATURE_AXIS_VERIFIED`

## Macha/V77 interaction

Macha's S146/S147 repairs are separate and remain valid. They repair synthetic support/source-order semantics and do not repair historical real-H5 feature columns. Do not redo those repairs and do not conflate their synthetic address-order checks with real H5AD physical-column qualification.

## Execution boundary

No real-RNA rebuild or corrected 50K extraction is authorized by this checkpoint. Under the current mandate, preserve the decoder lineage and use it as design/authority evidence only. A full 41K HVS/SEA-AD discovery rebuild or generalized decoder execution requires explicit real-data-lane authorization.

Unchanged hard boundaries:

- `TARGET_WINNER = NONE`
- `REPRESENTATION_WINNER = NONE`
- `TRAINING = OFF`
- `REAL_RNA_STAGE_A_EXECUTION = NOT_AUTHORIZED`
- `STAGE_4 = NOT_AUTHORIZED`
- `NIH_CARD_REAL_BIOLOGICAL_CORRESPONDENCE = UNOPENED`
- `MORABITO = PROTECTED`

## Next audit action without real-RNA execution

Trace whether any later branch generalized the b642dce6 decoder to every matrix used by the 50K discovery producer without executing new real RNA. If no such authority exists, the missing work is precisely a generalized, matrix-specific decoder/rematerializer design plus tests/receipts, to be executed only after real-data-lane authorization.
