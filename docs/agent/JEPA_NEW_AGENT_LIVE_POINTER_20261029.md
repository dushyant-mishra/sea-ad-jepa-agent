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


---

## 2026-10-29 execution delta: D1/D2 ruling and PR #500/#501

This appended delta supersedes *the snapshot of open repair progress*, not any frozen science. Always query live PR heads before acting.

**Deciding-lane interface ruling:** the audit #322 branch now holds `docs/agent/JEPA_D1_D2_DEPTH_INTERFACE_DECISION_20261029.md` and its machine mirror `results/target_discovery/unified_qualification_v1/JEPA_D1_D2_DEPTH_INTERFACE_DECISION_20261029.json` (created through audit head `3a1f42a84a61f8a2c3b1919baab25a13aefdeb98`). D1 was **selected only as the prospective, non-promoting V2 content covariate**, using frozen visible-base measured raw counts; D2 was **rejected as default** pending authenticated residual/alias/QC evidence. No legacy `library_size` redefinition, source attestation, real training, or target selection.

- **#486**, independently reviewed by ChatGPT tests-only #499: 4/4 Linux/Windows × NumPy1/2 passed at `f97af8f669752e1a34cf62a9e1e6069089b28644`, run `40895491010`. Accept incremental numeric/parameter registry fixture mechanics, not operator semantics or authenticated calibration.
- **#495**, A3 exact-type repair, author CI green. **#496**, A1/A2 fixture bound-content proposal: unchanged Macha #481 A1–A3 targeted 23/23 pass, but cumulative red owing to contradictory historical V2 shape-only count acceptance and other inherited REDs. **Do not merge as production V2**. Split and review a genuinely versioned content consumer; keep #474 A4 RED and original reviewer tests immutable.
- **#497**, G7 metaclass repair, retains R1/R1D/R2 hostiles RED. Stacked **#500** introduces one composed E3 binder → frozen-row check → V3 fixture path; exact head `27d9dc450f47dbf0829922d9c22a2d5df8fd93e4`, run `40898122458` passed Ubuntu/Windows. Legacy direct V3 stays callable but not qualified as this path; no source authentication.
- **#498**, canonical exact-type/exception-cause repair, independently reviewed by tests-only **#501** exact head `abf65eb758efe98fa1f43e702d3f1f0dec82a31d`. Run `40898494819` passed all 4 Linux/Windows × NumPy1/2 jobs. Inherited `40898494798` still fails T2-D external independent-scan issuer; live generator trust unqualified.

**Next execution:** version the #496 content contract rather than silently changing shape-only expectations; coordinate #474 A4; independently qualify G7 R1/R1D/R2 physical source/QC/alias/donor provenance and T2-D custody; link real rights to a durable issuer before biological PS Task4.

The standing no-authority state is unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.


---

## Live 2026-10-29 #502 V2 content version-split execution receipt

**New draft PR #502** exact head `0789247cdbbdfca671613b020865aba958dfd699` introduces a **separate fixture-only rights-bound V2 content law** alongside unchanged historical V2 shape-only validation. The D1 per-cell base-visible measured sum is checked in the new consumer, but the producer's in-process rights map is not an independent source issuer. No V1/G7 `library_size` change; D2 OFF.

**Author CI on #502:** [run 40902399672](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40902399672) PASS Linux and Windows. Each platform: 22 original V2 shape/A3 checks, 14 independent new fixture content hostiles, 23 explicitly **adapted** Macha #481 reviewer cases (A4 excluded), 106 original source/producer regressions; all six final-head workflow runs passed. Original Macha #481 reviewer source is retained byte-identically (blob `3dda6c2cc9be19d5daececfb07967e94067519f6`) in a non-auto-discovered module. This is NOT a new independent Macha review of #502; reviewer acceptance still pending. The earlier #496 compatibility-conflict RED and #502 failed intermediate runs remain historically valid.

**Macha parallel assignment** documented in PR #474 comment `6500893535`: author a fresh **upstream #474 A4 zero-base refusal noninterference** repair, independently test unchanged counterfactual class+message, then review ChatGPT #502 separately in a tests-only adversarial branch. Coordinate source/ETL R1/R1D/R2 without falsely inferring physical or donor identities.

Audit #322 machine custody: `results/target_discovery/unified_qualification_v1/JEPA_V2_BOUND_CONTENT_502_EXECUTION_20261029.json`, created at audit head `00aee012fd7595eb544679f5d557b0d40d60c4af`.

Standing stop: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.


---

## 2026-10-29 V2 private pair preflight — PR #503

**New stacked draft PR #503** head `f93aa8a7132fa02fa2c7be7c7ddfca4dfec6f325`, based on unchanged #502 head `0789247cdbbdfca671613b020865aba958dfd699`. Adds `observation_v2_private_pair_coherence_v1.py` to privately snapshot and verify separate student/teacher V2 D1 views, rights/query roster, cell/source/donor/operator identity, and exact base counts without returning the teacher digest, query count, private rows, or physical total. Does not alter the prior V2 producer or consumer.

**Author CI:** [run 40903779280](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40903779280) green Linux and Windows; 15 new + 55 inherited V2 + 106 producer tests per OS, six total PR workflows PASS. Await independent reviewer. Deliberate synthetic counterexample: an independently issued student view with one hidden q count and teacher view with another can still pass the coherence check. Therefore **same physical source, feature alias closure, donor/specimen identity, source/QC independence and G7 V2 remain unqualified**. G7 V1 `library_size` cannot be replaced by D1; #500 composed V3 fixture is separately nonpromoting. D2 OFF, #474 A4 RED under Macha ownership.

Machine custody mirror in audit #322: `results/target_discovery/unified_qualification_v1/JEPA_PRIVATE_V2_PAIR_COHERENCE_503_20261029.json`, created at audit head `1cfc6e47e81520cefa06f7211c379f89339de202`.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.


---

## 2026-10-29 R2 uploaded archive + Macha A4 independent acceptance + V2 composition

**New audited uploaded archive source:** Draft **PR #505** exact head 3eecdd464c9b43f01490c250852dba18185b3844. It is a read-only LOCAL audit of the historical August FOUNDATION_CALIBRATION_BUNDLE_20260824.zip, archive SHA-256 07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444. It checks 42 × 41,238 = 1,731,996 matrix/address support records with exact namespace crosswalk, 11,435 main collision pairs plus 14 supplemental nonoverlapping pairs, and the archived loader's override to 11,449 unresolved. It finds an archived source_library-based log1p(CP10K) normalization dependency; synthetic counterfactual proves a q-leak ONLY IF q contributes to that denominator. This is not an empirical human-cell claim or current physical feature closure. PR #505 synthetic code CI run 40907288365 Linux/Windows, 16 PASS per OS. No human expression/phenotype rows or source archive bytes committed to GitHub.

**Macha #474 A4:** Macha new repair #504 source head b66c23e589249360b20103dff8cdc88b9df72a19. Independently reviewed by ChatGPT tests-only **PR #506** head 61da252cea0201d3d51f4519534322c803d9aa26; run 40907800828 passed **4/4** Linux/Windows × NumPy1/2 jobs, with 10 independent + 28 original A4 + 101 original producer tests per OS. Verdict ACCEPT_INCREMENTAL_A4_REFUSAL_NONINTERFERENCE__FIXTURE_ONLY, inside exact integer domain < 2**53. Macha #504 author Windows checkout remains a path-length error prior to test; independent scoped checkout ran successfully. Physical/source/issuer R1/R1D/R2 still RED.

**New stacked combined #508:** exact head 414cee7b448c94c7479a437cddd19f4b2298af4c based on #503, carries **byte-identical** independently reviewed Macha source blob 10a02426e0b8ec079831c26bfae972586533d4f1 and original Macha A4 tests. Run 40908710258 passes 4/4 Linux/Windows × NumPy1/2 jobs; every OS ran 7 composition tests (including original #481 A4 via explicit V2-bound adapter), 28 Macha A4, 106 producer and 70 V2 shape/bound/pair/adapted hostiles. All seven PR #508 workflows green. This is synthetic mechanical composition, not independent Macha acceptance of ChatGPT #502/#503, not external source rights and not G7 E3 V2.

Audit machine mirror at #322: results/target_discovery/unified_qualification_v1/JEPA_20261029_R2_ARCHIVE_A4_V2_COMPOSITION_EXECUTION_DELTA.json (appended at audit head e90011c6c06ac963ff82288b86bdb0311c4ab176).

**Next nonrepeat dependency:** source-authorized raw feature/alias census; source_library and depositor QC/selected-cell invariance; physical nucleus and specimen/donor witness; durable query-rights/known-truth issuer; then independently reviewed versioned G7 E3 V2 source→student/teacher→decision. Keep D2 residual OFF and legacy physical G7 V1 library_size distinct. No Task4/Stage4/training.

TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED.
