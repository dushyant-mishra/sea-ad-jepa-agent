# JEPA Live Branch Inventory — 2026-09-13

This document supplements `JEPA_NEW_CHAT_HANDOFF_20260913_V5_FULL_LINEAGE_CURRENT.md` and records every live branch returned by GitHub during the Sept-13 handoff audit.

Rules:

- The canonical current V5 implementation ledger is `planning/v5-dataset-first-production-closure-20260912`.
- `main` is not the current V5 implementation authority.
- Do not infer scientific authority from a branch name.
- Do not blindly merge/delete divergent branches. Preserve provenance until content/ancestry audit proves unique work is absorbed.
- T0 is a separate methodology/test-rig lane; its numbers/targets are not V5 authority.

## Canonical current V5

- `planning/v5-dataset-first-production-closure-20260912` — canonical integrated V5 successor; continue here after re-fetching live head.

## V5 repair/fix/planning history

- `fix/v5-schedule-metadata-hash-revalidation-20260910` — historical schedule metadata/hash repair.
- `planning/teacher-student-v5-dataset-schedule-20260909` — schedule/EMA exposure-design history; historical constants not current authority.
- `planning/teacher-student-v5-gpu-rng-mechanics-20260908` — historical GPU/RNG mechanics candidate; supporting mechanics only unless requalified.
- `planning/v5-full-population-cheat-proofing-20260909` — full-population anti-cheat lineage.
- `planning/v5-preexecution-hardening-20260909` — preexecution/dependency hardening lineage.
- `planning/v5-pretraining-qualification-20260909` — pretraining/qualification/checkpoint history; not current training authority.
- `repair/v5-authority-evidence-integration-20260912` — Sept-12 reconciliation lane; reviewed protections were folded into successor; preserve for provenance.
- `repair/v5-executable-power-authority-20260911` — executable-power postqualification source lineage.
- `repair/v5-installed-target-root-binding-20260912` — FULL104 metadata/root-binding repair lineage; historically divergent and reconciled by content.
- `repair/v5-qualified-target-guard-20260911` — qualified target/runtime guard source lineage; ancestral to successor work.

## Integrated V5 review history

- `review/integrated-target-v5-repairs-20260911`
- `review/integrated-target-v5-repairs-code-20260911`
- `review/integrated-target-v5-repairs-exec-20260911`
- `review/integrated-target-v5-repairs-finalwork-20260911`
- `review/integrated-target-v5-repairs-work-20260911`

These preserve independent review/reconciliation history and are not the active production ledger.

## T0 primary branches

- `t0/v20-pathology-blind-materialization-20260908` — V20/pathology-blind T0 methodology lineage.
- `t0/v21-closeout-candidate-20260911` — current T0 closeout candidate; last independently checked at `c22031f92b65c5aa284d40e23f9405f5f235dae0` during handoff preparation.
- `t0/v21-prospective-design-20260910` — prospective V21 design lineage.

## T0 repair/history branches

- `repair/t0-v21-authority-hardening-20260911`
- `repair/t0-v21-authority-restoration-20260911`
- `repair/t0-v21-integrated-authority-regression-20260911`

## T0 independent review branches

- `review/t0-r4-dataset-bound-hardening-20260909`
- `review/t0-r4-dataset-bound-inputs-20260908`
- `review/t0-r4-independent-reds-20260909`
- `review/t0-r4-independent-review-20260909`
- `review/t0-r5-dataset-chain-hardening-20260909`
- `review/t0-r5-dataset-first-framework-20260909`
- `review/t0-r5-external-hardening-20260909`
- `review/t0-v2-api-surface-portability-20260911`
- `review/t0-v20-replay-equivalence-20260910`
- `review/t0-v21-integrated-candidate-20260911`
- `review/t0-v21-integrated-restored-20260911`
- `review/t0-v21-integrated-restored-v2-20260911`
- `review/t0-v21-successor-20260911`

## T0 docs/handoff branches

- `docs/t0-closeout-handoff-20260911`
- `handoff/jepa-t0-v2-claude-ready-20260911`

## F1 historical branch

- `fix/f1-review-closeout-20260911` — historical F1 review/closeout. Preserve as provenance for the QID/matched-null estimand gap; do not import its semantics automatically into V5.

## Governance branches

- `governance/integrated-target-discovery-v5-handoff-20260911` — joins target discovery/qualification with V5 as one production-review chain.
- `governance/project-lineage-reconstruction-20260911` — repository/project lineage reconstruction and governance history.

## General handoff branches

- `handoff/jepa-new-chat-20260910-t0-v21-v5`
- `handoff/jepa-new-chat-20260911-asap-repair-status`
- `handoff/jepa-new-chat-20260911-post-v21-repair-current`
- `handoff/jepa-new-chat-r2-20260908`
- `handoff/jepa-new-chat-20260913-full-lineage-current` — Sept-13 provenance branch created during final handoff preparation; not a replacement for the canonical V5 branch.

## Main

- `main` — live head independently checked during handoff at `ba3f2a1200d0bbaf4b9ee0d7d16ddc17341d779f`. It is behind the active V5 successor and must not be used as the current V5 implementation ledger.

## Branch-use guidance

For new work:

1. re-fetch `planning/v5-dataset-first-production-closure-20260912`;
2. read the latest Sept-13 handoff/pointer;
3. use historical branches only to recover specific evidence/mechanics or audit ancestry;
4. never merge an old branch merely because it sounds newer or more authoritative;
5. if cleanup is desired later, first build a branch->unique-commit/content matrix and prove all scientifically/materially unique work is retained.
