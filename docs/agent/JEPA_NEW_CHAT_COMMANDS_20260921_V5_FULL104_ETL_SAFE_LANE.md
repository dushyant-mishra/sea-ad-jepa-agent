# JEPA V5 FULL104 — exact new-chat startup commands — 2026-09-21

These commands are a startup aid, not authority. Re-fetch live heads and compare them before changing code.

## 1. Fetch and record live heads

```bash
git fetch origin --prune

git ls-remote origin   refs/heads/audit/v5-full104-information-channel-redteam-20260920   refs/heads/gpt/v5-full104-safe-lane-20260921   refs/heads/claude/v5-full104-blocker-clearance-20260921   refs/heads/handoff/jepa-v5-full104-etl-safe-lane-20260921
```

At handoff freeze time:

```text
PR33/base:
ae5dc5c624fff341b8ef30c5359c55528383920a

PR35/GPT safe-lane + ETL:
0c2f5fb8419ea7d1572479e6ef1b13768e52f3c5

Claude GPU lane:
cdac29eba5f08994bc3d8309a31c05cd21da50aa
```

If live SHAs differ, use the live SHAs and inspect the intervening commits.

## 2. Read the takeover package before integration

```bash
git show origin/handoff/jepa-v5-full104-etl-safe-lane-20260921:START_HERE.md
git show origin/handoff/jepa-v5-full104-etl-safe-lane-20260921:docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
git show origin/handoff/jepa-v5-full104-etl-safe-lane-20260921:docs/agent/JEPA_NEW_CHAT_HANDOFF_20260921_V5_FULL104_ETL_SAFE_LANE_CURRENT.md
git show origin/handoff/jepa-v5-full104-etl-safe-lane-20260921:docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260921_V5_FULL104_ETL_SAFE_LANE_CURRENT.json
```

Then read the ETL package:

```bash
git show origin/gpt/v5-full104-safe-lane-20260921:analysis/v5_full104_dataset_etl_20260921/README.md
git show origin/gpt/v5-full104-safe-lane-20260921:analysis/v5_full104_dataset_etl_20260921/FULL104_DATASET_ETL_ATLAS_REPORT_20260921.md
git show origin/gpt/v5-full104-safe-lane-20260921:analysis/v5_full104_dataset_etl_20260921/evidence/FULL104_DATASET_ETL_ATLAS_SUMMARY_V3.json
```

## 3. Inspect branch divergence; do not merge wholesale

```bash
git log --oneline --decorate --no-merges   origin/audit/v5-full104-information-channel-redteam-20260920..origin/gpt/v5-full104-safe-lane-20260921

git log --oneline --decorate --no-merges   origin/audit/v5-full104-information-channel-redteam-20260920..origin/claude/v5-full104-blocker-clearance-20260921

git diff --stat   origin/gpt/v5-full104-safe-lane-20260921...origin/claude/v5-full104-blocker-clearance-20260921
```

At freeze time the lanes are diverged. Do not use a blind merge.

## 4. Recommended integration branch

After confirming PR #35 is still the intended green integration base:

```bash
git switch --create integrate/v5-full104-gpt-claude-20260921   origin/gpt/v5-full104-safe-lane-20260921
```

Do not push changes directly to Claude's branch and do not rewrite PR #33.

## 5. Review Claude commits in order

```bash
git show --stat a153ab655b84c26ac9646ccccef88468da9c7dba
git show --stat 1fe022de5f33c4644d74016e48dee5f0f2c25b6b
git show --stat 065bc12e67a1b3cf983773feb7a528b41dbb7403
git show --stat b6cac05aa05068ad576ac9bcac48e4ac9d97b943
git show --stat cdac29eba5f08994bc3d8309a31c05cd21da50aa
```

Claude V1 non-estimability commit `065bc12...` is superseded by Claude V2 `b6cac05...`. Do not integrate V1 as authority.

## 6. First integration targets

Port deliberately, not with an unreviewed range cherry-pick:

1. Phase-I parser-equivalence / heavy-statistics evidence and qualification.
2. Phase-II C2 fold-aware evidence and row-level cross-check.
3. Reconcile the two estimability-contract implementations.
4. Phase-IV Audit-B sample freeze.

The two estimability implementations to diff are:

```text
PR35:
src/sea_ad_jepa/v5/evidence_estimability_contract_v1.py

Claude:
analysis/v5_full104_information_channel_redteam_20260920/scripts/score_term_evidence_contract_v2.py
```

Minimum integrated invariants:

```text
finite numeric value <=> ESTIMABLE
undefined != numeric zero
TARGET_NON_VARIABLE distinct
PREDICTION_NON_VARIABLE distinct
TARGET_AND_PREDICTION_NON_VARIABLE distinct
MISSING distinct
INVALID_NUMERIC distinct
gross |r| > 1 rejected
state survives serialization/resampling
no silent aggregation default
conditional statistic != full intended estimand
```

Run both lanes' adversarial tests after reconciliation.

## 7. ETL reproduction only if inputs changed

Authenticated input:

```text
FOUNDATION_CALIBRATION_BUNDLE_20260824.zip
bytes 410278055
sha256 07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444

metadata/foundation_metadata_rows.sqlite
bytes 2709786624
sha256 a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913
```

Reproduction:

```bash
python analysis/v5_full104_dataset_etl_20260921/scripts/extract_full104_dataset_sql_aggregates_v1_20260921.py   --bundle-root /path/to/foundation_calibration_bundle_20260824   --out-dir /tmp/full104_etl_sql   --query-id ALL

python analysis/v5_full104_dataset_etl_20260921/scripts/build_full104_dataset_etl_atlas_v3_20260921.py   --bundle-root /path/to/foundation_calibration_bundle_20260824   --sql-cache-dir /tmp/full104_etl_sql   --out-dir /tmp/full104_etl_atlas
```

Do not rerun just to establish confidence: a fresh replay has already shown byte identity for all 11 SQL-cache files and all 13 machine atlas outputs.

## 8. GPU/full-data immediate next execution after integration

Audit B uses the already frozen target-sample specification from Claude Phase IV:

```text
freeze digest:
c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac

sample ladder:
N1 256
N2 1024
N3 4096

escalate only if relative SE > 0.05
```

No burden has been computed yet.

Do not extend/re-roll the sample based on burden magnitude, sign, policy ranking, or terminal result.

## 9. Permanent STOP boundaries

```text
NO TERMINAL MASKING OUTCOME OPENING
NO D_SHARED
NO PATHOLOGY-ADAPTIVE MODEL/POLICY CHOICE
NO DEV/SEALED EXPRESSION
NO MASKING POLICY SELECTION
NO G5 MARGIN SELECTION
NO TRAINING
```

until their upstream prospective authorities are actually closed.

## 10. Verification discipline

After each integrated blocker:

```text
implementation
-> unit tests
-> positive control
-> adversarial negative control
-> real safe-lane data
-> independent recomputation
-> red-team interpretation
-> scope classification
-> compact evidence + report
-> CI/no-skip verification
```

Do not treat a green workflow as a substitute for scientific closure.
