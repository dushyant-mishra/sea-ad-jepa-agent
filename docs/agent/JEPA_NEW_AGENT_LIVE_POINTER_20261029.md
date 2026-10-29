# JEPA new-agent live pointer — use this before any historical recrawl (2026-10-29)

This file is intentionally short. The detailed history already exists. Its purpose is to prevent a successor from wasting a session re-auditing finished work.

## Current long-lived branches

- **Audit PR #322:** exact head `88c24c4669e5e4a57d412d2f18cb78bec9ead2de`.
- **Handoff PR #460:** this branch; verify live head before acting.
- **Original independently reviewed V8e audit:** `a271164554076d0acda3bd0cf0b1bf957c0fdfd3`. Later append-only audit heads do **not** inherit that scientific acceptance.

Machine live pointer: audit #322 `results/target_discovery/unified_qualification_v1/JEPA_NEW_AGENT_LIVE_POINTER_20261029.json`.

## Read in this order

1. `docs/agent/JEPA_NEW_AGENT_BOOTSTRAP_20261029.md` — operational bootstrap and no-repeat rules.
2. `docs/agent/JEPA_SUCCESSOR_FINAL_FREEZE_20261028.md` — current source graph and live review verdicts.
3. `docs/agent/JEPA_SUCCESSOR_MACHA_V2_G7_REVIEW_DELTA_20261028.md` — Macha #481/#482/#483 verdicts and D1/D2/G7 contract analysis.
4. `docs/agent/JEPA_SUCCESSOR_TASK3_CHATGPT_INDEPENDENT_REVIEW_20261028.md` — independent RED of Task3 #437.
5. Only use older takeover/master documents for source lookup, not as current action plans.

## First three actions — do these before anything historical

### 1. Independently review Macha Task3 repair #486

Exact head `f17080516f77e79fb6f6cb44903cbabdb2a85dd7`.

The old #437 code is already independently RED in ChatGPT #480 for numeric aliasing and open-ended `OBS_` semantic spoofing. #486 is author-green but **not independently accepted**.

Attack:
- exact numeric comparison across int/float/bool-like edge cases;
- nonfinite and cross-type numerics;
- closed observation-parameter name registry and semantic spoofing;
- any route from fixture/self-pinned source to false calibration authority.

Do not rerun the old #437 audit except to verify the pinned repair against immutable #480 tests.

### 2. Repair #479 against unchanged Macha #481 tests

#479 head `ae762d7096a94ac663a0788f6f577ba404e37536`; #481 review head `957fa4a558ce2bd219b5c2dec6dad8f65dca81ab`; verdict **REPAIR_REQUIRED**.

Fix only the real defects:
- A1 depth spoofing: consumer accepts physical total/offset/scale in the released depth field.
- A2 self-declared student view can expose non-base rights.
- A3 metaclass route.
- A4 belongs upstream in #474/Macha when explicitly assigned.

Preserve the positive 240-world noninterference result at its exact scope. Do not expose teacher/private digests to the student; small hidden domains can be enumerable.

### 3. Repair #476 and #477, preserving external-source RED

**#476** head `26031df25b51087f2f3ec35a88eef2919d794c68`; Macha #482 head `58baa4f912c791866c1aae31eab797da9dca588a`.
- Repair exact-type/metaclass dispatch.
- Create one reviewed **bind → immutable snapshot → V3** composed entry so V3 cannot bypass binder evidence.
- Do not silently alter V3 decision law.
- R1 physical identity, R1D donor/specimen pseudoreplication and R2 normalization provenance remain RED.

**#477** head `c83088de090bc4f2fc6bbee353c46070bcca7be5`; Macha #483 head `48ec018735a095571a0bfaa25b33f9b9deb40b39`.
- Use exact `type(x) is` dispatch before any `isinstance`/payload `__class__` access.
- Refuse chained payload exception causes with `from None`.
- Preserve external T2-D issuer RED.

## Decision the new agent must not silently make

Macha proposes:

- **D1 / `VISIBLE_BASE_MAPPED_SUM_V1`** = sum of student-visible base-rights measured scalar counts. Candidate default because it uses no private physical total and is directly consumer-verifiable.
- **D2** = D1 plus source residual. Nondefault unless per-query/operator off-ledger alias and source-feature completeness are independently qualified.
- Preserve CaseBundle/G7 V1 physical `library_size` semantics. If D1 is accepted, create a versioned V2 content law; do not rename D1 to `library_size`.

This is a deciding-lane scientific contract choice. Record an explicit acceptance/rejection; do not let implementation code decide it accidentally.

## Do not re-audit or rerun by default

Treat the following as complete at their exact historical scope unless a pinned source changed, new independent executable evidence contradicts them, or the scientific question is prospectively changed:

- PR #314 corrected one-shot TD56/57B/57C/59 replay.
- R5 query-measured developmental target experiment.
- V44 real-RNA teacher proxy.
- Stage69/70 rare work.
- PR #164 separate-nucleus RNA/ATAC and PR #77 macrophage perturbation evidence.
- PR #328/#369/#451/#469 fixture mechanics.
- PR #471 historical 97/97 archive hashing.

Do **not** infer:
- same-cell pairing from separate nuclei;
- TF binding from motif/SCENIC+/chromVAR alone;
- adult microglial causality from macrophage perturbation;
- physical source truth from SHA equality;
- target construction from a surrogate predictor;
- scientific qualification from CI green.

## Data/custody reminders

Large historical archives and checkpoints are hash-indexed; not all raw bytes are guaranteed to exist on GitHub. A digest is not a retrieval mechanism or issuer proof. Do not download project-prohibited BAM/FASTQ data. Do not copy incidental sample-level diagnosis/age/sex into audit/handoff.

All current work is stacked open PRs. Never assume `main` contains the reviewed code.

## What comes after the repairs

Only after Task1–3 mechanics, calibration/source-right semantics, observation contract and G7 are independently qualified:

1. implement the **candidate-neutral V3.1.1 production-synthetic Task4 biology generator** — currently absent;
2. run one identifiable and one legitimate no-winner sealed known-truth challenge through the **same scientific producer/gates**;
3. only then return prospectively to human C2/C3 target qualification and downstream JEPA.

`TARGET_NONE` is a valid result.

**Standing authority:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
