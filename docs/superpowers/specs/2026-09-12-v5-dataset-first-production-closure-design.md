# V5 Dataset-First Production Closure Design

Status: `DESIGN_APPROVED_IN_CHAT__IMPLEMENTATION_NOT_STARTED__NO_TRAINING_AUTHORITY`

Base branch at design creation: `repair/v5-qualified-target-guard-20260911 @ da8bd7dfe138fc4b36c11007d0a0165cd2365bcc`

Working branch: `planning/v5-dataset-first-production-closure-20260912`

## Goal

Close the V5 pre-execution production-qualification chain around the real FULL104 reader-fit dataset, deriving production geometry from authenticated data before allowing any bounded qualification run. Do not redesign the dataset around historical model geometry.

Core ordering:

`FULL104 data -> support/estimability -> scientific estimand -> production dimensions/schedule/packing -> runtime/anti-cheat qualification -> lawful base EMA teacher -> TD60 -> partial-evidence relational student qualification`

Training remains unauthorized throughout this design.

## Non-negotiable scientific rules

1. The dataset is the authority. Synthetic fixtures may test mechanics/fail-closed behavior only.
2. `FOUNDATION_TARGET_DISCOVERY_TD13_TD60_IS_NOT_T0_V18_V20_V21`.
3. T0 methodology may inform V5 gate design but T0 pathology values/targets/thresholds may not set V5 biology.
4. The 50K discovery archive and 4,726-row corrected TRAIN cache are not FULL104 substitutes.
5. Production dimensions, locality, masking/evidence rules, triplet budgets, update geometry, and CUDA geometry must be derived from authenticated real reader-fit data or predeclared risk/precision rules, never inherited from historical 96/160/224/320/512 values or checkpoint outcomes.
6. `NOT_ESTIMABLE`/`NOT_MEASURABLE` is not PASS.
7. A PASS receipt is not authority unless its exact bytes are hash-bound to the validated content and parent artifacts.
8. Historical C2/128x8 GPU evidence is supporting mechanics regression only; true production-geometry CUDA evidence is separately required.
9. Relational training remains inactive until the Target Discovery->V5 integration contract requirements close.
10. No protected validation/oracle/pathology access and no optimizer/training authority are introduced here.

## Existing architecture that should be preserved

### FULL104 binder

Production binder: `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`.

Required terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Expected production geometry:

- 4,553,407 reader-fit cells
- 104 donors
- 42 operators / matrices
- 8,915 Level-4 expression blocks
- 41,238 molecular addresses
- block manifest SHA-256 `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`

### Dataset-derived registry and support mass

`derive_v5_real_data_parameter_registry_v1.py` already derives population/support facts from authenticated metadata/calibration assets and explicitly leaves `D_shared`, `D_private`, `D_total`, and `D_obs` unresolved.

`derive_support_family_mass_v1.py` correctly derives common-core vs operator-native family mass under the donor-equal estimand rather than raw-cell frequency.

`derive_full_population_schedule_optimum_v3.py` derives a full-reader presentation schedule from reader-fit metadata plus prospectively supplied group-floor/cell-cap/ESS constraints. Compute packing must preserve the scientific target `DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1`.

### Pre-execution dependency graph

`preexecution_dependency_guard_v1.py` correctly binds:

`FULL104 expression -> dimensions -> proposal weights -> packing/restart -> production GPU`

and separately requires representation firewall, QC policy, historical GPU regression, and production-geometry GPU qualification.

`preexecution_qualification_bundle_v2.py` and `trainer_preexecution_contract_v4.py` keep this qualification-only and explicitly deny production training authority.

### Runtime target/optimizer guard

Current live runtime already contains the key repairs from earlier review:

- optimizer-resident deny-by-default guard;
- schedule cursor presented at optimizer-step time;
- stale/missing cursor burns authorization;
- skipped/uncompleted qualified calls are disarmed;
- direct optimizer.step after a qualified call remains blocked;
- actual target package root installed on modules must equal the qualified receipt root;
- AMP converges on the same optimizer hook.

These areas require exact-head replay/red-team, not redesign unless a new failing test proves a defect.

### Representation firewall

`representation_firewall_v2.py` uses allowlists for direct learned-state fields and freezes objective gradient destinations. This is preferable to a blacklist and should remain the routing authority unless a reviewed successor explicitly supersedes it.

### Target Discovery integration

The active scientific bridge remains the anchored relational target:

`q(i;j,k) = sign(d(i,j) - d(i,k))`

with direct cell-state cosine geometry.

The Target Discovery->V5 integration contract requires all of the following before relational activation:

- lawful full-reader exposure-defined learned-teacher checkpoint;
- TD60 PASS;
- partial-evidence relational predictability PASS;
- finite relational triplet budget frozen;
- common-core vs operator-native relation-view policy frozen;
- independent relational integration review PASS.

TD57C nearest-third failure stands. TD59 nearest-half is pilot evidence only, not production locality authority.

## Code audit findings that require action

### Finding A — stale 42-shard "full-reader" preflight can mislabel TRAIN-cache closure

`full_reader_relational_target_preflight_v1.py` can emit:

`PASS_FULL_READER_TARGET_QUALIFICATION_EXPRESSION_PREFLIGHT`

by binding 42 physical shards from the frozen `foundation-train-loader-v1` manifest.

Later authority explicitly establishes that those 42 corrected shards contain only 4,726 TRAIN rows and cannot represent the 4,553,407-cell reader-fit expression store. `V5_FULL_READER_EXPRESSION_RECOVERY_CORRECTION_20260910.md` and `V5_FULL_READER_EXPRESSION_LOCATION_RECOVERY_CONTRACT_V2.json` supersede this inference.

Design requirement:

- this preflight must be made fail-closed for production FULL104 authority;
- it may remain as TRAIN-cache/history diagnostics only;
- no current gate may consume its PASS terminal as FULL104 expression closure;
- tests must prove that authentic corrected TRAIN shards cannot satisfy any FULL104 production preflight.

### Finding B — intended full-stream dimension producer is missing

`DimensionExecutionFirewallV1` tests explicitly list:

`scripts/v5_anticheat/derive_full_stream_dimension_family_v1.py`

as the final-authority script, but that file does not exist on the live V5 branch.

The current code contains validators/firewalls for the desired receipt but no production implementation that derives the dimension family from FULL104.

Design requirement:

Implement a real FULL104-stream producer that derives:

- `D_shared` from held-donor, disjoint-view/common-core predictability with full-refit matched nulls and donor-resampled stability;
- `D_private` only after `D_shared` is frozen, as lawful incremental biological rank from operator-native evidence;
- `D_total = D_shared + D_private`;
- `D_obs` separately from lawful observation descriptors/held-operator reconstruction;
- contiguous-prefix selection and search-envelope expansion behavior;
- replicate counts from prospective precision/error budgets rather than historical constants;
- exact FULL104 expression receipt/parent hashes and no sampled-stratum cap.

Zero must remain a lawful dimension result.

### Finding C — artifact SHA binding is currently caller-shaped at some boundaries

`DimensionAuthorityV4` validates a FULL104-derived receipt while receiving `expression_closure_artifact_sha256` separately in its authority constructor. Unit tests demonstrate shape validation with arbitrary 64-hex digests rather than proving the digest corresponds to the exact validated receipt bytes.

Design requirement:

Production producer functions must:

1. canonicalize/serialize the validated receipt;
2. compute the SHA-256 from those exact bytes;
3. emit the receipt and artifact digest together;
4. bind parent artifact SHA values into the child artifact;
5. provide replay validators that recompute hashes from bytes rather than trusting caller-provided digest strings.

The same principle applies to dimension, proposal-weight, packing/restart, production-GPU, and gate-evidence artifacts.

### Finding D — production-geometry GPU validator exists; production runner is missing

`production_geometry_gpu_guard_v1.py` and its tests define the exact required receipt and correctly refuse historical 128x8 evidence as production geometry.

No `scripts/v5_anticheat/run_v5_production_geometry_gpu_qualification_v1.py` exists on the live branch.

Design requirement:

After FULL104, dimensions, scientific schedule/proposal weights, packing, firewall, and protected registry are frozen, implement a production-geometry CUDA qualification runner that:

- uses a real FULL104 reader batch;
- uses data-derived effective batch/microbatch/model width/model depth;
- executes the frozen successful-update mechanics chain;
- proves all protected 48 gradients live elementwise;
- proves parameter motion beyond decay;
- proves both Adam moments live;
- proves EMA update;
- proves atomic checkpoint/telemetry commit;
- emits a hash-bound execution receipt;
- never authorizes production training.

### Finding E — rejection-gate power logic is a validator, not executed evidence production

`rejection_gate_power_calibration_v3.py` has the correct two-sided semantic requirement: each rejection-capable gate must accept a minimally-valid frozen control and reject a minimally-invalid frozen control at exact adjudication geometry.

The unit tests build report dictionaries directly; they do not execute the seven gates to generate raw evidence.

Canonical gates:

- donor recurrence validation
- held-out biology validation
- QC/measurement confounding closure
- same-cell technical intervention
- shortcut superiority
- student representation collapse
- teacher representation collapse

Design requirement:

Build executable control producers/harnesses for each gate. Every report must be generated from the actual frozen gate implementation and exact sampling geometry, with raw outputs hashed before summary qualification. Caller-supplied booleans cannot be the only evidence of gate acceptance/rejection.

### Finding F — production FULL104 physical store is still the first substrate blocker

Current authoritative terminal remains:

`STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`

Historical expected root:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

The >30GB store is expected on the GPU laptop/attached drive. It should not be copied into ChatGPT. The only accepted closure is the V4 binder over the exact 8,915-block store plus metadata authority.

## Work-unit architecture

### Unit A — FULL104 data authority

Purpose: prove the exact production expression substrate and emit a canonical hash-bound closure artifact.

Deliverables:

- exact V4 binder replay on real 8,915-block store;
- canonical serialized closure artifact and SHA-256;
- negative-control tests proving TRAIN/50K/synthetic stores cannot close FULL104;
- deprecation/fail-closed repair for stale 42-shard full-reader preflight.

No dimensions are derived until Unit A closes.

### Unit B — dataset-derived production geometry

Purpose: derive scientific/representation geometry from Unit A rather than historical architecture constants.

Deliverables:

- `derive_full_stream_dimension_family_v1.py` plus tests;
- exact dimension artifact bound to Unit A bytes;
- support-family and proposal/schedule artifacts bound to the same FULL104 closure;
- finite relation-support tables and estimability summaries needed later for triplet-budget/locality qualification;
- explicit search expansion terminal when the supported dimension lies on a tested boundary.

### Unit C — runtime and anti-cheat qualification

Purpose: prove the exact derived geometry cannot bypass the authority chain or exploit known shortcuts.

Deliverables:

- replay/current-head optimizer/target guard tests;
- executable two-sided gate control harnesses;
- donor-held-out nuisance/identity/source/operator/depth/library/specimen attacks;
- same-cell technical interventions;
- duplicate/shared-view/lookup/technical-only/corrupted-biology controls;
- hash-bound raw evidence and replay validators.

### Unit D — production-geometry CUDA qualification

Purpose: prove the derived model/data geometry executes correctly on real hardware before any biological learning checkpoint is considered lawful.

Deliverables:

- production-geometry CUDA runner;
- exact protected-48 gradient/moment/motion/EMA/atomic-commit evidence;
- dependency-closed preexecution bundle V2;
- `BOUNDED_QUALIFICATION_ONLY` eligibility, never production-training authority.

### Unit E — lawful base teacher -> TD60 -> relational student

Purpose: only after Units A-D close, obtain a lawful exposure-defined base EMA teacher with relational training still inactive, then test whether learned geometry preserves the already-frozen Target Discovery biology.

Deliverables:

- lawful base checkpoint selected by prospective exposure clock, not outcome;
- TD60 global 24/24 + mesoscale 24/24 test using exact frozen TD57B/TD59 semantics;
- partial-evidence relational predictability qualification;
- finite triplet budget and common-core/native-support view policy freeze;
- independent integration review before relational activation.

## Testing policy

Authority-critical changes use TDD and must include negative controls.

For each work unit:

1. write a failing test that demonstrates the current gap;
2. run the targeted test and verify the expected failure;
3. implement the minimum correction/producer;
4. rerun targeted tests;
5. run the relevant existing V5 suites;
6. replay from clean tracked bytes / clean archive where practical;
7. mutation-test or explicit adversarially mutate authority-critical validation logic where the risk justifies it;
8. commit one auditable unit at a time.

Do not report a PASS based only on a schema validator or hand-authored receipt.

## Git/branch policy

- Source branch `repair/v5-qualified-target-guard-20260911` remains untouched.
- Work proceeds on `planning/v5-dataset-first-production-closure-20260912` or a reviewed successor created from it.
- Governance PR #16 remains separate until the scientific/engineering candidate is coherent.
- Avoid sibling repair-branch proliferation; prefer one successor lineage with small auditable commits.
- Re-fetch live heads before every integration/write that depends on another branch.

## Current intended order of implementation

1. Fail-close/deprecate the stale 42-shard full-reader preflight.
2. Add canonical artifact serialization/hash-binding utility used by new production producers.
3. Close FULL104 physical binding on the remote substrate and emit canonical closure artifact.
4. Implement `derive_full_stream_dimension_family_v1.py` against the canonical FULL104 reader.
5. Bind dimension -> proposal/schedule -> packing/restart artifacts to one design context and FULL104 root.
6. Build executable two-sided anti-cheat control producers.
7. Implement true production-geometry GPU runner and receipt producer.
8. Close dependency bundle for bounded qualification.
9. Obtain lawful base EMA teacher only after explicit bounded-qualification authority.
10. Run TD60, then partial-evidence student relational qualification.
11. Seek integrated independent review before any relational activation or production-training authority.

## Explicit non-goals

This design does not:

- solve T0 effect transport;
- open reader_validation/reader_oracle/pathology;
- re-run Target Discovery molecular search;
- retune TD57C/TD59 locality based on downstream outcomes;
- choose production dimensions from historical model widths;
- authorize training;
- merge governance PR #16 automatically.
