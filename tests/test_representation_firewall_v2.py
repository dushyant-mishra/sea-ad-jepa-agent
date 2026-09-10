import pytest

from sea_ad_jepa.v5.representation_firewall_v2 import (
    RepresentationFirewallAuthorityV2,
    validate_routing_manifest_v2,
)


def good_manifest():
    return {
        "z_bio_direct_fields": ["common_core_expression", "common_core_detection"],
        "z_obs_direct_fields": [
            "measurement_mask",
            "depth",
            "detected_genes",
            "operator_support_state",
        ],
        "common_core_anchor_present": True,
        "native_support_biology_route": "PREDICT_COMMON_CORE_ANCHORED_Z_BIO",
        "observation_gradient_into_biology_allowed": False,
        "categorical_identity_embeddings_allowed": False,
        "same_cell_interventions": [
            "SUPPORT_FAMILY",
            "MASK_IDENTITY",
            "EVIDENCE_FRACTION",
            "MEASUREMENT_DEPTH",
        ],
        "objective_inputs": {
            "BASE_JEPA_CELL_STATE": ["z_bio"],
            "RELATIONAL_GEOMETRY": ["z_bio"],
            "BIOLOGICAL_CHECKPOINT_SELECTION": ["z_bio"],
            "DOWNSTREAM_BIOLOGY_READOUT": ["z_bio"],
            "GENE_LEDGER_RECONSTRUCTION": ["z_bio", "z_obs"],
        },
        "objective_gradient_targets": {
            "BASE_JEPA_CELL_STATE": ["z_bio"],
            "RELATIONAL_GEOMETRY": ["z_bio"],
            "BIOLOGICAL_CHECKPOINT_SELECTION": [],
            "DOWNSTREAM_BIOLOGY_READOUT": [],
            "GENE_LEDGER_RECONSTRUCTION": ["z_obs"],
        },
    }


def test_good_v2_firewall_passes():
    out = validate_routing_manifest_v2(good_manifest())
    assert out["passed"] is True
    assert out["training_authorized"] is False


@pytest.mark.parametrize(
    "alias",
    [
        "dataset_id",
        "study_id",
        "batch_id",
        "operator_id",
        "stable_key",
        "cell_id",
        "sample_row",
        "pathology",
    ],
)
def test_identity_and_protected_aliases_cannot_enter_z_bio(alias):
    m = good_manifest()
    m["z_bio_direct_fields"] = ["common_core_expression", alias]
    with pytest.raises(ValueError, match="forbidden direct model fields"):
        validate_routing_manifest_v2(m)


@pytest.mark.parametrize(
    "alias",
    ["donor_id", "matrix_id", "dataset_id", "stable_key", "protected_label"],
)
def test_identity_and_protected_aliases_cannot_hide_in_z_obs(alias):
    m = good_manifest()
    m["z_obs_direct_fields"] = ["measurement_mask", alias]
    with pytest.raises(ValueError, match="forbidden direct model fields"):
        validate_routing_manifest_v2(m)


def test_unknown_direct_descriptor_fails_closed_until_authorized():
    m = good_manifest()
    m["z_obs_direct_fields"].append("free_dataset_embedding")
    with pytest.raises(ValueError, match="unregistered direct fields"):
        validate_routing_manifest_v2(m)


def test_unregistered_auxiliary_objective_cannot_bypass_routing():
    m = good_manifest()
    m["objective_inputs"]["BIOLOGY_AUXILIARY"] = ["z_obs"]
    with pytest.raises(ValueError, match="unregistered objectives"):
        validate_routing_manifest_v2(m)


def test_reconstruction_cannot_add_a_side_channel():
    m = good_manifest()
    m["objective_inputs"]["GENE_LEDGER_RECONSTRUCTION"] = [
        "z_bio",
        "z_obs",
        "dataset_id",
    ]
    with pytest.raises(ValueError, match="exactly"):
        validate_routing_manifest_v2(m)


def test_unknown_same_cell_intervention_fails_closed():
    m = good_manifest()
    m["same_cell_interventions"].append("DATASET_ID_SWAP")
    with pytest.raises(ValueError, match="unregistered same-cell"):
        validate_routing_manifest_v2(m)


def test_observation_gradient_and_categorical_identity_flags_must_be_false():
    m = good_manifest()
    m["observation_gradient_into_biology_allowed"] = True
    with pytest.raises(ValueError, match="must not be allowed"):
        validate_routing_manifest_v2(m)
    m = good_manifest()
    m["categorical_identity_embeddings_allowed"] = True
    with pytest.raises(ValueError, match="must be explicitly disabled"):
        validate_routing_manifest_v2(m)


def test_reconstruction_cannot_write_gradient_into_z_bio():
    m = good_manifest()
    m["objective_gradient_targets"]["GENE_LEDGER_RECONSTRUCTION"] = ["z_bio", "z_obs"]
    with pytest.raises(ValueError, match="gradient targets must be exactly"):
        validate_routing_manifest_v2(m)


def test_evaluation_readouts_cannot_become_training_losses():
    for name in ("BIOLOGICAL_CHECKPOINT_SELECTION", "DOWNSTREAM_BIOLOGY_READOUT"):
        m = good_manifest()
        m["objective_gradient_targets"][name] = ["z_bio"]
        with pytest.raises(ValueError, match="gradient targets must be exactly"):
            validate_routing_manifest_v2(m)


def test_missing_or_unknown_gradient_route_fails_closed():
    m = good_manifest()
    del m["objective_gradient_targets"]["RELATIONAL_GEOMETRY"]
    with pytest.raises(ValueError, match="missing objective gradient routes"):
        validate_routing_manifest_v2(m)
    m = good_manifest()
    m["objective_gradient_targets"]["AUX"] = []
    with pytest.raises(ValueError, match="unregistered objective gradient routes"):
        validate_routing_manifest_v2(m)


def test_v2_authority_rejects_identity_embeddings_source_adversary_and_pathology():
    good = dict(
        biological_state_id="BIO",
        observation_state_id="OBS",
        common_core_anchor_policy_id="CORE",
        same_cell_intervention_policy_id="PAIR",
        observation_descriptor_authority_id="OD",
        reconstruction_routing_policy_id="REC",
        relational_routing_policy_id="REL",
        observation_gradient_firewall_policy_id="STOP_GRAD_OBS_TO_BIO",
        categorical_identity_embeddings_allowed=False,
        source_adversary_is_default=False,
        pathology_used_for_training=False,
    )
    RepresentationFirewallAuthorityV2(**good).validate()
    for field in (
        "categorical_identity_embeddings_allowed",
        "source_adversary_is_default",
        "pathology_used_for_training",
    ):
        bad = dict(good)
        bad[field] = True
        with pytest.raises(ValueError):
            RepresentationFirewallAuthorityV2(**bad).validate()
