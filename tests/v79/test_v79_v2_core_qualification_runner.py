from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import run_v79_v2_core_qualification as Q  # noqa: E402

CODE="a"*40
SEED=123456


def _queue():
    rows=[]
    for wi,oid in enumerate(("000000000001","000000000002")):
        for g in range(2):
            for part in ("detection","positive"):
                rows.append({"opaque_world_id":oid,"world_manifest_sha256":f"{wi+1:064x}","gene_index":g,"part":part,"fit_id":f"{len(rows)+1:064x}"})
    return rows


def _seed_map(q): return {x["fit_id"]:SEED for x in q}


def _qs(labels):
    n=len(labels)
    return {"labels":list(labels),"mean":[0.0]*n,"sd":[1.0]*n,
            "q005":[-2.5]*n,"q025":[-2.0]*n,"q05":[-1.0]*n,"q50":[0.0]*n,
            "q95":[1.0]*n,"q975":[2.0]*n,"q995":[2.5]*n}


def _calibration():
    return [{"bin_index":i,"lower":i/10,"upper":(i+1)/10,"n":1 if i==5 else 0,
             "mean_predicted":0.5 if i==5 else None,"observed_rate":1.0 if i==5 else None} for i in range(10)]


def _heldout(part):
    if part=="detection":
        same={"schema":"V79_V2_CORE_DETECTION_HELDOUT_V1","replicate_mode":"same_donor","posterior_draws":200,
              "gauss_hermite_nodes":None,"n_measured":1,"mean_log_loss":0.693,"predicted_prevalence":0.5,
              "observed_prevalence":1.0,"calibration_bins":_calibration()}
        new=dict(same); new["replicate_mode"]="new_donor"; new["gauss_hermite_nodes"]=40
    else:
        same={"schema":"V79_V2_CORE_POSITIVE_HELDOUT_V1","replicate_mode":"same_donor","posterior_draws":200,
              "gauss_hermite_nodes":None,"n_positive":1,"mean_lpd":-0.919}
        new=dict(same); new["replicate_mode"]="new_donor"; new["gauss_hermite_nodes"]=40
    return {"same_donor":same,"new_donor":new}


def _receipt(item):
    quantities={"intercept":_qs(["intercept"]),"depth1":_qs(["depth1"]),"depth2":_qs(["depth2"]),
                "class":_qs(["helmert_0","helmert_1"]),"source":_qs(["helmert_0","helmert_1"]),
                "donor_sd":_qs(["donor_sd"]),"donor_effects":_qs(["donor_0"])}
    if item["part"]=="positive": quantities["sigma"]=_qs(["sigma"])
    attempt={"stage":"PRIMARY","seed":SEED,"chains":4,"warmup":1000,"draws_per_chain":1000,"target_accept":0.9,
             "max_tree_depth":10,"extended":False,"dense_mass":False,"init":"uniform_radius_2","divergences":0,
             "worst_rhat":1.0,"worst_ess_bulk":800,"worst_ess_tail":800,"mean_tree_steps":10.0,
             "started_at_utc":"2026-10-12T00:00:00+00:00","ended_at_utc":"2026-10-12T00:01:00+00:00",
             "wall_seconds":60.0,"process_cpu_seconds":200.0,"peak_working_set_bytes":1000,"jax_devices":["TFRT_CPU_0"]}
    return {"schema":"V79_V2_CORE_FIT_RECORD_V1","execution_mode":"QUALIFICATION","fit_id":item["fit_id"],
            "opaque_world_id":item["opaque_world_id"],"gene_index":item["gene_index"],"part":item["part"],
            "input_manifest_sha256":item["world_manifest_sha256"],"contract_sha256":Q.SOURCE_CONTRACT_SHA256,
            "qualification_fits_run":1,"benchmark_run":False,"scoring_run":False,"truth_accessed":False,
            "training_authorized":False,"final_diagnosis":"COMPLETE","attempts":[attempt],"code_sha":CODE,
            "final_diagnostics":{"divergences":0,"worst_rhat":1.0,"worst_ess_bulk":800,"worst_ess_tail":800,"mean_tree_steps":10.0},
            "scoring_summary":{"schema":"V79_V2_CORE_IDENTIFIED_POSTERIOR_SUMMARY_V1","part":item["part"],
                "identification":{"class":{"mode":"helmert","observed_levels":[0,1,2],"reference_level":None},
                                  "source":{"mode":"helmert","observed_levels":[0,1,2],"reference_level":None},"donor_codes":[0]},
                "quantities":quantities},
            "ppc":[{"name":"fixture_stat","observed":0.5,"p_value":0.5}],
            "heldout_predictive":_heldout(item["part"]),"posterior_artifacts":{}}


def _write_receipt(path:Path,receipt:dict,*,with_artifact:bool=True)->None:
    r=json.loads(json.dumps(receipt))
    if with_artifact:
        raw=("artifact:"+str(r["fit_id"])).encode("ascii"); name=f"donor_effect_draws_{r['fit_id']}.npz"
        (path.parent/name).write_bytes(raw)
        r["posterior_artifacts"]={"donor_effect_draws":{"path":name,"sha256":hashlib.sha256(raw).hexdigest()}}
    path.write_bytes((json.dumps(r,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8"))


def test_world_groups_preserve_opaque_order_and_det_then_pos_per_gene():
    groups=Q.group_queue_by_world(_queue())
    assert [g[0] for g in groups]==["000000000001","000000000002"]
    assert [(x["gene_index"],x["part"]) for x in groups[0][1]]==[(0,"detection"),(0,"positive"),(1,"detection"),(1,"positive")]


def test_checkpoint_scan_accepts_exact_prefix_only(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir()
    for item in q[:3]: _write_receipt(out/f"fit_{item['fit_id']}.json",_receipt(item))
    assert Q.completed_prefix(out,q,expected_code_sha=CODE,seed_by_fit_id=_seed_map(q))==3
    _write_receipt(out/f"fit_{q[4]['fit_id']}.json",_receipt(q[4]))
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q,expected_code_sha=CODE,seed_by_fit_id=_seed_map(q))


def test_checkpoint_scan_refuses_tampered_existing_receipt(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); r=_receipt(q[0]); r["opaque_world_id"]="ffffffffffff"
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q,expected_code_sha=CODE,seed_by_fit_id=_seed_map(q))


def test_checkpoint_refuses_wrong_code_or_seed(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); r=_receipt(q[0]); r["code_sha"]="b"*40
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q,expected_code_sha=CODE,seed_by_fit_id=_seed_map(q))
    for p in out.iterdir(): p.unlink()
    r=_receipt(q[0]); r["attempts"][0]["seed"]=SEED+1
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q,expected_code_sha=CODE,seed_by_fit_id=_seed_map(q))


def test_checkpoint_refuses_missing_gate_ready_output(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); r=_receipt(q[0]); r.pop("scoring_summary")
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q,expected_code_sha=CODE,seed_by_fit_id=_seed_map(q))


def test_checkpoint_refuses_missing_95_or_99_interval(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); r=_receipt(q[0]); r["scoring_summary"]["quantities"]["intercept"].pop("q995")
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q,expected_code_sha=CODE,seed_by_fit_id=_seed_map(q))


def test_checkpoint_artifact_path_cannot_escape_result_root(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); escape=tmp_path/"escape.npz"; escape.write_bytes(b"x")
    r=_receipt(q[0]); r["posterior_artifacts"]={"donor_effect_draws":{"path":"../escape.npz","sha256":hashlib.sha256(b"x").hexdigest()}}
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r,with_artifact=False)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q,expected_code_sha=CODE,seed_by_fit_id=_seed_map(q))


def test_campaign_summary_keeps_scoring_and_truth_off():
    r=Q.campaign_receipt_skeleton(code_sha=CODE,custody_receipt_sha="b"*64,fit_count=1056)
    assert r["qualification_fits_run"]==0
    assert r["scoring_run"] is False and r["truth_accessed"] is False and r["training_authorized"] is False


def test_campaign_finalization_is_idempotent_after_all_fit_receipts_exist(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir()
    for item in q: _write_receipt(out/f"fit_{item['fit_id']}.json",_receipt(item))
    seeds=_seed_map(q)
    a=Q.finalize_campaign(out,q,code_sha=CODE,custody_receipt_sha="b"*64,seed_by_fit_id=seeds)
    b=Q.finalize_campaign(out,q,code_sha=CODE,custody_receipt_sha="b"*64,seed_by_fit_id=seeds)
    assert a==b and a["qualification_fits_run"]==len(q)


def test_qualification_processes_import_no_controller_or_scoring_modules():
    forbidden={"generate_v79_v2_core_worlds","v79_v2_core_world_writer","v79_v2_core_launch","v79_v2_core_score"}
    for name in ("run_v79_v2_core_qualification.py","run_v79_v2_core_qualification_world.py"):
        tree=ast.parse((HERE/name).read_text(encoding="utf-8")); imported=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imported.update(alias.name for alias in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module: imported.add(node.module)
        assert not (imported & forbidden)
