import dataclasses, inspect
from pathlib import Path
import pytest
from sea_ad_jepa.v5.model_geometry_authority_v1 import ModelGeometryAuthorityV1

def make_authority():
    return ModelGeometryAuthorityV1('g','1'*64,'2'*64,'3'*64,'schema','4'*64,'5'*64)

def test_inputs_explicit():
    for name,param in inspect.signature(ModelGeometryAuthorityV1).parameters.items():
        if name!='training_authorized': assert param.default is inspect._empty

def test_geometry_authority_is_hash_bound_and_training_off():
    authority=make_authority(); authority.validate()
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64

def test_bad_geometry_root_fails_closed():
    authority=dataclasses.replace(make_authority(),geometry_artifact_sha256='bad')
    with pytest.raises(ValueError,match='geometry_artifact'): authority.validate()

def test_source_does_not_pick_historical_geometry_or_equate_rank_with_width():
    source=Path('src/sea_ad_jepa/v5/model_geometry_authority_v1.py').read_text(encoding='utf-8')
    forbidden=('160','heads = 4','blocks = 6','model_width = 512','D_shared == model_width')
    assert [token for token in forbidden if token in source] == []
