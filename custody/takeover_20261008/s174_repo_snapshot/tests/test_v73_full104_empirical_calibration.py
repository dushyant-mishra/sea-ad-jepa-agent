from pathlib import Path
import importlib.util
import csv
import json
import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/v64/build_v73_full104_empirical_calibration_authority.py"

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def make_population(path,B,include_forbidden=False):
    source_rows=[('SEA_AD',1260),('NPH52',72),('HVS',68)]; rows=[]; gid=0
    for source,nrows in source_rows:
        total=B.EXPECTED_SOURCES[source]; base,rem=divmod(total,nrows)
        for j in range(nrows):
            rows.append({'group_id':f'G{gid:04d}','donor_id':f'D{gid%B.EXPECTED_DONORS:03d}','source':source,
                         'operator_id':f'OP{gid%B.EXPECTED_OPERATORS:02d}','cell_count':base+(1 if j<rem else 0)}); gid+=1
    fields=['group_id','donor_id','source','operator_id','cell_count']
    if include_forbidden:
        fields.append('cell_id')
        for r in rows:r['cell_id']='FORBIDDEN'
    with open(path,'w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(rows)

def make_qc(path,B,population):
    strata=[]
    for r in population['source_operator']:
        strata.append({'source':r['source'],'operator_id':r['operator_id'],'population_n_cells':r['cell_count'],
          'sample_n_cells':1,'measured':True,'rna_library_size_quantiles':[100,200,500,1000,2000,5000,10000],
          'rna_detected_feature_quantiles':[20,30,50,70,80,90,95],
          'rna_zero_fraction_quantiles':[.1,.15,.2,.3,.4,.5,.6],'structural_missing_fraction':.12})
    path.write_text(json.dumps({'quantile_probabilities':B.QPROBS,'sampling_frame':'SYNTHETIC_TEST_FROZEN_SAMPLE',
      'population_total_cells':B.EXPECTED_CELLS,'sample_total_cells':len(strata),'strata':strata}))

def test_valid_aggregate_authority_builds_without_cell_level_data(tmp_path):
    B=load(BUILDER,'v73_cal_builder'); pop=tmp_path/'population.csv'; make_population(pop,B); p=B.read_population(pop)
    assert p['n_cells']==4553407 and p['n_groups']==1400 and p['n_donors']==104 and p['n_operators']==42
    qc=tmp_path/'qc.json'; make_qc(qc,B,p); out=B.build(pop,qc,tmp_path/'authority.json')
    assert out['status']=='QUALIFIED_AGGREGATE_AUTHORITY'; assert out['cell_level_data_exported'] is False
    assert out['real_correspondence_opened'] is False; assert out['population']['source_counts']==B.EXPECTED_SOURCES
    assert out['qc_quantiles_are_full_population_exact'] is False

def test_builder_rejects_cell_level_columns(tmp_path):
    B=load(BUILDER,'v73_cal_forbidden'); pop=tmp_path/'population.csv'; make_population(pop,B,True)
    with pytest.raises(ValueError,match='forbidden columns'):B.read_population(pop)

def test_builder_rejects_duplicate_group_identity(tmp_path):
    B=load(BUILDER,'v73_cal_dup'); pop=tmp_path/'population.csv'; make_population(pop,B)
    lines=pop.read_text().splitlines(); fields=lines[0].split(','); first=dict(zip(fields,lines[1].split(',')))
    with open(pop,'a',newline='') as fh: csv.DictWriter(fh,fieldnames=fields).writerow(first)
    with pytest.raises(ValueError,match='duplicate group_id'):B.read_population(pop)

def test_qc_requires_complete_source_operator_strata(tmp_path):
    B=load(BUILDER,'v73_cal_qc'); pop=tmp_path/'population.csv'; make_population(pop,B); p=B.read_population(pop)
    qc=tmp_path/'qc.json'; make_qc(qc,B,p); obj=json.loads(qc.read_text()); obj['strata'].pop(); obj['sample_total_cells']-=1; qc.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match='QC strata mismatch population'):B.read_qc(qc,p)

def test_structural_missingness_is_separate_from_measured_zero_fraction(tmp_path):
    B=load(BUILDER,'v73_cal_missing'); pop=tmp_path/'population.csv'; make_population(pop,B); p=B.read_population(pop)
    qc=tmp_path/'qc.json'; make_qc(qc,B,p); row=B.read_qc(qc,p)['strata'][0]
    assert 'structural_missing_fraction' in row and 'rna_zero_fraction_quantiles' in row
    assert row['structural_missing_fraction']!=row['rna_zero_fraction_quantiles']
