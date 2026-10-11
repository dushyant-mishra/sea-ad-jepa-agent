"""Structural measurement support in the cheap exact-S174 replay (PR #286 controller ruling 6113874774).

MEASURED_SCALAR != STRUCTURALLY_UNMEASURED. A measured zero is a detection observation y=0. A structurally
unmeasured cell-gene entry (its matrix does not measure the gene's address) is outside every likelihood, metric and
permutation test. Support is resolved at operator (= Stage81A2R matrix) x gene, never collapsed to source.

Synthetic arrays only. Unmeasured entries are filled with impossible sentinels to prove they are never read: changing
the sentinel while the mask stays fixed must change no output.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import build_v79_structural_support as B  # noqa: E402
import run_v79_s174_structure_replay as R  # noqa: E402

REPLAY = ROOT / "scripts" / "v79" / "run_v79_s174_structure_replay.py"
V3_REPLAY = ROOT / "tests" / "v79" / "fixtures" / "run_v79_s174_structure_replay_v3_02fb78c3.py"
V3_REPLAY_SHA256 = "cf01e84f9518a0d2cd875a29a64d49c38593507ad5c31ada4ea5bc47c7b74a20"  # git blob 194a1ecd at 02fb78c3
OPS_BY_SOURCE = {0: (0, 1), 1: (2, 3, 4), 2: (5, 6)}       # source 1 is NPH52-like: several matrices
ADDRESSES = np.array([101, 102, 103, 104], dtype=np.int64)
CLEAN_GENE, FULL_ABSENT_GENE, PARTIAL_GENE, ZERO_RICH_GENE = 0, 1, 2, 3


def _support_matrix() -> np.ndarray:
    m = np.ones((7, 4), dtype=bool)
    m[[2, 3, 4], FULL_ABSENT_GENE] = False          # gene 1 fully unmeasured in source 1
    m[3, PARTIAL_GENE] = False                       # gene 2 unmeasured only in matrix 3 of source 1
    return m


def _design():
    rng = np.random.default_rng(7)
    donor = np.repeat(np.arange(18), 24)
    src = np.repeat(np.arange(3), 6)[donor]
    within = np.tile(np.arange(24), 18)
    op = np.array([OPS_BY_SOURCE[s][w % len(OPS_BY_SOURCE[s])] for s, w in zip(src, within)], dtype=np.int64)
    cls = (within % 3).astype(np.int64)
    depth = rng.normal(size=len(donor))
    return dict(donor=donor, src=src, op=op, cls=cls, depth=depth, rng=rng)


def _clean_counts(d) -> np.ndarray:
    rng = d["rng"]
    cls, depth, donor = d["cls"], d["depth"], d["donor"]
    du = rng.normal(scale=0.4, size=(18, 4))
    eta = (np.array([-0.2, 0.3, -0.5, -1.6])[None, :] + 0.7 * depth[:, None] + 1.1 * (cls[:, None] == 1)
           - 0.9 * (cls[:, None] == 2) + du[donor])
    det = rng.uniform(size=eta.shape) < 1 / (1 + np.exp(-eta))
    mag = np.exp(0.8 + 0.25 * depth[:, None] + 0.5 * (cls[:, None] == 1) + rng.normal(scale=0.3, size=eta.shape))
    counts = (det * np.maximum(1, np.rint(mag))).astype(np.int32)
    cellmask = _support_matrix()[d["op"]]            # operator level == row index in this fixture
    counts[~cellmask] = 0                            # honest cache: an unmeasured entry is stored as 0
    return counts


def _write_cache(tmp: Path, name: str, counts: np.ndarray, d, prevalence: np.ndarray) -> tuple[Path, Path]:
    npz = tmp / f"{name}.npz"
    n = len(d["donor"])
    np.savez(npz, counts_selected=counts, gene_address_index=ADDRESSES, prevalence_selected=prevalence,
             library_cached=np.full(n, 1000), n_detected=np.full(n, 100), source_library=np.full(n, 1000),
             cls=d["cls"], src=d["src"], op=d["op"], donor=d["donor"], dk=d["donor"] * 3 + d["cls"],
             log_lib_centered=d["depth"])
    rec = tmp / f"{name}.receipt.json"
    rec.write_text(json.dumps({"schema": "V79_ANALYSIS_CACHE_RECEIPT_V2", "npz": npz.name,
                               "npz_sha256": hashlib.sha256(npz.read_bytes()).hexdigest(), "streaming_passes": 2,
                               "max_count_shards_resident": 1, "global_sparse_assembly": False}), encoding="utf-8")
    return npz, rec


def _write_support(tmp: Path, name: str, npz: Path, measured: np.ndarray) -> tuple[Path, Path]:
    out = tmp / f"{name}.support.npz"
    rec = B.write_support(out, measured, np.arange(7, dtype=np.int64), ADDRESSES,
                          cache_npz_sha256=hashlib.sha256(npz.read_bytes()).hexdigest(),
                          provenance={"fixture": "synthetic"})
    return out, rec


@pytest.fixture()
def world(tmp_path):
    d = _design()
    counts = _clean_counts(d)
    prevalence = (counts > 0).mean(0)                # the cache's frozen all-cell panel covariate
    cellmask = _support_matrix()[d["op"]]
    return dict(tmp=tmp_path, d=d, counts=counts, prevalence=prevalence, cellmask=cellmask)


def _poisoned(w, sentinel) -> np.ndarray:
    c = w["counts"].copy()
    c[~w["cellmask"]] = sentinel
    return c


def _run_replay(w, name, counts, measured=None, extra=(), script=REPLAY, with_support=True):
    npz, rec = _write_cache(w["tmp"], name, counts, w["d"], w["prevalence"])
    out = w["tmp"] / f"{name}.replay.json"
    cmd = [sys.executable, str(script), str(npz), str(rec), str(out), "--genes", "4", "--support-genes", "4",
           "--permutations", "9", *extra]
    if with_support:
        s_npz, s_rec = _write_support(w["tmp"], name, npz, _support_matrix() if measured is None else measured)
        cmd += ["--support", str(s_npz), "--support-record", str(s_rec)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r, out


def _scientific(res: dict) -> str:
    """Everything except byte provenance (cache, receipt and support-file hashes legitimately differ)."""
    res = dict(res)
    for k in ("cache_sha256", "receipt_sha256", "structural_support"):
        res.pop(k, None)
    return json.dumps(res, sort_keys=True)


def _data(w, counts=None):
    npz, rec = _write_cache(w["tmp"], "direct", w["counts"] if counts is None else counts, w["d"], w["prevalence"])
    return R.load_compact_cache(npz, rec), npz


# --------------------------------------------------------------------------------------------- A measured zero
def test_measured_zero_enters_detection_and_unmeasured_never_does(world):
    data, npz = _data(world)
    s_npz, s_rec = _write_support(world["tmp"], "a", npz, _support_matrix())
    support = R.load_structural_support(s_npz, s_rec, data, hashlib.sha256(npz.read_bytes()).hexdigest())
    m = R.gene_measured_mask(data, support, PARTIAL_GENE)
    c = data["counts_selected"][:, PARTIAL_GENE]
    measured_zero = np.where(m & (c == 0))[0]
    unmeasured = np.where(~m)[0]
    assert measured_zero.size and unmeasured.size
    assert m[measured_zero[0]] and not m[unmeasured[0]]
    det = R.evaluate_detection_gene(data, PARTIAL_GENE, 3, R.SEED, measured=m)
    for model in R.MODELS:
        assert det["models"][model]["n_test_predictions"] == int(m.sum())     # measured zeros included, unmeasured not
    assert det["prevalence"] == float((c[m] > 0).mean())
    poisoned = data["counts_selected"].copy()
    poisoned[~world["cellmask"]] = 57                                          # a plausible-looking positive count
    pdata = dict(data, counts_selected=poisoned)
    pos = R.evaluate_positive_gene(pdata, PARTIAL_GENE, 3, R.SEED, measured=m)
    assert pos["n_positive"] == int(((c > 0) & m).sum())
    assert pos == R.evaluate_positive_gene(data, PARTIAL_GENE, 3, R.SEED, measured=m)


# ----------------------------------------------------------------------------------- B fully unmeasured source
def test_fully_unmeasured_source_is_excluded_not_counted_as_zero_prevalence(world):
    data, npz = _data(world)
    s_npz, s_rec = _write_support(world["tmp"], "b", npz, _support_matrix())
    support = R.load_structural_support(s_npz, s_rec, data, hashlib.sha256(npz.read_bytes()).hexdigest())
    m = R.gene_measured_mask(data, support, FULL_ABSENT_GENE)
    assert not m[data["src"] == 1].any() and m[data["src"] != 1].all()
    table = R.measured_observation_table(data, FULL_ABSENT_GENE, m)
    assert table["by_source"]["1"]["n_measured"] == 0
    assert table["by_source"]["1"]["prevalence_measured"] is None              # undefined, never 0.0
    assert table["measured_sources"] == 2
    outs = []
    for fill in (0, 3, -5):
        c = data["counts_selected"].copy()
        c[(data["src"] == 1), FULL_ABSENT_GENE] = fill
        dd = dict(data, counts_selected=c)
        outs.append(json.dumps([R.evaluate_detection_gene(dd, FULL_ABSENT_GENE, 3, R.SEED, measured=m),
                                R.evaluate_positive_gene(dd, FULL_ABSENT_GENE, 3, R.SEED, measured=m),
                                R.residual_support_for_gene(dd, FULL_ABSENT_GENE, R.SEED, 9, measured=m)],
                               sort_keys=True))
    assert outs[0] == outs[1] == outs[2]


# ----------------------------------------------------------------------------------- C partial matrix support
def test_partial_support_is_resolved_per_matrix_not_per_source(world):
    data, npz = _data(world)
    s_npz, s_rec = _write_support(world["tmp"], "c", npz, _support_matrix())
    support = R.load_structural_support(s_npz, s_rec, data, hashlib.sha256(npz.read_bytes()).hexdigest())
    m = R.gene_measured_mask(data, support, PARTIAL_GENE)
    s1 = data["src"] == 1
    assert m[s1].any() and not m[s1].all()                                     # not collapsed to source level
    assert not m[data["op"] == 3].any()
    assert m[(data["op"] == 2) | (data["op"] == 4)].all()
    np.testing.assert_array_equal(m, _support_matrix()[data["op"], PARTIAL_GENE])
    table = R.measured_observation_table(data, PARTIAL_GENE, m)
    assert 0 < table["by_source"]["1"]["n_measured"] < table["by_source"]["1"]["n_cells"]


def test_operator_levels_are_matched_by_value_not_position(world):
    data, npz = _data(world)
    perm = np.array([3, 0, 6, 1, 5, 2, 4], dtype=np.int64)                     # support rows in a shuffled order
    out = world["tmp"] / "perm.support.npz"
    rec = B.write_support(out, _support_matrix()[perm], perm, ADDRESSES,
                          cache_npz_sha256=hashlib.sha256(npz.read_bytes()).hexdigest(), provenance={})
    support = R.load_structural_support(out, rec, data, hashlib.sha256(npz.read_bytes()).hexdigest())
    np.testing.assert_array_equal(R.gene_measured_mask(data, support, PARTIAL_GENE),
                                  _support_matrix()[data["op"], PARTIAL_GENE])


# ------------------------------------------------------------------------------ D/E poison sentinels, entrypoint
def test_poison_sentinel_replay_completes_with_identical_legitimate_metrics(world):
    r0, out0 = _run_replay(world, "clean", world["counts"])
    r1, out1 = _run_replay(world, "poison_neg", _poisoned(world, -999))
    assert r0.returncode == 0, r0.stderr[-3000:]
    assert r1.returncode == 0, r1.stderr[-3000:]
    a, b = json.loads(out0.read_text(encoding="utf-8")), json.loads(out1.read_text(encoding="utf-8"))
    assert _scientific(a) == _scientific(b)


def test_changing_the_sentinel_with_the_same_mask_changes_nothing(world):
    r1, out1 = _run_replay(world, "poison_a", _poisoned(world, -999))
    r2, out2 = _run_replay(world, "poison_b", _poisoned(world, np.iinfo(np.int32).max))
    assert r1.returncode == 0 and r2.returncode == 0, (r1.stderr[-2000:], r2.stderr[-2000:])
    assert _scientific(json.loads(out1.read_text(encoding="utf-8"))) == \
        _scientific(json.loads(out2.read_text(encoding="utf-8")))


def test_a_sentinel_on_a_measured_entry_is_refused(world):
    c = world["counts"].copy()
    i = int(np.where(world["cellmask"][:, CLEAN_GENE])[0][0])
    c[i, CLEAN_GENE] = -999                                                     # mask says measured: a real read
    r, _ = _run_replay(world, "poison_read", c)
    assert r.returncode != 0
    assert "STOP" in (r.stderr + r.stdout)


def test_the_replay_refuses_to_run_without_structural_support(world):
    r, _ = _run_replay(world, "nosupport", world["counts"], with_support=False)
    assert r.returncode != 0


def test_support_bound_to_another_cache_is_refused(world):
    npz_a, rec_a = _write_cache(world["tmp"], "cache_a", world["counts"], world["d"], world["prevalence"])
    other = world["counts"].copy(); other[0, 0] = other[0, 0] + 1
    npz_b, _ = _write_cache(world["tmp"], "cache_b", other, world["d"], world["prevalence"])
    s_npz, s_rec = _write_support(world["tmp"], "bound_to_b", npz_b, _support_matrix())
    data = R.load_compact_cache(npz_a, rec_a)
    with pytest.raises(SystemExit, match="STOP"):
        R.load_structural_support(s_npz, s_rec, data, hashlib.sha256(npz_a.read_bytes()).hexdigest())


def test_the_masked_replay_reports_measured_observations_and_undefined_estimands(world):
    r, out = _run_replay(world, "report", world["counts"])
    assert r.returncode == 0, r.stderr[-3000:]
    res = json.loads(out.read_text(encoding="utf-8"))
    assert res["schema"] == "V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED"
    ss = res["structural_support"]
    assert ss["entries_unmeasured_in_replay_panel"] == int((~world["cellmask"]).sum())
    by_gene = {g["gene_position"]: g for g in res["per_gene_detection"]}
    assert by_gene[FULL_ABSENT_GENE]["measured_observations"]["measured_sources"] == 2
    assert by_gene[CLEAN_GENE]["measured_observations"]["n_measured"] == len(world["counts"])
    assert sorted(res["replay_genes_affected_by_support"]) == [FULL_ABSENT_GENE, PARTIAL_GENE]
    assert res["undefined_estimands"] == []                                    # every gene keeps >= 2 measured sources


# ------------------------------------------------------------------------------- F clean-data equivalence to V3
def test_all_measured_support_reproduces_the_v3_replay_exactly(world):
    assert hashlib.sha256(V3_REPLAY.read_bytes()).hexdigest() == V3_REPLAY_SHA256
    clean = world["counts"].copy()
    clean[~world["cellmask"]] = 0                    # irrelevant here: every entry is declared measured below
    r_old, out_old = _run_replay(world, "v3", clean, script=V3_REPLAY, with_support=False)
    r_new, out_new = _run_replay(world, "v4_all", clean, measured=np.ones((7, 4), dtype=bool))
    assert r_old.returncode == 0, r_old.stderr[-3000:]
    assert r_new.returncode == 0, r_new.stderr[-3000:]
    old, new = json.loads(out_old.read_text(encoding="utf-8")), json.loads(out_new.read_text(encoding="utf-8"))
    for key in ("panel_positions_internal", "support_panel_positions_internal", "detection_summary",
                "positive_lognormal_summary", "random_effect_support", "operator_increment_robustness"):
        assert new[key] == old[key], key
    for key in ("per_gene_detection", "per_gene_positive", "per_gene_random_effect_support"):
        assert len(new[key]) == len(old[key])
        for gn, go in zip(new[key], old[key]):
            assert {k: gn[k] for k in go} == go, key


# ------------------------------------------------------------------------------------------------ builder
def _authority_csv(path: Path, rows) -> Path:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
        fh.write("matrix_id,source_dataset_id,molecular_address_index,molecular_address_id,identity_class,"
                 "measured_address,measurement_status,measured_zero_distinct_from_unmeasured\n")
        for mid, addr, measured, status in rows:
            fh.write(f"{mid},X,{addr},ENSG{addr},current_exact,{measured},{status},True\n")
    return path


def _authority_rows(measured: np.ndarray):
    rows = []
    for op in range(7):
        for g, addr in enumerate(ADDRESSES):
            ok = bool(measured[op, g])
            rows.append((f"M{op}", int(addr), str(ok),
                         "addressable_measured_zero_or_nonzero_at_runtime" if ok else "structurally_unmeasured"))
    rows.append(("M9", 999, "True", "addressable_measured_zero_or_nonzero_at_runtime"))   # unrelated rows are ignored
    return rows


def _bridge(path: Path, op_to_matrix) -> Path:
    path.write_text(json.dumps({"rows": [{"operator_index": op, "matrix_id": mid, "source": "S", "stem": f"s{op}"}
                                         for op, mid in op_to_matrix]}), encoding="utf-8")
    return path


def _pins(npz, bridge, authority):
    return {"cache": hashlib.sha256(npz.read_bytes()).hexdigest(), "bridge": hashlib.sha256(bridge.read_bytes()).hexdigest(),
            "authority": hashlib.sha256(authority.read_bytes()).hexdigest()}


def test_builder_reproduces_the_operator_by_gene_support_and_binds_the_cache(world):
    npz, rec = _write_cache(world["tmp"], "bcache", world["counts"], world["d"], world["prevalence"])
    bridge = _bridge(world["tmp"] / "bridge.json", [(op, f"M{op}") for op in range(7)])
    auth = _authority_csv(world["tmp"] / "auth.csv.gz", _authority_rows(_support_matrix()))
    out = world["tmp"] / "built.support.npz"
    record = B.build(npz, rec, bridge, auth, out, pins=_pins(npz, bridge, auth))
    with np.load(out, allow_pickle=False) as z:
        np.testing.assert_array_equal(z["measured_op_gene"], _support_matrix())
        np.testing.assert_array_equal(z["operator_levels"], np.arange(7))
    r = json.loads(record.read_text(encoding="utf-8"))
    assert r["cache_npz_sha256"] == hashlib.sha256(npz.read_bytes()).hexdigest()
    assert r["nonzero_counts_on_unmeasured_entries"] == 0
    assert r["genes_partially_unmeasured_within_a_source"] == 1
    assert r["genes_fully_unmeasured_in_a_source"] == 1


def test_builder_refuses_wrong_input_hashes(world):
    npz, rec = _write_cache(world["tmp"], "bcache", world["counts"], world["d"], world["prevalence"])
    bridge = _bridge(world["tmp"] / "bridge.json", [(op, f"M{op}") for op in range(7)])
    auth = _authority_csv(world["tmp"] / "auth.csv.gz", _authority_rows(_support_matrix()))
    pins = _pins(npz, bridge, auth); pins["authority"] = "0" * 64
    with pytest.raises(SystemExit, match="STOP"):
        B.build(npz, rec, bridge, auth, world["tmp"] / "x.npz", pins=pins)


def test_builder_refuses_a_missing_support_pair_instead_of_assuming_measured(world):
    npz, rec = _write_cache(world["tmp"], "bcache", world["counts"], world["d"], world["prevalence"])
    bridge = _bridge(world["tmp"] / "bridge.json", [(op, f"M{op}") for op in range(7)])
    rows = [r for r in _authority_rows(_support_matrix()) if not (r[0] == "M4" and r[1] == 103)]
    auth = _authority_csv(world["tmp"] / "auth.csv.gz", rows)
    with pytest.raises(SystemExit, match="STOP"):
        B.build(npz, rec, bridge, auth, world["tmp"] / "x.npz", pins=_pins(npz, bridge, auth))


def test_builder_refuses_a_status_that_contradicts_the_measured_flag(world):
    npz, rec = _write_cache(world["tmp"], "bcache", world["counts"], world["d"], world["prevalence"])
    bridge = _bridge(world["tmp"] / "bridge.json", [(op, f"M{op}") for op in range(7)])
    rows = _authority_rows(_support_matrix())
    rows[0] = (rows[0][0], rows[0][1], "True", "structurally_unmeasured")
    auth = _authority_csv(world["tmp"] / "auth.csv.gz", rows)
    with pytest.raises(SystemExit, match="STOP"):
        B.build(npz, rec, bridge, auth, world["tmp"] / "x.npz", pins=_pins(npz, bridge, auth))


def test_builder_refuses_an_operator_bridged_to_two_matrices(world):
    npz, rec = _write_cache(world["tmp"], "bcache", world["counts"], world["d"], world["prevalence"])
    bridge = _bridge(world["tmp"] / "bridge.json", [(op, f"M{op}") for op in range(7)] + [(3, "M5")])
    auth = _authority_csv(world["tmp"] / "auth.csv.gz", _authority_rows(_support_matrix()))
    with pytest.raises(SystemExit, match="STOP"):
        B.build(npz, rec, bridge, auth, world["tmp"] / "x.npz", pins=_pins(npz, bridge, auth))


def test_builder_refuses_a_nonzero_count_on_an_unmeasured_entry(world):
    c = world["counts"].copy()
    i = int(np.where(~world["cellmask"][:, FULL_ABSENT_GENE])[0][0])
    c[i, FULL_ABSENT_GENE] = 4                       # the cache contradicts the authority
    npz, rec = _write_cache(world["tmp"], "bcache", c, world["d"], world["prevalence"])
    bridge = _bridge(world["tmp"] / "bridge.json", [(op, f"M{op}") for op in range(7)])
    auth = _authority_csv(world["tmp"] / "auth.csv.gz", _authority_rows(_support_matrix()))
    with pytest.raises(SystemExit, match="STOP"):
        B.build(npz, rec, bridge, auth, world["tmp"] / "x.npz", pins=_pins(npz, bridge, auth))


# --------------------------------------------------------------------------------------- old-vs-masked comparison
def test_masking_audit_reproduces_v3_deltas_and_reports_a_masked_change(world):
    import compare_v79_s174_replay_masking as C

    clean = world["counts"].copy()
    r_old, out_old = _run_replay(world, "cmp_v3", clean, script=V3_REPLAY, with_support=False)
    r_new, out_new = _run_replay(world, "cmp_v4", clean)                    # the real mask: genes 1 and 2 affected
    assert r_old.returncode == 0 and r_new.returncode == 0, (r_old.stderr[-2000:], r_new.stderr[-2000:])
    deltas = world["tmp"] / "v3_deltas.json"
    deltas.write_text(json.dumps({"parts": C.nested_deltas(json.loads(out_old.read_text(encoding="utf-8")))}),
                      encoding="utf-8")
    res = C.compare(out_old, out_new, deltas, world["tmp"] / "audit.json")
    assert res["v3_deltas_reproduced_exactly"] is True
    assert res["replay_genes_affected"] == [FULL_ABSENT_GENE, PARTIAL_GENE]
    assert set(res["questions_A_to_H"]) == {"A_quadratic_depth", "B_broad_class", "C_source", "D_operator", "E_donor",
                                            "F_operator_beyond_donor", "G_donor_class", "H_positive_lognormal"}
    assert res["positive_part_identical_to_v3"]["per_gene_positive"] is True     # no positives on unmeasured entries
    c = res["nested_steps"]["detection"]["C_source"]
    assert c["old_v3"]["median"] != c["masked"]["median"] or c["old_v3"]["mean"] != c["masked"]["mean"]
    bad = world["tmp"] / "bad_deltas.json"
    bad.write_text(json.dumps({"parts": {}}), encoding="utf-8")
    with pytest.raises(SystemExit, match="STOP"):
        C.compare(out_old, out_new, bad, world["tmp"] / "audit2.json")
