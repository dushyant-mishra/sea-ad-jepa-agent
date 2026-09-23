# PR #63 × corrected FULL104 successor integration contract (synthetic-only)

Status: `DESIGN_ONLY__NO_REAL_N1_AUTHORITY`. Written after PR #74's metadata requalification and independent receipt review PR #75. Do not merge PR #63 wholesale onto an unrelated historical base. Review its exact live head and resolve source-code lineage explicitly.

## Reviewed roots, immutable historical scope

- Quarantined parent NPZ `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae` **must remain rejected** by the old PR #62 binder.
- Corrected derivative NPZ `4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b`, size 363,053,057 B; independent producer rebuild reported byte-identical in PR #74.
- Existing V2 evidence: six-donor canonical receipt `7046fd3591a06029a87c6c8d51952d092358a34388c1f602a9778bae15453cfb`, corrected physical preflight canonical receipt `cf068ff48dd9af4e5894945dca6a1fce58903363ed41a1a1b440a01406fd5c76`. Both mean **review evidence only**.
- Existing split receipt physical SHA `56f045d7dc80fde7e30c97632c1d109286e4b8f9f033b77476521c2822980585`, canonical `5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4`; full frozen pass1 SHA `37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`.
- **No all-104 raw-count reaggregation has been demonstrated.** Six-donor raw qualification and all-104 metadata donor identity are distinct facts.

## Integration seams and required fail-closed behavior

1. New adapter must **not** instantiate old `audit_b_n1_physical_binding_v1.inspect_physical_inputs` as its sole positive authenticator: its frozen `HEAVY_ARTIFACT_SHA256` is still the quarantined parent. Preserve that original binder unchanged as a **negative control**. Implement a new derivative-specific binder that independently checks all input-file SHA identities, both V2 canonical receipts, the reviewed PR69 per-array manifest, `pass1_npz_sha256`, the true all-cell donor-vector digest, canonical `source_names`, exact 104 donor order/source vector, 4-fold source mapping, 17,186-address core order, and available numeric statistic digests. Compare source and donor vectors by full values, not just counts or digests inherited from the caller.
2. Keep `N1DonorTensorAccumulator` and the frozen PR #63 `run_resumable_units`/`finalize_from_journal` as independent mechanics primitives, not data authorities. A source-bound adapter must validate its stream independently before calling either. The new adapter cannot substitute a different source-label lookup or trust a cached old-parent-derived `stream.source_by_donor`.
3. Each journal directory must be bound to an immutable execution-context manifest **before** any unit is committed: corrected derivative SHA; reviewed preflight canonical SHA; code and parameter roots; frozen 256-target order, four-fold assignment, six rung and policy definitions; verified physical stream identity; precise sampling/partner plan; and RNG authority. Resume must verify the entire context manifest; never replay old-parent journal units under the corrected derivative or change an execution design during restart. A self-hashed JSON unit alone does not prove correct dataset lineage.
4. On resume, validate each committed unit's target/fold/rung/target-col and observation schema. Reject wrong donor/source, duplicate or missing observations, extra or malformed unit files, altered context, partial final artifacts, changed frozen target order, and unexpected dtype/shape. Interrupted/restarted and uninterrupted **synthetic** runs must produce byte-identical journal final artifacts and receipts. Include mutation controls where the old and corrected sources have the same source *counts* but different donor assignments.
5. Physical count/molecular streams may be opened **only after a separate future execution gate**. The current task is static and synthetic: never run real N1 target selection, mask generation, burden estimation, precision estimation, rare-tail RNA, clinical outcomes, D_shared/G5 or training merely because metadata preflight passed. Keep policy-effect inference and N1 outcomes sealed.

## Executable synthetic adversaries required before any physical adapter review

- Same source-count but transposed donor-source vector; within-source donor swap, including an unsampled row; stale parent/source-name order and parent NPZ substitution.
- Alternate pass1 file with identical decoded `cell_donor`, `core` and `duniq` arrays but changed NPZ container bytes; mutated split `pass1_npz_sha256` even if the test also patches its split-file SHA.
- Wrong V2 six-donor or preflight receipt, stale PR69 array manifest, nonmatching per-array digest, malformed or absent fold vector.
- Real `run_resumable_units` and `finalize_from_journal` calls with early interruption, clean continuation, corrupted unit digest, *validly rehashed* unit bound to wrong context, extra unit, duplicate donor, stale stage file, and altered code/parameter/RNG context.
- Negative parent regression: the immutable PR #62 binder must still reject the original `f77dff47...` parent.

## Review sequence

First finish this branch's explicit pass1 whole-file SHA check and end-to-end negative tests (PR #76). Once CI and an independent code review pass, inspect PR #63's **live** exact head and implement its successor adapter on a separate descendant or consciously rebased branch with new synthetic fixtures and dedicated fail-closed CI. The independent physical proof in PR #74 need not be redone for purely synthetic adapter development. If any physical receipt is later regenerated with the enhanced source code, version it; do not overwrite V2 or recast old execution as executed by new code.

`AUDIT_B_N1=UNOPENED | MASKS=NONE | BURDEN=NOT_RUN | RARE_TAIL_MOLECULAR=UNOPENED | TD60=UNEXECUTED | PATHOLOGY_DEV_SEALED=UNOPENED | D_SHARED_G5=UNOPENED | TRAINING=OFF`
