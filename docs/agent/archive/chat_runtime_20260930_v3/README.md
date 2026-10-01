# Chat-runtime custody — 2026-09-30 V3

This is a **delta** on top of `chat_runtime_20260930_v2`.

It exists because this chat accumulated new audit material after the V65 handoff, especially Claude's Phase-B B1–B5 closeout and the uncommitted/local B6 availability attempt.

## New material committed here

- `Claude_B1_B6_runtime_transcript_20260930.md` — full current uploaded transcript brought directly from the Files surface. Treat it as evidence/history, not repository execution authority.
- `Prior_runtime_handoff_snapshot_SUPERSEDED.txt` — readable historical runtime handoff snapshot. Its execution status is obsolete.
- `independent_dual_ledger_audit.py` — chat-local promoter-ledger audit helper preserved for reproducibility.
- `CHAT_RUNTIME_EXCLUSIVE_ASSET_CUSTODY_20260930_V3.json` — exact source sizes/SHA-256 values and classification.

## Do not duplicate Project-backed files

The runtime also mounted `WSL execution issue.txt`, `Status and Repair Plan.txt`, and the discovery split checksum CSV. Files retrieval shows these are Project-backed; V2 already preserved the small text/checksum material, so V3 does not create another copy.

## Large binary rule

The runtime contains foundation archives, checkpoints, expression artifacts and downloaded GitHub Actions artifacts. Do not assume these bytes are in Git. V2/V3 record size/SHA and recovery/custody status. GitHub Actions downloads are not considered chat-exclusive scientific sources.

## Current authority

This archive is subordinate to the current V66 handoff/state and committed scientific/audit receipts.

The key current boundary is:

- Phase A V3 accepted at 13,175.
- Phase-B B1–B5 accepted at Claude `154935c5`.
- B6 per-element T3/T4 availability is still blocked pending executable proof/custody fixes in `results/v64/V64_PHASE_B_B6_AVAILABILITY_PRECOMMIT_AUDIT_V1.json`.
- Stage 4 sealed.
- Real training OFF.
