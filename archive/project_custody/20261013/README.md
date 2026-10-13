# Project-custody evidence snapshot — 2026-10-13

Status: `PARTIAL_TRANSPORT_SCRATCH__NON_AUTHORITATIVE__USE_CUSTODY_MANIFEST`

This directory records an attempted convenience copy of project/chat-only non-secret text/CSV evidence. The connector interrupted/blocked the tail of the base64 transport, so these `*.b64.*` fragments are deliberately **not** an authority surface and must not be reconstructed or used as scientific evidence.

The authoritative custody record for project-only material is:

`docs/agent/PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`

That manifest freezes the original filenames, byte sizes, SHA-256 values, custody action and caveats. Large binary datasets/checkpoints and controller-truth bytes were intentionally never copied into this public handoff branch.

The science/governance evidence needed to continue the lane is preserved independently by immutable Git refs and exact non-secret receipts indexed in:

- `docs/agent/TD_SYNTHETIC_CROSSCERT_COMPLETE_TAKEOVER_20261013.md`
- `docs/agent/TD_SYNTHETIC_HISTORICAL_NO_REPEAT_LEDGER_20261013.md`
- `docs/agent/CURRENT_LANE_GIT_OBJECT_INDEX_20261013.json`
- `docs/agent/HISTORICAL_BRANCH_INDEX_20261013.txt`
- `archive/td_synthetic_crosscert_20261013/final/`

Original local convenience bundle identity, retained only for custody matching:

- filename: `PROJECT_CUSTODY_SMALL_TEXT_EVIDENCE_20261013.tar.gz`
- SHA-256: `796b7c246b01ddc78c4768f656a63c22b9dc6610c899e7f6992ef924282de6cb`
- size: 148362 bytes

Do **not** treat the partial base64 fragments in this directory as a valid copy of that bundle. A future agent should consume the GitHub historical refs/receipts first and request/recover a project-custody source file only if a specific unresolved question requires its bytes.

The 50K `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` remains manifest-only because it is large. Its duplicated `sample_row` 0..24999 across A/B halves remains an unresolved row-identity caveat.
