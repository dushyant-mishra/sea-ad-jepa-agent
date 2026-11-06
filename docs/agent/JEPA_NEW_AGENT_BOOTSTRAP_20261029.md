# JEPA new-agent bootstrap — start here, do not recrawl history (2026-10-29)

**Purpose:** this is a short operational entry point for a new agent taking over the JEPA target-discovery / production-synthetic / downstream lane. It does **not** replace the deeper historical audit. It tells you what can be trusted without re-auditing, what remains genuinely open, and what to execute next.

**Repository:** `dushyant-mishra/sea-ad-jepa-agent`.

**Current long-lived branches when this bootstrap was written**
- Audit PR #322: `bae9ce01ffabb7e96cd0987921d7cd979e8814a7`, **23/23 workflows green** before this bootstrap append.
- Handoff PR #460: `da5c3909bbab0a615d88ae48e11ddab913dd3ec0`, **2/2 workflows green** before this bootstrap append.
- Original independently reviewed V8e audit head: `a271164554076d0acda3bd0cf0b1bf957c0fdfd3`. Later append-only audit heads **do not inherit that scientific acceptance**.

Machine bootstrap mirror: `results/target_discovery/unified_qualification_v1/JEPA_NEW_AGENT_BOOTSTRAP_20261029.json` on audit #322.

---

## 1. Do not start by re-auditing the project

Open these in order:

1. **Current final freeze:** `docs/agent/JEPA_FINAL_LANE_TAKEOVER_FREEZE_20261028.md` on audit #322.
2. Its machine mirror: `results/target_discovery/unified_qualification_v1/JEPA_FINAL_LANE_TAKEOVER_FREEZE_20261028.json`.
3. **Latest independent Macha V2/G7 review:** `docs/agent/JEPA_MACHA_V2_G7_OBSERVATION_CONTRACT_DELTA_20261028.md`.
4. **Latest ChatGPT Task3 independent RED:** `docs/agent/JEPA_PS_TASK3_MACHA437_INDEPENDENT_REVIEW_20261028.md`.
5. Only if you need older provenance, follow the exact source links from `JEPA_COMPLETE_LANE_TAKEOVER_FREEZE_20261028.md` and `JEPA_LANE_TAKEOVER_MASTER_20261028.md`.

The old master contains the historical chronology. **Do not recrawl every old PR unless a pinned source changed or a new contradiction appears.**

### Re-audit only when one of these is true

- The exact Git SHA or Git blob of a relied-upon artifact changed.
- A new independent reviewer produced a contradictory executable result.
- New authenticated physical/source data changes a previously unavailable fact.
- The scientific question, evidence-right policy, or target definition has deliberately changed.
- A newly discovered integrity/security flaw invalidates an earlier receipt.

Otherwise, treat the archived historical result at its exact scope as **already audited** and continue from the open dependency.

---

## 2. Historical science you should reuse, not repeat

### C2 corrected real relational result — PR #314

PR #314 `c6899a2910244a0352c0c57e7aea6e3026191da1` is the **spent one-shot corrected HVS/SEA replay**.

- TD56 PASS
- TD57B PASS
- TD57C nearest-third FAIL
- TD59 PASS

Interpretation: **broad/mesoscale C2 relational structure remains biologically viable, but there is no selected JEPA target**. Do not rerun the replay just to try to obtain a better verdict.

### C3 measured query precedent — historical R5

R5 constructed a query-conditioned target from **eight other measured genes**, excluding the queried gene from the target and normalization. Developmental donor-held-out results:

- q-specific: R² 0.4300
- technical + q: 0.3496
- q-agnostic: 0.2760
- q-count only: 0.1610

This is **C3 QUERY-MEASURED**, not a production-qualified target and not “rare microglia.”

### Other frozen biology

Reuse V44 real-RNA teacher proxy results, Stage69/70 rare work, PR #164 separate-nucleus RNA/ATAC, PR #77 macrophage CRISPR, SCENIC+/chromVAR caveats, the 8,915-block reader-fit raw-count audit, and the 6.35M/149-donor metadata census **at their recorded scope**.

Never treat:
- separate nuclei as same-cell paired RNA/ATAC;
- SCENIC+/motif/footprint evidence as independent physical TF binding;
- macrophage perturbation as automatic adult microglial causal evidence;
- metadata coverage as the same thing as physically authenticated raw-count support.

---

## 3. Current independent review state — these are the live engineering problems

### PR #479 — V2 normalization view

Code head: `ae762d7096a94ac663a0788f6f577ba404e37536`.

Independent Macha review PR #481: `957fa4a558ce2bd219b5c2dec6dad8f65dca81ab`.

**Verdict: `REPAIR_REQUIRED`.**

Author tests had 124 PASS, but Macha found:

- **A1:** the consumer accepts a depth that carries the physical total, an offset, or a scale.
- **A2:** “student” is self-declared; non-base rights can be exposed.
- **A3:** metaclass route through snapshot/type handling.
- **A4:** empty-base refusal class depends on withheld mass; inherited from PR #474.

Important positive result: over 240 complete-world counterfactuals, the intended student-view withheld-mass noninterference held within the original scope.

**Owner now:** ChatGPT repairs A1–A3 against **unchanged** PR #481 tests. Macha owns A4 upstream in PR #474 when explicitly assigned.

Do not expose a teacher digest to the student. An unkeyed digest over a small hidden domain can itself leak by enumeration.

---

### PR #476 — G7 snapshot/binder

Code head: `26031df25b51087f2f3ec35a88eef2919d794c68`.

Independent Macha review PR #482: `58baa4f912c791866c1aae31eab797da9dca588a`.

**Verdict: `ACCEPT_INCREMENTAL_WITH_R1_R2_BLOCKERS`.**

Fixed:
- the original PR #472 R5X routes;
- R6 mutable-input receipt forgeries.

Still open:
- an exact-type/metaclass route in JSON validation;
- a **composition gap**: V3 can be called directly without the binder receipt, so binder-refused evidence can still reach the decision code;
- R1 physical measurement identity;
- R1D donor/specimen pseudoreplication;
- R2 query-excluded normalization provenance.

**Owner now:** repair type dispatch and create one reviewed **bind → immutable snapshot → V3** composed entry. Do not silently alter the old V3 decision law.

---

### PR #477 — production-synthetic canonical encoder

Code head: `c83088de090bc4f2fc6bbee353c46070bcca7be5`.

Independent Macha review PR #483: `48ec018735a095571a0bfaa25b33f9b9deb40b39`.

**Verdict: `ACCEPT_INCREMENTAL_WITH_LIMITATIONS`.**

Earlier Windows `intc/uintc` and error-name problems are fixed. New hostile findings remain:
- `isinstance` / `__class__` payload routes;
- chained payload exception `__cause__`;
- external T2-D issuer still RED.

**Owner now:** exact `type(x) is` dispatch before any `isinstance`; refuse payload exception chaining with `from None`; decide explicitly whether live generator rows are even permitted at this trust boundary.

---

### Production-synthetic Task 3 — PR #486 needs independent ChatGPT review first

Original Macha Task3 PR #437 failed independent ChatGPT PR #480 for:

- lossy float coercion falsely equating distinct large integer witnesses;
- open-ended `OBS_` parameter names that allowed semantic spoofing.

Macha repair PR #486:
- exact head `f17080516f77e79fb6f6cb44903cbabdb2a85dd7`;
- author CI currently 3/3 workflows green;
- exact numeric comparison and closed named observation registry;
- **no authenticated empirical calibration issuer**.

**Highest-priority independent task:** review PR #486 against immutable PR #480 tests, then add new attacks for:
- finite/non-finite and cross-numeric-type equality;
- booleans, ints, floats, NumPy scalars and subclasses;
- registry-name closure versus semantic meaning;
- accidental biological parameter admission under an observation-looking name;
- any path that turns empty `_AUTHENTICATED_CALIBRATION_REGISTRY` into implied authority.

Only an independent exact-head verdict can change Task3 engineering status. Even a code PASS does not create real TRAIN calibration data.

---

## 4. Observation-depth scientific decision that still needs an explicit owner ruling

Macha recommends:

### D1 — default candidate

`VISIBLE_BASE_MAPPED_SUM_V1`

Definition:

`D1 = Σ counts of base-visible MEASURED_SCALAR addresses`

Properties:
- computed only from student-visible data;
- no private physical total;
- invariant under later rights expansion if the base rights are frozen;
- exactly consumer-verifiable per cell;
- works on real rows even when physical source residual exists.

### D2 — optional, not default

`D2 = D1 + source residual`

Do **not** expose D2 unless a per-query/per-operator off-ledger alias and source-feature audit establishes that the residual is lawful with respect to the query.

### Preserve V1

Do not:
- rename D1/D2 to legacy `library_size`;
- weaken existing physical `count <= library_size` CaseBundle/G7 rules;
- put a hash of the private physical or teacher value into the student payload;
- claim a rename adapter establishes G7 compatibility.

The deciding scientific lane must explicitly **accept, modify, or reject D1** before productionizing a V2 observation contract.

---

## 5. Exact first-session action order for the new agent

1. **Fetch live heads** of #322, #460, #486, #479/#481, #476/#482, #477/#483. Compare them to this handoff. If unchanged, do **not** recrawl historical PRs.
2. **Read the final freeze and machine mirror.** Confirm audit/handoff CI still green. If a branch moved, inspect only the delta from the pinned head.
3. **Independently review PR #486.** This is the cleanest current prerequisite for production-synthetic readiness.
4. **Repair PR #479 A1–A3** against Macha #481 unchanged tests. Do not self-accept. Coordinate A4 separately with Macha/PR474.
5. **Repair PR #476** exact-type route and make the binder/decision composition mandatory. Preserve R1/R1D/R2 RED.
6. **Repair PR #477** exact-type and exception-cause routes. Preserve T2-D RED.
7. **Get an explicit D1/D2 decision.** If D1 is accepted, create a versioned V2 content law instead of mutating CaseBundle/G7 V1.
8. **ETL/source work:** quantify reader-fit residual decomposition and feature/alias closure; external evidence lane obtains depositor QC methods and SEA-AD specimen keys if permitted.
9. **Only after Tasks 1–3, calibration, G7 source rights, and observation contract qualify:** implement the V3.1.1 **production-synthetic Task 4 candidate-neutral biological generator**. It is currently absent.
10. **Only after sealed known-truth qualification:** return to human C2/C3 comparison and downstream JEPA. `TARGET_NONE` remains a valid scientific outcome.

Do not build another simulator, registry, target selector, or JEPA harness unless you first demonstrate a real deficiency in the existing #344 / #379–381 / #328 / #369 / #451 / #469 architecture.

---

## 6. Data and custody rules the next agent must know

- Large historical archives/checkpoints are **hash-indexed, not guaranteed to be available as GitHub bytes**.
- PR #471 verified 97/97 historical archive members by SHA, but that does not make the August archive a current real calibration issuer.
- Do not download BAM/FASTQ files prohibited by project policy.
- Do not copy incidental sample-level diagnosis/age/sex values into handoff/audit. Macha disclosed an incidental read-only print; it was not used in deciding science and is not reproduced.
- All current implementations are **open stacked PRs**. Never assume `main` contains the latest code merely because a PR CI is green.
- A SHA verifies content identity, not physical source truth, biological independence, or issuer authority.

---

## 7. What “done” means for the next phase

The next meaningful milestone is **not another historical audit** and not another fixture PASS.

It is:

1. independently accepted Task3 mechanics with a still-explicit absent real issuer;
2. repaired and independently accepted observation/G7/encoder trust boundaries;
3. a deciding-lane observation-depth contract;
4. authenticated enough source/right semantics to run the same scientific producer/gates on a candidate-neutral known-truth world;
5. one identifiable world and one legitimate no-winner world adjudicated by external hidden truth;
6. only then a prospective human C2/C3 target qualification.

If a prerequisite is unavailable, record `NOT_ESTIMABLE` or the exact external blocker. Do not manufacture authority from fixture labels or passing CI.

**Standing authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
