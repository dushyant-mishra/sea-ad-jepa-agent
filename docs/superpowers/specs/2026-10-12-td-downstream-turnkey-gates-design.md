# Target-Discovery Downstream Turnkey-Gates Design

Date: 2026-10-12
Status: DESIGN FROZEN FOR REVIEW — NO EXECUTION AUTHORITY
Branch: `science/td-target-tournament-scaffold-20261011`

## 1. Purpose

The target-discovery program is now substantially ahead in scientific decision logic but uneven in physical execution readiness. The objective of this design is to close the remaining downstream engineering gaps *before* upstream biological gates open, so that future progression does not pause for new executor design, contract invention, or qualification infrastructure.

The desired operational property is:

> once an upstream scientific gate is accepted, the next stage should require only a fresh stage-specific authorization plus execution against already-qualified bytes; it should not require new design, new science code, or retroactive qualification work.

This design is prospective and non-authorizing. It must not open any protected biological outcome, select a target, select a representation, authorize TD60, authorize Stage 4, authorize 500K, or authorize JEPA training.

## 2. Governing boundaries

The current hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

The following principles are immutable through this work:

1. Technical/custody PASS is not biological evidence.
2. Synthetic evidence may falsify or stress-test a candidate where prospectively valid, but synthetic PASS cannot establish human biological truth or rescue real FAIL / NOT_ESTIMABLE.
3. Biological replication is donor-primary; source/acquisition is an observation operator, not an independent biological replicate.
4. Measured zero remains distinct from structurally unmeasured.
5. Unsupported candidates abstain; no forced modality imputation is introduced.
6. No average-score rescue, best-loser rescue, or threshold relaxation is allowed.
7. Current target-convergence logic remains non-authorizing and may not manufacture a winner.
8. Existing G6/G7, corrected-replay, V79, representation, and runtime evidence is not rewritten.
9. Every future value-bearing stage receives fresh, stage-specific authority; predecessor authority is not recycled.
10. No infrastructure built under this design may consume an unopened scientific result during qualification.

## 3. Architectural choice

Use six independent **turnkey-gate modules**, all following the same four-layer pattern:

### Layer A — Frozen input contract

Each stage declares:
- exact predecessor authorities and hashes;
- exact allowed inputs;
- exact forbidden inputs;
- stage-specific candidate/target identity;
- support / missingness semantics;
- executable source identity;
- expected output namespace grammar;
- authority flags, all false by default.

The contract is machine-readable and prospectively frozen before any stage outcome is opened.

### Layer B — QUALIFY mode

A read-only or outcome-blind qualification path exercises the maximum physically meaningful portion of the stage without consuming its protected scientific endpoint.

Qualification must prove, where applicable:
- exact predecessor binding;
- exact file/schema compatibility;
- address and row identity;
- support semantics;
- allowed-input firewall;
- negative refusal cases;
- fresh namespace rules;
- deterministic receipt grammar;
- no protected value read;
- no training or downstream authority.

### Layer C — EXECUTE_ONCE mode

The value-bearing path:
- requires fresh stage-specific owner/runtime/operational authority;
- creates an immutable start marker before protected outcome-bearing reads;
- refuses reused authority, reused namespace, or stale predecessor evidence;
- records exact execution identities;
- preserves every post-marker failure;
- never converts a failure into a rerun without a successor authority process.

### Layer D — Evidence package + validator

Every stage emits a standardized evidence package containing:
- start marker;
- final receipt or preserved failure state;
- exact code and authority hashes;
- predecessor hashes;
- stdout/stderr digests;
- input/output inventory;
- before/after custody assertions;
- spent-authority identity;
- stage-local terminal;
- all downstream authority flags false unless a separate later decision explicitly changes them.

A separate validator must be able to adjudicate package integrity without rerunning the science.

## 4. Module 1 — Corrected relational replay launcher

### 4.1 Scientific scope

Execute the already-prefrozen corrected TD56 / TD57B / TD57C / TD59 replay only after G7 is externally accepted and corrected-replay authority is separately issued.

No scientific rule may be changed here. Existing frozen interpretation remains controlling:

- TD56 FAIL stops relational promotion.
- TD56 PASS + TD57B FAIL means donor-recurrent scale-free order is not confirmed.
- TD56 PASS + TD57B PASS + TD57C FAIL + TD59 PASS supports the historical-scale relational bracket.
- TD56 PASS + TD57B PASS + TD57C FAIL + TD59 FAIL preserves only a broad/global scale-free candidate.
- corrected TD57C PASS is a divergence and requires a new prospective locality experiment.
- source disagreement is not averaged away.
- NOT_ESTIMABLE is not biological PASS.

### 4.2 Required engineering

Build a corrected-replay stage controller that:
- consumes only externally accepted G7 evidence plus the frozen corrected-replay manifest/contracts;
- authenticates all replay inputs before value use;
- invokes the recovered exact TD56/TD57B/TD57C executors and the frozen admissible TD59 successor;
- preserves stage separation while producing one bundled replay evidence package;
- has QUALIFY and EXECUTE_ONCE paths;
- generates a machine-readable replay projection consumable by existing downstream routing;
- cannot authorize target selection, TD60, Stage4, or training.

### 4.3 Qualification target

Qualification must prove the controller can bind the exact frozen experiment lineage, select each correct executor, refuse altered historical identities, refuse stale G7 evidence, refuse unauthorized execution, and create no protected replay outcome.

## 5. Module 2 — Real target-tournament executor

### 5.1 Scientific scope

Physically evaluate the already-frozen target candidates:
- C1 `C1_SHARED_EMERGENT`
- C2 `C2_RELATIONAL_SHARED`
- C3 `C3_QUERY_MEASURED`
- C6 `C6_SHARED_QUERY_COMPOSITE`
- C4 `C4_STRUCTURED_COMPOSITE`
- C5 `C5_REGULATORY_SPECIALIST` as specialist-only

using the already-frozen real-data gates, falsifiers, donor-primary replication, source-replication requirements, support semantics, and candidate dependency lattice.

The executor must not redefine candidate biology. It operationalizes the existing tournament contract.

### 5.2 Mandatory falsifiers

The execution contract must preserve at minimum:
- constant/train-mean baseline;
- technical/operator-only baseline;
- address/support/operator shortcut baseline;
- matched wrong-cell;
- fine-neighborhood wrong-cell;
- q-count-only;
- q-address-only;
- query-agnostic;
- wrong-q;
- technical+q;
- q-excluded teacher;
- identity+support-only.

### 5.3 Required engineering

Build:
- one candidate registry bound to exact frozen candidate definitions;
- one stage-independent case ledger with donor-primary resampling identity;
- candidate-specific adapters, not a monolithic outcome-tuned scorer;
- full gate receipt with raw sufficient statistics plus thresholded status;
- a strict separation between measurement/support uncertainty and biological uncertainty;
- a complete candidate result bundle that can be fed directly into `td_target_tournament_routing_v4.py` and `td_target_convergence_v1.py`.

The executor must refuse execution if required real replay prerequisites are unresolved for a candidate that depends on them. C1/C3/C6 may remain independently testable where the frozen routing says relational failure does not eliminate them.

## 6. Module 3 — Synthetic target-candidate evaluator

### 6.1 Scientific scope

Evaluate target candidates against the already-realized, byte-audited V79 Q00–Q11 worlds only where the existing crosswalk says a claim is estimable.

This module is separate from the V79 statistical-model qualification executor. It answers candidate-level target questions, not whether the V79 generator/model itself is qualified.

### 6.2 Blinding and truth separation

The fit/evaluation side may consume only the prospectively allowed blinded realization surface. Controller truth remains unavailable until the candidate result object is frozen.

After candidate output freeze, the scoring side may combine it with controller truth only under the predeclared crosswalk.

### 6.3 Required engineering

Build:
- exact candidate-to-world adapters for all currently estimable claims;
- a blinded execution receipt keyed by opaque world IDs;
- post-freeze scoring against exact truth-manifest SHA and result SHA;
- complete-claim-set enforcement so claims cannot be cherry-picked;
- candidate-level evidence receipts compatible with `td_v79_synthetic_crosswalk_v1.py`;
- support for C6 extension rules already frozen in the target-discovery scaffold.

Synthetic outputs remain non-promoting on their own. Real FAIL / NOT_ESTIMABLE cannot be rescued by synthetic PASS.

## 7. Module 4 — Protected head-to-head and protected-confirmation executor

### 7.1 Scientific scope

The current target-convergence layer can adjudicate already-thresholded statuses and protected pairwise metadata, but it does not itself physically generate protected comparison or protected-confirmation evidence.

This module closes that gap.

### 7.2 Multi-survivor branch

If multiple foundation candidates survive:
- execute only prospectively frozen pairwise added-information / robustness tests;
- do not rank by average aggregate score;
- preserve incomparability when supported by evidence;
- permit a multi-component scientific conclusion only if prospectively defined and biologically justified, not by automatic concatenation.

### 7.3 Protected confirmation branch

For one frozen finalist:
- bind exact finalist identity before opening protected confirmation data;
- prohibit any candidate redesign or threshold change after finalist freeze;
- execute exactly one protected confirmation protocol;
- emit PASS / FAIL / NOT_ESTIMABLE plus raw evidence;
- PASS still does not auto-select the target; it produces `TARGET_CANDIDATE_CONFIRMED__OWNER_SELECTION_DECISION_REQUIRED__NO_TARGET_AUTHORITY`.

## 8. Module 5 — TD60 successor

### 8.1 Scientific scope

TD60 is learned-teacher relational continuity. It is not another target search, not a new locality sweep, and not permission to reuse historical u40/u205 as biological authority.

The successor must consume only a legitimately selected/authorized target and an eligible learned teacher representation under the current representation rules.

### 8.2 Required modernization

The historical TD60 prose/freeze is insufficient as a turnkey production executor. Build a successor that:
- binds the selected target protocol explicitly;
- binds the exact learned-teacher checkpoint/representation authority;
- preserves the frozen scale-free relational continuity objective where still scientifically applicable;
- defines donor-primary evaluation and source/operator nuisance reporting;
- separates target continuity failure from representation failure;
- refuses historical learned-state artifacts that are mechanics-only or not representation-qualified;
- runs QUALIFY without opening the protected biological endpoint;
- uses EXECUTE_ONCE with stage-specific authority.

No TD60 PASS may authorize Stage4 or training by itself.

## 9. Module 6 — Target/representation/dimension-to-training launch bridge

### 9.1 Purpose

The runtime mechanics are already comparatively mature: guarded optimizer-step semantics, q-safety execution proof, presentation-normalized EMA, typed checkpoint continuation, physical row/value provenance, and bounded synthetic mutation rehearsal exist.

The missing piece is a single immutable bridge from scientific selection to those runtime mechanics.

### 9.2 Inputs

The bridge may only be created after separate valid decisions exist for:
- selected target protocol;
- selected representation protocol;
- required numerical dimension family / production widths where applicable;
- biological support / measurement-domain policy;
- production observation-operator contract;
- training data scope;
- production EMA timescale authority;
- Stage-A / Stage4 scale authority.

### 9.3 Training launch manifest

The bridge produces one immutable training launch manifest binding:
- target identity and confirmation receipt;
- representation identity and qualification receipt;
- dimension/width authority;
- runtime source digest;
- optimizer and scaler contract;
- EMA contract;
- data substrate and sampling contract;
- q-safety proof identity;
- checkpoint lineage root;
- allowed stage and scale;
- TEST/Morabito/pathology boundaries;
- exact authority flags.

The launch bridge must refuse to infer missing scientific decisions from defaults, historical values, architecture capacity, or convenience.

## 10. Shared receipt grammar

All six modules should share a minimal common envelope:

```json
{
  "schema": "JEPA_TD_TURNKEY_GATE_RECEIPT_V1",
  "stage": "...",
  "mode": "QUALIFY | EXECUTE_ONCE",
  "code_identity": {},
  "predecessor_authorities": [],
  "stage_authority": null,
  "start_marker_sha256": null,
  "input_inventory": [],
  "output_inventory": [],
  "terminal": "...",
  "spent_authority": false,
  "target_selected": false,
  "representation_selected": false,
  "td60_authorized": false,
  "stage4_authorized": false,
  "training_authorized": false
}
```

Stage-local receipts may extend this envelope but may not weaken its authority semantics.

## 11. Cross-stage state machine

The intended future chain is:

1. accepted G7
2. corrected replay authorized and executed
3. corrected replay externally audited
4. real candidate tournament authorized and executed
5. synthetic candidate challenge executed where estimable
6. candidate routing / zero-one-many convergence
7. protected head-to-head if needed
8. protected confirmation of frozen finalist
9. explicit target-selection decision
10. representation qualification / selection
11. required FULL104 dimension closure / numerical selection where applicable
12. TD60 successor qualification + separately authorized execution if still required by the selected target/representation path
13. immutable target/representation/dimension-to-training launch manifest
14. separately authorized bounded real training stage
15. later scale promotion only under its own prospective authority

No stage may silently skip an unresolved predecessor.

## 12. Test strategy

Each module is implemented under RED→GREEN discipline with four test classes:

1. **Contract tests** — exact schemas, hashes, registries, dependency rules, authority defaults.
2. **Adversarial refusal tests** — stale authority, wrong predecessor, wrong code identity, altered candidate, reused namespace, forbidden truth leakage, wrong row/address, support corruption, duplicate IDs, partial evidence.
3. **Outcome-blind physical qualification tests** — exercise the real substrate as far as possible without opening the protected endpoint.
4. **Receipt roundtrip tests** — independent validator reproduces package integrity and stage-local terminal from frozen receipts.

Tests must not encode the expected biological winner.

## 13. What will be built now versus later

### Build and qualify now
- corrected-replay launcher and validator;
- real target-tournament execution framework and candidate adapters against synthetic/fixture data only;
- synthetic target-candidate evaluator against realized-world interfaces without opening target outcomes unless separately authorized;
- protected head-to-head / confirmation execution framework using fixtures;
- TD60 successor executor framework using fixtures / non-authoritative learned-state substitutes only;
- final scientific-selection-to-runtime launch-manifest builder and validator;
- common turnkey-gate receipt envelope and authority checks.

### Do not execute now
- corrected biological replay;
- real biological target tournament;
- synthetic candidate target outcome scoring where not separately authorized;
- protected confirmation;
- TD60 biological execution;
- target selection;
- representation selection;
- FULL104 numerical dimension run unless separately authorized in its own lane;
- Stage4 / 500K;
- JEPA real training.

## 14. Success criterion for this readiness program

This program is complete when every remaining downstream stage has:
- a frozen machine-readable contract;
- a qualified executable implementation;
- an outcome-blind QUALIFY path;
- a fail-closed EXECUTE_ONCE path;
- standardized evidence receipts and independent validator;
- explicit predecessor and authority bindings;
- no unresolved code or qualification work that would be discovered only after the upstream gate opens.

At that point, future scientific progression should be delayed only by evidence acquisition, external audit, or explicit owner authorization — not by missing pipeline engineering.

## 15. Non-authority statement

This design and any engineering performed under it create no biological result and no scientific winner. The current terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
