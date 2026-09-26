"""Independent PR149 V2 metadata result replay from PR146 exact source CSVs."""
import csv, importlib.util, os, shutil
from fractions import Fraction
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[0] / 'independent_v2_relational_mass_replay.py'
SPEC = importlib.util.spec_from_file_location('v28_v2_replay', SCRIPT)
MOD = importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)
SOURCE = Path(os.environ.get('V28_PR146_SOURCE_DIR', '/mnt/data/full104_meta_audit'))

@pytest.fixture
def inputs(tmp_path):
    dest=tmp_path/'source';dest.mkdir()
    for n in MOD.EXPECTED_INPUTS:shutil.copyfile(SOURCE/n,dest/n)
    return dest

def test_positive_independent_104_donor_byte_identical_replay(inputs,tmp_path):
    result=MOD.replay(inputs,tmp_path/'out')
    assert result['byte_identical'] and result['donors']==104
    assert result['groups']==1400 and result['eligible_groups']==1361
    assert result['noneligible_cells']==59 and not result['training_authorized']

def test_any_source_byte_mutation_refuses_even_if_same_row_count(inputs,tmp_path):
    path=inputs/'fit104_donor_scientific_masses.csv'
    data=path.read_bytes();path.write_bytes(data.replace(b'H15.03.003',b'H15.03.004',1))
    with pytest.raises(ValueError,match='STOP_V28_V2_REPLAY_SOURCE_SHA_'):
        MOD.replay(inputs,tmp_path/'out')

def test_bad_declared_pr149_result_root_refused_not_tolerance_widened(inputs,tmp_path):
    with pytest.raises(ValueError,match='STOP_V28_V2_REPLAY_INDEPENDENT_BYTE_DIGEST_MISMATCH'):
        MOD.replay(inputs,tmp_path/'out',required_digest='0'*64)

def test_preexisting_output_directory_refused(inputs,tmp_path):
    dest=tmp_path/'out';dest.mkdir();(dest/'old.csv').write_text('NOT AN EMPTY DESTINATION')
    with pytest.raises(ValueError,match='STOP_V28_V2_REPLAY_OUTPUT_MUST_BE_EMPTY'):
        MOD.replay(inputs,dest)

def test_three_weight_laws_are_not_interchangeable(inputs,tmp_path):
    MOD.replay(inputs,tmp_path/'out')
    p=tmp_path/'out'/'FULL104_FIT104_RELATIONAL_V2_RATIONAL_MASSES.csv'
    with p.open(newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==1400
    eligible=[r for r in rows if r['eligible_anchor']=='True']
    ineligible=[r for r in rows if r['eligible_anchor']=='False']
    assert len(eligible)==1361 and len(ineligible)==39
    assert sum(int(r['group_cells']) for r in ineligible)==59
    assert all(int(r['V2_relational_group_mass_num'])==0 and int(r['base_JEPA_group_mass_num'])>0 for r in ineligible)
    assert any(Fraction(int(r['V2_relational_group_mass_num']),int(r['V2_relational_group_mass_den']))!=Fraction(int(r['D1_P002_group_mass_num']),int(r['D1_P002_group_mass_den'])) for r in eligible)

def test_pair_probability_is_conditional_not_a_triplet_sampling_weight(inputs,tmp_path):
    MOD.replay(inputs,tmp_path/'out')
    with (tmp_path/'out'/'FULL104_FIT104_RELATIONAL_V2_RATIONAL_MASSES.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    import math
    assert all(int(r['unordered_comparator_pairs_per_anchor'])==math.comb(int(r['group_cells'])-1,2) for r in rows if r['eligible_anchor']=='True')
    assert all(int(r['V2_comparator_pair_probability_num'])==0 and int(r['V2_comparator_pair_probability_den'])==1 for r in rows if r['eligible_anchor']=='False')
