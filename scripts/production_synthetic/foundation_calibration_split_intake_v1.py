#!/usr/bin/env python3
"""Read-only integrity check for the *historical* 2026-08-24 calibration package.

Reconciles the 97-file manifest across four logical archives without unpacking
large matrices to disk. No donor identities or expression values enter receipts.
A matching source SHA is NOT a real-data/Task3/G7 biological attestation.
"""
from __future__ import annotations
import argparse
import bisect
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import zipfile

MAIN = "FOUNDATION_CALIBRATION_BUNDLE_20260824.zip"
EXPRESSION = "expression.zip"
CHECKPOINTS = "checkpoints.zip"
PART_STEM = "FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip"
PART_MANIFEST = PART_STEM + ".parts.sha256.csv"
ROOT = "FOUNDATION_CALIBRATION_BUNDLE_20260824/foundation_calibration_bundle_20260824/"
STATUS = "BUNDLE_STATUS.json"
MANIFEST = "BUNDLE_SHA256_MANIFEST.csv"
SPLIT = "splits/reader_donor_split.csv"
BLOCK = 8 * 1024 * 1024
QUICK_MAX = 20 * 1024 * 1024

class IntakeError(ValueError):
    pass

class ConcatenatedParts(io.RawIOBase):
    """Seekable read-only view of two independently hashed ZIP parts."""
    def __init__(self, paths):
        self._files = [p.open("rb") for p in paths]
        self._offsets = [0]
        for p in paths:
            self._offsets.append(self._offsets[-1] + p.stat().st_size)
        self._pos = 0
        self._closed = False

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self._pos
    def seek(self, offset, whence=0):
        if whence == 1: offset += self._pos
        elif whence == 2: offset += self._offsets[-1]
        elif whence != 0: raise OSError("invalid seek")
        if offset < 0: raise OSError("negative seek")
        self._pos = offset
        return self._pos
    def read(self, size=-1):
        if size is None or size < 0: size = self._offsets[-1] - self._pos
        if size == 0 or self._pos >= self._offsets[-1]: return b""
        last = min(self._pos+size,self._offsets[-1]); chunks=[]
        while self._pos < last:
            idx=bisect.bisect_right(self._offsets,self._pos)-1
            f=self._files[idx]
            f.seek(self._pos-self._offsets[idx])
            count=min(last-self._pos,self._offsets[idx+1]-self._pos)
            chunk=f.read(count)
            if len(chunk)!=count: raise OSError("short split-archive read")
            chunks.append(chunk)
            self._pos+=count
        return b"".join(chunks)
    def close(self):
        if not self._closed:
            for f in self._files: f.close()
            self._closed=True
        super().close()

def digest_stream(fd):
    h=hashlib.sha256(); total=0
    while True:
        b=fd.read(BLOCK)
        if not b:break
        h.update(b);total+=len(b)
    return h.hexdigest(),total

def check(valid,reason):
    if not valid: raise IntakeError(reason)

def digest_file(path):
    with path.open("rb") as f:return digest_stream(f)

def verify_parts(root):
    records=list(csv.DictReader((root/PART_MANIFEST).read_text(encoding="utf-8-sig").splitlines()))
    check(len(records)==3 and records[0]["file"]==PART_STEM,"parts manifest missing")
    names=[PART_STEM+".part001",PART_STEM+".part002"]
    check([x["file"] for x in records[1:]]==names,"parts ordering")
    paths=[root/n for n in names]
    for row,p in zip(records[1:],paths):
        h,n=digest_file(p)
        check(h.upper()==row["sha256"].upper() and n==int(row["bytes"]),"part SHA/length mismatch")
    with ConcatenatedParts(paths) as f:sha,size=digest_stream(f)
    check(sha.upper()==records[0]["sha256"].upper() and size==int(records[0]["bytes"]),
          "joined expression archive SHA/length mismatch")
    return paths,sha,size

def inspect(input_dir:Path,*,full=False):
    root=input_dir.resolve()
    check(root.is_dir(),"input directory not found")
    parts,combined_sha,combined_size=verify_parts(root)
    with zipfile.ZipFile(root/MAIN) as main, zipfile.ZipFile(root/EXPRESSION) as exp, \
         zipfile.ZipFile(root/CHECKPOINTS) as ckpt,ConcatenatedParts(parts) as fd,zipfile.ZipFile(fd) as big:
        status=json.loads(main.read(ROOT+STATUS))
        manifest=main.read(ROOT+MANIFEST)
        sha=hashlib.sha256(manifest).hexdigest()
        check(sha==status["manifest_sha256"],"manifest SHA mismatch")
        rows=list(csv.DictReader(io.StringIO(manifest.decode("utf-8"))))
        check(len(rows)==status["files"]==97 and len({x["path"] for x in rows})==97,
              "declared manifest count/uniqueness changed")
        groups=[
            ("main",main,ROOT),
            ("expression",exp,"expression/"),
            ("checkpoints",ckpt,""),
            ("split_41k_expression",big,"FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K/"),
        ]
        catalog={}
        for label,archive,prefix in groups:
            for member in archive.infolist():
                if member.is_dir() or not member.filename.startswith(prefix):continue
                logical=member.filename[len(prefix):]
                if label=="split_41k_expression":logical="expression/"+logical
                if label=="main" and logical in {STATUS,MANIFEST}:continue
                check(logical not in catalog,"duplicate logical path in archive groups")
                catalog[logical]=(label,archive,member.filename,member.file_size)
        check(set(catalog)=={x["path"] for x in rows},
              "declared bundle paths differ from cross-archive members")
        archive_counts=Counter(); checked=0
        for row in rows:
            label,archive,path,size=catalog[row["path"]]
            check(size==int(row["bytes"]),"member length mismatch: "+row["path"])
            archive_counts[label]+=1
            if full or size<=QUICK_MAX:
                with archive.open(path) as stream:h,n=digest_stream(stream)
                check(h==row["sha256"] and n==size,"member sha mismatch: "+row["path"])
                checked+=1
        split_rows=list(csv.DictReader(io.StringIO(main.read(ROOT+SPLIT).decode("utf-8"))))
        check(bool(split_rows) and set(split_rows[0])=={"donor_id","reader_partition"},"reader split schema")
        ids=[x["donor_id"] for x in split_rows]
        check(all(type(x) is str and x for x in ids) and len(set(ids))==len(ids),
              "reused/blank donor identity in historical split")
        split_counts=Counter(x["reader_partition"] for x in split_rows)
        check(split_counts==Counter({"reader_fit":104,"reader_validation":22,"reader_oracle":23}),
              "historical split differs from 104/22/23")
        check(status["addresses"]==41238 and status["operators"]==42 and
              status["metadata_cells"]==6351753 and status["expression_cells"]==50000,
              "historical declared coverage drift")
        check(status["dev_sealed_expression_included"] is False and
              status["pathology_fields_included"] is False,
              "protected-expression/pathology declarations changed")
        return {
            "schema":"JEPA_HISTORICAL_FOUNDATION_CALIBRATION_INTAKE_V1",
            "source_scope":"HISTORICAL_2026_08_24_ARCHIVE_ONLY__NOT_CURRENT_QUALIFIED_CALIBRATION",
            "bundle_manifest_sha256":sha,
            "split_expression_archive_sha256":combined_sha,
            "split_expression_archive_bytes":combined_size,
            "split_expression_parts_verified":True,
            "logical_manifest_files":len(rows),
            "logical_members_by_archive":dict(sorted(archive_counts.items())),
            "physical_member_hashes_verified":checked,
            "physical_member_hashes_unverified_large":len(rows)-checked,
            "verification_mode":"ALL_SHA256" if full else "SMALL_SHA256__LARGE_LENGTH_ONLY",
            "historical_reader_split_donor_counts":dict(sorted(split_counts.items())),
            "status_declared_coverage":{
                "addresses":status["addresses"],"operators":status["operators"],
                "metadata_cells":status["metadata_cells"],"expression_cells":status["expression_cells"]
            },
            "status_declares_no_dev_sealed_expression":True,
            "status_declares_no_pathology_fields":True,
            "present_day_real_reference_ready":False,
            "calibration_authenticated_under_task3_registry":False,
            "physical_cell_gene_identity_externally_attested":False,
            "safe_for_synthetic_observation_realism_conventions":False,
            "stops":[
                "August archive cannot inherit later repaired HVS/SEA raw-count/G7 physical identity authority",
                "Reader split metadata is not a trusted observed count or q-excluded library producer",
                "Historical expression 50k development sample is not all 6.35M measured observations",
                "Hash and archive roles verified, but no new biology or real gate was executed",
                "Production V3.1.1 needs current TRAIN observation-only statistics and independent issuer"
            ],
            "authority":"TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED",
        }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input-dir",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--full",action="store_true")
    args=parser.parse_args()
    data=inspect(args.input_dir,full=args.full)
    args.output.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("HISTORICAL_CALIBRATION_SPLIT_INTAKE_VERIFIED__NO_CURRENT_AUTHORITY",
          data["physical_member_hashes_verified"],"of",data["logical_manifest_files"])

if __name__=="__main__":main()
