# Controlled post-repair synthetic rerun: same Stage81A3 biology, JEPA_ONLY, strict C2 gradients (2026-11-04)

**Do not confuse this new test code with a completed GPU result.** This version remains an additive **synthetic-only GPU execution candidate**, without changes to historical sources, any human cohort, Stage4, or a selected JEPA representation.

## What was actually repaired, and where prior experiments stopped

1. **Old original Stage81A3 V4A 24-slot Perceiver:** 10×500 planted-factor optimizer/EMA trajectories failed biological-factor recovery despite >99% falling JEPA loss. Faster EMA 0.996 vs .99925 did not rescue. An improved attention-logit/PCA 10×500 version still failed S2–S7. These are **unchanged negatives for the old model**, not a verdict on all successors. See original `docs/v4/STAGE81A3_CALIBRATION_AND_SYNTHETIC_MECHANICS_READOUT.md`.
2. **Original six-IPB v4.1 `stage81a3_ipb_jepa_feasibility.py`:** actually trained **THREE** 500-update trajectories, not the eight planned. Original `stage81a3_rlc_causal_fast_probe.py` explicitly reports `completed_runs=3`, `final_classification_valid=False`. The tokenizer/gene-level target retained information but its learned CELL state and masked inference moved away from retention gates. Original partial report SHA-256 `aa949f23e1e9c6de2daed2bf858b8f822b6cb0dc393e2d7bf62f14267c449308` independently verified in 2026-09-02 custody audit. **Do not re-execute or complete that historic combined anchor run**.
3. **Subsequent corrected Stage81B causal runs:** original matched `JEPA_ONLY/CURRENT/ANCHOR_ONLY` u100/u300/u500 comparisons found `JEPA_ONLY` more stable, combined less stable and anchor-only strongly degraded, with shared gene-identity movement ~7.618× higher for anchor. **DEC-001 rejects hidden-gene/CELL anchor**; archived `docs/agent/archive/governance/ACTIVE_STATE_20260903_HISTORICAL.md`. Exact historical source/fixture matching is not established, so this does **not** qualify a new JEPA student or replace an exact same-world comparison.
4. **Later C2 mandatory-gradient repair:** failure was 48 protected query/key/value/attention-norm tensors with zero Adam moments in historical **FP16 backward-inside-autocast 128/8 T1**. Independently qualified K1 disabled backward autocast, plus unscaled gradient and Adam-moment gates; see `scripts/v4/f1b_c3_training_successor_v2.py` and preserved C2 package root. This corrects **that exact historical execution condition**. It is **not** evidence that the separate Stage81A3 IPB failure was caused by zero gradients; the original IPB source already calls `.backward()` outside the autocast context.
5. **Later Stage81A3R molecular/measurement architecture:** full-G 37,346/41,238 address probes and donor/refit basis work were actually tested; accepted 224-D candidate concerns the **global projection dimensionality**, not a new 500-step trained EMA JEPA student passing planted biology. The real TRAIN global-state audit does not qualify masked student recovery or a target.

## Exact, non-retuned execution contract

New source: `scripts/v4/stage81a3_ipb_jepa_only_postrepair_rerun_20261104.py`, derived from **unchanged** `scripts/v4/stage81a3_ipb_jepa_feasibility.py` git blob `49206efd40b8f7a69891d788f657fc5d44d9f687`. This source **does not implement a new synthetic generator or new neural architecture**.

It binds the original:

- **Biology:** two original `balanced_multifactor`, `dominant_axis_multifactor` 8,192-cell, 4,096-gene, 32-factor planted worlds. Exactly two original training seeds `8114001`, `8114002`, independent 7,168-cell fit pool plus frozen 256-cell readout-train and 256-cell evaluation roles from historical fixture.
- **Learning geometry:** six-block width160 `IPBEncoder`, `BlockPredictor`, full-evidence EMA teacher gene-block target (no direct factor oracle), 40% target masking, 16 graph-formed blocks, EMA .996; AdamW LR 1e-4/weight decay .01, physical microbatch8/effective256 accumulation32, FP16 CUDA forward with backward outside autocast. **500 updates each** (2 fixtures × 2 seeds = four new runs). No planned step budget/EMA/masking changes.
- **Single causal change:** `JEPA_ONLY` removes the formerly combined hidden-gene/CELL anchor from the decoder optimizer, gradient and forward. It does not infer that a different synthetic population or target wins.
- **Additional execution protection:** exact C2 mandatory unscaled 48-backbone-tensor and predictor-gradient gate before step, independent finite and nonzero Adam first/second moment checks after step, and EMA updates only after a successful optimizer step. The independent CPU source tests fail on anchor reintroduction, missing protection, pre-existing result edits, uncompleted steps, and noncompensating scientific failures.
- **Endpoint:** original experiment's teacher CELL planted-factor R², partial-mask student CELL factor R², visible-RNA reference, raw-PCA160 reference, gene-token retention, target CELL retention and student-minus-visible-RNA increment. The old **per-run >= .90 token / >= .80 CELL / >= .80 partial-to-full / >= 0 student gain** and **per-fixture medians >= .95 token / >= .90 CELL** criteria remain unchanged. Report negative results explicitly even if JEPA loss decreases. No historical numeric gate threshold is tuned.
- **Unqualified subclaims:** no donor generalization (this exact historical two-world fixture does not include donor heldouts), no multiquery C3 conditional gain, no authentic real assay support, no human biology/AD/causality, no Stage4. The decoder is untrained, and hidden-gene-value reconstruction is `NOT_ESTIMABLE`, not a failure to be disguised.

No large real data. This is a **matched controlled diagnosis of whether removing the historically rejected anchor rescues the old IPB CELL bottleneck**, not an answer to the distinct C2/C3 learned-target question or production target selection. History's own JEPA_ONLY runs were not proven to have this original same-seed/same-world configuration, which motivates this narrow comparison.

## GPU laptop execution (Macha)

Use a clean Linux/WSL checkout/worktree of the exact PR head; **never run from the historical Stage81A3 output directory if it contains untracked experimental edits**. Verify the original source blob and executable branch commit before use:

```bash
git fetch origin pull/537/head
git worktree add --detach ../jepa-ipb-jepa-only-postrepair FETCH_HEAD
cd ../jepa-ipb-jepa-only-postrepair
git rev-parse HEAD
git rev-parse HEAD:scripts/v4/stage81a3_ipb_jepa_feasibility.py
python -m unittest discover -s tests/v4 -p 'test_stage81a3_ipb_jepa_only_postrepair_rerun_20261104.py' -v
python scripts/v4/stage81a3_ipb_jepa_only_postrepair_rerun_20261104.py --project-dir .
```

The fixed original blob must equal `49206efd40b8f7a69891d788f657fc5d44d9f687`. Do **not** use the original script's `--overwrite` mode; the new script refuses overwriting. Exact original file `results/v4/stage81a3_ipb_jepa_feasibility.json` remains unmodified. Execution emits new `results/synthetic/stage81a3_ipb_jepa_only_postrepair_20261104/RECEIPT.json` (full local run) and `RUNS.csv` (compact reported metrics). The historical 3-trajectory receipt may be read and hash-checked to compare matching fixture/seed, without rerunning it.

**Crash-safe trajectory continuation:** the script writes the fixed-version receipt after each fully completed 500-update arm. If an interruption leaves one, two or three completed arms, repeat the *same exact committed Git HEAD* with `--resume`: it checks the original parent source blob, committed source/worktree identity, frozen config hash, exact fixture+seed roster, complete protected update counters and no old mechanical failures, skips completed arms, and trains only the remaining arms. `--resume` refuses changed science, completed terminal results, missing receipts or forged partial arms. The original history cannot be overwritten. There is no exact mid-trajectory resume; that interrupted arm alone must start again. **No unrelated source change after the first GPU arm is permitted.**

**Return for independent review:** exact Git HEAD, original source git blob, source+env versions, SHA-256 of full local receipt, four rows of `RUNS.csv`, actual 500 optimizer/EMA update counts, status/exception and all halted attempts. Do not claim success if any protected gradient fails, CUDA OOMs, source differs, output is partial, a missing metric becomes PASS, or any original report changed. Macha can keep full trajectory weights/results on the GPU laptop and return the compact proof via GitHub. If independent review finds a different issue, preserve failure and create a *new* clearly versioned successor rather than editing outcomes.

**CPU GitHub CI is syntax/scientific-law/identity preflight only. It cannot establish a GPU training result.** No background GPU job has been triggered from this chat. This is user-authorized **synthetic execution only**; the standing human-data authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
