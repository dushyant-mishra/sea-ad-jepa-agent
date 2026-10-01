from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_recoverability_precision_contract_freezes_materiality_and_test_firewall():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_20260930.md").read_text()
    assert "DELTA_R2 >= 0.05" in t
    assert "10,000 deterministic permutations per donor" in t
    assert "0, 2, 4, 8, 16" in t
    assert "Select the **smallest** eligible nonzero rank" in t
    assert "median TEST `DELTA_R2` is at least 50% of median VALIDATION" in t
    assert "cannot assign PRIVILEGED_PRIVATE" in t
    assert "four independent donors" in t
    assert "will NOT report a donor-bootstrap interval over four TEST donors" in t

def test_recoverability_test_cannot_retune_after_opening():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_20260930.md").read_text()
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
