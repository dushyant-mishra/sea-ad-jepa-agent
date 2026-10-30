# JEPA lane successor audit — 2026-10-13

Status: `AUDIT_CONSOLIDATED__PHASE1_RECEIPT_FROZEN__POST_TD_CONTROL_PLANE_GREEN__NO_TARGET_OR_TRAINING_AUTHORITY`

This document is the append-only successor to the frozen PR #322 checkpoint `6d6ec998e38b5da5a5281ebba89c471de16f243f`. Do not redo the historical archaeology summarized below unless a concrete contradiction is found. The old SHA remains a provenance checkpoint; this newer PR #322 head adds post-freeze evidence and runnable control-plane artifacts.

## Read-first order

1. `docs/agent/JEPA_LANE_AUDIT_SUCCESSOR_20261013.md` — this file.
2. `docs/agent/JEPA_HISTORICAL_ARCHITECTURE_DECISION_LEDGER_20261013.md` and JSON mirror.
3. `docs/agent/JEPA_GENE_IDENTITY_RECLASSIFICATION_AUDIT_20261013.md`.
4. `docs/agent/JEPA_DOWNSTREAM_IMPLEMENTATION_READINESS_AUDIT_20261013.md` and JSON mirror.
5. `docs/agent/JEPA_ROBUST_PIPELINE_POST_JEPA_ANYTHING_AUDIT_20261013.md` and `results/target_discovery/JEPA_ROBUST_PIPELINE_SMOKE_AUDIT_V1.json`.
6. `docs/agent/TD_PHASE1_INDEPENDENT_RECEIPT_AUDIT_20261013.md`.
7. `docs/agent/TD_SYNTHETIC_PHASE1_BLINDED_FIT_1f474a44_20261013/` — exact Macha phase-1 evidence copied by Git object identity from evidence commit `a1aed169be5f4552208128f9d71b2d601a657393`.
8. `scripts/v5/jepa_post_td_*_v1.py` plus `tests/v5/test_jepa_post_td_*_v1.py` — post-TD non-authorizing orchestration/control plane.
9. `docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_V2_20261013.csv` — external/local data and binary custody.
10. PR #323 handoff successor for the operational takeover checklist.

## Current hard authority

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No document or script on this branch changes that state. In particular:

- no target is selected;
- no representation is selected;
- TD60 is not authorized;
- Stage4 is not authorized;
- multimodal training is not authorized;
- JEPA training on real biology is not authorized;
- controller adjudication is not authorized by this audit document.

## TD synthetic test-of-test state

The repaired two-phase chain remains:

- TD repair PR #320: `1f474a44a6baabc667dbfda726e0755426c732e7`;
- synthetic V2.1 PR #321: `15f519c00137d581e25232c16be52c2b9badd83e`;
- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`;
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`;
- controller archive SHA-256: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328`;
- certification receipt SHA-256: `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`.

Macha executed phase 1 exactly once on a fresh checkout of `1f474a44...`. Evidence commit:

`a1aed169be5f4552208128f9d71b2d601a657393`

Frozen blinded V4 receipt SHA-256:

`e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`

The independent audit decision is:

`PASS_PHASE1_RECEIPT_STRUCTURE_AND_CUSTODY__SAFE_TO_CONSIDER_SEPARATE_PHASE2_AUTHORIZATION`

This means only that the frozen receipt/custody are mechanically acceptable for a separately authorized phase 2. It does not itself authorize `adjudicate`. Controller truth remains unopened in this lane.

The execution environment disclosure is retained: Python 3.11.15, NumPy 2.4.6, non-locked local environment; CI had Python 3.11 with NumPy unpinned. The Windows mtime extraction warning was followed by clean re-extraction and byte verification. Concurrent V79 execution was disclosed. Do not silently erase these caveats and do not rerun phase 1 merely to normalize them.

## Gene-identity reclassification — binding rule

Historical biological architecture evidence must be tagged as one of:

- `SOURCE_NATIVE_SAFE`;
- `FROZEN_4K_IDENTITY_AUDITED`;
- `REPAIRED_41K_ADDRESS_BOUND`;
- `GENE_IDENTITY_PROVENANCE_UNRESOLVED__NOT_ARCHITECTURE_AUTHORITY`.

The later recovery showed the highest unresolved identifier burden was concentrated in NPH52. Therefore pre-repair NPH/cross-source gene-semantic conclusions cannot silently become current authority. This is not a blanket invalidation of semantics-free mechanics, SEA-AD source-native experiments, HVS source-native experiments, or repaired 41K-address-bound results.

## Historical architecture decisions — do not reopen by default

The decision ledger remains the authority for exact status. Key closed/negative-prior lineages include:

- hidden-gene/CELL anchor as an encoder objective — rejected;
- ANCHOR_ONLY — strongly negative mechanistic result;
- core-only evidence and evidence-starvation cascades — insufficient/rejected;
- T0/T1/TCTX — no production target qualified; identity-dominance/self-information findings retained;
- V6R5B residual target — `RESIDUAL_TARGET_DOES_NOT_RESCUE`;
- historical PROD41K T1 — defective training evidence; forensic only, never resume;
- rare auxiliary head — interesting internal signal but failed benchmark-lock qualification;
- graph auxiliary — real graph did not beat randomized graph; no graph-specific lock;
- arithmetic block-mean targets — negative prior for rare/local preservation;
- Signed-V2 — richer signal but conditionally unpredictable/causally harmful in its tested formulation;
- historical fixed EMA beta values — mechanics evidence only, no production beta authority.

Do not put any of those back into a full tournament without a new, explicit scientific reason that addresses the historical failure mode.

## Surviving downstream architecture hypotheses

The active implementation prior is deliberately small:

- primary teacher topology: `SINGLE_RICH` or `SHARED_TYPED_HEADS`;
- independent complementary teachers require prospectively established interference;
- privileged critics require separate multimodal authority;
- primary student topology: one full-capacity shared backbone with typed heads;
- specialist students require prospectively established negative transfer;
- point/conditional-mean targets are allowed only when point-identifiable;
- stochastic-identifiable targets require uncertainty/distributional semantics;
- teacher-private state is critic-only;
- `NOT_ESTIMABLE` means abstain, never encode a fake zero target;
- global OPF across biological blocks is forbidden by the control-plane contract; optional factorization is block-internal and non-authorizing;
- aggregate score cannot rescue a failed biological block gate.

## Post-TD harness implementation state

Canonical implementation source branch:

`implementation/jepa-post-td-harness-prefreeze-20261013`

Exact green head:

`97dd73f49e1554053bbfab6c5369377a23a72ceb`

GitHub Actions run `38448458550` completed successfully on that exact head.

The audit branch carries byte-identical Git blobs for:

- `scripts/v5/jepa_post_td_harness_contract_v1.py`;
- `scripts/v5/jepa_post_td_rehearsal_preflight_v1.py`;
- `scripts/v5/jepa_post_td_tournament_controller_v1.py`;
- `scripts/v5/jepa_post_td_presentation_ema_v1.py`;
- four corresponding test modules;
- `.github/workflows/jepa-post-td-harness-prefreeze.yml`.

The harness is a control plane, not a neural winner. It implements target-portfolio dependency checks, lawful teacher evidence masks, teacher/student topology guards, recoverability semantics, matched-compute contracts, evaluator/non-compensation gates, zero-update teacher-screen manifests, write-once rehearsal preflight, three-arm presentation-half-life EMA screens, and restart-safe presentation-normalized EMA state/checkpoint overlays. All authority flags remain false.

A specific probabilistic likelihood/loss for stochastic-identifiable state was not historically frozen. Do not invent one as if it were decided; choose and qualify it only if the frozen target portfolio actually requires that recoverability class.

## Data/result custody

Large expression/calibration/checkpoint binaries stay out of the public Git repository. Their exact filenames, sizes, hashes, evidence class and permitted use are in `JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_V2_20261013.csv`.

Important examples:

- repaired 50k x 41,238 discovery expression archive and split parts — smoke/historical proxy only;
- Aug-24 calibration bundle and 41,238-address namespace — identity/provenance support, not production-training authority;
- repaired-address program-weight NPZ — smoke input;
- historical T1 checkpoints — forensic only, never resume;
- Macha phase-1 receipt — committed exact evidence, still semantically blinded;
- controller archive — phase-2-only custody; do not introduce without explicit phase-2 authority.

## Related PRs / lane boundaries

- PR #313: real target tournament engineering; separate lane, do not silently mutate from here.
- PR #314: corrected replay; one-shot spent and immutable.
- PR #316: historical/frozen relational successor design; old one-process external executor superseded by #320/#321.
- PR #320/#321: current TD two-phase custody/runtime and sealed synthetic package.
- PR #322: this robust-pipeline/historical audit lane.
- PR #323: operational handoff/custody lane stacked on #322.
- PR #324/#325: separate TD+synthetic cross-cert takeover/audit custody work. Treat as complementary historical/custody evidence, not as authority to merge ownership boundaries.
- V79 synthetic campaign is a separate lane and not controlled by this handoff.

## Next legitimate actions

1. Do not rerun phase 1.
2. If phase 2 is desired, create a separate explicit authorization binding the exact blinded receipt SHA, TD commit and controller identities; only then may controller bytes enter the adjudication workspace.
3. Keep target/representation/training authority off until the test-of-test is adjudicated and the relevant TD claims are qualified.
4. Continue post-TD harness engineering only in non-authorizing mode until a target portfolio is frozen.
5. When the target portfolio is frozen, use the existing zero-update teacher-target screen first; do not jump directly to a neural training tournament.
6. Only after target semantics/recoverability are frozen should the matched teacher/student/EMA architecture tournament run.

## Anti-duplication rule

A future agent should start from this document and the ledgers above. Historical experiments are not "unresolved" merely because their raw chat is not in context. Before proposing a rerun, find the ledger status, inspect the cited artifact/commit, apply the gene-identity evidence class, and state what new uncertainty the rerun would resolve.
