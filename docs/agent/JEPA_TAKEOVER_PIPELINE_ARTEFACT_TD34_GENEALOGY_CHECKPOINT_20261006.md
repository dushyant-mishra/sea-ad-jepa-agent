# JEPA takeover checkpoint — PIPELINE_ARTEFACT_m and TD34 genealogy

Date: 2026-10-06
Branch: `audit/td34-genealogy-s149-20261006`
Parent handoff observed before write: `a8b1057ea00babf163109fe588f86b940db5d43f`
Status: `DOCUMENTATION_ONLY__FAIL_CLOSED`

## Scope

This checkpoint continues the audited V64/V74/S149 handoff. It does **not** authorize or execute training, Stage A, Stage 4, real NIH-CARD biological correspondence, TEST, Morabito, target selection, representation selection, or new TD41 outcome analysis.

Two questions were audited:

1. Was the prospectively required `PIPELINE_ARTEFACT_m` CONTROL_A-vs-CONTROL_B discrimination experiment ever established strongly enough to close S102/G2?
2. Can the four deterministic 512-gene TD34 panels used downstream by TD41 be genealogically cleared under S149?

## A. PIPELINE_ARTEFACT_m archaeology

### Primary evidence recovered

The V74 full Macha audit at commit:

`785a45972fed3ea896d2209058e2860ef115fc2d`

file:

`docs/agent/V74_MACHA_FULL_AUDIT_FINAL_20261003.md`

states in M-A12 that the G2 successor contract remained:

`FROZEN__NOT_IN_FORCE__DECIDING_MARGIN_UNSET`

and records that the discriminating `PIPELINE_ARTEFACT_m` experiment was specified but not run, with no real substrate read and no real correspondence values computed.

M-A13 is even more specific: the existing planted synthetic worlds put signal on linked intervals only and **do not plant CONTROL_A-vs-CONTROL_B asymmetry**. They can therefore test the false-alarm half of G2, but not whether G2 detects the pipeline artifact it is supposed to police.

The G2 successor head audited there is:

`claude/v74-g2-continuous-successor-20261002`
@ `03c0c48612860e4bd2f094ce54fdef9cde274490`

The later S102/G2 PASS/hash-equivalence lineage was inspected as historical material, but no recovered evidence supersedes the V74 audit with a prospectively frozen, positive-control `PIPELINE_ARTEFACT_m` CONTROL_A-vs-CONTROL_B discrimination run and predefined deciding margins.

### Decision

`S102_G2_NOT_CLOSED__PIPELINE_ARTEFACT_M_DETECTION_HALF_UNQUALIFIED`

This is stronger than merely saying that the old K-curve was withdrawn. The blocker is identifiability of the intended artifact detector itself.

Consequences:

- G2 remains `NOT_IN_FORCE`.
- Stage 4 remains `NOT_AUTHORIZED`.
- real NIH-CARD biological correspondence remains `UNOPENED`.
- no historical S102/G2 PASS label is sufficient authority unless a future audit can produce the exact prospectively frozen artifact-world protocol, positive and negative controls, deciding margins, result receipts and supersession chain.

This audit did not compute any real NIH-CARD correspondence.

## B. TD34 512-gene panel genealogy

### Historical anchor

The TD34 closure enters repository history at commit:

`ff85f5bb18dc7d438113c3a5662856a360d2cd8f`

message:

`target-discovery: close TD30-TD36 and freeze new-chat handoff`

That commit preserves:

- `target_discovery/HANDOFF_CURRENT_20260907.md`
- `target_discovery/iterations/TD30_TD36_CLOSURE_LEDGER.md`
- `target_discovery/iterations/td34_state_geometry_globalrow/TD34_SUMMARY.csv`

The closure ledger describes TD34 as using:

- four 512-gene common-scalar panels;
- 19 outcome-blind/pathology-blind states shared by HVS/SEA_AD;
- the corrected global-row guard;
- a local TD34 script SHA-256:
  `1e26f37b760ea049a7b342d7c37229c849f26042871db1c815090f6a6dc5b566`.

The repository-resident TD34 directory at the inspected historical ref contains only `TD34_SUMMARY.csv`. The closing commit preserves the **script digest**, but not the actual TD34 producer script, panel membership manifests, or a provenance receipt sufficient to reconstruct panel membership and its selection inputs.

### Downstream TD41 does not solve the missing genealogy

At historical ref `54f67f5cd5138c47311e95441b4895076ffb7bfc`, `TD41S_PROSPECTIVE_FREEZE.md` explicitly says:

`Use the same four deterministic 512-gene TD34 panels.`

TD41 then deterministically hashes **pairs within those already-fixed panels** and forbids pair selection by expression/state/outcome. That protects the TD41 pair sampler, but it does not establish how TD34 selected the 512 genes in each panel.

Therefore later TD41/TD43 source-stratified, donor-balanced and wrong-cell-controlled analyses cannot retrospectively prove that TD34 panel membership was S149-safe.

### What is known versus missing

Known for the four TD34 panels as a family:

- panel width: 512 genes;
- number of panels: 4;
- described as deterministic/common-scalar;
- TD34 states were outcome-blind and pathology-blind;
- global-row addressing was corrected by TD33;
- downstream TD41 reused the panels unchanged before hashing 4,096 within-panel pairs.

Not recoverable from the inspected repository authority:

- exact per-panel gene membership;
- exact producer bytes matching the recorded script SHA;
- exact input candidate population used by that producer;
- exact gene-selection statistic/ranking/hash rule;
- whether source/study-pooled covariance, topology, detectability or composition affected membership;
- whether panel construction was source-independent or repeated within source;
- exact common-support construction used for membership rather than later evaluation;
- an independently checkable freeze chronology for the panel memberships themselves;
- train/test provenance of panel construction beyond the high-level falsification-only 50k archive boundary recorded in the closure handoff.

No evidence recovered in this audit shows outcome/pathology information selecting panel membership; however outcome blindness is not sufficient to answer the S149 measurement-composition question.

### Fail-closed classification

Because the primary producer and panel manifests needed to decide the S149 question are missing from repository authority, all four panels receive the same current classification:

| panel | classification | reason |
|---|---|---|
| TD34 panel 1 (512 genes) | `INDETERMINATE__PRIMARY_PROVENANCE_MISSING` | producer/membership/source-handling provenance not repository-recoverable |
| TD34 panel 2 (512 genes) | `INDETERMINATE__PRIMARY_PROVENANCE_MISSING` | same |
| TD34 panel 3 (512 genes) | `INDETERMINATE__PRIMARY_PROVENANCE_MISSING` | same |
| TD34 panel 4 (512 genes) | `INDETERMINATE__PRIMARY_PROVENANCE_MISSING` | same |

Do **not** upgrade these to `S149_SAFE__SOURCE_INDEPENDENT_OR_WITHIN_SOURCE` merely because TD41's downstream analysis is source-stratified.

Also do **not** classify them as proven `S149_RISK__POOLED_MEASUREMENT_COMPOSITION_COULD_SELECT_GENES` without the missing producer. The correct current result is indeterminate, not guilt by association.

### TD41 consequence

`TD41_REMAINS_SCIENTIFICALLY_INTERESTING__UPSTREAM_PANEL_GENEALOGY_NOT_CLEARED`

No new TD41 biological outcome analysis should be run from this branch until one of the following happens:

1. the original TD34 producer bytes and the four panel manifests are recovered and content-bound to the historical script digest/freeze; or
2. TD41 is prospectively re-expressed using a new S149-safe panel construction that is source-independent or fit within observation process and then transported across observation process, without consulting protected outcomes.

Option 2 would be a **new prospective experiment**, not a retroactive validation of historical TD34.

## C. Repository topology / collision guard

Immediately before this documentation write, the audit branch still pointed to:

`a8b1057ea00babf163109fe588f86b940db5d43f`

Open runtime work also exists, including draft PR #224:

`reconcile/canonical-v5-runtime-successor-20261006`

This checkpoint does not modify or claim authority over that runtime lane.

## D. Updated scientific boundary

The takeover therefore advances two archaeology questions to explicit fail-closed states:

1. `PIPELINE_ARTEFACT_m`: no qualified execution recovered; G2/S102 remain open/not-in-force; Stage 4 stays closed.
2. TD34 genealogy: four 512-gene panels cannot currently be cleared under S149 from repository-resident primary provenance; all four are `INDETERMINATE__PRIMARY_PROVENANCE_MISSING`.

Everything else from the audited handoff remains binding, including:

- Training OFF.
- Stage A OFF.
- Stage 4 NOT AUTHORIZED.
- Real NIH-CARD correspondence UNOPENED.
- Morabito protected.
- TEST sealed.
- no qualified target winner.
- no qualified representation winner.
- authoritative Phase-A eligible population remains 13,510, not 15,646.

## Next safe archaeology action

Search for the local handoff package identified at the TD34 closure:

- `JEPA_TARGET_DISCOVERY_NEW_CHAT_HANDOFF_20260907.zip`
  SHA-256 `d0b883ff798e94933b5e8aade3845551fad0b23d51451b01a59230476a7c59e4`
- embedded markdown SHA-256
  `5f49bf4072b44c8f1a269be86d299fb0157a6cf2a923040d2dbe348126af09b1`

The historical closure says this package contains corrected outputs/scripts and large-artifact hash manifests. If the TD34 producer and panel manifests are recoverable anywhere, that package is the most specific provenance lead found so far.

Until those bytes are recovered and authenticated, preserve the indeterminate classification and do not reopen TD41 outcome analyses.