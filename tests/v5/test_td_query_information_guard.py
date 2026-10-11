import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_query_information_guard.py'
spec = importlib.util.spec_from_file_location('td_query_information_guard', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_q_address_is_allowed_for_student_conditioning():
    graph = {'student_head':['q_address','masked_rna'], 'q_address':[], 'masked_rna':[]}
    roles = {'student_head':'student_sink','q_address':'q_address','masked_rna':'lawful_evidence'}
    m.assert_query_safe(graph, roles)


def test_direct_q_scalar_student_leak_rejected():
    graph = {'student_head':['q_scalar'], 'q_scalar':[]}
    roles = {'student_head':'student_sink','q_scalar':'q_scalar'}
    with pytest.raises(m.QueryLeakageError): m.assert_query_safe(graph, roles)


def test_indirect_q_scalar_descendant_student_leak_rejected():
    graph = {'student_head':['qc_feature'], 'qc_feature':['library_norm'], 'library_norm':['q_scalar'], 'q_scalar':[]}
    roles = {'student_head':'student_sink','qc_feature':'lawful_evidence','library_norm':'derived','q_scalar':'q_scalar'}
    with pytest.raises(m.QueryLeakageError) as e: m.assert_query_safe(graph, roles)
    assert 'student_head' in str(e.value) and 'q_scalar' in str(e.value)


def test_q_bearing_target_normalization_rejected():
    graph = {'target_norm':['q_scalar','context_counts'], 'q_scalar':[], 'context_counts':[]}
    roles = {'target_norm':'target_normalization_sink','q_scalar':'q_scalar','context_counts':'teacher_non_q_evidence'}
    with pytest.raises(m.QueryLeakageError): m.assert_query_safe(graph, roles)


def test_teacher_q_visible_covariate_is_allowed_when_not_target_normalization():
    graph = {'teacher_aux':['q_scalar'], 'q_scalar':[]}
    roles = {'teacher_aux':'teacher_aux_sink','q_scalar':'q_scalar'}
    m.assert_query_safe(graph, roles)


def test_cycle_is_rejected():
    graph = {'student_head':['a'], 'a':['b'], 'b':['a']}
    roles = {'student_head':'student_sink','a':'derived','b':'derived'}
    with pytest.raises(m.DependencyCycleError): m.assert_query_safe(graph, roles)
