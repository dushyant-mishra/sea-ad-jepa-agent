# GSE178317 V2 count-binding successor — 2026-09-24

Status: SOURCE/EXECUTION HARDENING FOR FUTURE REISSUE. No new physical result is claimed.

Claude's current DEVELOPMENT result remains recorded at PR #77. This successor does **not**
erase or reinterpret those measurements. It closes a provenance/runtime gap for the next
physical reissue:

- full count stage must use the reviewed sgRNA library bytes and reviewed four GEX H5 roots;
- bounded/smoke count receipts cannot feed the call stage;
- call stage requires the exact count-stage receipt and NPZ SHA;
- NPZ loading is `allow_pickle=False`;
- identity arrays must be plain strings, matrix counts nonnegative integers, geometry and total
  UMI count must match the receipt;
- count and call outputs refuse occupied paths.

The already-produced physical count NPZ predates this safe-format contract and therefore cannot
satisfy it without a clean versioned reissue. That is a provenance-hardening requirement for
promotion beyond the current DEVELOPMENT scope, not a claim that Claude's current DEVELOPMENT
point estimates are wrong.

TRAINING=OFF. PROSPECTIVE_CONFIRMATION=OFF. THERAPEUTIC_RANKING=OFF.
