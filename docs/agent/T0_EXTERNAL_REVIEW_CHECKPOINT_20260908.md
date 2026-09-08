# T0 External Reviewer Checkpoint — 2026-09-08

Producing branch:
`t0/v20-pathology-blind-materialization-20260908`

Producing head reviewed:
`760c68efdba022a14670fa5bcaa4c985e28b686d`

External review branch:
`review/t0-positive-path-external-20260908`

## Scientific freezes added by external review

### IMMUNE_FRACTION

Formula:

`IMMUNE_FRACTION(d) = immune_n_donor(d) / total_op31_reader_fit_n_donor(d)`

The exact integers are primary; the float is derived at the consumer boundary.

Formula document SHA-256:
`2e2bc9046e49e9459f1186d0d0373b82e2836a375b471adb949d8ab3261e51f4`

Formula document Git blob:
`280d17e6d34e4529fd559cbc90d0892459e286fd`

Verified production geometry:
- 46 donors;
- numerator total 20,804;
- reader-fit op31 denominator total 638,150;
- reader_validation 173,736 excluded;
- reader_oracle 121,386 excluded.

This is a successor specification resolving an undefined V18 input, not a claim of recovered executable V18 ratio semantics.

## External interface specifications

Frozen on this review branch:
- donor metadata authority;
- IMMUNE support-count authority;
- threshold-free technical completeness authority;
- stagewise pathology-blind estimability preflight;
- one-shot positive-path execution plan.

## Current producing-head blockers

Production B2 remains unauthorized.

IMMUNE_FRACTION current producing implementation remains candidate-only because:
1. `build_authority` accepts finished rows plus detached parent digest labels;
2. no one-shot production constructor derives rows internally from authenticated parents;
3. loader lacks external membership / complete-manifest / derivation-code / formula-root expectations;
4. formula freeze is not yet bound into the producing authority;
5. loader captures the internal manifest but does not validate its registry/metadata rows against captured member lengths/digests.

The review branch contains explicit red tests for these boundary defects.

B2 also still needs the expanded external attack set:
- membership -> closure -> logical anti-splice;
- authenticated NPZ -> parse -> block-local row coupling;
- counts matrix row/width geometry;
- stored == recomputed == external logical/physical/closure roots;
- execution-used path binding or deterministic reconstruction.

## Positive-path tooling

External local package:
`T0_POSITIVE_PATH_WORK_PACKAGE_V2_20260908.zip`

Package manifest root:
`7943f496b8c9f8ff0af50d67c1b2fccd3049a97f54eb1e54873e209e5472ebe8`

ZIP SHA-256:
`e7b394cb9be1a1a92107a28314c64e28a088d7d36eba85077239451105eba706`

Local mechanics:
- Python compile PASS;
- 9/9 positive-path tests PASS;
- manifest verification PASS;
- ZIP CRC PASS.

The simulator has no approximate statistical fallback and requires externally supplied accepted-code digests for both the V20 adjudicator and studentized Freedman-Lane implementation.

No real AT8 outcomes were used.

## Upstream-interface package

`T0_UPSTREAM_INTERFACE_SPECS_V1_20260908.zip`

Package manifest root:
`53a81c683d927493a0b41312089535d003eff868d7b219f2e25aa438e5f4abeb`

ZIP SHA-256:
`7791e8d52027847c3b2d649dc315ec847b529a6e765a50a3962e05f3e1a02e3d`

## Gate state

- production B2: STOP
- donor-role gate: SHUT
- numeric confirmation AT8: CLOSED
- `real_execution_ready=False`
- real T0: NOT AUTHORIZED

Next producing action: make the review red cases green without weakening gates, then hand the successor commit back for independent review before any production B2 run.
