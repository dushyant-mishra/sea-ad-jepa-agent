# JEPA shared qualification pipeline design — 2026-10-06

Status: `DESIGN_FROZEN_FOR_REVIEW__NO_EXECUTION_AUTHORITY__TRAINING_OFF`

## Purpose

Define one qualification architecture that can be exercised first with V77/S127 synthetic worlds (where planted truth is available) and later with authenticated real RNA, without creating a separate synthetic trainer or allowing runtime mechanics to choose scientific meaning.

Organizing principle:

> Does the qualification pipeline give the right answers when we know the truth?

The synthetic world is therefore an instrument for validating the same qualification machinery intended for real data. Synthetic success does not select a biological target/representation and does not confer biological validation.

## Controlling authorities and lane roles

1. **PR #220 / merged V3 governance on main** remains the current scientific/prefreeze authority. It defines representation-family neutrality, observation-operator semantics, q-leakage and shortcut boundaries, evidence-vs-depth separation, transport/OOD axes, claim ladder, external-evidence rules, and unresolved estimand/threshold choices. It does not authorize Stage A or training.
2. **Real-data GPT lane** extends and refines the scientific qualification contracts for future real-data execution. Runtime must consume those contracts and must not preselect unresolved science.
3. **Claude/Macha (same local GPU agent)** owns V77/S127 synthetic/instrument work and local runtime/GPU qualification.
4. **PR #221 / PR #222 convergence** supplies the single non-authorizing runtime substrate. Neither donor PR is independently canonical.

## Architectural decomposition

The pipeline has four distinct layers:

### Layer A — Scientific qualification protocol

Machine-readable experiment contract derived from, and cryptographically bound to, the exact approved V3 governance state plus later approved successors.

It defines what is being tested, not how optimizer mutation is implemented.

### Layer B — Dataset adapter

Either:

- `RealQualificationAdapter`, for authenticated real RNA; or
- `SyntheticQualificationAdapter`, for V77/S127.

Both produce the same `QualificationBatch` schema.

The synthetic adapter additionally emits a physically separate `SyntheticOracleTruth` object.

### Layer C — Shared qualification pipeline

Common preprocessing, visibility/firewall enforcement, q-safety, observation-operator handling, representation extraction, target/evidence construction, diagnostics, and evaluation.

### Layer D — Optional mutation substrate

A bounded, explicitly enabled rehearsal path routed through the one converged #221/#222 successor runtime.

This layer is optional. Zero-update scientific qualification must not require optimizer/EMA mutation.

## QualificationBatch

`QualificationBatch` is the shared boundary between data adapters and the qualification pipeline.

It must not be a flat bag of tensors/metadata. Fields are grouped by visibility class and machine-enforced.

### Visibility classes

Every field must carry exactly one visibility designation:

- `MODEL_VISIBLE` — may enter encoder/predictor model input directly.
- `PREPROCESSING_VISIBLE` — may be used by lawful preprocessing/normalization/mask construction but must not automatically become model input.
- `LAWFUL_OPERATOR_CONTEXT` — observation-process descriptors permitted by the frozen observation-operator contract; may enter only through the explicit operator interface.
- `SPLIT_ONLY` — may be used to form TRAIN/inner-TRAIN/held-donor/study/operator splits, never as model input.
- `READOUT_ONLY` — may be used by frozen diagnostic evaluation/readout logic only.
- `PROVENANCE_ONLY` — identity/digest/source metadata used only for audit and reproducibility.
- `ORACLE_ONLY` — synthetic planted truth; must never enter normal preprocessing, model input, target construction unless explicitly declared as an oracle-only post hoc comparison, optimizer, EMA, or checkpoint model state.

Unknown visibility classes fail closed.

### Logical groups

The shared batch should conceptually contain:

1. `model_inputs`
   - canonical gene/address IDs;
   - permitted expression/count values;
   - measurement mask;
   - hidden-target/query mask where model-visible representation of masking is lawful.

2. `preprocessing_context`
   - only fields explicitly permitted for q-safe normalization/mask construction;
   - must exclude query descendants that would leak the hidden answer.

3. `lawful_operator_context`
   - authenticated assay/platform/chemistry/vocabulary/depth/detection/count-split/acquisition descriptors permitted by PR #220 or a later successor.

4. `evaluation_strata`
   - donor/source/study/operator/technology identities and labels used for splits, stratification, transport/OOD analysis, and estimand aggregation;
   - default visibility `SPLIT_ONLY` or `READOUT_ONLY`, not model-visible.

5. `provenance`
   - dataset identity, file/artifact digests, registry/order/reader/tokenizer bindings, adapter version, protocol digest.

6. `target/evidence specification references`
   - references to the external `QualificationProtocol`, not silent embedded winner choices.

## SyntheticOracleTruth

Synthetic planted truth is stored in a separate object and separate access path.

Candidate fields include:

- latent biological state;
- `z_reg_private`;
- B3 arm membership;
- B6 planted information level;
- planted observation/operator effects;
- planted nuisance variables;
- recoverable vs intentionally unrecoverable truth;
- generator/observer realization identity.

Hard rule: normal preprocessing/model/runtime code must not accept a `SyntheticOracleTruth` object as an argument.

Oracle access is restricted to dedicated post-prediction evaluation functions.

Changing oracle-only fields must not change model-visible input unless the synthetic generative process explicitly changes the observed data through a declared causal path.

## QualificationProtocol

PR #220 remains controlling governance, but its machine state is not sufficient by itself as an executable synthetic/real protocol. A successor machine-readable `QualificationProtocol` is required.

It must bind the exact governance digest and explicitly declare execution semantics that currently live partly in prose.

At minimum it must contain:

- governance digest/version;
- candidate representation family;
- target/evidence construction identifier;
- q-safety policy identifier;
- observation-operator descriptor policy;
- biological-evidence perturbation operator;
- measurement-depth perturbation operator;
- split/resampling protocol;
- representation-stability protocol;
- transport/OOD axes being tested;
- diagnostic-readout firewall;
- estimand/evaluation aggregation spec or explicit `UNSET`;
- numeric decision margins or explicit `UNSET`;
- mutation mode (`ZERO_UPDATE` or separately authorized `BOUNDED_MUTATION_REHEARSAL`);
- checkpoint/diagnostic ladder for bounded mutation rehearsals;
- claim ceiling.

Unresolved scientific choices must remain explicit unresolved fields. The synthetic harness must not silently choose them and then imply they were approved for real-data use.

## q-safety contract

The shared real/synthetic path must implement one transitive q-safety firewall.

Removing q from visible tokens is insufficient.

The pipeline must prove the hidden/query value cannot leak through:

- normalization denominator;
- library-size summary;
- detected-feature count/summary;
- QC-derived variables;
- support/missingness summaries;
- mask construction;
- query-dependent preprocessing;
- target/teacher pre-context;
- any deterministic descendant channel.

The synthetic world should include impossible-to-lawfully-recover oracle variables specifically to test these paths.

A machine-readable q-safety policy is required before synthetic qualification is treated as evidence about the future real-data pipeline.

## Representation-family neutrality

The shared pipeline must support all four current candidate families without preselecting a winner:

- `GLOBAL_CELL_STATE`
- `QUERY_LOCAL_STATE`
- `PROGRAM_STATE`
- `STRUCTURED_COMBINED_STATE`

V77 may test whether the qualification procedure behaves sensibly for each family, including shortcut sensitivity, planted-truth recovery, stability behavior, evidence response, depth response, and operator leakage.

V77 cannot establish which family is biologically correct for human brain.

No special incumbent status is given to `cell_state` or to width 160.

## Biological-evidence vs measurement-depth operators

These remain separate axes.

- Biological-evidence perturbation changes lawful information support/context.
- Measurement-depth perturbation holds the information universe fixed and thins count realization.

Exact fractions remain protocol fields and may remain `UNSET_REQUIRES_APPROVAL` for future real-data qualification.

Synthetic pipeline-validity tests may use prospectively frozen synthetic-only schedules, but those schedules must be labeled synthetic-test parameters and must not silently become real-data decision thresholds.

## Estimand separation

Estimand belongs primarily to experiment/evaluation aggregation, not model visibility.

The model batch may carry precomputed scientific weights only when the protocol explicitly requires them, but:

- the selected estimand remains part of the `QualificationProtocol`;
- donor/source/study identities remain non-model-visible unless separately authorized as lawful operator context;
- changing the evaluation estimand must not silently change encoder inputs;
- if the real-data estimand is unresolved, synthetic qualification must either report multiple predeclared candidate estimands or remain non-deciding on estimand-dependent conclusions.

## Two execution modes

### Mode 1 — `ZERO_UPDATE_QUALIFICATION`

Default scientific qualification mode.

Permits:

- adapter execution;
- q-safe preprocessing;
- target/evidence construction;
- frozen representation extraction;
- forward inference;
- frozen diagnostic readouts;
- stability/uncertainty/transport/OOD metrics;
- synthetic oracle comparison;
- receipts/provenance.

Requires:

- encoder optimizer updates = 0;
- predictor/encoder training updates = 0 except a separately allowed diagnostic readout that is not JEPA training;
- EMA updates = 0.

### Mode 2 — `BOUNDED_MUTATION_REHEARSAL`

Optional mechanics/anti-cheat mode, only after a separate narrow authority explicitly permits it.

Routes through the single converged runtime:

`backward -> unscale/no-AMP equivalent -> gradient validation -> guarded optimizer/scaler transition -> proven completion -> one-shot EMA -> persisted checkpoint/restart`

Synthetic mutation success does not authorize real-data training.

## Common pipeline vs oracle-specific diagnostics

Both real and synthetic adapters must feed the same common qualification pipeline.

Common diagnostics include:

- q-safety;
- identity/address shortcut controls;
- observation-operator residual imprint;
- representation-family extraction;
- evidence-vs-depth convergence;
- stability;
- transport/OOD reporting;
- estimand-aware aggregation;
- restart/mechanics diagnostics where mutation mode is enabled.

Synthetic-only oracle diagnostics include:

- impossible private-latent recovery;
- planted recoverable/unrecoverable truth;
- B3 arm behavior;
- B6 ladder monotonicity/sensitivity;
- known nuisance vs biology separation;
- generator/observer truth comparisons.

## Pipeline-validity vs realism/calibration tests

Two synthetic evidence classes must remain separate.

### Pipeline-validity tests

May proceed without perfect real-RNA geometry:

- q leakage;
- oracle leakage;
- identity shortcuts;
- masks/target construction;
- evidence/depth operator separation;
- B3 impossible recovery;
- B6 ladder behavior;
- restart;
- optimizer-skip/EMA ordering;
- checkpoint completeness.

### Realism/calibration tests

Needed before claiming transfer from synthetic performance to real RNA:

- abundance distribution;
- covariance topology;
- latent-rate dynamic range;
- sign/community structure;
- depth/capture realism;
- other calibrated measurement geometry.

Failure of realism does not invalidate a well-posed pipeline-validity result. Pipeline-validity success does not establish real-world transfer.

## 41,238-address identity boundary

Runtime/synthetic qualification cannot close real biological identity correctness by tensor shape or byte hash alone.

The real adapter must authenticate:

`41,238 registry -> canonical ordering -> reader/index mapping -> tokenizer identity -> tensor entering model`

The synthetic adapter should provide an equivalent authenticated synthetic registry/address mapping so the same identity-aware downstream machinery can be exercised without claiming artificial addresses are human biological identities.

## Runtime convergence dependency

PR #221 and PR #222 are donor lanes only.

The final shared pipeline may use only one canonical runtime successor.

The successor must preserve #222's governance/spillover protections and selectively retain #221's real inactive-consumer/PyTorch/checkpoint mechanics.

The shared qualification contract must be frozen before final runtime interface decisions so runtime does not hard-code assumptions that conflict with real-data qualification.

## Historical spillover constraints

The design must not resurrect:

- historical V64 target/E2 authority graphs;
- old target winners;
- residual-target rescue as an untried route;
- corrected synthetic T_A/T_B as biological evidence;
- biological interpretation of width 160;
- old calibration lineage that erased observation operators at smoke scale;
- historical checkpoint/receipt authority without prospective requalification.

Negative findings remain part of the audit history.

## Acceptance criteria for the shared contract

Before Claude/Macha uses V77 to exercise the intended real-data pipeline, require:

1. exact V3 governance digest is bound;
2. every field has a machine-enforced visibility class;
3. donor/source/study identifiers cannot accidentally enter model input;
4. oracle truth is physically/API separated from normal pipeline code;
5. q-safety is machine-bound transitively;
6. four representation families are expressible without preselection;
7. observation-operator context is explicit and shortcut-controlled;
8. evidence and depth perturbations are separately declared;
9. estimand is evaluation-contract state, not an implicit model feature;
10. unresolved real-data choices remain explicit unresolved values;
11. zero-update qualification is a first-class mode;
12. bounded mutation is separate and requires narrow authority;
13. synthetic-only oracle metrics are separated from common qualification metrics;
14. pipeline-validity and realism/calibration evidence are reported separately;
15. 41K identity authentication remains an explicit real-adapter gate;
16. one canonical runtime successor is used for any mutation rehearsal;
17. historical spillover audit passes;
18. TRAINING remains OFF.

## Non-authority statement

This design freezes architecture for review only.

It does not authorize Stage A, JEPA training, multimodal training, 500K, Stage 4, TEST opening, Morabito opening, a target winner, a representation winner, an estimand, or deciding numeric thresholds.
