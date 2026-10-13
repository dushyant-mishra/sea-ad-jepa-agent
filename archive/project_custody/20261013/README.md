# Project-custody small text evidence bundle — 2026-10-13

This archive preserves project/chat-only **non-secret** text and CSV evidence that was not safely attributable to an immutable GitHub path at takeover time. It deliberately excludes controller-truth bytes and large binary datasets/checkpoints.

Original archive: `PROJECT_CUSTODY_SMALL_TEXT_EVIDENCE_20261013.tar.gz`
SHA-256: `796b7c246b01ddc78c4768f656a63c22b9dc6610c899e7f6992ef924282de6cb`
Original size: 148362 bytes.

GitHub stores the archive as base64 text parts named:
`PROJECT_CUSTODY_SMALL_TEXT_EVIDENCE_20261013.tar.gz.b64.part00` ... `part12`.

Reconstruct exactly:

```bash
cat PROJECT_CUSTODY_SMALL_TEXT_EVIDENCE_20261013.tar.gz.b64.part* | tr -d '\n' | base64 -d > PROJECT_CUSTODY_SMALL_TEXT_EVIDENCE_20261013.tar.gz
sha256sum PROJECT_CUSTODY_SMALL_TEXT_EVIDENCE_20261013.tar.gz
# must equal 796b7c246b01ddc78c4768f656a63c22b9dc6610c899e7f6992ef924282de6cb
tar -tzf PROJECT_CUSTODY_SMALL_TEXT_EVIDENCE_20261013.tar.gz
```

Contents include the local rare-program mining audit/tables, rare synthetic geometry results/hash ledgers, the 41K split-archive checksum manifest, and local historical execution/repair notes. The exact per-file source hashes are in `docs/agent/PROJECT_CUSTODY_ASSET_MANIFEST_20261013.csv`.

The 50K `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` is not embedded because it is much larger; its exact size/SHA-256 and the duplicated `sample_row` caveat are frozen in the custody manifest and takeover/audit documents.
