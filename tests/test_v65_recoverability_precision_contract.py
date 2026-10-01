from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_recoverability_precision_contract_freezes_materiality_and_test_firewall():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    assert "DELTA_R2 >= 0.05" in t
    assert "one canonical permutation schedule" in t
    assert "generate exactly 10,000 sequential `rng.permutation(n_donor_nuclei)` permutations" in t
    assert "0, 2, 4, 8, 16" in t
    assert "Select the **largest contiguous eligible rank**" in t
    assert "no skipping over a failed lower rank" in t.lower()
    assert "smallest-eligible rule is superseded" in t.lower()
    assert "median TEST `DELTA_R2` is at least 50% of median VALIDATION" in t
    assert "cannot assign PRIVILEGED_PRIVATE" in t
    assert "four independent donors" in t
    assert "will NOT report a donor-bootstrap interval over four TEST donors" in t

def test_recoverability_test_cannot_retune_after_opening():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    for forbidden in [
        "changing rank",
        "changing alpha",
        "changing normalization",
        "changing factor basis",
        "changing thresholds",
        "dropping a TEST donor",
    ]:
        assert forbidden in t
    assert "TEST may not influence" in t


def test_recoverable_projection_is_target_space_and_rotation_unambiguous():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    assert "C = Z_true_train^T Z_pred_train" in t
    assert "P_k = U[:, :k] U[:, :k]^T" in t
    assert "Z_true_shared = Z_true P_k" in t
    assert "Z_pred_shared = Z_pred P_k" in t
    assert "UNQUALIFIED_FOR_SELECTION" in t


def test_geometry_gate_v2_is_distinct_and_reproducible():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    assert "canonical correlations" in t
    assert "relational-geometry correlation" in t
    assert "principal-angle threshold is **SUPERSEDED BEFORE REAL EXECUTION**" in t
    assert "numpy.random.PCG64" in t
    assert "digest[:8]" in t
    assert 'byte order' in t
    assert 'numpy.quantile(null, 0.99, method="higher")' in t


def test_incremental_shell_gate_is_frozen_for_validation_and_test():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    for shell in ("S_2 = P_2","S_4 = P_4 - P_2","S_8 = P_8 - P_4","S_16 = P_16 - P_8"):
        assert shell in t
    assert "aggregate `P_k` and its incremental shell `S_k`" in t
    assert "A higher aggregate rank may not qualify" in t
    assert "Every incremental shell from `S_2` through `S_k`" in t
    assert "TEST may not fall back to a smaller rank" in t


def test_nested_shells_and_intrinsic_ranks_are_frozen():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    for expr in ["S_2 = P_2","S_4 = P_4 - P_2","S_8 = P_8 - P_4","S_16 = P_16 - P_8"]:
        assert expr in t
    assert "aggregate `P_k` and its incremental shell `S_k`" in t
    assert "aggregate `P_k`, the expected intrinsic rank is `k`" in t
    assert "`S_4: 2`" in t and "`S_8: 4`" in t and "`S_16: 8`" in t
    assert "Every incremental shell from `S_2` through `S_k`" in t


def test_tie_tolerance_and_geometry_numerics_are_frozen():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    assert "1e-8 * max(1, abs(s[k-1]), abs(s[k]))" in t
    assert "1e-8 * max(1, abs(s[k-1]), abs(s[k]))" in t
    assert "pairwise Euclidean distances" in t
    assert "nonzero left-singular subspace" in t
    assert "Fail closed if:" in t
    assert "No rank, shell or metric gets an independently resampled null" in t


def test_pairing_and_geometry_share_one_canonical_permutation_schedule():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    assert "one canonical permutation schedule" in t
    assert "No rank, shell or metric gets an independently resampled null" in t
    assert "numpy.random.PCG64" in t
    assert "10,000 sequential `rng.permutation(n_donor_nuclei)`" in t
    assert 'numpy.quantile(null, 0.99, method="higher")' in t
    assert "strictly greater" in t
