# JEPA V5 — New Chat Takeover: F16/F17 + Handoff/Governance Repair

Date: 2026-09-18

## Purpose

This handoff is intentionally narrow.

The next chat should **fix only the unresolved issues identified in the latest handoff audit**, then requalify the exact changed scientific head and continue the already-defined GPU calibration/freeze sequence.

Do not restart settled T0/T1/QID/F1/Stage81/Layer-2/Stage-A/D_shared work.

Do not open terminal FULL104 masking outcomes while these repairs are open.

## Scientific base to re-fetch

Repository:

`dushyant-mishra/sea-ad-jepa-agent`

Implementation branch:

`impl/v5-full104-masking-redteam2-20260918`

Handoff scientific base:

`3084c1f497a3db6056fd100fb896ccdf67318c8a`

PR:

`#20`

PR base:

`impl/v5-full104-masking-redteam-freeze-20260918`

PR state at handoff:

- open
- draft
- conflicting / not mergeable

Do not resolve PR conflicts as housekeeping. Preserve the scientific lane and repair only what is required.

Exact-head CI at the handoff base:

`35392547631`

Observed workflow log:

- `268 passed`
- explicit fail-on-skips rerun: `268 passed`
- no skips reported

Re-fetch all of this before editing.

---

# 1. FIRST SCIENTIFIC REPAIR — F16 policy-selector materiality

## Current defect

At the handoff base, `select_policy_v2()` in:

`src/sea_ad_jepa/v5/masking_qualification_decision_v2.py`

uses a lexicographic selector whose first targeted-policy key is:

`mean_effective_targeted_n`

and only then:

`-delta_lower_one_sided`

Therefore an arbitrarily small targeting-complexity advantage can dominate a much larger efficacy difference.

Current rule id:

`UNIFORM_IF_SUFFICIENT_ELSE_MIN_TARGETING_THEN_MAX_LOWER_BOUND_V1`

This is a pre-terminal scientific decision-rule defect.

## Required method

Do not invent a post-outcome threshold.

Before changing code:

1. inspect the historical prospective intent of the selector;
2. determine the smallest scientifically defensible prospective materiality/equivalence rule for targeting complexity;
3. freeze that rule before terminal outcomes;
4. make it part of the semantic/decision authority, not a hidden implementation epsilon.

A defensible repair should prevent a microscopic complexity difference from automatically beating a meaningfully stronger qualified policy.

Possible implementation shapes include a prospectively frozen complexity-equivalence margin or an exact discrete-complexity tier derived from the target×fold count geometry. Do **not** choose an arbitrary floating epsilon merely to satisfy a test.

## Required discriminating tests

At minimum create cases where:

- two targeted policies both qualify;
- policy A has a microscopic complexity advantage but materially weaker effect;
- old selector picks A;
- repaired selector does not let that microscopic difference dominate;
- a clearly material complexity advantage still has its intended priority;
- exact ties are deterministic and role/order stable;
- UNIFORM_RANDOM remains selected immediately when it itself qualifies.

The decision-rule ID and receipt schema must change if semantics change.

Update every downstream source hash / RunContract role affected by the changed decision source.

---

# 2. SECOND SCIENTIFIC REPAIR — F17 target-heterogeneity floor

## Current defect

At the handoff base, targeted heterogeneity uses:

`worst_target_delta >= negative_control_delta.lower_two_sided`

inside:

`src/sea_ad_jepa/v5/masking_qualification_decision_v2.py`

This leaves target-level harm tolerance coupled to the *observed* negative-control interval.

F12 already fixed the larger exploit where observed negative-control width could enlarge the overall null tolerance, but F17 preserves a related dependency.

## Required repair

The target-heterogeneity floor must be prospective and independent of the realized negative-control interval.

Before editing, verify the historical intent. Then bind the floor to a pre-terminal authority quantity, preferably the already frozen null-equivalence framework if scientifically appropriate, rather than to `negative_control_delta.lower_two_sided`.

Do not inspect terminal outcomes to set this floor.

## Required discriminating tests

Construct evidence with the same:

- worst target delta;
- frozen null-equivalence margin;
- primary/null/planted/nonlinear evidence;

but vary the admissible negative-control interval.

The heterogeneity PASS/FAIL result must remain invariant to that observed-control variation.

Also test:

- target harm beyond the prospective floor fails;
- target delta within the prospectively allowed equivalence region behaves exactly as specified;
- changing the frozen authority margin changes the rule only through the authority, never through realized negative-control width.

If the decision semantics change, update the rule ID / receipt schema and downstream source bindings.

---

# 3. Requalify after F16/F17

After both repairs:

1. self-review the diff;
2. perform a current-production spillover scan;
3. run the focused exact-head workflow;
4. require the explicit no-skip gate;
5. inspect the workflow log and test count;
6. record the exact new scientific SHA and CI run;
7. independently red-team the repaired selector and heterogeneity rule.

Do not proceed to final masking freeze on merely green unit tests.

---

# 4. Governance/handoff repairs required after the scientific head is stable

These repairs are documentation/governance, but they must describe the **new repaired scientific SHA**, not the old handoff base.

## G1 — stale scientific-head references in active execution plan

`docs/exec-plans/active/JEPA_SCIENTIFIC_BLOCKER_EXECUTION.md`

contains stale references to `93093be1...` and incorrectly associates later CI with that old SHA.

Repair every current-head/CI statement to the final repaired scientific SHA and its actual exact-head run.

Historical SHAs may remain only when explicitly labelled historical.

## G2 — machine-checkpoint / RunContract ordering contradiction

The correct dependency is:

**final committed source freeze -> build/validate machine checkpoint -> build RunContract V4 using that checkpoint -> independent verification -> terminal preflight**

The RunContract builder accepts `--machine-checkpoint` and validates its semantic digest, so documentation must never instruct RunContract first.

Repair the active plan, handoff instructions, and any state document that contradicts this order.

## G3 — checkpoint-state stale self-binding

`docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json`

pins the active execution plan by SHA-256.

After editing the execution plan, recompute its actual SHA-256 and update the checkpoint-state pin in the same coherent governance package.

Verify the checkpoint state is internally current after all governance edits.

## G4 — representation F13 must be split correctly

Do not classify all of F13 as training-side.

`MaskingQualificationDesignAuthorityV2` consumes a representation authority.

Therefore:

**pre-terminal requirement:** instantiate/verify the exact current representation authority and bind it into final Design V2 / RunContract lineage.

**training-side remainder:** executable model use of that representation may remain part of later V5 teacher/student closure.

Carry this distinction into blocker ledgers and execution order.

## G5 — rederive F13/F14/F15 evidence

The preserved Claude second-pass transcript is incomplete for F13/F14 and ends during the V5→V4 seam investigation.

Do not promote the prose summary to authority.

Independently rederive:

- F13: where/if VALUE_ONLY_256 is instantiated as a concrete current production representation authority and what exact bytes/root it binds;
- F14: whether a current V5 dimension/rank/subspace authority exists; distinguish already-closed historical D_shared outcome work from missing current production authority;
- F15: whether `PRODUCTION_MECHANICS_CHAIN_V1` is actually enforced by current executable V5 code/tests, and the exact naming/token drift around the gradient gate.

Preserve the new evidence in the governance handoff.

Do not reopen protected D_shared outcomes.

## G6 — target-evidence-budget role ambiguity

Record both artifacts explicitly:

- `target_evidence_budget_template_authority_v1.py` = burden-free final design template / current freeze role;
- `target_evidence_budget_authority_v2.py` = concrete burden-specific/evidence-budget role where applicable.

Do not let a successor substitute the concrete burden authority for the burden-free Design V2 template.

Update `CURRENT_WORK_CHECKPOINT_STATE.json` inventory accordingly.

## G7 — calibration bundle wording

The existing Project file `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` is supporting/historical.

Document it accurately:

- physical ZIP: 50 files + 10 directory entries;
- internal SHA manifest: 97 data records;
- 49 manifest-listed paths are not physically present in that ZIP;
- separate existing Project artifacts such as `expression.zip`, `checkpoints.zip`, and `t1_checkpoint_u0200.zip` supply some historical material.

Do not call it a self-contained "97-file bundle".

Do not promote any of these historical files to FULL104 authority.

## G8 — execution-plan numbering

Remove the duplicate step 14 while editing the active plan.

## G9 — PR state

PR #20 is draft/conflicting at handoff time.

Record this accurately.

Do not merge/rebase/resolve it automatically merely to make the handoff look clean.

---

# 5. Existing Project files — reference, do not duplicate

The next chat in this same Project can already access the uploaded Project artifacts. Do **not** recreate or re-upload them.

Relevant existing files include:

- `Pasted markdown.md` — latest handoff audit identifying F16/F17 and governance defects;
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`;
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`;
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`;
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`;
- `checkpoints.zip`;
- `expression.zip`;
- `t1_checkpoint_u0200.zip`;
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`;
- `WSL execution issue.txt`;
- `Status and Repair Plan.txt`.

Treat them according to their documented historical/supporting roles.

Previously verified discovery split reconstruction:

- concatenation order: part001 then part002
- combined bytes: `607,959,761`
- combined SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Do not treat availability as authority.

---

# 6. Settled repairs to verify, not redo

At the handoff base, prior audits had already driven repairs for:

- F1 raw-evidence hash binding;
- F2 current PrecisionAuthorityV4 type enforcement;
- F3 mechanical replay/identity/no-privileged-metadata receipts;
- F4 observed outer-fold derivation rather than a free literal;
- F5 one-rung terminal executor;
- F10 explicit fixed-source statistical framing;
- F11 source-specific improvement guardrails;
- F12 frozen null-equivalence margin / negative-control precision floor;
- source binding, mask roots, target/donor/fold identity;
- no terminal cache input;
- no auto-escalation;
- post-run physical Level-4 revalidation.

After F16/F17 edits, verify these remain intact. Do not redesign them without a changed-input reason.

---

# 7. Spillover/self-audit methodology

After every substantive scientific change search the current dependency cone for unauthorized ingress of:

- Stage81;
- T1;
- `X_common6000`;
- discovery 800/2000/6000 universes;
- historical targets/folds/seeds/burdens/target counts/nonlinear caps;
- provisional 20260917 freeze;
- placeholder SHA values;
- stale authority versions;
- historical PASS/FAIL;
- calibration cache in terminal role;
- old terminal runners.

A historical token in a tombstone/audit/test is not itself a defect. The defect is historical material occupying a current production authority role.

Use:

`ALREADY_AUDITED`

`SUPERSEDED`

`OPEN`

`CHANGED_INPUT_REQUIRES_REQUALIFICATION`

for all repeated work.

---

# 8. After these repairs, resume the existing GPU sequence

Do not invent a new roadmap.

Resume the already-defined order:

1. GPU real census V2 receipts;
2. authenticated calibration-only cache;
3. target-panel control-only ladder 128 -> 256 -> 512 -> 1024, first qualifier;
4. final TargetPanelAuthorityV3;
5. OuterSplitAuthorityV1;
6. final PrecisionAuthorityV4 instance;
7. nonlinear control-only cap ladder 64 -> 128 -> 256 -> 512 -> 1024, first qualifier;
8. burden-free evidence-budget template;
9. burden ladder V2;
10. RNG replay V2;
11. NonlinearChallengeAuthorityV3;
12. representation-authority closure required for Design V2;
13. Design V2;
14. final committed source freeze;
15. machine checkpoint;
16. RunContract V4;
17. independent frozen-package audit;
18. terminal preflight;
19. only then open 5% FULL104.

One burden per terminal invocation. No auto-escalation. If 5% qualifies, 10% remains unopened.

Masking PASS still does not authorize training.

---

# 9. Training-side blockers remain separate

After masking-side work, training still requires:

- executable current V5 teacher/student/update path;
- healthy-current-teacher remaining-RNA necessity;
- measurement robustness;
- production geometry;
- geometry-specific memorization;
- enforced production mechanics/gradient recurrence gates;
- runtime/source/environment provenance;
- explicit final training authority.

Do not use F16/F17/governance repair as an excuse to open training.

---

# 10. Required completion report from the next chat

When the next chat finishes this repair package, it must report:

- final scientific implementation SHA;
- exact changed files;
- F16 reproduction and discriminating test;
- F16 prospective repair and authority semantics;
- F17 reproduction and discriminating test;
- F17 prospective repair and authority semantics;
- spillover scan result;
- exact-head CI run;
- regression count;
- no-skip result;
- independent red-team verdict;
- final governance/handoff commit/branch;
- corrected checkpoint-state plan SHA;
- F13/F14/F15 rederived status;
- exact blockers remaining before GPU calibration/final masking freeze.

Do not claim terminal readiness until all of the above is mechanically verified.
