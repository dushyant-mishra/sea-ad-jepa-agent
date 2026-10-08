import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_v72_g2_process_selects_no_posthoc_threshold():
    p=ROOT/'results/v64/V72_STAGE4_G2_SPECIFICATION_PROCESS_V1.json'
    d=json.loads(p.read_text())
    assert d['status']=='PROSPECTIVE_PROCESS_ONLY__NO_G2_THRESHOLD_SELECTED'
    assert d['governance']['no_posthoc_margin'] is True
    assert 'V2 BIOLOGY_POSITIVE G2 pass rates' in d['forbidden_sources_for_margin_selection']
    assert all(x['status']=='CANDIDATE_NOT_SELECTED' for x in d['candidate_semantics'])

def test_v72_synthetic_successor_carries_s102_as_open_variable():
    d=json.loads((ROOT/'results/v64/V72_SYNTHETIC_ECOSYSTEM_SUCCESSOR_CONTRACT_V1.json').read_text())
    g2=d['stage4_successor_requirements']['G2_S102']
    assert g2['status']=='OPEN_SPECIFICATION_VARIABLE'
    assert 'must not silently freeze' in g2['forbidden']

def test_v72_blacklist_amendment_is_grch38_and_pinned_before_result():
    d=json.loads((ROOT/'results/v64/V72_ROUTEB_BLACKLIST_PROSPECTIVE_AMENDMENT_V1.json').read_text())
    assert d['status']=='PROSPECTIVE_AMENDMENT__BEFORE_REAL_ROUTEB_CONSENSUS_RESULT'
    assert d['decision']=='APPLY_ENCODE_GRCH38_UNIFIED_BLACKLIST'
    assert d['resource']['accession']=='ENCFF356LFX'
    assert d['resource']['assembly']=='GRCh38'
    assert d['resource']['md5sum']=='393688b4f06c9ce26165d47433dd8c37'

def test_successor_dockerfile_has_no_default_master_for_cistarget():
    s=(ROOT/'docker/scenicplus/Dockerfile.successor_pinned').read_text()
    assert 'ARG CREATE_CISTARGET_DATABASES_COMMIT' in s
    assert 'CREATE_CISTARGET_DATABASES_REF=master' not in s
    assert 'test -n "${CREATE_CISTARGET_DATABASES_COMMIT}"' in s
    assert 'git -C /opt/create_cisTarget_databases checkout --detach' in s

def test_successor_dockerfile_requires_downloaded_tool_digests():
    s=(ROOT/'docker/scenicplus/Dockerfile.successor_pinned').read_text()
    for key in ('CBUST_SHA256','LIFTOVER_SHA256','BIGWIG_AVERAGE_OVER_BED_SHA256'):
        assert f'ARG {key}' in s
        assert ('test -n "${' + key + '}"') in s
