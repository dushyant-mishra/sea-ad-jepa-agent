# T0 external review checkpoint at producer head 24b2c9ff

Reviewed producer head:

`24b2c9ffc0ab2d63061c20af8829bcb86114b11a`

## Accepted directionally

- IMMUNE_FRACTION now has a one-shot parent-derived production constructor.
- IMMUNE support-count authority derives from authenticated membership and keeps
  the 80-cell floor tail-only.
- B2 complete-manifest internal op31 selection is repaired.
- B2 raw-source provenance labels are substantially checked, but actual H5AD row authentication remains open.
- B2 authenticated NPZ -> parse -> bound block-row extraction is repaired.
- B2 membership -> closure -> logical anti-splice is repaired.

## Remaining STOP 1: logical B2 authority chain

The logical digest still omits:

- `population_closure_root_sha256`;
- `meta_path`;
- `counts_path`.

The row verifier also does not require:

`stored logical root == recomputed logical root == externally expected logical root`.

Therefore the logical object can still carry a substituted parent-closure or
operational path identity while preserving the externally expected logical root.

Required repair:

1. bind the parent closure root in the logical root;
2. bind every execution-used path or remove paths and reconstruct them
   deterministically from bound fields;
3. type-check those fields;
4. add `expected_population_closure_root_sha256` to the logical verifier;
5. require stored == recomputed == external for the logical root.

## Remaining STOP 2: raw H5AD row is still not authenticated

`prove_source_library()` receives:

- `raw_source_row_values`;
- a caller-supplied provenance mapping naming source SHA, source row, cell,
  donor, width and matrix slot.

It does **not** receive or authenticate the frozen H5AD bytes/path/reader from
which those values were extracted. There is no H5AD reader/authenticator in the
B2 module.

Therefore a synthesized 36,601-wide nonnegative integer vector can be labelled
with the correct frozen source SHA, `layers/UMIs`, expression_row, cell and donor
and will be accepted if its sum equals the bound source_library.

Required repair:

1. capture/authenticate the exact frozen H5AD source identity;
2. read `layers/UMIs` from that authenticated source;
3. select exact `expression_row`;
4. verify source cell ID and donor ID from the same source;
5. compute the full-row sum from those exact extracted bytes/arrays;
6. use that extracted row for the source_library proof.

Provenance labels alone are not authentication.

## Remaining STOP 3: age/sex candidate-universe splice

The source pathology-metadata bytes are authenticated correctly and emitted
fields exclude numeric pathology. However, the production constructor currently
takes `candidate_donors` as a free caller list.

A lawful 84-donor source can therefore be paired with the wrong 46-donor subset.

Required repair:

Preferred:
- accept authenticated accepted membership bytes + externally expected
  membership SHA;
- derive the candidate donor set internally.

Alternative:
- accept an externally frozen candidate-universe/donor-set root and verify the
  caller list against it.

The loader must bind the same parent identity externally.

## Current terminal

`STOP_T0_24B2C9_EXTERNAL_REVIEW__B2_LOGICAL_CHAIN_RAW_SOURCE_NOT_AUTHENTICATED_AND_AGE_SEX_CANDIDATE_PARENT_UNBOUND`

Production B2 remains forbidden.
Donor-role gate remains shut.
`real_execution_ready=False`.
Numeric confirmation AT8 remains unopened.
