# Unified Task 4 — Sealed Challenge Custody Design

Date: 2026-10-15
Status: DESIGN APPROVED IN CHAT; IMPLEMENTATION BLOCKED ON TASK 3 INDEPENDENT ACCEPTANCE
Authority effect: NONE

Binding global state remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Purpose

Unified Task 4 implements custody of the qualification exam. Its job is not to decide whether a challenge is biologically true or scientifically harder. Its job is to make the qualification process tamper-evident and non-retunable after exposure.

Task 4 must prevent silent reset, cherry-picking, replay, exposure-history erasure, method-renaming resets, challenge-set truncation, output mutation after reveal, post-exposure reroll, stale-registry reuse, actor aliasing, and hidden-material leakage.

Task 4 produces custody evidence. Task 5 interprets qualification outcomes.

## 2. Gate and authority boundary

Task 4 production implementation must not begin until Unified Task 3 is independently accepted and frozen at an exact head.

Preparation before that gate may include only design/specification, exact historical reuse mapping, RED attack inventory, schema planning, and CI planning.

No final challenge secrets, hidden nonces, final realization roots, protected biological values, candidate outcomes, validation/oracle values, or real qualification worlds may be created during preparation.

Task 4 grants no target, representation, human-execution, Stage 4, or training authority.

## 3. Inputs that Task 4 must bind

Every authority-bearing Task 4 object must ultimately bind exact identities for:

- frozen Task 1 canonical/authority primitives;
- frozen Task 2 execution manifest/access authority at `c7dfff1cee608e4a101855d42cf0af08491c2aaf`;
- exact independently accepted Task 3 registry snapshot;
- exact Task 3 registry-unit identities under qualification;
- scientific producer actor identity;
- scientific executor actor identity;
- qualification controller actor identity;
- independent adjudicator/reviewer actor identity;
- challenge generator code identity;
- challenge generator policy identity;
- realization schema identity;
- RNG derivation-law identity;
- challenge-family/content schema identity;
- adjudication/scoring contract identity;
- multiplicity/draw-accounting policy identity;
- publication/secret-scan policy identity.

Task 4 must use Task 1 canonical identity and Task 3 actor/prerequisite authority. It must not create a second identity system.

## 4. Core object split

Task 4 must not use one monolithic commitment object. The qualification exam is split into distinct immutable objects with distinct semantics.

### 4.1 `QualificationCampaign`

The one genesis object for a qualification attempt. It binds:

- campaign ID;
- exact Task 2 manifest identity;
- exact Task 3 registry snapshot identity;
- exact registry-unit identities;
- producer/executor/controller/adjudicator actors;
- qualification budget;
- multiplicity law;
- challenge-generator code/policy identities;
- realization/RNG policy identities;
- challenge-content/adjudication contract identities;
- genesis ledger identity;
- authority scope/restrictions;
- campaign state.

Starting a fresh ledger is not a continuation. It creates a new campaign with no inherited qualification result.

### 4.2 `SealedChallengeDefinition`

Public metadata plus cryptographic commitments to hidden challenge specification. It binds family/version, challenge-class budget, RNG law, generator identities and commitments to hidden specification/nonces without publishing those hidden bytes.

### 4.3 `SealedRealizationSet`

The exact finite qualification exam. Before the first exposure, the harness must deterministically materialize the complete qualification realization inventory and commit to:

- ordered realization IDs;
- exact content digests;
- challenge-class membership;
- realization count;
- generation metadata;
- total qualification budget;
- sealed root commitment.

Hidden content remains hidden. Cardinality and cryptographic identities are frozen.

### 4.4 `ExposureLedger`

Append-only history of all qualification information consumed. Every exposure is counted even if execution later crashes, output is malformed, or the method is subsequently renamed or repaired.

### 4.5 `MethodOutputFreezeReceipt`

Binds the exact method scientific identity, exact exposure, exact produced output artifact, and freeze time/order before hidden challenge material can be revealed.

### 4.6 `SealedQualificationReveal`

Supplies hidden material only after required outputs are frozen. Verification regenerates the committed realization set and checks exact identities. Caller-supplied world lists are non-authoritative.

### 4.7 `QualificationEligibilityReceipt`

Custody-only statement that the campaign completed the sealed lifecycle law. It is not a biological PASS/FAIL statement.

## 5. Campaign genesis and anti-reset law

The campaign genesis object is the anti-reset anchor.

Rules:

1. one campaign has one genesis ledger;
2. one ledger belongs to exactly one campaign;
3. a new ledger means a new campaign;
4. qualification outcomes never transfer automatically across campaigns;
5. campaign restart after unfavorable exposure does not erase the prior exposure history;
6. prior campaign exposures remain part of project-level multiplicity/accounting where applicable;
7. a campaign ID cannot be reused with changed dependencies;
8. changing a decision-bearing dependency creates a new campaign identity.

Task 4 must preserve both campaign-local and project/lineage exposure counts sufficient for downstream multiplicity control.

## 6. Task 3 registry snapshot freshness

Task 4 binds both:

- exact Task 3 registry snapshot identity at campaign creation; and
- exact unit identities under qualification.

Before every authority-bearing transition — campaign creation, definition sealing, realization sealing, exposure, output freeze, reveal, regeneration verification, and final custody completion — Task 4 must re-resolve current registry state.

If a relevant unit is `SUPERSEDED`, `REVOKED_BY_DEFECT`, or `REQUIRES_REQUALIFICATION`, the transition fails closed.

A registry hash that was once valid is not perpetual authority.

## 7. Development vs final qualification namespaces

Development challenges and final qualification challenges are separate namespaces.

Development challenge objects carry:

`promotion_authority = NONE`

They may support debugging/tuning only. Success on a development challenge can never produce final qualification custody or `KNOWN_TRUTH_QUALIFIED` authority.

Final qualification challenges use distinct domain separation for commitments, roots and realization IDs. Debug/development nonce material can never satisfy a final commitment.

## 8. Non-circular commitment law

Task 4 adopts the non-circular E2 correction prospectively.

The public commitment payload contains only lawful public metadata and cryptographic commitments to hidden material.

Hidden nonce/specification/root bytes are absent from the public payload before reveal.

Commitment identity is the canonical digest of the public commitment payload.

Reveal supplies hidden material; verification recomputes committed digests and regenerates realization identities/content.

No digest contains itself and no fixed-point construction is required.

## 9. Do not mechanically decide generic scientific difficulty

Task 4 must not implement a generic total ordering of challenge difficulty.

Arbitrary scientific challenge mutations may be incomparable. Custody may prove identity and mutation, but substantive “harder/easier” judgments require explicit reviewed authority.

Successor classes are:

### `IDENTICAL_CONTINUATION`

Mechanically identical scientific challenge and realization law. Reroll is forbidden.

### `NEW_QUALIFICATION_CAMPAIGN`

Any changed or ambiguous scientific challenge defaults here. Prior qualification authority does not transfer.

### `REVIEWED_ADDITIONAL_STRESS`

May add challenges to an existing campaign only if:

- prior failures/exposures remain present;
- existing realization set is not altered or replaced;
- an exact independent reviewer decision explicitly authorizes the additive stress;
- the additional set gets its own committed identities and exposure accounting.

No “additional stress” path may replace an unfavorable prior challenge.

## 10. Full finite exam before first exposure

Before qualification exposure begins, the complete final realization inventory must be sealed.

The producer cannot lazily request additional worlds after observing earlier results.

The realization set must bind the exact ordered inventory and content digests.

A final qualification verdict is impossible unless every committed realization is accounted for.

Each realization ends in an explicit terminal accounting category such as:

- evaluated;
- lawful technical failure;
- unsupported / not-estimable;
- independently defect-invalidated.

“Missing from results” is not a legal terminal state.

## 11. State machine

Canonical campaign state machine:

`CAMPAIGN_CREATED`
→ `DEFINITION_SEALED`
→ `REALIZATION_SET_SEALED`
→ `EXPOSURE_ACTIVE`
→ `ALL_REQUIRED_OUTPUTS_FROZEN`
→ `HIDDEN_MATERIAL_REVEALED`
→ `REGENERATION_VERIFIED`
→ `CUSTODY_COMPLETE`

Failure/revocation transition:

`INVALIDATED`

No automatic transition out of `INVALIDATED`.

Post-exposure scientific repair normally creates a new qualification campaign.

## 12. Exposure and output custody

Exposure must be issued by the harness/custody service, not by producer-authored ledger entries.

The harness:

1. resolves campaign and registry authority;
2. selects the next committed realization according to the frozen exposure law;
3. appends the exposure record;
4. releases only allowed challenge material;
5. records the exact method scientific identity;
6. receives/finalizes output freeze;
7. permits reveal only after required output freeze.

A hand-constructed exposure event has no authority.

Once challenge material is exposed, the exposure budget is consumed even if:

- the method crashes;
- output is malformed;
- the result is unfavorable;
- the run is abandoned;
- the method is renamed;
- a software defect is later discovered.

## 13. Mutation law after exposure

After first final exposure:

- no failed world may be deleted;
- no realization may be replaced;
- no family may be silently swapped;
- no unchanged successor may reroll RNG;
- no method rename may reset draw/multiplicity history;
- no public/reused family may be declared secret again;
- no late exposure is allowed after the campaign enters final output-freeze completion;
- no output artifact may change after its freeze receipt;
- no post-exposure repair inherits qualification automatically;
- no new campaign may erase prior campaign exposure history.

## 14. Multiplicity and information-spend accounting

Task 4 distinguishes:

- `exposures_consumed` — every time sealed information is released;
- `valid_adjudicated_results` — outcomes later accepted as technically valid.

Qualification information is spent at exposure, not at successful completion.

Accounting must support at least:

- per method scientific identity;
- per unit;
- per campaign lineage;
- per challenge family;
- project-level cumulative sealed exposure where needed downstream.

Method-name or wrapper changes cannot reset multiplicity.

## 15. Actor independence

Task 4 must reuse Task 3 actor objects and compare authenticated underlying actor IDs.

At minimum:

- scientific producer;
- scientific executor;
- qualification controller;
- independent adjudicator/reviewer

must obey the role-separation laws defined by the controlling registry/qualification plan.

Digest inequality alone is not sufficient evidence of actor independence.

## 16. Substantive content qualification

Role labels are not substantive authority.

Before final sealing, Task 4 requires authenticated Task 3 prerequisite/content-validation evidence for the owning contracts, including:

- challenge generator policy;
- RNG/realization law;
- challenge family definition;
- realization schema;
- adjudication/scoring contract;
- multiplicity policy;
- publication/secret-scan policy.

A bare object such as `{object_role: CHALLENGE_GENERATOR_POLICY}` cannot satisfy the prerequisite.

## 17. Persistent ledger and signer boundary

Task 4 moves historical ledger-persistence/head-publication obligations into the custody mechanics.

Requirements:

- append-only persistent ledger;
- exact hash-chain replay;
- externally anchored/published ledger head after every authority-bearing append;
- every load/replay checks expected prior head;
- no caller-provided ledger truncation can become authority;
- replay must validate custody order, not only hashes.

Task 4 must not own the long-lived signing secret inside producer code.

The custody API should define a signer/verifier interface. Durable cross-process verification should support a verifier identity that does not require distributing the signing secret to producers. Public-key signing is preferred conceptually over caller-supplied HMAC for durable receipts, but the cryptographic library choice is not frozen by this design.

## 18. R1/R4 process isolation boundary

Before human execution:

- registry state used for finalization is outside producer process;
- signing key is outside producer process;
- reader-fit values remain outside producer process as required by Task 2;
- harness drives exposure and finalization;
- protected partitions remain physically unavailable under the access law.

Fixture-mode mechanics may run in-process but cannot claim current-TD/human qualification authority.

## 19. Secret/publication surface

Secret absence must be checked across all publication channels controlled by the project, not Git working files alone.

Publication surface includes at least:

- exact committed repository tree/archive;
- CI logs;
- uploaded workflow artifacts;
- generated receipts;
- exception/error text;
- filenames/paths;
- published cache metadata.

The NO-ECHO principle remains binding: custody refusal messages must not echo hidden nonce/specification material or attacker-controlled secret keys.

## 20. D1 exception hardening

Expected custody refusals use narrow, explicit error classes/reasons.

Unexpected programming/internal errors must remain distinguishable from lawful custody refusal.

Tests must prove that an internal programming failure is not silently converted into a successful fail-closed custody verdict.

## 21. Historical substrate reuse

Old production-synthetic Task 2 exact implementation:

`ff597faf2182522a320ec5322f8db9b67c9c6094`

Classification:

`ADAPT_AND_WRAP__SEALED_CUSTODY_RNG_SUBSTRATE`

Exact historical test blobs include:

- `tests/production_synthetic/test_custody_v1.py` blob `3d27802f60ff026aef8b6d1a07bb879e55a3a39b`;
- `tests/production_synthetic/test_custody_v1_hostile.py` blob `8f22cd69e3332f4f6f4129b3099673472317520a`;
- fixture blob `23fb531077942223f4b4169853403de380af0b89`.

Reuse only independently understandable primitives:

- canonical commitment/reveal hashing;
- domain-separated RNG derivation;
- append-only hash-chain ledger mechanics;
- lineage replay validation;
- exposure accounting;
- secret scan mechanics;
- deterministic regeneration concepts;
- replay/cache performance strategies.

Do not copy historical authority assumptions or generic “harder/easier” logic blindly.

## 22. Mandatory inherited 13 attacks

Task 4 RED must reproduce all historical custody failures through the new interface:

1. incomplete can’t-get-easier component accounting;
2. superseded version remained commit/expose capable;
3. withheld commitment accepted debug nonce;
4. easier withheld-family swap;
5. unchanged successor reroll;
6. reused family remained secret after reveal;
7. class-nonce reveal leaked shared open-run family;
8. successor reverted to public family;
9. method rename reset draw count;
10. late exposure after fit freeze;
11. realistic-size secret scan failure;
12. eligibility true before own reveal;
13. pathological ledger build/replay performance.

Where the revised design removes generic difficulty ordering, the historical attack is translated into the new lawful rule: ambiguous/changing scientific challenge cannot inherit the old campaign and must become a new campaign unless independently approved as additive stress.

## 23. Expanded Task 4 RED attack matrix

In addition to the inherited attacks, RED must cover at least:

1. development challenge cannot create final qualification authority;
2. fresh-ledger/reset attack after unfavorable exposure;
3. campaign abort/restart after sealed exposure;
4. incomplete realization inventory before first exposure;
5. lazy generation of additional worlds after earlier outcomes;
6. selective completion/cherry-pick finalization;
7. missing committed world silently omitted;
8. early reveal before output freeze;
9. reveal mismatch;
10. caller-supplied realization list accepted without regeneration;
11. stale Task 2 manifest substitution;
12. stale Task 3 registry snapshot after revocation;
13. changed/revoked Task 3 unit still advancing campaign;
14. controller/adjudicator aliasing producer/executor actor;
15. hand-constructed exposure event;
16. output mutation after output-freeze receipt;
17. failed/crashed run incorrectly not counted as exposure;
18. method wrapper/config rename resetting multiplicity;
19. producer-supplied signing key accepted for authoritative campaign;
20. hidden nonce/spec appears in public commitment payload;
21. hidden material leaks via error text;
22. hidden material leaks via CI/artifact publication surface;
23. ledger truncation/rechain accepted without anchored expected head;
24. ledger entry reordering;
25. duplicate exposure ID;
26. lineage fork;
27. superseded commitment exposes/finalizes;
28. post-exposure repair inherits old qualification;
29. additive-stress successor replaces prior failures instead of augmenting;
30. generic challenge mutation mechanically declared “harder” without review;
31. fixture-only campaign satisfies human/current-TD authority;
32. qualification eligibility before own reveal;
33. replay cache survives dependency mutation;
34. optimized replay path skips semantic/order validation;
35. secret scan fails realistic secret sizes;
36. performance optimization changes ledger hashes/semantics.

## 24. Performance qualification

Task 4 must carry both a slow/reference semantic replay and the optimized production replay for qualification testing where practical.

Performance tests must prove:

- identical canonical ledger/result identities between reference and optimized paths;
- no skipped validators;
- deterministic behavior;
- declared performance ceiling at historical scale;
- declared performance ceiling at a larger projected campaign scale.

Optimization may change implementation, never scientific/custody semantics.

## 25. Outputs of Task 4

Task 4 produces two distinct downstream artifacts.

### `SEALED_CUSTODY_RECEIPT_V1`

Proves the qualification exam was sealed, exposed, frozen, revealed and regenerated according to custody law.

### `QUALIFICATION_EVIDENCE_PACKAGE_V1`

Contains exact outcome artifacts and accounting required for Task 5 interpretation.

Task 4 does not classify biological PASS/FAIL. Task 5 consumes the evidence package and applies known-truth qualification logic.

## 26. Planned implementation surfaces after Task 3 acceptance

Production surfaces are expected to include:

- `scripts/v5/td_unified/challenge_custody_v1.py`;
- `schemas/target_discovery/unified_v1/qualification_campaign_v1.json`;
- `schemas/target_discovery/unified_v1/sealed_challenge_definition_v1.json`;
- `schemas/target_discovery/unified_v1/sealed_realization_set_v1.json`;
- `schemas/target_discovery/unified_v1/exposure_ledger_v1.json`;
- `schemas/target_discovery/unified_v1/method_output_freeze_receipt_v1.json`;
- `schemas/target_discovery/unified_v1/sealed_qualification_reveal_v1.json`;
- `schemas/target_discovery/unified_v1/sealed_custody_receipt_v1.json`;
- `tests/v5/td_unified/test_challenge_custody_v1.py`;
- hostile-cycle test files preserving RED/GREEN history;
- dedicated Task 4 workflow with full-history checkout.

Exact filenames may be refined in the implementation plan, but object boundaries and authority semantics are fixed by this design unless prospectively amended before execution.

## 27. CI and verification law

After Task 3 acceptance and Task 4 implementation starts:

1. cut branch from exact frozen Task 3 head;
2. preserve RED-only commit first;
3. focused Task 4 RED/GREEN workflow;
4. full `tests/v5/td_unified` regression;
5. frozen Task 3 regression;
6. frozen Task 2 regression;
7. frozen Task 1 regression;
8. inherited unified synthetic integration;
9. full-history checkout for ancestry and archive secret scans;
10. repeated owner hostile self-audit cycles;
11. independent exact-head Macha review before Task 5.

## 28. No-repeat / historical custody rule

Task 4 must reuse authenticated historical mechanics and attack knowledge. It must not redo old synthetic custody work merely to rediscover settled failures.

Historical artifacts, tests, exact blobs, performance observations, negative findings, repair decisions, new RED heads, repair heads, receipts and review outcomes must be continuously preserved in PR #322 and summarized in PR #323.

## 29. Explicit non-goals

Task 4 does not:

- decide target biology;
- decide representation biology;
- open validation/oracle values;
- execute real target discovery;
- construct known-truth CaseBundle/TruthBundle;
- declare biological PASS/FAIL;
- authorize human execution by itself;
- authorize Stage 4;
- authorize training.

## 30. Acceptance condition for implementation start

Task 4 production implementation may begin only after:

1. Task 3 exact head is independently accepted and frozen;
2. this design remains the controlling Task 4 design or is prospectively amended before Task 4 execution;
3. an implementation plan derived from this spec is reviewed;
4. a RED-only Task 4 branch is created from frozen Task 3;
5. no hidden final challenge material has been generated before that prospective freeze.
