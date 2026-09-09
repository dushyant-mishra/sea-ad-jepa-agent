#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, sqlite3
from fractions import Fraction
from pathlib import Path
import numpy as np


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):
            h.update(b)
    return h.hexdigest()


def frac_obj(x: Fraction) -> dict:
    return {'numerator': x.numerator, 'denominator': x.denominator, 'float': float(x)}


def derive(metadata_sqlite: Path, support_npz: Path, partition: str='reader_fit') -> dict:
    z=np.load(support_npz, allow_pickle=False)
    required={'states','matrix_id','operator_index','molecular_address_index','state_names'}
    if set(z.files) != required:
        raise RuntimeError('STOP_SUPPORT_LEDGER_SCHEMA_MISMATCH')
    states=np.asarray(z['states'])
    matrix_ids=np.asarray(z['matrix_id']).astype(str)
    operators=np.asarray(z['operator_index']).astype(int)
    addr=np.asarray(z['molecular_address_index']).astype(int)
    state_names=np.asarray(z['state_names']).astype(str)
    if states.ndim!=2 or len(matrix_ids)!=states.shape[0] or len(operators)!=states.shape[0]:
        raise RuntimeError('STOP_SUPPORT_LEDGER_GEOMETRY_MISMATCH')
    if len(set(operators.tolist()))!=len(operators) or len(set(matrix_ids.tolist()))!=len(matrix_ids):
        raise RuntimeError('STOP_SUPPORT_LEDGER_OPERATOR_OR_MATRIX_DUPLICATE')
    if not np.array_equal(np.sort(addr), np.arange(states.shape[1])):
        raise RuntimeError('STOP_SUPPORT_LEDGER_ADDRESS_CLOSURE_MISMATCH')
    ix=np.flatnonzero(state_names=='MEASURED_SCALAR')
    if len(ix)!=1:
        raise RuntimeError('STOP_SUPPORT_LEDGER_SCALAR_STATE_UNRESOLVED')
    scalar_code=int(ix[0])
    scalar=states==scalar_code
    core=scalar.all(axis=0)
    core_n=int(core.sum())
    scalar_n=scalar.sum(axis=1).astype(int)
    native_n=(scalar & ~core[None,:]).sum(axis=1).astype(int)

    con=sqlite3.connect(f'file:{metadata_sqlite}?mode=ro&immutable=1', uri=True)
    rows=con.execute(
        'select donor_id,source,operator_index,matrix_id,count(*) from cells where partition=? '
        'group by donor_id,source,operator_index,matrix_id order by donor_id,operator_index', (partition,)
    ).fetchall()
    total=con.execute('select count(*) from cells where partition=?',(partition,)).fetchone()[0]
    donors=con.execute('select count(distinct donor_id) from cells where partition=?',(partition,)).fetchone()[0]
    ops=con.execute('select count(distinct operator_index) from cells where partition=?',(partition,)).fetchone()[0]
    mats=con.execute('select count(distinct matrix_id) from cells where partition=?',(partition,)).fetchone()[0]
    sources=con.execute('select count(distinct source) from cells where partition=?',(partition,)).fetchone()[0]
    con.close()
    if not rows or sum(int(r[4]) for r in rows)!=total:
        raise RuntimeError('STOP_METADATA_GROUP_CLOSURE_MISMATCH')
    if ops!=len(operators) or mats!=len(matrix_ids):
        raise RuntimeError('STOP_SUPPORT_METADATA_OPERATOR_MATRIX_CARDINALITY_MISMATCH')
    op_to_i={int(op):i for i,op in enumerate(operators)}
    op_matrix={}
    op_source={}
    donor_sizes={}
    for donor,source,op,matrix,n in rows:
        op=int(op); n=int(n); donor=str(donor); source=str(source); matrix=str(matrix)
        if op not in op_to_i:
            raise RuntimeError('STOP_METADATA_OPERATOR_NOT_IN_SUPPORT_LEDGER')
        i=op_to_i[op]
        if matrix_ids[i] != matrix:
            raise RuntimeError('STOP_SUPPORT_METADATA_MATRIX_ID_MISMATCH')
        if op in op_matrix and op_matrix[op]!=matrix:
            raise RuntimeError('STOP_METADATA_OPERATOR_MATRIX_NOT_ONE_TO_ONE')
        if op in op_source and op_source[op]!=source:
            raise RuntimeError('STOP_METADATA_OPERATOR_SOURCE_NOT_ONE_TO_ONE')
        op_matrix[op]=matrix; op_source[op]=source
        donor_sizes[donor]=donor_sizes.get(donor,0)+n
    if len(donor_sizes)!=donors:
        raise RuntimeError('STOP_METADATA_DONOR_CLOSURE_MISMATCH')

    expected_native=Fraction(0,1)
    expected_scalar=Fraction(0,1)
    raw_native_num=0
    raw_scalar_num=0
    for donor,source,op,matrix,n in rows:
        op=int(op); n=int(n); donor=str(donor); i=op_to_i[op]
        p_group=Fraction(n, donors*donor_sizes[donor])
        expected_native += p_group * int(native_n[i])
        expected_scalar += p_group * int(scalar_n[i])
        raw_native_num += n*int(native_n[i])
        raw_scalar_num += n*int(scalar_n[i])
    if expected_scalar != Fraction(core_n,1)+expected_native:
        raise RuntimeError('STOP_SUPPORT_FAMILY_ARITHMETIC')
    family_den=Fraction(core_n,1)+expected_native
    common_weight=Fraction(core_n,1)/family_den
    native_weight=expected_native/family_den
    raw_native=Fraction(raw_native_num,total)
    raw_scalar=Fraction(raw_scalar_num,total)
    raw_common_weight=Fraction(core_n,1)/raw_scalar

    operator_rows=[]
    for op in sorted(op_to_i):
        i=op_to_i[op]
        operator_rows.append({
            'operator_index':op,
            'source':op_source[op],
            'matrix_id':op_matrix[op],
            'measured_scalar_addresses':int(scalar_n[i]),
            'operator_native_addresses':int(native_n[i]),
            'common_core_addresses':core_n,
        })

    return {
        'schema':'JEPA_V5_SUPPORT_FAMILY_MASS_DERIVATION_V1',
        'status':'DERIVED_FROM_REAL_READER_FIT_AND_FROZEN_OPERATOR_SUPPORT__NO_TRAINING_AUTHORITY',
        'inputs':{
            'metadata_sqlite_sha256':sha256_file(metadata_sqlite),
            'support_npz_sha256':sha256_file(support_npz),
            'partition':partition,
        },
        'geometry':{
            'cells':int(total),'donors':int(donors),'operators':int(ops),'matrices':int(mats),'sources':int(sources),
            'molecular_addresses':int(states.shape[1]),'common_core_addresses':core_n,
            'measured_scalar_per_operator_min':int(scalar_n.min()),
            'measured_scalar_per_operator_median':float(np.median(scalar_n)),
            'measured_scalar_per_operator_max':int(scalar_n.max()),
            'operator_native_per_operator_min':int(native_n.min()),
            'operator_native_per_operator_median':float(np.median(native_n)),
            'operator_native_per_operator_max':int(native_n.max()),
        },
        'donor_equal_estimand':{
            'expected_measured_scalar_addresses_per_base_cell':frac_obj(expected_scalar),
            'expected_operator_native_addresses_per_base_cell':frac_obj(expected_native),
            'family_mass_weights':{
                'COMMON_CORE':frac_obj(common_weight),
                'OPERATOR_NATIVE':frac_obj(native_weight),
            },
        },
        'raw_cell_weighting_non_authority_contrast':{
            'expected_measured_scalar_addresses_per_cell':frac_obj(raw_scalar),
            'expected_operator_native_addresses_per_cell':frac_obj(raw_native),
            'COMMON_CORE_fraction_of_measured_scalar':frac_obj(raw_common_weight),
            'selection_role':'DIAGNOSTIC_ONLY__RAW_CELL_MASS_IS_NOT_THE_DONOR_EQUAL_ESTIMAND',
        },
        'operator_support':operator_rows,
        'rules':{
            'family_weight_rule':'weight family losses by expected eligible address mass under p_i = 1/(D*n_donor), not raw cell frequency',
            'common_core_definition':'MEASURED_SCALAR in every authenticated operator',
            'operator_native_definition':'MEASURED_SCALAR in the cell operator and outside COMMON_CORE',
            'rederive_on_population_or_support_change':True,
            'synthetic_data_may_set_numeric_authority':False,
            'checkpoint_outcomes_may_tune_family_weights':False,
        },
        'synthetic_data_used':False,
        'pathology_used':False,
        'checkpoint_outcomes_used':False,
        'training_authorized':False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--metadata-sqlite', type=Path, required=True)
    p.add_argument('--support-npz', type=Path, required=True)
    p.add_argument('--partition', default='reader_fit')
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    out=derive(a.metadata_sqlite,a.support_npz,a.partition)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
