# V77 Pre-Rehearsal Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the exact non-authorizing runtime, provenance, smoke-test and corrected-science state that must be true before any bounded synthetic mutation rehearsal is even considered.

**Architecture:** Keep runtime/provenance and science lanes separate. Add one docs-only freeze record on top of the GREEN provenance branch; reference exact external science/smoke SHAs and CI runs rather than importing their code.

**Tech Stack:** Markdown, GitHub commit/PR metadata, GitHub Actions evidence.

**Spec:** `docs/agent/JEPA_FINAL_V77_S174_NEW_AGENT_TAKEOVER_20261007.md`

## Global Constraints

- No real-data training authority.
- No optimizer/EMA mutation is authorized by this document.
- Do not change runtime, sampler, target, representation, thresholds, EMA half-life, TEST, Morabito, 500K, Stage 4, or the 353 gene mappings.
- Keep S174 corrected-science evidence separate from runtime implementation.
- Record exact SHAs and CI run IDs.

## Review Focus

- A GREEN workflow that did not actually execute a named gate.
- Stale PR descriptions that overstate or understate current implementation.
- Mixing corrected-science conclusions into runtime authority.
- Treating donor-bootstrap envelopes as qualification targets before S159 is resolved.
- Treating the class-separation gap as a reason to rewrite the completed replay rather than a constraint on the next design.

---

### Task 1: Freeze the verified pre-rehearsal state

**Files:**
- Create: `docs/agent/JEPA_V77_PRE_REHEARSAL_FREEZE_20261007.md`

**Interfaces:**
- Consumes: exact GitHub heads/CI for PRs #224, #226, #228, #232, #233 and S174 replay branch.
- Produces: one non-authorizing cross-lane freeze record.

- [ ] **Step 1: Verify exact heads and CI evidence**

Check that the record uses the exact SHAs and successful runs already verified in GitHub.

- [ ] **Step 2: Write the freeze record**

Record what is GREEN, what remains only descriptive, and what is explicitly not authorized.

- [ ] **Step 3: Self-review for authority leakage**

Confirm the document does not authorize mutation, real training, target/representation freeze, or corrected-envelope gating.

- [ ] **Step 4: Commit**

Commit the docs-only record on `handoff/v77-pre-rehearsal-freeze-20261007`.
