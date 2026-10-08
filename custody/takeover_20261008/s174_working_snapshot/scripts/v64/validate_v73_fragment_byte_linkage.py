#!/usr/bin/env python3
"""Independently validate synthetic fragment bytes against manifest and multiome source."""
from __future__ import annotations
import argparse,gzip,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np


def sha256_file(path:Path,chunk:int=1<<20)->str:
    h=hashlib.sha256()
    with open(path,'rb') as fh:
        for block in iter(lambda:fh.read(chunk),b''):h.update(block)
    return h.hexdigest()


def _fail(code:str,**details)->dict:
    return {'schema':'V75_FRAGMENT_BYTE_LINKAGE_RECEIPT_V1','status':'FAIL_CLOSED','failure_code':code,'details':details,'qualified':False}


def validate(root:Path)->dict:
    frag_root=root/'observable_raw'/'PAIRED_MULTIOME_fragments'; multi_root=root/'observable_raw'/'PAIRED_MULTIOME_like_sharded'
    frag_manifest_path=frag_root/'SYNTHETIC_FRAGMENT_MANIFEST.json'; multi_manifest_path=multi_root/'PAIRED_MULTIOME_SHARDED_MANIFEST.json'
    if not frag_manifest_path.exists() or not multi_manifest_path.exists():return _fail('MISSING_MANIFEST')
    try:
        fm=json.loads(frag_manifest_path.read_text()); mm=json.loads(multi_manifest_path.read_text())
    except Exception as exc:return _fail('MANIFEST_PARSE_ERROR',error=repr(exc))
    multi_by_name={s['file']:s for s in mm.get('shards',[])}; seen_barcodes={}; total_rows=0; total_multiplicity=0; verified=[]
    for shard in fm.get('shards',[]):
        frag_path=frag_root/shard['file']
        if not frag_path.exists():return _fail('FRAGMENT_SHARD_MISSING',file=shard['file'])
        actual_sha=sha256_file(frag_path)
        if actual_sha!=shard.get('sha256'):return _fail('COMPRESSED_SHA256_MISMATCH',file=shard['file'],expected=shard.get('sha256'),actual=actual_sha)
        source_name=shard.get('source_multiome_file'); source=multi_by_name.get(source_name)
        if source is None:return _fail('SOURCE_MULTIOME_SHARD_UNKNOWN',source_file=source_name)
        multi_path=multi_root/source_name
        if not multi_path.exists():return _fail('SOURCE_MULTIOME_SHARD_MISSING',source_file=source_name)
        source_sha=sha256_file(multi_path)
        if source_sha!=shard.get('source_multiome_sha256') or source_sha!=source.get('sha256'):
            return _fail('SOURCE_MULTIOME_DIGEST_MISMATCH',source_file=source_name,actual=source_sha,fragment_manifest_value=shard.get('source_multiome_sha256'),multiome_manifest_value=source.get('sha256'))
        try:
            z=np.load(multi_path,allow_pickle=False); cell_ids=[str(x) for x in z['cell_id']]; atac=z['atac_counts']
        except Exception as exc:return _fail('SOURCE_MULTIOME_READ_ERROR',source_file=source_name,error=repr(exc))
        if atac.shape[1]!=len(cell_ids):return _fail('SOURCE_MULTIOME_AXIS_MISMATCH',source_file=source_name)
        expected={}
        for j,barcode in enumerate(cell_ids):
            if barcode in seen_barcodes:return _fail('DUPLICATE_BARCODE_IN_SOURCE',barcode=barcode,first_source_file=seen_barcodes[barcode][0],second_source_file=source_name)
            seen_barcodes[barcode]=(source_name,j); expected[barcode]=int(atac[:,j].sum())
        observed=Counter(); rows=0
        try:
            with gzip.open(frag_path,'rt',encoding='utf-8') as fh:
                for line_no,line in enumerate(fh,start=1):
                    fields=line.rstrip('\n').split('\t')
                    if len(fields)!=5:return _fail('MALFORMED_FRAGMENT_ROW',file=shard['file'],line=line_no)
                    barcode=fields[3]
                    try:multiplicity=int(fields[4])
                    except Exception:return _fail('INVALID_MULTIPLICITY',file=shard['file'],line=line_no)
                    if multiplicity<=0:return _fail('NONPOSITIVE_MULTIPLICITY',file=shard['file'],line=line_no)
                    observed[barcode]+=multiplicity; rows+=1
        except Exception as exc:return _fail('FRAGMENT_DECOMPRESSION_ERROR',file=shard['file'],error=repr(exc))
        unknown=set(observed)-set(expected)
        if unknown:return _fail('UNKNOWN_FRAGMENT_BARCODE',file=shard['file'],examples=sorted(unknown)[:5])
        mismatches=[b for b in expected if observed.get(b,0)!=expected[b]]
        if mismatches:
            b=mismatches[0]; return _fail('BARCODE_MULTIPLICITY_MISMATCH',file=shard['file'],barcode=b,expected=expected[b],observed=observed.get(b,0),mismatch_count=len(mismatches))
        shard_mult=sum(observed.values())
        if rows!=int(shard.get('rows',-1)) or shard_mult!=int(shard.get('multiplicity',-1)):
            return _fail('SHARD_TOTAL_MISMATCH',file=shard['file'],observed_rows=rows,manifest_rows=shard.get('rows'),observed_multiplicity=shard_mult,manifest_multiplicity=shard.get('multiplicity'))
        total_rows+=rows; total_multiplicity+=shard_mult; verified.append({'file':shard['file'],'sha256':actual_sha,'rows':rows,'multiplicity':shard_mult})
    if total_rows!=int(fm.get('total_rows',-1)) or total_multiplicity!=int(fm.get('total_multiplicity',-1)):
        return _fail('GLOBAL_TOTAL_MISMATCH',observed_rows=total_rows,manifest_rows=fm.get('total_rows'),observed_multiplicity=total_multiplicity,manifest_multiplicity=fm.get('total_multiplicity'))
    return {'schema':'V75_FRAGMENT_BYTE_LINKAGE_RECEIPT_V1','status':'PASS','qualified':True,'compressed_sha256_recomputed_from_bytes':True,'barcode_multiplicity_reconciled_to_multiome':True,'duplicate_barcode_guard_runs_before_mapping':True,'total_rows':total_rows,'total_multiplicity':total_multiplicity,'shards':verified}


def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();receipt=validate(Path(a.root));Path(a.out).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));return 0 if receipt.get('qualified') else 2

if __name__=='__main__':raise SystemExit(main())
