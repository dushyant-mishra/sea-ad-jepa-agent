# Independent frozen reader-source cross-tab: physically executed V26 metadata audit

**Status: REAL FROZEN METADATA PASS; 18 SYNTHETIC/ADVERSARIAL TESTS PASS LOCALLY; NEVER PROTECTED BIOLOGICAL DATA.** Date 2026-09-25. Standalone audit stacked on PR #130 reader-fit metadata preflight, with **distinct scope**: independent 149-donor reader partition-by-study cross-tab against the separately frozen 215-row foundation/continuation/external split registry, including oracle study composition; PR130 authenticated the 104 reader_fit counts but did not independently cross-tab all 149 reader donors against the population access registry. No code changes to PR130, PR132/135/139 sampler, PR120 raw-count N1, PR133 old94 recovery, PR136/138 new104 baseline, or CRISPRbrain ETL.

## Physical source and exact source-code authentication

On the original user-supplied local August 24 bundle, the author **physically hashed the ENTIRE 410,278,055-byte ZIP**, expected and observed SHA256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`. Four independently frozen allowlisted CSV members were opened through that same verified archive descriptor, with all exact member SHA256 checked before parsing (no SQLite, expression, pathology or Level4 blocks):

- `splits/reader_donor_split.csv` — 149 donors; `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`.
- `splits/foundation_split_registry.csv` — 215 split records; `35afb7f53fa36d580a4552dd5ad7e59841e454ea85d4adcb761666cb20d05433`.
- `metadata/FOUNDATION_METADATA_ALL149_CONTEXT.csv` — eight archived aggregate partition/source rows; `ea4c28afeafac46e63545990c1d9884189647735f2049e947558eeb2de7bc1b0`. Its NON-fit cell counts are archived aggregates, **not** per-donor proof.
- `metadata/FOUNDATION_METADATA_DONOR.csv` — 104 fit-only per-donor count rows; `c9cbe47d4727aabec8a0c3fed5474c2dab4f9f2b8848357e08b0cec6ef044508`.

The actual physically executed producer is `verify_reader_split_source_crosstab_v1.py`, exact SHA256 **`f1cd7ba6999666736a8021f961b1e83a5c4c66d369374d9635e77e15b66ff7e4`**, exact Git blob `7837e9edeb918f77afff1812ca7cd4701b79a13d`. Its adversarial suite `test_reader_split_source_crosstab_v1.py` has exact SHA256 **`dba553e5bff857aebbb8df63dc147b9580dbfce479d874e617ea17062d34eebd`**, exact Git blob `a4abca15867dee76547c014e888d862da0b7dd59`. The **exact physical result** is committed at `results/V26_INDEPENDENT_READER_SOURCE_CROSSTAB_RECEIPT_R2.json`, SHA256 **`c40eab5aad962d51bc43a93b8a9a23fb761ff97e66609d28190f4439d312dd9f`**, Git blob `f1b394e368f13df0527bc4afff8707af88b0a775`. All THREE committed byte lengths and Git blob SHAs were independently compared with the exact LOCAL physically executed files; GitHub bytes matched. The original on-device 18-test self audit PASS was observed after fixing a stale expected error-message assertion in the added adversarial fixture. No failed test was silently dropped.

## Frozen metadata join and measured results

For each reader donor, join frozen `reader.donor_id` to **the INDEPENDENT canonical foundation/train registry** at `canonical_person_id = study_id + "::" + donor_id`, not to a guessed per-source substring or the old Stage81A2 CSV. All 149 reader donors matched EXACTLY all 149 foundation/train donor IDs, no reader↔continuation overlap. All 17 continuation train donors are separate; 19 foundation+5 continuation in each development and sealed holdout; one separately reserved Siletti whole-study external holdout. Pathology-influenced split flags forbidden across all 215 rows.

| Reader partition | HVS | NPH52 | SEA_AD | Total |
|---|---:|---:|---:|---:|
| reader_fit | 41 | 17 | 46 | 104 |
| reader_validation | 10 | **0** | 12 | 22 |
| reader_oracle | 11 | **2** | 10 | 23 |

Actual fit-only per-donor metadata independently sums **HVS 198,718 + NPH52 236,476 + SEA_AD 4,118,213 = 4,553,407** fit cells. The reader_validation/oracle cell totals in the receipt are independently compared against the existing archived context table for donor-count consistency only; no per-donor reserved expression outcomes or individual reserved cell rows were inspected. Do not misrepresent the 2 NPH52 oracle donors as a new NPH52 validation cohort, or access them to tune the next architecture.

The reader_validation **12 SEA_AD/10 HVS/0 NPH52** split is now physically VERIFIED, not merely a user/Opus-reported cross-tab; main registry's previously verified *overall counts* are consistent but do not independently contain that source cross-tab.

## Reproduce exact original physically executed result, not a synthetic substitute

Use the **identical SHA-bound Aug24 archive**, not a guessed new version or subset. Execute in a clean worktree at this PR's exact commit; use a NEW output path inside an existing runtime parent. The script refuses to overwrite any prior receipt:

```powershell
python -m unittest discover -s analysis/v26_reader_source_crosstab_20260925 -p "test_reader_split_source_crosstab_v1.py" -v

python analysis/v26_reader_source_crosstab_20260925/verify_reader_split_source_crosstab_v1.py `
  --calibration-zip "D:/<AUTHENTIC_PATH>/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip" `
  --out "D:/<FRESH_VERSIONED_PARENT>/V26_INDEPENDENT_READER_SOURCE_CROSSTAB_RECEIPT.json"
```

The exact deterministic result must hash to `c40eab5aad962d51bc43a93b8a9a23fb761ff97e66609d28190f4439d312dd9f` under the exact source bundle. Full archive hashing is ~410MB I/O; it does NOT run FULL104 raw count, train a model or open reserved expression.

**Scope:** metadata-only scientific planning; no 104-donor raw-cell identity attestation, no pass1 histogram or 8,915-block raw scan, no N1 burden outcome, no JEPA optimizer step, no D_shared, no pathology, no Siletti outcome, no validation/oracle expression. Even PASS does NOT authorize actual training or release held-out evaluation. Local 18 adversarial tests are synthetic; GitHub Actions similarly exercises only fixture tests and rechecks exact GitHub committed producer/test/receipt hashes. Its CI cannot independently replay the 410MB ZIP because that archive is intentionally not uploaded to GitHub.

## No-overlap and evidence retention

The separate physically executed 8KB source+test+receipt ZIP has SHA256 `7f02cf9b610795c822f1fcad37e4c0566d61df42b998bc0aaf1ffa4c6e3c27b0` and was also retained in user Library folder `JEPA_V26_parallel_staging`. But all three essential original payloads are **committed in plain UTF-8 to this PR**, not dependent on scratchpad recovery. No large raw data or protected arrays committed. Reader-fit count preflight PR130 and physical pass1 PR132 remain their own tasks; no further source cross-tab recomputation is required.
