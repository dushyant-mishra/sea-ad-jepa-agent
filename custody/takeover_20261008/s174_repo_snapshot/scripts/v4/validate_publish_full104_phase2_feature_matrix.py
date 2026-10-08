#!/usr/bin/env python3
"""Final fail-closed validation for the existing FULL104 mmap matrix package."""
from __future__ import annotations
import argparse, ctypes, gc, hashlib, json, os
from pathlib import Path
import numpy as np
import pandas as pd
import psutil

CHUNK_ROWS = 16_384
RSS_ALLOWANCE_BYTES = 768 * 1024**2
WRITER_CODE_SHA256 = "4c39d215657927e76141b073033dee086074c87b78b577a79116dc44063122e5"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def atomic_json(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8'); os.replace(tmp,path)

def trim_working_set():
    if os.name=='nt':
        kernel32=ctypes.windll.kernel32; psapi=ctypes.windll.psapi
        kernel32.GetCurrentProcess.restype=ctypes.c_void_p
        psapi.EmptyWorkingSet.argtypes=[ctypes.c_void_p]
        psapi.EmptyWorkingSet(kernel32.GetCurrentProcess())

def main():
    p=argparse.ArgumentParser(); p.add_argument('--staging',required=True); p.add_argument('--selection',required=True); p.add_argument('--features',required=True); p.add_argument('--preflight',required=True); p.add_argument('--patch-log',required=True); a=p.parse_args()
    stage=Path(a.staging).resolve(); selection_dir=Path(a.selection).resolve(); features=Path(a.features).resolve(); preflight=Path(a.preflight).resolve(); patch_log=Path(a.patch_log).resolve()
    n=4_553_407; expected_blocks=8_915
    selection_path=selection_dir/'PHASE2_METADATA_SELECTION_LEVEL4.csv.gz'
    cursor=0
    for chunk in pd.read_csv(selection_path,usecols=['selection_row'],chunksize=250_000):
        values=chunk.selection_row.to_numpy(np.int64); expected=np.arange(cursor,cursor+len(values),dtype=np.int64)
        if not np.array_equal(values,expected): raise RuntimeError('selection rows are not canonical unique range')
        cursor+=len(values)
    if cursor!=n: raise RuntimeError('selection cardinality mismatch')

    journal=pd.read_csv(stage/'ASSEMBLY_JOURNAL.csv',dtype={'block_key':str})
    feature_manifest=pd.read_csv(features/'PHASE2_MULTIVIEW_FEATURE_BLOCK_MANIFEST.csv',dtype={'block_key':str})
    if len(journal)!=expected_blocks or journal.block_key.nunique()!=expected_blocks or int(journal.rows.sum())!=n: raise RuntimeError('assembly journal geometry mismatch')
    if set(journal.block_key)!=set(feature_manifest.block_key) or len(feature_manifest)!=expected_blocks: raise RuntimeError('assembly/feature block-key set mismatch')

    arrays={
        'A_views':((n,4,512),np.dtype('float32')),'B_views':((n,4,512),np.dtype('float32')),
        'A_full':((n,512),np.dtype('float32')),'B_full':((n,512),np.dtype('float32')),
        'physical_descriptors':((n,6),np.dtype('float32')),'ASSEMBLY_SEEN':((n,),np.dtype('uint8')),
    }
    process=psutil.Process(); trim_working_set(); baseline=process.memory_info().rss; peak=baseline
    per_array=[]
    for name,(shape,dtype) in arrays.items():
        path=stage/f'{name}.npy'; array=np.load(path,mmap_mode='r')
        if array.shape!=shape or array.dtype!=dtype: raise RuntimeError(f'array geometry mismatch: {name}')
        array._mmap.close(); del array; gc.collect(); trim_working_set()
        chunks=0
        for begin in range(0,n,CHUNK_ROWS):
            # Reopen for each fixed chunk so Windows cannot retain pages from
            # earlier chunks in this process's mapped working set.
            array=np.load(path,mmap_mode='r')
            block=array[begin:begin+CHUNK_ROWS]
            valid=(block==1).all() if name=='ASSEMBLY_SEEN' else np.isfinite(block).all()
            if not valid: raise RuntimeError(f'nonfinite/unseen row in {name} at {begin}')
            chunks+=1; peak=max(peak,process.memory_info().rss); del block; array._mmap.close(); del array; gc.collect(); trim_working_set()
        per_array.append({'name':name,'rows_scanned':n,'chunks':chunks,'shape':list(shape),'dtype':str(dtype)})
    rss_bound=baseline+RSS_ALLOWANCE_BYTES
    if peak>rss_bound: raise RuntimeError(f'RSS bound exceeded: peak={peak} bound={rss_bound}')

    assembly_code=Path(__file__).with_name('assemble_full104_phase2_feature_matrix.py')
    current_text=assembly_code.read_text(encoding='utf-8')
    current_sha=sha(assembly_code)
    preflight_report=json.loads((preflight/'FULL104_FEATURE_STORAGE_MEMORY_PREFLIGHT.json').read_text(encoding='utf-8'))
    if preflight_report['input_hashes']['matrix_assembly_code']!=WRITER_CODE_SHA256: raise RuntimeError('writer code hash authority mismatch')
    if 'finite_scan_rows = 16_384' not in current_text or 'if not np.isfinite(array).all()' in current_text: raise RuntimeError('validation-only patch shape mismatch')
    diff_text='''writer validation:\n    for array in arrays.values():\n        if not np.isfinite(array).all(): fail\npublisher validation:\n    finite_scan_rows = 16_384\n    for array in arrays.values():\n        for begin in range(0, len(array), finite_scan_rows):\n            if not np.isfinite(array[begin:begin + finite_scan_rows]).all(): fail\n'''
    diff_path=stage/'VALIDATION_ONLY_PATCH.diff.txt'; diff_path.write_text(diff_text,encoding='utf-8')
    aborted={'schema':'full104-matrix-aborted-prepublication-v1','status':'ABORTED_ENGINEERING_PREPUBLICATION_NOT_A_PACKAGE','rows_written':n,'blocks_written':expected_blocks,'published':False,'reason':'whole-array np.isfinite temporary violated bounded-RAM contract','arrays_rebuilt':False,'write_semantics_changed':False,'writer_code_sha256':WRITER_CODE_SHA256,'validation_publisher_code_sha256':current_sha,'validation_only_diff_sha256':sha(diff_path)}
    aborted_path=stage/'ABORTED_PREPUBLICATION_ATTEMPT.json'; atomic_json(aborted_path,aborted)

    file_rows=[]
    for name,(shape,dtype) in arrays.items():
        path=stage/f'{name}.npy'; file_rows.append({'name':name,'path':path.name,'shape':json.dumps(list(shape)),'dtype':str(dtype),'bytes':path.stat().st_size,'sha256':sha(path)})
    row_path=stage/'PHASE2_FEATURE_ROWS.csv'; file_rows.append({'name':'rows','path':row_path.name,'shape':json.dumps([n]),'dtype':'csv','bytes':row_path.stat().st_size,'sha256':sha(row_path)})
    matrix_manifest=stage/'PHASE2_FEATURE_MATRIX_MANIFEST.csv'; pd.DataFrame(file_rows).to_csv(matrix_manifest,index=False,lineterminator='\n')
    validation={'schema':'full104-feature-matrix-final-validation-v1','status':'PASS_FULL104_FEATURE_MATRIX_FINAL_VALIDATION','rows':n,'blocks':expected_blocks,'unique_selection_rows':n,'unique_block_keys':expected_blocks,'chunk_rows':CHUNK_ROWS,'all_A_B_full_and_view_rows_finite':True,'assembly_seen_all_one':True,'baseline_rss_bytes':baseline,'peak_rss_bytes':peak,'rss_bound_bytes':rss_bound,'rss_bounded':True,'array_scans':per_array,'arrays_rebuilt':False,'write_semantics_changed':False,'writer_code_sha256':WRITER_CODE_SHA256,'validation_publisher_code_sha256':current_sha,'validation_only_diff_sha256':sha(diff_path),'patch_log_sha256':sha(patch_log),'selection_sha256':sha(selection_path),'feature_manifest_sha256':sha(features/'PHASE2_MULTIVIEW_FEATURE_MANIFEST.csv'),'matrix_manifest_sha256':sha(matrix_manifest)}
    validation_path=stage/'FULL104_FEATURE_MATRIX_FINAL_VALIDATION.json'; atomic_json(validation_path,validation)

    package_files=[matrix_manifest,stage/'PHASE2_FEATURE_MATRIX_AUDIT.json',stage/'ASSEMBLY_JOURNAL.csv',assembly_code,Path(__file__),patch_log,preflight/'FULL104_FEATURE_STORAGE_MEMORY_PREFLIGHT.json',stage/'FAILED_FINAL_VALIDATION_ATTEMPT_1.json',aborted_path,diff_path,validation_path]
    package=stage/'PHASE2_FEATURE_MATRIX_PACKAGE_MANIFEST.csv'
    pd.DataFrame([{'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)} for path in package_files]).to_csv(package,index=False,lineterminator='\n')
    root=sha(package); (stage/'PHASE2_FEATURE_MATRIX_PACKAGE_ROOT_SHA256.txt').write_text(root+'\n',encoding='ascii')
    print(json.dumps({**validation,'package_manifest_sha256':root},indent=2))
if __name__=='__main__': main()
