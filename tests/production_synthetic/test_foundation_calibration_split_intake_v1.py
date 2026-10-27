"""Hostile synthetic ZIP fixtures only; no real donors, matrices or counts."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import zipfile

import pytest

from scripts.production_synthetic.foundation_calibration_split_intake_v1 import (
    inspect, IntakeError, MAIN, EXPRESSION, CHECKPOINTS, ROOT, PART_STEM, PART_MANIFEST,
)

def digest(b):
    return hashlib.sha256(b).hexdigest()

def zip_blob(items):
    f=io.BytesIO()
    with zipfile.ZipFile(f,"w",zipfile.ZIP_STORED) as z:
        for name,body in items.items():
            z.writestr(name,body)
    return f.getvalue()

def make_archives(root, *, duplicate_donor=False, mutate_payload=False):
    # All identities below are synthetic, and never appear in emitted receipts.
    split="donor_id,reader_partition\n"
    split+="".join(f"F{i:03d},reader_fit\n" for i in range(104))
    split+="".join(f"V{i:03d},reader_validation\n" for i in range(22))
    split+="".join(f"O{i:03d},reader_oracle\n" for i in range(23))
    if duplicate_donor:
        split=split.replace("O022,reader_oracle","F000,reader_oracle")
    main={"splits/reader_donor_split.csv":split.encode()}
    main.update({f"meta/m{i:03d}.txt":f"M{i}".encode() for i in range(48)})
    exp={f"expression/e{i:03d}.txt":f"E{i}".encode() for i in range(44)}
    ckpt={f"checkpoints/c{i:03d}.txt":f"C{i}".encode() for i in range(3)}
    big={"expression/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz":b"TEST_ONLY_SYNTHETIC"}
    source={"main":main,"expression":exp,"checkpoints":ckpt,"split":big}
    rows=[]
    for members in source.values():
        for p,b in members.items():
            rows.append({"path":p,"bytes":len(b),"sha256":digest(b),"role":"SYNTH_TEST","source":"SYNTH_TEST"})
    assert len(rows)==97
    fd=io.StringIO()
    writer=csv.DictWriter(fd,fieldnames=["path","bytes","sha256","role","source"],lineterminator="\n")
    writer.writeheader();writer.writerows(rows)
    manifest=fd.getvalue().encode()
    status={
        "schema":"foundation-calibration-bundle-v1","files":97,
        "manifest_sha256":digest(manifest),
        "dev_sealed_expression_included":False,"pathology_fields_included":False,
        "metadata_cells":6351753,"expression_cells":50000,
        "addresses":41238,"operators":42,
    }
    contained={ROOT+k:v for k,v in main.items()}
    contained[ROOT+"BUNDLE_SHA256_MANIFEST.csv"]=manifest
    contained[ROOT+"BUNDLE_STATUS.json"]=json.dumps(status).encode()
    if mutate_payload:contained[ROOT+"meta/m001.txt"]=b"x1"
    (root/MAIN).write_bytes(zip_blob(contained))
    (root/EXPRESSION).write_bytes(zip_blob({"expression/"+k:v for k,v in exp.items()}))
    (root/CHECKPOINTS).write_bytes(zip_blob(ckpt))
    stem=PART_STEM.removesuffix(".zip")
    bigzip=zip_blob({stem+"/"+stem+"/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.npz":
                    b"TEST_ONLY_SYNTHETIC"})
    cut=len(bigzip)//2
    parts=[bigzip[:cut],bigzip[cut:]]
    for i,body in enumerate(parts,1):
        (root/(PART_STEM+f".part{i:03d}")).write_bytes(body)
    f=io.StringIO();writer=csv.DictWriter(f,fieldnames=["file","bytes","sha256"],lineterminator="\n")
    writer.writeheader()
    for name,body in [(PART_STEM,bigzip),
                      (PART_STEM+".part001",parts[0]),(PART_STEM+".part002",parts[1])]:
        writer.writerow({"file":name,"bytes":len(body),"sha256":digest(body).upper()})
    (root/PART_MANIFEST).write_text(f.getvalue(),encoding="utf-8-sig")
    return root

def test_complete_separate_archives_can_be_fully_verified(tmp_path):
    data=inspect(make_archives(tmp_path),full=True)
    assert data["logical_manifest_files"]==97
    assert data["physical_member_hashes_verified"]==97
    assert data["physical_member_hashes_unverified_large"]==0
    assert data["logical_members_by_archive"]=={
        "main":49,"expression":44,"checkpoints":3,"split_41k_expression":1}
    assert data["present_day_real_reference_ready"] is False
    assert data["calibration_authenticated_under_task3_registry"] is False
    assert data["physical_cell_gene_identity_externally_attested"] is False
    assert data["authority"].endswith("STAGE4_NOT_AUTHORIZED")
    assert data["historical_reader_split_donor_counts"]=={
        "reader_fit":104,"reader_validation":22,"reader_oracle":23}
    assert "F000" not in json.dumps(data)

def test_split_part_corruption_cannot_be_relabelled(tmp_path):
    make_archives(tmp_path)
    p=tmp_path/(PART_STEM+".part002")
    b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
    with pytest.raises(IntakeError,match="part SHA/length mismatch"):
        inspect(tmp_path)

def test_mutated_archive_member_is_refused(tmp_path):
    make_archives(tmp_path,mutate_payload=True)
    with pytest.raises(IntakeError,match="member sha mismatch"):
        inspect(tmp_path)

def test_reader_split_identity_overlap_is_refused(tmp_path):
    make_archives(tmp_path,duplicate_donor=True)
    with pytest.raises(IntakeError,match="reused/blank donor"):
        inspect(tmp_path)

def test_forged_manifest_sha_is_refused(tmp_path):
    make_archives(tmp_path)
    p=tmp_path/MAIN
    with zipfile.ZipFile(p) as z:
        items={x.filename:z.read(x) for x in z.infolist() if not x.is_dir()}
    status=json.loads(items[ROOT+"BUNDLE_STATUS.json"])
    status["manifest_sha256"]="0"*64
    items[ROOT+"BUNDLE_STATUS.json"]=json.dumps(status).encode()
    p.write_bytes(zip_blob(items))
    with pytest.raises(IntakeError,match="manifest SHA mismatch"):
        inspect(tmp_path)

def test_missing_expression_member_is_refused(tmp_path):
    make_archives(tmp_path)
    p=tmp_path/EXPRESSION
    with zipfile.ZipFile(p) as z:
        items={x.filename:z.read(x) for x in z.infolist() if not x.is_dir()}
    items.pop(next(iter(items)))
    p.write_bytes(zip_blob(items))
    with pytest.raises(IntakeError,match="declared bundle paths differ"):
        inspect(tmp_path)

def test_archive_roles_and_nonpromotion_are_not_equivalent_to_authentication(tmp_path):
    result=inspect(make_archives(tmp_path))
    assert result["physical_member_hashes_verified"]==97
    assert result["status_declares_no_dev_sealed_expression"] is True
    assert result["status_declares_no_pathology_fields"] is True
    assert result["safe_for_synthetic_observation_realism_conventions"] is False
    assert result["source_scope"].endswith("NOT_CURRENT_QUALIFIED_CALIBRATION")
