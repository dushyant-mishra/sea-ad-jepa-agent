from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_candidate_is_fail_closed_on_cuda_and_independent_verification():
    x=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_V1.json').read_text())
    assert x['status']=='IMPLEMENTATION_COMPLETE_AWAITING_INDEPENDENT_VERIFICATION_AND_CUDA_QUALIFICATION'
    assert x['cuda_qualification']['qualified'] is False
    assert x['cuda_qualification']['evidence'] is None
    assert x['implementation_verifier']['terminal'] is None
    assert x['implementation_verifier']['status']=='PENDING_INDEPENDENT_IMPLEMENTATION_VERIFIER'
    assert x['training_authorized'] is False and x['execution_authorized'] is False
    assert not any(x['authority_effect'][k] for k in ('changes_frozen_rng_contract','changes_scientific_target','changes_base_proposal_v3','changes_presentation_horizon_v1','changes_evidence_schedule','authorizes_training','authorizes_execution','authorizes_successor_u0','authorizes_td60'))

def test_candidate_binds_exact_frozen_rng_contract_and_prototype_root():
    import hashlib
    x=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_V1.json').read_text())
    p=ROOT/x['frozen_v5_prototype']['rng_contract_v2_path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==x['frozen_v5_prototype']['rng_contract_v2_sha256']=='7e8dcf488c80b4fd9b31f2dce23c6395eeebff244016d78066f4da81e91b06f1'
    assert (ROOT/'docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_PROTOTYPE_ROOT.txt').read_text().strip()==x['frozen_v5_prototype']['prototype_root']=='9684f4c2b7eff1da863ae50124c6aad49d25f137a84898e05e98d2ae1f0c67ad'

def test_candidate_test_selection_is_explicit_and_unique():
    rows=[x.strip() for x in (ROOT/'docs/agent/TEACHER_STUDENT_V5_GPU_RNG_CANDIDATE_TEST_SELECTION.txt').read_text().splitlines() if x.strip()]
    assert len(rows)==6 and len(set(rows))==6
    for row in rows: assert (ROOT/row).is_file(),row
