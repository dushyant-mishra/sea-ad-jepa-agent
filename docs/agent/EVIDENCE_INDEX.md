# EVIDENCE_INDEX.md — Selective Historical Retrieval Map

Use this file to retrieve only the evidence needed for the current question. Do not feed all historical artifacts to every agent.

## Live gate — read first

- Compact state: `docs/agent/memory-os/ACTIVE_STATE.md`
- Machine-readable next action: `docs/agent/memory-os/NEXT_ALLOWED_ACTION.json`
- Current authority index: `docs/agent/CURRENT_AUTHORITY_INDEX.md`
- Current supersession map: `docs/agent/CURRENT_SUPERSESSION_MAP.md`
- Controlling external review: `docs/agent/reviews/F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_EXTERNAL_REVIEW_20260902.md`

Current controlling terminal:
`STOP_F1_EVIDENCE_TREND_NUMERICAL_DEFECT_UNRESOLVED`

## Evidence-trend repair evidence

- Historical frozen decision arithmetic: `scripts/v4/contextual_target_f1_decision_v1.py`
- Current frozen-base decision: `scripts/v4/contextual_target_f1_decision_v4.py`
- decision-v4 invokes historical v1 `evidence_slopes()` for the evidence-trend endpoint.
- Frozen evidence grid: `(0.2,0.4,0.6,0.8,1.0)`.
- Current prospective stable identity: `(A100-A20)+0.5*(A80-A40)`.
- Do not edit historical decision-v1/v4 in place; the next work is a superseding synthetic-only decision layer with full gate-vector regression and fresh external review.

## Accepted 15C HC3 numerical repair

- Final reviewed commit: `5e8127d360d1effd0867a73c2bb007ddffb2c901`.
- External review: `docs/agent/reviews/F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_EXTERNAL_REVIEW_20260902.md`.
- Repair output package: `outputs/contextual_teacher_target_v1_f1_hc3_15c_numerical_robustness_repair_20260902/`.
- Repair manifest SHA-256: `f7cc3be9340c817f57953d3ef009c568a57dca7ea4fffbc2ccefbe6266e123a5`.
- Production HC3: `scripts/v4/contextual_target_f1_hc3_stable_qr_v2.py`.
- Independent SVD validator: `scripts/v4/validate_contextual_target_f1_hc3_svd_v2.py`.
- Additive adapter: `scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py`.
- Frozen effective centered design SHA-256: `37653ed4a21f513a7389630bffa7447f9022323e8240bb80f53394138f1917eb`.

The earlier `STOP_F1_HC3_15C_NUMERICAL_INDEPENDENCE_UNRESOLVED` is historical/resolved. Use the supersession map before treating old 15C review text as current.

## 15A4 / 15B nuisance-design authority

- 15A4 complete frontier procedure: `scripts/v4/derive_contextual_target_f1_hc3_replication_frontier_v3.py`
- 15B selected geometry: `docs/history/exact_bytes/outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902/F1_HC3_SELECTED_GEOMETRY.json`
- Frozen selection: `(5,0,4)`
- Selected design SHA-256: `5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3`

15A4's conclusion-bearing leverage route used SVD column-space projection with an independent pivoted-QR cross-check. That numerical discipline is now reflected in the accepted 15C QR/SVD repair.

## Preservation / chronology

- Preservation ledger: `docs/history/JEPA_PRESERVATION_LEDGER_20260902.md`
- Historical recovery class: `RECOVERED_HISTORICAL_BYTES__BACKFILLED_20260902`

Git backfill dates are preservation dates, not reconstructed historical dates. Do not upgrade recovered historical bytes into false Git chronology.

## Complete local retrospective

Artifact:
`V4_COMPLETE_EXPERIMENT_AUDIT_FINAL_20260821.md`

Use when a claim cannot be resolved from the compact ACTIVE_STATE, current authority index, current source/contracts, or the current gate packet.

## Machine-readable decision/experiment ledgers

Artifacts:
- `docs/agent/memory-os/DECISION_REGISTRY.csv`
- `docs/agent/memory-os/EXPERIMENT_LEDGER.csv`

Use to check whether an old question is CLOSED / REJECTED / OPEN / SUPERSEDED. A stale historical row must not override the compact live gate, authority index, or supersession map.

## Anchor causality

Relevant historical findings:
- CURRENT vs JEPA_ONLY vs ANCHOR_ONLY u100/u300/u500
- incumbent hidden-RNA anchor rejected
- shared gene-identity movement ~7.618x ANCHOR/JEPA

Open only if proposing any new encoder-side molecular-fidelity loss.

## Molecular fidelity without anchor

Relevant findings:
- online detached reader failed because coordinates moved
- frozen-endpoint observed gene-local reader recovered strong molecular signal

Use when judging whether H has actually lost molecular information.

## Target design

Relevant findings:
- arithmetic block mean can destroy rare/local target information
- multimode/gene-addressed targets retained more rare information in forward audits
- Signed-V2 was biologically richer but conditionally unpredictable and causally harmful
- T0/T1/TCTX local causal bridge found no local winner
- later decoder-free H-space evidence demonstrated strong u0 query-local contextual biology and erosion by T1 u205
- Contextual Target V1 F0 closed PASS under query-self-masked safe semantics

Use for target-semantic decisions.

## Coordinate rotation

Relevant findings:
- fixed/EMA basis made partial online H look much worse
- online self-basis showed near-stability

Use before interpreting representation drift as information loss.

## Rare biology

Relevant findings:
- shared+innovation needed
- core+halo materially improves rare biology
- rare evidence response is nonlinear
- N_eff and physical support matter
- some 1% states become underidentified under masking

Use for rare/uncertainty/evidence qualification.

## Data / measurement semantics

Relevant current authorities:
- 41,238 addresses
- FULL104 reader-fit: 4,553,407 lawful cells / 104 donors / 42 operators
- three physical observation states
- measured zero != structural missing != collision unresolved
- `M_physical` != `U_evidence`
- reader DEV/SEALED/pathology firewall remains closed

Use for loader, masking, evidence, namespace, or population audits.

## Historical Stage81B 4,096 artifacts

Use only as optional mechanism evidence. Never treat as production molecular authority and do not delay production-scope work merely to reproduce the old fixture.
