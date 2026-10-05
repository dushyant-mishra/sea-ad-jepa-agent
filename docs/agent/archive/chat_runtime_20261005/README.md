# 2026-10-05 chat-runtime custody

This directory preserves only runtime bytes not already covered by prior Oct-3/Oct-4 custody, plus the manifest that binds all repeated artifacts by exact size and SHA-256.

New bytes preserved here:

- `Pasted text(20261005-014928).txt` as three base64 parts;
- `v75-2k-promotion-smoke-receipts.zip` as one base64 part;
- `v75-100k-measurement-architecture-receipts.zip` as three base64 parts.

See `CHAT_RUNTIME_CUSTODY_MANIFEST_20261005_V1.json` for exact byte sizes, SHA-256 values, recovery commands, prior-custody bindings, and scope limitations.

The large repeated scientific binaries/checkpoints present in the chat runtime were not duplicated into ordinary Git history because their exact bytes were already hash-bound by prior custody.
