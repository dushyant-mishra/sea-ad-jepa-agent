# JEPA NEW CHAT HANDOFF — 2026-09-11 POST-V21-REPAIR CURRENT

Status: `CURRENT_HANDOFF_CANDIDATE__POST_V21_AUTHORITY_REPAIR__NO_TRAINING_AUTHORITY`

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Handoff branch: `handoff/jepa-new-chat-20260911-post-v21-repair-current`

This handoff supersedes the morning 2026-09-11 integrated handoff **for startup context only**. It does not by itself confer scientific authority on any repair branch. Branch names, passing focused tests, design prose, or a committed repair are not production/training authority.

## 0. First instructions for the next chat

1. Open `START_HERE.md` first on this handoff branch.
2. Read `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json` on this handoff branch.
3. Read this file completely.
4. Read `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260911_POST_V21_REPAIR_CURRENT.json`.
5. Re-fetch every live head below before writing or executing. Do not trust the SHAs in this handoff if a branch has moved.
6. Do not restart the project analysis from scratch.
7. Preserve frozen V20 unchanged.
8. Do not run S0-S4, fresh AT8, `reader_validation`, `reader_oracle`, or training until the explicit prerequisites below close.
9. Use iterative self-review/red-team method: inspect -> write a failing/adversarial test -> minimal repair -> full relevant regression surface -> clean-tree/archive rerun -> independent re-audit.
10. Any documented limitation that code does not enforce is only a comment, not a limitation.

## 1. Permanent scientific boundary

The production chain is one integrated scientific object:

`raw SEA-AD substrate -> discovery population/masks -> target discovery -> target statistical qualification/freeze -> teacher target -> V5 student/teacher training -> downstream evaluation`

A technically correct V5 model cannot rescue a circular/confounded/leaky target. A biologically valid target cannot rescue a V5 learner that exploits identity, technical nuisance, same-cell leakage, target recomputation, or post-hoc threshold selection.

Training remains OFF.

Standing rule:

`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

Synthetic/small fixtures are unit/mechanics evidence only. They cannot set production biology, dimensions, thresholds, schedules, power, or training authority.

## 2. Authenticated production population and heavy-data authority

Historical/current project authority has already established the intended production population geometry:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / matrices
- 41,238 molecular addresses
- 17,186 common measured-core addresses
- historical FULL104 Phase2 block manifest: 8,915 blocks
- historical Phase2 manifest SHA-256: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`

Important correction to the older main handoff: FULL104 is **not a dataset rediscovery/recovery project**. Population authority, manifest identity, B2 verifier logic, row/block/payload/identity binding machinery, and reader-fit population geometry were developed earlier. The unresolved status question is narrower: recover whether the final one-shot production B2/full-expression verifier was subsequently executed on the real store and produced the terminal receipt. The older governance text still says `STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`; do not assume that is the latest factual state without checking later evidence/receipts.

If no later production receipt is found, Claude/hard-drive lane should run the already-built one-shot verifier against the known real substrate and return the receipt. Do **not** rebuild the substrate from scratch.

Already separate and closed:

- full reader proposal-weight / affine-order / packing / restart replay
- `H = 5,267,086` presentations
- terminal `PASS_FULL_READER_PROPOSAL_WEIGHT_PACKING_RESTART_REPLAY`
- presentation-stream SHA-256 `08a1df725b3803d049cf6a0a75811c1863b4bd0b537ed2ecaf70445380f02f74`

This packing/restart PASS does not create expression, biological-target, production-dimension, GPU, postqualification, or training authority.

## 3. Frozen T0 V20

Frozen branch:

`t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`

V20 is immutable.

Current frozen interpretation:

- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- training unauthorized

Do not modify V20 to repair V21.

## 4. V21 prospective design authority

Historical design branch:

`t0/v21-prospective-design-20260910 @ 11e76d36ace556ac48cdd2992995e63c1e35df18`

Status remains design/prospective authority, not executed target-discovery authority.

Frozen donor hierarchy in the design:

- 28 discovery donors: all method/estimator/ridge/power design work
- 18 spent historical-validation donors: development/internal sensitivity only
- 12 fresh `reader_validation` donors: one single-shot T1 confirmation only after complete freeze and a valid power authority
- 10 `reader_oracle` donors: sealed final reserve

T2 remains decoupled from the T1 freeze. MTG remains the T1 confirmation tissue. Cross-region work is secondary generalization, not an independent confirmation cohort.

Nothing in the current work opened fresh AT8, `reader_validation`, or `reader_oracle`.

## 5. V21 executor successor from Claude

Claude executor successor branch:

`review/t0-v21-successor-20260911`

Key known commits:

- original executor successor: `4e60caea2d9370671b572f93ccf31d21dcd88842`
- later effect-transport fail-closed successor: `3a8c8e3e5ca84d38eb363e9791e1c86c854a55af`

Major executor repairs:

1. Cross-fit verification no longer trusts sealing. A canonical structural validator is used by both sealing and verification, and the digest binds decision-relevant fields.
2. Confirmation covariates are treated as a frozen design envelope, not caller-supplied protected-cohort arguments.
3. Discovery geometry is measured from the actual out-of-fold score while confirmation geometry is bounded over a frozen admissible class.
4. Whole-pipeline permutation evidence is required and digest-bound.
5. Null calibration demonstrated that the assembled HC3 t under the full overlapping cross-fit procedure is wider than nominal; reported historical measurements were approximately 1.304x nominal SD for fixed ridge and 1.477x with inner LOODO selection.

The committed null-calibration evidence/manifest was added under the executor successor lineage.

### 5.1 Critical scientific correction: effect transport remains OPEN

The earlier design used or discussed a standardized quantity of the form:

`delta = t / sqrt(n)`

and prospective projection of the form:

`t_projected = delta * sqrt(n_confirmation)`

For the old 28-discovery / 12-confirmation design this appeared as `t/sqrt(28)` transported to `sqrt(12)`.

The null calibration shows that this cannot be treated as an authority-bound effect transport under the overlapping nested cross-fit procedure. The 1.304/1.477 null-spread measurements are evidence that the old mapping is not justified; they are **not** themselves replacement correction factors.

The executor now records:

- `EFFECT_TRANSPORT = OPEN`
- `POWER_GATE_PRODUCTION_VERDICT_CAPABILITY = DISABLED`
- `STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND`

The old arithmetic survives only as planning/diagnostic projection. It must not expose `clears_gate=True` or otherwise become production authorization.

Whole-pipeline permutation can establish a procedure-specific association/null claim. It does not automatically establish a transportable effect magnitude for the fresh n=12 confirmation design.

Scientific separation to preserve:

`whole-pipeline permutation -> association evidence`

`cross-fitted HC3 t -> descriptive/studentized statistic`

`effect transported to n=12 -> NOT AUTHORIZED until separately derived/calibrated`

Do not invent a correction factor from observed null SD inflation.

### 5.2 Confirmation sex-balance admissibility

Claude measured that a 1/11 sex split at n=12 gives singleton HC3 leverage 1.0000 and is non-estimable. Reported leverage examples:

- minority count 1: 1.0000, non-estimable
- minority count 2: about 0.6579
- minority count 3: about 0.6965
- balanced 6/6: about 0.6978

Therefore the fresh confirmatory cohort design requires at least two donors of each sex for the intended HC3 nuisance design to be estimable. This is a cohort-admissibility condition, not a tuning choice and not permission to inspect protected outcomes.

## 6. V21 authority-wrapper regression: cause and repair

### 6.1 Regression cause

The branch `repair/t0-v21-authority-hardening-20260911 @ 9f98320f03e19577527b2153159ea0df2c62babd` was produced by promoting an incomplete locally reconstructed `scripts/v4/t0_v21_authority_v1.py`.

The focused local 23-test surface did not cover the complete historical authority API. Relative to the earlier good authority implementation `a36fd209b40aa9c28cd3d6790bda1fe5054a1923`, the promoted file deleted major API functions, including seal/validate functions and `decision_capable_power_gate`.

This was not a Git random deletion and not Claude's merge. It was a bad local reconstruction/promotion combined with insufficient regression coverage.

The integrated candidate:

`review/t0-v21-integrated-candidate-20260911 @ c8a1947ea109e11f20277917410ebc1992ae400f`

faithfully exposed that regression: executor tests passed, while the authority/measurement suites failed because the wrapper API was truncated.

### 6.2 Dedicated authority repair line

A repair branch now exists:

`repair/t0-v21-integrated-authority-regression-20260911 @ 9a861b41607b16cb40a8240ecda025c9447514ae`

Known repair commits on that line include:

- `3a63e79a41ac59f4f4985cfaa8f66c9dda16cf84` — restore pre-hardening authority implementation as reference core
- `46aa81920327c898834feae157bdbd11d0b61e70` — restore complete authority surface and fail closed on open transport
- `be9230f2d5b2b6f8690d96ecca33f4f132a63080` — replace stale production-verdict expectation with fail-closed authority regressions
- `9a861b41607b16cb40a8240ecda025c9447514ae` — add clean-runner CI verification for the integrated authority repair

A separate restoration branch also exists:

`repair/t0-v21-authority-restoration-20260911 @ 93abcf50e89778585bda1e20f2eab824cc6bae77`

The restoration line is ahead of the earlier good `a36fd209...` lineage and contains dedicated restoration regressions.

### 6.3 Qualification status of the repaired authority line

Do not yet call `9a861b41...` independently qualified solely because the repair is present.

At handoff creation time GitHub's commit-status endpoint for `9a861b41...` reported no completed statuses (`total_count = 0`, state shown as pending). Therefore:

- repair code exists
- API restoration commits exist
- clean-runner workflow/CI support exists
- but the handoff does not claim a completed independent exact-head CI result from GitHub status

Next chat must re-fetch statuses/check-runs and, ideally, independently run the complete combined V21 suite from a clean archive/worktree before promoting/finalizing this repair.

### 6.4 Required anti-regression rule going forward

No future authority-file promotion may rely only on a focused test subset.

Before promotion of `t0_v21_authority_v1.py` or equivalent authority modules, require all of:

1. compare exported/public API against the last known-good authority surface;
2. fail if required seal/validate/gate symbols disappear unexpectedly;
3. run the full authority tests;
4. run the measurement/freeze tests;
5. run the executor tests;
6. run explicit fail-closed effect-transport tests;
7. run from a clean archive/worktree containing tracked bytes only;
8. inspect diffstat for suspicious large deletions before push;
9. if a file has net large deletion, require manual/API-surface review before promotion;
10. never infer authority from a focused green suite.

## 7. V21 currently allowed vs forbidden

Allowed now:

- code review
- adversarial/mutation review
- planning-only power calculations
- discovery-side simulations/calibration that do not use protected confirmation outcomes
- repair of executor/wrapper/receipts
- derivation or simulation study for a valid effect-transport estimand

Still forbidden:

- real S0-S4 selection run before executable measurement/producer review closes
- production power verdict while effect transport is OPEN
- fresh AT8 opening
- `reader_validation` outcome opening
- `reader_oracle` opening
- post-confirmation retuning
- training

## 8. What remains scientifically open in V21

The most important remaining scientific blocker is no longer basic cross-fit mechanics. It is:

`STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND`

A defensible mapping is needed from discovery-side procedure output to an effect quantity that can support prospective confirmation power.

Valid routes include:

- mathematical derivation from the actual overlapping nested cross-fit dependence structure, then simulation verification;
- controlled known-effect/injected-effect simulations that rerun the entire frozen discovery procedure and empirically identify a stable conservative mapping;
- preferably theory + simulation.

The mapping must be learned from discovery-side authorized information/procedure. Do not use the fresh 12 validation donors to calibrate it.

If no stable conservative transport exists, the correct conclusion may be that the present n=12 confirmatory power claim is unsupported under this design.

## 9. S0-S4 implementation / measurement layer

The design has a closed prospective S0-S4 estimator family and ranking/tie-break semantics, but production execution remains unauthorized.

Before any real S0-S4 selection run, external/adversarial executable review must close at least:

- exact raw-expression discovery population and mask identities;
- donor-level split independence; no cell-level pseudoreplication masquerading as donor evidence;
- no leakage from spent/protected AT8, fresh validation, or oracle;
- legal normalization/feature-selection/PCA/cache fit scope;
- exact S0-S4 construction;
- exact outer-LODO / inner-LODO mechanics;
- one OOF prediction/score row per discovery donor;
- nuisance design and HC3 implementation, if retained diagnostically;
- whole-pipeline permutation producer and receipt binding;
- effect-transport authority or explicit production power disablement;
- donor robustness, retention, sparsity, preprocessing sensitivity;
- technical confound attacks: donor, batch/library, depth, source/dataset, specimen;
- duplicate/near-duplicate leakage;
- target measurability at deployment;
- immutable target lineage into V5;
- proof V5 cannot substitute, recompute, tune, or redefine the frozen target.

Do not confuse a design document with this executable closure.

## 10. V5 repairs completed in this environment

### 10.1 Qualified-target / optimizer guard branch

Live repair branch observed at handoff creation:

`repair/v5-qualified-target-guard-20260911 @ da8bd7dfe138fc4b36c11007d0a0165cd2365bcc`

Key repair in this chat:

- same-cell cosine calculation no longer treats asymmetric `(nonzero, zero)` or `(zero, nonzero)` as perfect cosine 1.0;
- edge cases were added for asymmetric zero, zero/zero, near-zero/finite stability, NaN/Inf, and extreme scale;
- implementation was made scale-stable rather than relying on a norm product that can overflow/underflow on finite values.

Focused optimizer-guard regression was reconstructed in this environment after restoring missing handoff-package dependencies and reproduced 12 passing tests. Treat that as local focused evidence, not final production authority.

### 10.2 Executable-power authority successor

Live successor branch observed at handoff creation:

`repair/v5-executable-power-authority-20260911 @ 52fca8ab7f23f2235ff37be0521ca9444165b2ef`

Reason for successor:

The older rejection-power calibration path accepted report-level booleans stating that valid/invalid controls were accepted/rejected. Downstream postqualification could consume those assertions and advance to `production_training_eligible=True` without independently executing/recomputing the frozen gates.

The successor adds an executable-power receipt and versioned downstream closure requiring, per canonical gate:

- frozen gate identity
- valid/invalid control artifact identity
- raw numerical output hashes
- execution code hash
- independent recomputation code hash
- context/checkpoint binding
- parent/child artifact binding
- independent recomputation rather than caller self-attestation

Focused local tests for the successor chain passed 5/5, including rejection of:

- legacy V3 report-only power
- missing/tampered raw-output hashes
- non-independent recomputation
- stale child-artifact substitution
- mixed design contexts

The successor does not authorize training. It is intended to prevent a report-only path from manufacturing eligibility.

### 10.3 Remaining V5 blocker in this environment

The exact **reachability audit** is still open:

Determine whether any currently active/prospective production-facing entrypoint can still call the legacy chain:

`report-only power V3 -> dependency closure V1 -> postqualification V2 -> production_training_eligible=True`

Creating a safe V3 successor is insufficient if old production selectors can still invoke V2 directly.

Next chat should finish the import/call-graph audit and either:

- prove the legacy path is unreachable from all active production entrypoints, or
- cut it through a versioned selector/runtime successor and add a deliberate bypass test.

Do not rewrite historical V1/V2 artifacts merely to hide their existence; preserve them as historical and make the active successor path explicit/fail-closed.

## 11. Historical QID/F1 semantic debt — not current V5 blocker unless resurrected

Historical exact locus:

`dd078625c3537f5ff2c3f8c0b382ba2803b24ee2`

Recovered behavior:

- `contextual_target_f1_preflight_executor_v1.py::qid_v2` defines QID margin as `own_similarity - paired_wrong_similarity`.
- `f1_real_producer_v1.py::_effect_row_from_states` supplied the matched-null student state against the true teacher as the value called `paired_wrong_similarity`.
- matched-null lineage preserves recipient query identity while substituting donor-distinct normalized values.

No frozen authority was recovered establishing:

`matched-null state intervention == paired-wrong-query intervention`

Historical fail-closed marker:

`STOP_F1_QID_WRONG_ARM_SEMANTICS_NOT_AUTHORITY_BOUND`

Current repaired V5 did not show active QID/`paired_wrong_similarity` computation in the inspected path, so classify this as historical lineage/authority debt, not a present training blocker unless current code resurrects or depends on it.

## 12. Heavy/runtime assets and hashes

Do not duplicate very large immutable assets unnecessarily. Use the canonical heavy-asset/runtime references unless bytes are needed locally.

Known important assets/hashes from project history:

- Foundation 41K discovery expression archive SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- part001 SHA-256: `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- part002 SHA-256: `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- Foundation calibration bundle SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- historical biology evaluation cohort: 4,540 rows, SHA-256 `d7cfbe006f6dc04bee96041fcf4ce78595b87a724f8a78d14f32a07651f268a1`
- historical intrinsic-label cohort: 4,540 rows, SHA-256 `ba50eb0a6683621fc60fd30f2126bb9fb4a609286360463a964dfb8a7b4af52b`

Prior runtime paths may include foundation archive parts, calibration bundle, checkpoints, expression zip, and `t1_checkpoint_u0200.zip`; always verify actual runtime presence and hashes before use.

`/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` remains `PROVENANCE_MISMATCH_DO_NOT_USE` unless a later authority explicitly supersedes that finding.

Canonical historical references remain:

- `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`
- `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`
- `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`

## 13. Production dimensions

Production dimensions remain unresolved unless a later receipt explicitly closes them.

Historical dimensions such as 5 / 96 / 160 / 224 / 320 / 512 are not production authority merely because they were used previously.

Production dimensions must be derived at the correct point through the frozen dataset-first qualification chain using the real authorized substrate. Do not set them from synthetic/small cohorts and do not improvise them simply because Claude has the full data.

## 14. Anti-cheat requirements to preserve

Historical JEPA training repeatedly found shortcuts. The target architecture therefore requires explicit anti-cheat qualification.

Important adversarial families include:

- direct identity copy
- masked-input leakage
- shared-view leakage
- constant / near-constant representations
- depth-only solutions
- donor/batch/source encoding
- lookup memorization
- duplicate/near-duplicate cells
- deterministic preprocessing/cache leakage
- target-gene overlap leakage
- pre-split cache fitting
- checkpoint/threshold selection on protected confirmation
- corrupted biology with technical structure preserved
- technical nuisance recovery from donor-held-out representations

A low loss, pretty embedding, smoke test, or passing mechanics suite is not biological proof.

## 15. Current live heads to re-fetch at startup

At handoff creation time the relevant observed heads were:

- `main @ ba3f2a1200d0bbaf4b9ee0d7d16ddc17341d779f`
- `t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`
- `t0/v21-prospective-design-20260910 @ 11e76d36ace556ac48cdd2992995e63c1e35df18`
- `review/t0-v21-successor-20260911` — re-fetch; known key executor successor `3a8c8e3e5ca84d38eb363e9791e1c86c854a55af`
- `review/t0-v21-integrated-candidate-20260911 @ c8a1947ea109e11f20277917410ebc1992ae400f` — known broken authority wrapper integration; historical review target only
- `repair/t0-v21-integrated-authority-regression-20260911 @ 9a861b41607b16cb40a8240ecda025c9447514ae` — current integrated authority repair candidate; independently re-qualify before promotion
- `repair/t0-v21-authority-restoration-20260911 @ 93abcf50e89778585bda1e20f2eab824cc6bae77`
- `repair/v5-qualified-target-guard-20260911 @ da8bd7dfe138fc4b36c11007d0a0165cd2365bcc`
- `repair/v5-executable-power-authority-20260911 @ 52fca8ab7f23f2235ff37be0521ca9444165b2ef`
- `planning/v5-full-population-cheat-proofing-20260909` — re-fetch before use; earlier governance head was `1de20b1c222c7fb27fcef5ec1a4b798d5b26a534`

Branch names do not confer authority.

## 16. Immediate next-work order for the new chat

### Lane A — V21 authority repair verification here

1. Re-fetch `repair/t0-v21-integrated-authority-regression-20260911`.
2. Compare its `t0_v21_authority_v1.py` API against the last known-good `a36fd209...` and intended hardening.
3. Verify required seals/validators/`decision_capable_power_gate` are restored.
4. Verify open transport forces fail-closed behavior.
5. Run the complete authority + measurement/freeze + executor suites, not a focused subset.
6. Run from a clean archive/worktree containing tracked bytes only.
7. Inspect diffstat/API-surface guard before any promotion.
8. Re-run mutation/adversarial tests if available.
9. Only after exact-head independent PASS should the repair become the new integrated V21 review candidate.

### Lane B — V5 legacy-path reachability here

1. Re-fetch `repair/v5-executable-power-authority-20260911` and `repair/v5-qualified-target-guard-20260911`.
2. Trace imports/callers of legacy dependency closure V1 and postqualification V2.
3. Prove whether report-only V3 can still yield eligibility through any active production entrypoint.
4. If reachable, add a versioned active-path selector/entrypoint that requires executable-power V4/V2/V3 successor chain.
5. Add a deliberate bypass test.
6. Preserve historical files; supersede rather than rewrite history.

### Lane C — effect-transport science, shared design/review

1. Keep production power verdict disabled.
2. Define the candidate estimand and legal discovery-side calibration experiment.
3. Prefer whole-procedure known-effect simulations and/or derivation of dependence-aware transport.
4. Do not use the fresh 12 outcomes.
5. Require a frozen derivation/receipt before any production `clears_gate=True` capability can return.

### Lane D — Claude/hard-drive data execution

1. First search for the later FULL104/B2 real-execution receipt; do not rebuild FULL104.
2. If absent, run the existing one-shot B2 verifier against the already-known real substrate and return exact manifest/count/hash/terminal evidence.
3. Run only non-protected full-data lineage/confound/identity audits that are authorized before S0-S4.
4. Do not run S0-S4 until its executable producer/measurement layer has passed external/adversarial review.
5. Do not open fresh validation/oracle.

### Lane E — after A-D close

Only after executable S0-S4 review + data identity/lineage closure + valid effect-transport/power authority should a real discovery-only S0-S4 run on the 28 discovery donors become eligible.

Then audit that output before considering the fresh 12-donor single-shot confirmation.

Oracle stays sealed.

V5 full/GPU production qualification comes only after a target is legitimately qualified/frozen and target->V5 lineage is immutable.

## 17. Things not to do

- Do not merge/delete old branches merely to make the repo look clean before authority/supersession is documented.
- Do not modify V20.
- Do not run protected confirmation to help choose a method.
- Do not treat permutation significance as effect transport.
- Do not treat observed null SD inflation as an automatic correction factor.
- Do not treat a focused green suite as API-complete regression coverage.
- Do not promote locally reconstructed files without API/diff parity against the known-good source.
- Do not treat synthetic dimensions or historical architecture widths as production dimensions.
- Do not treat TRAIN cache closure as FULL104 expression closure.
- Do not let V5 recompute/redefine the frozen teacher target.
- Do not claim training authority while any upstream target-discovery authority remains open.

## 18. Current project verdict

`NO_PRODUCTION_TRAINING_AUTHORITY`

`V20_IMMUTABLE`

`V21_EFFECT_TRANSPORT_OPEN`

`V21_POWER_GATE_PRODUCTION_VERDICT_DISABLED`

`V21_AUTHORITY_REPAIR_PRESENT_BUT_REQUIRES_EXACT_HEAD_INDEPENDENT_REQUALIFICATION`

`S0_S4_NOT_AUTHORIZED`

`FRESH_READER_VALIDATION_SEALED`

`READER_ORACLE_SEALED`

`V5_EXECUTABLE_POWER_SUCCESSOR_PRESENT__LEGACY_REACHABILITY_AUDIT_STILL_OPEN`

`FULL104_DATASET_NOT_A_REDISCOVERY_TASK__FINAL_B2_EXECUTION_RECEIPT_STATUS_MUST_BE_RECOVERED_OR_RERUN`

Training remains OFF.