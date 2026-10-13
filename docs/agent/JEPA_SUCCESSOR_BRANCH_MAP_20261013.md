# JEPA successor branch map — 2026-10-13

Canonical historical checkpoints:

- PR #322 / `science/jepa-robust-pipeline-post-jepa-anything-audit-20261013` @ `6d6ec998e38b5da5a5281ebba89c471de16f243f` — historical architecture/gene-ID/downstream audit snapshot.
- PR #323 / `handoff/jepa-lane-takeover-20261013` @ `87cd356dd739d12662da14ecc3625ff8d80c21ec` — historical takeover + phase-1 receipt-audit snapshot.

Canonical active successor branches:

- `audit/jepa-lane-successor-20261013` — append-only audit successor; includes cleanly squashed green post-TD harness plus updated audit/custody state.
- `handoff/jepa-lane-successor-20261013` — stacked read-first handoff successor.

Separate scientific/execution lanes that must not be silently modified from these branches:

- PR #313 — real target-tournament executor engineering.
- PR #314 — frozen/spent corrected replay.
- PR #320 — repaired two-phase TD custody/runtime @ `1f474a44a6baabc667dbfda726e0755426c732e7`.
- PR #321 — sealed synthetic V2.1 @ `15f519c00137d581e25232c16be52c2b9badd83e`.

Companion TD/synthetic custody PRs #324/#325 may contain parallel custody/navigation work from the synthetic lane. They do not supersede the lane-specific biological architecture history in #322/#323 or the successor documents here.
