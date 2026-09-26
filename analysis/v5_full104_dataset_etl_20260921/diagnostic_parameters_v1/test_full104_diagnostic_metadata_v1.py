"""Adversarial tests for real FULL104 receipt; cloned outputs are synthetic tamper attacks.

The untampered fixture is physically produced by the exact 410MB calibration ZIP and
2.7GB SQLite, but pytest DOES NOT rerun the full physical scan on every attack.
"""
import csv,json,shutil
from pathlib import Path
import pytest
from verify_full104_metadata_receipt_v1 import OUTPUTS,verify,file_sha

SOURCE=Path(__file__).resolve().parent

@pytest.fixture
def fixture(tmp_path):
 for file in (*OUTPUTS,'OUTPUT_SHA256_MANIFEST.json'):
  shutil.copyfile(SOURCE/file,tmp_path/file)
 return tmp_path

def refresh(root):
 records=[]
 for f in sorted(OUTPUTS):
  p=root/f
  records.append({'file':f,'bytes':p.stat().st_size,'sha256':file_sha(p)})
 (root/'OUTPUT_SHA256_MANIFEST.json').write_text(json.dumps(records,indent=2)+'\n')

def mutate_csv(root,name,mutation):
 p=root/name
 with p.open(newline='') as f:rows=list(csv.DictReader(f))
 mutation(rows)
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 refresh(root)

def mutate_receipt(root,mutation):
 p=root/OUTPUTS[3];j=json.loads(p.read_text());mutation(j)
 p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n');refresh(root)

def test_authentic_source_derived_receipt_passes_independent_validator(fixture):
 d=verify(fixture)
 assert (d['donors'],d['cells'],d['groups'],d['groups_ge3'])==(104,4553407,1400,1361)

def test_raw_byte_edit_is_stopped_by_output_hash(fixture):
 p=fixture/OUTPUTS[0];p.write_bytes(p.read_bytes()+b'bad')
 with pytest.raises(ValueError,match='byte identity tampered'):verify(fixture)

def test_manifest_omitted_output_cannot_become_green(fixture):
 m=fixture/'OUTPUT_SHA256_MANIFEST.json';j=json.loads(m.read_text());j.pop();m.write_text(json.dumps(j))
 with pytest.raises(ValueError,match='manifest has missing'):verify(fixture)

def test_duplicate_donor_identity_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[0],lambda r:r[1].update(donor_id=r[0]['donor_id']))
 with pytest.raises(ValueError,match='roster duplicate'):verify(fixture)

def test_historical_small_sample_replacement_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[0],lambda r:r[0].update(fit_cells='3292'))
 with pytest.raises(ValueError,match='wrong cell scientific mass|per-cell scientific weights'):verify(fixture)

def test_wrong_per_donor_scientific_weight_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[0],lambda r:r[0].update(cell_scientific_mass_denominator='100'))
 with pytest.raises(ValueError,match='wrong cell scientific mass'):verify(fixture)

def test_source_relabeling_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[0],lambda r:r[0].update(source='FAKE_COHORT'))
 with pytest.raises(ValueError,match='group donor/source/operator spillover'):verify(fixture)

def test_heldout_or_extra_donor_injection_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[0],lambda r:r.append({**r[0],'donor_id':'FAKE_ORACLE_DONOR'}))
 with pytest.raises(ValueError,match='row count'):verify(fixture)

def test_donor_operator_group_duplicate_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[2],lambda r:r[1].update(donor_id=r[0]['donor_id'],operator_index=r[0]['operator_index'],source=r[0]['source']))
 with pytest.raises(ValueError,match='group donor/source/operator spillover'):verify(fixture)

def test_triplet_capacity_corruption_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[2],lambda r:r[0].update(triplet_capacity='7'))
 with pytest.raises(ValueError,match='relational capacity'):verify(fixture)

def test_support_zero_collapsed_into_missing_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[1],lambda r:r[0].update(collision_unresolved_addresses='100'))
 with pytest.raises(ValueError,match='support state collapse'):verify(fixture)

def test_operator_cross_source_spillover_fails_even_after_rehash(fixture):
 mutate_csv(fixture,OUTPUTS[1],lambda r:r[0].update(source='NPH52'))
 with pytest.raises(ValueError,match='group donor/source/operator spillover'):verify(fixture)

def test_provisional_mask_fraction_cannot_enter_receipt(fixture):
 mutate_receipt(fixture,lambda j:j['deferred_parameters'].update(mask_fraction=.4))
 with pytest.raises(ValueError,match='numerical parameter contamination'):verify(fixture)

def test_synthetic_rank_cannot_enter_receipt(fixture):
 mutate_receipt(fixture,lambda j:j['deferred_parameters'].update(D_shared=160))
 with pytest.raises(ValueError,match='numerical parameter contamination'):verify(fixture)

def test_false_training_authority_fails_even_after_rehash(fixture):
 mutate_receipt(fixture,lambda j:j.update(training_authorized=True))
 with pytest.raises(ValueError,match='scope promotion training_authorized'):verify(fixture)

def test_false_protected_outcome_claim_fails_even_after_rehash(fixture):
 mutate_receipt(fixture,lambda j:j.update(protected_expression_or_outcomes_opened=True))
 with pytest.raises(ValueError,match='scope promotion protected_expression_or_outcomes_opened'):verify(fixture)

def test_source_root_substitution_fails_even_after_rehash(fixture):
 mutate_receipt(fixture,lambda j:j['source_roots'].update(sqlite_member_sha256='0'*64))
 with pytest.raises(ValueError,match='source provenance root substitution'):verify(fixture)

def test_common_core_confusion_fails_even_after_rehash(fixture):
 mutate_receipt(fixture,lambda j:j['support'].update(strict_all42_operator_measured=17346))
 with pytest.raises(ValueError,match='support recurrence'):verify(fixture)

def test_sampler_capacity_cannot_inherit_historical_batch(fixture):
 mutate_receipt(fixture,lambda j:j['candidate_bound_not_execution_schedule'].update(unique_cells_per_donor_draw_without_replacement_limit=128))
 with pytest.raises(ValueError,match='wrong unique-donor capacity'):verify(fixture)

def test_cell_uniform_source_mix_cannot_be_forged_as_donor_mix(fixture):
 mutate_receipt(fixture,lambda j:j['census']['source_donor_counts'].update(SEA_AD=90))
 with pytest.raises(ValueError,match='source mass'):verify(fixture)


def test_unexpected_authority_field_fails_even_if_rehashed(fixture):
 mutate_receipt(fixture,lambda j:j.update(training_authorized_override=True))
 with pytest.raises(ValueError,match='unknown/missing authority-bearing receipt fields'):verify(fixture)

def test_alternate_fit_roster_root_fails_even_after_rehash(fixture):
 mutate_receipt(fixture,lambda j:j['source_roots'].update(**{'splits/reader_donor_split.csv_sha256':'a'*64}))
 with pytest.raises(ValueError,match='source provenance root substitution'):verify(fixture)


def test_d1_group_weights_cannot_be_replaced_with_base_jepa_weights(fixture):
 mutate_csv(fixture,OUTPUTS[2],lambda r:r[0].update(D1_P002_donor_operator_group_mass_denominator='104'))
 with pytest.raises(ValueError,match='D1 donor/operator group mass'):verify(fixture)

def test_d1_scope_cannot_be_promoted_to_qualified_rank(fixture):
 mutate_receipt(fixture,lambda j:j['D1_P002_metadata_ready'].update(qualification='D1_RANK_QUALIFIED'))
 with pytest.raises(ValueError,match='D1 scope promotion'):verify(fixture)
