from __future__ import annotations
import json
from pathlib import Path
import pytest, torch
from sea_ad_jepa.v5.data_first_geometry import (
    evidence_telemetry, ragged_relational_support, pack_valid_tokens,
    operator_homogeneous_microbatch_plan, mean_loss_weight,
)
ROOT=Path(__file__).resolve().parents[1]

def test_profile_is_full_reader_fit_not_mechanics_geometry():
    p=json.loads((ROOT/'docs/agent/READER_FIT_DATA_GEOMETRY_PROFILE_V1.json').read_text())
    assert p['reader_fit']['cells']==4_553_407
    assert p['reader_fit']['donors']==104
    assert p['reader_fit']['operators']==42
    g=p['reader_fit']['donor_operator_groups']
    assert g['groups']==1400
    assert g['cells_per_group_quantiles']['0']==1.0
    assert g['cells_per_group_quantiles']['0.5']==228.0
    assert g['cells_per_group_quantiles']['1']==42209.0
    assert g['group_fraction_ge_3'] > .97
    assert g['cell_fraction_in_groups_ge_3'] > .99998
    m=p['mechanics_3292_comparison']
    assert m['donor_operator_groups']==1400
    assert m['cells_per_group_quantiles']['1']==5.0
    assert m['group_fraction_lt_3'] > .72

def test_evidence_reports_support_and_universe_separately():
    h=evidence_telemetry(measured_count=18736,hidden_count=int(18736*.4),vocabulary_size=41238)
    s=evidence_telemetry(measured_count=35076,hidden_count=int(35076*.4),vocabulary_size=41238)
    assert h['visible_fraction_within_measured']==pytest.approx(s['visible_fraction_within_measured'],abs=1e-4)
    assert h['visible_fraction_of_universe'] < .28
    assert s['visible_fraction_of_universe'] > .51

def test_ragged_relational_support_does_not_require_equal_groups():
    r=ragged_relational_support(['d0','d0','d0','d1','d1','d2'],['o0']*6)
    assert r['groups_total']==3
    assert r['groups_estimable']==1
    assert r['cells_in_estimable_groups']==3
    assert r['cells_not_in_estimable_groups']==3

def test_packing_preserves_exact_valid_canonical_ids():
    x=torch.tensor([[1.,2.,3.,4.],[5.,6.,7.,8.]])
    m=torch.tensor([[True,False,True,False],[False,True,False,True]])
    p=pack_valid_tokens(x,m)
    assert p.canonical_gene_ids.tolist()==[[0,2],[1,3]]
    assert p.expression.tolist()==[[1.,3.],[6.,8.]]

def test_operator_packing_uses_support_budget_without_changing_cell_set():
    ops=[0,1,0,1,1,0]
    plan=operator_homogeneous_microbatch_plan(ops,{0:10,1:25},max_teacher_tokens_per_microbatch=50)
    assert plan==((0,2,5),(1,3),(4,))
    assert sorted(i for b in plan for i in b)==list(range(6))

def test_operator_packing_has_no_implicit_budget():
    with pytest.raises(TypeError):
        operator_homogeneous_microbatch_plan([0],{0:10}) # type: ignore[call-arg]

def test_accumulated_local_means_can_form_exact_global_mean():
    assert mean_loss_weight(local_elements=30,total_elements=100)==pytest.approx(.3)
    assert mean_loss_weight(local_elements=70,total_elements=100)==pytest.approx(.7)

def test_full_group_triplet_capacity_is_computed_without_enumeration():
    from sea_ad_jepa.v5.data_first_geometry import anchored_triplet_capacity
    assert anchored_triplet_capacity(2)==0
    assert anchored_triplet_capacity(3)==3
    assert anchored_triplet_capacity(16)==1680
    assert anchored_triplet_capacity(228)==5_848_428
    assert anchored_triplet_capacity(42_209)==37_597_098_110_352


def test_singleton_null_stratum_is_not_estimable_without_killing_other_strata():
    from sea_ad_jepa.v5.data_first_geometry import partial_fine_derangement
    ids=torch.tensor([0,0,1,2,2,2],dtype=torch.int64)
    r=partial_fine_derangement(ids,seed=19)
    perm=r['permutation']; ok=r['estimable_mask']
    assert ok.tolist()==[True,True,False,True,True,True]
    assert perm[2].item()==-1
    assert torch.equal(ids[perm[ok]],ids[ok])
    assert not bool((perm[ok]==torch.arange(len(ids))[ok]).any())

def test_profile_binds_portable_bundle_members_and_stays_reader_fit_only():
    text=(ROOT/'docs/agent/READER_FIT_DATA_GEOMETRY_PROFILE_V1.json').read_text()
    p=json.loads(text)
    assert p['calibration_bundle_sha256']=='07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444'
    assert p['authority_inputs']['metadata_sqlite']['bundle_member']=='metadata/foundation_metadata_rows.sqlite'
    assert '/mnt/data/' not in text
    assert 'reader_validation' not in text
    assert 'reader_oracle' not in text

def test_uniform_scientific_weights_reduce_exactly_to_legacy_block_mse():
    from sea_ad_jepa.v5.data_first_geometry import weighted_block_jepa_loss
    torch.manual_seed(12)
    p=torch.randn(5,4,7)
    t=torch.randn(5,4,7)
    w=torch.ones(5)
    assert torch.allclose(weighted_block_jepa_loss(p,t,w),torch.nn.functional.mse_loss(p,t),atol=1e-7,rtol=1e-7)


def test_scientific_weighted_loss_is_invariant_to_unequal_compute_partition():
    from sea_ad_jepa.v5.data_first_geometry import weighted_block_jepa_loss, weighted_loss_partition_weight
    torch.manual_seed(13)
    p=torch.randn(7,3,5); t=torch.randn(7,3,5)
    w=torch.tensor([0.2,2.0,0.5,4.0,1.0,3.0,0.1])
    full=weighted_block_jepa_loss(p,t,w)
    idx=[slice(0,2),slice(2,5),slice(5,7)]
    recon=0.0
    total=float(w.sum())
    for s in idx:
        local=weighted_block_jepa_loss(p[s],t[s],w[s])
        recon=recon+local*weighted_loss_partition_weight(local_weight_mass=float(w[s].sum()),total_weight_mass=total)
    assert torch.allclose(full,recon,atol=1e-7,rtol=1e-7)


def test_scientific_estimand_probability_has_no_implicit_sampler_or_default():
    from sea_ad_jepa.v5.data_first_geometry import scientific_target_cell_probability, importance_weight_from_probabilities
    n=1000; nd=100; d=10; ds=4; s=3
    assert scientific_target_cell_probability('cell_uniform',total_cells=n,donor_cells=nd,total_donors=d,donors_in_source=ds,total_sources=s)==pytest.approx(1/n)
    assert scientific_target_cell_probability('donor_uniform',total_cells=n,donor_cells=nd,total_donors=d,donors_in_source=ds,total_sources=s)==pytest.approx(1/(d*nd))
    assert scientific_target_cell_probability('source_donor_uniform',total_cells=n,donor_cells=nd,total_donors=d,donors_in_source=ds,total_sources=s)==pytest.approx(1/(s*ds*nd))
    with pytest.raises(ValueError,match='unsupported scientific estimand'):
        scientific_target_cell_probability('auto',total_cells=n,donor_cells=nd,total_donors=d,donors_in_source=ds,total_sources=s)
    assert importance_weight_from_probabilities(target_probability=.02,proposal_probability=.01)==pytest.approx(2.0)


def test_full_reader_estimand_analysis_is_descriptive_and_selects_nothing():
    p=json.loads((ROOT/'docs/agent/READER_FIT_SCIENTIFIC_ESTIMAND_ANALYSIS_V1.json').read_text())
    assert p['population']=='reader_fit' and p['reader_fit_cells']==4_553_407 and p['reader_fit_donors']==104
    assert p['selected_estimand'] is None and p['selected_proposal_sampler'] is None
    cell=p['candidate_estimands']['cell_uniform']
    donor=p['candidate_estimands']['donor_uniform']
    sd=p['candidate_estimands']['source_donor_uniform']
    assert cell['target_source_mass']['SEA_AD'] > .90
    assert donor['target_source_mass']['SEA_AD']==pytest.approx(46/104)
    assert sd['target_source_mass']['HVS']==pytest.approx(1/3)
    assert donor['if_proposed_cell_uniform']['importance_weight_max_to_min_ratio'] > 2000
    assert donor['if_proposed_cell_uniform']['effective_sample_size_fraction'] < .10
    assert sd['if_proposed_cell_uniform']['effective_sample_size_fraction'] < .04
    assert p['training_authorized'] is False and p['execution_authorized'] is False
