"""Prospective known-truth fixture worlds for frozen JEPA diagnostic evaluation.

NOT A PRODUCTION GENERATOR. No real RNA, Bayesian priors, checkpoint fitting,
teacher, EMA, protected human labels or hidden synthetic qualification worlds.
World labels are known only to these hostile tests, never to the evaluator.
"""
from __future__ import annotations

import numpy as np
import pytest

from sea_ad_jepa.evaluation.frozen_probe_v1 import FrozenProbeError, evaluate_frozen_probe


def _world(kind: str, seed: int = 20261026):
    rng=np.random.default_rng(seed)
    donors=np.repeat(np.arange(20), 80)
    n=donors.size
    source=2*(donors%2)-1
    depth=rng.normal(size=n)+.6*source
    broad, local, unused=rng.normal(size=(3,n))
    rare=(rng.random(n)<.13).astype(np.float64)
    # Nuisance baseline has the technical polynomial terms; simple biological
    # comparator observes only the broad program, not the local/rare truth.
    baseline=np.column_stack((source,depth,depth**2,source*depth,
                              broad+.15*rng.normal(size=n)))
    y=(1.4*local+3.*rare+.2*broad+2.*source+1.2*depth
       +.45*rng.normal(size=n))
    if kind=="MULTIPROGRAM":
        z=np.column_stack((broad,local,rare,local+.1*rng.normal(size=n),
                           rng.normal(size=n)))
    elif kind=="COLLAPSED":
        z=np.zeros((n,5),dtype=np.float64)
    elif kind=="NUISANCE":
        z=np.column_stack((source,depth,depth**2,source*depth,
                           rng.normal(size=n)))
    elif kind=="COMPACT":
        z=np.column_stack((local,rare))
    elif kind=="COMPACT_RARE_DROPPED":
        z=np.column_stack((local,np.zeros(n)))
    else:
        raise AssertionError("unknown planted fixture world")
    folds=[([int(d) for d in range(20) if d%5!=k],
            [int(d) for d in range(20) if d%5==k]) for k in range(5)]
    return dict(donor_ids=donors,baseline=baseline,embeddings=z,
                target=y,folds=folds,source_role="PLANTED_SYNTHETIC_FIXED",
                target_semantics="CONTINUOUS_SYNTHETIC",
                query_leakage_provenance="EXCLUDED_BY_FIXTURE_CONSTRUCTION")


def _run(kind):
    return evaluate_frozen_probe(**_world(kind))


def test_four_world_biology_vs_nuisance_and_valid_compact():
    a,b,c,d=[_run(kind) for kind in
             ("MULTIPROGRAM","COLLAPSED","NUISANCE","COMPACT")]
    assert a["authority_effect"]==b["authority_effect"]==c["authority_effect"]==d["authority_effect"]=="NONE"
    assert b["geometry"]["constant"] is True
    assert c["geometry"]["effective_rank"]>d["geometry"]["effective_rank"]
    assert d["geometry"]["constant"] is False
    # RELATIVE discrimination, not a post-hoc numeric qualification threshold.
    assert a["mean_delta_nll"]>c["mean_delta_nll"]
    assert d["mean_delta_nll"]>c["mean_delta_nll"]
    assert abs(b["mean_delta_nll"])<1e-8
    assert a["mean_delta_nll"]>0 and d["mean_delta_nll"]>0
    assert all(x["n_held_donors"]==4 for x in a["folds"])
    assert len(a["donor_rows"])==20
    assert all(x["cells"]==80 for x in a["donor_rows"])
    assert "qualified" not in a and "biological_pass" not in a

def test_rare_program_loss_detected_despite_valid_compact_geometry():
    intact=_run("COMPACT")
    dropped=_run("COMPACT_RARE_DROPPED")
    assert intact["mean_delta_nll"]>dropped["mean_delta_nll"]
    assert dropped["mean_delta_nll"]>0
    assert dropped["geometry"]["constant"] is False

def test_donor_sharing_between_fit_and_test_rejected():
    x=_world("MULTIPROGRAM")
    x["folds"][0][0].append(x["folds"][0][1][0])
    with pytest.raises(FrozenProbeError):evaluate_frozen_probe(**x)

def test_incomplete_held_donor_coverage_rejected():
    x=_world("MULTIPROGRAM")
    x["folds"]=x["folds"][:4]
    with pytest.raises(FrozenProbeError):evaluate_frozen_probe(**x)

def test_duplicate_donor_hierarchy_not_inflated_to_new_donor():
    x=_world("MULTIPROGRAM")
    x["donor_ids"]=np.arange(x["target"].shape[0])
    with pytest.raises(FrozenProbeError):evaluate_frozen_probe(**x)

def test_changed_query_provenance_fails_closed():
    x=_world("MULTIPROGRAM")
    x["query_leakage_provenance"]="INCLUDED_IN_QC_LIBRARY_SIZE"
    with pytest.raises(FrozenProbeError):evaluate_frozen_probe(**x)

def test_real_human_target_attempt_refused():
    x=_world("MULTIPROGRAM")
    x["source_role"]="READER_VALIDATION"
    with pytest.raises(FrozenProbeError):evaluate_frozen_probe(**x)

def test_invalid_target_semantics_refused_not_forced_to_gaussian():
    x=_world("MULTIPROGRAM")
    x["target_semantics"]="RAW_UMI_COUNTS"
    with pytest.raises(FrozenProbeError):evaluate_frozen_probe(**x)

def test_nonfinite_predictions_inputs_fail_closed():
    x=_world("MULTIPROGRAM")
    x["embeddings"][0,0]=float("inf")
    with pytest.raises(FrozenProbeError):evaluate_frozen_probe(**x)

def test_embedding_is_not_modified_by_readout_fitting():
    x=_world("MULTIPROGRAM")
    original=x["embeddings"].copy()
    original_base=x["baseline"].copy()
    original_target=x["target"].copy()
    _=evaluate_frozen_probe(**x)
    assert np.array_equal(x["embeddings"],original)
    assert np.array_equal(x["baseline"],original_base)
    assert np.array_equal(x["target"],original_target)

def test_deterministic_receipt_and_finite_scores():
    first=_run("MULTIPROGRAM")
    second=_run("MULTIPROGRAM")
    assert first==second
    assert np.isfinite(first["mean_delta_nll"])
    assert all(np.isfinite(row["delta_nll"]) for row in first["donor_rows"])
    assert first["fitted_encoder_updates"]==0
    assert first["fitted_ema_updates"]==0
    assert first["score_family"]=="TRAIN_ONLY_GAUSSIAN_RIDGE_CONTINUOUS_FIXTURE"

def test_nuisance_only_raw_likelihood_can_look_good_but_increment_is_trivial():
    x=_world("NUISANCE")
    controlled=evaluate_frozen_probe(**x)
    # Deliberately remove source/depth/biology control to expose raw-score trap.
    x["baseline"]=np.zeros((len(x["target"]),1),dtype=np.float64)
    uncontrolled=evaluate_frozen_probe(**x)
    assert uncontrolled["mean_delta_nll"]>controlled["mean_delta_nll"]
    assert uncontrolled["mean_delta_nll"]>0
    assert controlled["authority_effect"]=="NONE"

def test_exact_query_in_embedding_rejected_even_with_lying_fixture_label():
    x=_world("MULTIPROGRAM")
    x["embeddings"][:,0]=x["target"].copy()
    with pytest.raises(FrozenProbeError):
        evaluate_frozen_probe(**x)

def test_exact_query_in_baseline_rejected_even_with_lying_fixture_label():
    x=_world("MULTIPROGRAM")
    x["baseline"][:,1]=x["target"].copy()
    with pytest.raises(FrozenProbeError):
        evaluate_frozen_probe(**x)
