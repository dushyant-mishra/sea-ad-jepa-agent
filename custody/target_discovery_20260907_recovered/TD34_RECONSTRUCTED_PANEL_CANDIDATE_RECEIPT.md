# TD34 reconstructed panel candidate — byte custody receipt

Status: `CANDIDATE_ONLY__NOT_HISTORICAL_PANEL_AUTHORITY`

Source supplied in takeover chat:

`TD34_RECONSTRUCTED_PANEL_CANDIDATE(1).csv`

Exact source CSV properties:

- bytes: `25033`
- rows including header: `2049`
- data rows: `2048`
- columns: `panel,panel_rank,molecular_address_index`
- line endings: CRLF (`2049` occurrences)
- SHA-256: `c3d706e62b7de5eec67a2aa78f91e376df976038ce7dfc3b6b1106bf39aced2c`

Because the GitHub connector used in this takeover writes UTF-8 text but does not upload arbitrary binary files directly, the exact source bytes are preserved losslessly as deterministic gzip (`mtime=0`) followed by base64 text:

`custody/target_discovery_20260907_recovered/TD34_RECONSTRUCTED_PANEL_CANDIDATE.csv.gz.b64`

Deterministic gzip bytes:

- gzip bytes: `10072`
- gzip SHA-256: `8be0ac60d0504b7327a4005819aeef17c7512f4d78169a95104d6575ae535aaf`

Recovery command:

```bash
base64 -d custody/target_discovery_20260907_recovered/TD34_RECONSTRUCTED_PANEL_CANDIDATE.csv.gz.b64 \
  | gzip -dc > TD34_RECONSTRUCTED_PANEL_CANDIDATE.csv
sha256sum TD34_RECONSTRUCTED_PANEL_CANDIDATE.csv
```

Expected recovered CSV SHA-256:

`c3d706e62b7de5eec67a2aa78f91e376df976038ce7dfc3b6b1106bf39aced2c`

Candidate ordered int32 panel-vector hashes:

- panel 0: `45414005bf84af3d85a2bdd5062f8c00b0163872a2f95848efaa8a55d89f4976`
- panel 1: `c34ec8a677c688501a5b5a4a1ab2d2d02c06610fe9f42e4c94ea973acbe2ce44`
- panel 2: `b7b863962dda2d68ef9c66b0b88d2ad7a0ea1578241b40dc25a3bfc2cf9b7e56`
- panel 3: `df5aa4d410d6f51fbcf7796ced7093d2ad807cca398ce36d9e6512651ef6a0d5`

Authority boundary:

This preserves the candidate manifest bytes exactly. It does **not** prove that these 2,048 addresses are the exact historical TD34 panel membership. Historical panel authority remains open pending the original support NPZ/authenticated equivalent or an independent historical exact panel/pair membership bind.
