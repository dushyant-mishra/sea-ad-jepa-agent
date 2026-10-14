import pathlib, sys
import pytest
ROOT=pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from scripts.v5 import td_real_transfer_coverage_contract_v2 as T
CANDS=("C1_SHARED_EMERGENT","C2_RELATIONAL_SHARED","C3_QUERY_MEASURED","C6_SHARED_QUERY_COMPOSITE","C4_STRUCTURED_COMPOSITE","C5_REGULATORY_SPECIALIST")

def registry():
    claims={c:["DONOR","SOURCE","OPERATOR_MATRIX","STUDY_FAMILY","TECHNOLOGY"] for c in CANDS}
    def states():
        x={c:"SUPPORTED" for c in CANDS}; x["C5_REGULATORY_SPECIALIST"]="UNSUPPORTED_STRUCTURAL"; return x
    rows=[
      {"stratum_id":"fit_hvs_d1_op1","donor_id":"D1","source":"HVS","operator_matrix":"OP1","study_family":"HVS","technology":"snRNA-seq","reader_partition":"reader_fit","candidate_support_state":states()},
      {"stratum_id":"eval_sea_d2_op2","donor_id":"D2","source":"SEA_AD","operator_matrix":"OP2","study_family":"SEA_AD","technology":"snRNA-seq","reader_partition":"reader_validation","candidate_support_state":states()},
      {"stratum_id":"oracle_nph_d3_op3","donor_id":"D3","source":"NPH52","operator_matrix":"OP3","study_family":"NPH52","technology":"snRNA-seq","reader_partition":"reader_oracle","candidate_support_state":states()},
    ]
    return {"schema":"JEPA_TD_REAL_STATIC_POPULATION_SUPPORT_REGISTRY_V2","frozen":True,"candidate_transfer_claims":claims,"strata":rows}

def test_partition_is_required_and_bound():
    r=registry(); del r['strata'][0]['reader_partition']
    with pytest.raises(T.StaticContractError,match='missing stratum fields'): T.derive_static_contract(r)

def test_donor_cannot_cross_reader_partitions():
    r=registry(); r['strata'][1]['donor_id']='D1'
    with pytest.raises(T.StaticContractError,match='multiple reader partitions'): T.derive_static_contract(r)

def test_donor_transfer_requires_fit_and_heldout_support():
    out=T.derive_static_contract(registry()); assert out['transfer_applicability']['C1_SHARED_EMERGENT']['DONOR']=='REQUIRED'
    r=registry()
    for row in r['strata']: row['reader_partition']='reader_fit'
    out=T.derive_static_contract(r); assert out['transfer_applicability']['C1_SHARED_EMERGENT']['DONOR']=='BLOCKED_DEPENDENCY'

def test_single_technology_is_blocked_not_passed():
    assert T.derive_static_contract(registry())['transfer_applicability']['C1_SHARED_EMERGENT']['TECHNOLOGY']=='BLOCKED_DEPENDENCY'

def test_zero_support_candidate_is_not_estimable_and_has_no_envelope():
    out=T.derive_static_contract(registry()); assert out['mandatory_claim_envelopes']['C5_REGULATORY_SPECIALIST']==[]
    assert out['claim_envelope_status']['C5_REGULATORY_SPECIALIST']=='NO_SUPPORTED_STRATA__NOT_ESTIMABLE'

def test_partition_summary_is_emitted_without_authority():
    out=T.derive_static_contract(registry()); assert out['supported_partition_counts']['C1_SHARED_EMERGENT']=={'reader_fit':1,'reader_validation':1,'reader_oracle':1}
    assert all(v is False for v in out['authority'].values())

def test_blocked_candidate_evidence_contract_blocks_claim_envelope_and_transfer():
    r=registry()
    for row in r['strata']: row['candidate_support_state']['C3_QUERY_MEASURED']='BLOCKED_EVIDENCE_CONTRACT'
    out=T.derive_static_contract(r)
    assert out['claim_envelope_status']['C3_QUERY_MEASURED']=='SUPPORT_REGISTRY_INCOMPLETE__NOT_ESTIMABLE'
    assert set(out['transfer_applicability']['C3_QUERY_MEASURED'].values())=={'BLOCKED_DEPENDENCY'}

def test_structurally_unsupported_specialist_is_distinct_from_blocked_evidence():
    out=T.derive_static_contract(registry())
    assert out['candidate_support_state_counts']['C5_REGULATORY_SPECIALIST']['UNSUPPORTED_STRUCTURAL']==3

def test_old_boolean_support_field_is_rejected():
    r=registry(); r['strata'][0]['candidate_support']={c:True for c in CANDS}; del r['strata'][0]['candidate_support_state']
    with pytest.raises(T.StaticContractError): T.derive_static_contract(r)
