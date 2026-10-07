# JEPA premise V3 — component-level fidelity/recoverability machine-enforcement gap

Date: 2026-10-07

Role: `INDEPENDENT_HISTORICAL_ASSIMILATION_AUDIT__NOT_STAGE_A_AUTHORITY`

Hard state remains: `TRAINING=OFF`; `STAGE_A_EXECUTION=NOT_AUTHORIZED`; multimodal training off; TEST sealed; Morabito protected; target winner none; representation winner none; estimand unset; deciding numeric margins unset.

## What was inspected

Premise V3 branch `design/premise-qualification-contract-v3-20261006`, current reviewed head `6deeb27f778e4bf1251837a717218fd91d323727` / tree `0811454232017438f2aef02a88ff16a4f7aa0bea`.

Binding artifacts inspected directly by blob identity include:

- `docs/agent/JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json` — blob `d8d6be5f2f1d4f7f50dfc2cc38b688deff9ef1f9`
- `docs/agent/JEPA_STAGE_A_REAL_RNA_TARGET_GATE_V3_PREFREEZE_20261006.md` — blob `aaed96ab481d39ac71820c90a60cfb3f968df6db`
- `docs/agent/JEPA_PREMISE_V3_SELF_REVIEW_20261006.md` — blob `b9303ac077bc65890aae20b71b5faad1322eb78a`
- `docs/agent/JEPA_PREMISE_V3_INDEPENDENT_AGENT_REVIEW_20261006.md` — blob `8abb43893ab3381f0fc370d4eb6213d810fa71f2`

The previous V3 self/independent reviews correctly repaired top-level schema closure, Stage-A verdict binding, hard-state flags, diagnostic firewall, uncertainty-operator separation, alignment leakage, observation shortcuts and claim vocabulary. This checkpoint does not dispute those repairs.

## Finding

Classification:

`P1_COMPONENT_LEDGER_MISSING__PROSE_SEMANTICS_STRONGER_THAN_MACHINE_ENFORCEMENT`

Premise V3 correctly states several important principles:

1. target-object recoverability is distinct from biological-truth recoverability;
2. a nonrecoverable component is not automatically a model defect;
3. biological-evidence uncertainty and measurement-depth uncertainty must remain separate;
4. external does not imply independent;
5. Stage A can at most qualify an RNA representation, not transferable biology/regulation/causality.

However, the machine state contains no mandatory per-component target ledger. The Stage-A prefreeze prose says a nonrecoverable *component* should be reported as `NONRECOVERABLE_FROM_VIEW`, but the machine state only binds a top-level verdict roster. It does not require each component of a structured target to carry its own semantic/fidelity/recoverability/support record.

## Why this matters scientifically

Historical target work demonstrated the exact failure mode:

- R5/R8 showed that a measured RNA target can be predictably reconstructed from complementary RNA.
- R7 showed that the same developmental anchor did not demonstrate the prespecified added biological readouts.
- Therefore student predictability and teacher biological fidelity are empirically separable in this project.
- Earlier rich-H/contextual work also showed that aggregate latent improvement can be dominated by cell-global/easy structure while fine query-local biology deteriorates or remains unproven.

A `STRUCTURED_COMBINED_STATE` can therefore contain, simultaneously:

- a highly recoverable but same-assay/developmental component;
- a biologically important but only partially recoverable component;
- a teacher-private/nonrecoverable component;
- a component whose fidelity has not been independently established;
- a component requiring abstention because support is absent.

Without a mandatory component ledger, an aggregate/top-level verdict can hide these differences even while obeying the present top-level schema.

## Minimal machine-level successor requirement before Stage-A execution authority

Require a nonempty `target_components` roster for every candidate target/representation object. At minimum each deciding component should bind:

- `component_id`
- `semantic_role`
- `measurement_basis`
- `fidelity_status`
- `recoverability_status`
- `support_status`
- `abstention_rule`
- `uncertainty_axes`
- `fidelity_evidence_root`
- `recoverability_evidence_root`
- `claim_ceiling`

Recommended exact recoverability vocabulary:

- `RECOVERABLE_FROM_VIEW`
- `PARTIALLY_RECOVERABLE_FROM_VIEW`
- `NONRECOVERABLE_FROM_VIEW`
- `NOT_IDENTIFIED`

Recommended fidelity vocabulary should distinguish at least:

- `INDEPENDENTLY_SUPPORTED`
- `SAME_ASSAY_DEVELOPMENTAL`
- `UNVALIDATED`
- `NOT_TESTABLE_AT_AVAILABLE_POWER`

These vocabularies are a proposed repair target, not current authority.

## Required aggregation rule

Top-level qualification must not allow an aggregate score from one easy component to rescue a failed/unvalidated deciding component. The Stage-A execution authority should prospectively state which components are:

- veto-bearing;
- report-only;
- allowed to be partially/nonrecoverable without student failure;
- required to abstain when unsupported.

A component may be biologically meaningful and nonrecoverable from the student view. Conversely, a component may be highly predictable from RNA yet remain biologically unvalidated. Those states must remain machine-distinct.

## External evidence binding

For any component promoted above same-assay developmental status, the component ledger should bind the independent-evidence root and exposure state. Morabito aggregate/gene-level exposure and SCENIC+/Stage75F RNA-derived hypotheses cannot silently satisfy independent biological fidelity.

## Current decision

This finding does **not** invalidate Premise V3 as governance documentation. It identifies a narrower missing machine-enforcement layer that should be closed before any Stage-A execution authority is issued.

Current classification:

`PREMISE_V3_CONCEPTUALLY_SOUND__COMPONENT_LEVEL_FIDELITY_RECOVERABILITY_LEDGER_NOT_MACHINE_BOUND`

No Stage-A execution or training is authorized by this checkpoint.
