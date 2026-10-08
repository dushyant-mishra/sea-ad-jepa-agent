# T0 B2 Production Entrypoint Acceptance Oracle V1

Status: **EXTERNAL REVIEW ORACLE — NOT PRODUCTION AUTHORIZATION**

A collection of individually safe helper functions is not sufficient for a
production B2 run. The production path must make it impossible to omit one of
the required checks.

## Required one-shot production flow

The production entrypoint may be named freely, but one callable must own this
entire sequence:

1. capture/authenticate the accepted broad-IMMUNE membership bytes;
2. capture/authenticate the COMPLETE Phase2 manifest bytes;
3. assert production manifest geometry:
   - 8,915 blocks;
   - 42 operators;
   - exactly 1,247 operator-31 MTG blocks selected internally;
4. capture/authenticate every selected metadata member;
5. build population closure and externally verify its parent identities/root;
6. build logical rows from the same bound membership;
7. build and externally verify the logical root;
8. build the physical plan and externally verify it restores the logical rows;
9. for every selected materialized block:
   - capture exact NPZ bytes once;
   - authenticate those bytes;
   - parse only those bytes;
   - require matrix width 41,238;
   - require parsed row count == manifest declared row count;
   - select only the bound block-local `row_index`;
10. authenticate the exact frozen MTG H5AD source identity;
11. read `layers/UMIs` from that authenticated source;
12. for every logical cell:
   - source row == `expression_row`;
   - source cell == `canonical_cell_id`;
   - source donor == `donor_id`;
   - source width == 36,601;
   - raw counts nonnegative integer;
   - full source-row sum == bound `source_library`;
13. project/normalize only from vectors proven by the above chain.

## Logical-root chain

The logical authority must bind:

- feature authority root;
- population closure root;
- logical_index;
- canonical_cell_id;
- donor_id;
- block_key;
- row_index;
- meta_path or deterministic reconstruction identity;
- meta_sha256;
- counts_path or deterministic reconstruction identity;
- counts_sha256;
- selection_row;
- expression_row;
- primary_row_weight;
- source_library.

External logical verification must establish:

`stored logical root == recomputed logical root == externally expected logical root`

and must separately require the externally accepted population-closure root.

## No detached raw-source proof

A function that accepts a caller-provided vector plus a dictionary saying
`source_sha256=<accepted SHA>` is not source authentication.

The row values used to prove `source_library` must be extracted through the
production entrypoint from the exact authenticated H5AD source itself, or from an
authenticated reader object whose construction and source identity are bound by
the production entrypoint.

## Unsafe helper containment

Legacy helpers may remain for unit tests, but the production entrypoint must not
use the old uncoupled pattern:

`verify_counts_payload(...) + independently supplied row_values`

nor:

`prove_source_library(caller_values, caller_provenance_labels)`

unless the caller values were produced by a bound authenticated extractor inside
the same production flow.

## Production terminal

Until this one-shot path is implemented and externally reviewed:

- `PRODUCTION_B2_NOT_AUTHORIZED`
- `DONOR_ROLE_GATE_SHUT`
- `real_execution_ready=False`
