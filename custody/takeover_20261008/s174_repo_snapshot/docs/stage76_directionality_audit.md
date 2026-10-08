# Stage76 F9 - directionality audit

F9 audits signed TF-target hypotheses from the frozen Stage75/F8 evidence tables.
It preserves the coactivity sign as `predicted_response_sign_from_coactivity`
only. Positive coactivity is not called activation, and negative coactivity is
not called repression.

Existing Stage72B thresholds are reused:

- absolute Spearman threshold: `0.20`
- bootstrap sign-stability threshold: `0.70`

No existing TF-level rare-high/background or disease-state association table was
identified that can justify assigning a desired TF perturbation direction. As a
result, `desired_tf_change` is `unresolved` for supported regulators, with both
up and down preserved for future simulation controls. Tier C regulators remain
represented as negative-gate audit rows and are excluded from perturbation graph
assembly.

Run:

```bash
cd "/mnt/d/Jepa project"
DOCKER_MEMORY=4g IMAGE=scenicplus:1.0a2-container.1 \
  bash scripts/stage76_run_directionality_audit_wsl.sh
echo "EXIT_CODE=$?"
```

Outputs:

- `results/tables/stage76_signed_tf_target_hypotheses_v1.csv`
- `results/tables/stage76_regulator_directionality_summary_v1.csv`
- `results/tables/stage76_unresolved_directionality_v1.csv`
- `results/reports/stage76_directionality_audit_v1.json`

This audit does not make validated regulation, validated-GRN, causal, activation,
repression, or therapeutic claims.