# JEPA lane audit + custody snapshot — 2026-10-17

Status: `DURABLE_AUDIT_CUSTODY__NON_AUTHORIZING__NO_REPEAT`

This file is the dated custody snapshot for the JEPA Target Discovery -> unified qualification -> downstream lane. It does not replace historical audits; it binds the current state to them so a successor does not repeat settled archaeology, lose rejected evidence, or mistake mechanics for biological authority.

## Read-first order

1. This file.
2. `docs/agent/JEPA_LANE_CURRENT_CUSTODY_NO_REPEAT_20261016.md` for the deep no-repeat index.
3. `docs/agent/JEPA_HISTORICAL_NO_REPEAT_INDEX_20261015.md` for earlier Target Discovery / ETL / downstream history.
4. `results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V3_20261017.json` for the machine-readable state.
5. `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_V3_20261017.json` before using any local/private data artifact.
6. PR #404 `docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md` and `results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json` before changing Task 4.

## Frozen accepted authority

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 3: `117dd51dea827e734b299982da93991b934bdc8f`
- Task 3 freeze branch: `freeze/unified-task3-accepted-117dd51d-20261016`
- Task 3 acceptance PR: #401
- Macha acceptance review head: `c33f2bd2`
- verdict: `ACCEPT_UNIFIED_TASK3`

Global authority remains exactly:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Task 4 may exist prospectively as custody/mechanics, but neither Task 4 code nor a green CI run grants target, representation, Stage 4, protected-value or training authority.

## Task 3 rejection lineage that must not be re-audited from scratch

Preserve each rejected candidate because each discovered distinct authority defects:

- `851544e8dc2a3881193a4d5bbcf07933e1d61149`: original B1-B6 rejection.
- `68df31584d17f91da2635cdf8e03bbe93695f9d1`: rejected after critical Task 2 binding bypass N1, declared-KTQ route N2, and partial B3/B5 repairs.
- `d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`: rejected with N2, nested validator-independence B3-V and B5-F revocation-route family still open.
- `117dd51dea827e734b299982da93991b934bdc8f`: accepted exact Task 3 code.

Carry-forward into Task 4 is binding: C1-C9, R4 cross-process persistence, R7 credential/authenticated actor identity, and R5 pooled donor-level claim scope. The accepted review lesson is also binding: after fixing one gate, attack all sibling routes to the same authority state.

## Task 4 design / RED / implementation state

### Approved design and plan

PR #402, branch `design/unified-task4-c1-c9-amendment-20261016`, head `979833a51391248f568426f508cce1d01e3e32a5`.

- binding amendment: `docs/superpowers/specs/2026-10-16-unified-task4-c1-c9-binding-amendment.md`
- implementation plan: `docs/superpowers/plans/2026-10-16-unified-task4-sealed-custody-c1-c9-implementation.md`

### Preserved initial RED

PR #403, branch `work/unified-task4-red-20261016`, head `c5e40b04c6dcbb07d3a92edc9f9677ceb7f584ff`.

Valid initial RED: run `38938697657`, job `117100597615`, read-only token, 14 intentional failures at not-yet-existing Task 4 interfaces. Do not replace this with a clean narrative.

### Implementation candidate

PR #404, branch `work/unified-task4-impl-20261016`.

- live observed head on this snapshot: `b31371d62f3270c965d321e61c35898ca6be3721`
- last fully verified code/test head: `cfa3b7c4f92a1569639b6733a6956c516d7f4cf4`
- compare `cfa3b7c4... -> b31371d...`: four commits, documentation/result metadata only; no script, test, schema, workflow or frozen Task 0-3 production bytes changed.
- files in that docs/result-only delta: `docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md`, `docs/agent/UNIFIED_TASK4_EXECUTION_LEDGER_20261016.md`, `results/target_discovery/unified_qualification_v1/TASK4_ATTACK_MATRIX_V1.json`, `results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json`.

Last fully verified exact code/test head `cfa3b7c4...`:

- Task 4 run `38946411134`, job `117126540739`: focused Task 4 PASS, projected 100k replay PASS, full unified regression PASS.
- Task 1 regression `38946411299`: PASS.
- Task 2 regression `38946411331`: PASS.
- Task 3 registry regression `38946411463`: PASS.
- unified synthetic integration `38946411400`: PASS.

Candidate classification remains:

`CANDIDATE_ONLY__INDEPENDENT_EXACT_HEAD_REVIEW_REQUIRED`

Genuine external C5-C9 authority context remains fail-closed.

## Task 4 REDs already found and repaired

These failures are scientific/engineering evidence and must be retained:

- initial missing Task 4 interfaces: `38938697657` / `117100597615`.
- terminal-accounting gap: `38943608912` / `117117078319`.
- campaign schema drift: `38944319232` / `117119472176`.
- incomplete/aliasable C1-C9 vocabulary: `38944836349` / `117121219990`.
- signer object accepted without actor-action attestation: `38945592644` / `117123776998`.
- caller self-asserted actor/process authority context: `38946266116` / `117126036930`.

Do not recreate these attacks from scratch; retain them in the hostile matrix and only extend with genuinely new sibling routes.

## Task 4 staged implementation inventory

Prospective scripts on PR #404:

- `scripts/v5/td_unified/challenge_custody_v1.py`
- `scripts/v5/td_unified/task4_actor_attestation_v1.py`
- `scripts/v5/td_unified/task4_authority_barrier_v1.py`
- `scripts/v5/td_unified/task4_custody_store_v1.py`
- `scripts/v5/td_unified/task4_publication_guard_v1.py`
- `scripts/v5/td_unified/task4_registry_adapter_v1.py`
- `scripts/v5/td_unified/task4_requirement_policy_v1.py`

Prospective schemas include campaign/evidence/sealed challenge/custody/reveal/realization/exposure/output-freeze/actor-action-attestation/persistent-custody-head contracts under `schemas/target_discovery/unified_v1/`.

Tests cover focused custody, hostile challenge custody, actor attestation, attack matrix, authority barrier, persistent custody, replay/performance, publication guard, C1-C9, registry adapter, replay mutations, requirement policy, schema contracts, terminal accounting and workflow policy.

Do not reimplement these modules from the specification. Review and repair exact current bytes.

## Historical Target Discovery / ETL / science already custodied

The deep 2026-10-15 no-repeat index remains the detailed source. Key settled custody includes:

- population/support authority PR #349 / `1ab453e5cb60efb209a8eee2aecb61c5ea0fbfc7`, authenticated population registry SHA-256 `50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`, with 6,351,753 rows / 149 donors / 42 observation operators / 3 sources / 2,028 donor×operator strata / 104 reader-fit / 22 reader-validation / 23 reader-oracle donors.
- repaired TD units and lineages: G8 #364; G6 #365; geometry G9/S1/S2 #366; R1 #367; G2 #368; G7 #362; R4/C6/C4 #358; C4->C6 firewall #351; G12 #360; system battery #369. PRs #375-#378 are superseded duplicates.
- historical teacher/student mechanics: optimizer/gradient flow, teacher no-grad, optimizer-before-EMA, invalid-update EMA blocking, Adam moments, restart/checkpoint behavior, identity RNG, packing/scientific weights, FULL104 support/normalization, donor-primary target, p/q separation, visibility/context, masking and anti-carryover.
- unresolved scientific control retained: target/query identity shortcut risk requires identity-only/shared/fixed/stop-grad/shuffle comparators before biological authority.
- technology/assay should be treated as an observation operator; donor/technology/dataset transfer, subspace/axis stability and evidence-vs-depth uncertainty are separate scientific questions.
- chromVAR/limma motif-program accessibility is a distinct non-authorizing evidence layer; ATAC DA/chromVAR/footprinting/SCENIC+ that reuse the same ATAC source are not four independent datasets.
- measurement evidence, mechanics evidence and biological authority must remain separate.

## Historical files imported from chat

Already in Git; do not reconstruct manually:

- `docs/agent/historical_imports/WSL_EXECUTION_ISSUE_AND_FOUNDATION_DESIGN_NOTES_20260824.txt`
- `docs/agent/historical_imports/STATUS_AND_REPAIR_PLAN_20260912.txt`
- `docs/agent/TD_MOTIF_PROGRAM_EVIDENCE_LAYER_CHROMVAR_LIMMA_V1_20261015.md`

## Local/private artifact custody

Large binary artifacts are intentionally not duplicated into Git. The V3 manifest binds exact names, sizes and SHA-256 values. Verify hashes before use. Byte presence never confers authority.

Current local set includes the split foundation discovery expression archive, its supplied SHA manifest, calibration bundle, expression archive, checkpoint bundles, NPZ artifact, focused Task 3 pytest artifact, and the two imported historical text notes.

## Known inherited CI/environment defects

Three frozen/inherited workflows can fail before intended assertions because NumPy is absent when `canonical_v1.py` imports:

- Task 0 migration audit `38946411227`.
- Task 0 B1-B5 verification `38946411361`.
- Task 3 B6 workflow policy `38946411617`.

Classify these as inherited workflow-environment defects. Do not mutate frozen authority code or misclassify them as Task 4 scientific failures.

## Permanent no-repeat protocol

For any proposed work, classify it first as one of:

`ALREADY_AUDITED` / `SUPERSEDED` / `OPEN` / `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

Only `OPEN` or `CHANGED_INPUT_REQUIRES_REQUALIFICATION` should trigger new implementation/audit. Preserve all RED and rejected evidence. For new authority boundaries use: assimilate history -> self-audit -> RED -> minimal repair -> focused regression -> inherited regression -> hostile sibling-route audit -> exact-head independent review.
