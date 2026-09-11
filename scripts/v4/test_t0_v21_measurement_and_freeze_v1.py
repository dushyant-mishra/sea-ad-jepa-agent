import copy,sys
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import t0_v21_measurement_artifact_v1 as m
import t0_v21_target_freeze_v1 as f
H={k:(hex(i+10)[2:]*64)[:64] for i,k in enumerate(m.REQ_ROOTS)}
def candidate_table():return {c:{"definition_digest":("a"+str(i))*32,"worst_standardized_displacement":.1+i/100,"selection_eligible":True} for i,c in enumerate(m.CANDIDATES)}
def ridge():return {c:{x:{"lodo_envelope":.2,"induced_displacement":.1} for x in m.RIDGE_METRICS} for c in m.CANDIDATES}
def test_measurement_requires_exact_s0_s4_and_all_ridge_views():
 t=candidate_table();del t["S4"]
 with pytest.raises(RuntimeError,match="exactly S0-S4"):m.seal_measurement_artifact(source_roots=H,candidate_table=t,thinning_draws=[{"retention":.5,"draw_index":0,"draw_digest":"b"*64}],biology_preservation={c:{} for c in m.CANDIDATES},ridge_stability=ridge())
 r=ridge();del r["S0"]["beta_direction"]
 with pytest.raises(RuntimeError,match="ridge stability"):m.seal_measurement_artifact(source_roots=H,candidate_table=candidate_table(),thinning_draws=[{"retention":.5,"draw_index":0,"draw_digest":"b"*64}],biology_preservation={c:{} for c in m.CANDIDATES},ridge_stability=r)
def test_measurement_tamper_and_external_root_mismatch_fail():
 a=m.seal_measurement_artifact(source_roots=H,candidate_table=candidate_table(),thinning_draws=[{"retention":.5,"draw_index":0,"draw_digest":"b"*64}],biology_preservation={c:{"within_envelope":True} for c in m.CANDIDATES},ridge_stability=ridge())
 b=copy.deepcopy(a);b["candidate_table"]["S2"]["selection_eligible"]=False
 with pytest.raises(RuntimeError,match="digest"):m.validate_measurement_artifact(b,expected_source_roots=H)
 x=dict(H);x["expression_root_digest"]="f"*64
 with pytest.raises(RuntimeError,match="external expected"):m.validate_measurement_artifact(a,expected_source_roots=x)
def bindings():return {k:(str((i%9)+1)*64) for i,k in enumerate(f.DIGEST_FIELDS)}
def test_28_donor_receipt_cannot_masquerade_as_46():
 with pytest.raises(RuntimeError,match="46 unique"):f.seal_target_freeze_receipt(development_donor_ids=[f"D{i}" for i in range(28)],protected_donor_ids=[],estimator_id="S2",ridge_exponent=-4,bindings=bindings(),qualification_receipt_digests=["a"*64,"b"*64])
def test_protected_donor_cannot_enter_46_refit_and_tamper_fails():
 ids=[f"D{i}" for i in range(46)]
 with pytest.raises(RuntimeError,match="protected donor"):f.seal_target_freeze_receipt(development_donor_ids=ids,protected_donor_ids=["D45"],estimator_id="S2",ridge_exponent=-4,bindings=bindings(),qualification_receipt_digests=["a"*64,"b"*64])
 r=f.seal_target_freeze_receipt(development_donor_ids=ids,protected_donor_ids=["R1"],estimator_id="S2",ridge_exponent=-4,bindings=bindings(),qualification_receipt_digests=["a"*64,"b"*64])
 r["bindings"]["expression_root_digest"]="f"*64
 with pytest.raises(RuntimeError,match="package root"):f.validate_target_freeze_receipt(r,expected_role_ledger_digest=bindings()["role_ledger_digest"],expected_expression_root_digest=bindings()["expression_root_digest"])
