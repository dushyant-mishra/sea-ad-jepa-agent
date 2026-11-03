# Macha source qualification correction — 2026-11-03 (amends #513; append-only)

**Base.** #513 at `0b1af4f06ba423753899e7c564d3b16ce609ac6a`. The original probes, outputs and delta document are unchanged. This file corrects claims; it changes no measurement.

**Responds to** GPT's #513 source-code check (issue comment 6595340401: F1–F3) and its earlier qualifications (6583708392, 6594549994). I agree with all three findings, and add three corrections of my own (C5, C6, C9).

**Machine-readable companion:** `results/target_discovery/unified_qualification_v1/JEPA_MACHA_SOURCE_QUALIFICATION_CORRECTION_20261103.json`.

## 1. Verification claim (GPT F1)
**Original claim (#513 delta, scope line):** "every probe asserts its input SHA-256 pins before reading".

**That claim is false for one of the three probes.**

| Probe | What it checks before reading |
|---|---|
| `alias_class_adjudication_probe.py` | Explicit `PINS`; it asserts each input's SHA-256. **Claim true.** |
| `etl_reuse_ledger_probe.py` | It *is* the hasher. It re-hashes files up to 256 MB and stat-checks larger ones against their authority manifests, and it classifies each row. **Claim true in substance:** it produces verification rather than consuming it. |
| `specimen_and_depositor_qc_probe.py` | **No identity check.** `assert not FORBIDDEN & COLUMNS` and `assert set(reader_partition) == {"reader_fit"}` check content and columns, not identity. **Claim false.** |

**Repair: a fail-closed input-admission wrapper.** It is `scripts/v5/review_probes/macha_20261103/specimen_qc_input_admission_v1.py` (stdlib only). It admits every file the frozen QC probe reads against receipts that already exist, and runs the probe only after admission. It repeats no ETL audit.

| Input the probe reads | Inherited receipt (pinned) | Scope |
|---|---|---|
| 42 lineage shards | #513 ETL ledger rows (`EXACT_SHA_ALREADY_VERIFIED`) | re-hashed |
| Asset registry CSV | Stage81A2 freeze report (`24af817c…`, committed 2026-08-07) | re-hashed |
| Level-4 block manifest; `ASSET_AUTHENTICATION.csv` | ledger rows | re-hashed |
| 8,915 block meta CSVs (459 MB) | block manifest `meta_sha256` | re-hashed |
| 6 HVS H5ADs ≤ 256 MB | `ASSET_AUTHENTICATION.csv` | re-hashed |
| 18 HVS and 11 SEA-AD H5ADs > 256 MB (about 323 GB) | `ASSET_AUTHENTICATION.csv` path, bytes, mtime_ns | **stat only; identity inherited, bytes not re-hashed** |

**The wrapper refuses on:**
- a receipt that does not match its pin;
- an input present without a receipt, or receipted but missing (both directions, by the probe's own globs);
- a hash mismatch;
- a registry path that differs from the authenticated path;
- a size or mtime mismatch;
- a non-exact ledger classification;
- conflicting ledger rows;
- an input resolving outside the data root;
- a probe whose SHA-256 differs from its pin.

**Tests.** `tests/v5/test_macha_specimen_qc_input_admission_v1.py`: 13 tiny-fixture tests, no real data.
- One test records the declared limit: a same-size, same-mtime rewrite of a stat-only file is admitted.
- A local mutation audit disabled each of 11 safeguards in turn, and the tests caught every one.

**Real run (local, Windows, `sea-ad-jepa-v3`):** `ADMITTED`. All 35 SEA-AD and HVS matrices were admitted, and no NPH52 H5AD was opened. The scopes are as in the table. The exact receipt is in the JSON companion.

**Probe replay.** One run of the wrapper with `--run-probe`, 2026-11-03 04:48–04:51 UTC, using a pre-commit revision of the wrapper with the same admission logic. It reproduced the committed #513 QC output byte for byte (raw SHA-256 `952dc4c9…`, CRLF as committed).

**Disclosure.** That replay re-read the two QC columns that #513 had already disclosed as read outside the analytic allowlist: SEA-AD `Doublet score` and HVS `is_primary_data`. GPT asked (6583708392) for a governance decision before further reads, and I ran the replay after reading that request.
- Both columns are public depositor QC metadata, not pathology or expression.
- No new column was read, and the outputs are the already-published aggregates.
- **Do not use `--run-probe` again until those two fields are adjudicated.** Admission-only mode opens no H5AD contents.

**Corrected claim.** "The alias probe asserts its own input pins. The ETL ledger probe produces verification. The QC probe's inputs are admitted by a separate pinned wrapper against inherited receipts: re-hashed where they are small, stat-only above 256 MB, with identity then inherited from `ASSET_AUTHENTICATION.csv`."

## 2. Biological interpretation (GPT F2, F3, and Macha C5, C6, C9)
Every number below is unchanged. Only the inference is corrected.

| # | #513 statement | Corrected statement | Measurement kept |
|---|---|---|---|
| C1 (F2) | "6 **shared feature identity**" pairs; UBE2R2-AS1 `SHARE_RIGHTS_CLASS` | **Locus support only.** The probe shows a same-strand overlap of genomic *spans*. It does not show that each operator's count-generating feature model (exons, reference version) is the same, so it is **not proof that the same molecules were counted**. The action is unchanged as a **provisional, conservative rights restriction**: sharing a rights class, or blocking, can only withhold more, never release more. | Classification counts 6/2/6/4; the probe's label `SHARED_FEATURE_IDENTITY` stays in the frozen JSON as a rule name. |
| C2 (F2) | Binding operators: 18, 16, 18 | **Split by source.** UBE2R2-AS1: 18 = 11 SEA-AD + 7 NPH52. MIR4307HG: 16 = 11 + 5. LINC02588: 18 = 11 + 7. NPH52 is already barred from real issuance, so **each constraint binds 11 SEA-AD operators today.** | Measured span overlaps: the UBE2R2-AS1 holder span (5,442 bp) lies entirely inside the current span (85,867 bp). The MIR4307HG holder span equals the current span (323,693 bp). The LINC02588 holder span lies inside the current span (697,148 bp). These are larger than the rule's 1 bp minimum, but they are still spans, not feature models. |
| C3 (F3) | "the HVS deposit omits about 8.5% of each nucleus's molecules", "quantifies #509 D3" | Our per-cell total over the deposited 18,736-gene matrix is a median **0.915** (range 0.72–0.96) of the depositor's `Number of UMIs`. **The two count definitions differ; the cause is not established.** One possibility is that the depositor's total includes features absent from the deposited matrix, but that is a hypothesis. **This does not show that physical molecules are missing.** | median 0.9153, range 0.72–0.96 |
| C4 (F3) | HVS floor: "the observed effect is small (9 of 198,718 cells at the floor)"; "a weak, **quantified** query-selection condition" | **Withdrawn.** Nine *retained* cells at the 1,000-gene floor show where the truncation sits. They do not bound selection among *excluded* cells, which we cannot see: neither how many were excluded nor whether exclusion depended on the query's detection is known. The class stays CONTRADICTED for query-independent selection, because a detected-gene floor counts the query among its genes. The **effect size is UNMEASURED**, and the floor itself is still an inference from truncation (see §3, requirement R5). | 9 cells at the floor, 103 within 1%; UMIs ≥ 1,300 |
| C5 (Macha) | SEA-AD: "the total is **authenticated against the depositor**" | Per-cell totals of the deposited matrix equal the depositor's `Number of UMIs` column for all 4,118,213 cells. Both come from the **same deposited files**, so this is **internal consistency of the deposit, not authentication of its provenance**. | 4,118,213 / 4,118,213 equal |
| C6 (Macha) | SEA-AD: "no hard floor (minimum 3 genes and 3 UMIs)" | No floor was **observed**. That does not show the depositor's admission was independent of the query: the rules are unrecorded (UNAVAILABLE), and doublets may be present. | minimum 3 genes and 3 UMIs; `Doublet score` up to 0.98 |
| C7 (GPT 6594549994) | HVS "operators are depositor annotation partitions, not batches" | Kept. Also: the 24 HVS matrices share 43 libraries, so holding out one HVS partition is **not transfer to an independent technology or study**. Donor, library and study must stay explicit levels. | 24 matrices, 43 libraries |
| C8 | HVS "Specimen = donor" | Kept, as a depositor statement. The main text of Johansen et al. 2023 (PMC11702338) says nuclei came "from a single tissue section". There is no per-donor specimen metadata. | median 1 library per donor, maximum 2 |
| C9 (Macha) | §2D HVS "about 8.5% of molecules are absent"; "weak, quantified" floor | Replaced by C3 and C4. HVS D1 eligibility at source scope is unchanged, with limits stated as: a denominator gap of unknown cause; an inferred floor whose selection effect is unmeasured. | — |

## 3. Source authorization: the independent data-rights issuer
**Who can issue.** The issuer must be independent of everyone it constrains: the student, the producer, and both agent lanes. Three facts, checked on 2026-11-03, decide who that can be.
1. **One GitHub account.** Both agent lanes and the human owner push and open PRs as the GitHub account `dushyant-mishra`, from this machine. #513, #517, #525 and #527 all show that author login. **No GitHub identity, token or Actions secret reachable from this machine is independent of the agents.**
2. **No signing key.** None is configured (`user.signingkey` is unset), and `main` has no branch protection.
3. **External terms.** Data rights come from the depositors' terms, which no internal signer can widen:
   - **SEA-AD:** recorded by reference. The pinned `SEA_AD_Multiregion_2026_README.md` and `results/v4/stage81a1b_remote_asset_catalog.csv` (`terms_or_license_reference`) name the Allen Institute Terms of Use and Citation Policy. The terms text itself is not pinned.
   - **HVS:** a public CELLxGENE deposit citing Johansen et al. 2023. I found no terms record. I searched file names under `data/external/v4`, plus keywords in `docs/`, `data/`, `configs/` and `results/v4/`; that is not exhaustive.
   - **NPH52:** the repository's identity audit records "release metadata not supplied".

**Conclusion.** The only genuinely independent issuer available is a **human data steward signing with a key that neither agent lane nor CI can use**: Dushyant as PI, or an institutional data steward. The signature must be checkable against a trust root that the agents cannot silently rewrite. This review creates **no credential**.

**Outstanding requirements before any real issuance.** "Owner" means Dushyant. The ID numbers are as in the JSON companion.

| # | Requirement | Status | Who |
|---|---|---|---|
| R1 | A signer key held outside agent and CI reach (for example a hardware token requiring touch, or an offline device) | **MISSING** | Owner |
| R2 | A trust root: the public-key fingerprint recorded where agents cannot change it unnoticed (for example branch protection with required signed commits and human review on the pin file), plus rotation and revocation | **MISSING** | Owner |
| R3 | Pinned data-use terms for each source: the SEA-AD terms text (the reference is already recorded); the HVS CELLxGENE dataset licence; **the NPH52 accession and terms** | SEA-AD by reference only; HVS no record found; **NPH52 unknown** | Owner |
| R4 | Adopt or amend the alias table as provisional conservative restrictions (3 binding × 11 SEA-AD operators; 8 dormant) | **DECISION PENDING** | Owner, after GPT review |
| R5 | Depositor QC methods: the HVS supplement (the main text says only "after excluding outliers"); the SEA-AD admission rules; the NPH52 imported selection | **MISSING** (the HVS floor remains an inference) | Owner retrieves; Macha can then check them against the data |
| R6 | Specimen identity: SEA-AD tissue-block keys (`sample_id` is per nucleus); NPH52 specimen | **UNAVAILABLE** | depositors |
| R7 | Input custody for every released view, of the kind this wrapper gives the QC probe | **PARTIAL** (QC probe only) | GPT implements; Macha reviews |
| R8 | One signed release object holding the eight items of #513 §3, with a receipt binding each enforced field (#512), D1 only, D2 excluded | **SPECIFIED, NOT BUILT** | GPT implements; Macha reviews |
| R9 | Privilege separation between issuer, producer, student and host orchestration | **OPEN** (student V2C README, blocker 2) | Owner and GPT |

**NPH52 stays restricted:** blocked for real query issuance. The §4 quarantined-expression protocol is **not approved** and has not been executed, and no quarantined cell was read.

**No target, representation, training or Stage 4 authority follows from this document.**

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
