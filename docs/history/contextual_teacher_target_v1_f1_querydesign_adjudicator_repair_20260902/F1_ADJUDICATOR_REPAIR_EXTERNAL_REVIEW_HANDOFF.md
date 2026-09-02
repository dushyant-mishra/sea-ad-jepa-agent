# External review handoff

Terminal: `PASS_F1_QUERYDESIGN_ADJUDICATOR_REPAIR_AWAITING_EXTERNAL_REVIEW`.

This is an outcome-blind source repair only. The CSPRNG key, 44,496 assignments, selected queries, PPS design, cell/donor weights, namespace, null map, F0, thresholds, multiplicity rules, evidence levels, nuisance semantics, and claim scope are unchanged.

What changed: exact result completeness now derives from frozen assignment authority; all omission/relabel/extra attacks reject; `qid_win` has an exact domain; v2 is explicitly component-only; and the sole production integration entry revalidates raw records and derives complete-engine endpoints from the same aggregate. All frozen non-query gates remain active through the unchanged hash-pinned v1 engine.

Review the current source snapshot and manifests, especially the independent validator and adversarial report. No real reader/forward execution is authorized. `FROZEN_FORWARD_AUTHORITY_SHA256` and `FROZEN_NUISANCE_AUTHORITY_SHA256` remain unset, so the next real-data gate is still fail-closed.
