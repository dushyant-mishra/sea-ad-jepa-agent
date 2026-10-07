# JEPA Stage-A V3 donor split receipt — 2026-10-07

Status: `METADATA_ONLY__NO_EXPRESSION_OUTCOMES_OPENED`

## Source

The exact reader-fit donor roster was recovered from the already-authenticated Sept-8 handoff package:

`JEPA_NEW_CHAT_HANDOFF_V5_DATA_FIRST_20260908(1).zip`

member:

`v5/chat_local_evidence/v5_final_replay/TEACHER_STUDENT_READER_FIT_DONOR_SUPPORT_PROFILE_V1.csv`

The support-profile table has 196 rows but exactly 104 unique donor IDs because NPH52 donors recur across support fingerprints. Source-unique donor counts are exactly:

- HVS: 41
- NPH52: 17
- SEA_AD: 46
- total: 104

The split therefore deduplicates by exact `(source, donor_id)` before hashing. No expression value, pathology field, target score, model output, or protected outcome enters the split.

## Split-key clarification

For the materialized manifest, the exact frozen key is the `donor_id` field from the reader-fit support profile, not an unverified canonical-person alias.

Hash input:

`JEPA_STAGE_A_V3_SPLIT_20261007|<SOURCE>|<DONOR_ID>`

This receipt is the controlling clarification for the split-key wording in `JEPA_STAGE_A_PREFREEZE_DECISIONS_20261007.md`.

## Result

Deterministic source-stratified allocation:

| Source | INNER_TRAIN_FIT | HELD_DONOR_EVAL | Total |
|---|---:|---:|---:|
| HVS | 27 | 14 | 41 |
| NPH52 | 11 | 6 | 17 |
| SEA_AD | 30 | 16 | 46 |
| **Total** | **68** | **36** | **104** |

Exact manifest:

`docs/agent/JEPA_STAGE_A_V3_SPLIT_20261007.csv`

SHA-256:

`cc2c87cc7b8085f71850a7817cc28524ae518e109584da4cdfae07b2c6f75fe7`

## Held-donor identities

### HVS — 14

`H16.03.001, H18.03.323, H17.03.012, H18.06.005, H18.06.002, H15.03.003, H16.06.003, H15.06.008, H16.03.002, H18.06.363, H18.03.008, H15.03.005, H16.03.010, H19.06.362`

### NPH52 — 6

`human_NPH_910, human_NPH_898, human_NPH_1055, human_NPH_923, human_NPH_976, human_NPH_1069`

### SEA_AD — 16

`H20.33.024, H21.33.032, H20.33.039, H20.33.012, H21.33.028, H21.33.012, H20.33.030, H20.33.013, H20.33.036, H21.33.010, H21.33.009, H21.33.035, H20.33.043, H20.33.038, H20.33.037, H21.33.036`

## Authority boundary

This receipt freezes metadata partitioning only. It does not authorize Stage-A real-RNA execution, HVS/SEA-AD rematerialization, V77 cache rebuild, target-discovery replay, training, TEST, Morabito, reader_validation/oracle, Stage 4, 500K, or pathology access.
