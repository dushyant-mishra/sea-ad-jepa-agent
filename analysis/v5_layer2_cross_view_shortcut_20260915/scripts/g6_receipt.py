import json, pathlib, hashlib
S = pathlib.Path(r'C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad')
H = json.load(open(S / 'aud_hashes.json'))
V = json.load(open(S / 'aud_verify.json'))
D = json.load(open(S / 'aud_design.json'))
W = json.load(open(S / 'aud_weights.json'))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 22), b''):
            h.update(c)
    return h.hexdigest()


NESTNOTE = V['screen_mech_json_nesting_flag_note']
SUPERSEDED = (
    "preflight.py seeded Philox from sha256(THIN_NS|block_key) and used ladder "
    "PROB=[.25,.25,.25,.15,.10]; screen.py shipped cell-identity seeding with "
    "COND=[.25,1/3,.5,.6]. These preflight results therefore validate the mechanics "
    "FAMILY, not the shipped construction.")
QDEPTHNOTE = (
    "qdepth_cnt.npy holds the DECLARED source_library (ledger + out-of-ledger), not the "
    "in-block ledger sum; indexed by selection_row it matches lib_p100 exactly for all "
    "201,149 rows (max abs diff 0). An initial assertion against the ledger sum failed "
    "because it named the wrong quantity.")
CONTENTIND = (
    "PROVEN BY REPRODUCTION: recomputing the rank from namespace + block_key alone "
    "reproduced the frozen 396-block BASE selection exactly (396/396, 0 missing, 0 extra). "
    "The hash input contains no cell content, depth, expression, QC, outcome, source "
    "abundance or learned quantity.")

R = {
    "receipt_id": "V5_VALUE_ONLY_SAME_CELL_MEASUREMENT_PREFLIGHT_RECEIPT",
    "provenance_class": "RECEIPT_ASSEMBLED_AFTER_SCREEN_FROM_PREEXISTING_EVIDENCE",
    "provenance_warning": (
        "This receipt was assembled after the screen completed. It is NOT a prospectively "
        "created artifact. Each check below carries its own execution class; only checks "
        "marked CHECK_EXECUTED_BEFORE_SCREEN_ON_SHIPPED_CONSTRUCTION were both run in "
        "advance and run against the construction that actually shipped."),
    "authority": "MECHANICS_SCALE_MEASUREMENT_SCREEN__NOT_FULL104_QUALIFICATION",
    "artifact_hashes": H,
    "rng": {
        "namespace": "JEPA_V5_SAME_CELL_THINNING_V1",
        "binding_rule": "Philox(int(sha256(THIN_NS|canonical_cell_id)[:8])) - one generator per CELL IDENTITY",
        "outside_ledger_substream": "Philox(int(sha256(THIN_NS|canonical_cell_id|OUTSIDE_LEDGER_TOTAL|<outside>)[:8]))",
        "bit_generator": "numpy.random.Philox",
        "numpy_version": "1.24.2",
        "conditional_ladder": [0.25, 0.3333333333333333, 0.5, 0.6],
        "cumulative_retention": [0.25, 0.50, 0.75, 0.90],
        "storage_independence": (
            "seed depends only on canonical_cell_id; NOT on block_key, shard, row offset or "
            "any other storage artifact, so repacking the store cannot change any cell's realization")},
    "base_sampling_design": {
        "BASE_SAMPLING_DESIGN": "OPERATOR_STRATIFIED_WHOLE_BLOCK_HASH_RANK_SAMPLE",
        "CELL_INCLUSION_PROBABILITY_WITHIN_OPERATOR": "min(12,B_o)/B_o",
        "selection_rule": "per operator, rank population blocks by sha256(JEPA_V5_MECHANICS_SCALE_MEASUREMENT_SCREEN_SAMPLE_V1|block_key), take first 12",
        "BLOCK_HASH_SELECTION_IS_CONTENT_INDEPENDENT_BY_CONSTRUCTION": True,
        "content_independence_evidence": CONTENTIND,
        "population_blocks": 8915, "operators": 42, "selected_blocks": 396,
        "whole_block_inclusion": D['whole_block'],
        "q_min": 0.008386, "q_median": 0.406897, "q_max": 1.0,
        "operators_with_Bo_le_12_hence_q_eq_1": 16,
        "not_simple_random_sampling": True,
        "primary_inclusion_unit": "BLOCK"},
    "population": {"N_total": D['N_total'], "N_by_source": D['Ns'], "S": 3},
    "checks": [
        {"name": "p=1.00 identity replay vs frozen substrate (5 blocks, both views)",
         "class": "CHECK_EXECUTED_BEFORE_SCREEN_ON_SHIPPED_CONSTRUCTION",
         "note": "binding-independent: p=1 performs no draws, so the superseded RNG binding does not affect it",
         "result": "PASS (max abs diff below 1e-4 tolerance; script preflight.py)"},
        {"name": "full-sample p=1 identity: lib_p100 == declared source_library for every cell",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS", "value": V['p1_identity_lib_equals_source_library'], "n": V['N']},
        {"name": "nested-thinning monotonicity and analytic retention (preflight)",
         "class": "CHECK_EXECUTED_BEFORE_SCREEN_ON_SUPERSEDED_RNG_BINDING",
         "note": SUPERSEDED,
         "result": "PASS (on superseded binding) - DOES NOT CARRY"},
        {"name": "nested-thinning monotonicity, shipped construction",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS",
         "ascending_violations": V['nesting_violations_ascending_correct_orientation'],
         "library_total_violations": V['lib_total_nesting_violations'],
         "screen_mech_json_raw_flag": V['screen_mech_json_nesting_flag_raw'],
         "defect_note": NESTNOTE},
        {"name": "analytic thinning verifier, shipped construction",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS", "observed_retention": V['analytic_retention'],
         "max_abs_error": V['analytic_retention_max_abs_error']},
        {"name": "deterministic replay reproduces the frozen realization",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS", "total_deviation": V['replay_vs_frozen_total_deviation'],
         "note": "qc_replay.py re-ran the exact RNG call sequence; all five lib_p*, ledger and outside matched bit-for-bit"},
        {"name": "full-library arithmetic: ledger + outside == declared source_library",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS", "exact": V['ledger_plus_outside_equals_source_library_exact'],
         "max_abs_diff": V['ledger_plus_outside_max_abs_diff']},
        {"name": "OUTSIDE_LEDGER_TOTAL non-negativity and mass",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS", "nonneg": V['outside_ledger_nonneg'],
         "cells_with_zero_outside": V['outside_ledger_zero_cells'],
         "outside_mass_fraction": V['outside_ledger_mass_fraction'],
         "rule": "thinned in its own RNG substream so its presence cannot perturb in-ledger draws; normalization denominator is the FULL library (ledger+outside), applied exactly once"},
        {"name": "Q_DEPTH row authority",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS", "note": QDEPTHNOTE,
         "matches_source_library": True, "max_abs_diff": 0.0},
        {"name": "Q_DETECT row authority",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS",
         "note": "re-derived p=1 detected-address count equals qdetect_cnt.npy exactly for all rows",
         "value": V['qdetect_row_authority_matches_p1_detect']},
        {"name": "canonical cell id / selection row uniqueness",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS", "selection_row_unique": V['selection_row_unique'],
         "canonical_cell_id_unique": V['canonical_cell_id_unique'], "N": V['N']},
        {"name": "cells addressed individually, not by block",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS",
         "note": "screen.py maps selection_row -> global index per cell; RNG seeded per canonical_cell_id"},
        {"name": "zero-library accounting (unconditional denominators)",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS",
         "policy": "MEASUREMENT_FAILURE_ZERO_LIBRARY -> NOT_ESTIMABLE, retained in the attempted population, never imputed",
         "by_p": V['zero_library']},
        {"name": "BASE/STRESS stratum disjointness",
         "class": "CHECK_VERIFIED_AFTER_SCREEN_FROM_FROZEN_EVIDENCE",
         "result": "PASS", "overlapping_selection_rows": D['base_stress_overlap']},
        {"name": "runtime benchmark",
         "class": "MIXED",
         "preflight_projection_class": "CHECK_EXECUTED_BEFORE_SCREEN_ON_SUPERSEDED_RNG_BINDING",
         "observed_screen_wall_minutes": 18.9,
         "observed_replay_wall_minutes": 9.6,
         "blocks_read": 1698, "cells_filled": 201149}],
    "firewall_state": {
        "NO_D_SHARED_OUTCOME_EXECUTION_OR_INSPECTION": True, "TRAINING_OFF": True,
        "PROTECTED_DATA_CLOSED": True, "TD60_OFF": True, "RELATIONAL_ACTIVATION_OFF": True,
        "inputs_read": [
            "expression_level4 count blocks + meta (FULL104)",
            "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv",
            "stage81a2r molecular address registry",
            "FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
            "D:/jepa_v5_substrate_20260914 V0_full.npy / V1_full.npy",
            "scratchpad frozen screen artifacts"],
        "inputs_NOT_read": [
            "D_shared outcomes", "pathology / protected donor variables",
            "training checkpoints", "TD60"]},
    "weighting": W,
    "decision_authority": {
        "MEASUREMENT_ROBUSTNESS_DECISION_RULE_NOT_YET_FROZEN": True,
        "no_threshold_introduced_after_seeing_outcomes": True}
}
p = S / 'V5_VALUE_ONLY_SAME_CELL_MEASUREMENT_PREFLIGHT_RECEIPT.json'
p.write_text(json.dumps(R, indent=2, sort_keys=True))
print('receipt written: %s  (%d bytes)' % (p.name, p.stat().st_size))
print('receipt sha256: %s' % sha(p))
print()
for c in R['checks']:
    print('  %-56s %s' % (c['name'][:56], c['class']))
