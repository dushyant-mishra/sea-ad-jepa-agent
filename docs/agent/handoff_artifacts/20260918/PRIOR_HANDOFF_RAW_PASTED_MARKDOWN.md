We are continuing the JEPA project. Do not restart the project from scratch and do not repeat closed audits without changed input.

Repository:

dushyant-mishra/sea-ad-jepa-agent

Current implementation branch:

impl/v5-full104-masking-redteam2-20260918

Current implementation/governance head:

d6ef93e274e42e17d78f3fc652b0dfec202036ac

Scientific source/test/data anchor underneath the docs-only governance repair:

86692cde7e61fe4beae7fff4070bd376a8090af2

Current audited handoff branch:

handoff/jepa-v5-full104-calibration-audited-20260918

Current audited handoff commit:

c8346518e9099a48ea92c8db8344d405eaa28ab6

Draft implementation PR:

\#20

PR base:

impl/v5-full104-masking-redteam-freeze-20260918

The older handoff branch `handoff/jepa-v5-full104-calibration-20260918` is SUPERSEDED. Do not use it as current authority.

## Mandatory startup

1. Re-fetch the live GitHub heads before doing anything. Verify the audited handoff is still exactly one docs-only commit above the implementation branch. Verify PR #20 head/base. If source/test/data bytes have moved beyond `86692cde...`, inspect the delta and classify it as `CHANGED_INPUT_REQUIRES_REQUALIFICATION` before proceeding.
2. Read the current authority package in this exact order:

START\_HERE.md

docs/agent/JEPA\_LATEST\_HANDOFF\_POINTER.json

docs/agent/JEPA\_NEW\_CHAT\_HANDOFF\_20260918\_V5\_FULL104\_MASKING\_CALIBRATION\_CURRENT.md

docs/agent/JEPA\_NEW\_CHAT\_HANDOFF\_STATE\_20260918\_V5\_FULL104\_MASKING\_CALIBRATION\_CURRENT.json

docs/agent/JEPA\_NEW\_CHAT\_COMMANDS\_20260918\_V5\_FULL104\_MASKING\_CALIBRATION.md

docs/agent/CURRENT\_WORK\_CHECKPOINT\_STATE.json

docs/exec-plans/active/JEPA\_SCIENTIFIC\_BLOCKER\_EXECUTION.md

docs/agent/handoff\_artifacts/20260918/V5\_FULL104\_MASKING\_DATA\_RESULTS\_SCRIPTS\_MANIFEST.json

docs/agent/JEPA\_HISTORICAL\_AUDITS\_INDEX\_20260915.md

docs/agent/JEPA\_HEAVY\_ASSET\_REFERENCE\_20260909\_FINAL\_R4.md

3. Audit the handoff as an authority package, not merely as prose. Cross-check branch ancestry, PR metadata, source/test/script path existence, hashes, authority versions and command executability. Stop on contradictions.
4. Use our normal classification before repeating historical work:

ALREADY\_AUDITED

SUPERSEDED

OPEN

CHANGED\_INPUT\_REQUIRES\_REQUALIFICATION

Do not redo settled work simply because this is a new chat.

## Working methodology

Use the same iterative process we have been following.

Work in small auditable increments.

Before implementation, identify the scientific claim and the failure mode the change is supposed to prevent.

Write behavior tests before or with implementation changes.

After implementation, self-review it adversarially.

Run focused tests and fail closed on skips.

Use an independent verifier/red-team pass before promoting conclusion-bearing work.

Check whether any historical artifact, smaller dataset, fixture, placeholder, old target list, old fold assignment, exploratory hyperparameter or stale authority has accidentally entered the current FULL104 chain.

Treat accidental spillover as a first-class failure condition.

When historical findings are useful, preserve them in the correct role: they may tell us what hypothesis is worth independently confirming, but they do not automatically become FULL104 authority.

Do not invent a threshold or authority simply because it is computationally convenient.

Do not use confirmation outcomes to choose an upstream design parameter.

If confirmation data could change a design choice, do not inspect those outcomes until the design is frozen.

Preserve dirty workspaces. Do not reset, clean, stash, rewrite history or overwrite user changes. Use isolated worktrees when appropriate.

Codex/ChatGPT and Claude are equal implementation peers. Neither may self-promote conclusion-bearing work. Maintain implementer + independent verifier discipline.

## Biological objective

The project is trying to infer biological/cellular state from partial RNA, including query-local biological state associated with a supplied canonical molecular address.

We are NOT training a hidden-gene scalar imputation model.

Expression ridge/correlation/nonlinear models are anti-shortcut diagnostics only.

A reduction in hidden-expression predictability is not itself evidence that the JEPA recovered biological state.

Permanent work order:

DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> TARGET SEMANTICS -> PRODUCTION GEOMETRY -> MODEL

## FULL104 authority

Current authenticated substrate:

4,553,407 cells

104 donors

42 operators

41,238 addresses

17,186 strict common-core addresses

8,915 Level-4 blocks

Block-manifest SHA-256:

66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29

Observation-state SHA-256:

852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537

Canonical registry SHA-256:

7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd

GPU Level-4 root:

D:/Jepa project/outputs/full104\_v014\_20260826/03\_phase2\_state\_derivation\_v1/expression\_level4/

Never substitute Stage81A3, T1 checkpoints, discovery archives, exploratory matrices or any smaller/historical cache for FULL104.

## Changed-input census that must remain in perspective

Corrected strict-core measured-zero frequency:

0.832983

Strict-core nonzeros:

13,069,917,135

Strict-core measured zeros:

65,184,935,567

Addresses estimable in every four donor-held-out folds:

17,053 / 17,186

104 donors are the independent inclusion units; Kish ESS is approximately 42 donor-equivalents.

Consequences:

Measured zero is real measured evidence, not structural missingness.

Use strict `MEASURED_SCALAR` support.

Masking eligibility is value-independent over strictly measured non-target addresses.

Do NOT inherit the old 15% burden from the exploratory 800-address universe.

The GPU machine still must regenerate the real V2 census execution receipts from the authentic `pass1.npz`. Repository constants do not replace runtime receipts.

## Historical masking findings — correct role

The September-17 discovery work supports this candidate for independent FULL104 confirmation:

targeted partner cap = 8

ridge candidate pool = 64

ridge score features = 32

ridge alpha = 1/100

PREFIX inner folds = 3

PREFIX candidates = 20

PREFIX floor = 1/20

PREFIX reduction = 1/2

These are not hidden defaults. They are the exact pre-FULL104 candidate worth independently testing.

Historical data, target lists, folds, burden, seeds and row caps must NOT spill into the current run.

The historical nonlinear work may support model shape only.

RIDGE8 is still only the strongest broad exploratory candidate tested so far. No production masking policy is selected.

## Current calibration architecture

The FULL104 calibration cache has the permanent role:

CONTROL\_CALIBRATION\_ONLY\_\_FORBIDDEN\_FOR\_TERMINAL\_MASKING\_QUALIFICATION\_V1

It is an acceleration/calibration artifact only.

It may never be used as the terminal FULL104 masking substrate or as training input.

Terminal masking must use:

AUTHENTICATED\_FULL104\_LEVEL4\_BLOCK\_STREAM\_V1

Target-panel capacity ladder:

128 -> 256 -> 512 -> 1024

Nonlinear row-cap ladder:

64 -> 128 -> 256 -> 512 -> 1024

For both ladders:

use control-only evidence;

real terminal masking-policy outcomes remain closed;

require exact replay;

stop at the first qualifying rung;

never inspect higher rungs after a lower rung passes.

Important replay rule:

Run A and Run B MUST use different output directories.

The evaluator writes matrices into its output directory before checking replay inputs. Therefore never point Run B at replay matrices in the same directory it is writing. Preserve Run-A matrices unchanged and use them as Run-B replay inputs.

## Immediate work sequence

First, run focused CI on the exact current implementation head. GitHub recorded no workflow runs for `d6ef93e...` at this handoff. Do not report older `8ee5d0a5...` green workflows as verification of the current head.

Fail closed on all skips or new failures.

Then refresh or supersede:

scripts/agent/v5\_full104\_masking\_gpu\_preflight\_20260917.ps1

It is stale for the V4/cache-calibrated chain and must not be used as final GPU authority.

The replacement preflight must check current branch/head, clean isolated worktree, manifest/registry hashes, current census/support/split/eligibility roots, calibration-cache role, authenticated terminal-stream role, current authority/source hashes, anti-spillover V2 and fail-on-skips tests.

Then follow the exact executable templates in:

docs/agent/JEPA\_NEW\_CHAT\_COMMANDS\_20260918\_V5\_FULL104\_MASKING\_CALIBRATION.md

Do not reduce them to bare script names.

The intended order is:

build MaskingQualificationParametersAuthorityV2;

regenerate real census V2 summary/split/target-eligibility receipts;

build census authority V2;

build authenticated calibration-only cache;

verify cache hashes, role, all 104 donors and closure;

run target-panel ladder with separate Run-A/Run-B replay directories;

build target-selection receipt;

build TargetPanelAuthorityV3;

build OuterSplitAuthorityV1;

build PrecisionAuthorityV4;

build nonlinear model-capacity authority V1;

run nonlinear row-cap ladder with separate Run-A/Run-B replay directories.

## Three implementation gaps that must be closed before terminal masking

Do not pretend these already have executable final builders.

There is currently no final current builder for:

NonlinearChallengeAuthorityV3

MaskingRngReplayAuthorityV2

MaskingQualificationRunContractV4

The existing:

scripts/agent/build\_full104\_nonlinear\_challenge\_authority\_v2\_20260918.py

builds V2 only and MUST NOT be used as final V3 nonlinear authority.

Implement current builders for all three gaps.

Each builder must have behavior tests, exact root/source-role binding, anti-placeholder checks, spillover checks and independent verifier review.

Do not hand-create JSON or use placeholder hashes to bypass these gaps.

After adding builders, update the current execution plan/checkpoint state and refresh the GPU preflight inventory if necessary.

## Final freeze boundary

Only after all current runtime receipts and current authority builders are complete:

bind exact current source hashes;

freeze MaskingQualificationRunContractV4;

freeze it BEFORE terminal masking-policy outcomes are inspected;

ensure the terminal execution role is authenticated FULL104 Level-4 stream, not calibration cache;

rebuild docs/agent/CURRENT\_WORK\_CHECKPOINT.json on the final committed GPU-worktree head;

validate it with scripts/agent/work\_checkpoint.py;

independently red-team the final package.

Only then may terminal masking begin.

Start at 5%.

If 5% fully qualifies, STOP. Do not inspect 10%.

If 5% explicitly fails, proceed to the next frozen burden.

Continue only until the first fully qualifying burden.

## After masking

A masking PASS does NOT authorize training.

Still required afterward:

healthy-current-teacher remaining-RNA necessity;

current measurement robustness;

production geometry;

geometry-specific memorization check;

runtime/environment/source provenance;

complete current authority graph;

explicit final training authority.

Training remains OFF until that entire chain closes.

## Permanent hard boundaries

TRAINING\_OFF

NO\_D\_SHARED\_OUTCOME\_EXECUTION\_OR\_INSPECTION

NO\_PATHOLOGY\_DEV\_SEALED\_OUTCOME\_ACCESS\_WHILE\_DESIGN\_OPEN

NO\_SMALLER\_OR\_HISTORICAL\_FULL104\_SUBSTITUTE

NO\_STAGE81\_CACHE\_AS\_FULL104

NO\_HISTORICAL\_T1\_AS\_HEALTHY\_TEACHER

NO\_DISCOVERY\_MATRIX\_AS\_FULL104

NO\_HISTORICAL\_TARGET\_LIST\_OR\_FOLD\_MAP\_IN\_CURRENT\_CALIBRATION

NO\_CALIBRATION\_CACHE\_AS\_TERMINAL\_INPUT

NO\_PLACEHOLDER\_SHA256\_AUTHORITY

NO\_FREE\_PASS\_STRING\_WITHOUT\_BOUND COMPUTED EVIDENCE

NO\_POST\_OUTCOME\_RETUNING

NO\_BURDEN\_ESCALATION\_AFTER\_FIRST\_FULL\_QUALIFICATION

NO\_REOPENING\_SETTLED\_AUDITS\_WITHOUT\_CHANGED\_INPUT

Do not reopen without changed input:

FULL104 lineage/substrate

K2 partition

VALUE\_ONLY\_256

base estimand

T0/T1/C2 chronology

QID/F1

Stage81A3 scope

Layer-2

target-identity shortcut discovery

Stage-A structural qualification

visibility ablation

same-cell thinning

streaming/reference parity

## Current truth at takeover

No target-panel count has been selected.

No nonlinear row cap has been selected.

No terminal masking outcome has been opened.

No production masking policy has been selected.

No final MaskingQualificationRunContractV4 instance exists.

Training is OFF.

Start by verifying the authority package and exact live GitHub state, then continue the open sequence above using iterative self-audit, red-team review, spillover checks and historical-context checks at every promotion boundary.