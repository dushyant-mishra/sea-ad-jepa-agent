# Foundation Representation Residual Gates Audit Addendum — 2026-10-11

## Scope

Independent successor review of PR #276 on top of the verified PR #269 representation-qualification implementation. No TEST/Morabito, pathology, corrected target-discovery values, representation selection, Stage4 or training authority is created.

## Verification

PR #276 head: `2f0012d6aece9f0f6c119c2220bcd76fb49c1a28`.

TDD/execution history is informative rather than hidden:
- RED run `38152620525`: missing residual-gate module;
- subsequent failures exposed focused-CI import defects (missing `src` path, then accidental PyTorch import through `v4.__init__`);
- both execution defects were repaired without relaxing scientific assertions;
- GREEN run `38153112172`, job `114510466966`: **19 passed in 0.51 s**.

The residual adjudication code is now pure/focused and does not require the heavyweight training package merely to review compact evidence.

## Current held-out-donor evidence

Authenticated calibration bundle SHA-256:
`07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.

At u205 on 45 held-out TRAIN donors, `rich_H` shows:
- source balanced accuracy `1.0`;
- operator balanced accuracy `0.763206`;
- measured-support-count R² `0.999800`;
- broad-annotation balanced accuracy `0.495018`;
- broad-annotation change from u0 `+0.004386729`;
- innovation-tail R² `0.650789`, change from u0 `+0.003248402`.

These are legitimate held-out-donor measurements, but no prospectively frozen learned-representation pass threshold existed that would permit retrospective promotion. Ruling:

`CURRENT_HELDOUT_DONOR_EVIDENCE_AVAILABLE__NO_PREFROZEN_PASS_THRESHOLD__NOT_FREEZE_QUALIFIED`

## Conditional source/technology imprint

A direct u205 EMA-target 160-D CELL-state diagnostic was run on the authenticated 84-cell truth table. Truth-table expression SHA-256:
`2aca870343b65f2deabe32fdc8e18bd26211f505e8bcb3b6f2d53cb0dc6573c3`.

Using donor-grouped 5-fold CV:
- all-source learned-state source BA: `1.0`;
- on 68 HVS/SEA-AD cells with shared broad biological classes, broad-class-only source BA: `0.5895833333`;
- broad class + learned state source BA: `1.0`;
- increment attributable to adding learned state over broad class: `+0.4104166667`;
- source BA remains `1.0` separately within GABAergic, glutamatergic and non-neuronal shared broad classes.

This is strong evidence that the learned state retains source/acquisition information beyond coarse biological class. It is deliberately **not** called a purely technical causal effect because source, donor, biological composition and observation process are not fully separable here. It is also fit-population evidence, not held-out technology authority.

Ruling:
`RESIDUAL_SOURCE_IMPRINT_OBSERVED__FIT_POPULATION_DIAGNOSTIC__TECHNOLOGY_INVARIANCE_NOT_QUALIFIED`

## Matrix-transfer identifiability

The exact frozen 50K sample metadata were audited leave-one-matrix-out across 42 matrices.

- 35 matrices have broad labels available;
- all 7 NPH52 matrices have no broad-label vocabulary in the frozen metadata;
- mean leave-one-matrix native-label cell coverage is approximately `0.77769`;
- some HVS labels (for example VLMC and Microglia-PVM) are unique to one matrix;
- SEA-AD caudate carries 17 native subclass labels absent from every other matrix;
- SEA-AD hippocampus has additional unique native labels.

Therefore matrix-transfer scoring must be stratified by what is actually identifiable; a single pooled matrix-transfer number would be scientifically misleading. Identifiability accounting is closed, but final-representation matrix performance is not.

## Resource audit

Measured CPU u205 forward path over the full 41,238-token vocabulary:
- 1 cell: ~`1.03 s` inference, ~`753 MiB` peak RSS;
- 4 cells: ~`4.52 s`, ~`1.55 GiB` peak RSS;
- 12-cell chunks: ~`13.4–15.5 s`, ~`1.65 GiB` peak RSS.

The conservative laptop CPU batch ceiling is `<=4`. This is bounded CPU evidence only; it is not a final production-GPU RAM/I/O/wall-time qualification.

## FULL104 dimension cross-check

PR #270/#273/#274 already close the prospective Monte-Carlo precision and authenticated metric-receipt mechanics. The remaining FULL104 work is genuinely physical: bind the >30 GB / 8,915-block substrate to terminal `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`, compute actual full-stream rank metrics, validate the receipt, apply the frozen selectors, then independently audit the numerical D_shared/D_private/D_obs result. Those bytes are not mounted in this environment, so no dimension value is fabricated here.

## Audit ruling

Preserved conclusions remain:
- state-basis interpretation: `SUBSPACE_ONLY`;
- biological-evidence and measurement-depth uncertainty: separate;
- biological-support and measurement-domain OOD: separate axes;
- production sampler: prospectively frozen metadata-only authority;
- observation provenance shortcuts: forbidden.

New terminal:

`FOUNDATION_RESIDUAL_GATES_MEASURED__LEARNED_T1_INVARIANCE_NOT_QUALIFIED__MATRIX_IDENTIFIABILITY_ACCOUNTED__FINAL_HELDOUT_CONDITIONAL_AND_GPU_FULL104_PHYSICAL_GATES_PENDING__REPRESENTATION_FREEZE_BLOCKED__TRAINING_OFF`

Still false: representation winner, target winner, Stage4, target-discovery value-read authority, TEST/Morabito/pathology access and JEPA training.
