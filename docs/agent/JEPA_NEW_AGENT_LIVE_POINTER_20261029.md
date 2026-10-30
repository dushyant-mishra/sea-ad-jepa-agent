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


---

## 2026-10-29 post-Macha #507/#509 decision and student-only V2B draft #510

**Reviewer correction:** Macha #507 head `a4894f366b9d73df03a675d0b70383dea6a36454`, unchanged tests-only, found **4 RED** on ChatGPT #502: a shared public teacher-view validator membership oracle recovers (7,23) hidden q counts without teacher digest, and caller-issuable uncommitted rights/query policy can expose higher rights behind a decoy. #502 is **REPAIR_REQUIRED__UNSAFE_FOR_STUDENT_USE** despite earlier author CI and later #503/#508 mechanics. Preserve original #507 RED and do not promote the old API. PR #507 was directly acknowledged in issue comment 6505243256.

**Identity/source audit correction:** Macha #509 exact head `3e5694e2c1b959c8e21f9fc6dd50cbf694ac4013` shows #492's claim that stage81a2r final all-feature decision table lacks GitHub SHA/bound bytes and alias audit cannot run was incorrect. The 2026-09-02 preservation manifest and committed 17,002,348-byte decision table are identified in #509, which executed identity-level alias probe without expression. ChatGPT attempted a direct #492 correction comment; GitHub permission blocked it. Corrective comment is instead on #509 (6505197594) and machine decision mirror on audit #322 `JEPA_NPH52_RIGHTS_ISSUER_AND_507_509_DECISION_20261029.json` (created at audit head `042a5076bd097866527a28b0c6892039d2d0df75`), 23/23 audit CI PASS. Candidate decision-table custody still does not establish external biological identity/physical source.

**Deciding-lane ruling:** NPH52 symbol-only off-ledger features are not negative per-query clearance. **NPH52 real query issuance blocked** until independently reviewed unambiguous source identifiers, all off-ledger/query alias classes and query-selection/QC contract; metadata-only work may proceed under existing firewalls. The 18 candidate in-ledger legacy/current alias pairs and 11 current at-risk addresses must be co-restricted or excluded pending identity adjudication. **No access authorization for quarantined NPH52 reader-fit expression** is granted; metadata-only depositor annotation and QC history first, then an independently approved, explicitly limited expression protocol if scientifically necessary. SEA-AD brain regions are nested repeated specimens within donors; between-person donor inference must cluster by donor, not count regions as new donors.

**New separately named student-only V2B:** ChatGPT draft PR #510 stacks on #508, original #502 unsafe public method unchanged. Its `validate_public_student_v2b` refuses every teacher view before digest or issuance lookup; uses only student-visible values and an explicitly passed frozen policy; no teacher membership lookup. Its own 13 adversarial tests per Linux/Windows NumPy1/2 passed run `40932450755` (4/4). However at head `aebe4341265302663799b8f0f50de9bfdc6909dd`, broader Task2 and Task3 repository discovery each had **1 failure / 512 passing**: an inherited adapted reviewer test encounters a shared process-local registry policy collision. A proposed fixture isolation edit was tool-blocked; **#510 cumulative CI RED, no independent reviewer acceptance**. More importantly the caller can self-supply a false policy, so no external source rights issuer or security boundary has been established. Do not deploy as authentic human-data student interface. #507 original RED remains.

**State:** `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.


---

## Later 2026-10-29 exact-head supersession: PR #510 CI now GREEN (author mechanics only)

**Supersedes only the prior paragraph's #510 CI RED snapshot**: new #510 exact head `ef51325d0c31bbac2eb0bf74bd3f770d244657f2` passes all **6/6** workflows. Dedicated [run 40932955463](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40932955463) passed 4/4 Linux/Windows × NumPy1/2 jobs; per platform 13 new student-only attacks, 14 bound V2, 15 pair, 7 exact-source composition, 28 Macha #504 A4. Both broad Task2 and Task3 workflows passed on the final head. A process-local issuer fixture digest collision in the original new synthetic cells was resolved by namespacing **only the new test cell IDs**. No old Macha review, original #502 code or original producer source changed. Historical failed CI remains a real intermediate receipt.

**Do not supersede the more important scientific RED:** Macha #507's teacher-view oracle and self-issued rights attacks on original #502 are still valid. The new versioned V2B accepts only STUDENT-role views and never queries teacher issuance, but independent issuer policy authentication, enforced student/teacher process separation, physical source provenance, specimen/donor identity and query/QC alias closure remain unqualified. A caller supplying its own `expected_policy` does NOT gain authority. #510 has **author CI only**, not independent Macha review.

Audit #322 machine author-CI delta: `results/target_discovery/unified_qualification_v1/JEPA_507_509_V2B_510_AUTHOR_CI_DELTA_20261029.json` created at audit head `93b2368ae41d28e51b9404ad53cbeeb8d460f932`. Source decision #509 and NPH52 quarantine/no-symbol-issuance from the preceding section remain unchanged.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.


---

## 2026-10-29 source-total-free D1 student projection — draft PR #511

**New independent engineering increment PR #511** stacked on #510, exact head `5fe18a11b010b0adb857104d10329e840a9e7d4c`. Source `scripts/v5/td_unified/observation_d1_base_only_student_fixture_v1.py` blob `e70d84383f4011010d207623c035fbcde639d2ad`, tests blob `10dbfc11831a1c5804462b8a04cb9ffa8bbea723`. The new function accepts **already-redacted base counts and an unauthenticated expected policy only**, never full physical library total, teacher/query count or residual. It computes D1 from measured base scalars and publishes only bound-schema student rows through the new #510 student-only validator, with query measured-scalar support required for each selected operator. The historical #502/old V2 producer's physical conservation law is deliberately unchanged.

**Exact-head author CI:** [run 40936357384](https://github.com/dushyant-mishra/sea-ad-jepa-agent/actions/runs/40936357384), all 4/4 Linux/Windows × NumPy1/2 matrix jobs PASS, with **114 new** source-edge cases + 13 V2B defense + 7 Macha #504 composition + 129 original producer/A4 + 14 old V2 content = **277 tests/job**. All six PR #511 workflows PASS. The result is fixture MECHANICS ONLY, with **no independent Macha acceptance** of #511 and independent #510 review pending. Counterexamples deliberately demonstrate q-alias molecules contaminating a base address and q-conditioned source-cell selection changing student bytes. Base-only arithmetic cannot repair those upstream semantic leaks. The method cannot authenticate caller-supplied counts/rights, source physical unit/donor/specimen, depositor QC or source feature alias closure.

**Audit append-only mirror:** `results/target_discovery/unified_qualification_v1/JEPA_D1_BASE_ONLY_SOURCE_EDGE_511_AUTHOR_CI_20261029.json` at audit #322 head `aff351e9f08e4fef229ece2942298ebe1b326192`. No existing dataset bytes were rehashed or modified; 97/97 August archive and FULL104 historical hashed lineage were reused rather than recomputed. Macha owns independent #510 review and local metadata/source verification; do not duplicate.

**Remaining source qualification:** #509 candidate 18 alias pairs and 11 at-risk query addresses, NPH52 symbol-only negative clearance blocked and quarantined reader-fit expression not authorized, depositor QC query dependence, physical nucleus/specimen/donor identity, externally trusted policy/redaction issuer, strict separate teacher/student custody and new G7 E3 V2. Old #502 public teacher oracle remains RED. No real training/Stage4/PS Task4 authority.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.


## Macha #512/#513 decision and V2C author result, 2026-10-30

Macha #512 head 16b5bc6c050222c592f88c35dc65b0a256d65402 remains REPAIR_REQUIRED on old #510/#502, preserving ten new RED and four #507 RED. Macha #513 head 0b1af4f06ba423753899e7c564d3b16ce609ac6a reports 322 ETL artifacts checked, no drift/missing within SHA-versus-size scopes; 8,915 blocks counted not rehashed; adapter inventory is 50 (historical note 47 was not reconciled). #509's registry was already pinned by #492.

Deciding-lane policy: provisional joint withholding of UBE2R2-AS1 with its legacy predecessor; MIR4307HG and LINC02588 blocked at affected operators, other eight retained. NPH52 expression-access protocol NOT approved. NPH52 query issuance remains blocked. Issuer role JEPA_SOURCE_RIGHTS_ISSUER designated only as a role, with no actual key/signature identity provisioned. HVS observed gene minimum is not a confirmed depositor rule. SEA-AD sample_id is per cell, not specimen; metadata allowlist excursions disclosed. Detailed machine decision on audit #322: JEPA_512_513_DECISION_AND_ISSUER_ROLE_20261030.json.

New draft #514 head 63099f6b17b14bcfcfd92b0334bf564e9cf8376d stacks on #511, adds a standalone stdlib student-only verifier and receipt commitments to full expected policy and validated view, correcting Macha #512 mechanical receipt concerns on a NEW API. Author CI run 40997285142 4/4 OS NumPy jobs green, all six workflows green. No independent review, real issuer, process isolation or source authorization. Original #512 RED remains unchanged. No Task4, Stage4 or training.

TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED.
