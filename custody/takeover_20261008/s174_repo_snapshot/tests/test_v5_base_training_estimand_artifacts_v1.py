import json
from dataclasses import fields
from pathlib import Path
from sea_ad_jepa.v5.base_training_estimand_authority_v1 import BaseTrainingEstimandAuthorityV1
from sea_ad_jepa.v5.base_training_estimand_recovery_v1 import RecoveredScientificWeightLawV1, validate_current_recovered_base_estimand_v1

LAW_SHA='0ddab1d6d88dfd671ce615c7b470a2ce0545c4f06fe2388f48499e6eb18aa774'
EST_SHA='a766d42f9f8e37aa63e6c694d6c65b30962e45568f41b1cde8199cbed118ce26'

def _load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def _kwargs(cls,payload): return {f.name:payload[f.name] for f in fields(cls)}

def test_frozen_weight_law_artifact_matches_current_validator_and_digest():
    p=_load('docs/agent/V5_RECOVERED_BASE_TRAINING_SCIENTIFIC_WEIGHT_LAW_20260915.json')
    assert p['schema']=='V5_RECOVERED_SCIENTIFIC_WEIGHT_LAW_V1'
    law=RecoveredScientificWeightLawV1(**_kwargs(RecoveredScientificWeightLawV1,p))
    law.validate_current_binding()
    assert law.canonical_digest()==LAW_SHA
    assert p['training_authorized'] is False

def test_frozen_base_estimand_artifact_matches_weight_law_and_digest():
    lp=_load('docs/agent/V5_RECOVERED_BASE_TRAINING_SCIENTIFIC_WEIGHT_LAW_20260915.json')
    ep=_load('docs/agent/V5_BASE_TRAINING_ESTIMAND_AUTHORITY_20260915.json')
    law=RecoveredScientificWeightLawV1(**_kwargs(RecoveredScientificWeightLawV1,lp))
    est=BaseTrainingEstimandAuthorityV1(**_kwargs(BaseTrainingEstimandAuthorityV1,ep))
    validate_current_recovered_base_estimand_v1(law,est)
    assert est.scientific_weight_artifact_sha256==LAW_SHA
    assert est.canonical_digest()==EST_SHA
    assert ep['training_authorized'] is False
