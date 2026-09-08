# JEPA Project — Authoritative New-Chat Handoff

Date: 2026-09-08
Role: external-review / project-continuity handoff
Canonical repository: dushyant-mishra/sea-ad-jepa-agent

## Start here

The repository has been consolidated. **main is the single canonical branch.**

Handoff snapshot base:
d8917ea3fedfd4b1de457b25e8e8be4cd0e6ea88

Fetch current main before doing anything. Do not reset main to the snapshot SHA;
the SHA is only a provenance anchor.

Read in this order:
1. docs/agent/CURRENT_AUTHORITY_INDEX.md
2. docs/agent/memory-os/NEXT_ALLOWED_ACTION.json
3. docs/agent/memory-os/ACTIVE_STATE.md
4. docs/agent/CURRENT_SUPERSESSION_MAP.md
5. docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json
6. docs/agent/JEPA_GLOBAL_BLOCKER_LEDGER_20260908.json
7. this handoff

The older docs/agent/T0_LANE_HANDOFF_20260908.md is preserved history and
contains stale lane-specific statements where it conflicts with the files above.

## Global state

Current gate:
STOP_JEPA_EXECUTION_AUTHORITIES_INCOMPLETE

This is an engineering/governance STOP, not a biological negative result.

Current absorbed source heads:
- T0 V20 implementation: 24b2c9ffc0ab2d63061c20af8829bcb86114b11a
- Teacher/Student V5: c7b1663cc4390843978b973986edfe58f93320a3
- V5 materialization: 71484ab99d276d7251836c109885d22ab4e7abb1
- Target Discovery: 26c3cfaba77bb8e5935e76473ab1fd5f90a562bf
- F1 real producer/replay: a884f558970479278bc21f3f2274dc24bee89758
- F1-B/C3 mechanics: c0eaf2acc0a5edc837fb2a48f726b9d626772f06
- D1 V2: c13c06c103a588fc95bb93174730bf26dd613884
- population/holdout registry: 14c2d586239aa5af15ed7cd70fdfb196d1c99f5f
- healthy-teacher base: 26e1c27d3578b794a1d522061df6d57ff435a688

## Branch consolidation and cleanup

Branch consolidation and pruning are complete:
- remote branch refs: **1**;
- canonical and only branch: **main**;
- 57 verified non-main refs were deleted by guarded workflow run `34284674854`;
- dry-run preflight PASS;
- deletion PASS;
- final "only main remains" verification PASS;
- tags, commit objects, package roots and immutable artifacts were preserved.

Audit:
- `docs/agent/JEPA_BRANCH_CONSOLIDATION_20260908.json`
- `docs/agent/JEPA_BRANCH_PRUNE_RESULT_20260908.json`
- `docs/agent/JEPA_SAFE_BRANCH_DELETE_LIST_20260908.json`

## P0 T0

V18/V20 science is accepted. Real T0 is not authorized.

Accepted V20 anchors:
- review ZIP a069cad258d278bf8d97e20ba1317ccc62b93265e7f93208a2ae1a4848561947
- package root 896dce257b8ed7330cfe9ac9a561e6d87090903485236dbf37f389d6432cb9e7
- V20 contract b8e5a38f9a158d0436d38e6846a51692f9a949580c899768c7d7507ab8646f62
- implementation manifest 1f55741e83bf1b504c052975649ec3a8978428b311251c9b0bd5271cf20c6b9d
- active-test manifest 99b9aeacea525ff06d6ab6d64aaed2fd74167795c2da21c02ef912f867fb0d6b
- V18 contract 0851b47d2351ded1be35a772bb9d7c05ed57d4bbbe551d81c7845a87ace85050

Frozen alphas:
- state primary .025
- sensitivity directional .05
- tail primary .02
- negative .005

Frozen IMMUNE_FRACTION successor formula:
IMMUNE_FRACTION(d) =
immune_n_donor(d) / total_op31_reader_fit_n_donor(d)

Geometry:
- 46 donors
- numerator total 20,804
- denominator total 638,150

Current three hard T0 STOPs:

1. B2 logical-root chain:
   logical authority must bind population closure and every execution-used
   identity/path, with stored == recomputed == externally expected.

2. Raw H5AD authenticity:
   source_library must be proven from the exact authenticated frozen MTG H5AD
   layers/UMIs row, not caller-supplied values plus provenance labels.

3. Age/sex candidate parent:
   the candidate donor universe must be derived from authenticated membership or
   verified against an externally frozen donor-set identity.

Until externally closed:
- production B2 forbidden
- donor-role gate shut
- numeric confirmation AT8 closed
- real_execution_ready=False

External red tests already exist in consolidated history:
- tests/v4/test_t0_b2_logical_chain_external_red_v2.py
- tests/v4/test_t0_b2_raw_source_external_red_v1.py
- tests/v4/test_t0_age_sex_external_parent_red_v1.py

After repair: replay reds, run all explicit T0 suites, external review, then
technical-completeness -> eligible donors -> deterministic roles -> stagewise
estimability -> discovery fit/qualification -> freeze -> one-shot confirmation.

## P0 Teacher/Student V5

Current continuation source:
028989a5f1504e4d6403a44e7c90d37172c54150

Materialization:
71484ab99d276d7251836c109885d22ab4e7abb1

Prototype root:
9684f4c2b7eff1da863ae50124c6aad49d25f137a84898e05e98d2ae1f0c67ad

Evidence:
- V5 active suite 66/66 PASS
- V4 regression 98/98 PASS

Frozen prospectively:
- scientific target V2
- relational proposal V2
- base proposal V3 with exact p/q correction
- presentation horizon V1: exactly 4,553,407 presentations, no automatic extension
- prospectively frozen repeat/group-coverage/ESS/importance-conditioning constraints
- donor-primary objective direction

Still pending:
- support-aware evidence/view/block policy
- finite relational triplet budget
- update size / token budget / microbatch execution geometry
- EMA half-life in exposure units
- learned-teacher biological checkpoint milestone within the frozen horizon
- optimized GPU Philox parity
- hardware packing calibration
- one integrated trainer binding
- mechanics qualification
- external V5 review

No training, optimizer updates, production checkpoints, EMA advancement or TD60.

Scientific target remains DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1. The frozen base proposal V3 is a separately derived convex proposal selected under the frozen coverage/conditioning constraints, with exact p/q importance correction mandatory; proposal mass does not redefine scientific mass.

## Mechanics clock vs biology clock

Historical 3,292-cell u40/u205 is mechanics evidence only.

On 4,553,407 reader-fit cells, u40 gives 5,120 presentations, about 0.1124% of
one cell inventory.

A Q40-style run may prove mechanics, but a decision-bearing learned teacher must
be defined prospectively in full-reader exposure/coverage units.

TD60 must consume that exposure-defined teacher, not historical u40 as biology
clock.

## F1-B/C3

c0eaf2acc0a5edc837fb2a48f726b9d626772f06 is attack-hardened mechanics
evidence, not the final trainer.

Before mechanics qualification:
- prospectively freeze movement-vs-decay criterion/tolerance; do not inherit the
  unreviewed hard-coded 2x rule;
- freeze exact mandatory predictor registry;
- bind one exact end-to-end data/mask/loss/update/checkpoint trainer.

## Target Discovery

Do not restart fixed-coordinate target search.

- TD57B: 24/24 PASS
- TD59 nearest-half mesoscale: 24/24 PASS
- TD57C nearest-third: failed in HVS and remains closed

Next biological question is learned-teacher relational continuity. TD60 waits
for lawful full-reader teacher.

## F1 real

a884f558970479278bc21f3f2274dc24bee89758 is available for parallel review,
but real F1 biological sweep still needs explicit execution authorization.

## D1 V2

c13c06c103a588fc95bb93174730bf26dd613884 contains the future-safe readout
resolver, teacher-state archive, incremental resampling, atlas, score archive,
sparse reader and molecular sufficient store.

Real D1 waits for:
- lawful qualified full-reader teacher
- frozen canonical readout contract
- teacher qualification authority
- final independent closure

Terminal posture: WAIT_HEALTHY_TRAINED_TEACHER.

## Protected populations

reader_validation, reader_oracle, foundation development/sealed, external
holdout and pathology remain closed except through exact frozen release
authorities.

## Immediate work order

Parallel Track A — T0:
1. close the three STOPs;
2. red->green without gate weakening;
3. full T0 suites;
4. external review;
5. no production B2 before acceptance.

Parallel Track B — V5:
1. work only from main/current V2 surface;
2. finish prospective proposal/evidence/horizon/EMA authorities;
3. GPU RNG parity;
4. hardware calibration;
5. integrated trainer;
6. external review;
7. mechanics qualification only after explicit authority.

Track C — hygiene:
dry-run verified branch cleanup and delete refs only through the guarded script.

Parallel nonblocking:
F1 review and D1 readout/qualification design may continue pathology-blind.

## Working discipline

- fetch current main before every write batch;
- reproduce defect before repair;
- tests are claims to attack;
- NOT_MEASURABLE is not PASS;
- skip is not run;
- verify exact diffs and test counts;
- never invent thresholds;
- docs are not implementation;
- authority failure is STOP, not donor exclusion;
- never weaken a gate to make tests green;
- no numeric confirmation pathology before lawful unlock.

## Local handoff package

The portable chat-local handoff package has now been materialized and verified:

- filename: `JEPA_COMPLETE_CHAT_HANDOFF_20260908.zip`
- bytes: `76,699,663`
- ZIP SHA-256: `50c6d06f55f7c54e4ddd2e52444428e2eaa4a94c225155178db377c54631a692`
- package-manifest root SHA-256: `9c4be64ba15c58360ab9a1e2fa71ba88637d24467031011389bd539f0b72ccc7`
- top-level chat artifacts copied: `26`
- package manifest payload rows: `30`
- ZIP CRC: PASS
- manifest mismatches: `0`

It contains:
- this chat's detailed handoff/state copies;
- current T0 external-review/self-audit packages;
- T0 positive-path V2 and upstream-interface specs;
- availability V1/V2/V3 packages and V6 code-preacceptance note;
- external B1/B2 attack/spec/oracle files;
- chat-uploaded pasted context and WSL execution issue;
- `checkpoints.zip`, `expression.zip`, and the NPZ data artifact.

Large immutable inputs remain separate to avoid duplicating more than 1 GB:
- Foundation calibration bundle SHA-256
  `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`;
- 41K discovery-expression combined archive SHA-256
  `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`;
- T1 u0200 checkpoint ZIP SHA-256
  `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`.

Exact chat-local binding:
`docs/agent/JEPA_CHAT_LOCAL_ARTIFACT_BINDING_20260908.json`.

Successor instruction:
Work from main only. Read the current authority index/next-action state first.
Close T0's three implementation STOPs and V5's pre-execution gaps in parallel.
Do not run real T0, training, TD60, D1 or protected releases until their exact
authorities exist and pass independent review.

