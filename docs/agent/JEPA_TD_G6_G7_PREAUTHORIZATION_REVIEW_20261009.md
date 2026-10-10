# JEPA Target Discovery — G6/G7 preauthorization readiness review

Date: 2026-10-10

Status: `SUPERSEDED_BY_STANDALONE_V2_DESIGN__DO_NOT_EXECUTE_CURRENT_WRAPPER`

This review remains useful historical evidence of defects found before any corrected value read. Its first wrapper-based implementation is **not** the future-authorized candidate.

No corrected expression values have been read. No G6/G7 runtime authority exists. No biological replay or training authority exists.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Findings retained from the first review

The historical dormant implementation had two prospective defects:

1. G6 V1 decoded physical H5AD values with `int(round(float(v)))`, which could silently round fractional/transformed values even though G4/G5 is intentionally value-blind.
2. G7 labeled zero natural S174 overlap as `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` but returned process exit code 0.

The first hardening pass introduced a V2 wrapper with strict finite/nonnegative/integer value checks and made G7 process-success only for actual exact-overlap PASS.

A subsequent self-audit found that this wrapper design is still not a sufficiently strong authorization boundary:

- it inherits the historical V1 preflight gate, which accepts a bare PASS status string instead of cryptographically binding the hardened V2 G4/G5 receipt and required mapping evidence;
- historical G6 checks H5AD presence/size immediately before value access rather than re-hashing the physical source at time of use;
- G7 likewise needs an independent immediate physical-source SHA check before its reread;
- the first V2 runtime authority does not bind exact preflight receipt SHA or exact G6/G7 code SHA;
- wrapper execution delegates to V1 `main()` and would emit V1 G6/cache schemas under a V2 authority, creating custody ambiguity.

## Controlling successor design

The future candidate is now specified in:

`docs/superpowers/specs/2026-10-10-td-g6-g7-standalone-v2-design.md`

Controlling design status:

`DESIGN_SPEC__NO_EXECUTION_AUTHORITY__NO_VALUE_READ`

The design requires a standalone V2 implementation, not additional monkey-patching of V1. Historical V1 remains preserved lineage.

The future standalone V2 must, before any value read:

- authenticate exact `JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V2` evidence rather than a bare PASS string;
- bind the exact preflight receipt SHA in the runtime authorization;
- bind exact G6/G7 script SHA values and entrypoint paths;
- independently re-hash each HVS/SEA source immediately before first value access in G6;
- independently re-hash each HVS/SEA source immediately before G7 reread;
- require finite/nonnegative/exact-integer physical raw values;
- preserve full-row library totals before replay filtering;
- preserve authenticated NPH52 pass-through hashes;
- emit V2-only G6 receipt/cache schemas;
- keep biological replay, target selection, TD60, and training explicitly false;
- keep G7 `NOT_ESTIMABLE` as a non-pass/non-success state;
- require full 41,238-address S174 cache geometry and zero-tolerance comparison of every natural overlap across all 9,216 replay addresses.

## Current sequencing

1. Claude/Macha executes only PR #248 G4/G5 code freeze `b3ff8366f28280e7d3269c305efa6317a05c8834`.
2. Any G4/G5 failure stops.
3. G4/G5 PASS is reviewed; it does not authorize values.
4. The standalone V2 successor is reconstructed/reconciled onto the exact G4/G5 execution lineage and developed by TDD.
5. Only after a separate explicit owner decision may a runtime V2 authorization be created.
6. Even future G6+G7 PASS stops before corrected TD56/TD57B/TD57C/TD59 biological replay.

Do not execute the current wrapper-based `materialize_td_relational_corrected_sampleA_v2.py` or use its current template as runtime authority. They are superseded implementation artifacts retained only for audit history until the standalone successor replaces them.
