GitHub custody and the successor handoff are now updated to the actual current lane state.

PR **#322** is the durable audit/no-repeat surface at head `977faf2cbeabe9f086950e6986eb923d7d58f834`. It now contains the V4 audit snapshot, machine-readable lane state, complete Task 4 hostile-review lineage, and reverified local-artifact custody.&#x20;

PR **#323** is the operational successor surface at head `de7547fb3c5573e8b43d293edefee39f704db55f`. Its first read is now `JEPA_NEW_AGENT_DETAILED_HANDOFF_V4_20261017.md`, and it explicitly directs the next agent to the current Task 4 regeneration-provenance blocker rather than the obsolete original candidate.&#x20;

The large/private data were **not duplicated into Git**. Their byte sizes and SHA-256 identities were recomputed and matched the existing custody record; the split discovery archive also reproduces its combined SHA-256. The two small historical chat-only notes are already imported in `docs/agent/historical_imports/`. &#x20;

The detailed handoff I would give the incoming agent is:

# JEPA Target Discovery / Unified Qualification / Downstream Lane Takeover

## Current mission

Do **not** restart the historical audit.

The historical Target Discovery, ETL, qualification-governance, runtime/mechanics, scientific-control, local-artifact and Task 0–4 audit work has been custodied on PR #322 and navigated from PR #323.

Your immediate job is narrow:

**repair the current Task 4 regeneration-provenance defect, qualify the successor, and obtain an independent exact-SHA review.**

Before doing anything, classify proposed work as:

`ALREADY_AUDITED | SUPERSEDED | OPEN | CHANGED_INPUT_REQUIRES_REQUALIFICATION`

Only the last two categories justify substantive new work.

---

## Frozen accepted authority

These exact code identities are settled:

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- Task 3: `117dd51dea827e734b299982da93991b934bdc8f`

Task 3 freeze branch:

`freeze/unified-task3-accepted-117dd51d-20261016`

Task 3 was independently accepted on PR #401.

Do not modify frozen Task 0–3 production code as part of Task 4 repair.

The global project authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Nothing in Task 4 mechanics changes this automatically.

---

## Read order

Start with these current files rather than reconstructing repository history:

1. PR #323\
   `docs/agent/JEPA_NEW_AGENT_DETAILED_HANDOFF_V4_20261017.md`
2. PR #323\
   `results/target_discovery/unified_qualification_v1/JEPA_SUCCESSOR_POINTER_V4_20261017.json`
3. PR #322\
   `docs/agent/JEPA_LANE_AUDIT_AND_CUSTODY_SNAPSHOT_V4_20261017.md`
4. PR #322\
   `results/target_discovery/unified_qualification_v1/JEPA_LANE_AUDIT_SNAPSHOT_V4_20261017.json`
5. PR #322\
   `results/target_discovery/unified_qualification_v1/TASK4_HOSTILE_REVIEW_LINEAGE_INDEX_V1_20261017.json`
6. PR #322\
   `results/target_discovery/unified_qualification_v1/LOCAL_ARTIFACT_CUSTODY_MANIFEST_V4_20261017.json`
7. PR #322 historical no-repeat indexes only if deeper archaeology becomes necessary.
8. PR #402 for the approved Task 4 architecture and implementation plan.
9. PRs #403–#417 for the exact Task 4 RED/review/repair chronology.

Do not begin by re-auditing all branches.

---

# Task 3 history that must remain preserved

Task 3 required several independent hostile-review rounds.

Rejected candidates:

- `851544e8...` — original B1–B6 authority/custody defects.
- `68df3158...` — Task 2 validator binding bypass, declared-KTQ path, actor/custody residuals.
- `d9e58a18...` — residual N2, nested validator independence and revocation-route defects.
- `117dd51d...` — independently accepted.

Task 4 inherited the C1–C9 conditions, R4 persistence requirement, R7 authenticated actor issue and R5 pooled-donor claim limitation.

The most important review rule inherited from Task 3 is:

**After repairing a gate, attack every other path capable of reaching the same state.**

That includes construction, reload, restart, fork, replay, legacy interfaces, nested prerequisites, revocation, supersession and state mutation.

---

# Task 4 chronology

## Architecture

PR #402 contains the approved architecture and implementation plan.

The design already establishes the intended system. Do not casually redesign it.

Major elements include:

- persistent cross-process custody;
- external authority separation;
- actor-action attestation;
- closed requirement/issuer law;
- C1–C9 pre-authority barrier;
- sealed finite challenge lifecycle;
- exposure accounting;
- immutable method-output freeze;
- hidden reveal only after allowed preconditions;
- terminal accounting;
- replay/rechain/truncation resistance;
- deterministic regeneration qualification;
- hostile-review separation;
- no biological/training authority from mechanics alone.

## First RED

PR #403 preserves the original RED-first Task 4 implementation evidence.

Run:

`38938697657`

Job:

`117100597615`

Result:

14 intentional failures before production Task 4 interfaces existed, using a read-only GitHub token.

Do not erase this history.

---

# Existing Task 4 code — do not rebuild

The current implementation lineage already contains:

- `challenge_custody_v1.py`
- `task4_actor_attestation_v1.py`
- `task4_authority_barrier_v1.py`
- `task4_custody_store_v1.py`
- `task4_publication_guard_v1.py`
- `task4_registry_adapter_v1.py`
- `task4_requirement_policy_v1.py`

There are also schemas and tests for campaign state, sealed challenges, realization sets, exposure accounting, custody, reveal, frozen outputs, evidence packages, actor attestations, persistent heads, replay/performance, hostile routes and terminal accounting.

Work from these bytes.

---

# Task 4 rejected-candidate lineage

These failures are permanent audit evidence.

### Candidate 1 — `b31371d6...`

Rejected because caller-created signer/verifier/publisher/policy objects could effectively self-mint the trust graph.

Hostile review: PR #405/#412.\
Repair: PR #406.

### Candidate 2 — `c537db4e...`

Rejected because a caller could substitute challenge definitions or realization sets after sealing.

Hostile review: PR #407.\
Repair: PR #408.

### Candidate 3 — `b5ed724c...`

Rejected because advanced `QualificationCampaign` state could be fabricated directly instead of being reached through the lawful lifecycle.

Hostile review: PR #409.\
Repair: PR #410.

### Candidate 4 — `d41720be...`

Rejected because hidden material could be revealed before terminal exposure classification was frozen, allowing terminal classification after seeing hidden truth.

Hostile review: PR #413.\
Repair: PR #414.

### `56b864e2...`

Mechanically green, but superseded as an immutable review pin because it retained stale review artifacts from its predecessor.

### Successor-4 — `068880822bca8036e605e3c5264770ce89057fee`

This candidate passed its pre-attack regression suite, but it is **not acceptable now**.

PR #417 found another legitimate authority defect.

---

# Current blocker

The controlling Task 4 open defect is:

**regeneration provenance**

Review branch:

`review/unified-task4-regeneration-provenance-red-06888082-20261017`

Review head:

`c543bd7c8b40d89db550dedad3ff5adbfbc356c0`

RED run:

`39000234158`

RED job:

`117301422733`

Focused result:

`1 failed, 109 passed, 1 skipped`

Failing attack:

`test_replaying_preexisting_rows_is_not_deterministic_regeneration_evidence`

The problem is conceptually important:

The implementation can currently mark regeneration as verified when the caller simply supplies the already-known sealed realization rows again.

Matching content/root proves that the supplied rows equal the committed rows.

It does **not** prove that the frozen generator, code, policy and RNG contract independently regenerated those rows.

Therefore:

`06888082...` is blocked/rejected as a final Task 4 candidate.

Current state:

`TASK4_SUCCESSOR4_REJECTED_BY_REGENERATION_PROVENANCE_RED__SUCCESSOR5_REPAIR_REQUIRED__INDEPENDENT_ACCEPTANCE_ABSENT`

---

# Immediate implementation sequence

## 1. Preserve PR #417

Do not modify the hostile-review branch.

Do not patch `06888082...`.

The failure is permanent RED evidence.

## 2. Create successor-5

Cut the repair branch from exactly:

`068880822bca8036e605e3c5264770ce89057fee`

Port/retain the current failing test before production changes.

## 3. Repair regeneration provenance

The new system must establish that regeneration actually came through the committed regeneration mechanism.

Bind at least:

- exact challenge-definition identity;
- exact sealed realization-set identity/root;
- exact generator code identity;
- exact generator policy identity;
- exact RNG identity/state/seed contract;
- campaign identity;
- lawful lifecycle/reveal state;
- regeneration event/receipt provenance;
- a trust boundary the caller cannot manufacture merely by implementing an interface or presenting copied rows.

Avoid another magic-string or caller-constructed protocol-object authority hole.

## 4. Red-team sibling paths

Before declaring GREEN, explicitly attack:

- original rows echoed unchanged;
- deep-copied rows with identical hashes/root;
- fake generator object with the correct interface;
- substituted generator code SHA;
- substituted generator policy SHA;
- substituted RNG identity/state/seed;
- regeneration before lawful reveal;
- regeneration against another sealed definition;
- regeneration against another realization root;
- stale regeneration receipt replay;
- receipt reused between campaign forks;
- provenance object mutated after reveal;
- direct construction of a “verified” regeneration state;
- reload/restart paths that omit execution provenance.

Do not limit testing to the repaired public function.

## 5. Exact-head verification

On the same exact successor-5 code/test head run:

- focused Task 4 custody/hostile tests;
- projected 100k custody replay benchmark;
- full unified Task 0–4 test suite;
- Task 1 regression;
- Task 2 manifest/access regression;
- Task 3 registry regression;
- unified synthetic integration;
- frozen Task 0–3 byte/diff check.

Keep inherited workflow-environment problems separate from actual Task 4 failures.

## 6. Self-audit

Before pinning, deliberately ask:

“What other path reaches `REGENERATION_VERIFIED` without the intended regeneration event?”

Attack it.

## 7. Immutable candidate

Only after all exact-head checks are green:

- create an immutable successor-5 branch;
- bind candidate state/review packet to that SHA;
- do not add unrelated docs commits afterward and continue referring to the old SHA.

## 8. Independent review

Create a separate hostile-review branch.

The reviewer must explicitly return either:

`ACCEPT_TASK4_CUSTODY_CANDIDATE`

or

`REJECT_TASK4_CUSTODY_CANDIDATE`

against the exact candidate SHA.

If rejected, preserve the RED and repeat narrow RED→repair→review.

---

# Historical scientific work already done

Do not restart these audits unless source bytes/contracts changed.

## Population / ETL

Population-support authority is already custodied.

Authenticated census:

- 6,351,753 rows
- 149 donors
- 42 observation operators
- 3 sources
- 2,028 donor × operator strata
- 104 reader-fit donors
- 22 reader-validation donors
- 23 reader-oracle donors

## Repaired TD units

Already handled:

- G8
- G6
- G9 / S1 / S2 geometry
- R1
- G2
- G7
- R4 / C6 / C4
- C4→C6 firewall
- G12
- system battery

Older duplicate PRs #375–#378 are superseded.

## Runtime/mechanics

Already audited:

- optimizer/gradient flow;
- teacher no-grad behavior;
- optimizer-before-EMA ordering;
- invalid-update EMA blocking;
- Adam moments;
- restart/checkpoint behavior;
- identity RNG;
- packing/scientific weights;
- FULL104 support and normalization;
- donor-primary targets;
- p/q separation;
- context/visibility/masking;
- anti-carryover.

These are mechanics evidence only.

---

# Scientific laws to preserve

The scientific pipeline is intentionally multi-layer.

Evidence may include:

- RNA expression;
- peak accessibility/differential accessibility;
- chromVAR motif-program accessibility;
- footprinting;
- SCENIC+ regulatory inference;
- gene-expression programs;
- perturbational evidence;
- external datasets;
- historical ETL/provenance.

Do **not** treat several analyses of the same ATAC observations as several independent datasets.

Maintain a source-dependency graph.

For chromVAR specifically, the defensible default claim is motif-associated accessibility, often at motif-family level—not direct TF binding or causality.

Donors, not cells, are the replicate for donor-level inference.

Keep:

- measurement evidence;
- mechanics evidence;
- biological evidence;
- causal evidence

separate.

Do not let one source failure average away.

Do not favorable-zero-fill missing evidence.

Preserve contradictions and unsupported states explicitly.

---

# Teacher / target design warning

A model trained to predict the proposed target from another gene panel is not automatically a richer “teacher.”

The teacher must construct a measured state from the richer biological evidence assigned to it.

The student predicts that state from the restricted evidence available to it.

Continue to test target/query identity shortcuts using controls such as:

- identity-only;
- shared target;
- fixed target;
- stop-gradient;
- shuffled query identity.

---

# Dataset exposure warning

Do not automatically call a dataset independent or contaminated merely because it has been seen previously.

Use the actual ETL/exposure ledger to determine what information was exposed, when, and whether it could influence architecture, target selection, parameter tuning or evaluation.

---

# Local/private data custody

Large binary artifacts are not copied into Git.

Their hashes and byte counts are retained in the PR #322 V4 custody manifest.

Hash-verify before use.

Then establish semantic provenance before interpreting them.

A checkpoint being physically available is not biological evidence.

The small historical WSL/foundation note and Status/Repair Plan have already been imported into Git.

---

# What happens after Task 4 is eventually accepted

Do not jump directly to training.

Task 4 acceptance means the **qualification custody mechanics** have passed hostile review.

It does not mean:

- a target has won;
- a representation has won;
- biological validity has been established;
- Stage 4 execution is authorized;
- training is authorized.

The next scientific architecture step should formalize the evidence-dependency/adjudication framework.

That framework should distinguish:

- within-source analytical convergence;
- cross-assay convergence;
- cross-dataset replication;
- perturbational/causal evidence;
- external replication.

Shared-source evidence gets dependency-aware treatment rather than naive additive credit.

A target should likely need minimum classes of evidence, not merely the highest scalar score.

---

# Working protocol

For every proposed task:

1. Read the custody/handoff.
2. Classify it as `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN`, or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`.
3. If open, self-audit assumptions.
4. Write the hostile RED first.
5. Make the smallest repair.
6. Run focused regression.
7. Run inherited regression.
8. Attack sibling routes.
9. Pin exact immutable bytes.
10. Get independent exact-SHA review.
11. Update PR #322 and PR #323 at the next major gate transition.

Never delete or rewrite rejection history into a story where the candidate was always correct.

The key correction for the new agent is that **Task 4 successor-4 is no longer a candidate waiting for routine review**. PR #417 has demonstrated a specific reproducible defect: replayed sealed rows can masquerade as deterministic regeneration. The current work therefore begins with **successor-5 regeneration-provenance repair**, not with Task 4 acceptance. The durable audit explicitly records that chronology.&#x20;

The handoff also tells the successor not to rebuild Task 4 modules or restart broad historical audits; the existing implementation, rejection lineage, population/ETL custody, scientific framework, and local-artifact identities are already indexed.