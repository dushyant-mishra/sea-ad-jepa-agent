# JEPA V5 — post-Claude FULL104 takeover handoff

Date: 2026-09-18

## 0. Exact takeover state

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Current scientific branch: `impl/v5-full104-post-claude-binding-repair-20260918`

Exact scientific SHA: `72338541c3a161cf461dde5215e6841ee9704ee7`

Draft PR #26: `V5 post-Claude binding repairs: G1 H1 H2`

This handoff package is deliberately documentation-only and is based directly on the exact scientific SHA above. The scientific branch itself still contains stale September-17 startup docs; do not infer scientific staleness from that. Use this docs-only handoff branch for takeover documentation and the PR #26 branch for implementation bytes.

## 1. Why this handoff exists

The previous startup pointer on the scientific branch still named the September-17 lane. That was a documentation-location defect, not evidence that the current implementation reverted. The current implementation is PR #26 at `72338541...`, exact-head CI is green, and terminal outcomes remain sealed.

The user also asked to prevent accidental spillover of older/smaller runs and to start exercising the real FULL104 data sooner so pipeline failures are discovered before months of additional framework work. This handoff therefore separates: (a) current authority, (b) historical/supporting material, and (c) what can safely run over the real FULL104 substrate now without consuming terminal confirmation outcomes.

## 2. Scientific objective and permanent boundaries

The foundation task is biological/cellular latent-state inference from partial RNA, including query-local state associated with a supplied canonical molecular address. It is not hidden-gene scalar reconstruction. Expression, ridge and nonlinear predictors are anti-shortcut diagnostics rather than the scientific target.

Permanent order:

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL`

Permanent rules:

- `IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`
- `TRAINING_OFF`
- protected/pathology/DEV/SEALED/D_shared outcomes remain closed while upstream design is open
- historical/smaller-run material never becomes FULL104 authority by resemblance, filename, schema or prior PASS
- calibration cache role remains `CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1`
- terminal input role remains `AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1`
- structural caller-trust rule: `NO_CALLER_SUPPLIED_DERIVABLE_RECEIPT_FIELDS_V1`

## 3. FULL104 substrate

- 4,553,407 cells
- 104 donors
- 42 operators
- 41,238 canonical addresses
- 17,186 strict common-core addresses
- 8,915 Level-4 blocks
- block manifest: `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- canonical registry: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`
- observation state: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- GPU root: `D:/Jepa project/outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

The >30 GB substrate is available on the user's GPU laptop/attached drive, not in this chat environment. Never request that it be uploaded here and never substitute a smaller cache/dataset as FULL104.

## 4. Current F16/F17 and post-Claude repair state

F16 and F17 were independently attacked at the prior exact head `144873cec377e2cd098ce66220377f10723f413a`. The external review reported 25/25 adversarial attacks behaved correctly for the specified F16/F17 mechanics, with no historical/smaller-run spillover detected. Subsequent review found G1/H1/H2, which are repaired on PR #26.

### G1 — repaired on PR #26

Problem: `null_noise_tolerance_ceiling` could be declared on an evidence object without proving it came from the precision authority.

Current repair:

- evidence carries exact `null_equivalence_margin_numerator/denominator`;
- evidence validation requires exact rational consistency with its float ceiling;
- terminal rung evaluation requires the actual `QualificationPrecisionAuthorityV4` object;
- evidence `precision_authority_sha256` must equal `precision.canonical_digest()`;
- exact rational margin and ceiling must match that precision authority.

### H1 — repaired on PR #26

Problem: prior failed-rung receipts could be caller-constructed and used to walk the terminal burden ladder.

Current repair:

- every prior rung receipt requires a corresponding `MaskingQualificationExecutionAuthorityV4`;
- the execution authority must bind the same RunContract as the current invocation;
- `execution.bind_rung_decision_receipt(receipt)` must succeed;
- prior execution must be `EXECUTED_FAIL`;
- both prior decision-receipt roots and prior execution-authority roots are carried into the terminal raw-result artifact.

### H2 — repaired on PR #26

Policy receipt roots now require lowercase hexadecimal SHA-256, not merely length 64.

### Exact-head CI at 72338541

- FULL104 masking runner: run `35414815529` — SUCCESS — `285 passed`; explicit fail-on-skips check; rerun `285 passed`; zero skipped.
- Stage-A spillover firewall: `35414815136` — SUCCESS.
- V5 runtime closure: `35414815158` — SUCCESS.
- remaining-RNA / target-semantics successor: `35414815141` — SUCCESS.

These green runs prove software regression closure at `72338541...`; they do not prove the remaining scientific design questions.

## 5. Parallel repair branches — DO NOT SILENTLY COMBINE

Three useful candidate repairs remain on parallel branches based on `144873ce...`, not on PR #26:

- PR #23 `impl/v5-full104-terminal-runtime-closure-20260918 @ c7750142e7a585beb53f97aa2b4acb8660004ea3`: direct terminal executor validates a live work checkpoint before consuming evidence.
- PR #24 `impl/v5-full104-null-equivalence-margin-authority-20260918 @ 6379e5b1d62f7d97b5aad70e688fa8d7880618e8`: typed prospective `NullEquivalenceMarginAuthorityV1`, builder removes free numeric margin CLI. This is a candidate G5 repair but its scientific rationale still requires review; do not treat `1/1000` as authority merely because it is typed.
- PR #25 `impl/v5-full104-masking-f16-f17-receipt-hardening-20260918 @ 64affd70cce578459658668f0e1076d212c1ab28`: policy-receipt self-validation against hand-constructed current-looking receipts.

Next integration work must deliberately reconcile these branches onto one successor of `72338541...`, preserving only scientifically justified changes. Re-run the complete exact-head suite and independent red team after integration. Do not resolve PR conflicts merely as housekeeping.

## 6. Current decision mechanics and formulas

Let `m` be the prospectively frozen null-equivalence margin from PrecisionAuthorityV4.

`target_heterogeneity_floor = -m`

Negative-control precision passes only if its two-sided interval contains zero and lies wholly inside `[-m, +m]`.

Primary shortcut-null condition:

`excess_over_shuffled_null.upper_one_sided <= m`

and every fixed-source upper bound must also be `<= m`.

For targeted policies:

`delta_vs_uniform.lower_one_sided > 0`

`target_delta_median >= 0`

every source-specific improvement lower bound `>= 0`,

and

`worst_target_delta >= -m`.

Nonlinear shortcut-null condition:

`nonlinear_excess_over_shuffled_null.upper_one_sided <= m`.

F16 complexity is assembled from the integer target×outer-fold grid:

`mean_effective_targeted_n = total_effective_targeted_n / targeting_complexity_observation_count`.

Current policy selection treats a one-total-event difference as complexity-equivalent before effect lower bound breaks the tie. This exact-lattice implementation is mechanically robust, but G2 remains open because the scientific materiality of one total event does not scale with panel size.

## 7. External audit findings still open

The external reviewer explicitly corrected several of its own initial probes, so use these as hypotheses to verify, not automatic authority.

### G2 — complexity materiality

One total event means a different relative effect on 128, 256, 512 and 1024 target panels. Do not invent another arbitrary percentage after seeing terminal results. Derive the materiality rule from the estimand/design before terminal outcomes.

### G3 — attacker/model capacity mismatch

The current ridge/nonlinear challenge uses 32 features, whereas a production JEPA can observe thousands of remaining addresses per cell. Any current masking PASS is conditional on the tested attacker class and must not be read as proof against a full-context model. A capacity-matched/deep objective-aligned anti-shortcut gate remains required before training.

### G4 — signal preservation

The masking ladder currently measures shortcut suppression, not whether biologically useful state remains learnable. Add a prospective signal-preservation/learnability criterion before treating the selected burden as production-safe.

### G5 — margin rationale

The load-bearing equivalence margin must have an external scientific rationale or a prospective derivation. PR #24 is a candidate mechanism for freezing it, not by itself a scientific justification.

### H3 — target-panel sizing tests the wrong power question

The current target-panel control verdict qualifies on a planted shortcut's one-sided lower bound being `> 0`. That sizes for detecting an easy superiority effect, while the terminal primary question is bounded equivalence near `m`. Before running the panel ladder, redesign/justify the capacity criterion so the selected panel has power/precision for the actual terminal equivalence decision.

### H4 — pre-register fail-closed interpretation

Before terminal execution, define how a complete ladder failure will distinguish at least:

1. targeted masking genuinely does not suppress shortcuts;
2. margin is scientifically too strict;
3. measurement/depth structure is irreducible under current normalization;
4. panel/estimator has insufficient equivalence precision.

Without this, a multi-hour FULL104 failure is not a discriminating experiment.

## 8. What to run on FULL104 now

The user explicitly wants early full-dataset testing to avoid discovering late that the pipeline cannot run. Do that, but keep the confirmation boundary intact.

Safe now, using the real FULL104 store:

1. verify physical Level-4 manifest, registry and observation-state hashes;
2. run the real FULL104 read-only census V2 and reproduce expected support geometry;
3. verify all 104 donors, all 42 operators, source labels and four outer-fold coverage;
4. stream every Level-4 block exactly once and record wall-clock, throughput, peak RAM/GPU memory and failures;
5. build the authenticated calibration-only cache and validate its provenance/role;
6. run calibration-mode preflight and deterministic replay/mechanics checks that do not expose real terminal masking-policy outcomes;
7. exercise serialization/reload of prospective authorities using non-terminal/control outputs;
8. run spillover scans against the actual runtime directory to ensure no Stage81/T1/discovery/RIDGE8 historical artifacts are present.

Stop before the target-panel ladder until H3 is resolved. Stop before any terminal 5% rung until G2/G3/G4/G5/H3/H4 and required branch integration/re-review are closed.

## 9. Representation / geometry / training perspective

Do not let certification apparatus outrun the model. The current open representation/dimension/mechanics work remains F13/F14/F15. In particular, recover and prove the current production representation and dimension/subspace chain rather than assuming historical `VALUE_ONLY_256` prose or historical D_shared work is executable authority.

Historical T1/C2 zero-gradient failure remains design evidence only. Required eventual mechanics include nonzero/subnormal gradient gate, optimizer-step verification, EMA only after proved optimizer step, no-op detection, mixed-precision safeguards, checkpoint-resume semantics and parameter-change verification.

Training stays OFF until the actual current authority graph closes.

## 10. Global caller-trust rule

The recurring F1 -> G1 -> H1 defect class should be handled structurally:

`NO_CALLER_SUPPLIED_DERIVABLE_RECEIPT_FIELDS_V1`

For every authority/receipt constructor and validator: if a field can be recomputed from bound artifacts/objects, recompute it and compare; do not accept the caller's value as evidence. Hashes, counts, margins, status booleans, selected IDs, fold summaries and prior-chain roots all require this audit. Caller-provided filesystem paths are locators only; their contents must be hashed/validated before authority use.

## 11. Local artifacts available in this chat environment

The manifest referenced by the pointer records exact size/SHA-256 for every local file. These are historical/supporting unless explicitly stated otherwise. Heavy binaries are intentionally NOT committed to Git.

Important details:

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`: SHA `07748d5b...`; 50 physical files. Its internal status says `files:97` and its SHA manifest has 97 records, with 49 manifest-listed paths absent physically. Correct description: 97 manifest records, not a self-contained 97-file bundle.
- discovery expression split parts reconstruct a declared 607,959,761-byte ZIP whose recorded SHA is `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`; the two local part hashes match the supplied parts manifest.
- `checkpoints.zip`, `t1_checkpoint_u0200.zip`, `expression.zip`, and the 41,238-address NPZ are supporting historical artifacts only.
- `Pasted markdown.md` is local external-audit source text, supporting audit evidence only.

## 12. Exact next work order

1. Re-fetch live PR/branch heads and verify PR #26 is still at `72338541...`; if moved, classify as `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.
2. Independently re-review PR #26 G1/H1/H2 repairs and the new global caller-trust invariant.
3. Deliberately integrate justified parts of PRs #23/#24/#25 onto one successor of PR #26; do not auto-merge all three.
4. Resolve H3 before target-panel sizing; define equivalence-power/precision criterion prospectively.
5. Resolve G5 margin rationale/authority and G2 materiality before terminal decisions.
6. Design and freeze G4 signal-preservation criterion and capacity-matched G3 anti-shortcut gate.
7. Pre-register H4 fail-closed interpretation.
8. In parallel, run non-terminal FULL104 physical/streaming/census/cache shakedown on GPU hardware.
9. Rebuild and validate the machine checkpoint only after final scientific source freeze on the exact clean GPU worktree.
10. Only after independent review and terminal preflight may the 5% FULL104 terminal rung be opened.
11. Burden sequence remains `5% -> 10% -> 15% -> 20% -> 30% -> 50%`, one rung per invocation, exact proved-failure prefix, stop at first qualifier.
12. A masking PASS still does not authorize training.

## 13. Historical findings in perspective

Use historical failures to explain why present guardrails exist. Do not repeatedly reopen closed T0/T1/QID/F1/Stage81/Layer-2 work unless a current dependency changed. Conversely, do not promote a historical PASS, checkpoint, target list, matrix, seed, fold, burden or result merely because it is convenient or has a matching schema.
