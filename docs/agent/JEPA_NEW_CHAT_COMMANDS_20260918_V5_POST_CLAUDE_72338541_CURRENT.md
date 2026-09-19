# JEPA V5 — exact takeover commands for post-Claude 72338541 state

Date: 2026-09-18

## 1. Verify GitHub state

PowerShell:

~~~powershell
$Repo = "D:\Jepa project"
$ScientificBranch = "impl/v5-full104-post-claude-binding-repair-20260918"
$ExpectedScientific = "72338541c3a161cf461dde5215e6841ee9704ee7"
$HandoffBranch = "handoff/jepa-v5-post-claude-72338541-20260918"

git -C $Repo fetch origin
git -C $Repo status --porcelain
git -C $Repo rev-parse "origin/$ScientificBranch"
git -C $Repo rev-parse "origin/$HandoffBranch"
~~~

If the scientific branch is not exactly `$ExpectedScientific`, STOP and classify the delta as `CHANGED_INPUT_REQUIRES_REQUALIFICATION`. Do not reset, clean, stash, rebase or overwrite a dirty worktree automatically.

Use the handoff branch only to read current docs. Use the scientific branch for implementation bytes.

## 2. Verify the handoff is docs-only relative to the scientific head

~~~powershell
git -C $Repo diff --name-only $ExpectedScientific "origin/$HandoffBranch"
~~~

Expected changed paths are documentation/handoff files only. Any `src/`, `tests/`, workflow, binary data or runtime artifact change is a STOP.

## 3. FULL104 physical inputs

~~~powershell
$L4 = "D:\Jepa project\outputs\full104_v014_20260826\03_phase2_state_derivation_v1\expression_level4"
$ExpectedL4 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
$ExpectedObs = "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"
$ExpectedRegistry = "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd"
~~~

Resolve the current observation-state and registry paths from current project authorities; do not use Stage81/T1/discovery substitutes.

Verify the Level-4 manifest hash before reading any block. Revalidate it after long runs.

## 4. What to execute first on the GPU machine

Do a non-terminal FULL104 shakedown before adding more architecture:

1. regenerate/read-only FULL104 census V2 from the real pass1 substrate;
2. verify 104 donors, 42 operators, source/fold coverage, 17,186 strict core and current eligibility counts;
3. stream all 8,915 blocks exactly once and record throughput/peak memory;
4. build the authenticated calibration-only cache in a new empty runtime directory;
5. run calibration-mode preflight;
6. scan that runtime directory for Stage81/T1/discovery/RIDGE8 historical ingress.

Do not run the target-panel sizing ladder yet. H3 must first resolve whether the panel is sized for the actual equivalence question rather than easy planted-shortcut detectability.

## 5. Scientific integration work

PR #26 is current. PRs #23/#24/#25 are parallel candidates, not inherited.

Create one explicit successor of PR #26 and integrate only justified changes after review. Required candidates to evaluate:

- PR #23 live checkpoint closure;
- PR #24 margin authority (mechanism useful; scientific 1/1000 rationale must be re-reviewed);
- PR #25 policy-receipt self-validation.

After any integration, run all four workflows at the exact new head with fail-on-skips and inspect logs.

## 6. Terminal boundary

Do not open 5% until at minimum:

- PR #26 G1/H1/H2 independently re-reviewed;
- global caller-derivable-field audit completed or bounded;
- H3 equivalence-power panel sizing resolved and frozen;
- G5 margin rationale/authority resolved and frozen;
- G2 policy-complexity materiality resolved;
- G4 signal-preservation criterion frozen;
- G3 capacity-matched/deep anti-shortcut gate specified;
- H4 fail-closed interpretations pre-registered;
- final source freeze + clean machine checkpoint + RunContract + terminal preflight complete.

Then terminal burdens are one invocation each:

`5% -> 10% -> 15% -> 20% -> 30% -> 50%`

Each higher rung requires exact proved-failed prior execution authority from the same RunContract. Stop at the first qualifier. Never inspect a higher rung after a lower pass.

Masking PASS does not authorize training.
