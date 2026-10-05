# JEPA V5 production-authority closure design

Date: 2026-09-17
Status: APPROVED_WORKING_DESIGN__TRAINING_OFF
Branch: impl/v5-remaining-rna-target-semantics-20260917

## Goal

Close the current JEPA V5 software/authority framework without reopening settled historical work, while keeping every data-dependent scientific choice explicit and prospectively frozen before FULL104 outcomes are inspected.

The foundation objective is biological/cellular latent state, including query-local state conditioned on a canonical molecular address. Numerical hidden-gene expression is not the JEPA target. Expression prediction is only an anti-shortcut diagnostic.

## Non-negotiable boundaries

- TRAINING_OFF until explicit final training authority.
- Protected/pathology/DEV/SEALED/D_shared outcomes remain sealed.
- Historical T0/T1/QID/F1/Stage81A3/FULL104-lineage/Stage-A findings are fixtures/provenance, not current authority unless explicitly rebound.
- Common-core support means comparability, not biology.
- Unmeasured is missing, not zero.
- VALUE_ONLY_256 remains the primary molecular representation.
- Base scientific mass remains donor-uniform, cell-uniform within donor.
- No long FULL104 execution before exact runner commit, tests, independent audit and deterministic canary.

## Architecture

The current authority graph is:

FULL104 substrate
  -> representation
  -> support/estimability
  -> base scientific estimand
  -> canonical address registry/provider
  -> target evidence budget
  -> masking policy
  -> target construction
  -> teacher-target semantics
  -> remaining-RNA necessity
  -> target-identity/anti-cheat bundle
  -> model geometry
  -> EMA timescale/presentation
  -> measurement robustness
  -> runtime source
  -> current preexecution closure
  -> current teacher-target receipt
  -> optimizer/checkpoint guards
  -> explicit training authority

Authority schemas may not infer behavior from experiment names, historical constants, branch names, or free-form labels. Behavioral choices use enumerated vocabulary and exact SHA-256 root binding.

## Masking decomposition

Masking is deliberately split into independent roles.

1. TargetEvidenceBudgetAuthority
   - owns numerical mask burden/evidence-retention rules;
   - owns what happens when requested burden is not feasible on a cell;
   - never chooses which correlated partners to mask.

2. CurrentMaskingPolicyAuthority
   - owns partner-selection policy only;
   - binds support, canonical registry, shortcut/dependency artifact, evidence-budget authority and deterministic RNG authority;
   - cannot silently absorb burden values.

3. MaskingQualificationDesignAuthority
   - owns outer donor split, target-panel selection, address-universe ladder, attacker families, paired estimand, uncertainty method, controls and decision rule;
   - terminal universe must include full 17,186 common core;
   - must reject vacuous/below-precision qualification;
   - primary expression attacker remains diagnostic only.

RIDGE8, TOP8, PREFIX3 and UNIFORM are fixed comparator names for qualification. Exploratory 15%, cap8, ridge alpha .01, target count 32 and PREFIX3 thresholds are not production authority.

## Precision and target panels

Precision authority is separate from masking policy. It binds:

- minimum target count and/or target-clustered effective support;
- minimum outer-fold support;
- target-clustered uncertainty method;
- any prespecified interval or decision threshold;
- policy for insufficient support.

Target-panel authority binds a deterministic, outcome-blind selection rule and exact address list/root. No panel may be selected using the qualification outcome being tested.

Outer-split authority binds deterministic held-donor folds. Feature screening/fitting uses training donors only; held-out donors are evaluation only.

## Target construction and remaining-RNA necessity

TeacherTargetSemanticsAuthorityV2 remains semantic authority:

- BIOLOGICAL_CELLULAR_LATENT_STATE_V1;
- QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1;
- hidden-gene scalar reconstruction forbidden;
- remaining RNA required; identity-only and global-only routes insufficient.

A separate TargetConstructionAuthority binds the exact query-safe computation graph, including:

- canonical query identity remains supplied;
- queried scalar evidence is withheld before contextual mixing;
- lawful non-query RNA evidence remains available;
- lawful global biological context may remain available;
- teacher state construction is detached from student optimization;
- scalar-expression reconstruction is absent from the JEPA objective.

RemainingRnaNecessityAuthority binds the prospective decision rule. Scientific execution evidence is separate from the rule. A healthy current-V5 implementation must be compared against:

1. query identity only;
2. query identity + lawful global biological context with remaining RNA removed.

Passing means remaining RNA materially improves query-local latent-state recovery under the frozen precision authority. Historical T1 checkpoints are adversarial fixtures only.

## Geometry

Historical 128x8, six blocks, 48 tensors, widths 160/224/320/512 and qualification rank ceilings are not production geometry authority.

Geometry authority must bind:

- qualified dimension/rank authority;
- deterministic rank-to-geometry rule;
- exact geometry artifact;
- dynamic protected registry derived from that geometry.

Once geometry is selected, the Stage-A memorization/capacity predicate must be rerun against the actual current geometry before training can advance.

## EMA and measurement robustness

EMA mechanics are already established: update only after a proved optimizer step; presentation cursor advances only after successful presentation.

EMA timescale authority owns presentation unit and half-life. Historical .996 is not authority. Preferred functional form remains presentation-normalized half-life; exact half-life is a separate explicit scientific choice.

Measurement robustness binds a prospective perturbation protocol, state-level metric, stratification guardrails and acceptance rule. It must distinguish representation failure from insufficient physical evidence/support.

## Runtime and training lock

A current runtime-source authority must bind the exact production implementation bytes. No current closure may call historical V4 production_update or validate through legacy receipt schemas.

Preexecution closure must verify exact current roots, critical-test authority, dynamic protected registry, runtime source and training lock.

Final training authority is a distinct object. No other authority may set training_authorized=True.

Before final training authority, required evidence includes:

- current target/masking/evidence-budget/precision/split/panel/target-construction roots frozen;
- FULL104 masking qualification completed under frozen contract;
- healthy-teacher remaining-RNA necessity completed;
- geometry selected and Stage-A geometry-dependent capacity rerun passed;
- EMA timescale frozen;
- measurement robustness passed;
- runtime-source provenance exact;
- all critical tests EXECUTED_PASS with zero skipped;
- current authority closure/root-splice checks passed.

## Execution discipline for FULL104/Claude

Long runs follow:

commit exact runner -> code audit -> unit/fixture tests -> deterministic FULL104 canary -> canary audit -> long run.

Claude may execute read-only FULL104 census work before scientific outcomes are opened. The census should determine support, feasible burdens, target/fold support and precision inputs. Claude must not tune masking policy from qualification outcomes before the prospective authorities are frozen.

## Governance

Use one successor integration line rather than parallel redesign branches. Every historical component is classified ALREADY_AUDITED, SUPERSEDED, OPEN or CHANGED_INPUT_REQUIRES_REQUALIFICATION before reuse.

Any successor schema must be added to the Stage-A spillover firewall and the superseded schema quarantined. Current closure must reject self-consistent legacy objects, not merely mismatched hashes.

## Completion definition

Software/framework closure is reached when all current schemas, binders, tests, execution packages and governance are complete and only explicit data-dependent values/results remain to be supplied by prospectively audited FULL104 runs.

Scientific/training closure is reached only after those FULL104 results pass their frozen authorities and a distinct explicit training authority is issued.
