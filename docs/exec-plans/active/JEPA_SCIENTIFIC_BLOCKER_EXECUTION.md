# JEPA Scientific Blocker Execution — Current

Date: 2026-09-18

Status: `F16_F17_REPAIRED__EXACT_HEAD_QUALIFIED__GPU_CALIBRATION_NEXT__TERMINAL_OUTCOMES_UNOPENED__TRAINING_OFF`

## Exact scientific anchor

Branch: `impl/v5-full104-masking-f16-f17-repair-20260918`

SHA: `144873cec377e2cd098ce66220377f10723f413a`

Exact-head verification:

- FULL104 masking runner `35408018294`: SUCCESS — 280 passed; explicit no-skip rerun 280 passed.
- Stage-A spillover firewall `35408018321`: SUCCESS.
- runtime closure `35408018218`: SUCCESS.
- remaining-RNA / target-semantics `35408018310`: SUCCESS.

Historical green heads are historical evidence only and never substitute for the exact current head.

## Method

Before repeating work classify it as `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN`, or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.

For every scientific repair:

1. reproduce the defect;
2. derive the repair prospectively without terminal/protected outcomes;
3. make the narrowest authority-bearing change;
4. add a discriminating adversarial regression;
5. spillover-scan the changed dependency cone;
6. run exact-head CI plus explicit no-skip gates;
7. independently re-review before promotion.

Do not weaken tests to regain green status.

## Closed current findings

### F16 — policy-selector materiality

Closed at the exact scientific head.

Targeting complexity is bound to the exact discrete target × outer-fold lattice:

- `total_effective_targeted_n` is an integer total;
- `targeting_complexity_observation_count` is the exact target×fold count;
- the mean must equal exact total/count;
- off-lattice floats, stale semantic IDs, NaN/Inf and negative complexity fail closed.

Only a one-total-event difference is complexity-equivalent; effect lower bound then breaks the tie. Two or more events preserve the prospective least-targeted priority.

### F17 — target-heterogeneity floor

Closed at the exact scientific head.

The target-harm floor is `-PrecisionAuthorityV4.null_equivalence_margin`, frozen prospectively. It no longer moves with the realized negative-control CI. Negative-control precision remains a separate gate.

### F13 — masking-side representation binding

Closed for masking/pre-terminal use.

`docs/agent/V5_PRIMARY_REPRESENTATION_AUTHORITY_20260915.json` is exact-byte pinned at:

`92756711fde939e27abc982d6ab1a0bc0dab53fae209c0f5a3fba4fde86ef4b1`

It binds FULL104 manifest `66f589e5...`, VALUE_ONLY_256 channel semantics and exact parent/selection artifacts. The current Design V2 builder hard-pins this exact authority and verifies the FULL104 substrate.

Training-side deep-model measurement robustness remains open.

## Open blockers

### GPU masking lane

- real GPU census V2 receipts;
- authenticated calibration-only cache;
- target-panel control-only capacity ladder and final TargetPanelAuthorityV3;
- current OuterSplitAuthorityV1 and PrecisionAuthorityV4 instances;
- nonlinear control-only cap ladder and final NonlinearChallengeAuthorityV3;
- burden-free TargetEvidenceBudgetTemplateAuthorityV1;
- MaskingBurdenLadderAuthorityV2;
- MaskingRngReplayAuthorityV2;
- final Design V2 instance;
- final clean machine/worktree checkpoint;
- final RunContract V4;
- independent frozen-package audit;
- terminal-mode preflight;
- 5% terminal FULL104 rung.

The current one-rung evidence assembler, mechanical-controls layer and executor are already implemented and exact-head tested. Their existence does not bypass final freeze/audit/preflight.

### F14 — dimension/rank/subspace authority

OPEN.

No current V5 qualified-dimension authority instance was established by the current audit. Do not promote historical ranks/widths (5/96/160/224/320/512), qualification ceilings or historical shared-state artifacts into production model width. Do not reopen D_shared outcomes to fill this gap.

### F15 — executable current V5 production mechanics

OPEN.

Closure V2, preexecution V2, the training-authority schema, optimizer guard V3 and runtime-source schema are strong fail-closed gates. But no concrete current runtime-source authority artifact plus production trainer entrypoint is bound to the complete forward → backward → gradient gate → optimizer → EMA chain. `inactive_update_reference.py` is not production runtime.

## Target-evidence-budget roles

Keep these distinct:

- `target_evidence_budget_template_authority_v1.py`: burden-free final Design V2 template.
- `target_evidence_budget_authority_v2.py`: concrete burden-specific evidence-budget carrier when a rung requires one.

The template must never silently freeze a terminal burden.

## Permanent anti-spillover rules

- no Stage81/T1/discovery matrix as FULL104;
- no historical target list, fold map, burden, seed, row cap, target count, selected policy or PASS state as current authority;
- no placeholder/unresolved SHA roots;
- no historical same-schema authority at current ingress without exact explicit reauthorization plus current-root binding;
- no discovery 800/2,000/6,000 universe ladder in final Design V2;
- no calibration cache as terminal or training input;
- no historical T1 checkpoint as healthy-current-teacher authority;
- no historical rank/model width or EMA constant as current default;
- no post-outcome retuning;
- no reopening settled audits without changed inputs.

Intentional historical reauthorization is lawful only when exact historical bytes are pinned, the role is explicitly narrow, current FULL104 roots are bound and tests prevent role expansion.

## Correct execution order

1. Re-fetch live scientific head and PR states; stop on unclassified source/test/workflow drift.
2. Build the explicit masking parameter authority from its narrowly reauthorized frozen provenance.
3. On GPU regenerate real FULL104 census V2 summary/split/target-eligibility receipts.
4. Build authenticated control-calibration-only cache from current FULL104 Level-4 + current registry.
5. Run calibration-mode preflight.
6. Run target-panel ladder 128 → 256 → 512 → 1024 with exact replay; stop at first qualifier.
7. Freeze TargetPanelAuthorityV3 and current OuterSplitAuthorityV1.
8. Freeze PrecisionAuthorityV4, including prospective null-equivalence margin before terminal outcomes.
9. Run nonlinear cap ladder 64 → 128 → 256 → 512 → 1024 with exact replay; stop at first qualifier.
10. Freeze burden-free template, burden ladder, RNG replay, nonlinear V3 authority and Design V2.
11. Commit final scientific source freeze and rerun exact-head CI/no-skips if any source/test/workflow bytes changed.
12. Build and validate `CURRENT_WORK_CHECKPOINT.json` on that exact clean GPU worktree.
13. Build RunContract V4 using the validated machine checkpoint and artifact paths only.
14. Independently audit the frozen package: live source hashes, authority roots, terminal input role, checkpoint semantic digest and no historical/smaller-run role ingress.
15. Run terminal-mode preflight. Any failure is STOP.
16. Only then open the 5% FULL104 terminal rung with the current one-rung executor.
17. If 5% qualifies, stop and leave higher burdens unopened. Escalate only after explicit failure, one rung per invocation.

Masking PASS does not authorize training.

## PR state

- PR #20 belongs to the earlier lane. Preserve its conflict/history; do not clean it up as takeover housekeeping.
- PR #22 contains the focused F16/F17 repair against the audited `3084c1f...` base. It remains draft even if GitHub currently reports it mergeable.

## Calibration-bundle wording

`FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` is historical/supporting only:

- physical ZIP: 50 files + 10 directory entries;
- internal SHA manifest: 97 data records;
- 49 manifest-listed paths are not physically present in that ZIP;
- separate Project artifacts supply some historical material.

Do not describe it as a self-contained 97-file FULL104 bundle and do not promote it to current FULL104 authority.
