from __future__ import annotations

import ast
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


def _receipt(item):
    return {"schema":"V79_V2_CORE_FIT_RECORD_V1","execution_mode":"QUALIFICATION","fit_id":item["fit_id"],
            "opaque_world_id":item["opaque_world_id"],"gene_index":item["gene_index"],"part":item["part"],
            "input_manifest_sha256":item["world_manifest_sha256"],"contract_sha256":Q.SOURCE_CONTRACT_SHA256,
            "qualification_fits_run":1,"benchmark_run":False,"scoring_run":False,"truth_accessed":False,
            "training_authorized":False,"final_diagnosis":"COMPLETE","attempts":[],"posterior_artifacts":{},"code_sha":"a"*40}


def test_world_groups_preserve_opaque_order_and_det_then_pos_per_gene():
    groups=Q.group_queue_by_world(_queue())
    assert [g[0] for g in groups]==["000000000001","000000000002"]
    assert [(x["gene_index"],x["part"]) for x in groups[0][1]]==[(0,"detection"),(0,"positive"),(1,"detection"),(1,"positive")]


def test_checkpoint_scan_accepts_exact_prefix_only(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir()
    for item in q[:3]:
        (out/f"fit_{item['fit_id']}.json").write_text(json.dumps(_receipt(item),sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    assert Q.completed_prefix(out,q)==3
    (out/f"fit_{q[4]['fit_id']}.json").write_text(json.dumps(_receipt(q[4]),sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    with pytest.raises(Q.QualificationRunRefused):
        Q.completed_prefix(out,q)


def test_checkpoint_scan_refuses_tampered_existing_receipt(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir()
    r=_receipt(q[0]); r["opaque_world_id"]="ffffffffffff"
    (out/f"fit_{q[0]['fit_id']}.json").write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    with pytest.raises(Q.QualificationRunRefused):
        Q.completed_prefix(out,q)


def test_checkpoint_artifact_path_cannot_escape_result_root(tmp_path):
    q=_queue(); out=tmp_path/"r"; out.mkdir(); escape=tmp_path/"escape.npz"; escape.write_bytes(b"x")
    import hashlib
    r=_receipt(q[0]); r["posterior_artifacts"]={"donor_effect_draws":{"path":"../escape.npz","sha256":hashlib.sha256(b"x").hexdigest()}}
    (out/f"fit_{q[0]['fit_id']}.json").write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    with pytest.raises(Q.QualificationRunRefused): Q.completed_prefix(out,q)


def test_campaign_summary_keeps_scoring_and_truth_off():
    r=Q.campaign_receipt_skeleton(code_sha="a"*40,custody_receipt_sha="b"*64,fit_count=1056)
    assert r["qualification_fits_run"]==0
    assert r["scoring_run"] is False and r["truth_accessed"] is False and r["training_authorized"] is False


def test_qualification_processes_import_no_controller_or_scoring_modules():
    forbidden={"generate_v79_v2_core_worlds","v79_v2_core_world_writer","v79_v2_core_launch","v79_v2_core_score"}
    for name in ("run_v79_v2_core_qualification.py","run_v79_v2_core_qualification_world.py"):
        tree=ast.parse((HERE/name).read_text(encoding="utf-8"))
        imported=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imported.update(alias.name for alias in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module: imported.add(node.module)
        assert not (imported & forbidden)
