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


def _queue():
    rows=[]
    for wi,oid in enumerate(("000000000001","000000000002")):
        for g in range(2):
            for part in ("detection","positive"):
                rows.append({"opaque_world_id":oid,"world_manifest_sha256":f"{wi+1:064x}","gene_index":g,"part":part,"fit_id":f"{len(rows)+1:064x}"})
    return rows


def _qs(labels):
    n=len(labels); return {"labels":list(labels),"mean":[0.0]*n,"sd":[1.0]*n,"q05":[-1.0]*n,"q50":[0.0]*n,"q95":[1.0]*n}


def _receipt(item):
    quantities={"intercept":_qs(["intercept"]),"depth1":_qs(["depth1"]),"depth2":_qs(["depth2"]),
                "class":_qs(["helmert_0","helmert_1"]),"source":_qs(["helmert_0","helmert_1"]),
                "donor_sd":_qs(["donor_sd"]),"donor_effects":_qs(["donor_0"])}
    if item["part"]=="positive": quantities["sigma"]=_qs(["sigma"])
    return {"schema":"V79_V2_CORE_FIT_RECORD_V1","execution_mode":"QUALIFICATION","fit_id":item["fit_id"],
            "opaque_world_id":item["opaque_world_id"],"gene_index":item["gene_index"],"part":item["part"],
            "input_manifest_sha256":item["world_manifest_sha256"],"contract_sha256":Q.SOURCE_CONTRACT_SHA256,
            "qualification_fits_run":1,"benchmark_run":False,"scoring_run":False,"truth_accessed":False,
            "training_authorized":False,"final_diagnosis":"COMPLETE","attempts":[],"code_sha":"a"*40,
            "final_diagnostics":{"divergences":0,"worst_rhat":1.0,"worst_ess_bulk":800,"worst_ess_tail":800,"mean_tree_steps":10.0},
            "scoring_summary":{"schema":"V79_V2_CORE_IDENTIFIED_POSTERIOR_SUMMARY_V1","part":item["part"],
                "identification":{"class":{"mode":"helmert","observed_levels":[0,1,2],"reference_level":None},
                                  "source":{"mode":"helmert","observed_levels":[0,1,2],"reference_level":None},"donor_codes":[0]},
                "quantities":quantities},
            "ppc":[{"name":"fixture_stat","observed":0.5,"p_value":0.5}],"posterior_artifacts":{}}


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
    assert Q.completed_prefix(out,q)==3
    _write_receipt(out/f"fit_{q[4]['fit_id']}.json",_receipt(q[4]))
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q)


def test_checkpoint_scan_refuses_tampered_existing_receipt(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); r=_receipt(q[0]); r["opaque_world_id"]="ffffffffffff"
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q)


def test_checkpoint_refuses_missing_gate_ready_output(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); r=_receipt(q[0]); r.pop("scoring_summary")
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q)


def test_checkpoint_artifact_path_cannot_escape_result_root(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); escape=tmp_path/"escape.npz"; escape.write_bytes(b"x")
    r=_receipt(q[0]); r["posterior_artifacts"]={"donor_effect_draws":{"path":"../escape.npz","sha256":hashlib.sha256(b"x").hexdigest()}}
    _write_receipt(out/f"fit_{q[0]['fit_id']}.json",r,with_artifact=False)
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q)


def test_campaign_summary_keeps_scoring_and_truth_off():
    r=Q.campaign_receipt_skeleton(code_sha="a"*40,custody_receipt_sha="b"*64,fit_count=1056)
    assert r["qualification_fits_run"]==0
    assert r["scoring_run"] is False and r["truth_accessed"] is False and r["training_authorized"] is False


def test_campaign_finalization_is_idempotent_after_all_fit_receipts_exist(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir()
    for item in q: _write_receipt(out/f"fit_{item['fit_id']}.json",_receipt(item))
    a=Q.finalize_campaign(out,q,code_sha="a"*40,custody_receipt_sha="b"*64)
    b=Q.finalize_campaign(out,q,code_sha="a"*40,custody_receipt_sha="b"*64)
    assert a==b and a["qualification_fits_run"]==len(q)


def test_qualification_processes_import_no_controller_or_scoring_modules():
    forbidden={"generate_v79_v2_core_worlds","v79_v2_core_world_writer","v79_v2_core_launch","v79_v2_core_score"}
    for name in ("run_v79_v2_core_qualification.py","run_v79_v2_core_qualification_world.py"):
        tree=ast.parse((HERE/name).read_text(encoding="utf-8")); imported=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imported.update(alias.name for alias in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module: imported.add(node.module)
        assert not (imported & forbidden)
