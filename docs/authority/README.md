# Current scientific authority

This directory is reserved for the **currently binding** JEPA contracts and decision authorities.

## Admission rule

A file belongs here only when it materially determines one or more of:

- lawful dataset/population scope;
- model/target semantics;
- protected biological endpoints;
- query/evidence/null construction;
- statistical estimand, multiplicity or stopping rule;
- execution legality/firewall;
- promotion/qualification decision.

Historical or superseded versions belong under `docs/history/`, even when they remain scientifically informative.

## Byte-preservation rule

Frozen authority files should be copied byte-for-byte from the canonical working tree. Do not reformat, normalize line endings, rename internal identifiers, or rewrite prose merely for GitHub presentation.

Each mirrored frozen authority should be accompanied by or referenced from a manifest containing its exact SHA-256.

## Supersession rule

Supersession must be explicit. A newer Git commit does not automatically supersede an older scientific authority.

For every replacement authority, record:

- predecessor;
- successor;
- reason for supersession;
- whether the predecessor remains historical evidence or is scientifically closed;
- relevant exact hashes.

## Current priority families

The current mirror should prioritize:

1. FULL104 dataset/observation/firewall authority.
2. CONTEXTUAL_TEACHER_TARGET_V1 and F0 closure.
3. F1 two-draw query/population authority.
4. QID-v2 authority.
5. F1 final truth table and conclusion-bearing decision source.
6. Frozen HC3 `(5,0,4)` selection/integration authority.
7. Reader/forward/executor authority once prospectively frozen.

Generated outputs are not promoted into this directory merely because they are recent.
