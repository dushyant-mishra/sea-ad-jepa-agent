# JEPA new-chat takeover commands — 2026-09-20

Repository:
`dushyant-mishra/sea-ad-jepa-agent`

## 1. Fetch live heads

```bash
git fetch origin --prune
git ls-remote origin \
  refs/heads/audit/v5-full104-information-channel-redteam-20260920 \
  refs/heads/handoff/jepa-v5-gpt-parallel-audit-20260920 \
  refs/heads/impl/v5-full104-pass1-review-repairs-20260920
```

Do not trust the SHAs in the handoff without re-fetching.

## 2. Preferred takeover branch

```bash
git switch --detach origin/handoff/jepa-v5-gpt-parallel-audit-20260920
git status --short
```

The handoff branch contains the latest red-team scripts/results that were merged at handoff construction plus supporting review/historical evidence.

If PR #33 is newer than the audit head recorded in the handoff, inspect its delta before changing anything:

```bash
git log --oneline --decorate --graph --all -40
git diff --stat origin/handoff/jepa-v5-gpt-parallel-audit-20260920..origin/audit/v5-full104-information-channel-redteam-20260920
```

## 3. Read order

```text
START_HERE.md
docs/agent/JEPA_LATEST_HANDOFF_POINTER.json
docs/agent/JEPA_NEW_CHAT_HANDOFF_20260920_V5_INFORMATION_CHANNEL_CURRENT.md
docs/agent/JEPA_NEW_CHAT_HANDOFF_STATE_20260920_V5_INFORMATION_CHANNEL_CURRENT.json
docs/agent/handoff_artifacts/20260920/V5_INFORMATION_CHANNEL_DATA_RESULTS_SCRIPTS_MANIFEST.json
analysis/v5_full104_information_channel_redteam_20260920/README.md
analysis/v5_full104_information_channel_redteam_20260920/CROSS_AUDIT_INTERACTIONS.md
analysis/v5_full104_information_channel_redteam_20260920/EVIDENCE_SHA256.csv
analysis/v5_full104_information_channel_redteam_20260920/EXTERNAL_ARTIFACTS.json
analysis/v5_full104_information_channel_redteam_20260920/supporting_gpt_parallel/GPT_PARALLEL_AUDIT_STATE_20260920.json
```

Then inspect PR #33 review comments.

## 4. Safe local tests

Run the audit-lane tests and no-skip gates available on the live head before modifying audit code.

Do not run terminal masking outcomes.

## 5. GPU/heavy assets

Large FULL104 data remain on the GPU machine. Use the paths/hashes in:
`analysis/v5_full104_information_channel_redteam_20260920/EXTERNAL_ARTIFACTS.json`

Do not replace them with historical 50K data or small caches for authority-bearing execution.

## 6. First scientific task

Before G4/G5:
- repair/clarify source-target non-estimability;
- production-align Audit B burden confirmation;
- production-align Audit E decomposition;
- settle attacker score estimand and fit weighting;
- make Audit F real-teacher design multivariate/scalable.

No terminal masking, no policy selection, no training.
