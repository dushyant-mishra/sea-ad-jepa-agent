# V66 Stage-4 authority source map — 2026-10-01

Stage 4 remains **NOT AUTHORIZED**. This document maps each V3 authority label to its intended source so a future manifest cannot satisfy a vague label with the wrong artifact.

## Git-resident authority artifacts

| Validator label | Authoritative source | Authority branch/head |
|---|---|---|
| correspondence_design_contract_sha256 | results/v64/V64_NIH_CARD_E2_CORRESPONDENCE_DESIGN_CONTRACT_V1.json | ChatGPT V66 lineage |
| phase_b_statistical_contract_v3_sha256 | results/v64/phase_b_design/V64_PHASE_B_DOWNSTREAM_NULL_CONTRACT_V3.json | Claude 6c265d9c |
| phase_b_measurement_substrate_contract_sha256 | results/v64/phase_b_design/V64_PHASE_B_MEASUREMENT_SUBSTRATE_CONTRACT_V1.json | Claude 6c265d9c |
| phase_a_receipt_sha256 | results/v64/phase_a_v3/PHASE_A_V3_RECEIPT_PROVENANCE_PATCHED_V1.json | Claude accepted lineage |
| b6_v2_receipt_sha256 | results/v64/phase_b_design/V64_PHASE_B_T3_T4_AVAILABILITY_V2.json | Claude 6c265d9c |
| r3_conditioning_reference_sha256 | results/v64/phase_b_design/V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1.json | Claude 6c265d9c |
| phase_b_substrate_aggregate_receipt_sha256 | results/v64/phase_b_design/V64_PHASE_B_SUBSTRATE_AGGREGATE_V1.json | Claude 6c265d9c |
| phase_b_substrate_closeout_receipt_sha256 | results/v64/phase_b_design/V64_PHASE_B_SUBSTRATE_CLOSEOUT_V1.json | Claude 6c265d9c |
| phase_b_enum_intervals_sha256 | results/v64/phase_b_design/V64_PHASE_B_ENUM_INTERVALS_V1.json | Claude 6c265d9c |
| e2_edge_table_gzip_sha256 | results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz | accepted E2 lineage |

## Local authenticated scientific artifacts

These are not ordinary Git files and must be supplied by exact local path at validation time.

| Validator label | Artifact |
|---|---|
| t5_sha256 | PHASE_B_T5_DONOR_AGGREGATES.npz |
| availability_artifact_sha256 | PHASE_B_T3_T4_AVAILABILITY.npz |
| consensus_peak_set_sha256 | the exact NIH-CARD consensus-peak artifact bound in the Phase-B shard receipts |
| PHASE_B_SUBSTRATE_s00.npz ... s07.npz | the eight accepted Phase-B substrate shards |

The validator must hash the actual local bytes. A receipt, filename, or copied digest string is not a substitute for the artifact.

## Important semantic distinction

The E2 table is bound in V3 by its **gzip-file SHA-256**, not the historical uncompressed-content SHA. This was corrected because the generic authority validator hashes raw file bytes. V2 is preserved as superseded evidence of that mismatch.

The consensus-peak set is intentionally not assigned an invented repository path. Its authority comes from exact byte custody in the accepted Phase-B build lineage.

## Governance

- correspondence unopened
- Stage 4 not authorized
- training off
- multimodal training off
- Morabito protected
- TD60 blocked
