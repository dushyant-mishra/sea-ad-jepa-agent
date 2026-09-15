import json, hashlib, pathlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 22), b''):
            h.update(c)
    return h.hexdigest()


FILES = ['x1_spec.py', 'x2_audit.py', 'x3_nuis.py', 'x5_within.py', 'x6_fixture.py', 'y1_source.py',
         'y2_donor.py', 'y3_qc.py', 'y4_ln.py', 'z1_repro.py', 'z2_estimand.py', 'z3_donorrec.py',
         'z4_lodo.py', 'z5_lodo.py', 'z6_closeout.py',
         'X_CROSS_VIEW_SHORTCUT_AUDIT_SPEC.json', 'Z_RESIDUAL_OVER_CONTEXT_SPECIFICATION.md',
         'bind_population.npz', 'x_audit.json', 'x_nuisance.json', 'x_within.json', 'x_fixture.json',
         'y_source.json', 'y_donor.json', 'y_qc.json', 'y_ln.json', 'z_repro.json', 'z_estimand.json',
         'z_donorrec.json', 'z_lodo.json', 'screen_out.npz', 'qc_post.npz', 'final_manifest.csv',
         'pair_plan.csv', 'V5_VALUE_ONLY_SAME_CELL_MEASUREMENT_PREFLIGHT_RECEIPT.json']
H = {n: sha(S / n) for n in FILES if (S / n).exists()}

pkg = {
    "package_id": "V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT",
    "scope": "Layer 2 - training-objective shortcut exposure. NOT Layer 1 substrate qualification, NOT Layer 3 downstream inference.",
    "population": {
        "stratum": "BASE_MECHANICS (probability sample)", "cells": 196817, "donors": 94,
        "operators": 42, "sources": {"HVS": 88015, "NPH52": 41218, "SEA_AD": 67584},
        "inclusion": "q_i = min(12,B_o)/B_o, whole blocks, content-independence proven by reproduction (396/396)",
        "stress_strata_excluded_from_all_weighting": True},
    "fold_identities": {
        "donor_held_out": "donor_code mod 5, sizes [39924,33340,44759,39770,39024]",
        "cell_held_out": "default_rng(7).integers(0,5), sizes [39358,39351,39087,39504,39517]",
        "binding_digest": "f0ca25e5e91d2b87991a6ea301d41a4f64d8805519aa39370e29dd43c8635ec0"},
    "model_class": "ridge, lambda=1e-2*n_train, metric = total-variance-explained OOF R2",
    "estimator_validation": json.load(open(S / 'x_fixture.json')),
    "item2_independent_reproduction": json.load(open(S / 'z_repro.json')),
    "item3_estimand_sensitivity": json.load(open(S / 'z_estimand.json')),
    "item4_donor_recurrence": json.load(open(S / 'z_donorrec.json'))['per_source'],
    "item5_lodo_full_refit": {k: {kk: vv for kk, vv in v.items() if kk != 'donor_r2'}
                              for k, v in json.load(open(S / 'z_lodo.json')).items()},
    "item6_loss_geometry_proxy": json.load(open(S / 'y_ln.json')),
    "measurement_shortcut_audit": json.load(open(S / 'x_audit.json')),
    "variance_decomposition": json.load(open(S / 'y_donor.json'))['decomposition'],
    "qc_control_within_donor": json.load(open(S / 'y_qc.json')),
    "corrected_interpretation": {
        "WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES": True,
        "explicitly_not_claimed": ["THE_SIGNAL_IS_BIOLOGICAL", "THE_SIGNAL_IS_NOT_TECHNICAL"],
        "scope_of_qc_control": ("rules out the measured Q_DEPTH/Q_DETECT family as the primary explanation; "
                                "does NOT eliminate unmeasured technical state"),
        "DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_DEMONSTRATED_IN_SEA_AD_AT_THIS_MODEL_CLASS": True,
        "DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_NOT_DEMONSTRATED_IN_HVS_OR_NPH52_AT_THIS_MODEL_CLASS": True,
        "negative_result_is_not_absence": True,
        "prior_claim_corrected": ("the earlier '85% of cross-view signal is operator mean structure' was computed "
                                  "correctly but conflated between-source pooling inflation with donor-generalisation "
                                  "failure; per-source and within-donor analyses supersede that framing")},
    "unresolved_questions": [
        "Whether the within-donor signal survives a non-linear model class - a linear probe bounds neither direction.",
        "Why HVS and NPH52 fail donor generalisation while SEA_AD succeeds; cohort heterogeneity is a hypothesis, not evidence.",
        "Whether unmeasured technical state (beyond Q_DEPTH/Q_DETECT) explains part of the within-donor signal.",
        "Whether the residual-over-context construction changes what the molecular pathway LEARNS - requires training.",
        "The V5 teacher target is undefined, so no objective-aligned result is possible, only a geometry proxy.",
        "Whether operator identity is admissible as a training-time input at all - a design decision, not a measurement."],
    "terminals": [
        "MEASUREMENT_SHORTCUT_NOT_DEMONSTRATED_AT_THIS_MODEL_CLASS",
        "WITHIN_DONOR_MOLECULAR_VIEW_SIGNAL_BEYOND_MEASURED_QC_RECURS_ACROSS_ALL_THREE_SOURCES",
        "DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_DEMONSTRATED_IN_SEA_AD_AT_THIS_MODEL_CLASS",
        "DONOR_GENERALISABLE_LINEAR_CROSS_VIEW_SIGNAL_NOT_DEMONSTRATED_IN_HVS_OR_NPH52_AT_THIS_MODEL_CLASS",
        "CONTEXT_SHORTCUT_DECOMPOSITION_INDEPENDENTLY_REPRODUCED",
        "ESTIMAND_SENSITIVITY_CHARACTERIZED",
        "DONOR_LEVEL_RECURRENCE_CHARACTERIZED",
        "MECHANICS_ALIGNED_LOSS_PROXY_CHARACTERIZED"],
    "retained": [
        "BATCH_TECHNICAL_VS_BIOLOGICAL_DECOMPOSITION_NOT_IDENTIFIABLE_IN_FULL104",
        "CURRENT_V5_TEACHER_AUTHORITY_NOT_YET_ESTABLISHED",
        "PRIMARY_REPRESENTATION_AUTHORITY_NOT_YET_FROZEN",
        "MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN",
        "V3_NULL_NOT_YET_FROZEN",
        "NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION",
        "TRAINING_OFF"],
    "not_done": ["residual objective NOT implemented - specification only",
                 "no production training", "no representation modification",
                 "no operator/source residualization", "D_shared and protected outcomes untouched"],
    "artifact_hashes": H}
p = S / 'V5_LAYER2_CROSS_VIEW_SHORTCUT_CLOSEOUT.json'
p.write_text(json.dumps(pkg, indent=2, sort_keys=True))
print('closeout: %s (%d bytes)' % (p.name, p.stat().st_size))
print('CLOSEOUT_SHA256 %s' % sha(p))
print('artifacts bound: %d' % len(H))
