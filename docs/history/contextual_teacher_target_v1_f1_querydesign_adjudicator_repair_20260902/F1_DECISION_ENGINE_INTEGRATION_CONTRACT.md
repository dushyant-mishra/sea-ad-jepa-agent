# F1 decision-engine integration contract

Lawful path: **Path A**. `contextual_target_f1_querydesign_decision_v2.py` is explicitly `QUERY_DESIGN_COMPONENT_ONLY`; it exposes `query_design_component_pass`, never a full-F1 qualification decision.

The complete frozen engine remains `scripts/v4/contextual_target_f1_decision_v1.py`, SHA-256 `204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34`. Its controlling prose authorities remain:

- `F1_DECISION_LOGIC_PROPOSAL.md`, SHA-256 `c7c4938f01762a4f6ae221690b87ef1e77dea0107dcca5fa8e5e7364875963bf`;
- `F1_CONTEXTUAL_STATISTICAL_ESTIMAND_CONTRACT.md`, SHA-256 `34af5c31b361eb8d17e1daaf47126f14fb6296f6d998f4855622922ca2f8df14`.

The already-frozen `F1_QUERY_IDENTITY_V2_CONTRACT.md`, SHA-256 `15d873871787e0820f63aaead8f27a6f1057541e16640d8492053144a9c69423`, prospectively replaces the older margin/Spearman pair with own-minus-wrong margin and exact win-minus-0.5. The adapter therefore maps those two v2 donor arrays to the unchanged engine's two query-identity slots; it does not claim that win is Spearman.

The thin hash-bound adapter `contextual_target_f1_decision_integration_v3.py` rejects engine hash drift and has exactly one production qualification entry: `integrate_records()`. That entry invokes the exact-population aggregator itself, derives every decision endpoint from the resulting aggregate, requires component-only scope, executes the complete engine, and defines full qualification as the conjunction of component PASS and complete-engine qualification. There is no production aggregate-only qualification API and no caller-supplied complete outcome payload. Thus every frozen non-query gate remains independently veto-capable: protected-family estimability/reporting, direct-degradation Holm veto, evidence trend, query identity v2, HC3 nuisance audit, cross-source replication, legal authority, and missing/nonfinite/zero-variance/rank failures.

Nuisance input is limited to exact ordered donor IDs plus all six frozen semantic categories: source indicators, operator-mixture fractions, recipient physical support, recipient depth, correct-minus-null visible depth, and correct-minus-null measured-zero rate. Empty/missing categories or donor mismatch fail closed. The real nuisance-authority root remains unset in this pre-result turn; no caller-chosen nuisance matrix is promotable.

No v2 component result can promote by itself. Real evaluation is also blocked because `FROZEN_FORWARD_AUTHORITY_SHA256` remains unset. A future forward root must bind model/checkpoint, query, physical and artificial masks, evidence level, role, recipient, null source, semantic snapshot, model/source provenance, sketch, and numerical identity. Only true teacher target reuse is lawful across comparisons; correct and null student forwards cannot share identity.

No threshold, multiplicity family, evidence level, nuisance rule, endpoint, or claim scope is changed here.
