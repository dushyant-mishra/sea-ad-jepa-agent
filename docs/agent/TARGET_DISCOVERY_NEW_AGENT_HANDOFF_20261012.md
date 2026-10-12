# Target Discovery — New-Agent Cold-Start Handoff — 2026-10-12

Status: **TAKEOVER READY — NON-AUTHORIZING**

Hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This is the shortest safe entry point for a future agent. It exists to prevent historical re-auditing, duplicate implementation, and accidental promotion of superseded evidence.

## Read order

1. `docs/agent/TARGET_DISCOVERY_MASTER_AUDIT_INDEX_20261012.md`
2. `docs/agent/TARGET_DISCOVERY_DUPLICATION_SUPERSESSION_LEDGER_20261012.md`
3. `custody/takeover_20261012/TARGET_DISCOVERY_CURRENT_TAKEOVER_STATE_20261012.json`
4. `custody/takeover_20261012/TARGET_DISCOVERY_PR_BRANCH_INDEX_20261012.csv`
5. `docs/agent/TARGET_DISCOVERY_MASTER_HANDOFF_20261011.md` only when deeper historical narrative is needed.

Do not begin by reconstructing TD history from scratch. The audit index tells you which historical artifact is canonical, superseded, failed, spent, or still live.

## Current lane ownership

### Macha owns corrected biological replay implementation

Live implementation:
`feat/td-corrected-replay-turnkey-20261012@f74632ed51a0ffc28ac46daf240debbb8c2d6e01`

Live launch-authority package:
`authority/td-corrected-replay-launch-f74632ed-20261012@635f9f00050234f4e90306e97bce131bf741d73c`

At this handoff freeze:
- corrected biological replay has not run;
- Macha's canonical historical-fixture equivalence is 16/16 exact;
- replay-only authority exists;
- execution still requires exact external launch-audit acceptance plus the required decision-ratification record;
- no downstream target/TD60/Stage4/training authority exists.

**Do not implement another corrected-replay launcher/controller.**

The audit chat accidentally did that once on `science/td-corrected-replay-turnkey-20261012`. That branch is quarantined reference-only and must not be continued or merged.

## G6/G7 state — already audited

Accepted G6 producer:
`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

G7 successor implementation:
`8d41fb9838b425ddcb704ecbdf5cd51f3eeb9f27`

G7 was executed exactly once and returned:
`NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`

It is not a PASS.

Independent metadata diagnostic:
`diag/td-g7-cell-id-namespace-20261012@0b50938e48f7c257b362a0c66899bc1caa0d27a1`

classified the cell sets:
`GENUINELY_DISJOINT_NATURAL_CELL_SETS`

The zero overlap is structural: S174 samples T1 encoder-fit cells; discovery Sample A explicitly excludes T1 cells. Therefore the corrected-replay technical prerequisite is prospectively closed without converting G7 into PASS.

Do not rerun G7 and do not repeat the ID-format diagnostic.

## Exact next task for this lane

Audit Macha's exact corrected-replay implementation and authority package. Specifically resolve/verify the package's two open decision points, bind all physical hashes, and decide whether to issue an external launch-audit acceptance for exactly one corrected-replay attempt.

If accepted, Macha executes corrected TD56/57B/57C/59 once. Then this lane audits the resulting evidence before any real target tournament execution.

## Frozen corrected-replay interpretation

- TD56 FAIL -> stop relational promotion.
- TD56 PASS + TD57B FAIL -> donor-recurrent scale-free order not confirmed.
- TD56 PASS + TD57B PASS + TD57C FAIL + TD59 PASS -> historical-scale relational bracket survives.
- TD56 PASS + TD57B PASS + TD57C FAIL + TD59 FAIL -> broad/global scale-free relation survives; mesoscale locality not confirmed.
- corrected TD57C PASS -> historical/corrected divergence; new prospective locality experiment required.
- source disagreement is not averaged away.
- NOT_ESTIMABLE never becomes biological PASS.

Do not change thresholds/statistics/locality after seeing corrected outcomes.

## Target tournament state

Canonical prospective decision machinery is PR #275 / `science/td-target-tournament-scaffold-20261011`.

Foundation candidates:
- C1 shared emergent
- C2 relational shared
- C3 query measured
- C6 shared+query composite
- C4 shared+relational+query composite
- C5 regulatory specialist only

The current scaffold already contains corrected-replay routing, candidate dependencies, protected pairwise comparison, V79 target crosswalk/binding, C6 extension and final zero/one/many convergence logic. Do not write a second routing/convergence stack.

## Synthetic state

Q00-Q11 are physically realized and independently byte-audited. Target discovery is bound to PR #297 / `bb892356...` realization evidence.

Do not regenerate the worlds in this lane. Synthetic PASS cannot select a human target. Current V79 does not estimate every biological latent-target claim.

## Important historical errors already caught

- reset/sample-local row aliasing -> global freeze-file row must be assigned before filtering/merge;
- Windows CRLF manifest bytes changed authority hashes;
- literal Sample-A label mismatch (`A` versus `A_NATURAL_MIXTURE`);
- 35 physical H5AD files versus 34 occupied Sample-A matrices;
- first real G6 attempted to rely on absent physical `global_row`;
- original G7 omitted G6's historical-row derivation;
- G7 overlap test was structurally impossible because its two cell sets were disjoint by construction;
- Bayesian historical-replication spike was prospectively `SAMPLER_NOT_ESTIMABLE` and must not be tuned into a pass;
- audit chat once duplicated Macha's replay work; duplication ledger now forbids repeating that mistake.

These are not open discovery tasks. They are reasons current guards exist.

## Large/chat-exclusive artifacts

`custody/takeover_20261012/TARGET_DISCOVERY_CHAT_RUNTIME_ARTIFACTS_20261012.csv` contains exact sizes and SHA-256 values for the conversation's large archives/checkpoints/expression files. Do not upload >GB-class binaries into normal Git history; use the recorded hashes/custody locations. Two small chat-exclusive historical notes were archived under `docs/agent/archive/chat_target_discovery_20261012/`.

## Authority boundary

At this handoff:
- biological replay authorized: false
- target selection authorized: false
- representation selection authorized: false
- TD60 authorized: false
- Stage4 authorized: false
- training authorized: false

Technical readiness, synthetic realization, or historical biological evidence cannot change those flags by implication.

## Handoff principle

A future agent should spend time on **the next unresolved evidence gate**, not on rediscovering the history. If a proposed task sounds like something the project has already attempted, search the PR/branch index and supersession ledger before writing code or reopening data.