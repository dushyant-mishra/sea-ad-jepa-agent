# V5 runtime architecture authentication audit — 2026-10-07

Status: **RUNTIME CONVERGENCE PAUSED ON EMA-CONFIGURATION BINDING RED**

This checkpoint records the historical-spillover audit triggered before further PR #224 runtime changes. It does not authorize training, Stage A, real-RNA execution, target selection, or any production operating point.

## Verified low-level architecture lineage

The current PR #224 student encoder uses `KeyedIPBEncoderV2Reference` from `src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py`. The exact Git blob for that file (`0fd06ae0891625924761ef097b20ba6e11495cb3`) is unchanged on the later V47, V48, and V63 scientific/audit branches checked during this audit. The later scientific lineage therefore did not replace this low-level student encoder implementation.

The current PR #224 predictor/mechanics file `src/sea_ad_jepa/v4/ipb_jepa.py` has Git blob `3bd9d601a6779818a45c437cc21fd4a64749eb6e`, identical to the later V63 branch. The tokenizer `src/sea_ad_jepa/v4/gene_tokenizer.py` has Git blob `0fd283136323a49b5554f2fb33d0c65ee31be576`, also identical to V63.

The current rehearsal teacher is a parameter-identical deepcopy of the authenticated student encoder at construction and is then updated by EMA. This establishes the low-level teacher encoder mechanics only; it does **not** establish a scientifically qualified teacher target.

## Later teacher-science work does not supersede the low-level encoder

V43 is explicitly a read-only/research teacher-target design layer. Its workflow is non-authorizing and requires unapproved parameters to remain unset. Its target-construction primitive explicitly states that it is not model training and not current-V5 authority. V47/V48/V63 subsequently address specificity/identifiability/external-regulatory questions rather than replacing the keyed encoder, predictor, or tokenizer blobs above.

Therefore the current low-level student/predictor/tokenizer mechanics are accepted as the latest authenticated reusable mechanics found in the audited lineage. Scientific teacher-target semantics remain owned by the scientific qualification lane and are not promoted by this runtime audit.

## Confirmed historical spillover: EMA operating point

The 2026-09-15 current-authority handoff explicitly left `EMA presentation unit/half-life` OPEN and explicitly prohibited silently inheriting historical `EMA 0.996`, optimizer defaults, geometry, masking, or target semantics as current authority.

No later prospective closure of the EMA half-life/timescale was found in the searched authority/commit lineage. The current update function is already parameterized by an explicit `ema_momentum`; it does not hard-code 0.996. However current tests/rehearsal fixtures still commonly supply `.996`, and the current checkpoint/mechanical-authority chain does **not** bind the EMA configuration.

This is a real proof defect: a restart or subsequent guarded update could use a different teacher timescale while retaining otherwise valid model/optimizer/scaler/checkpoint provenance.

Accordingly:

- `.996` is **NOT an authorized production EMA value**;
- any occurrence in focused tests is a **test-only fixture value** unless a future scientific/operating-point authority prospectively selects it;
- PR #224 must bind an explicit EMA-configuration identity to the mechanical checkpoint/authority path before runtime handoff;
- the bound identity is mechanical provenance only and does not itself make the chosen EMA timescale scientifically optimal or production-authorized.

## RED established

Commits `d9051093633ad0990d0f77226d1a884d51ee591c` and `16a5946368e083cab4d0aafd7d80c179077166d6` added and executed the focused EMA-configuration-binding RED.

GitHub CI result on `16a5946368e083cab4d0aafd7d80c179077166d6`:

- 35 pre-existing focused runtime tests passed;
- exactly 3 new EMA-configuration-binding tests failed;
- all three failed because the canonical runtime has no explicit EMA-configuration identity/binding surface yet.

This is the expected RED and is not accepted as a runtime regression.

## Required next repair

The next bounded repair must:

1. define an explicit, deterministic identity for the EMA configuration actually used by the rehearsal;
2. bind that identity to checkpoint/mechanical authority provenance rather than to an implicit historical default;
3. reject configuration drift before teacher mutation on the canonical guarded path;
4. carry the EMA configuration identity through completed/persisted proof sufficient to reject restart drift;
5. retain `training_authorized=false`, `execution_authorized=false`, and `production_promotable=false`;
6. avoid selecting a production EMA timescale or scientific teacher target.

After GREEN, perform a fresh bypass/spillover audit before returning to the previously established `runtime_contract` proof-field RED and PR #223 rebasing/binding.

## Current classifications

| Surface | Classification |
|---|---|
| keyed V5 student encoder implementation | AUTHENTICATED REUSABLE MECHANICS |
| teacher encoder structural implementation | AUTHENTICATED REUSABLE MECHANICS (deepcopy + EMA), scientific meaning not implied |
| V4 predictor/IPB mechanics | AUTHENTICATED REUSABLE MECHANICS |
| gene tokenizer mechanics | AUTHENTICATED REUSABLE MECHANICS |
| scientific teacher target | UNRESOLVED / SCIENCE-LANE AUTHORITY |
| EMA update mechanism | REUSABLE MECHANIC, CONFIGURATION BINDING INCOMPLETE |
| EMA momentum / half-life | UNSET / NOT PRODUCTION-AUTHORIZED |
| historical `.996` | TEST/HISTORICAL VALUE ONLY |
| PR #224 runtime handoff | BLOCKED ON CURRENT RED + FINAL AUDIT |

Hard boundaries remain unchanged: TRAINING=OFF; MULTIMODAL_TRAINING=OFF; STAGE_A_EXECUTION=OFF; 500K=NOT_AUTHORIZED; STAGE4=NOT_AUTHORIZED; TEST=SEALED; MORABITO=PROTECTED.
