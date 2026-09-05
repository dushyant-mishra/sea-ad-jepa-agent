# F1-B Independent Verification Review — 2026-09-05

Status: `STOP_F1B_INDEPENDENT_VERIFICATION_REPAIR_REQUIRED`

Reviewed base: `f1b-minimal-bridge-20260905@f0fb23c2c520028fc4d8c18a32e197f03a1d7cf8`.

This review preserves the existing synthetic observation as descriptive evidence. It does not rewrite the implementer's contract or result after seeing outcomes. It identifies implementation defects that must be repaired prospectively before a formal verifier PASS or any real-data authorization.

## Independently closed historical dependency

The T1 optimizer ID→parameter-name mapping was reconstructed independently from checkpoint ordering. Across u10/u25/u50/u100/u200/u205, all 48 required `{attention_norm,Q,K,V}×6` tensors have both Adam moments exactly zero, while 12/12 attention-output tensors have nonzero moments. Claude's B7 uncertainty can therefore be closed.

## Verifier findings

1. **G1 nonfinite hole.** `gradient_coverage()` counts only norm==0. A NaN/Inf gradient norm is not zero and can satisfy the current G1 arithmetic.
2. **G2 contract mismatch.** The contract requires both `exp_avg` and `exp_avg_sq` nonzero. The implementation marks a tensor dead only when both are zero. A zero/missing/nonfinite second moment can therefore be hidden by a nonzero first moment.
3. **G3 pooled movement.** G3 gates mean relative movement across the family. A decay-only tensor can be hidden by large movement elsewhere. The protected family requires a minimum/per-tensor rule plus explicit zero-baseline handling.
4. **Predictor mechanics are not gated.** The successor's `SingletonQueryPredictor` is critical to the observed conditional computation but its gradients/moments/movement are telemetry-only.
5. **Backbone routing samples cell 0.** The implementation uses the first cell's query addresses and first cell support; this is not valid for variable-support real data.
6. **Predictor routing normalizes by cell 0 support.** Real cells/operators have different valid-key counts; normalization must be per cell/query.
7. **G4 implementation does not match its prose.** The current backbone spread expression compares across heads rather than directly across query addresses.
8. **Routing metric name collision.** F1-B computes entropy perplexity `exp(H)`; earlier local probes used participation ratio `1/sum(p^2)`. Both are legitimate but must be explicitly named and preferably both reported.
9. **Predictor-routing telemetry lacks analytic mutation tests.** Uniform, one-hot, masked-key, variable-support and permutation invariance tests are required.
10. **G5 real biology is not implemented.** Fixed-coordinate projection retention is nonterminal in synthetic mode but would still be the arithmetic used if `biology_evaluable=True`. Real G5 must use checkpoint-specific refit donor-held-out probes.
11. **Frozen horizon mismatch.** The contract freezes 40 updates; the published descriptive trajectory used 300 via `--updates`. Preserve u0–u300 as descriptive evidence; formal requalification should rerun exactly 40 after repairs.
12. **Directional claim is too strong.** Query-centering removes additive query-common cell components; it does not prove a query-conditioned transformation of global/CELL state is impossible. Real M3 therefore requires CELL-only and identity-only controls.
13. **Target semantics differ from F0/F1.** F1-B masks the entire query set Q; F0/F1 masks one q at a time. A TRAIN-only singleton-vs-all-Q target-equivalence audit is required before production training.
14. **Production AMP smoke remains open.** The published F1-B loop is CUDA but does not qualify the final fp16 autocast+GradScaler production successor path.

## Required prospective repair

Create a new implementation generation. Do not edit or replace the existing f0fb result. The repaired generation must:
- fail on missing/zero/nonfinite gradient for every mandatory tensor;
- require both Adam moments independently;
- gate minimum per-tensor movement beyond exact decay, with zero-baseline handling;
- gate the authenticated predictor parameter registry;
- compute backbone/predictor routing for all cells with per-cell valid-key counts;
- report `N_eff_entropy` and `N_eff_participation` separately plus top-k mass and query-map cosine;
- add analytic routing mutation tests;
- keep real G5 fail-closed until the refit-probe protocol is frozen;
- formal-run exactly 40 updates;
- bind both original and verifier-repair contracts.

Terminal remains STOP until a fresh independent verifier reruns the repaired generation.
