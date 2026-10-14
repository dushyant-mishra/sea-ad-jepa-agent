from __future__ import annotations

import pytest

import scripts.v5.td_real_evidence_ladder_contract_v1 as E


def _manifest():
    return {
        "schema": "JEPA_TD_REAL_EVIDENCE_LADDER_MANIFEST_V1",
        "frozen": True,
        "candidate_id": "C1_SHARED_EMERGENT",
        "full_evidence_rights": ["RNA:CORE", "RNA:EXTENDED", "CONTEXT:LAWFUL"],
        "levels": [
            {
                "level_id": "L1_CORE",
                "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION",
                "evidence_rights": ["RNA:CORE"],
            },
            {
                "level_id": "L2_EXTENDED",
                "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION",
                "evidence_rights": ["RNA:CORE", "RNA:EXTENDED"],
            },
            {
                "level_id": "L3_FULL",
                "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION",
                "evidence_rights": ["RNA:CORE", "RNA:EXTENDED", "CONTEXT:LAWFUL"],
            },
        ],
    }


def test_frozen_three_level_nested_manifest_derives_terminal_contrast():
    out = E.derive_evidence_ladder(_manifest())
    assert out["status"] == "EVIDENCE_LADDER_FROZEN"
    assert out["candidate_id"] == "C1_SHARED_EMERGENT"
    assert out["level_ids"] == ["L1_CORE", "L2_EXTENDED", "L3_FULL"]
    assert out["terminal_contrast"] == {
        "reference_level": "L2_EXTENDED",
        "full_level": "L3_FULL",
    }
    assert out["strict_adjacent_monotonicity_required"] is False
    assert out["count_thinning_authorized"] is False


def test_unfrozen_manifest_is_rejected():
    manifest = _manifest()
    manifest["frozen"] = False
    with pytest.raises(E.EvidenceLadderError, match="frozen"):
        E.derive_evidence_ladder(manifest)


def test_fewer_than_three_levels_is_not_estimable_not_invented():
    manifest = _manifest()
    manifest["levels"] = manifest["levels"][:2]
    manifest["full_evidence_rights"] = manifest["levels"][-1]["evidence_rights"]
    out = E.derive_evidence_ladder(manifest)
    assert out["status"] == "NOT_ESTIMABLE_FEWER_THAN_THREE_LAWFUL_LEVELS"


def test_levels_must_be_strictly_nested_without_rights_removal():
    manifest = _manifest()
    manifest["levels"][1]["evidence_rights"] = ["RNA:EXTENDED"]
    with pytest.raises(E.EvidenceLadderError, match="strictly nested"):
        E.derive_evidence_ladder(manifest)


def test_duplicate_rights_or_level_ids_fail_closed():
    manifest = _manifest()
    manifest["levels"][0]["evidence_rights"] = ["RNA:CORE", "RNA:CORE"]
    with pytest.raises(E.EvidenceLadderError, match="unique"):
        E.derive_evidence_ladder(manifest)
    manifest = _manifest()
    manifest["levels"][1]["level_id"] = "L1_CORE"
    with pytest.raises(E.EvidenceLadderError, match="level_id"):
        E.derive_evidence_ladder(manifest)


def test_terminal_level_must_equal_declared_full_rights_exactly():
    manifest = _manifest()
    manifest["full_evidence_rights"].append("MODALITY:EXTRA")
    with pytest.raises(E.EvidenceLadderError, match="terminal level"):
        E.derive_evidence_ladder(manifest)


def test_count_depth_or_fraction_operator_is_forbidden_in_g7():
    manifest = _manifest()
    manifest["levels"][1]["operator_family"] = "COUNT_DEPTH_THINNING"
    with pytest.raises(E.EvidenceLadderError, match="count thinning"):
        E.derive_evidence_ladder(manifest)


def test_rights_tokens_must_be_literal_nonempty_strings():
    manifest = _manifest()
    manifest["levels"][1]["evidence_rights"] = ["RNA:CORE", 25]
    with pytest.raises(E.EvidenceLadderError, match="nonempty strings"):
        E.derive_evidence_ladder(manifest)


def test_static_contract_has_no_outcome_or_training_authority():
    out = E.derive_evidence_ladder(_manifest())
    assert out["authority"] == {
        "value_read_authorized": False,
        "real_tournament_authorized": False,
        "target_selection_authorized": False,
        "representation_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }
    assert out["claim_boundary"] == "STATIC_EVIDENCE_LADDER_ONLY__NO_G7_BIOLOGICAL_OUTCOME"
