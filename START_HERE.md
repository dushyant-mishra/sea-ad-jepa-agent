# START HERE — JEPA PROJECT

Date: 2026-09-11
Status: `CURRENT_TARGET_DISCOVERY_TO_V5_INTEGRATED_EXTERNAL_REVIEW__NO_TRAINING_AUTHORITY`

**The goal is not to make V5 train successfully. The goal is to make it impossible for V5 to receive an unqualified biological target or obtain good training metrics through a shortcut, and to make every authority transition independently auditable.**

## Read first

Use `main` for project-current governance/startup context once the current governance lane is promoted. Until then, the active governance lane carries the prospective handoff corrections. Read in this order:

1. `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
2. `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260911_TARGET_DISCOVERY_V5_INTEGRATED_CURRENT.md`
3. `docs/agent/JEPA_REVIEW_EVIDENCE_PROMOTION_FAILURE_CONTRACT_20260911.md`
4. `docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260911_CURRENT.json`
5. current `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md` on the live V21/review branch
6. `docs/agent/JEPA_RUNTIME_ASSET_STATUS_20260910_CURRENT.json`
7. `docs/agent/JEPA_FORMULAS_AND_AUTHORITY_LEDGER_20260909_FINAL_R4.md`
8. `docs/agent/JEPA_HEAVY_ASSET_REFERENCE_20260909_FINAL_R4.md`
9. `docs/agent/CURRENT_AUTHORITY_INDEX.md`
10. `docs/agent/CURRENT_SUPERSESSION_MAP.md`

The earlier `JEPA_NEW_CHAT_HANDOFF_20260911_T0_V21_EXTERNAL_REVIEW_V5_CURRENT.md` remains useful historical context but is superseded for startup by the integrated target-discovery→V5 handoff.

Before writing, executing, reviewing, or committing, re-fetch live heads for at least:

- `main`
- `governance/integrated-target-discovery-v5-handoff-20260911`
- `t0/v20-pathology-blind-materialization-20260908`
- `t0/v21-prospective-design-20260910`
- `review/t0-v20-replay-equivalence-20260910`
- `planning/v5-full-population-cheat-proofing-20260909`
- active repair lanes including `fix/f1-review-closeout-20260911`

Re-fetch again before committing a substantial batch. Branch names do not confer scientific authority.

## Mandatory evidence labels

Every material result must be labeled at the point it is reported as exactly one of:

```text
PRODUCER_CLAIM
SOURCE_CODE_CONFIRMED
REVIEWER_REPRODUCED
REAL_DATA_EVIDENCE
NOT_YET_VERIFIED
```

Do not upgrade a producer-reported test count, mutation result, power calibration, nested-permutation claim, or provenance statement merely because the source code appears plausible.

## Exact blocker-closure rule

A blocker closes only through:

```text
contract
→ implementation
→ failing adversarial/regression test
→ repair
→ focused tests
→ surrounding tests
→ mutation/adversarial checks
→ provenance verification
→ independent reread
→ closure verdict
```

"Tests pass" alone is never sufficient scientific closure.

## Integrated production-review boundary

For production authority, target discovery and V5 are one scientific chain:

`raw SEA-AD substrate → discovery population/masks → target discovery → target statistical qualification/freeze → teacher target → V5 student/teacher training → downstream evaluation`

A V5 anti-cheat review alone is incomplete. A technically strong V5 model can still learn a circular, confounded or leakage-derived target. Conversely, a valid target can still fail if V5 exploits identity, technical or same-cell shortcuts.

Current target-discovery status:

`IN_PROGRESS__3b5933f6_PRODUCER_REPAIR_CANDIDATE_REQUIRES_INDEPENDENT_REREVIEW`

Current V5 verdict at `1de20b1c222c7fb27fcef5ec1a4b798d5b26a534`:

`MAJOR_REVISION_NO_GO_FOR_PRODUCTION_TRAINING`

Training remains OFF.

## Current high-priority review candidate

`review/t0-v20-replay-equivalence-20260910 @ 3b5933f6be45c2ec5589ddd4f200e9ff5eb49f46`

Parent:

`a89f4c3f6f65b14bc6ac55c11dc173676cdad140`

The producing lane claims repairs to six prior V21 blockers, `97 tests, 0 skipped`, and a `34 caught / 3 unreachable / 0 survived` mutation audit. These remain `PRODUCER_CLAIM` until independently reviewed/reproduced. First technical priority is exact diff/source/test/mutation/provenance review of this candidate. Do not assume the commit message is closure evidence.

## Current project boundary

Authenticated intended production population:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / matrices
- 41,238 molecular addresses
- 17,186 common measured-core addresses

Synthetic data may be used for unit/mechanics tests only. It may not set production biology, dimensions, schedules, thresholds or training authority.

## T0 / target discovery

Frozen V20:
`t0/v20-pathology-blind-materialization-20260908 @ d5d67e21398da92e39095afd864b4fb9ebe3da02`

V20 is immutable:

- broad state: `BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL`
- rare tail: `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`
- training unauthorized

V21 design branch observed:
`t0/v21-prospective-design-20260910 @ 11e76d36ace556ac48cdd2992995e63c1e35df18`

Status: `DRAFT_FOR_REVIEW_NOT_FROZEN`.

No fresh AT8 value has been opened, no protected partition has been opened, estimator selection has not run, the decision-capable power gate has not run, and V21 has not executed.

The prospective donor structure remains:

- 28 discovery donors for method/estimator/ridge/power choices;
- 18 spent historical-validation/development donors for development/internal sensitivity only;
- 12 fresh `reader_validation` donors for one single-shot T1 confirmation only after a passing power gate and complete freeze;
- 10 `reader_oracle` donors sealed as final reserve.

Standing rule:
`IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`

Do **not** run S0–S4 selection until the executable/adversarial review and the missing measurement layer close.

## Formal promotion ladder

```text
mechanics-valid
→ provenance-valid
→ statistically-valid
→ biology-qualified
→ frozen target
→ V5-bound target
→ anti-cheat qualified
→ FULL104-qualified
→ production training authorized
```

Passing one level creates no authority at the next level.

## Frozen failure rule

Do not improvise rescue procedures after observing failure. No admissible S0–S4 candidate, ridge instability, power below 80%, inconsistent effect direction, unrecoverable FULL104, target-binding failure, provenance mismatch, or successful anti-cheat attack remains a STOP under the predeclared contract. Any successor rescue design must be prospective and must not consume protected evidence to choose the rescue.

## Negative controls and checkpoint lineage

Negative controls are first-class immutable artifacts: preserve inputs, generator/configuration, code identity, raw outputs, verdict, and hashes/package root.

Every future V5 checkpoint must resolve the chain:

`frozen target package root → teacher-target digest → pre-execution receipt → exact trainer/code head → training-run identity → checkpoint → downstream evaluation`.

A checkpoint without that lineage is not scientifically attributable.

## V5 current blockers

The current V5 review requires at minimum:

- asymmetric-zero cosine repair and numerical edge tests;
- executable rejection-power gate over hash-bound controls, not report assertions;
- optimizer non-bypassability before even one `optimizer.step()`;
- donor-held-out nuisance-recovery attacks;
- deliberate identity/same-cell/shared-view/lookup/duplicate/technical-only/corrupted-biology attacks;
- exact target-discovery/freeze→V5 target binding;
- exact-head qualification evidence.

The corrected TRAIN cache closes only its own 4,726-row byte-binding claim. It is not FULL104.

Current FULL104 expression blocker:
`STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`

Required closure:
`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Production dimensions remain unresolved; historical 5/96/160/224/320/512 are not production authority.

## Runtime / reproduction boundary

Major discovery/calibration/checkpoint assets under `/mnt/data` are documented in the runtime-asset and heavy-asset ledgers.

`/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` remains `PROVENANCE_MISMATCH_DO_NOT_USE`.

In a preceding review environment, direct container→GitHub networking failed. Some review work therefore used the GitHub connector plus small locally reconstructed adversarial probes. That is not the same as a clean-checkout exact-head reproduction. If a proper checkout becomes possible, reproduce claimed suites there before upgrading evidence to `REVIEWER_REPRODUCED`.

## Permanent rules

A decreasing loss, passing unit test/CI, branch name, smoke test, design-document closure or mechanically healthy checkpoint is not biological/training authority.

Target discovery must be independently qualified and frozen before V5 can claim a production teacher target. V5 must then be shown unable to bypass that frozen target lineage or its anti-cheat gates.

The authority index and supersession map must agree with this startup order after `3b5933f6` review and after any durable repair branch is promoted.

**Training remains OFF** until exact production expression identity, target-discovery qualification, prospective anti-cheat/QC/power gates, donor-level evidence, production dimensions, production-geometry GPU qualification, bounded qualification, postqualification and a fresh integrated independent review all close.

**Do not optimize for reaching training quickly. Optimize for reaching a state where, if training succeeds, we can defend why the signal is biological, why it was discovered without circularity, why the student could not cheat, and exactly which immutable data/code/target lineage produced every checkpoint.**
