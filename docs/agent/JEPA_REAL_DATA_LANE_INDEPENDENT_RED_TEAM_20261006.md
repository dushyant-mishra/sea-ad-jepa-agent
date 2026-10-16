# JEPA real-data lane independent red-team — 2026-10-06

Scope: independent audit of merged PR #220 premise-qualification V3 work for use as the scientific contract underlying the future synthetic qualification rehearsal and later real-data qualification pipeline.

This audit does not reopen PR #220 as invalid governance. It asks a narrower and harder question: is the merged governance package sufficient, by itself, to serve as an executable machine contract for the synthetic rehearsal that is intended to test the future real-data qualification pipeline?

## Audit status

PR #220 remains the controlling scientific/prefreeze governance on `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`.

Hard boundaries remain unchanged: training OFF; Stage A execution OFF; multimodal training OFF; 500K not authorized; Stage 4 not authorized; TEST sealed; Morabito protected; no target winner; no representation winner; no selected estimand; no deciding numeric thresholds.

## What independently survived red-team

The merged V3 package is scientifically careful about several important distinctions:

- target-object recoverability is not automatically biological-truth recoverability;
- four representation families remain open and neutral;
- donor/operator/study/technology transfer are separate axes;
- observation technology is modeled as an observation process rather than an unrestricted identity shortcut;
- biological-evidence convergence and count-depth convergence are explicitly distinct perturbations;
- biological-support OOD and measurement-regime OOD are separate;
- subspace stability is separated from coordinate stability;
- held-donor alignment leakage is explicitly prohibited;
- external does not imply independent;
- same-nucleus and separate-nucleus evidence classes remain distinct;
- cell count cannot substitute for donor count;
- observational regulatory support cannot be promoted automatically to causality;
- Stage A's maximum claim remains RNA_REPRESENTATION;
- synthetic planted-truth recovery cannot promote a real biological claim.

The pre-existing independent review was substantive and found four defects before merge: incomplete hard-state binding, incomplete observation-shortcut binding, stale stability vocabulary, and mixed claim/evidence ladder wording. Those were repaired under RED→GREEN evidence. This new audit does not treat that earlier review as sufficient for the current synthetic-pipeline use case.

## New findings from this audit

### P1 — q-safety is scientifically binding in prose but not machine-bound in the V3 state

The Stage-A contract defines absolute leakage failure transitively: q/the hidden answer or deterministic descendants must not enter through direct values, teacher pre-context, normalization denominator, QC summary, support/missingness, derived features, mask construction, or equivalent descendant channels.

However, `JEPA_PREMISE_QUALIFICATION_V3_STATE_20261006.json` contains no machine-readable q-safety object or transitive leakage-channel roster, and `verify_premise_qualification_v3_surface.py` does not validate one.

Why it matters now: the synthetic world is specifically intended to test the future real-data qualification pipeline for cheating. A synthetic harness could satisfy the current V3 machine state while implementing only the weak rule "hide q from visible tokens" and thereby fail to test normalization/QC/support descendant leakage.

Ruling: do not weaken or modify merged PR #220. Create a successor machine-readable qualification protocol that imports the exact PR #220 governance digest and explicitly binds transitive q-safety channels and oracle/model-visible separation.

### P1 — source-document membership is machine-bound, source-document semantics are not

The machine state freezes the exact roster of binding source-document filenames and CI triggers when those files change. The validator checks the roster, but does not hash or semantically validate the complete content of those documents.

Examples of important semantics that therefore remain prose-level include the full q-leakage definition, detailed representation-family shortcut definitions, exact Stage-A STOP logic, and much of the external-asset role matrix.

Why it matters: #222 now binds the exact V3 JSON digest. That proves the machine state is unchanged, not that every source document still has identical scientific semantics. A later edit to a binding prose document could retain a valid state JSON unless additional tests caught the specific drift.

Ruling: the successor executable qualification protocol should bind its own exact semantics and the exact PR #220 governance digest. For any PR #220 prose rule promoted into executable pipeline behavior, encode that rule machine-readably rather than relying only on source-document membership.

### P1 for convergence, not a defect in PR #220 — PR #220 is governance, not a complete executable QualificationProtocol

The merged state intentionally leaves important execution choices unresolved:

- exact biological-evidence fractions;
- exact depth fractions/thinning operator details;
- selected estimand;
- deciding numeric thresholds;
- winner adjudication across representation families;
- potentially the final biological resampling unit if a later estimand authority changes it.

That was correct for prefreeze governance. It means Macha/Claude must not silently choose these values in the synthetic rehearsal and then imply the real-data lane authorized them.

Ruling: create a separate synthetic-rehearsal protocol with explicit status for each field: inherited/frozen from PR #220, synthetic-only diagnostic choice, or unresolved for future real-data authority. Synthetic-only choices must not back-propagate into real-data scientific authority.

### P2 — representation-family names are machine-bound more strongly than their executable semantics

The V3 machine state exactly freezes the four family names, but the detailed meanings and shortcut risks of GLOBAL_CELL_STATE, QUERY_LOCAL_STATE, PROGRAM_STATE, and STRUCTURED_COMBINED_STATE are primarily prose-defined.

For the synthetic rehearsal, the executable extraction definition for each candidate must therefore be frozen separately before optimization. Otherwise two implementations could both claim `PROGRAM_STATE` while constructing materially different objects.

Ruling: the successor QualificationProtocol must carry explicit extraction/target/view definitions or immutable references/digests for the implementation under test.

### P2 — donor-primary resampling and estimand neutrality must not be conflated

PR #220 makes donor the primary biological resampling unit for representation stability, while keeping the foundation-population estimand unset and allowing a later estimand authority to select a different unit where justified.

This is not internally contradictory, but a synthetic pipeline could accidentally turn donor-weighting into an implicit selected estimand.

Ruling: distinguish `biological_resampling_unit` from `population_estimand` in the synthetic protocol. The former may inherit DONOR for stability diagnostics; the latter remains UNSET unless explicitly synthetic-only and non-authorizing.

### P2 — 41,238-address identity authentication is outside PR #220 and remains independently required

PR #220 does not close the historical registry/order/reader/tokenizer/tensor identity problem, nor should it be treated as having done so.

For the future shared qualification pipeline, both real and synthetic adapters must emit authenticated feature identity. Real-data execution must prove registry -> ordering -> reader/index mapping -> tokenizer -> model tensor. Synthetic execution should use an explicit synthetic registry/identity map rather than shape-only compatibility.

Ruling: add identity-chain fields/tests at the adapter/pipeline boundary; do not modify PR #220 to pretend this was already qualified.

## No P0 found in the audited governance logic

This audit did not find a current P0 that invalidates PR #220 as merged scientific/prefreeze governance. The new P1 findings are about using PR #220 as an executable pipeline contract without a successor machine layer.

## Consequence for the synthetic rehearsal

Do not feed V77/S127 directly into a runtime consumer using only the PR #220 state JSON.

The correct layering is:

1. exact merged PR #220 governance digest;
2. a new machine-readable `QualificationProtocol` that binds the executable scientific semantics required by the rehearsal without selecting unresolved real-data science;
3. `QualificationBatch` shared by synthetic and future real adapters;
4. separate `SyntheticOracleTruth` object that cannot reach the model-facing batch;
5. the single converged #221/#222 runtime consumer;
6. common qualification metrics plus synthetic-only oracle diagnostics.

## Required RED tests before Macha/Claude synthetic optimization

At minimum:

- q removed from visible tokens but leaked through normalization denominator -> FAIL_LEAKAGE;
- q removed from tokens but leaked through detected-feature/QC/support summary -> FAIL_LEAKAGE;
- oracle-only latent copied into model-facing batch -> structural failure;
- representation-family label with altered extraction semantics -> protocol digest mismatch/fail closed;
- biological-evidence schedule implemented by count thinning -> contract failure;
- depth schedule changes feature/support universe -> contract failure;
- synthetic-only estimand/fraction choice incorrectly presented as inherited real-data authority -> contract failure;
- same-shape 41K tensor with wrong identity mapping -> identity-chain failure;
- protected/real external assets referenced by synthetic target selection -> failure.

## Overall verdict

PR #220 is acceptable as the controlling scientific/prefreeze governance package within its declared scope.

It is not, by itself, sufficient as the executable contract for the synthetic rehearsal that is intended to validate the future real-data qualification pipeline.

The right repair is prospective composition, not retroactive rewriting: preserve PR #220 unchanged, bind its exact governance digest, and create a new machine-readable QualificationProtocol that closes the executable semantics required for synthetic testing while keeping unresolved real-data decisions explicitly unresolved.
