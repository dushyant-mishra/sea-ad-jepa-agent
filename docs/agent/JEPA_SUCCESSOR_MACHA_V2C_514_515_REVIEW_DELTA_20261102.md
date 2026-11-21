# Successor pointer delta — Macha V2C reviews, 2026-11-02 (append-only)

This adds to `JEPA_NEW_AGENT_LIVE_POINTER_20261029.md` (live head `d9949d633c0522338f50ec1bcc7ceea82241e072`) without editing it. The full record is on audit #322: `docs/agent/JEPA_MACHA_V2C_514_515_REVIEW_DELTA_20261102.md`.

## Current audited implementation and review status
| Implementation | Head | Independent review | Fixture consistency |
|---|---|---|---|
| #514 standalone V2C | `63099f6b17b14bcfcfd92b0334bf564e9cf8376d` | [#516](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/516) at `881194aec9d99a9d42cbf206ffcb779429c4e768` | **`REPAIR_REQUIRED`** (4 RED) |
| #515 D1 → V2C | `fa06d486d5f8a130ff545690a8f0b12773c4f85d` | [#518](https://github.com/dushyant-mishra/sea-ad-jepa-agent/pull/518) at `32c0a22b9ae6220ed03fe7d6e944da753c0e4a0c` | **`ACCEPT_SCOPED`** for the composition delta only; the head inherits #514's repair |

These verdicts apply to both PRs:
- Student runtime isolation: `NOT_TESTED`, recorded as `STUDENT_PROCESS_ISOLATION_NOT_YET_DEMONSTRATED`. No deployment artifact exists.
- Source-rights authentication: `NOT_AUTHENTICATED`.
- Real human-source issuance: `BLOCKED`.

The #507 and #512 RED tests are preserved unchanged and still fail at #514, because the #502 and #510 modules are untouched.

## What the next agent does
1. **ChatGPT repairs only the V2C entry guard, on a new head:**
   - require exact-`str` top-level keys before any lookup;
   - read the role once;
   - re-check the role on the snapshot.

   Then rebase #515 onto that head. Do not edit #516, #518 or any historical RED file.
2. **Macha rechecks.** The repaired head is rechecked with #516 unchanged, and the rebased #515 with #518 unchanged.
3. **External owners.** Two owners must act; neither may be satisfied by a self-signed key, a receipt or a launch flag:
   - the student-runtime owner provides a deployment artifact that enforces the filesystem and process boundary;
   - source governance provisions `JEPA_SOURCE_RIGHTS_ISSUER`.
4. **Do not treat these as qualified:**
   - an author CI pass;
   - a V2C consistency receipt, which is an unkeyed, mintable digest;
   - the `-I -S -B` packaging launch.

## Unchanged
These decisions stand:
- D1 selected and D2 excluded;
- the provisional alias table, which is **not enforced** by V2C or D1 → V2C, since the policy has no alias field;
- NPH52 quarantined;
- SEA-AD `sample_id` is nucleus-level;
- no issuer key.

There is no target winner, no representation winner, no Stage 4 and no training.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
