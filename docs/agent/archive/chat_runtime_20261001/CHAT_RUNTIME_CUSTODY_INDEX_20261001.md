# Chat runtime custody index — 2026-10-01

This directory contains the exact small-file artifacts that were physically present in the ChatGPT runtime during the October 1 custody pass, plus a manifest for every runtime file.

## Verbatim small-file bundle

`CHAT_EXCLUSIVE_SMALL_FILES_20261001.zip` contains these files exactly as supplied to the runtime:

- `Pasted text.txt`
  - raw Macha/Stage-4/SCENIC+ execution transcript and handback material
- `Pasted markdown.md`
  - later SCENIC+ speed-cycle / Stage-4 execution transcript and handback material
- `Status and Repair Plan.txt`
  - historical project status/repair artifact supplied to this runtime
- `WSL execution issue.txt`
  - historical WSL/architecture discussion artifact supplied to this runtime
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
  - supplied checksum inventory for the split foundation discovery expression archive

Bundle identity:

- bytes: 78,034
- SHA-256: `bc04cb8e534c3ba94d1e5ffdb6e67773a198bde92b212c62376d152c9f51f2c0`

## All-runtime-file manifest

`CHAT_RUNTIME_BINARY_CUSTODY_MANIFEST_20261001.json` records exact bytes and SHA-256 for every file physically present in `/mnt/data` at custody time, including large binary scientific assets deliberately not committed to Git.

## Interpretation rule

Raw pasted transcripts contain time-local process observations, intermediate SHA heads, errors, retractions and superseded claims. They are evidence/history, not a canonical current-state document. Use `../../JEPA_CHAT_EXCLUSIVE_CUSTODY_AND_HANDOFF_20261001.md` for the interpreted handoff, and re-query GitHub for current branch heads before execution.
