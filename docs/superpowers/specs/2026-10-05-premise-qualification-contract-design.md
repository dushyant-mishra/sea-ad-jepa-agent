# JEPA Premise Qualification and Real-RNA Target Contract — Design

Date: 2026-10-05
Role: PROSPECTIVE_SCIENTIFIC_GOVERNANCE_SPEC
Branch base: `main@3d70167800369fb4f6b335563712576a8cb6c1f3`

## 1. Purpose

Freeze the scientific questions, comparison structure, claim boundaries, and fail-closed decision logic that must govern future target/representation work **before any deciding TRAIN-only real-RNA result is opened** and before Macha's new synthetic Worlds B/C/D are used to tune verdict rules.

This specification does not authorize encoder optimization, EMA updates, 500K promotion, Stage 4, Morabito opening, or TEST opening.

The controlling scientific premise is:

> Observable RNA is not the same object as recoverable RNA structure; recoverable RNA structure is not automatically biological state; biological state is not automatically transferable biological state; transferable state is not automatically causal state.

The project must test each transition rather than infer stronger claims from a weaker success.

## 2. Premise gates P1-P6

### P1 — Target meaning
For each candidate target, state what biological/statistical object it is intended to represent **independently of the architecture used to predict it**.

A valid declaration must specify:
- object scope: transcriptomic/global/program/query-local/novelty/other;
- what measured quantities are allowed to define it;
- what measured quantities are forbidden;
- whether it is an observation-derived object or an independently supported biological object;
- why matching it would mean more than reconstructing the hidden scalar or generic covariance.

Failure state: `TARGET_MEANING_UNDEFINED`.

### P2 — Recoverability ceiling
For every target component, estimate how much information is available from the lawful partial-RNA view before model qualification.

Each component must be classified prospectively as one of:
- `BIOLOGICALLY_RELEVANT__RECOVERABLE`;
- `BIOLOGICALLY_RELEVANT__PARTIALLY_RECOVERABLE`;
- `BIOLOGICALLY_RELEVANT__NONRECOVERABLE_FROM_VIEW`;
- `NOT_ESTABLISHED_AS_BIOLOGICAL`.

Model recovery is interpreted relative to the recoverable ceiling, not raw planted/observed variance alone.

A biologically real but nonrecoverable component is **not** a model failure.

### P3 — Structured-state test
No single-vector representation is privileged prospectively.

At minimum compare these representation families:
1. `GLOBAL_CELL_STATE` — one cell-level vector intended to encode broad shared/recoverable state.
2. `QUERY_LOCAL_STATE` — address-conditioned/gene-conditioned representation of local state.
3. `PROGRAM_STATE` — one or more program/subspace representations.
4. `STRUCTURED_COMBINED_STATE` — explicit combination of global + program + query-local/novelty components.

Qualification must determine which biological information each family can recover and which it necessarily discards. Failure of a global vector to recover genuinely local or novelty information must not automatically count as failure of the structured representation family.

### P4 — Technical identifiability
A candidate must demonstrate that its apparent biological signal is not explained by lawful technical/measurement structure.

Mandatory nuisance/control families:
- gene/address identity;
- source identity;
- operator identity;
- sequencing depth/library size;
- visibility/support/missingness pattern;
- normalization-mediated query leakage;
- donor/source imbalance;
- matched wrong-query/query-exchangeability controls;
- biology x operator interaction when the substrate supports it.

Naive global technology invariance is **not** required. State-dependent observation effects are allowed to exist; they must be measured and bounded rather than erased by definition.

### P5 — Transport estimand
Transport claims must state the population over which generalization is intended.

The evaluation ladder is distinct:
`held-out cell < held-out donor < held-out operator < held-out study < held-out technology`.

A donor holdout may support donor transfer within a source family. It cannot by itself support universal cross-study or cross-technology state claims.

Before real training, the foundation-population estimand must be declared separately (cell-weighted, donor-weighted, source-balanced donor-weighted, or another explicitly justified estimand).

### P6 — Claim boundary
Success is classified on a four-level claim ladder:

1. `RNA_REPRESENTATION` — recoverable transcriptomic structure from lawful partial RNA.
2. `TRANSFERABLE_BIOLOGICAL_STATE` — additional evidence of transport/semantic validity across independent biological/measurement contexts.
3. `REGULATORY_SUPPORT` — independent regulatory/chromatin evidence supports biological interpretation.
4. `CAUSAL_PERTURBATIONAL_PREDICTION` — intervention evidence supports counterfactual claims.

No lower level automatically promotes to a higher level.

## 3. Stage-A TRAIN-only real-RNA qualification contract

Stage A is a **target/representation discrimination experiment**, not model training.

### 3.1 Hard execution boundary
During target selection:
- encoder optimizer steps = 0;
- predictor/encoder training steps = 0 unless a separately approved frozen diagnostic explicitly requires a fitted readout;
- EMA teacher updates = 0;
- no warm start from legacy checkpoints as biological authority;
- TRAIN-only data may be used only according to the prospective split/estimand contract;
- TEST remains sealed;
- Morabito remains protected;
- no external validation asset is used to choose the target.

### 3.2 Legality gate — absolute fail
A target fails immediately if the hidden answer can reach the target or permitted evidence through:
- direct query value;
- pre-contextual teacher access to the query value;
- total-count or other normalization that changes visible tokens as a function of the hidden query value;
- support/missingness channels that encode the answer;
- another hidden scalar copied through a deterministic transform;
- any unenumerated equivalent leakage seam found by audit.

Verdict: `FAIL_LEAKAGE`.

### 3.3 Shortcut gate — absolute fail
A target must add information beyond predeclared shortcut baselines. At minimum:
- address/gene identity only;
- matched wrong-query / query exchangeability;
- capacity-matched global summary;
- source/operator/depth/support-only baselines;
- technical-only model;
- remaining-RNA ablation/necessity where meaningful.

A shortcut-only world or baseline that satisfies the biological qualification rule invalidates that rule.

Verdict: `FAIL_SHORTCUT`.

### 3.4 Recoverability-aware biological gate
For each target/representation family report:
- recoverability ceiling under lawful partial RNA;
- observed candidate recovery;
- candidate recovery / recoverable ceiling;
- uncertainty at the biological resampling unit;
- global information recovery;
- query/local information recovery;
- program-level recovery;
- rare/novel signal behavior where the real substrate permits a defensible test.

No requirement forces all information into one vector.

### 3.5 Transport gate
Stage-A minimum: held-donor evaluation with donor-level uncertainty under the chosen estimand.

Where the TRAIN substrate permits non-confounded evaluation, also report held-source/operator transport. Do not upgrade absence of an available higher transport level into a pass.

Possible verdicts include `FAIL_TRANSPORT` or `TRANSPORT_LEVEL_NOT_TESTED`.

### 3.6 Decision outcomes
A candidate/representation may receive only one of:
- `QUALIFIED_FOR_RNA_REPRESENTATION`;
- `INFORMATIVE_BUT_NOT_QUALIFIED`;
- `FAIL_LEAKAGE`;
- `FAIL_SHORTCUT`;
- `FAIL_TRANSPORT`;
- `NONRECOVERABLE_FROM_VIEW`;
- `INDETERMINATE`.

`QUALIFIED_FOR_RNA_REPRESENTATION` authorizes **no stronger biological/regulatory/causal claim** and does not itself authorize production training.

## 4. Prospective statistics and threshold discipline

Freeze before deciding results are opened:
- comparison directions;
- paired comparison structure;
- biological resampling unit;
- estimand weights;
- multiplicity policy;
- negative-control roster;
- stop/fail conditions;
- metric definitions;
- representation extraction definitions.

Numeric effect margins may be fixed only from pre-existing independent calibration/null authority or from a separately prospectively approved calibration procedure that does not view deciding candidate outcomes.

If no defensible authority exists, the numeric margin remains `UNSET_REQUIRES_APPROVAL`. It must not be selected after viewing target results.

Cell count must not substitute for biological-unit count. Disease/donor claims use donor-level or higher biological units as appropriate.

## 5. Relationship to synthetic Worlds A/B/C/D

Macha's synthetic lane is method-development evidence, not real biological validation.

- World A: locked linear/common-biology recoverability and nuisance-control world.
- World B: heterogeneous/rare/partial-recoverability truth.
- World C: structured/local/nonlinear/biology x operator truth.
- World D: regulatory/multimodal truth with biological-vs-technical ATAC-private separation.

The synthetic worlds may validate whether metrics and controls behave as intended. They must not be used to retrofit the real-RNA target meaning, claim boundary, or deciding thresholds after observing a preferred architecture's performance.

Oracle/recoverability ceilings may be measured before JEPA evaluation because they define the denominator. If measured synthetic ceilings contradict the prospectively designed truth class, that is a simulator construction failure to repair or withdraw, not a reason to reinterpret the class.

## 6. Claim separation

The project will use this vocabulary:

- `recoverable transcriptomic state` or `predictable shared molecular state` for Stage-A RNA-only objects;
- `transferable biological state` only after independent transport/semantic qualification;
- `regulatory support` only after independent regulatory/chromatin evidence;
- `causal/counterfactual state` only after perturbational/intervention evidence.

`pathology-label blind` means labels are not supplied for optimization. It does not mean pathology-associated biology is absent from RNA.

`molecule-subsampling stability` is not equivalent to independent experimental remeasurement stability.

The canonical 41,238-address ledger is the lawful RNA observation universe, not complete cellular molecular state.

## 7. Stop conditions

STOP and redesign the premise/metric rather than tune thresholds if:
- target meaning is undefined;
- the target is not identifiable from the permitted view and the experiment interprets that as model failure;
- a biology-absent/covariance-only or technical-only control passes the biological qualification rule;
- rare/novel biology is classified as absent solely because it is poorly predictable;
- a cross-modal semantic validation uses information already supplied to the model;
- the result materially depends on an arbitrary synthetic-feature-to-41K identity mapping;
- training loss/masked-RNA prediction is being used as biological-state proof;
- a stronger claim level is inferred from a weaker one without its own qualification;
- the deciding threshold is being chosen after the deciding result is visible.

## 8. Required artifacts before any production training decision

1. target-meaning declaration for every candidate;
2. recoverability assessment/ceiling where estimable;
3. frozen representation comparison (`GLOBAL_CELL_STATE`, `QUERY_LOCAL_STATE`, `PROGRAM_STATE`, `STRUCTURED_COMBINED_STATE`);
4. leakage seam audit;
5. shortcut/negative-control specification;
6. transport estimand and biological resampling unit;
7. foundation-population estimand declaration;
8. frozen metric/verdict contract;
9. claim level requested by the experiment;
10. explicit statement of what remains untested.

Only after these artifacts exist may a separate authority decide whether a narrow TRAIN-only execution is permitted.

## 9. Non-authority statement

This specification freezes scientific governance. It does **not** select a target, select a representation winner, set network width/dimension, authorize training, authorize 500K, authorize Stage 4, open TEST, open Morabito, or confer biological validity on `cell_state`, gene-block state, or any legacy checkpoint.
