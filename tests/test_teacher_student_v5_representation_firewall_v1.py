import pytest
from sea_ad_jepa.v5.representation_firewall_v1 import RepresentationFirewallAuthorityV1,validate_routing_manifest

def good_manifest():
    return {"z_bio_direct_fields":["common_core_expression","common_core_detection"],"z_obs_direct_fields":["measurement_mask","depth","detected_genes","operator_support_state"],"common_core_anchor_present":True,"native_support_biology_route":"PREDICT_COMMON_CORE_ANCHORED_Z_BIO","same_cell_interventions":["SUPPORT_FAMILY","MASK_IDENTITY","EVIDENCE_FRACTION","MEASUREMENT_DEPTH"],"objective_inputs":{"BASE_JEPA_CELL_STATE":["z_bio"],"RELATIONAL_GEOMETRY":["z_bio"],"BIOLOGICAL_CHECKPOINT_SELECTION":["z_bio"],"DOWNSTREAM_BIOLOGY_READOUT":["z_bio"],"GENE_LEDGER_RECONSTRUCTION":["z_bio","z_obs"]}}

def test_good_firewall_passes(): assert validate_routing_manifest(good_manifest())["passed"]

def test_source_or_operator_direct_to_biology_is_rejected():
    m=good_manifest(); m["z_bio_direct_fields"]=["common_core_expression","source","operator_index"]
    with pytest.raises(ValueError,match="forbidden direct z_bio"): validate_routing_manifest(m)

def test_z_obs_cannot_enter_relational_biology_objective():
    m=good_manifest(); m["objective_inputs"]["RELATIONAL_GEOMETRY"]=["z_bio","z_obs"]
    with pytest.raises(ValueError,match="must consume z_bio only"): validate_routing_manifest(m)

def test_common_core_anchor_and_all_technical_interventions_are_required():
    m=good_manifest(); m["common_core_anchor_present"]=False
    with pytest.raises(ValueError,match="common-core"): validate_routing_manifest(m)
    m=good_manifest(); m["same_cell_interventions"].remove("MEASUREMENT_DEPTH")
    with pytest.raises(ValueError,match="missing same-cell"): validate_routing_manifest(m)

def test_authority_rejects_blind_source_adversary_and_pathology_training():
    good=dict(biological_state_id="BIO",observation_state_id="OBS",common_core_anchor_policy_id="CORE",same_cell_intervention_policy_id="PAIR",observation_descriptor_authority_id="OD",reconstruction_routing_policy_id="REC",relational_routing_policy_id="REL",source_adversary_is_default=False,pathology_used_for_training=False)
    RepresentationFirewallAuthorityV1(**good).validate()
    bad=dict(good); bad["source_adversary_is_default"]=True
    with pytest.raises(ValueError,match="not a default"): RepresentationFirewallAuthorityV1(**bad).validate()
    bad=dict(good); bad["pathology_used_for_training"]=True
    with pytest.raises(ValueError,match="cannot enter"): RepresentationFirewallAuthorityV1(**bad).validate()
