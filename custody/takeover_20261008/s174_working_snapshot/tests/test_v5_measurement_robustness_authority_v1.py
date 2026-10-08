import dataclasses
import inspect
from pathlib import Path
import pytest
from sea_ad_jepa.v5.measurement_robustness_authority_v1 import MeasurementRobustnessDecisionAuthorityV1

def make_authority():
    return MeasurementRobustnessDecisionAuthorityV1('a','1'*64,'2'*64,'3'*64,'metric',1,100,'4'*64,'fail')

def test_inputs_explicit():
    for name,param in inspect.signature(MeasurementRobustnessDecisionAuthorityV1).parameters.items():
        if name != 'training_authorized': assert param.default is inspect._empty

def test_authority_binds_rule_without_training():
    authority=make_authority(); authority.validate()
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64

def test_bad_margin_fails_closed():
    authority=dataclasses.replace(make_authority(),acceptance_margin_numerator=2,acceptance_margin_denominator=1)
    with pytest.raises(ValueError,match='acceptance_margin'): authority.validate()

def test_source_does_not_import_historical_thinning_ladder_or_margin():
    source=Path('src/sea_ad_jepa/v5/measurement_robustness_authority_v1.py').read_text(encoding='utf-8')
    assert [token for token in ('0.90','0.75','0.50','0.25','0.05') if token in source] == []
