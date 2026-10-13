from __future__ import annotations
import numpy as np
from scripts.v79.unified_synthetic_integration_v1 import UnifiedBiologyConfig, build_unified_biology
from scripts.v79.unified_synthetic_fit_view_v1 import UnifiedObservationConfig, observe_unified_world, serialize_fit_view

def _world():
    return build_unified_biology(UnifiedBiologyConfig(n_cells=480,n_genes=48,n_donors=16), seed=19)

def test_same_world_two_measurements_preserve_biology_but_change_counts():
    w=_world(); cfg=UnifiedObservationConfig()
    a=observe_unified_world(w,cfg,seed=1); b=observe_unified_world(w,cfg,seed=2)
    assert a.world_hash == b.world_hash == w.world_hash
    assert a.counts_hash != b.counts_hash

def test_source_operator_changes_observation_not_world_truth():
    w=_world()
    a=observe_unified_world(w,UnifiedObservationConfig(source_mode="balanced"),seed=4)
    b=observe_unified_world(w,UnifiedObservationConfig(source_mode="shifted"),seed=4)
    assert a.world_hash == b.world_hash
    assert a.counts_hash != b.counts_hash

def test_support_preserves_measured_zero_vs_unmeasured():
    w=_world(); v=observe_unified_world(w,UnifiedObservationConfig(),seed=7)
    p=serialize_fit_view(v)
    values=np.asarray(p["values"]); support=np.asarray(p["support"],dtype=bool)
    assert np.any((values == 0) & support)
    assert np.any(~support)
    assert np.all(values[~support] == 0)

def test_separate_nucleus_never_claims_cell_pairing():
    w=_world(); v=observe_unified_world(w,UnifiedObservationConfig(multimodal_mode="separate_nucleus"),seed=9)
    assert all(a != b for a,b in zip(v.rna_entity_id,v.atac_entity_id))
    assert np.array_equal(v.donor_id, v.atac_donor_id)

def test_fit_payload_exposes_provenance_but_not_hidden_truth():
    w=_world(); p=serialize_fit_view(observe_unified_world(w,UnifiedObservationConfig(),seed=11))
    assert {"address_index","donor_id","source","operator","support","values","split"} <= set(p)
    forbidden={"rare_activity","rare_eligible","expected_molecular_state","candidate_mapping","recoverability","controller_truth"}
    assert forbidden.isdisjoint(p)
    donors={}
    for donor,split in zip(p["donor_id"],p["split"]):
        donors.setdefault(donor,set()).add(split)
    assert all(len(v)==1 for v in donors.values())
