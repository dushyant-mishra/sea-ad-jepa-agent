# JEPA Lane Takeover Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the historical architecture/target-discovery audit, gene-identity reclassification, downstream implementation state, external artifact custody, and active authority chain so a future agent can take over without repeating the archaeology or reviving closed experiments.

**Architecture:** Keep scientific authority and custody separate. The audit branch records conclusions and machine-readable ledgers; a successor handoff branch adds a single read-first takeover document, external/local artifact manifest, and historical context snapshots. Frozen TD/synthetic execution branches remain untouched and are referenced by exact PR/commit/hash.

**Tech Stack:** Markdown, JSON, CSV, Python standard library, GitHub branch/PR provenance.

**Spec:** User request in the JEPA project conversation on 2026-10-13: update GitHub handoff/audit branches with historical audits, scripts, data/results custody and current execution state so future agents do not repeat work.

## Global Constraints

- Do not modify frozen TD PR #316, repair PR #320, or synthetic PR #321 code/bytes.
- Do not reinterpret narrow TD failures as absence of biology.
- Do not revive closed historical experiments unless the ledger explicitly marks them unresolved or identity-contaminated and needing replay.
- Distinguish `SOURCE_NATIVE_SAFE`, `FROZEN_4K_IDENTITY_AUDITED`, `REPAIRED_41K_ADDRESS_BOUND`, `SEMANTICS_FREE_MECHANICS`, and `GENE_IDENTITY_PROVENANCE_UNRESOLVED` evidence.
- Do not upload large/private expression/checkpoint binaries to public GitHub; bind them by exact filename, size, SHA-256 and custody status instead.
- Keep all target selection, TD60, Stage4, multimodal training, and JEPA training authority false.
- Current blinded synthetic successor is PR #320 @ `1f474a44a6baabc667dbfda726e0755426c732e7` plus PR #321 @ `15f519c00137d581e25232c16be52c2b9badd83e`; next lawful execution is phase-1 only and must stop before controller adjudication.

## Review Focus

- Historical result accidentally promoted despite later supersession.
- Pre-repair NPH/cross-source semantic result mistakenly treated as valid architecture evidence.
- Mechanics-only EMA/optimizer evidence incorrectly promoted to biological authority.
- Large local binary copied into public GitHub instead of custody-manifested.
- Future agent follows frozen #316 one-process path instead of audited #320/#321 two-phase successor.

---

### Task 1: Historical decision and gene-identity audit

**Files:**
- Create: `docs/agent/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.md`
- Create: `results/target_discovery/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.json`
- Create: `docs/agent/JEPA_GENE_IDENTITY_RECLASSIFICATION_AUDIT_20261013.md`

**Interfaces:**
- Consumes: repository `DECISION_REGISTRY.csv`, Oct-5 terminal target lineage reconstruction, Stage64/69/70/71 results, Stage81A2R identity recovery, V43/V44 research-only teacher-team work.
- Produces: authoritative navigation ledger for Task 2 and the final takeover handoff.

- [ ] Record each relevant historical hypothesis as `question -> experiment -> result -> current status -> identity class -> carry-forward rule`.
- [ ] Explicitly preserve closed/rejected items and identify design-only/provisional items.
- [ ] Reclassify evidence under the later gene-identity repair without blanket invalidation.
- [ ] Record exact source paths/PRs and no-authority boundary.

### Task 2: Downstream implementation-readiness audit

**Files:**
- Create: `docs/agent/JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.md`
- Create: `results/target_discovery/JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.json`

**Interfaces:**
- Consumes: Task 1 ledger plus canonical runtime/EMA/checkpoint history.
- Produces: reduced active teacher/student/EMA implementation space, explicitly excluding historically closed arms.

- [ ] Separate runnable canonical runtime from design-only post-TD tournament layers.
- [ ] List teacher target construction, teacher topology, student topology/semantics and EMA policies with `active`, `control`, `closed`, `provisional`, or `conditional` status.
- [ ] Preserve presentation-normalized EMA half-life as native mechanics while recording that no production half-life is selected.
- [ ] Define the missing target-portfolio adapter/tournament harness without authorizing training.

### Task 3: Machine-readable takeover validation

**Files:**
- Create: `scripts/v5/verify_jepa_lane_takeover_manifest_v1.py`
- Create: `tests/v5/test_verify_jepa_lane_takeover_manifest_v1.py`
- Create: `.github/workflows/jepa-lane-takeover-audit.yml`

**Interfaces:**
- Consumes: machine ledgers from Tasks 1-2.
- Produces: fail-closed schema/status validation for the final handoff state.

- [ ] Validator must reject training/Stage4/TD60/target-selection authority true.
- [ ] Validator must require exact PR #320/#321 SHAs and package/pre-fit/certification identities.
- [ ] Validator must reject any active item with identity class `GENE_IDENTITY_PROVENANCE_UNRESOLVED` unless explicitly marked `REPLAY_REQUIRED`.
- [ ] Tests cover false authority, stale TD SHA, stale synthetic SHA, and unresolved identity promoted to active.

### Task 4: Successor takeover branch

**Files:**
- Create on successor handoff branch: `docs/agent/JEPA_LANE_TAKEOVER_HANDOFF_20261013.md`
- Create: `docs/agent/JEPA_LANE_TAKEOVER_STATE_20261013.json`
- Create: `docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv`
- Create: `docs/agent/JEPA_ACTIVE_BRANCH_PR_MAP_20261013.md`
- Create: `docs/agent/external_context/STATUS_AND_REPAIR_PLAN_20260912.txt`
- Create: `docs/agent/external_context/WSL_EXECUTION_ARCHITECTURE_NOTES_SNAPSHOT.txt`

**Interfaces:**
- Consumes: all prior tasks plus exact local file hashes/sizes.
- Produces: one read-first takeover entrypoint and custody inventory.

- [ ] Point to master repository inventories instead of duplicating every historical result byte.
- [ ] Include exact local/project artifact SHA-256 and sizes; mark large binaries `EXTERNAL_CUSTODY_ONLY__DO_NOT_PUBLIC_UPLOAD`.
- [ ] Record phase-1 Macha execution instruction and STOP-before-controller rule.
- [ ] Record `next action`, `do not repeat`, `open questions`, and exact branch/PR map.

### Task 5: Verify and publish handoff pointers

**Files:**
- Update PR #322 description/comment with audit package contents.
- Create a draft successor handoff PR stacked on the audit branch.

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: discoverable GitHub navigation for future agents.

- [ ] Verify audit-branch files exist and machine validator/tests compile/pass in CI.
- [ ] Verify handoff branch contains all takeover files and no large binary payloads.
- [ ] Post exact branch heads and handoff instructions to PR #322 and successor PR.
- [ ] State explicitly that #316/#320/#321 bytes are untouched and all downstream authority remains false.
