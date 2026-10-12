# Target discovery — current G7 gate

Replacement G6 at exact executable head `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0` remains externally accepted.

External G6 disposition:

`ACCEPT_G6_PASS__VALUE_SUBSTRATE_AND_SOURCE_CUSTODY_CONFIRMED__NO_BIOLOGICAL_TARGET_AUTHORITY`

Accepted G6 evidence:
- evidence branch `evidence/td-g6-replacement-ff4a21f9-20261011`
- evidence commit `c595af589821bee28eb77e88e44b79dc81835e7a`
- receipt terminal `PASS_TD_G6_SOURCE_LIBRARY_EXACT`
- G6 receipt SHA-256 `2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b`
- values SHA-256 `fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9`
- metadata SHA-256 `bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74`

## G7 at ff4a21f9: pre-marker code failure

Evidence branch:
`evidence/td-g7-attempt-ff4a21f9-20261012`

Evidence commit:
`9ab5421169971012f0c358bc3c714e6afcabfca2`

External classification:

`G7_FF4A21F9_PREMARKER_IMPLEMENTATION_FAILURE__ATTEMPT_UNSPENT__SUCCESSOR_REQUIRED__NO_BIOLOGICAL_AUTHORITY`

The authorized G7 launch at `ff4a21f9...` passed its precondition hashes and pre-marker S174/cache/source checks, then crashed before `begin_g7_attempt` with:

`AttributeError: 'DataFrame' object has no attribute 'global_row'`

No G7 start marker, receipt, or output namespace was created. The accepted G6 namespace and historical failed G6 namespace remained unchanged and the worktree remained clean. Therefore the immutable one-shot G7 execution marker was never spent, but `ff4a21f9...` is not executable for G7 and must not be rerun.

Root cause: G7 has its own `select_sample_a()` implementation. Unlike the repaired G6 selector, G7 filters/sorts the authenticated Sample-A freeze without first deriving historical `global_row` from freeze-file row position. The real freeze does not physically contain `global_row`. The prior real-file qualification gate exercised only G6's selector and therefore did not expose this defect.

The earlier G7 operational authorization SHA `19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee` is now historical evidence only for the failed pre-marker launch and must not be reused for a successor.

## Required successor sequence

1. Create a new executable successor from the accepted `ff4a21f9...` lineage.
2. Add a RED regression test proving G7 derives `global_row` from original freeze-file row position before filtering/sorting, matching the historical TD33 rule.
3. Repair G7's selector with the minimal production change. Do not weaken G6 or shared custody checks.
4. Add a real-file qualification gate that executes G7's own pre-marker path against the authenticated Sample-A freeze and accepted G6 metadata, while preventing any G7 start marker or biological replay.
5. Fresh qualification must bind the new exact head, run the focused suite green, pass G6 real-file compatibility, pass G7 real pre-marker compatibility, verify accepted G6 hashes, and leave the worktree clean.
6. Stop for external audit of the successor qualification.
7. Only after qualification acceptance create fresh successor-specific owner/runtime/operational authority and run G7 once in a fresh output namespace.

No corrected TD56/57B/57C/59 replay is authorized yet. TD60, target selection, representation selection, Stage4 and training remain blocked.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
