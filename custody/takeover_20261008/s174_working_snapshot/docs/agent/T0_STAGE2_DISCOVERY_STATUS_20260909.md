# T0 Stage 2 discovery status — 2026-09-09

Status: `DISCOVERY_STAGE_DONE_AND_REPLAYED__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN`

This file records the active T0 lane status observed from branch `t0/v20-pathology-blind-materialization-20260908`. It is not V5 teacher/student training authority.

## Verified branch state

GitHub branch head observed after the Stage 2B rerun:

```text
branch: t0/v20-pathology-blind-materialization-20260908
head:   237427c734bfdf7d00f286ceeae63692b3075d49
parent: 7aaf53d35f87524d3f0594ba27306ef6b6442d91
```

The head commit records:

```text
DISCOVERY_STAGE_DONE_AND_REPLAYED__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN
```

## Discovery run summary

```text
elapsed_seconds: 1736.9
discovery_donor_count: 28
discovery_cells: 13767
declared_addresses: 35076
matrix_nnz: 37085014
counts_payload_reads: 1885
counts_payload_cache_hits: 11882
endpoint_identity: percent AT8 positive area_Grey matter
endpoint_identity_sha256: 95870f7dd32101983ff710f7b394fcca4177da1525cc2a87342eb1a285155f89
endpoint_values_sha256: 4cfb572798ab3f48c08aaa74a841e4cb92c01cfc69303f0f3a45c006a81c671a
selected_multiplier_exponent: 2.0
final_lambda: 2360764.285714286
response_residual_sd: 1.2245513389820333
discovery_age_center: 88.53571428571429
decision_gene_count: 24482
```

Important roots:

```text
r7_package_root_sha256: a7e25e515f8e9cb4ec43e1e3bf09798adca6a573059d4b7ca0b61483c5c96c09
r7_readiness_root_sha256: a75581dfc5e7ea88609a9ef62f54765b9a495a7dbdc5c09152ba7fb76d1488ae
discovery_scalar_matrix_sha256: 456377fb5bd37a57aadf03a7a641bafc8d3b6e556b85dc9cfa827dccf02dd2b7
discovery_target_package_root_sha256: b29429021b551f3b26dadbc5ee20f57cec4e84cccc483943b73602f5bcfad8fe
discovery_provenance_root_sha256: 15d13dd3e733e0ea90b199cf981b03ccd94bc67fbd19660ef88861e3ae1a37c2
discovery_authority_package_root_sha256: 9806de382c75f7a7a12bb952631ed0b6c9b458250e8161a876b470c48898f6f7
logical_row_authority_root_sha256: 64ea880ff6cf19aca48e0f2e77edfa6d37fc4f5e20022011131c496173896fc3
population_closure_root_sha256: ec350b8d9a30a8a08573f055b9a0c103d0f6805014998ac9975d94585421d397
population_raw_source_root_sha256: 0b3e44897f0a5af1951677af95110e16d46f9a285fe227c31e34f45137b98f1b
```

## Gates still closed

```text
CONFIRMATION_NUMERIC_AT8_NOT_ACCESSED = true
DEV_OPENED = false
SEALED_OPENED = false
PROTECTED_POPULATIONS_OPENED = false
TRAINING_BEGUN = false
SUCCESSOR_U0_MATERIALIZED = false
TD60_RUN = false
BIOLOGICAL_SWEEPS_RUN = false
SCIENTIFIC_DESIGN_UNCHANGED = true
PER_DONOR_AT8_VALUES_EMITTED = false
NON_AT8_PATHOLOGY_ENDPOINT_PARSED = false
```

## Required next T0 work

Stage 3 confirmation is scientifically ready to open only under the staged runbook, but the current head records that the adjudicator path is still blocked by the same readiness contradiction at `t0_adjudicator_v2` lines 34 and 48. The next T0 work must repair or gate that adjudicator path before confirmation/adjudication can complete.

## Cross-lane boundary

This T0 discovery milestone does not authorize V5 teacher/student training, TD60, successor-u0, D1, DEV/SEALED, protected-population sweeps, or biological sweeps. V5 remains separately blocked on anti-cheat qualification and integrated trainer mechanics.
