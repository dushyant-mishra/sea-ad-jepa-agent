from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v5'))

import td_relational_successor_observed_executor_v1 as X


def test_prepared_context_evaluates_multiple_profiles_without_reopening_observations():
    rng=np.random.default_rng(71)
    cells_per_donor=12
    donors=np.repeat([f'D{i}' for i in range(5)],cells_per_donor)
    n=len(donors)
    latent=np.tile(np.linspace(-2,2,cells_per_donor),5)
    load=rng.normal(size=512)
    base=latent[:,None]*load[None,:]+0.1*rng.normal(size=(n,512))
    measured=np.ones((n,512),dtype=bool)
    context=X.prepare_observed_relational_context(
        source='S',panel_id='P0',
        z_values=base+0.03*rng.normal(size=base.shape),
        x_values=base+0.03*rng.normal(size=base.shape),
        y_values=base+0.03*rng.normal(size=base.shape),
        z_measured=measured,x_measured=measured,y_measured=measured,
        z_feature_ids=[f'Z{i:04d}' for i in range(512)],
        x_feature_ids=[f'X{i:04d}' for i in range(512)],
        y_feature_ids=[f'Y{i:04d}' for i in range(512)],
        donor_ids=donors,operator_ids=np.array(['O']*n,dtype=object),global_rows=np.arange(n),
        source_library=np.full(n,1000.0),detected_genes=np.full(n,512,dtype=int),
    )
    assert context.n_cells==n
    primary=X.evaluate_prepared_relational_profile(
        context,profile_id='opaque-primary',focal_mask=np.ones(n,bool),neighbor_pool_mask=np.ones(n,bool),min_focal_anchors_per_donor=1,
    )
    focal=np.zeros(n,bool)
    for d in range(5): focal[d*cells_per_donor:d*cells_per_donor+6]=True
    control=X.evaluate_prepared_relational_profile(
        context,profile_id='opaque-control',focal_mask=focal,neighbor_pool_mask=np.ones(n,bool),min_focal_anchors_per_donor=1,
    )
    assert primary.profile_id=='opaque-primary'
    assert control.profile_id=='opaque-control'
    assert primary.focal_anchor_count==n
    assert control.focal_anchor_count==30
    assert primary.source==control.source=='S'
    assert primary.panel_id==control.panel_id=='P0'
