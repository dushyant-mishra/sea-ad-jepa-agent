# F1 15C Nuisance Integration Contract

Status: prospectively frozen before 15C implementation. This contract binds a synthetic-only integration test; it does not authorize real F1 execution.

1. The scientific nuisance selection is immutable at `(r_HVS, r_NPH52, r_SEAAD) = (5, 0, 4)`.
2. The exact selected design bytes are immutable at SHA-256 `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`.
3. Donor order comes only from `F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json`, SHA-256 `d7d0be302b455f7be0982d3e7906778c4fac59aee9b9f5c43e6017090d25e778`.
4. The nuisance calculation uses exactly the HC3 family resolved in `F1_15C_NUISANCE_SEMANTIC_PREFLIGHT.json`: equal-donor OLS at evidence 0.6; intercept under the frozen centered nuisance design; HC3 covariance; two-sided 95% lower bound; PASS iff estimable and lower bound is strictly positive. No new endpoint or test is introduced.
5. The adapter recomputes HC3 from donor-level synthetic inputs. Caller-supplied HC3 PASS flags, p-values, intervals, standard errors, leverage, rank, legal values, or replacement nuisance designs are rejected and never authoritative.
6. Legal provenance remains strict: `type(value) is bool`; only literal `True` can pass.
7. `F1_FINAL_DECISION_TRUTH_TABLE_V2.json`, SHA-256 `76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e`, remains byte-identical.
8. The query assignment, matched-null map, population, evidence ladder, multiplicity, claim scope `FINITE_FROZEN_2781_DESIGN_SAMPLED_W2_EXPECTATION`, and program estimand `DESIGN_SAMPLED_W2_PROGRAM_ESTIMAND` remain byte-identical.
9. 15C uses deterministic synthetic/adversarial outcomes only. It may not read expression, model/checkpoint tensors, or real candidate outcomes and may not train or update EMA.
10. Real reader/forward execution authority remains unset. The adapter must fail closed on any real-record execution attempt until a later reviewed authority explicitly sets it.

The additive route is controlling: `contextual_target_f1_decision_v4.py` and `contextual_target_f1_decision_integration_v4.py` remain unchanged. Any need to alter a scientific rule terminates with `STOP_F1_15C_NUISANCE_SEMANTIC_UNRESOLVED`.
