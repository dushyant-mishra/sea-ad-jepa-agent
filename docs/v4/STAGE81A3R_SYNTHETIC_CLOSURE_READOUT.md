# Stage81A3R Synthetic Closure Readout

**PROVISIONAL - SYNTHETIC ONLY - NOT FROZEN**

## Frozen Contract

- Universal molecular addresses: **41,238**.
- Semantic hash: `5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff` (unchanged).
- Measurement operators/rows: **42 / 1,731,996**.

## Final-Address Mechanics

- Microbatch 1: FULL 41,238-ADDRESS MECHANICALLY FEASIBLE; peak allocated/reserved 0.69/0.78 GiB; steps 2.
- Microbatch 8: FULL 41,238-ADDRESS MECHANICALLY FEASIBLE; peak allocated/reserved 5.42/5.71 GiB; steps 2.
- Microbatch 16: FULL 41,238-ADDRESS MECHANICALLY FEASIBLE; peak allocated/reserved 10.73/10.92 GiB; steps 2.

Classification: **FULL 41,238-ADDRESS MECHANICALLY FEASIBLE**.

## Contextual Capacity

- Width-256 gate fired: **False**.
- Replicated loss families: `[]`.
- Classification: **KEEP d_gene=160 PROVISIONAL**.

The capacity audit used the centered normalized Frobenius kernel over full contextual gene states. It did not mean-pool `H`, substitute the CELL token, or concatenate raw expression into `H`.

## Graph-Free Masking

- Pearson graph invoked: **False**.
- Classification: **PEARSON GRAPH NOT REQUIRED BY BOUNDED SYNTHETIC EVIDENCE**.

## Observation Operators

- Operator IDs supplied to encoder: **False**.
- Classification counts: `{'MEASUREMENT-AWARE TRANSFER SUPPORTED': 155, 'DATA / OPERATOR LIMITATION': 1}`.

## U_BIO / U_MEAS

- Classification: **SEPARATION NOT DEMONSTRATED**.
- U_BIO monotonicity violations: **0**; U_MEAS: **0**.

## Anti-Top-K Regression

- Full rare AUROC/AP: **1.000/1.000**.
- Top-4096 rare AUROC/AP: **0.593/0.078**.
- Broad full/top-K R2: **0.980/0.980**.
- Permanent deterministic regression: **ENABLED**.

## Governance

- Real RNA expression accessed: **NO**.
- DEV/SEALED RNA accessed: **NO/NO**.
- Pathology accessed: **NO**.
- Stage81B/Stage81C started: **NO/NO**.
- Stage81A3 Freeze1 declared: **NO**.

Final state: **STAGE81A3R_SYNTHETIC_CLOSURE_COMPLETE_NOT_FROZEN**

## Quantitative Results

### Full-H capacity at step 256

- **overlap_dense / graph_free**: raw mean R2 0.7786; learned-H mean R2 0.7590; mean H-minus-raw -0.0196; raw-recoverable factors 26/26.
- **partial_correlation / graph_free**: raw mean R2 0.8250; learned-H mean R2 0.8083; mean H-minus-raw -0.0167; raw-recoverable factors 26/26.
- **overlap_dense / oracle**: raw mean R2 0.7786; learned-H mean R2 0.7591; mean H-minus-raw -0.0195; raw-recoverable factors 26/26.
- **partial_correlation / oracle**: raw mean R2 0.8250; learned-H mean R2 0.8085; mean H-minus-raw -0.0165; raw-recoverable factors 26/26.

### Recurrent rare state at step 256

- **overlap_dense / oracle**: raw AUROC/AP 1.000/1.000; learned-H AUROC/AP 1.000/1.000.
- **overlap_dense / graph_free**: raw AUROC/AP 1.000/1.000; learned-H AUROC/AP 1.000/1.000.
- **partial_correlation / oracle**: raw AUROC/AP 1.000/1.000; learned-H AUROC/AP 1.000/1.000.
- **partial_correlation / graph_free**: raw AUROC/AP 1.000/1.000; learned-H AUROC/AP 1.000/1.000.

### Counterfactual observation operators

- **overlap_dense / O_A_high_support_high_depth**: raw-panel mean R2 0.8270; learned-H mean R2 0.8103; H-minus-panel -0.0167.
- **overlap_dense / O_B_medium_support**: raw-panel mean R2 0.7469; learned-H mean R2 0.7174; H-minus-panel -0.0295.
- **overlap_dense / O_C_limited_panel**: raw-panel mean R2 0.5905; learned-H mean R2 0.5504; H-minus-panel -0.0401.
- **partial_correlation / O_A_high_support_high_depth**: raw-panel mean R2 0.8657; learned-H mean R2 0.8531; H-minus-panel -0.0126.
- **partial_correlation / O_B_medium_support**: raw-panel mean R2 0.7972; learned-H mean R2 0.7705; H-minus-panel -0.0267.
- **partial_correlation / O_C_limited_panel**: raw-panel mean R2 0.6472; learned-H mean R2 0.6060; H-minus-panel -0.0412.

### Uncertainty convergence

- **overlap_dense / U_BIO** level:median-distance = `0.2:0.0105, 0.4:0.0073, 0.6:0.0055, 0.8:0.0030, 1:0.0000`.
- **overlap_dense / U_MEAS** level:median-distance = `0.25:0.1844, 0.5:0.1533, 0.75:0.1389, 1:0.1310`.
- **partial_correlation / U_BIO** level:median-distance = `0.2:0.0120, 0.4:0.0095, 0.6:0.0060, 0.8:0.0037, 1:0.0000`.
- **partial_correlation / U_MEAS** level:median-distance = `0.25:0.1851, 0.5:0.1542, 0.75:0.1408, 1:0.1329`.

The U_MEAS reference is an independently sampled complete-support observation after library normalization. Level 1.0 is a separate Poisson remeasurement at complete support and depth 12,000, not a self-comparison. Its nonzero value is therefore an independent-measurement/depth-noise floor; zero is not expected. U_BIO/U_MEAS separation remains **NOT DEMONSTRATED**, and neither score is calibrated.

### Clean-worktree portability ledger

- Audited failures: **28**.
- Classification counts: `{'MISSING_IGNORED_HISTORICAL_ARTIFACT': 17, 'OTHER': 2, 'STALE_HISTORICAL_UCDQ_MANIFEST': 9}`.
- Failures exercising new A3R code: **0**.
- A3R regressions: **0**.
- Conclusion: **HISTORICAL TEST-ARTIFACT PORTABILITY LIMITATION; NOT AN A3R SCIENTIFIC REGRESSION**.
- The row-level dependency and evidence are preserved in `stage81a3r_clean_worktree_portability_ledger.csv`.

## Final Validation

- Focused Stage81A3R: **13 passed**.
- Existing full v4 in the protected-artifact environment: **862 passed**.
- Repository suite: **874 passed**.
- Clean-worktree integrated v4: **845 passed / 28 failed** because historical tests require ignored local artifacts and one historical UCDQ manifest has a stale config hash.
- A3R-focused warnings/failures: **0/0**.
- Compileall and `git diff --check`: **PASS**.
- Frozen A2R semantic hash: **UNCHANGED**.
