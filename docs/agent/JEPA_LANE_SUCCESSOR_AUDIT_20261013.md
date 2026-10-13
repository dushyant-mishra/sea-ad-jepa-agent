# JEPA lane successor audit — 2026-10-13

Status: `AUDIT_SUCCESSOR_FROZEN__PHASE1_RECEIPT_STRUCTURALLY_AUDITED__CONTROLLER_CLOSED__POST_TD_HARNESS_GREEN__NO_TRAINING_AUTHORITY`

## Purpose

This document is the append-only successor to draft PR #322 and the read-first handoff in draft PR #323. It exists so future agents do **not** repeat the historical archaeology, silently revive rejected experiments, or confuse implementation readiness with biological authority.

The historical audit/handoff snapshots remain authoritative for what they recorded at their exact heads:

- PR #322 audit snapshot: `6d6ec998e38b5da5a5281ebba89c471de16f243f`
- PR #323 handoff + independent phase-1 receipt-audit snapshot: `87cd356dd739d12662da14ecc3625ff8d80c21ec`

This successor adds only work completed after those snapshots plus exact custody/indexing needed for takeover.

## Current authority

Hard project authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No document in this branch selects a target, selects a representation, authorizes TD60, opens Stage4, authorizes multimodal training, or authorizes real JEPA training.

## TD synthetic test-of-test state

Frozen upstream identities:

- TD repaired custody/runtime: PR #320 @ `1f474a44a6baabc667dbfda726e0755426c732e7`
- synthetic V2.1: PR #321 @ `15f519c00137d581e25232c16be52c2b9badd83e`
- authenticated package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- controller archive SHA-256: `f554e2a95315bb39cc8f7e366620bca5cb2126a4896b3790ed2c632e5cc6a328` (sealed; not phase-1 input)
- final cross-cert receipt SHA-256: `fbcf2d589ec05ff67914a890f465d39cdc8f9f53363129d98b4b7f0a00213ee9`

Macha executed phase 1 exactly once on evidence branch `evidence/td-synthetic-phase1-blinded-fit-1f474a44-20261013` at evidence commit `a1aed169be5f4552208128f9d71b2d601a657393`.

Frozen phase-1 blinded receipt SHA-256:

`e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`

Independent receipt audit is preserved in `docs/agent/TD_PHASE1_INDEPENDENT_RECEIPT_AUDIT_20261013.md` and concluded:

`PASS_PHASE1_RECEIPT_STRUCTURE_AND_CUSTODY__SAFE_TO_CONSIDER_SEPARATE_PHASE2_AUTHORIZATION`

Important: this is **not phase-2 authority**. Controller truth remains unopened. No opaque output has been semantically mapped in this lane.

Environment disclosure stays attached: phase 1 used Python 3.11.15 and NumPy 2.4.6 in `sea-ad-jepa-v3`; the original certification did not lock NumPy. The first Windows extraction failed only on timestamp restoration, was discarded/re-extracted, and bytes were hash-verified. Concurrent V79 execution was disclosed.

## Historical architecture decisions — do not repeat

The historical decision ledger and gene-identity reclassification in PR #322 remain the controlling history. Future agents must begin there rather than reconstructing these experiments from chat.

Closed / negative-prior lineages include, at minimum:

- hidden-gene/CELL anchor as encoder objective — rejected;
- ANCHOR_ONLY — strongly rejected in Stage81B mechanism attribution;
- core-only evidence and evidence-starvation/tier-hiding as production cascade — rejected/insufficient;
- T0/T1/TCTX historical target family — no production target qualified;
- V6R5B residual target — `RESIDUAL_TARGET_DOES_NOT_RESCUE`;
- historical PROD41K/T1 trajectory — defective training evidence because attention tensors had zero Adam moments under fp16-backward pathology; forensic only, never resume;
- rare auxiliary lineage — interesting internal signal but failed benchmark-lock qualification;
- graph auxiliary — failed graph-specific value because randomized graph control did better;
- arithmetic block means — negative prior for destroying rare/local information;
- Signed-V2 — biologically richer but conditionally unpredictable/causally harmful; rejected as production target;
- historical `.996` EMA or any old fixed beta — mechanics history only, not production authority.

Surviving principles include donor-primary evaluation, source separation, stable subspaces over named axes, observation-operator separation, biological-evidence versus depth-response curves, explicit rare/common preservation, non-compensation across target blocks, recoverability typing, and teacher-private information not being forced into impossible point targets.

## Gene-identity reclassification

Do not treat all historical real-data evidence equally.

Allowed evidence classes:

1. `SOURCE_NATIVE_SAFE` — source-native experiments whose molecular identities were not implicated in the NPH symbol-derived recovery problem.
2. `FROZEN_4K_IDENTITY_AUDITED` — experiments on the frozen 4,096 canonical Ensembl vocabulary after the later identity audit.
3. `REPAIRED_41K_ADDRESS_BOUND` — experiments whose columns are explicitly bound to the repaired 41,238 `molecular_address_index`.
4. `SEMANTICS_FREE_MECHANICS` — optimizer/EMA/checkpoint/collapse mechanics that do not depend on gene labels.

Pre-repair NPH/cross-source gene-semantic evidence without one of those bindings is:

`GENE_IDENTITY_PROVENANCE_UNRESOLVED__NOT_ARCHITECTURE_AUTHORITY`

This does not resurrect experiments rejected for independent reasons.

## Post-TD downstream implementation now preserved

The exact green implementation source was branch `implementation/jepa-post-td-harness-prefreeze-20261013` @ `97dd73f49e1554053bbfab6c5369377a23a72ceb`.

Its green workflow was `JEPA post-TD harness prefreeze`, run `38448458550`, conclusion `success`, on that exact SHA.

This successor squashes the implementation tree cleanly onto the audited handoff base. The runnable files are:

- `scripts/v5/jepa_post_td_harness_contract_v1.py`
- `scripts/v5/jepa_post_td_rehearsal_preflight_v1.py`
- `scripts/v5/jepa_post_td_tournament_controller_v1.py`
- `scripts/v5/jepa_post_td_presentation_ema_v1.py`
- `tests/v5/test_jepa_post_td_harness_contract_v1.py`
- `tests/v5/test_jepa_post_td_rehearsal_preflight_v1.py`
- `tests/v5/test_jepa_post_td_tournament_controller_v1.py`
- `tests/v5/test_jepa_post_td_presentation_ema_v1.py`
- `.github/workflows/jepa-post-td-harness-prefreeze.yml`

The harness is non-authorizing and implements the control-plane pieces that can be finished before target selection:

- target-portfolio schema/dependency expansion;
- teacher target-policy and evidence-mask contracts;
- teacher/student topology activation rules that preserve historical eliminations;
- recoverability classes: `POINT_IDENTIFIABLE`, `STOCHASTIC_IDENTIFIABLE`, `TEACHER_PRIVATE`, `NOT_ESTIMABLE`;
- lawful student output semantics for each recoverability class;
- `NOT_ESTIMABLE`/missing-evidence handling without fake zero targets;
- zero-update teacher-target screening manifests;
- matched-compute architecture tournament manifests;
- per-block non-compensation and evidence reduction;
- optional factorization only inside already-qualified biological blocks;
- write-once synthetic rehearsal preflight;
- presentation-normalized EMA screen with exactly short/intermediate/long half-life arms and no inherited beta winner;
- restart-safe presentation-normalized EMA state and checkpoint overlay;
- authority flags kept false by construction.

A probabilistic likelihood/loss for stochastic-identifiable targets was **not** historically frozen, so this harness deliberately does not invent one.

## Active architecture prior after historical filtering

Do not reopen a giant Cartesian architecture tournament.

Primary teacher topology candidates after historical filtering:

1. single rich EMA teacher;
2. shared EMA backbone + biologically typed heads.

Independent complementary teachers are conditional challengers only after a new interference test earns them.

Primary student topology:

`full-capacity shared student backbone + typed prediction heads`

Specialist/independent student branches require new demonstrated negative transfer; Stage69–71 do not grant them production status.

Teacher target construction remains separable from topology. Value-blind rich complementary construction deserves serious screening where query-conditioned targets qualify; value-visible construction remains a reference arm; block-level construction is relevant only when the qualified biological object is block/program based.

Privileged modalities should default to auxiliary critics/corroboration when the corresponding state is teacher-private rather than be forced into RNA-student point targets.

OPF/JEPA-Anything remains an optional numerical capacity-allocation mechanism inside qualified blocks, never a substitute for biological target qualification.

## What remains genuinely open

1. Separate phase-2 authorization for the frozen synthetic TD blinded receipt. No controller opening before that authority exists.
2. Phase-2 adjudication itself, once authorized, using exact receipt/package/controller/runtime identities.
3. TD interpretation strictly at the scope earned by the synthetic test-of-test; qualification does not auto-select a biological target.
4. Real target-portfolio qualification/selection in its own authorized lane.
5. Once a portfolio is frozen: zero-update teacher construction screen, recoverability assignment, topology tournament, then EMA half-life screen.
6. Specific probabilistic objective only if `STOCHASTIC_IDENTIFIABLE` is actually needed and after a separately frozen mechanics decision.
7. Real JEPA training remains off until explicit downstream authority.

## No-repeat rule

A future agent must not redo historical archaeology merely because a result is old. Reopen an item only if one of these is true:

- the original result depended on pre-repair gene semantics and has not been replayed on a repaired identity surface;
- a frozen audit explicitly labels it `REPLAY_REQUIRED`;
- the scientific target/estimand has materially changed and a new prospective contract is written before looking at results;
- an implementation defect is demonstrated that invalidates the original result.

Otherwise preserve the original PASS/FAIL/negative-prior status.
