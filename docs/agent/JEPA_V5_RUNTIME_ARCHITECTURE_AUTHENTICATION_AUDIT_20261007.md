# V5 runtime architecture authentication audit — 2026-10-07

Status: **PRESENTATION-NORMALIZED EMA MECHANICS RECOVERED; CANONICALIZATION / PERSISTENCE AUDIT IN PROGRESS**

This checkpoint records the historical-spillover audit triggered before further PR #224 runtime changes. It does not authorize training, Stage A, real-RNA execution, target selection, or any production operating point.

## Verified low-level architecture lineage

The current PR #224 student encoder uses `KeyedIPBEncoderV2Reference` from `src/sea_ad_jepa/v5/keyed_dropout_prototype_v2.py`. The exact Git blob for that file (`0fd06ae0891625924761ef097b20ba6e11495cb3`) is unchanged on the later V47, V48, and V63 scientific/audit branches checked during this audit. The later scientific lineage therefore did not replace this low-level student encoder implementation.

The current PR #224 predictor/mechanics file `src/sea_ad_jepa/v4/ipb_jepa.py` has Git blob `3bd9d601a6779818a45c437cc21fd4a64749eb6e`, identical to the later V63 branch. The tokenizer `src/sea_ad_jepa/v4/gene_tokenizer.py` has Git blob `0fd283136323a49b5554f2fb33d0c65ee31be576`, also identical to V63.

The current rehearsal teacher is a parameter-identical deepcopy of the authenticated student encoder at construction and is then updated by EMA. This establishes the low-level teacher encoder mechanics only; it does **not** establish a scientifically qualified teacher target.

## Later teacher-science work does not supersede the low-level encoder

V43 is explicitly a read-only/research teacher-target design layer. Its workflow is non-authorizing and requires unapproved parameters to remain unset. Its target-construction primitive explicitly states that it is not model training and not current-V5 authority. V47/V48/V63 subsequently address specificity/identifiability/external-regulatory questions rather than replacing the keyed encoder, predictor, or tokenizer blobs above.

Therefore the current low-level student/predictor/tokenizer mechanics are accepted as the latest authenticated reusable mechanics found in the audited lineage. Scientific teacher-target semantics remain owned by the scientific qualification lane and are not promoted by this runtime audit.

## Confirmed historical spillover: EMA operating point versus EMA mechanics

The 2026-09-15/16 V5 current-authority lineage explicitly left the numeric EMA presentation half-life OPEN and prohibited silently inheriting historical `EMA 0.996` as current authority. User-supplied custody packages independently corroborate the same boundary: an older V3 configuration froze `.996`, while later V5 records separate mechanics from numeric authority and keep the current operating point unresolved.

The audit also recovered a newer authenticated V5 mechanical contract that PR #224 had omitted:

- `src/sea_ad_jepa/v5/ema_presentation_v1.py`
- momentum is presentation-normalized: `exp(log(0.5) * presentations_this_update / half_life_presentations)`;
- the source explicitly states that it **does not select a half-life**;
- the associated historical `ema_timescale_authority_v1.py` separates `presentation_unit_id`, `half_life_presentations`, momentum-function identity and schedule authority, while keeping `training_authorized=False`.

Therefore the canonical V5 EMA abstraction is **presentation-normalized**, not a fixed scalar momentum. The numeric half-life remains unselected.

A recovered candidate value of 16,249 successful presentations remains candidate evidence only; it is not frozen current authority. Historical `.996` remains an older V3/test value only.

## RED / GREEN sequence preserved on GitHub

1. Initial EMA-binding RED at `16a5946368e083cab4d0aafd7d80c179077166d6`: **35 existing tests passed; exactly 3 new failures** because no EMA configuration identity existed.
2. A temporary constant-momentum successor was added. Before accepting it as canonical, the local custody / historical-lineage audit showed that this abstraction was too narrow.
3. Presentation-normalized successor RED at `266246677353a5953a1f804e6e6ade711159bd83`: **38 existing tests passed; exactly 3 new failures** because `ema_presentation_v1.py` and a presentation-timescale identity were missing.
4. Exact authenticated presentation mechanics were restored and the presentation identity added. Focused runtime CI passed at `288cca9d2473dedca34115367763cd821cc3ddb4`.
5. Post-GREEN self-audit then found two spillovers: the runtime-source digest omitted the restored EMA mechanics, and the temporary constant-momentum issuer/runner remained an alternate executable route.
6. Canonicalization RED at `f6b31a3ac96104adf5cf0b05c67d65cbd108038e`: **41 tests passed; exactly 2 failures**, isolated to those two known spillovers.
7. The successor repair now adds the presentation EMA files to transitive runtime provenance and removes the constant-momentum issuer/runner in favor of a presentation-based authority and runner. Fresh CI is required before acceptance.

## Current canonical EMA semantics under test

The canonical rehearsal path must:

1. receive an explicit `half_life_presentations` and `presentation_unit_id`;
2. use `SUCCESSFUL_BASE_CELL_PRESENTATIONS` as the current authenticated mechanical unit;
3. derive the scalar momentum for each completed update from the number of base-cell presentations in that update;
4. reject caller-supplied scalar-momentum override on the canonical presentation route;
5. bind the EMA configuration identity to the exact parent runtime/checkpoint authority;
6. remain completely non-authorizing for training or production use.

No numeric half-life is selected by this runtime work.

## Required remaining self-audits before handoff

After the canonicalization repair is GREEN:

1. prove the EMA presentation configuration survives checkpoint persistence/restart and cannot drift silently;
2. prove `presentations_seen` advances only after a successfully completed optimizer+EMA transition and matches the actual base-cell presentation count;
3. ensure completed/persisted runtime proof carries sufficient EMA configuration provenance for #223 to reject mismatches;
4. close the previously identified `runtime_contract` physical-proof field mismatch if still present;
5. restack/revalidate PR #223 against the final #224 runtime head;
6. execute q-safety proof on the joined V77 adapter + shared interface + canonical runtime path;
7. run a final bypass and historical-spillover audit before any bounded synthetic mutation rehearsal is handed to Macha.

## Current classifications

| Surface | Classification |
|---|---|
| keyed V5 student encoder implementation | AUTHENTICATED REUSABLE MECHANICS |
| teacher encoder structural implementation | AUTHENTICATED REUSABLE MECHANICS (deepcopy + EMA), scientific meaning not implied |
| V4 predictor/IPB mechanics | AUTHENTICATED REUSABLE MECHANICS |
| gene tokenizer mechanics | AUTHENTICATED REUSABLE MECHANICS |
| scientific teacher target | UNRESOLVED / SCIENCE-LANE AUTHORITY |
| EMA update mechanics | AUTHENTICATED PRESENTATION-NORMALIZED MECHANICS |
| EMA presentation unit | SUCCESSFUL BASE-CELL PRESENTATIONS (mechanical unit) |
| EMA numeric half-life | UNSET / NOT PRODUCTION-AUTHORIZED |
| candidate half-life 16,249 presentations | CANDIDATE ONLY / NOT FROZEN AUTHORITY |
| historical `.996` | HISTORICAL V3 / TEST VALUE ONLY |
| PR #224 runtime handoff | BLOCKED UNTIL CANONICALIZATION + PERSISTENCE + FINAL JOINED AUDITS |

Hard boundaries remain unchanged: TRAINING=OFF; MULTIMODAL_TRAINING=OFF; STAGE_A_EXECUTION=OFF; 500K=NOT_AUTHORIZED; STAGE4=NOT_AUTHORIZED; TEST=SEALED; MORABITO=PROTECTED.
