# JEPA V65 takeover commands — 2026-09-30

## 1. Refresh repository state

```bash
git fetch --all --prune

git show-ref --heads | grep -E 'chatgpt/v64-privileged-information-recoverability-20260930|claude/v64-exact-sampler-successor-20260930|handoff/jepa-v64-target-architecture-20260930|chatgpt/v64-e2-single-source-successor-20260929'
```

## 2. Primary takeover branch

```bash
git switch chatgpt/v64-privileged-information-recoverability-20260930
git pull --ff-only
```

Read in this order:

```bash
cat docs/agent/JEPA_NEW_CHAT_HANDOFF_20260930_V65_PRIVILEGED_RECOVERABILITY_SUCCESSOR.md
cat docs/agent/JEPA_HANDOFF_STATE_20260930_V65.json
cat docs/agent/V64_CLAUDE_NEXT_INSTRUCTIONS_20260930.md
cat docs/agent/archive/chat_runtime_20260930_v2/README.md
cat docs/agent/archive/chat_runtime_20260930_v2/CHAT_RUNTIME_EXCLUSIVE_ASSET_CUSTODY_20260930_V2.json
```

Then read the architecture/methodology contracts referenced by the handoff.

## 3. Refresh Claude lane before accepting execution status

```bash
git log -1 --oneline origin/claude/v64-exact-sampler-successor-20260930
git diff --stat f2b45699d1be88cc599971da243ba6e36a50c4a7..origin/claude/v64-exact-sampler-successor-20260930
```

If Claude advanced beyond `f2b45699`, audit every new sampler/qualification/Phase-A result before upgrading status.

## 4. Verify PR #199 CI status

PR #199 is the architecture/custody branch PR.

Do not assume mergeable == CI-clean.

Inspect all workflows on the current PR head.

The resource-fetch CI defect was repaired before handoff finalization.

Current design:
- deterministic architecture/custody tests remain PR CI;
- FANTOM/Claude import-export workflows remain verifiable custody workflows;
- the broad live open-resource downloader is `workflow_dispatch` only and is NOT a PR-gating check;
- Dong Supplementary Data 8/10 are manual/chat custody with exact hashes.

Verified repaired-code-head passes:
- architecture smoke run 36752876598: PASS
- FANTOM hg38 fetch run 36752876636: PASS
- Claude paired import run 36752876843: PASS
- Claude exact supplement import run 36752876592: PASS
- Claude paired export run 36752876849: PASS

Still refresh the current PR head and checks before merging, but do not require the manual external-download workflow as CI.

## 5. Exact-control hard gate

Do not rerun Phase A unless the full sampler qualification passes.

Require:
- 64/64 real edge-side oracle comparisons;
- non-empty count;
- zero inequalities;
- uniformity;
- frozen fixture/failure-path suite.

Then, and only then:
- rerun Phase A;
- STOP for audit.

No Phase B.

## 6. Parallel architecture lane

Safe next work:
- finish full GENCODE+SCREEN+Dong+FANTOM promoter ledger;
- freeze first real privileged-factor construction on TRAIN only;
- freeze recoverability baselines/decision rule on TRAIN+VALIDATION only;
- keep paired NIH-CARD TEST unopened until protocol is frozen;
- preserve private residual;
- never use NOT_MEASURED as zero.

## 7. Governance

- TRAINING = OFF
- Phase B = STOPPED
- Stage 4 = NOT AUTHORIZED
- TD60 = BLOCKED
- Morabito = PROTECTED
