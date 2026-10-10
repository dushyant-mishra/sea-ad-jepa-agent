"""V79 information firewall: denied fields and paths fail closed, only allowlisted metadata is read, every raw
class label maps to a broad class, and a synthetic-consumable artifact that carries gene, address or target
identity is refused rather than edited."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_firewall as FW  # noqa: E402


@pytest.mark.parametrize("name", ["braak_stage", "CERAD_score", "pathology_used_for_foundation_split", "APOE4",
                                  "td57b_panel", "target_rank", "scenic_edge", "nott_atac_peak", "gene_symbol",
                                  "ensembl_id", "nih_card_outcome", "disease_label", "MMSE"])
def test_denied_fields_are_refused(name):
    assert FW.denied_field(name)


@pytest.mark.parametrize("name", FW.ALLOWED_META_FIELDS + FW.ALLOWED_BRIDGE_FIELDS + FW.ALLOWED_SPLIT_COLUMNS)
def test_allowlisted_fields_are_not_denied(name):
    assert not FW.denied_field(name)


@pytest.mark.parametrize("path", ["D:/data/morabito/x.h5ad", "results/TEST/x.npz", "cache/sealed_holdout/a.npz",
                                  "results/target_discovery/td_relational/x.json", "D:/x/scenicplus/y"])
def test_denied_paths_are_refused(path):
    with pytest.raises(FW.FirewallError):
        FW.check_path(path)


def _shard(tmp_path, extra=None):
    f = tmp_path / "x.meta.npz"
    fields = dict(cell_id=np.array(["a", "b"]), donor_id=np.array(["d1", "d1"]),
                  broad_cell_class=np.array(["ExN", "Astro"]), source_library=np.array([10, 20]))
    fields.update(extra or {})
    np.savez(f, **fields)
    return f


def test_meta_reader_returns_only_allowlisted_fields(tmp_path):
    out = FW.read_meta_shard(_shard(tmp_path, {"some_other_field": np.array([1, 2])}))
    assert set(out) == set(FW.ALLOWED_META_FIELDS)


def test_meta_shard_with_a_denied_field_fails_closed(tmp_path):
    with pytest.raises(FW.FirewallError):
        FW.read_meta_shard(_shard(tmp_path, {"braak": np.array([3, 4])}))


def test_every_corrected_train_class_label_maps_to_a_broad_class():
    auth = json.loads((ROOT / "results/v77/V77_CLASS_COMPOSITION_AUTHORITY_V1.json").read_text(encoding="utf-8"))
    mapped = FW.harmonize_class(auth["class_labels"])
    assert set(mapped) == set(FW.BROAD_CLASSES)
    with pytest.raises(FW.FirewallError):
        FW.harmonize_class(["UnseenLabel"])


@pytest.mark.parametrize("bad", [{"gene": "ENSG00000141510"}, {"molecular_address_index": [1, 2]},
                                 {"panel": "TD59 panel 0"}, {"note": "target program"},
                                 {"per_gene": {"symbol": "APP"}}, {"donor_braak": 3}])
def test_scrub_refuses_identity(bad):
    with pytest.raises(FW.FirewallError):
        FW.scrub({"schema": "x", "payload": bad})


def test_scrub_accepts_identity_free_geometry():
    art = {"schema": "V79_SYNTHETIC_GEOMETRY_V1", "class_fraction_quantiles": [0.1, 0.2, 0.3],
           "t5_like_ratio_quantiles": [0.7, 0.74, 0.78], "eigen_share_top10": [0.25, 0.26]}
    assert FW.scrub(art) is art
