from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_fit_outputs as O  # noqa: E402


def test_ppc_seed_is_fit_id_only_and_deterministic():
    a="a"*64; b="b"*64
    assert O.ppc_seed(a)==O.ppc_seed(a)
    assert O.ppc_seed(a)!=O.ppc_seed(b)
    assert 0<=O.ppc_seed(a)<=0xffffffff


def test_two_sided_mid_p_matches_frozen_definition():
    reps=np.array([0.,1.,1.,2.])
    assert O.two_sided_mid_p(1.0,reps)==1.0
    assert O.two_sided_mid_p(2.0,reps)==0.25


def test_world_z_deciles_are_fixed_before_gene_masking():
    log_lib=np.arange(20,dtype=float)
    mask=np.array([True,False]*10)
    codes=O.world_z_decile_codes(log_lib,mask,n_bins=10)
    assert len(codes)==10
    # every selected cell is assigned under boundaries derived from all 20 cells
    assert codes.min()>=0 and codes.max()<=9


def test_donor_effect_compaction_is_200_float32_draws_and_deterministic():
    donor_raw=np.arange(2*120*2,dtype=float).reshape(2,120,2)/100.0
    donor_sd=np.ones((2,120),dtype=float)*0.5
    W=np.array([[1.,0.],[0.,1.],[-1.,-1.]])
    a=O.compact_donor_effect_draws({"donor_raw":donor_raw,"donor_sd":donor_sd},W,stored_draws=200)
    b=O.compact_donor_effect_draws({"donor_raw":donor_raw,"donor_sd":donor_sd},W,stored_draws=200)
    assert a.shape==(200,3) and a.dtype==np.float32
    assert np.array_equal(a,b)


def test_detection_ppc_statistics_cover_contract_families():
    y=np.array([0,1,0,1,0,1,0,1,0,1,0,1],dtype=int)
    z=np.linspace(-2,2,len(y)); cls=np.array([0,1,2]*4); src=np.array([0]*4+[1]*4+[2]*4); donor=np.array([0]*6+[1]*6)
    stats=O.detection_statistics(y,z=z,cls=cls,src=src,donor=donor,z_bin_count=10)
    names={x["name"] for x in stats}
    assert "zero_fraction_overall" in names
    assert any(n.startswith("zero_fraction_zdecile_") for n in names)
    assert {"zero_fraction_class_0","zero_fraction_class_1","zero_fraction_class_2"} <= names
    assert {"zero_fraction_source_0","zero_fraction_source_1","zero_fraction_source_2"} <= names
    assert "sd_donor_detection_fraction" in names


def test_positive_ppc_statistics_cover_contract_families():
    ylog=np.linspace(-1,2,30); z=np.linspace(-2,2,30); donor=np.repeat(np.arange(5),6)
    stats=O.positive_statistics(ylog,z=z,donor=donor,z_bin_count=10)
    names={x["name"] for x in stats}
    assert {"mean_log_positive","variance_log_positive","q01_log_positive","q99_log_positive","sd_donor_mean_log_positive"} <= names
    assert any(n.startswith("mean_log_positive_zdecile_") for n in names)
