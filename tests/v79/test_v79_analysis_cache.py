"""The compact analysis cache equals the current loader exactly (gene sample, selected counts, library, detected
features and design) and refuses a shard whose bytes differ from the authority. Synthetic shards only."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import build_v79_analysis_cache as C  # noqa: E402
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402


def make_world(tmp: Path, seed=0):
    rng = np.random.default_rng(seed)
    root = tmp / "cache"
    root.mkdir()
    labels = list(FW.CLASS_MAP)
    rows, auth = [], {}
    for i, (stem, src) in enumerate([("aaaa", "HVS"), ("bbbb", "SEA_AD"), ("cccc", "NPH52")]):
        n = 60 + 10 * i
        lam = np.zeros(DA.N_ADDRESSES)
        lam[:600] = rng.gamma(0.4, 1.0, 600)
        X = sparse.csr_matrix(rng.poisson(lam[None, :] * rng.uniform(0.5, 1.5, (n, 1))).astype(np.float32))
        np.savez(root / f"{stem}.counts.npz", data=X.data, indices=X.indices, indptr=X.indptr, shape=np.array(X.shape))
        np.savez(root / f"{stem}.meta.npz", cell_id=np.array([f"{stem}_{j}" for j in range(n)]),
                 donor_id=np.array([f"d{src}{j % 5}" for j in range(n)]),
                 broad_cell_class=np.array([labels[j % len(labels)] for j in range(n)]),
                 source_library=np.asarray(X.sum(1)).ravel().astype(np.int64) + 5)
        rows.append(dict(stem=stem, operator_index=i, source=src, matrix_id=f"{src}::{stem}"))
        for suffix in ("counts", "meta"):
            b = (root / f"{stem}.{suffix}.npz").read_bytes()
            auth[f"{stem}.{suffix}.npz"] = dict(sha256=hashlib.sha256(b).hexdigest(), bytes=len(b))
    bridge = tmp / "bridge.json"
    bridge.write_text(json.dumps(dict(rows=rows)), encoding="utf-8")
    authority = tmp / "authority.json"
    authority.write_text(json.dumps(dict(files=auth)), encoding="utf-8")
    return root, bridge, authority


def test_cache_equals_the_current_loader(tmp_path):
    root, bridge, authority = make_world(tmp_path)
    historical_design = DA.design_indices(FW.load_cell_design(root, bridge))
    for g in (10, 20):
        arrays, meta = C.build(root, bridge, authority, g)
        checks = C.verify_against_loader(arrays, root, bridge, g)
        assert all(checks.values()) and meta["shard_files_verified"] == 6
        assert arrays["counts_selected"].shape == (210, g) and len(arrays["gene_address_index"]) == g
        for name, old_name in (("cls", "cls"), ("src", "src"), ("op", "op"), ("donor", "donor"), ("dk", "dk"),
                               ("log_lib_centered", "log_lib_centered")):
            assert np.array_equal(arrays[name], historical_design[old_name])


def test_build_never_assembles_a_global_sparse_matrix(tmp_path, monkeypatch):
    root, bridge, authority = make_world(tmp_path)

    def forbidden_vstack(*args, **kwargs):
        raise AssertionError("streaming cache must not scipy.sparse.vstack all shards")

    monkeypatch.setattr(sparse, "vstack", forbidden_vstack)
    arrays, meta = C.build(root, bridge, authority, 10)
    assert arrays["counts_selected"].shape == (210, 10)
    assert meta["streaming_passes"] == 2
    assert meta["max_count_shards_resident"] == 1


def test_build_does_not_reread_metadata_after_authentication(tmp_path, monkeypatch):
    root, bridge, authority = make_world(tmp_path)

    def forbidden_design(*args, **kwargs):
        raise AssertionError("build must derive design from the authenticated metadata bytes already read")

    monkeypatch.setattr(FW, "load_cell_design", forbidden_design)
    arrays, meta = C.build(root, bridge, authority, 10)
    assert len(arrays["donor"]) == 210
    assert meta["metadata_from_authenticated_bytes"] is True


def test_verification_does_not_reload_the_global_matrix(tmp_path, monkeypatch):
    root, bridge, authority = make_world(tmp_path)
    arrays, _ = C.build(root, bridge, authority, 10)

    def forbidden_loader(*args, **kwargs):
        raise AssertionError("verification must stream shards, not DA.load_counts/vstack the full matrix")

    monkeypatch.setattr(DA, "load_counts", forbidden_loader)
    checks = C.verify_against_loader(arrays, root, bridge, 10)
    assert all(checks.values())


def test_a_tampered_shard_is_refused(tmp_path):
    root, bridge, authority = make_world(tmp_path)
    p = root / "bbbb.counts.npz"
    b = bytearray(p.read_bytes())
    b[-1] ^= 1
    p.write_bytes(bytes(b))
    with pytest.raises(SystemExit):
        C.build(root, bridge, authority, 10)
