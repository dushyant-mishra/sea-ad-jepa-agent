from __future__ import annotations

import pytest

import scripts.v5.td_real_relational_manifest_v1 as R


def _manifest():
    return {
        "schema": "JEPA_TD_REAL_RELATIONAL_MANIFEST_V1",
        "frozen": True,
        "candidate_id": "C2_RELATIONAL_SHARED",
        "relation_family": "SCALE_FREE_TRIPLET_ORDER",
        "scale_class": "GLOBAL_SCALE_FREE",
        "required_sources": ["HVS", "NPH52", "SEA_AD"],
        "lawful_view_ids": ["VIEW_A", "VIEW_B"],
        "null_permutation_unit": "RELATION_ID_WITHIN_DONOR_SOURCE_SUPPORT_STRATUM",
        "support_semantics": {
            "measured_zero": "VALID_MEASUREMENT",
            "unresolved_or_unsupported": "ABSTAIN",
            "imputation": "FORBIDDEN",
        },
        "relation_units": [
            {
                "relation_id": "REL_0001",
                "member_address_ids": ["ADDR_A", "ADDR_B", "ADDR_C"],
                "address_binding_state": "REPAIRED_41K_ADDRESS_BOUND",
            },
            {
                "relation_id": "REL_0002",
                "member_address_ids": ["ADDR_D", "ADDR_E", "ADDR_F"],
                "address_binding_state": "REPAIRED_41K_ADDRESS_BOUND",
            },
        ],
    }


def test_valid_manifest_freezes_scale_free_triplet_incumbent():
    out = R.derive_relational_contract(_manifest())
    assert out["status"] == "RELATIONAL_MANIFEST_FROZEN"
    assert out["candidate_id"] == "C2_RELATIONAL_SHARED"
    assert out["relation_family"] == "SCALE_FREE_TRIPLET_ORDER"
    assert out["scale_class"] == "GLOBAL_SCALE_FREE"
    assert out["required_sources"] == ["HVS", "NPH52", "SEA_AD"]
    assert out["relation_count"] == 2
    assert out["fine_locality_authorized"] is False
    assert out["graph_topology_claim_authorized"] is False


def test_manifest_must_be_frozen():
    manifest = _manifest()
    manifest["frozen"] = False
    with pytest.raises(R.RelationalManifestError, match="frozen"):
        R.derive_relational_contract(manifest)


def test_only_current_relational_candidate_is_allowed():
    manifest = _manifest()
    manifest["candidate_id"] = "C1_SHARED_EMERGENT"
    with pytest.raises(R.RelationalManifestError, match="C2_RELATIONAL_SHARED"):
        R.derive_relational_contract(manifest)


def test_fine_local_or_fraction_mining_is_not_reopened():
    manifest = _manifest()
    manifest["scale_class"] = "NEAREST_THIRD_FINE_LOCAL"
    with pytest.raises(R.RelationalManifestError, match="fine locality"):
        R.derive_relational_contract(manifest)


def test_relation_family_is_exact_scale_free_triplet_order():
    manifest = _manifest()
    manifest["relation_family"] = "STRING_GRAPH_EDGE"
    with pytest.raises(R.RelationalManifestError, match="SCALE_FREE_TRIPLET_ORDER"):
        R.derive_relational_contract(manifest)


def test_required_sources_are_exact_and_noncompensating():
    manifest = _manifest()
    manifest["required_sources"] = ["HVS", "SEA_AD"]
    with pytest.raises(R.RelationalManifestError, match="HVS.*NPH52.*SEA_AD"):
        R.derive_relational_contract(manifest)


def test_at_least_two_unique_lawful_views_are_required():
    manifest = _manifest()
    manifest["lawful_view_ids"] = ["VIEW_A"]
    with pytest.raises(R.RelationalManifestError, match="at least two"):
        R.derive_relational_contract(manifest)
    manifest = _manifest()
    manifest["lawful_view_ids"] = ["VIEW_A", "VIEW_A"]
    with pytest.raises(R.RelationalManifestError, match="unique"):
        R.derive_relational_contract(manifest)


def test_relation_units_bind_exact_three_unique_repaired_addresses():
    manifest = _manifest()
    manifest["relation_units"][0]["member_address_ids"] = ["ADDR_A", "ADDR_A", "ADDR_C"]
    with pytest.raises(R.RelationalManifestError, match="three unique"):
        R.derive_relational_contract(manifest)
    manifest = _manifest()
    manifest["relation_units"][0]["address_binding_state"] = "PRE_REPAIR_GENE_SYMBOL_ONLY"
    with pytest.raises(R.RelationalManifestError, match="REPAIRED_41K_ADDRESS_BOUND"):
        R.derive_relational_contract(manifest)


def test_relation_ids_and_member_tokens_must_be_literal_unique_strings():
    manifest = _manifest()
    manifest["relation_units"][1]["relation_id"] = "REL_0001"
    with pytest.raises(R.RelationalManifestError, match="relation_id"):
        R.derive_relational_contract(manifest)
    manifest = _manifest()
    manifest["relation_units"][0]["member_address_ids"] = ["ADDR_A", 3, "ADDR_C"]
    with pytest.raises(R.RelationalManifestError, match="nonempty strings"):
        R.derive_relational_contract(manifest)


def test_null_unit_is_frozen_and_preserves_donor_source_support():
    manifest = _manifest()
    manifest["null_permutation_unit"] = "GLOBAL_RELATION_SHUFFLE"
    with pytest.raises(R.RelationalManifestError, match="donor.*source.*support"):
        R.derive_relational_contract(manifest)


def test_support_semantics_are_exact_and_imputation_forbidden():
    manifest = _manifest()
    manifest["support_semantics"]["imputation"] = "ALLOWED"
    with pytest.raises(R.RelationalManifestError, match="support semantics"):
        R.derive_relational_contract(manifest)


def test_unknown_fields_fail_closed_to_prevent_locality_mining():
    manifest = _manifest()
    manifest["locality_fraction"] = 0.5
    with pytest.raises(R.RelationalManifestError, match="fields"):
        R.derive_relational_contract(manifest)


def test_static_manifest_grants_no_biological_or_training_authority():
    out = R.derive_relational_contract(_manifest())
    assert out["authority"] == {
        "value_read_authorized": False,
        "real_tournament_authorized": False,
        "target_selection_authorized": False,
        "representation_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }
    assert out["claim_boundary"] == "STATIC_RELATIONAL_IDENTITY_ONLY__NO_R1_BIOLOGICAL_OUTCOME"
