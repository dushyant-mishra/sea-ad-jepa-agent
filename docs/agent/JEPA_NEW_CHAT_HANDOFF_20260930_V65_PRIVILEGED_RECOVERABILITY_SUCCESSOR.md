# JEPA New-Chat Handoff — V64 successor: exact controls, privileged-information boundary, promoter authority, and recoverability

**Date:** 2026-09-30  
**Purpose:** canonical takeover package for the next ChatGPT agent.  
**Branch:** `chatgpt/v64-privileged-information-recoverability-20260930`  
**Branch head at handoff creation:** `9abb4a1daa00f6bfc7b44b286d88c974a951fc45` before this handoff commit sequence.  
**Draft PR:** #199 against `handoff/jepa-v64-target-architecture-20260930`

---

## 0. Read this first

This project is **not at training**.

Hard governance remains:

- **TRAINING = OFF**
- **Phase B = STOPPED**
- **Stage 4 = NOT AUTHORIZED**
- **TD60 = BLOCKED**
- **Morabito = PROTECTED**
- protected biological correspondence remains unopened unless separately authorized;
- do not tune scientific gates after viewing outcomes;
- do not convert NOT_MEASURED into zero;
- do not treat resource count as evidence-independence count;
- do not let a small, selected multimodal cohort redefine the universal biological state by default.

The central objective remains a JEPA-like **query-conditioned biological state**, not prediction of a hidden expression scalar.

The key architecture change developed in this chat is the **privileged-information boundary**:

> Rich regulatory measurements may constrain, validate, or augment the RNA representation, but only the portion of privileged state that is demonstrably recoverable from lawful RNA can become compulsory universal RNA-student supervision.

---

# 1. Refresh live heads before doing anything

Verified live state at handoff preparation:

### Current ChatGPT architecture branch

`chatgpt/v64-privileged-information-recoverability-20260930`

Verified head before handoff commit:

`9abb4a1daa00f6bfc7b44b286d88c974a951fc45`

Draft PR:

`#199 V64 privileged-information boundary and recoverability architecture`

PR is draft and mergeable against:

`handoff/jepa-v64-target-architecture-20260930 @ ad3a33198fc23292b09db5e3ea6d297fdf19f3fd`

### Claude execution branch

`claude/v64-exact-sampler-successor-20260930`

Verified live head:

`f2b45699d1be88cc599971da243ba6e36a50c4a7`

This is the execution authority for the repaired exact-control sampler lane.

### Prior canonical audit/science branch

`chatgpt/v64-e2-single-source-successor-20260929`

`23255baaf81381d5c22c655a605642db27f2a173`

### Prior handoff branch

`handoff/jepa-v64-target-architecture-20260930`

`ad3a33198fc23292b09db5e3ea6d297fdf19f3fd`

Always refresh all of these before interpreting current state.

---

# 2. Three lanes are intentionally separate

Do not collapse these into one execution stream.

## Lane A — Claude exact-control / Phase-A execution

Claude owns:

`exact supplement -> frozen sampler qualification -> Phase-A rerun -> HARD STOP`

Current status:

- exact supplement construction is complete;
- all 12 supplement shards independently reconcile;
- S50 ambiguity defect is repaired and production no-op is proven for shard 0;
- **full 64 edge-side real-oracle qualification is NOT yet complete**;
- Phase A must not rerun until that suite passes.

## Lane B — ChatGPT privileged-information / teacher-student architecture

This chat established:

- current V5 teacher/student path is RNA-to-RNA;
- future regulatory modalities cannot be silently appended to the universal teacher;
- privileged factors require explicit recoverability classification;
- universal teacher should remain RNA-native for now;
- rich regulatory encoders should begin as auxiliary critics/validators;
- recoverability must be judged at stable-subspace level when axes rotate.

This lane has architecture contracts, smoke tests and donor split machinery but **no final biological privileged factor has yet been qualified**.

## Lane C — promoter/TSS and regulatory-evidence architecture

This chat established:

- GENCODE v50 defines promoter/TSS candidate existence;
- FANTOM, SCREEN, Dong/Roussos, NIH-CARD, Nott add evidence;
- evidence layers do not censor the denominator;
- promoter evidence must preserve annotation-version drift and ambiguity;
- evidence family and estimator must be separate fields;
- matching/common support must be studied before E2-control matching is frozen;
- apparent evidence independence requires sensitivity analysis.

Do not let Lane C alter the currently frozen Phase-A exact-control rules.

---

# 3. Exact supplement — independently closed at shard-construction level

Claude's exact supplement rollup has been independently imported and audited.

Current independently reconciled totals:

- E2 edges: **20,709**
- edge-sides: **41,418**
- band positions: **1,576,398,690**
- safe affine positions: **1,560,436,760**
- supplement candidate positions: **15,961,930**
- uncovered positions: **0**
- `A_interior = 235,726,268`
- `A_supplement = 177,442`
- `A_exact = 235,903,710`

Exact identities:

`1,560,436,760 + 15,961,930 = 1,576,398,690`

`235,726,268 + 177,442 = 235,903,710`

All 12 shard canonical-content hashes match their receipts.

All shards report `OK`.

All shards agree on E2, PU.1 and liftOver input identities.

Independent audit artifact:

`results/v64/V64_EXACT_SUPPLEMENT_INDEPENDENT_SHARD_AUDIT_V1.json`

Important scientific conclusion:

The exact supplement recovered **177,442 admissible starts** that the single-block affine path alone would have omitted.

Therefore the old completeness gap was real, not hypothetical.

But this does **not** yet mean the sampler is qualified.

---

# 4. S50 ambiguity repair

Claude commit:

`f2b45699d1be88cc599971da243ba6e36a50c4a7`

S50 defect:

The affine shortcut could certify a 5-kb interval inside one plus-strand chain block without checking whether a second chain also maps that target span. The real C3/liftOver gate rejects multi-mapping ambiguity.

Repair:

- chain identity is retained;
- starts shadowed by blocks from another chain are removed from the fast affine-safe set;
- such starts fall through to the exact liftOver supplement oracle.

Production blast-radius result:

- shortcut-accepted hg19→hg38 target span: **2,847,258,323 bp**
- target span additionally shadowed by another chain block: **0 bp**

Positive control:

- F3 fixture planted overlap: **4,000 bp**
- detector found: **4,000 bp**

Stronger production no-op proof:

Shard 0 was rebuilt end-to-end with the repaired builder.

- 3,452 edge-sides;
- all counts identical;
- all interior intervals identical;
- all supplement starts identical;
- canonical payload SHA-256 before and after:

`577f86c530f2a87e108db7e81bb2160def4344bd32999032f91f2e34b35101e9`

Correct interpretation:

S50 is now enforced in the executor and proven to be a no-op for the tested production chain/data.

Do **not** generalize this to arbitrary chain files.

---

# 5. Exact sampler is still NOT qualified

At the user's last Claude report:

- real-edge qualification: **15 / 64 edge-sides completed**
- inequalities: **0 so far**

Claude must finish all:

`32 deterministic real edges × both sides = 64 edge-side comparisons`

Required final report:

- 64/64 completed;
- non-empty comparisons explicitly counted;
- empty comparisons explicitly counted;
- zero inequalities;
- total candidate starts compared;
- supplement-involving cases where applicable;
- all deterministic fixtures;
- uniformity test;
- all frozen failure-path tests.

A 0-vs-0 equality is not affirmative evidence.

**Phase A remains blocked until this completes.**

Do not infer qualification from the first 15 sides.

---

# 6. Phase-A rule

If and only if the complete sampler suite passes:

rerun repaired Phase A from the exact 20,709-edge denominator.

Report the full funnel and then:

**STOP FOR INDEPENDENT AUDIT.**

Do not open Phase B.

Do not open Stage 4.

Do not open Morabito.

Do not enable training.

---

# 7. Privileged-information boundary — major architecture result

Current V5 runtime audit found:

- teacher and online/student are the same RNA encoder family;
- teacher receives measured RNA support;
- student receives masked RNA support;
- teacher target blocks are RNA-derived;
- current semantic authority defines one biological/query-local latent state;
- there is no native privileged-private/recoverability factorization.

Therefore:

**adding ATAC/promoter/enhancer/contact/genetic/perturbational inputs to the current teacher is a real architecture change.**

It must not be treated as a drop-in enrichment.

Audit:

`results/v64/V64_PRIVILEGED_INFORMATION_RUNTIME_AUDIT_V1.json`

Contract:

`docs/agent/V64_PRIVILEGED_INFORMATION_RECOVERABILITY_CONTRACT_20260930.md`

Decomposition protocol:

`docs/agent/V64_PRIVILEGED_STATE_RECOVERABILITY_DECOMPOSITION_PROTOCOL_20260930.md`

---

# 8. Four recoverability states

Every future privileged/regulatory factor must end in exactly one of:

## RNA-RECOVERABLE

The factor/subspace is reproducibly predictable from lawful RNA on prospective biological holdouts, exceeds relevant simple technical/activity baselines, survives availability/shortcut diagnostics, and has stable factor geometry.

Only this state is eligible for compulsory universal RNA-student supervision.

## PARTIALLY-RNA-RECOVERABLE

Only a prospectively selected stable subspace is reproducibly RNA-predictable.

Only the locked shared subspace may become compulsory RNA supervision.

The private residual must be preserved.

## REGULATORY-PRIVATE

The privileged factor has credible biological support but is not reproducibly inferable from RNA.

This can still be highly valuable biology.

It may serve validation, multimodal inference, uncertainty, biological adjudication, relational constraints or held-out evidence-family tests.

It must **not** become a compulsory target for RNA-only cells.

## UNQUALIFIED

Default conservative state when biological reliability, recoverability, factor stability, common support or shortcut exclusion is insufficient.

Poor RNA prediction alone does not justify REGULATORY-PRIVATE.

High RNA prediction alone does not justify RNA-RECOVERABLE.

---

# 9. Preferred architecture

Do **not** replace the universal teacher with one giant rich multimodal teacher.

Current preferred prospective topology:

## Universal path

`FULL104 RNA -> online RNA encoder -> predictor -> RNA EMA teacher`

## Privileged path

paired/regulatory evidence:

`regulatory measurements -> privileged encoder/critic -> Z_priv`

then:

`Z_priv -> recoverability qualification -> shared/private classification`

Only qualified shared/recoverable structure may later become factor-specific auxiliary RNA supervision.

Machine-readable architecture:

`results/v64/V64_UNIVERSAL_RNA_PLUS_PRIVILEGED_CRITIC_ARCHITECTURE_V1.json`

Architecture rationale:

`docs/agent/V64_UNIVERSAL_RNA_TEACHER_PRIVILEGED_CRITIC_ARCHITECTURE_20260930.md`

---

# 10. Recoverability must beat shortcut baselines

High RNA R² is not sufficient.

A regulatory factor may look RNA-predictable because both are driven by:

- library depth;
- detected-gene count;
- generic activity;
- promoter accessibility;
- ATAC depth;
- evidence availability;
- E2 degree;
- dataset/operator identity.

Therefore future recoverability qualification must compare against prospective shortcut baselines.

Contract:

`docs/agent/V64_RECOVERABILITY_SHORTCUT_AND_TEACHER_IMMUTABILITY_CONTRACT_20260930.md`

Key rule:

> The privileged factor must be frozen before final recoverability testing. The teacher cannot move, rotate or simplify itself on TEST to become easier for the student.

If RNA was used in constructing the privileged factor, that contribution must be declared because recoverability can otherwise become tautological.

---

# 11. Rotation-aware shared/private split

Do not interpret individual latent axes unless basis stability supports them.

When axes rotate but the subspace is stable, qualify the subspace using rotation-aware measures such as:

- principal angles;
- canonical correlations;
- Procrustes alignment;
- eigen/singular-value gaps.

TEST may not select:

- factor rank;
- favorable rotation;
- feature set;
- threshold.

Synthetic software smoke already demonstrated:

- true shared state is recoverable;
- independent private state is not;
- forcing shared+private into one compulsory target lowers attainable recovery;
- a rotated shared subspace remains recoverable at subspace level.

Smoke receipt:

`results/v64/V64_PRIVILEGED_INFORMATION_ARCHITECTURE_SMOKE_RECEIPT_V1.json`

This is software evidence only, not biological qualification.

---

# 12. Paired NIH-CARD development subset

Claude's successor branch physically contains:

`results/v64/gpt_handoff_bundle/nihcard_paired_subset.npz`

Exact SHA-256:

`6dca0d35ed7fd6cc16bc086a07e36a9f4dc178b71608d0fdf4de2727428e00a6`

Structural audit in this chat established:

- 2,160 unique paired nuclei;
- 24 donors;
- exactly 90 microglial nuclei per donor;
- 4,000 genes;
- 12,000 ATAC peaks;
- raw nonnegative integer counts;
- sparse matrices have no duplicate coordinates;
- exact RNA/ATAC pairing reconciles 2,160/2,160.

No RNA↔ATAC biological recoverability result has yet been opened from this subset.

---

# 13. Outcome-blind donor split is frozen

Using only donor IDs and seed:

`20260930`

Rule:

sort donor IDs by:

`sha256("<seed>|<donor_id>")`

Then:

- first 16 donors = TRAIN;
- next 4 = VALIDATION;
- last 4 = TEST.

Counts:

- TRAIN: 16 donors / 1,440 nuclei
- VALIDATION: 4 donors / 360 nuclei
- TEST: 4 donors / 360 nuclei

Receipt:

`results/v64/V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json`

Generator:

`scripts/v64/freeze_nihcard_paired_donor_split_v1.py`

Do not reshuffle this split after viewing recoverability.

Cell-random splits have no scientific authority.

---

# 14. What has NOT been done on paired NIH-CARD yet

Do not let the next chat assume this is already a biological result.

Still needed:

1. define a bounded privileged factor using TRAIN only;
2. declare whether RNA enters factor construction;
3. freeze factor geometry/rank using TRAIN/VALIDATION only;
4. freeze RNA predictor and shortcut baselines;
5. perform donor-held-out recoverability qualification;
6. preserve private residual;
7. only then evaluate TEST;
8. where feasible, validate with a held-out evidence family.

Do not use TEST to choose the decomposition.

Do not jump straight to joint multimodal training.

---

# 15. Promoter/TSS candidate universe

Candidate denominator rule:

**GENCODE defines candidates. Measurement resources add evidence.**

Current reference:

GENCODE human Release 50 / GRCh38.p14.

Current counts from the comprehensive chromosome annotation:

- transcript candidates: **644,292**
- genes represented by transcript candidates: **78,733**

This is an annotation denominator, not a statement that every transcript is active in brain or microglia.

Contract:

`docs/agent/V64_PROMOTER_TSS_CANDIDATE_UNIVERSE_CONTRACT_20260930.md`

Executable builder:

`scripts/v64/build_promoter_candidate_ledger_v1.py`

No evidence layer is permitted to remove a GENCODE candidate.

---

# 16. SCREEN promoter-like cCRE evidence

SCREEN Registry V4 GRCh38 promoter-like cCREs are used as **evidence**, not denominator.

Current preliminary GENCODE-TSS overlap:

- GENCODE transcript candidates overlapping SCREEN PLS: **377,974**
- ~58.7% of GENCODE transcript candidates

This demonstrates why SCREEN cannot define candidate existence.

Access is public download.

Do not overclaim the data license; the registry currently records SCREEN data terms conservatively as not separately verified.

---

# 17. FANTOM coordinate warning and correction

Important discovery:

The FANTOM hg38 annotation table includes legacy `hg19::chr...` strings in its peak-identifier field.

Do **not** parse those legacy IDs as hg38 coordinates.

Coordinate authority must be:

`hg38_fair+new_CAGE_peaks_phase1and2.bed.gz`

Annotation authority can remain the separate annotation table.

The isolated GitHub Actions workflow successfully fetched and validated the actual hg38 BED:

`.github/workflows/v64-fetch-fantom-hg38-cage-bed.yml`

Latest successful run observed during this chat:

run `36749777293`

Artifact name:

`v64-fantom-hg38-cage-bed`

The next chat should materialize this artifact and run the promoter ledger builder with `--fantom-bed`.

Do not use the legacy hg19 identifier field as coordinate authority.

---

# 18. Dong/Roussos open human-brain promoter package

Article:

DOI `10.1038/s41467-024-54448-y`

All four relevant supplementary tables were byte-validated in this chat.

## Supplementary Data 7

Promoter-isoform annotations:

- 118,121 data rows;
- 118,033 unique transcript IDs;
- 58,825 unique gene IDs;
- fields include transcript/promoter-isoform, chromosome, TSS, strand, internal-promoter flag, gene, 5'-most flag.

SHA-256:

`6a46fd3bfdff213ca11111975ef01958be8238c349559e90dca43e5857a1d1dd`

## Supplementary Data 8

Regional differential promoter-isoform usage:

- 10 comparison sheets;
- 12,510 promoter isoforms per comparison;
- 10,767 genes.

SHA-256:

`eb3c2e0eaf055bac3954802497cbdd07ccc65638ae361e1cf9af10668f224a74`

## Supplementary Data 9

Alternative promoter-isoform events:

- 1,715 rows;
- 1,368 unique transcripts.

SHA-256:

`0d8b9e38c8a6502bd5a4851ffe408ad43771b5591ea5282c9547acd1c1bb5076`

## Supplementary Data 10

Promoter-isoform-resolution enhancer-promoter ABC links:

- 252,512 rows;
- 131,663 unique OCR intervals;
- 13,049 genes;
- 24,992 unique transcript IDs;
- 9 brain regions;
- ABC score min 0.02;
- median 0.031;
- max 0.732.

SHA-256:

`c2005fb8947b4352450a9a86f297673cce5350aab1b2ac69fe3949317c4f1f59`

Use Data 7–10 as contextual brain promoter/link evidence.

Do not use them as the base candidate denominator.

Data 10 is ABC-derived evidence, not an independent causal family.

---

# 19. Dong ↔ GENCODE bridge correction

Important implementation finding:

Dong Data 7 contains **88 repeated ENST IDs**, primarily chromosome-specific chrX/chrY records.

Therefore:

`ENST alone is not a universally safe join key`

for Dong evidence.

Use:

`(transcript_id, chromosome)`

for Dong evidence attachment.

Current corrected bridge:

- Data 7 unique transcript IDs: 118,033
- unique transcript IDs present in GENCODE v50: **115,678**
- ~98.0%
- exact gene+chr+TSS+strand matches: **92,669** in the corrected audit lineage; the executable ledger should be treated as final authority when fully rerun.

Current audit:

`results/v64/V64_DONG_ROUSSOS_PROMOTER_RESOURCE_CUSTODY_AND_BRIDGE_AUDIT_V1.json`

The chat originally produced row-level counts that slightly overstated transcript presence. Those were corrected.

Do not revive the older row-level counts.

---

# 20. Promoter ledger implementation status

Builder is committed:

`scripts/v64/build_promoter_candidate_ledger_v1.py`

Design:

Every GENCODE transcript/TSS candidate is emitted.

Evidence fields attach:

- SCREEN PLS overlap/count;
- Dong any-transcript presence;
- Dong same-chromosome presence;
- Dong gene match;
- Dong coordinate match;
- Dong internal-promoter / 5'-most evidence;
- FANTOM CAGE overlap/count.

The builder is now chromosome-aware for repeated Dong ENST records.

Next immediate promoter task:

1. materialize FANTOM hg38 BED artifact;
2. run the builder over GENCODE + SCREEN + Dong Data 7 + FANTOM;
3. produce the full ledger and receipt;
4. audit candidate row count remains exactly the GENCODE denominator;
5. quantify evidence coverage without using any evidence source as an inclusion gate.

---

# 21. Evidence independence and matching

Do not call:

`P(B|A,X) - P(B|X)`

an independence estimate.

Because X is measured with error, use:

**incremental support under observed adjustment**

and require sensitivity analysis for:

- measurement error;
- omitted/shared causes;
- alternative lawful adjustment sets;
- common-support/trimming dependence.

Contract:

`docs/agent/V64_COMMON_SUPPORT_AND_EVIDENCE_SENSITIVITY_CONTRACT_20260930.md`

Before E2 matching:

1. characterize support;
2. quantify trim fractions for candidate designs;
3. freeze matching operator;
4. only then open the biological comparison.

If no lawful match exists:

trim and count.

Do not widen tolerances after seeing outcomes.

---

# 22. Same evidence family vs different estimator

SCARlink and SCENT run on the same NIH-CARD cells/donors/modalities.

Therefore:

- same paired-observational evidence family;
- different estimator.

Agreement is robustness to estimator choice.

It is **not** two independent biological confirmations.

Future evidence ledger separates:

- measurement_source
- evidence_family
- estimator

Schema:

`results/v64/V64_REGULATORY_EVIDENCE_LEDGER_SCHEMA_V1.json`

---

# 23. Held-out evidence-family standard

Preferred validation:

`construct from evidence A/B/C -> lock -> test on mechanistically distinct family D`

Examples:

- construct without contact -> validate on held-out contact;
- observational construction -> validate on perturbation;
- construction without genetic evidence -> validate on eQTL/caQTL.

A new algorithm using the same measurements is not a held-out evidence family.

Contract:

`docs/agent/V64_HELDOUT_EVIDENCE_FAMILY_VALIDATION_CONTRACT_20260930.md`

Morabito remains protected and is not opened by this contract.

---

# 24. Availability shortcut

Known diagnostic population:

**379 E2-anchored genes are not RNA-measurable in NIH-CARD microglia.**

They are:

`structurally anchored / paired RNA not measurable`

not regulatory negatives.

Preserve states:

1. MEASURED_AND_SUPPORTS
2. MEASURED_AND_DOES_NOT_SUPPORT
3. NOT_MEASURED
4. UNRESOLVED where appropriate

Never zero-fill NOT_MEASURED.

Use the 379-gene stratum later as an availability-shortcut probe.

---

# 25. Address != gene != promoter

A critical identity contract is now committed:

`docs/agent/V64_ADDRESS_GENE_PROMOTER_IDENTITY_CONTRACT_20260930.md`

Current FULL104 discovery subset contains a backbone of:

**17,186 addresses**

This is NOT currently authorized as:

**17,186 genes**

Any coverage fraction requiring genes must use an audited address→gene bridge.

Never compute:

`E2 genes / common addresses`

as though the namespaces were equivalent.

---

# 26. FULL104 discovery subset

Exact binary became physically available in this chat runtime:

`full104_discovery_subset.npz`

Bytes:

`50,646,637`

SHA-256:

`615e57e3f45cc2bc020e3b48ed5401a9aa65323d82a919e7d577e9642e34be8f`

Structure inspected in this chat includes:

- 6,000 cells;
- 17,186 backbone address indices;
- 21,750,141 sparse triplets;
- donor/source/operator/sample/native-class/broad-class/cell ID metadata.

Important:

The binary itself is **not physically committed through the GitHub text connector**.

Its exact custody/recovery state is recorded in the chat-exclusive asset manifest.

---

# 27. Chat-exclusive asset custody

Canonical new custody package:

`docs/agent/archive/chat_runtime_20260930_v2/`

Read first:

`docs/agent/archive/chat_runtime_20260930_v2/CHAT_RUNTIME_EXCLUSIVE_ASSET_CUSTODY_20260930_V2.json`

and:

`docs/agent/archive/chat_runtime_20260930_v2/README.md`

This package distinguishes:

- `bytes_in_git=true`
- hash/provenance only
- public/reconstructible
- chat-only requiring retransmission/recovery.

Small chat-only text artifacts were copied into Git.

Large binaries are not falsely claimed as Git bytes.

Important binary records include:

- Dong Supplementary Data 8 and 10;
- FULL104 discovery subset;
- split 41K discovery-expression archive;
- calibration bundle;
- checkpoint archives;
- historical expression bundle;
- 41,238-address NPZ.

The two 41K expression parts were independently concatenated in this chat and reproduce:

`FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip`

SHA-256:

`63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

Do not assume a hash record means bytes exist in Git.

---

# 28. CI state and repaired external-fetch design

PR #199 was found mergeable but not CI-clean because the broad open-resource fetch workflow mixed deterministic PR validation with live external downloads. That was corrected during handoff preparation.

The repair has two parts:

1. Dong/Roussos Supplementary Data 8 and 10 are now explicit **manual/chat custody** resources with exact user-supplied hashes; they are no longer unattended CI fetch responsibilities.
2. `.github/workflows/v64-open-resource-fetch.yml` is now **workflow_dispatch only**. Live public downloads are custody operations, not deterministic PR-gating tests.

On repaired code head:

`4bd6f43b9cdb429a1cfcf8e1a35bca615ca3467f`

the following current-head workflows completed successfully:

- `V64 privileged-information architecture smoke` — run `36752876598` — **success**
- `V64 fetch FANTOM hg38 CAGE peak coordinates` — run `36752876636` — **success**
- `V64 import Claude paired handoff subset` — run `36752876843` — **success**
- `V64 import Claude exact supplement receipts` — run `36752876592` — **success**
- `V64 export Claude NIH-CARD paired subset` — run `36752876849` — **success**

The architecture smoke suite had previously exposed two stale tests after the custody manifest was redesigned. Those tests were corrected to assert the new automated-vs-manual custody semantics; the rerun is green.

The architecture suite is a focused architecture/custody guard, not a full production-regression or training qualification.

Do not call the manual open-resource fetch workflow a CI requirement. If run manually, its bytes must still pass the fail-closed validators before custody is accepted.

---

# 29. What the next ChatGPT agent should do first

Do not restart architecture reasoning from scratch.

### First 15 minutes

1. refresh all branch heads;
2. read this handoff;
3. read:
   - privileged-information recoverability contract;
   - universal RNA + privileged critic architecture;
   - common-support/sensitivity contract;
   - promoter universe contract;
   - chat-exclusive custody manifest;
   - independent supplement audit;
4. inspect whether Claude has advanced beyond `f2b45699`.

### If Claude has completed 64/64

Audit the complete qualification receipt before accepting sampler qualification.

Require:
- all 64 comparisons;
- non-empty count;
- zero inequalities;
- uniformity;
- frozen failure-path suite;
- no post-hoc gate change.

If qualified and Claude reruns Phase A:

audit Phase A, then preserve the hard stop.

### Parallel ChatGPT work

Continue promoter/recoverability work without opening protected outcomes:

1. finish the full GENCODE+SCREEN+Dong+FANTOM promoter candidate ledger;
2. audit candidate/evidence namespaces;
3. design the first bounded privileged factor using TRAIN only;
4. freeze factor construction before TEST;
5. freeze recoverability metrics/baselines/decision rule prospectively;
6. run TRAIN/VALIDATION development only;
7. do not open TEST until the decision protocol is frozen;
8. preserve REGULATORY-PRIVATE residual rather than forcing all privileged state into RNA.

---

# 30. Do not repeat these mistakes

Do not:

- treat E2 as universal target coverage;
- use edge count as gene count;
- use address count as gene count;
- zero-fill missing privileged evidence;
- call SCARlink and SCENT independent evidence;
- use Dong/FANTOM/SCREEN to define promoter candidate existence;
- parse FANTOM legacy hg19 ID strings as hg38 coordinates;
- join Dong evidence by ENST alone without chromosome awareness;
- use TEST to select factor rotation/rank;
- call high RNA prediction biologically qualified without shortcut baselines;
- call low RNA prediction biologically false;
- let CONTROL_B rescue CONTROL_A;
- reopen Phase B before the repaired Phase-A audit stop;
- claim a binary is in Git merely because its SHA is documented.

---

# 31. Immediate scientific destination

The current architecture hypothesis is:

- `Z_global`: broad RNA-supported biological state;
- `Z_query`: query-conditioned RNA-supported state;
- `Z_reg_shared`: regulatory state reproducibly recoverable from RNA;
- `Z_reg_private`: biologically supported regulatory state not recoverable from RNA;
- `Z_response`: perturbational/functional state where available.

This is still a hypothesis.

Do not automatically implement five neural heads.

The next architecture decision should be empirical:

> Which privileged regulatory factors are genuinely recoverable from lawful RNA, which are only partly recoverable, and which remain regulatory-private?

Only after that should auxiliary multimodal supervision be tested.

---

# 32. Governance at handoff

- TRAINING = OFF
- Phase B = STOPPED
- Stage 4 = NOT AUTHORIZED
- TD60 = BLOCKED
- Morabito = PROTECTED
- no protected biological correspondence opened by this handoff
- no final factorized target selected
- no multimodal teacher training authorized
