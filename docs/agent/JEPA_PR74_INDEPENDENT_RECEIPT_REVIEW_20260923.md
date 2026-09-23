# Independent receipt review of PR #74 — 2026-09-23

**Scope:** read-only independent GitHub review of `gpu/v5-pr73-metadata-requalification-20260923-claude @ 9073150ffccb6a82f0c114ff3b69940b8c4ca865` (PR #74), based on the exact `f2e227f4f379f637d676c9768acb38bc14151a84` PR #73 producer/qualifier. No heavy FULL104 physical NPZ or metadata blocks are available to this reviewer. Physical SHA and exhaustive metadata results are **producer-side recorded execution evidence**, not locally reproduced here. Do not equate either with N1 runtime authority.

## Independently performed checks (not the producing lane's own claims)

- Independently fetched and parsed the **committed** V2 preflight receipt, six-donor successor receipt, and independent-candidate per-array manifest from PR #74.
- Independently recomputed all **three canonical SHA-256 digests** from sorted-key compact ASCII JSON with each self-digest field excluded, using a separate SHA-256 implementation checked against the standard `abc` digest. Results match the committed receipt fields exactly:
  - Preflight: `cf068ff48dd9af4e5894945dca6a1fce58903363ed41a1a1b440a01406fd5c76`.
  - Six donor: `7046fd3591a06029a87c6c8d51952d092358a34388c1f602a9778bae15453cfb`.
  - Independent candidate manifest: `dcba868a2dc43a4af7b461140a8c50162003d487a46a9a16ca21f8cd8e140bfe`.
- Verified that the preflight binds the six-donor receipt's canonical hash exactly, cites the independently reviewed PR69 manifest canonical hash `4f55158c59d2ee6cdb3ad9276e887126ae78b5b9305021c8c607b524c61293a5`, and binds the original `f77dff47...` and corrected `4b15ee52...` NPZ SHA identities.
- Inspected the committed candidate manifest's **35 per-array rows**: exactly `source_names` and `src_of_cell` are flagged changed, all other **33** unchanged; candidate records the same corrected derivative SHA as the V2 receipts. Distinct candidate and reviewed manifest canonical digests are expected because the candidate path differs.
- Inspected six **distinct** committed sampled donor records: exactly two corrected `HVS`, two `NPH52`, and two `SEA_AD`; all six records claim preserved parent numeric rows/totals, four have corrected text labels. No all-104 raw count reaggregation is claimed.
- Verified preflight records `source_invariant_violations=0`, a concrete `fold_by_donor_sha256=7b472a0f...`, and the `split_donor_source_vector_sha256`; training, expression, masks, burden, and precision remain false/off. The original two disputed *unconditional* summary booleans are absent.
- PR #74 is one **evidence-only** commit over PR #73. Its PR metadata reports mergeable, and the hosted masking workflow completed successfully on the exact evidence head. This hosted run is not physical re-execution by this reviewer.

## Physical observations supported by the independently submitted evidence, not rerun here

The producing lane reports SHA-verified authentication of all 8,915 Level-4 metadata blocks; exhaustive donor comparison of all 4,553,407 cells; exactly-once coverage; a separately rebuilt candidate with identical 363,053,057-byte container SHA `4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b`; and the original `f77dff47...` artifact unchanged. The reviewed manifest and both V2 receipts document this chain without promoting it to N1 execution authority. PR #74 separately reports a negative regression: the original PR62 binder still rejects the unrepaired parent.

## Remaining precise code hardening (not a contradiction of the physical result)

The frozen split receipt already specifies `pass1_npz_sha256=37f79e49f11364daa487ad9e5a5680f72378daf338852765d2f52e1e98d90ba1`, and PR #74's producing lane reports independently hashing the exact physical pass1 file to that value. **However, PR #73's production successor CLI still binds only the pass1 `cell_donor` vector to independently authenticated metadata and checks pass1 `core`/`duniq`; it does not automatically compare the entire pass1 file SHA to the frozen split receipt.** Add this explicit cheap fail-closed comparison and an adversarial test *before the next new physical authority is promoted*. Do not rewrite or silently rebrand the current immutable V2 receipts. Whether it requires a fresh versioned successor receipt depends on the final authority rules, not on this review.

F3 is partially improved by actual producer/qualifier end-to-end synthetic tests in PR #73, but the older PR #69 local-toy tests retain their historical limitations. Count production-gate tests separately from mere toy assertions; do not claim all 48 focused tests are real end-to-end adversarial gates.

F6 was previously a focused static downstream inventory. Independently re-review any **new** crash-safe physical adapter before use; the PR #63 crash-safe engine is outcome-blind infrastructure and is not yet wired to a source-bound physical stream.

## Independent-review terminal

**`PASS_PR74_RECEIPT_STRUCTURAL_AND_CANONICAL_DIGEST_REVIEW__PHYSICAL_EVIDENCE_ACCEPTED_FOR_NEXT_STATIC_ADAPTER_WORK`**

This is a narrow acceptance of the committed V2 evidence's internal consistency and the producing lane's documented physical execution. **It is not** independent local verification of the 363 MB NPZ, all 8,915 metadata files, or 104-donor raw-count reaggregation, and it does **not** authorize N1, masks, rare-tail molecular access, D_shared/G5, clinical outcomes, intervention ranking, or training.

Next work: add full pass1-file binding in a separately reviewed successor; design and red-team PR #63's synthetic-only physical adapter against the corrected source lineage, including clean-vs-interrupted restart equality; retain N1 physical execution behind a separate explicit authority decision.
