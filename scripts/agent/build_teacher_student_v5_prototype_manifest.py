#!/usr/bin/env python3
"""Build/check the deterministic Teacher/Student V5 data-first prototype manifest.

This is planning/proof provenance only. It creates no execution authority.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ACTIVE_TESTS=(
 'tests/test_teacher_student_data_first_v1.py',
 'tests/test_teacher_student_packed_equivalence_v1.py',
 'tests/test_teacher_student_v5_finite_triplets_v1.py',
 'tests/test_teacher_student_v5_inactive_update_reference.py',
 'tests/test_teacher_student_v5_numerical_boundary_v1.py',
 'tests/test_teacher_student_v5_objective_schedule_v2.py',
 'tests/test_teacher_student_v5_proposal_policy_v1.py',
 'tests/test_teacher_student_v5_rng_contract_v2.py',
 'tests/test_teacher_student_v5_rng_dense_packed_v2.py',
 'tests/test_teacher_student_v5_scientific_target_v2.py',
 'tests/test_teacher_student_v5_support_schedule_v1.py',
)
STALE_PATHS={
 'src/sea_ad_jepa/v5/keyed_rng_reference.py',
 'src/sea_ad_jepa/v5/keyed_dropout_prototype.py',
 'tests/test_teacher_student_v5_keyed_packing_v1.py',
 'tests/test_teacher_student_v5_optimizer_boundary_v1.py',
 'tests/test_teacher_student_v5_rng_and_triplets.py',
}
MANIFEST='docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_PROTOTYPE_MANIFEST.csv'
ROOTFILE='docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_PROTOTYPE_ROOT.txt'
SELECTION='docs/agent/TEACHER_STUDENT_V5_ACTIVE_TEST_SELECTION.txt'
ACTIVE_MANIFEST='docs/agent/TEACHER_STUDENT_V5_ACTIVE_TEST_MANIFEST.csv'


def sha256_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def file_row(root:Path,rel:str)->tuple[str,int,str]:
    b=(root/rel).read_bytes(); return rel,len(b),sha256_bytes(b)

def expected_paths(root:Path)->list[str]:
    out=set()
    for p in (root/'docs/agent').glob('READER_FIT_*'):
        if p.is_file(): out.add(p.relative_to(root).as_posix())
    for p in (root/'docs/agent').glob('TEACHER_STUDENT_V5_*'):
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        if rel in {MANIFEST,ROOTFILE}: continue
        out.add(rel)
    for p in (root/'scripts/agent').glob('profile_reader_fit_*.py'):
        if p.is_file(): out.add(p.relative_to(root).as_posix())
    out.add('scripts/agent/build_teacher_student_v5_prototype_manifest.py')
    out.add('scripts/agent/audit_teacher_student_v5_data_first_v1.py')
    for p in (root/'src/sea_ad_jepa/v5').glob('*.py'):
        if p.is_file(): out.add(p.relative_to(root).as_posix())
    out.update(ACTIVE_TESTS)
    return sorted(out)

def render_csv(rows:list[tuple[str,int,str]])->bytes:
    import io
    s=io.StringIO(newline='')
    w=csv.writer(s,lineterminator='\n'); w.writerow(['path','bytes','sha256']); w.writerows(rows)
    return s.getvalue().encode()

def build_active(root:Path)->tuple[bytes,bytes]:
    selection=('\n'.join(ACTIVE_TESTS)+'\n').encode()
    rows=[file_row(root,p) for p in ACTIVE_TESTS]
    return selection,render_csv(rows)

def assert_fail_closed_flags(root:Path)->None:
    for rel in expected_paths(root):
        if not rel.endswith('.json'): continue
        data=json.loads((root/rel).read_text())
        for key in ('training_authorized','execution_authorized','successor_u0_materialization_authorized','td60_execution_authorized'):
            if data.get(key) is True:
                raise SystemExit(f'FAIL_OPEN_FLAG {rel}:{key}=true')

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); ap.add_argument('--write',action='store_true'); a=ap.parse_args()
    root=a.root.resolve()
    paths=expected_paths(root)
    stale=sorted(STALE_PATHS.intersection(paths))
    if stale: raise SystemExit(f'STALE_PATHS_PRESENT {stale}')
    missing=[p for p in paths if not (root/p).is_file()]
    if missing: raise SystemExit(f'MISSING_PATHS {missing}')
    selection,active_manifest=build_active(root)
    if a.write:
        (root/SELECTION).write_bytes(selection)
        (root/ACTIVE_MANIFEST).write_bytes(active_manifest)
    else:
        if (root/SELECTION).read_bytes()!=selection: raise SystemExit('ACTIVE_SELECTION_MISMATCH')
        if (root/ACTIVE_MANIFEST).read_bytes()!=active_manifest: raise SystemExit('ACTIVE_MANIFEST_MISMATCH')
    # Recollect after active metadata is guaranteed current.
    paths=expected_paths(root)
    rows=[file_row(root,p) for p in paths]
    manifest=render_csv(rows)
    digest=sha256_bytes(manifest)
    rootbytes=(digest+'\n').encode()
    if a.write:
        (root/MANIFEST).write_bytes(manifest)
        (root/ROOTFILE).write_bytes(rootbytes)
    else:
        if (root/MANIFEST).read_bytes()!=manifest: raise SystemExit('PROTOTYPE_MANIFEST_MISMATCH')
        if (root/ROOTFILE).read_bytes()!=rootbytes: raise SystemExit('PROTOTYPE_ROOT_MISMATCH')
    assert_fail_closed_flags(root)
    print(json.dumps({
      'terminal':'PASS_TEACHER_STUDENT_V5_DATA_FIRST_PROTOTYPE_MANIFEST',
      'active_tests':len(ACTIVE_TESTS),'manifest_rows':len(rows),'manifest_sha256':digest,
      'training_authorized':False,'execution_authorized':False,
    },sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
