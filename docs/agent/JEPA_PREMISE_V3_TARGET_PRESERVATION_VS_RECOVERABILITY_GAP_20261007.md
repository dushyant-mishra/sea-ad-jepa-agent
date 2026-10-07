# JEPA Premise V3 — target preservation versus partial-view recoverability

Date: 2026-10-07

Role: `INDEPENDENT_SCIENTIFIC_AUDIT__PREFREEZE_ONLY`

Hard state remains unchanged: training off; Stage A execution unauthorized; multimodal training off; TEST sealed; Morabito protected; no target winner; no representation winner; population estimand unset.

## Finding

Classification:

`TARGET_PRESERVATION_GATE_NOT_EXPLICITLY_SEPARATED_FROM_PARTIAL_VIEW_RECOVERABILITY`

Premise V3 correctly separates `TARGET_OBJECT_RECOVERABILITY` from `BIOLOGICAL_TRUTH_RECOVERABILITY`, and the representation tournament contains strong shortcut, transport, stability and uncertainty controls. However, the current governing artifacts do not freeze a separate decision-bearing verdict for whether the **rich/full target itself preserves the intended information** before asking whether lawful partial RNA can recover it.

The current flow is approximately:

`define target meaning -> measure target-object recoverability -> test shortcuts/transport/stability`

The historical evidence supports a stricter decomposition:

`rich/full target preservation -> partial-view inference/recoverability -> uncertainty/calibration`

These are different failure modes.

## Why the distinction is required by project history

The project has repeatedly observed that easier prediction can coexist with poorer information preservation:

- historical T0–T4 work identified an information × conditional-predictability frontier;
- TCTX-like targets could be easier to predict while retaining less planted/rare structure than richer H;
- authenticated u0 already contained useful query-local context, while T1 drove its mathematical loss downward and nevertheless eroded that context at biologically informative evidence levels;
- V6R5B produced real latent-space reconstruction improvement that was largely cell-global, without demonstrating the desired program-specific biology;
- R5/R8 later showed that a measured RNA anchor can be predictably reconstructed, while R7 failed to demonstrate the prespecified additional RNA biology.

Therefore a high recoverability score cannot establish that the target being recovered is sufficiently informative.

## What V3 already protects

This finding does not negate existing V3 safeguards. In particular:

- P1 requires target meaning to be declared;
- technical/identity shortcuts must fail;
- evidence and depth curves are separate;
- target-object recoverability is not called biological truth;
- representation transport/stability is separately tested;
- Stage A can claim at most `RNA_REPRESENTATION`;
- Stage A does not authorize training.

Those are strong controls.

## Missing explicit gate

Before a target's partial-view recoverability becomes decision-bearing, a later Stage-A execution authority should prospectively define a `TARGET_PRESERVATION` or equivalent rich/full-view gate.

For each deciding target component, that gate should answer at least:

1. Does the rich/full target vary with lawful biological evidence rather than only address/technical/global-summary structure?
2. Does it retain the RNA structures that the candidate claims to represent, including weak/local/sparse/innovation structure where those are in scope?
3. Does greater biological evidence change/refine the target in the expected direction rather than merely stabilize a low-information object?
4. Does the rich/full target outperform prospectively frozen low-information summaries on the intended preservation endpoints?
5. Which preservation endpoints are same-assay developmental diagnostics versus independently grounded biological fidelity?

Suggested machine statuses, as a proposal rather than current authority:

- `PRESERVATION_SUPPORTED_WITHIN_RNA_SCOPE`
- `PRESERVATION_PARTIAL`
- `PRESERVATION_NOT_SUPPORTED`
- `PRESERVATION_NOT_IDENTIFIED`

These should remain distinct from:

- `RECOVERABLE_FROM_VIEW`
- `PARTIALLY_RECOVERABLE_FROM_VIEW`
- `NONRECOVERABLE_FROM_VIEW`
- `RECOVERABILITY_NOT_IDENTIFIED`

and distinct again from independent biological-fidelity status.

## Consequence for structured targets

For `STRUCTURED_COMBINED_STATE`, preservation must be component-wise. A global component cannot rescue loss of an intended query-local/program component merely because the aggregate target is easy to recover. This requirement complements the separate component-ledger gap already recorded on this audit branch.

## Claim boundary

A Stage-A representation can still be useful even when independent biological truth is unavailable. The proposed preservation gate is not a demand for external biological validation during Stage A. It is a demand to distinguish:

- **does the rich RNA target preserve the RNA information it claims to preserve?**
from
- **can the partial student view infer that preserved information?**
from
- **does that information correspond to transferable biological truth?**

Those are three separate questions.

## Current decision

No current execution bypass was found: Stage A remains unauthorized and no Stage-A verdict authorizes training.

The required repair is prospective machine-level decomposition before later Stage-A execution authority, not a retrospective reinterpretation of old results.
