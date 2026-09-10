import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v5.pretraining_qualification_bundle_v1 import (
    REQUIRED_EVIDENCE,
    validate_pretraining_qualification_bundle,
)


def evidence():
    return {
        name: {
            "status": "EXECUTED_PASS",
            "artifact_sha256": format(i + 1, "064x"),
            "authority_id": f"{name}-authority-v1",
            "training_authorized": False,
        }
        for i, name in enumerate(REQUIRED_EVIDENCE)
    }


def run(e=None, frozen=True, started=False):
    return validate_pretraining_qualification_bundle(
        e or evidence(),
        qualification_rules_frozen_before_candidate_model_outcome=frozen,
        optimizer_started=started,
    )


def test_complete_bundle_closes_but_never_authorizes_training():
    out = run()
    assert out["qualification_bundle_closed"] is True
    assert out["training_authorized"] is False
    assert len(out["bundle_sha256"]) == 64


def test_missing_gate_cannot_hide_behind_generic_anticheat_marker():
    e = evidence(); del e["shortcut_superiority"]
    e["anti_cheat"] = {
        "status": "EXECUTED_PASS", "artifact_sha256": "f" * 64,
        "authority_id": "generic", "training_authorized": False,
    }
    with pytest.raises(RuntimeError, match="EVIDENCE_SET_MISMATCH"):
        run(e)


def test_missing_one_required_gate_stops():
    e = evidence(); del e["cuda_gate2_mechanics"]
    with pytest.raises(RuntimeError, match="cuda_gate2_mechanics"):
        run(e)


def test_unexpected_gate_stops_instead_of_being_ignored():
    e = evidence(); e["pretty_embedding"] = e["representation_firewall"].copy()
    with pytest.raises(RuntimeError, match="EVIDENCE_SET_MISMATCH"):
        run(e)


def test_nonexecuted_or_skipped_gate_stops():
    e = evidence(); e["heldout_biology_validation"]["status"] = "SKIPPED"
    with pytest.raises(RuntimeError, match="NOT_EXECUTED_PASS"):
        run(e)


def test_component_cannot_self_authorize_training():
    e = evidence(); e["qc_measurement_confounding_closure"]["training_authorized"] = True
    with pytest.raises(RuntimeError, match="COMPONENT_CLAIMS_TRAINING_AUTHORITY"):
        run(e)


def test_rules_must_be_frozen_before_candidate_outcome():
    with pytest.raises(RuntimeError, match="RULES_NOT_PROSPECTIVE"):
        run(frozen=False)


def test_bundle_must_precede_optimizer_start():
    with pytest.raises(RuntimeError, match="AFTER_OPTIMIZER_START"):
        run(started=True)


def test_invalid_artifact_digest_stops():
    e = evidence(); e["student_representation_collapse"]["artifact_sha256"] = "not-a-sha"
    with pytest.raises(ValueError, match="SHA-256"):
        run(e)


def test_evidence_schema_is_exact_not_extensible_by_accident():
    e = evidence(); e["donor_recurrence_validation"]["checkpoint_metric"] = 0.99
    with pytest.raises(ValueError, match="unexpected fields"):
        run(e)


def test_bundle_digest_is_order_independent():
    e = evidence()
    a = run(e)
    b = run(dict(reversed(list(e.items()))))
    assert a["bundle_sha256"] == b["bundle_sha256"]
