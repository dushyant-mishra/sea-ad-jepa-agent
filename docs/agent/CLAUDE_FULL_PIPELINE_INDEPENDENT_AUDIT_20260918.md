# Claude Full-Pipeline Independent Audit Mandate — 2026-09-18

## Scope

Claude is the independent red-team/audit lane for the **entire JEPA project**, not only the latest masking work.

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Implementation branch at handoff creation:
`impl/v5-full104-masking-redteam2-20260918`

Implementation SHA at handoff creation:
`91d50145d4573deb7fad8c599ebc5ed059a495c6`

PR: #20

Exact-head workflow observed before this handoff:
`35387164219` — SUCCESS, including the fail-on-skips gate.

**Do not trust these values as current. Re-fetch live heads and CI before using them.**

## Audit posture

Do not trust ChatGPT/Codex conclusions, previous Claude conclusions, green tests, handoff prose, or historical labels merely because they exist.

Do not wastefully rerun closed expensive work when inputs and role are unchanged. Classify every major component as:

- `ALREADY_AUDITED`
- `SUPERSEDED`
- `OPEN`
- `CHANGED_INPUT_REQUIRES_REQUALIFICATION`

For `ALREADY_AUDITED`, independently verify that the audit occurred, its inputs remain unchanged, its role remains the same, and later changes did not invalidate it.

Preserve dirty worktrees. Do not reset, clean, stash, rewrite history, or overwrite user changes.

## End-to-end audit

Audit the full dependency chain:

1. **Repository / governance / CI**
   - live branch and PR heads
   - scientific vs docs-only commits
   - exact-head CI
   - fail-on-skips
   - false-green / did-not-run failure modes
   - machine checkpoint / runtime provenance

2. **FULL104 data lineage**
   - 4,553,407 cells
   - 104 donors
   - 42 operators
   - 41,238 addresses
   - 17,186 common-core addresses where applicable
   - 8,915 Level-4 blocks
   - current manifests, registry, observation state, donor/source/operator identities
   - no subset/synthetic/fixture/Stage81/T1 substitution
   - physical closure vs metadata-only closure
   - no double normalization, row duplication/loss, zero/missing confusion, address remapping drift

3. **Representation / multiview lineage**
   - expression transforms
   - observation operator semantics
   - sketch/projection lineage
   - A/B or equivalent views
   - shared/private/observation subspaces
   - source/operator/QC/global-factor leakage
   - two-view address splitting must not be mistaken for removing cell-level technical effects

4. **Dimension authority**
   - D_shared, D_private, D_obs and related choices
   - dataset-first selection
   - held-donor evidence
   - technical leakage
   - subspace stability
   - hash/metric lineage
   - no TRAIN-cache or smaller-run promotion to FULL104

5. **Teacher/student/EMA architecture**
   - teacher input and target semantics
   - student input
   - stop-gradient boundaries
   - EMA direction
   - parameter ownership
   - mask interface
   - biological/state prediction rather than hidden-gene identity recovery
   - identity, address, target-membership, donor, source, operator, QC/depth, global-factor, visibility and same-cell technical shortcuts

6. **Historical T0/T1/QID/F1/Layer2/Stage81 work**
   - audit closures in context
   - do not reopen unless inputs or current dependencies changed
   - if current production silently depends on an unresolved historical estimand, escalate it

7. **Training-failure prevention**
   - exact-zero/subnormal gradients
   - no-op optimizer updates
   - collapse
   - checkpoint/resume provenance
   - mixed precision
   - skipped tests
   - target leakage and shortcut convergence
   - effective recurrence gates

8. **Masking qualification chain**
   Trace current FULL104 census/support/eligibility
   -> MaskingQualificationParametersAuthorityV2
   -> authenticated calibration-only cache
   -> target-panel ladder
   -> TargetPanelAuthorityV3
   -> current outer split
   -> PrecisionAuthorityV4
   -> nonlinear model-capacity authority
   -> nonlinear cap ladder
   -> evidence-budget template
   -> burden ladder
   -> RNG replay authority
   -> nonlinear challenge V3
   -> MaskingQualificationDesignAuthorityV2
   -> RunContractV4
   -> terminal evidence assembly
   -> one-rung terminal executor
   -> Decision V2
   -> ExecutionAuthorityV4.

9. **Accidental spillover**
   Search mechanically for unauthorized production ingress of:
   - Stage81/T1 artifacts
   - smaller-run matrices
   - `X_common6000`
   - discovery 800/2000/6000 universes
   - historical target lists/folds/seeds/burdens/target counts/nonlinear caps/policy winners
   - provisional 20260917 freeze artifacts
   - placeholder hashes
   - old GPU preflight
   - old terminal runner
   - stale authority versions
   - historical PASS/FAIL strings

10. **Intentional historical re-authorization**
    Independently verify every exact-byte historical ingress, especially:
    - `build_full104_masking_parameters_authority_v2_20260918.py`
    - `build_full104_nonlinear_capacity_model_authority_v1_20260918.py`

    Recompute their referenced SHA-256 values.

    Historical evidence may authorize only its explicitly frozen narrow role. It must not provide current FULL104 targets, folds, burden, target count, seed, nonlinear row cap, data, terminal result, policy authority, or training authority unless separately prospectively authorized.

11. **Target-panel calibration**
    Audit control-only ladder:
    `128 -> 256 -> 512 -> 1024`
    with exact replay and stop at the first qualifying rung.
    Terminal masking outcomes must not influence target count.

12. **Nonlinear capacity calibration**
    Audit control-only ladder:
    `64 -> 128 -> 256 -> 512 -> 1024`
    with exact replay and stop at the first qualifying cap.
    Historical nonlinear evidence may provide model shape only.

13. **Statistics / Monte Carlo / resampling**
    Audit:
    - target x donor geometry
    - donor/source balancing
    - held-donor evaluation
    - bootstrap / Monte Carlo implementation
    - seed derivation
    - CI and one-sided/two-sided bounds
    - null calibration
    - planted controls
    - paired estimands
    - source guardrails
    - target heterogeneity
    - nonlinear null
    - convergence / non-convergence handling
    - replicate counts
    - replay determinism

14. **Terminal evidence assembly**
    Hostile review of:
    `src/sea_ad_jepa/v5/masking_terminal_evidence_assembly_v1.py`
    and successors.

    Verify:
    - uniform-vs-policy is same target/donor/rung
    - real-vs-shuffled uses the same mask
    - null cannot be borrowed across policy arms
    - nonlinear actual/null use identical mask and current authority
    - target heterogeneity and source guardrails have intended weighting
    - effective targeting count has intended target x fold geometry
    - PrecisionAuthorityV4 is used lawfully
    - all current donors/targets are represented
    - no historical aggregation formula entered silently

    **Critical provenance test:** determine whether callers can supply arbitrary matrices plus unrelated `raw_*_sha256` values. Raw hashes must mechanically bind the actual evidence arrays/artifacts they identify. If not, STOP terminal execution and report the defect.

15. **One-rung terminal executor**
    It must:
    - consume only frozen current RunContractV4 + authenticated FULL104 Level-4 terminal input/current receipts
    - accept exactly one burden rung
    - never auto-escalate
    - derive evidence mechanically
    - bind raw evidence cryptographically
    - construct matrices itself
    - produce V2 decision + ExecutionAuthorityV4
    - reject calibration cache as terminal input
    - reject free PASS strings
    - never authorize training or protected outcomes

    If 5% fails, stop. Any 10% run requires a separate explicitly authorized invocation. If 5% passes, 10% stays unopened.

16. **CI/CD and regression infrastructure**
    Audit workflow triggers, exact-head execution, dependency install, test selection, path filters, workflow dispatch, stale-test detection, no-skip gates, branch/checkpoint provenance and reproducibility.

17. **Anti-cheat as a system**
    Attack combinations of leakage channels, not only individual channels:
    donor+source, source+operator, depth+detection, address+visibility, target membership+mask pattern, RNG+fold, technical state+global factor, teacher/student leakage, ordering effects.

18. **Training-authority boundary**
    Masking PASS alone must never authorize training.
    Verify remaining gates for healthy current teacher remaining-RNA necessity, measurement robustness, production geometry, geometry-specific memorization, runtime/source/environment provenance, and explicit final training authority.

## GPU / full-data lane

Only after prerequisite audit gates pass, use the GPU-resident FULL104 data for heavy control/calibration work:

1. build current parameters authority instance;
2. regenerate current real census V2 receipts from authenticated pass1;
3. build census authority;
4. build authenticated FULL104 calibration-only cache;
5. verify all 104 donors and all root/hash closure;
6. run target-panel ladder with replay;
7. freeze target panel / split / precision;
8. build nonlinear model-capacity authority;
9. run nonlinear cap ladder with replay;
10. freeze evidence-budget / burden / RNG / nonlinear / design authorities;
11. build RunContractV4;
12. rebuild machine-bound checkpoint;
13. terminal-mode preflight;
14. independently verify the frozen package.

Do **not** open terminal masking just because calibration/freeze succeeds.

Do **not** use calibration cache as terminal input.

Do **not** push giant FULL104 data to GitHub. Return compact authenticated receipts/hashes.

## Required deliverable

Produce a comprehensive end-to-end audit report with a master table:

`component | status | authoritative input | evidence | historical role | current risk | action`

For every defect include:
- severity
- classification
- exact commit
- file/line
- scientific consequence
- reproducible evidence
- whether prior conclusions are invalidated
- smallest defensible repair
- required tests
- whether calibration or terminal execution must STOP

Finish with the exact blockers remaining before:
1. terminal FULL104 masking;
2. final training authority.

Do not issue an overall PASS unless the entire dependency chain supports it.
