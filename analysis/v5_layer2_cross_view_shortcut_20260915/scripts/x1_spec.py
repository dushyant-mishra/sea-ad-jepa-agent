"""Freeze the cross-view shortcut-audit specification BEFORE computing anything."""
import json, hashlib, pathlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
SPEC = {
    "audit_id": "V5_CROSS_VIEW_MEASUREMENT_SHORTCUT_AUDIT_V1",
    "authority": "DIAGNOSTIC_SHORTCUT_EXPOSURE_AUDIT__NOT_A_QUALIFICATION_GATE",
    "question": "Does sharing the measurement state make V0 more useful for predicting V1?",
    "inputs_frozen": ["screen_out.npz", "qc_post.npz", "final_manifest.csv"],
    "population": "BASE_MECHANICS cells estimable at every p (probability sample; stress strata excluded)",
    "model_class": {
        "estimator": "ridge",
        "lambda": "1e-2 * n_train (identical to frozen ablation procedure)",
        "cv": "donor-held-out, 5 folds by donor_code mod 5",
        "no_in_sample_evaluation": True,
        "no_random_cell_split": True},
    "metric": {
        "name": "total_variance_explained_oof_r2",
        "formula": "1 - sum||y-yhat||^2 / sum||y-ybar||^2",
        "rationale": "exact under the classical attenuation null, and shared across all tests"},
    "scalars": {
        "variables": ["L_p", "detect_p", "L_1", "detect_1"],
        "transform": "log1p then standardized on training folds' scale"},
    "tests": {
        "T1_matched_state_advantage": {
            "contrast": "R2(V1^p <- V0^p) vs R2(V1^p <- V0^1.0), target identical in both arms",
            "symmetric": "R2(V0^p <- V1^p) vs R2(V0^p <- V1^1.0)",
            "null_direction_note": "V0^1.0 is the CLEANER predictor, so the contrast is biased toward the null"},
        "T2_scalar_channel_recovery": {
            "ladder": ["V0^1.0", "V0^1.0 + L_p", "V0^1.0 + L_p + detect_p",
                       "V0^1.0 + L_p + detect_p + L_1 + detect_1", "V0^p"],
            "question": "how much of any matched-state advantage returns from low-dimensional realized state"},
        "T4_matrix": {
            "grid": "C(p_i,p_j) = R2(V1^{p_j} <- V0^{p_i}) over the full 5x5",
            "separable_null": "C_null(p_i,p_j) = C(p_i,1)*C(1,p_j)/C(1,1)",
            "excess_ratio": "R(p_i,p_j) = C(p_i,p_j)*C(1,1) / (C(p_i,1)*C(1,p_j))",
            "null_value": 1.0,
            "rationale": "classical attenuation identity, exact for R2 under independent per-view attenuation"}},
    "prospective_structural_prediction": (
        "Conditional on the original counts, thinned counts are independent binomials across addresses and the "
        "two views draw from DISJOINT address sets. The only stochastic term shared by the two views is the "
        "realized full-library denominator L_p (including its out-of-ledger component), which enters both views' "
        "normalization identically. PREDICTION: if a matched-state advantage exists, supplying L_p (and detect_p) "
        "to the clean predictor should recover nearly all of it. A residual surviving beyond the scalars would "
        "indicate a coupling not accounted for in this description of the construction."),
    "outcome_semantics": {
        "positive": "SHORTCUT_EXPLOITABLE_DEMONSTRATED",
        "negative": "SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS",
        "explicitly_not": "SHORTCUT_ABSENT",
        "note": ("a simple probe finding the shortcut proves it exists; the same probe failing proves only that "
                 "it is not accessible to this model class, and does not clear a deep encoder trained against "
                 "exactly this objective")},
    "retired_before_execution": {
        "nuisance_matched_permutation": (
            "RETIRED: exact matching on realized (L_p, detect_p, source, operator) would leave overwhelmingly "
            "singleton strata in FULL104, and coarsening the match after observing that would be threshold "
            "widening after seeing the discrepancy. Retired prospectively rather than audited and relaxed."),
        "biological_signal_subtraction_claim": (
            "WITHDRAWN: observed cross-view predictability decomposes into a measured-state-associated component "
            "and a REMAINING component. The remainder is unresolved, not automatically biological -- it may hold "
            "unmeasured technical state and representation artifacts.")},
    "no_threshold_attached": True,
    "constraints_respected": ["NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION", "TRAINING_OFF",
                              "PROTECTED_DATA_CLOSED", "no new thinning realization", "no representation change"]
}
p = S / 'X_CROSS_VIEW_SHORTCUT_AUDIT_SPEC.json'
p.write_text(json.dumps(SPEC, indent=2, sort_keys=True))
print('spec frozen: %s' % p.name)
print('spec sha256: %s' % hashlib.sha256(p.read_bytes()).hexdigest())
