# MANDATORY_IMPLEMENTATION_VERIFIER_V1

Status: `FROZEN_PROJECT_GOVERNANCE`. This authority is permanent across JEPA phases and sessions until an explicit, prospectively reviewed supersession takes effect. It has no gate-based expiration.

IMPLEMENTATION VERIFICATION OCCURS BEFORE EXPENSIVE COMPUTE.

Any conclusion-bearing code requires the sequence: Authority/Historian → Implementer → independent Implementation Verifier (veto) → specialist reviews → expensive compute/scientific promotion. The implementer may report only `IMPLEMENTATION_COMPLETE_AWAITING_INDEPENDENT_VERIFICATION`; only the independent verifier may issue `PASS_IMPLEMENTATION_VERIFIER`. A substantiated verifier STOP cannot be overruled by majority vote.

Conclusion-bearing scope includes scientific endpoints, aggregation, selection/null/query/evidence-mask/stopping/threshold/inference rules, donor/cell/program weighting, dataset-derived dimensions or parameters, sufficient statistics, cache/dedup identities, shard reconciliation, provenance roots, firewalls, resource rules affecting completeness, and any code capable of changing a scientific PASS/STOP.

The verifier receives only the controlling frozen contract, authority hashes, base and implementation commits/diff, changed files, exact relevant reference code, tests, and bounded synthetic/technical fixtures. It does not reread project history unless authority ambiguity exists. For each requirement it records the exact contract, production behavior, independently reconstructed expectation, and deliberate detected mutation. It may not import/call the conclusion-bearing production helper, copy production outputs/gates/reports, or accept implementer PASS assertions as expected values. Verifier-written adversarial tests are mandatory.

Allowed terminal is `PASS_IMPLEMENTATION_VERIFIER`, or one of the frozen `STOP_IMPLEMENTATION_VERIFIER_*` terminals in the policy. Any STOP blocks expensive compute, production sweeps, promotion, and merge to main.

Persistent handoffs must carry:

- `implementation_verifier_required = true`
- `implementation_verifier_veto = true`
- `implementation_verifier_runs_before_expensive_compute = true`
