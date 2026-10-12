# Measurement-Noise Synthetic Fixture Plan

**Goal:** Qualify a pure synthetic reference implementation for same-cell complementary count splitting and nested depth thinning without opening biological files or choosing a technology-equivalence margin.

**Spec:** `docs/superpowers/specs/2026-10-11-td-measurement-noise-floor-prefreeze.md`

## Constraints

- standard library only;
- no file readers;
- no corrected value access;
- finite/nonnegative/exact-integer semantics represented as nonnegative Python integer fixture counts;
- support universe fixed by caller;
- split A + B exactly equals original count at every supported address;
- measured zeros remain explicit zeros;
- nested depth grid exactly 25/50/75/100%;
- deterministic versioned SHA-256 PRF bound to seed, cell, address and molecule index;
- no biological or target authority output.

## TDD sequence

1. Add tests first and preserve module-absent collection RED.
2. Implement minimal pure helper.
3. Require focused fixture tests GREEN.
4. Require complete science-harness GREEN.
5. Record exact hashes and explicit limitation: this is a synthetic reference, not an authorized raw-count executor and not independent biological remeasurement.
