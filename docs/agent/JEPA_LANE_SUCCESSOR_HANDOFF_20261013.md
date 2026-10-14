# JEPA lane successor handoff — 2026-10-13

**Read this first.** This is the current operational handoff for the target-discovery → teacher/student/EMA lane. It supersedes stale *next-action* language in older handoff documents while preserving those documents as historical evidence.

Current terminal:

`HISTORICAL_AUDITS_CUSTODIED__TD_PHASE1_BLINDED_RECEIPT_AUDITED__CONTROLLER_CLOSED__POST_TD_HARNESS_GREEN_SOURCE_CUSTODIED__TARGET_NONE__REPRESENTATION_NONE__TRAINING_OFF`

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Nothing in this handoff authorizes controller adjudication, real TD execution, target selection, TD60, Stage4, production EMA selection, multimodal training, or JEPA training.

## 1. Canonical surfaces

Use these surfaces; do not pick branches by recency or title alone.

- **PR #322 — historical/audit custody:** `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013`. Original audited freeze was `6d6ec998e38b5da5a5281ebba89c471de16f243f`; the successor audit adds only explicit custody/provenance layers and exact downstream harness blobs.
- **PR #323 — this takeover/handoff:** `handoff/jepa-lane-takeover-20261013`, stacked on PR #322.
- **PR #316 — TD V2 frozen compatibility target:** `2397ab83d8ae9d0c762a8fd5f3919edc350d137f`, formal freeze/checkpoint comment `6149576461`.
- **PR #320 — repaired TD execution/runtime:** `1f474a44a6baabc667dbfda726e0755426c732e7`.
- **PR #321 — sealed synthetic V2.1 provider:** `15f519c00137d581e25232c16be52c2b9badd83e`.
- **Post-TD harness source:** `implementation/jepa-post-td-harness-prefreeze-20261013` at `97dd73f49e1554053bbfab6c5369377a23a72ceb`.

PR #313 remains a separate real target-tournament executor lane. PR #314 is immutable/spent. Synthetic generator/world ownership remains outside this lane.

## 2. What historical work is already settled

The historical audit layer classifies old experiments rather than leaving them available for accidental reuse. Closed experiments stay closed; negative priors stay negative priors; mechanics evidence is not biological evidence; pre-repair NPH/cross-source gene-semantic results cannot become active authority; defective T1 checkpoints are forensic-only.

The corrected PR #314 replay ran once. The preserved result is: TD56 PASS; TD57B PASS; TD57C P0 HVS failed 3 of 4 cases with minimum margin -0.0071; TD59 PASS. Because sequential stopping occurred at TD57C P0 HVS, other TD57C source/panel combinations were unobserved. The only justified failure statement is that **universal nearest-third fine-local recurrence was not established**. It is not legitimate to infer that rare/local biology is absent, C2 is invalid, cross-source recurrence failed everywhere, or the dataset should be discarded. Overall historical status remains `BROAD_MESO_RELATIONAL_VIABLE__NOT_TARGET_WINNER`.

PR #318/V1 synthetic infrastructure is authentic historical evidence but its interface is superseded. The current V2/V2.1 design repaired semantic blindness, control-structure leakage, durable-fit freezing, opaque challenge/control IDs, path-collision handling, and the triplet population ordering bug by requiring Z eligibility and X measurability/non-tie before the deterministic cap. Those were mechanics/provenance repairs, not retroactive biological findings.

## 3. Phase-1 synthetic TD test-of-test: current state

Phase 1 has now executed once under blind custody and its receipt has been independently structurally audited. Do **not** repeat phase 1 merely to obtain a cleaner-looking environment.

Exact frozen identities:

- evidence commit: `a1aed169be5f4552208128f9d71b2d601a657393`
- TD execution commit: `1f474a44a6baabc667dbfda726e0755426c732e7`
- package SHA-256: `0977c30f6551df72e244423e1b37733cafa9178099bd0b9ab796beb8a52d2115`
- pre-fit archive SHA-256: `ba0fa56a49ffa009a0225606fb48d8fb30c3bd410a6a264ef905db5d4bb18803`
- binding SHA-256: `ab29bacd07fc6697eff8dfe48461ec5f1cc1ec7d378724b10def93910f98ac44`
- blinded receipt SHA-256: `e67aace8dfa8b9823cf8635155a48f5a78faed0a45bf9edb6f7adcba07737684`
- receipt-audit decision: `PASS_PHASE1_RECEIPT_STRUCTURE_AND_CUSTODY__SAFE_TO_CONSIDER_SEPARATE_PHASE2_AUTHORIZATION`

The controller remained unopened. The exact environment caveat is retained in `docs/agent/TD_PHASE1_INDEPENDENT_RECEIPT_AUDIT_20261013.md`: Python 3.11.15 / NumPy 2.4.6 rather than a newly locked phase-1 environment. This was not a contract violation because the phase-1 authority did not lock NumPy, but it remains part of reproducibility provenance. The first Windows extraction attempt failed only on mtime restoration, was discarded, then bytes were re-extracted and hash-verified. Concurrent V79 work is disclosed but did not share phase-1 files or controller material.

**Next legal synthetic action:** only after an explicit separate phase-2 authorization may controller transport enter custody. That authority must bind the exact blinded receipt, exact TD execution commit and exact controller identities. If phase 2 is run, freeze its result and perform an independent audit before any real-data TD or target-selection action.

## 4. Post-TD teacher/student/EMA implementation custody

The target-agnostic downstream harness is now copied byte-for-byte into the audit/handoff custody surfaces from the green source head `97dd73f49e1554053bbfab6c5369377a23a72ceb`. Source GitHub Actions run `38448458550`, job `115472916925`, concluded `success`; compilation and all four unittest modules in the workflow completed successfully.

Exact custody blobs are recorded in `results/target_discovery/JEPA_LANE_SUCCESSOR_AUDIT_STATE_20261013.json`. The bundle contains the harness contract, rehearsal preflight, tournament controller, presentation-normalized EMA implementation, four corresponding test modules, and the source workflow. The workflow referenced `docs/agent/JEPA_POST_TD_HARNESS_PREFREEZE_20261013.md`, but that path does not exist at the exact source head; this handoff records that fact rather than inventing a document.

The harness constrains output semantics by recoverability class. Point-identifiable targets can produce point state or conditional mean; stochastic-identifiable targets require state-plus-uncertainty or a conditional distribution; teacher-private material is critic-only; not-estimable material must abstain. Aggregate scores cannot rescue failed required block gates.

EMA is normalized to `SUCCESSFUL_BASE_CELL_PRESENTATIONS`, not optimizer-step count. Restart requires persisted EMA updates to equal both controller EMA-update count and global update step. An EMA update requires a proved optimizer step and advances exactly once. Checkpoint overlays bind base checkpoint, portfolio, architecture and EMA state hashes. The EMA screening manifest requires exactly three distinct positive half-lives, labels them short/intermediate/long, and deliberately selects no production half-life.

This is **implementation readiness only**. There is no architecture winner, EMA half-life winner, representation winner, target winner, or training authority.

## 5. Data/results custody

Do not upload the large project binaries to this public repository. Their exact identity and restrictions are already preserved in `docs/agent/JEPA_EXTERNAL_ARTIFACT_CUSTODY_MANIFEST_20261013.csv` and were rechecked against the mounted project files during this takeover refresh.

That manifest covers the repaired 41K expression archive and both transport parts, its checksum ledger, the calibration bundle, the historical program-weight NPZ, the expression metadata bundle, historical defective T1 checkpoint archives, both project-only historical text notes, and the synthetic V2.1 package/pre-fit/controller identities. The two historical text notes are also snapshotted under `docs/agent/external_context/`.

Important classification: the repaired 41K data are address-bound and useful for non-authorizing smoke/historical proxy work; they are not production target/training authority. Historical T1 checkpoints are defective forensic evidence and must never be resumed. Controller bytes remain phase-2-only material.

## 6. Scientific firewalls the next agent must preserve

Candidate/test failure are distinct. A narrow scale failure changes only that scale claim. Source failure changes only the claimed universality across required sources. A technical-control failure changes the program interpretation. `NOT_ESTIMABLE` is not biological failure. Lack of rare relational increment does not imply the rare program is absent. Source-separated evidence cannot be rescued by averaging. Rare identity must be defined independently of the relational geometry under test. Donor is the primary unit. Synthetic qualification evaluates the **test**, not human biology.

The current nine synthetic challenge intents were designed to verify broad/meso, fine recurrent, rare-local island, multi-island, donor-restricted, source-visibility stress, technical-twin negative, null negative and underpowered-positive behavior. Their purpose is to test whether the TD machinery passes, fails or abstains appropriately under known truth; they are not themselves biological validation.

## 7. JEPA-Anything / OPF

JEPA-Anything’s Orthogonal Predictive Factorization is relevant as a prospective representation architecture: it could potentially keep broad, fine, rare and query-dependent predictive structure from competing in one monolithic latent target. It does **not** decide what biological object deserves to be the target, and latent orthogonality is not biological independence. Do not use the paper to reinterpret PR #314 or modify the frozen phase-1 package after the fact.

If OPF is pursued, open a separate prospective qualification branch using frozen known-truth worlds. Test factor stability, donor/source/operator predictability, rare-state enrichment, relational-scale sensitivity, factor ablations, nonlinear dependence and technical-control sensitivity. A factor should never be assigned a pathway meaning merely because an orthogonal coordinate appears enriched.

## 8. Do not repeat these errors

- Do not rerun the spent PR #314 corrected replay.
- Do not resume defective T1 checkpoints.
- Do not regenerate or tune synthetic worlds from the TD lane after seeing TD outputs.
- Do not expose semantic challenge/control labels to the fit side.
- Do not acquire controller truth during a blind phase.
- Do not reconstruct the post-TD harness manually; use the exact custodied blobs.
- Do not re-audit repaired 41K gene/address identity unless bytes/bindings change.
- Do not convert `NE` to FAIL or a fine-scale FAIL into rejection of broad/meso/rare biology.
- Do not silently modify PR #313, PR #314, or synthetic-lane generators/results.
- Do not treat JEPA-Anything/OPF as target authority.
- Do not rely on temporary/probe branch names; the canonical audit/handoff PRs above are the navigation surface.

## 9. Next work queue

First, decide whether a separately scoped phase-2 controller adjudication should be authorized. If yes, bind it to the exact frozen receipt/controller identities, execute only that phase, freeze outputs, and audit before any downstream science. Second, continue the real target tournament only under its own explicit authority and candidate-specific gates. Third, continue target-agnostic teacher/student/uncertainty/EMA integration engineering without converting green engineering tests into scientific winners. Fourth, if desired, evaluate OPF as a new prospective architecture candidate in a separate experiment rather than altering frozen TD qualification history.

## 10. Verification for takeover

A future agent should verify branch/PR head identities, run `scripts/v5/verify_jepa_lane_takeover_manifest_v1.py`, run the successor custody workflow/tests, verify every post-TD path with `git hash-object` against `JEPA_LANE_SUCCESSOR_AUDIT_STATE_20261013.json`, and confirm every authority field remains `false` before making any new decision.

Once those checks pass, **do not restart historical auditing**. Start from the open work queue above and only reopen a historical conclusion when its underlying bytes, contract, or explicitly relevant new evidence has changed.
