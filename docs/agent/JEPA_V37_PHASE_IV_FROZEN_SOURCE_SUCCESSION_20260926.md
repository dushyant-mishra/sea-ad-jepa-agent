# V37 Phase-IV frozen planner provenance — read-only audit

Date: 2026-09-26. **NON-AUTHORIZING.** Stacked on PR #144 at `21efb1047c73cfe7b88047f0aeee1978b035971f`. Training OFF; Audit-B N1 and all protected outcomes unopened.

## Historical investigation and root cause

The September 21 immutable `AUDIT_B_FROZEN_TARGET_SAMPLE.json` captured the 7 pre-outcome bound files, including `planner_source` at SHA-256 `143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d`. PR #144's current checkout carries a newer `full104_masking_streaming_executor_v1.py` at `de2f019e28675e3258cfeede65f77557210f5fcd083f94ae09f97b1c8629f9f8`; historical CI failed 5 cases because it correctly detected this conflict. The source change is not an environment malfunction or necessarily a failure in the frozen sample: G3 commit `65ff187c9668cf0af28056222fde897380929141` added explicitly optional alternative fit masses and donor-matched ridge paths to the same source file. The earlier Sept20 LF-normalized predecessor commit is `2ebfd6ad52b0e2a99a4917391d3f0d97a667d79b`.

The accompanying `audit_phase_iv_source_succession_v37.py` physically reads both versioned source blobs with `git show` and verifies their actual SHA-256 values, rehashes all seven current original bound inputs, recomputes the *immutable* original sample-receipt digest, verifies only the planner source changed, and checks the changed source exposes G3 as opt-in with a `None` default. It does NOT equate a source-level default signature to a measured CPU/GPU numerical parity result.

## Safe succession policy

- **Original freeze remains immutable.** Do not patch the Sept21 digest, replace the original file under the same claim, or suppress the existing 5-failure regression to make PR #144 appear green.
- The historical predecessor bytes (and original frozen target list) may be used *only* on their own exact historical runtime source. New G3 opt-in source requires a **separately named successor pre-outcome freeze** with new parent-source SHA, all seven independently rebound root files, full-source lineage comparison and prospective signoff before any Audit-B N1 result is opened.
- Frozen target selection is SHA(salt|target_address) and independent of burden outcomes. Reuse of target IDs alone does not imply runtime equivalence; compare source semantics and replay synthetic/parity controls before promoting a successor.
- Neither the new read-only audit nor green CI authorizes a successor sample freeze, N1, current masking-policy qualification or production training.
- V30→V34→V36 issuer/guard provenance is a separate chain, and V32→V35 teacher-target archive replay is separate non-authorizing historical research.

## Status

Audit B original on PR144: `BLOCKED_BY_VERSIONED_PLANNER_SOURCE_MISMATCH`. Do not treat the five legacy failed tests as a new scientific negative result or as justification to widen tolerances. The V37 workflow tests original source lineage and expected freeze invalidity only; PR144's original masking workflow may remain RED until a separately approved successor changes the bound source semantics.
