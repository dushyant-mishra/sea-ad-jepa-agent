"""Prospective observation-vs-biology routing contract for Teacher/Student V5.

Real reader-fit support fingerprints can identify source. A single unrestricted
cell state can therefore encode acquisition identity even without source/matrix/
donor IDs. This contract gives technical information an explicit observation
route and reserves biological objectives for z_bio.

No loss coefficient is selected and no training authority is created.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Sequence

FORBIDDEN_DIRECT_Z_BIO_FIELDS=frozenset({"donor_id","source","matrix_id","operator_index","support_fingerprint","pathology","protected_label","sealed_label"})
REQUIRED_TECHNICAL_INTERVENTIONS=frozenset({"SUPPORT_FAMILY","MASK_IDENTITY","EVIDENCE_FRACTION","MEASUREMENT_DEPTH"})
BIOLOGICAL_OBJECTIVES=frozenset({"BASE_JEPA_CELL_STATE","RELATIONAL_GEOMETRY","BIOLOGICAL_CHECKPOINT_SELECTION","DOWNSTREAM_BIOLOGY_READOUT"})

@dataclass(frozen=True)
class RepresentationFirewallAuthorityV1:
    biological_state_id:str
    observation_state_id:str
    common_core_anchor_policy_id:str
    same_cell_intervention_policy_id:str
    observation_descriptor_authority_id:str
    reconstruction_routing_policy_id:str
    relational_routing_policy_id:str
    source_adversary_is_default:bool
    pathology_used_for_training:bool
    def validate(self)->None:
        for name,value in self.__dict__.items():
            if name.endswith("_id") and (not isinstance(value,str) or not value):
                raise ValueError(f"{name} must be an explicit nonempty authority ID")
        if self.source_adversary_is_default is not False:
            raise ValueError("source-adversarial erasure is not a default: source can be confounded with legitimate biology")
        if self.pathology_used_for_training is not False:
            raise ValueError("pathology/protected outcomes cannot enter foundation training")

def validate_routing_manifest(manifest:Mapping[str,object])->dict[str,object]:
    z_bio_fields=manifest.get("z_bio_direct_fields"); z_obs_fields=manifest.get("z_obs_direct_fields")
    objectives=manifest.get("objective_inputs"); interventions=manifest.get("same_cell_interventions")
    if not isinstance(z_bio_fields,Sequence) or isinstance(z_bio_fields,(str,bytes)): raise ValueError("z_bio_direct_fields must be a sequence")
    if not isinstance(z_obs_fields,Sequence) or isinstance(z_obs_fields,(str,bytes)): raise ValueError("z_obs_direct_fields must be a sequence")
    if not isinstance(objectives,Mapping): raise ValueError("objective_inputs must be a mapping")
    if not isinstance(interventions,Sequence) or isinstance(interventions,(str,bytes)): raise ValueError("same_cell_interventions must be a sequence")
    bad=sorted(FORBIDDEN_DIRECT_Z_BIO_FIELDS & set(map(str,z_bio_fields)))
    if bad: raise ValueError(f"forbidden direct z_bio fields: {bad}")
    if manifest.get("common_core_anchor_present") is not True: raise ValueError("z_bio requires a common-core same-cell anchor")
    if manifest.get("native_support_biology_route")!="PREDICT_COMMON_CORE_ANCHORED_Z_BIO":
        raise ValueError("native support may enter biology only by predicting common-core-anchored z_bio")
    missing=sorted(REQUIRED_TECHNICAL_INTERVENTIONS-set(map(str,interventions)))
    if missing: raise ValueError(f"missing same-cell technical interventions: {missing}")
    for objective in BIOLOGICAL_OBJECTIVES:
        inputs=objectives.get(objective)
        if not isinstance(inputs,Sequence) or isinstance(inputs,(str,bytes)): raise ValueError(f"missing routing for biological objective {objective}")
        names=tuple(map(str,inputs))
        if names!=("z_bio",): raise ValueError(f"{objective} must consume z_bio only, got {names}")
    reconstruction=objectives.get("GENE_LEDGER_RECONSTRUCTION")
    if not isinstance(reconstruction,Sequence) or isinstance(reconstruction,(str,bytes)): raise ValueError("GENE_LEDGER_RECONSTRUCTION routing is required")
    recon=tuple(map(str,reconstruction))
    if "z_bio" not in recon or "z_obs" not in recon: raise ValueError("gene/ledger reconstruction must be allowed to use both z_bio and z_obs")
    return {"passed":True,"forbidden_direct_z_bio_fields":sorted(FORBIDDEN_DIRECT_Z_BIO_FIELDS),"required_same_cell_interventions":sorted(REQUIRED_TECHNICAL_INTERVENTIONS),"biological_objectives_z_bio_only":sorted(BIOLOGICAL_OBJECTIVES)}
