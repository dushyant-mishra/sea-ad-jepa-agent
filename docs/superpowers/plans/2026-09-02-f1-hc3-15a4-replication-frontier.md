# F1 HC3 Command 15A4 Replication Frontier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete and independently validate the outcome-blind 70-row donor-replicated HC3 nuisance frontier without selecting a nuisance design.

**Architecture:** Three new v3 scripts implement production derivation, independent QR reconstruction, and fail-atomic package finalization. Production uses SVD projection leverage; validation independently uses pivoted QR and recomputes all 7,280 donor-deletion ranks. Existing v2 sources and all prior packages remain read-only authorities.

**Tech Stack:** Python 3, NumPy float64, SciPy pivoted QR, CSV/JSON/SHA-256.

**Spec:** `C:/Users/dushy/.codex/attachments/8ac0448e-82b3-4708-8b2e-0d3c5dc39782/pasted-text.txt`

## Global Constraints

- No expression, model/checkpoint, forward, outcome, training, or EMA access.
- Use all 104 frozen donors and unchanged 24/7/11 source operator blocks.
- Preserve prior packages and v2 scripts byte-for-byte.
- SVD leverage is conclusion-bearing; pivoted QR is the independent check.
- Enumerate all 70 rows; nonestimable rows are recorded, never terminal.
- Freeze only the reusable procedure, never a rank triple or design.

---

### Task 1: Behavioral tests

**Files:**
- Create: `tests/v4/test_contextual_target_f1_hc3_replication_frontier_v3.py`

**Interfaces:**
- Consumes: planned `svd_geometry(X)`, `qr_geometry(X)`, `classify_geometry(...)`, and `frontier_identities()`.
- Produces: regression protection for 70-row traversal, leverage equivalence, and reason-code classification.

- [ ] Write literal tests expecting 70 identities, 35 NPH-free identities, SVD/QR leverage agreement on a hand matrix, and continued enumeration after a nonreplicated row.
- [ ] Run the test and verify RED because the v3 module does not exist.

### Task 2: Production derivation

**Files:**
- Create: `scripts/v4/derive_contextual_target_f1_hc3_replication_frontier_v3.py`

**Interfaces:**
- Consumes: frozen nuisance binary/schema and corrected v2 package.
- Produces: authority, full 70-row frontier, source-prefix summary, SVD/QR crosscheck, NPH indispensability, and NPH-free summary.

- [ ] Implement frozen SVD rank and SVD projection leverage.
- [ ] Implement source-prefix reconstruction and all 70 Cartesian identities without break/return on invalid rows.
- [ ] Record full-rank, df, HC3, LOO, classifications, and source summaries.
- [ ] Run unit tests to GREEN, then run the real derivation in staging.

### Task 3: Independent reconstruction

**Files:**
- Create: `scripts/v4/validate_contextual_target_f1_hc3_replication_frontier_v3.py`

**Interfaces:**
- Consumes: authenticated nuisance inputs and production staging artifacts.
- Produces: independent all-row QR/rank/LOO/classification comparison.

- [ ] Implement pivoted-QR rank and leverage without importing production helpers.
- [ ] Reconstruct all 70 designs and all 104 donor deletions per design.
- [ ] Fail closed on identity, boolean, reason-code, critical-donor, or tolerance mismatch.
- [ ] Run validator and require PASS.

### Task 4: Governance and reusable contract

**Files:**
- Create: `F1_HC3_REUSABLE_NUISANCE_ADMISSIBILITY_CONTRACT.md` in staging.
- Create: five-lens review artifact in staging.

**Interfaces:**
- Consumes: completed production and independent evidence.
- Produces: cohort-agnostic algorithm freeze and preserved dissent.

- [ ] Write the procedure contract before any future-cohort use, explicitly forbidding current ranks/donors as constants.
- [ ] Run the requested five independent lenses and synthesis.

### Task 5: Finalization and verification

**Files:**
- Create: `scripts/v4/finalize_contextual_target_f1_hc3_replication_frontier_v3.py`
- Publish: `outputs/contextual_teacher_target_v1_f1_hc3_replication_frontier_complete_20260902/`

**Interfaces:**
- Consumes: passed staging artifacts and review.
- Produces: source snapshots, source manifest, complete package manifest, external handoff, terminal status.

- [ ] Snapshot exactly the three v3 scripts and hash every artifact.
- [ ] Publish atomically only after all required files and hashes verify.
- [ ] Rerun tests, production/independent integrity checks, and manifest verification immediately before reporting.
