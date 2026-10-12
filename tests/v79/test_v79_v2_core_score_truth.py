from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_score_truth as T  # noqa: E402


def _contract():
    return json.loads((ROOT/"results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json").read_text(encoding="utf-8"))


def _truth_root():
    return ROOT/"results/v79/v2_core_realization_audit_freeze_v1/package/controller_truth"


def test_all_twelve_controller_truth_worlds_hash_validate_and_match_contract():
    worlds=T.load_truth_set(_truth_root(),_contract())
    assert len(worlds)==12
    assert set(worlds)=={x["name"] for x in _contract()["worlds"]["world_list"]}
    assert {w.world_index for w in worlds.values()}==set(range(12))
    assert len({w.opaque_world_id for w in worlds.values()})==12


def test_truth_world_exposes_expected_per_gene_parameter_shapes():
    worlds=T.load_truth_set(_truth_root(),_contract())
    w=worlds["Q00_BASELINE"]
    for part in ("detection","positive"):
        intercept=w.load(f"truth/{part}/intercept.npy")
        depth1=w.load(f"truth/{part}/depth1.npy")
        depth2=w.load(f"truth/{part}/depth2.npy")
        cls=w.load(f"truth/{part}/class_contrasts.npy")
        src=w.load(f"truth/{part}/source_contrasts.npy")
        donor_sd=w.load(f"truth/{part}/donor_sd.npy")
        donor=w.load(f"truth/{part}/donor_effects.npy")
        assert intercept.shape==(44,) and depth1.shape==(44,) and depth2.shape==(44,)
        assert cls.shape==(44,2) and src.shape==(44,2) and donor_sd.shape==(44,)
        assert donor.shape==(149,44)
    assert w.load("truth/positive/sigma.npy").shape==(44,)


def test_truth_manifest_only_allows_hash_bound_numpy_outputs():
    worlds=T.load_truth_set(_truth_root(),_contract())
    for w in worlds.values():
        assert all(k.endswith(".npy") for k in w.manifest["generated_outputs"])
        assert np.asarray(w.load("support.npy")).dtype==np.bool_
