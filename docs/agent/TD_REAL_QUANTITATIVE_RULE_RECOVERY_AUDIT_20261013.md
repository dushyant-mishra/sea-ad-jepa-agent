# TD real quantitative-rule recovery audit — 2026-10-13

Status: `REUSABLE_STATISTICAL_COMPONENTS_RECOVERED__TWENTY_EIGHT_GATE_RULES_REMAIN_PROSPECTIVE__NO_REAL_TD_AUTHORITY`

## Scope

This is an outcome-blind engineering/recovery audit stacked on the qualified structural-gate executor work. It does not evaluate biological candidates, does not promote historical descriptive cutoffs, and does not authorize real target discovery.

The question was: among the 28 unique real-TD gate rules still unmaterialized, which low-level statistical/mechanical components already exist and can be reused exactly, and what scientific decision is still missing for each gate?

Machine-readable result:

`results/target_discovery/real_tournament/TD_REAL_QUANTITATIVE_RULE_RECOVERY_MAP_V1.json`

## Recovered reusable components

### Donor-primary exact directional inference

The existing `td_target_tournament_precision.py` already binds exact donor identity, rejects duplicate donor IDs, computes exact two-sided sign-test resolution, and distinguishes insufficient donor resolution from a directional failure.

A new thin reusable adapter, `td_real_quantitative_components_v1.py`, maps that frozen statistic into `PASS/FAIL/NOT_ESTIMABLE` while leaving the biological meaning and positive direction to the future gate-specific contract.

Self-audit corrected an erroneous test assumption: at two-sided `alpha_eff=0.01`, seven unanimous nonzero donors are not sufficient (`p=0.015625`), while eight unanimous donors are sufficient (`p=0.0078125`). The implementation already followed the correct frozen precision law; the regression test was fixed rather than weakening the code.

### Non-compensation and exact strata

The reusable adapter also provides:

- `noncompensating_status`: any FAIL -> FAIL; otherwise any NOT_ESTIMABLE -> NOT_ESTIMABLE; otherwise PASS;
- `required_strata_status`: requires the exact prospectively declared stratum set, refusing missing or extra strata before applying non-compensation.

These are reusable mechanics for source/transfer/composite rules. They do not define what biological endpoint each stratum must pass.

### Existing raw falsifier machinery

`td_real_tournament_falsifiers_v1.py` already emits raw case- and donor-level deltas for the frozen mandatory controls, including matched wrong cell, fine-neighborhood wrong cell, q-count only, q-address only, query-agnostic, wrong-q, technical+q and identity/support-only baselines.

These raw deltas are evidence components only. They do not establish a prospective biological gate threshold.

### Measurement and lineage components

- `td_measurement_noise_fixture.py` supplies deterministic synthetic-only same-cell pseudoreplicates and depth thinning. It remains synthetic reference mechanics, not a real G8 gate executor.
- `td_query_information_guard.py` supplies direct/transitive q-scalar leakage exclusion. It can support G6's information firewall, but does not establish a teacher information advantage.
- `td_donor_resampling_audit.py` protects donor dependence assumptions but does not define a candidate-specific recurrence endpoint.

## What remains unresolved

All 28 unique gates remain `RULE_NOT_MATERIALIZED`. The recovery audit deliberately made **zero gate-readiness promotions**.

The machine map records, for each gate, the exact reusable component(s) and the remaining prospective scientific decision. Broadly:

- biological-content, specificity, recurrence, source, transfer and falsifier gates still need candidate-specific donor-level endpoints and prospective decision rules;
- G6 still needs an actual teacher-versus-student information-advantage estimand/rule, beyond leakage exclusion;
- G7/G8 still need prospective convergence/measurement-robustness metrics and tolerances;
- G9 needs candidate-specific learned-teacher continuity; historical TD60 is conditional to the relational learned-teacher family, not a universal G9 rule;
- G12 still needs a prospectively frozen minimum eligible-coverage rule;
- C6/C4 need explicit incremental-information/robustness endpoints and nondegradation rules, while constituent survival remains independent;
- C5 specialist gates M1-M4 need a new prospective specialist structural contract because their names in V2 are insufficient to define exact machine predicates without adding science after the fact.

## Verification

Exact green head before this documentation-only commit:

`7db3c08e1ad84943cae04e6956023b7dc23ee47f`

Workflow:

- `TD real quantitative component audit`
- run `38477806445`
- job `115572729692`
- result: **SUCCESS**
- tests: **33 passed**
- tracked worktree: clean
- recorded `BIOLOGICAL_OUTCOMES_OPENED=false`
- recorded `REAL_TD_AUTHORIZED=false`

The branch-level diff from the structural qualification head contains only a new audit workflow, reusable statistical component module, tests, and the outcome-blind recovery map. No candidate definitions, biological outcomes, synthetic/V79 machinery, or real-tournament execution code were modified.

## Authority

No biological outcome was opened. No real-TD gate outcome was produced. No historical descriptive cutoff was promoted. Real tournament QUALIFY remains ineligible. Target selection, representation selection, TD60, Stage4, production EMA and training remain unauthorized.

Terminal:

`STRUCTURAL_EXECUTORS_QUALIFIED_MECHANICALLY__QUANTITATIVE_COMPONENTS_RECOVERED__TWENTY_EIGHT_GATE_RULES_STILL_REQUIRE_PROSPECTIVE_SCIENTIFIC_MATERIALIZATION__NO_REAL_TD_AUTHORITY`
