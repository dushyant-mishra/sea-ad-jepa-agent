"""A tiny synthetic world for running the REAL G6 (and G7) V2 entrypoints end to end.

Every input the entrypoints read is synthetic and written under pytest's tmp_path: physical H5AD-like files, the
Sample-A freeze, provenance, collision ledger, Macha freeze, TD50 sentinel archive, historical NPH52 CSR and S174
cache shards. Hash pins and geometry constants are pointed at the synthetic files with monkeypatch for one test only.
Nothing here reads, creates or stands in for a real owner decision, real authorization or real expression data.

Sample A has 12 rows (more than 10, so a text sort of sample_row would be caught) written in shuffled file order.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_g6g7_gate_fixtures as F  # noqa: E402

V5 = F.ROOT / "scripts" / "v5"
G6_SCRIPT = V5 / "materialize_td_relational_corrected_sampleA_v2.py"
G7_SCRIPT = V5 / "audit_td_relational_g7_s174_overlap_v2.py"

N_ADDR = 12
REPLAY = (3, 5, 8)
SOURCE_COUNTS = {"HVS": 3, "NPH52": 3, "SEA_AD": 6}
N_SAMPLE_A = 12
HIST_ROWS = 50_000  # verify_historical_csr requires the frozen 50,000-row historical geometry

# physical matrices: study, stem, var ids, CSR rows as (columns, raw integer counts), collision-ledger ids
MATRICES = {
    "HVS::h1": dict(study="HVS", stem="h1", var=["E0", "E1", "E2", "E3", "E4", "E5"], ledger=["E5"],
                    rows=[([0, 1, 4], [2, 3, 5]), ([2], [7]), ([2, 3, 5], [1, 4, 6]), ([0, 2], [4, 4])]),
    "SEA_AD::s1": dict(study="SEA_AD", stem="s1", var=["E0", "E1", "E2", "E3"], ledger=[],
                       rows=[([0, 2], [1, 1]), ([1, 3], [2, 9]), ([0, 1, 2], [5, 5, 5]), ([3], [3])]),
    "SEA_AD::s2": dict(study="SEA_AD", stem="s2", var=["E0", "E1", "E2", "E3"], ledger=[],
                       rows=[([3], [4]), ([1], [1]), ([0, 2], [2, 8])]),
}
PROVENANCE = {"HVS_COMMON": {"E0": 3, "E1": 5, "E2": 8, "E3": 10, "E5": 9},
              "SEA_AD_COMMON": {"E0": 3, "E1": 5, "E2": 8, "E3": 11}}
# sample_row -> (source, matrix_id, local_row, global_row)
SAMPLE_A = {
    0: ("HVS", "HVS::h1", 0, 100), 1: ("SEA_AD", "SEA_AD::s1", 0, 101), 2: ("NPH52", "NPH52::n1", 0, 200),
    3: ("HVS", "HVS::h1", 2, 102), 4: ("SEA_AD", "SEA_AD::s1", 1, 103), 5: ("SEA_AD", "SEA_AD::s2", 0, 104),
    6: ("NPH52", "NPH52::n1", 1, 201), 7: ("SEA_AD", "SEA_AD::s1", 2, 105), 8: ("HVS", "HVS::h1", 3, 106),
    9: ("SEA_AD", "SEA_AD::s1", 3, 107), 10: ("SEA_AD", "SEA_AD::s2", 2, 108), 11: ("NPH52", "NPH52::n1", 2, 202),
}
FILE_ORDER = [7, 2, 11, 0, 9, 4, 1, 10, 3, 6, 8, 5]
NPH_HISTORICAL = {200: {3: 0.5, 7: 0.25, 8: 1.5}, 201: {5: 2.0}, 202: {}}
NPH_LIBRARY = {200: 500, 201: 600, 202: 700}


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def cell_id(sample_row: int) -> str:
    source, mid, local, grow = SAMPLE_A[sample_row]
    return f"nph_{grow}" if source == "NPH52" else f"{MATRICES[mid]['stem']}_cell{local}"


def physical_row(mid: str, local: int):
    cols, vals = MATRICES[mid]["rows"][local]
    return dict(zip(cols, vals))


def column_address(mid: str) -> dict:
    spec = MATRICES[mid]
    family = PROVENANCE["HVS_COMMON" if spec["study"] == "HVS" else "SEA_AD_COMMON"]
    return {j: family[g] for j, g in enumerate(spec["var"]) if g in family and g not in spec["ledger"]}


def expected_values() -> dict:
    """(sample_row, address) -> float32 value G6 must materialize."""
    out = {}
    for sr, (source, mid, local, grow) in SAMPLE_A.items():
        if source == "NPH52":
            for a, v in NPH_HISTORICAL[grow].items():
                if a in REPLAY and v:
                    out[(sr, a)] = np.float32(v)
            continue
        row = physical_row(mid, local)
        total = sum(row.values())
        for j, raw in row.items():
            a = column_address(mid).get(j)
            if a in REPLAY and raw:
                out[(sr, a)] = np.float32(np.log1p(raw * 10000.0 / total))
    return out


def library(sample_row: int) -> int:
    source, mid, local, grow = SAMPLE_A[sample_row]
    return NPH_LIBRARY[grow] if source == "NPH52" else int(sum(physical_row(mid, local).values()))


def _write_h5ad(path: Path, mid: str) -> None:
    import h5py

    spec = MATRICES[mid]
    data, indices, indptr = [], [], [0]
    for cols, vals in spec["rows"]:
        indices += cols
        data += vals
        indptr.append(len(indices))
    with h5py.File(path, "w") as h:
        var = h.create_group("var")
        names = np.asarray(spec["var"], dtype="S")
        if spec["study"] == "HVS":
            var.attrs["_index"] = "_index"
            var.create_dataset("_index", data=names)
        else:
            var.create_dataset("gene_ids", data=names)
        obs = h.create_group("obs")
        obs.create_dataset("exp_component_name",
                           data=np.asarray([f"{spec['stem']}_cell{i}" for i in range(len(spec["rows"]))], dtype="S"))
        x = h.create_group("X")
        x.create_dataset("data", data=np.asarray(data, dtype=np.float32))
        x.create_dataset("indices", data=np.asarray(indices, dtype=np.int32))
        x.create_dataset("indptr", data=np.asarray(indptr, dtype=np.int64))


def _npz_bytes(**arrays) -> bytes:
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    return buf.getvalue()


def build_inputs(root: Path, *, library_offsets: dict | None = None) -> SimpleNamespace:
    """Write every synthetic input file; library_offsets plants TD50 sentinel errors by sample_row."""
    root = Path(root)
    src = root / "source_root"
    src.mkdir(parents=True)
    w = SimpleNamespace(root=root, source_root=src)
    freeze = {"schema": "SYNTHETIC_MACHA_FREEZE", "matrices": []}
    for mid, spec in MATRICES.items():
        path = src / f"{spec['stem']}.h5ad"
        _write_h5ad(path, mid)
        freeze["matrices"].append({"matrix_id": mid, "stem": spec["stem"], "slot": "X",
                                   "source": {"path": path.name, "bytes": path.stat().st_size, "sha256": sha(path)}})
    w.macha_freeze = root / "macha_freeze.json"
    w.macha_freeze.write_bytes((json.dumps(freeze, indent=1, sort_keys=True) + "\n").encode("utf-8"))

    rows = []
    for sr in FILE_ORDER:
        source, mid, local, grow = SAMPLE_A[sr]
        rows.append(dict(sample="A_NATURAL_MIXTURE", sample_row=sr, source=source, matrix_id=mid, local_row=local,
                         cell_id=cell_id(sr), donor_id=f"donor_{sr % 4}", operator_index=sr % 3, global_row=grow))
    rows.append(dict(sample="B_COVERAGE_DISCOVERY", sample_row=0, source="HVS", matrix_id="HVS::h1", local_row=1,
                     cell_id="h1_cell1", donor_id="donor_x", operator_index=0, global_row=300))
    w.sample_freeze = root / "sample_freeze.csv"
    pd.DataFrame(rows).to_csv(w.sample_freeze, index=False, lineterminator="\n")

    w.provenance = root / "provenance.csv"
    pd.DataFrame([dict(source_dataset_id=fam, source_exact_ensembl_id=g, molecular_address_index=a)
                  for fam, mapping in PROVENANCE.items() for g, a in mapping.items()]
                 ).to_csv(w.provenance, index=False, lineterminator="\n")
    w.collision_ledger = root / "collision_ledger.csv"
    pd.DataFrame([dict(matrix_id=mid, source_exact_ensembl_id=g) for mid, spec in MATRICES.items()
                  for g in spec["ledger"]]).to_csv(w.collision_ledger, index=False, lineterminator="\n")

    offsets = library_offsets or {}
    w.td50_members = {}
    w.td_artifacts_zip = root / "td_artifacts.zip"
    with zipfile.ZipFile(w.td_artifacts_zip, "w") as z:
        for source in SOURCE_COUNTS:
            srs = [sr for sr in SAMPLE_A if SAMPLE_A[sr][0] == source]
            raw = _npz_bytes(global_row=np.asarray([SAMPLE_A[sr][3] for sr in srs], dtype=np.int64),
                             source_library=np.asarray([library(sr) + offsets.get(sr, 0) for sr in srs], dtype=np.int64),
                             detected=np.asarray([len(physical_row(SAMPLE_A[sr][1], SAMPLE_A[sr][2]))
                                                  if source != "NPH52" else 5 for sr in srs], dtype=np.int64))
            z.writestr(f"TD41_TD58/td50_{source}.npz", raw)
            w.td50_members[source] = hashlib.sha256(raw).hexdigest()

    w.historical_csr_root = root / "historical_csr"
    w.historical_csr_root.mkdir()
    data, indices, indptr = [], [], np.zeros(HIST_ROWS + 1, dtype=np.int64)
    for grow in range(HIST_ROWS):
        entries = sorted(NPH_HISTORICAL.get(grow, {}).items())
        for a, v in entries:
            indices.append(a)
            data.append(v)
        indptr[grow + 1] = len(indices)
    arrays = {"data.npy": np.asarray(data, dtype=np.float32), "indices.npy": np.asarray(indices, dtype=np.int32),
              "indptr.npy": indptr, "shape.npy": np.asarray([HIST_ROWS, N_ADDR], dtype=np.int64)}
    w.hist_csr_sha = {}
    for name, arr in arrays.items():
        np.save(w.historical_csr_root / name, arr)
        w.hist_csr_sha[name] = sha(w.historical_csr_root / name)
    return w


def point_g6_at_world(g6, w, monkeypatch) -> None:
    """Pin the G6 module (and its own common instance) to the synthetic world for one test."""
    common = g6.common
    for attr, value in (("N_ADDR", N_ADDR), ("N_SAMPLE_A", N_SAMPLE_A), ("N_REPLAY", len(REPLAY)),
                        ("SOURCE_COUNTS", dict(SOURCE_COUNTS))):
        monkeypatch.setattr(g6, attr, value)
    hashes = {"sample_freeze_sha256": sha(w.sample_freeze), "provenance_sha256": sha(w.provenance),
              "collision_ledger_sha256": sha(w.collision_ledger), "macha_freeze_sha256": sha(w.macha_freeze),
              "td_artifacts_zip_sha256": sha(w.td_artifacts_zip)}
    for key, value in hashes.items():
        monkeypatch.setitem(common.EXPECTED_INPUT_HASHES, key, value)
    for attr, key in (("EXPECTED_SAMPLE_FREEZE_SHA", "sample_freeze_sha256"), ("EXPECTED_PROVENANCE_SHA", "provenance_sha256"),
                      ("EXPECTED_COLLISION_SHA", "collision_ledger_sha256"), ("EXPECTED_MACHA_FREEZE_SHA", "macha_freeze_sha256"),
                      ("EXPECTED_TD_ARTIFACTS_SHA", "td_artifacts_zip_sha256")):
        monkeypatch.setattr(g6, attr, hashes[key])
    for name, value in w.hist_csr_sha.items():
        monkeypatch.setitem(g6.HIST_CSR_SHA, name, value)
    for source, value in w.td50_members.items():
        monkeypatch.setitem(g6.TD50_SHA, source, value)


def bind_gate_to_real_scripts(common, b) -> None:
    """The entrypoints bind their own script files; rebuild the synthetic authorization around them."""
    b.g6, b.g7 = G6_SCRIPT, G7_SCRIPT
    F.rewrite_authorization(common, b)


def g6_argv(w, b, out: Path) -> list:
    return ["materialize_td_relational_corrected_sampleA_v2.py",
            "--preflight-result", str(b.preflight), "--mapping-receipt", str(b.mapping),
            "--value-authorization", str(b.auth), "--owner-decision", str(b.owner_decision),
            "--replay-manifest", str(b.replay_manifest), "--sample-freeze", str(w.sample_freeze),
            "--provenance", str(w.provenance), "--collision-ledger", str(w.collision_ledger),
            "--macha-freeze", str(w.macha_freeze), "--td-artifacts-zip", str(w.td_artifacts_zip),
            "--historical-csr-root", str(w.historical_csr_root), "--source-root", str(w.source_root),
            "--output-dir", str(out)]


def build_g6_world(tmp_path, monkeypatch, *, library_offsets: dict | None = None) -> SimpleNamespace:
    g6 = load_script(G6_SCRIPT, "td_g6_synthetic_world")
    w = build_inputs(Path(tmp_path) / "world", library_offsets=library_offsets)
    point_g6_at_world(g6, w, monkeypatch)
    gate_dir = Path(tmp_path) / "gate_g6"
    gate_dir.mkdir()
    b = F.build_gate(gate_dir, g6.common, monkeypatch)
    monkeypatch.setattr(g6, "EXPECTED_REPLAY_MANIFEST_SHA", sha(b.replay_manifest))  # G6's import-time alias
    bind_gate_to_real_scripts(g6.common, b)
    w.gate, w.g6 = b, g6
    w.g6_out = Path(tmp_path) / "g6_out"
    return w


def run_g6(w, monkeypatch) -> int:
    monkeypatch.setattr(sys, "argv", g6_argv(w, w.gate, w.g6_out))
    return w.g6.main()


def point_g7_at_world(g7, w, monkeypatch) -> None:
    """Pin the G7 module (and its own common instance) to the same synthetic world and gate as G6."""
    common, g6common = g7.common, w.g6.common
    for attr, value in (("N_ADDR", N_ADDR), ("N_SAMPLE_A", N_SAMPLE_A), ("N_REPLAY", len(REPLAY)),
                        ("SOURCE_COUNTS", dict(SOURCE_COUNTS))):
        monkeypatch.setattr(g7, attr, value)
    for key, value in g6common.EXPECTED_INPUT_HASHES.items():
        monkeypatch.setitem(common.EXPECTED_INPUT_HASHES, key, value)
    for attr in ("HIST_CSR_SHA", "TD50_SHA"):  # single authority in common once G7 validates G6 input hashes
        if hasattr(common, attr):
            for key, value in getattr(g6common, attr).items():
                monkeypatch.setitem(getattr(common, attr), key, value)
    for attr, key in (("EXPECTED_REPLAY_MANIFEST_SHA", "replay_manifest_sha256"),
                      ("EXPECTED_SAMPLE_FREEZE_SHA", "sample_freeze_sha256"),
                      ("EXPECTED_PROVENANCE_SHA", "provenance_sha256"),
                      ("EXPECTED_COLLISION_SHA", "collision_ledger_sha256"),
                      ("EXPECTED_MACHA_FREEZE_SHA", "macha_freeze_sha256")):
        monkeypatch.setattr(g7, attr, g6common.EXPECTED_INPUT_HASHES[key])
    monkeypatch.setattr(common, "PR259_DRIVER_SHA256", g6common.PR259_DRIVER_SHA256, raising=False)
    monkeypatch.setattr(common, "PR259_MAPPING_SHA256", g6common.PR259_MAPPING_SHA256, raising=False)
    monkeypatch.setattr(common, "code_identity", lambda left, right: F.fake_code_identity(common, left, right))


def build_g7_world(tmp_path, monkeypatch) -> SimpleNamespace:
    """A genuine synthetic G6 PASS execution, plus a G7 module pointed at the same world."""
    w = build_g6_world(tmp_path, monkeypatch)
    assert run_g6(w, monkeypatch) == 0
    w.g7 = load_script(G7_SCRIPT, "td_g7_synthetic_world")
    point_g7_at_world(w.g7, w, monkeypatch)
    w.g6_receipt = w.g6_out / "G6_RECEIPT.json"
    return w


def g7_expected_trace(w) -> dict:
    """The trace G7 itself expects for this gate, computed by G7's own code (not copied from the G6 receipt)."""
    b = w.gate
    args = SimpleNamespace(preflight_result=str(b.preflight), mapping_receipt=str(b.mapping),
                           value_authorization=str(b.auth), owner_decision=str(b.owner_decision))
    auth = json.loads(Path(b.auth).read_text(encoding="utf-8"))
    return w.g7.expected_authority_trace(args, auth, G6_SCRIPT, G7_SCRIPT)


def g7_prerequisite_inputs(w) -> dict:
    """The replay addresses and frozen Sample-A rows, loaded by G7's own pinned load_inputs (as main does)."""
    args = SimpleNamespace(replay_manifest=str(w.gate.replay_manifest), sample_freeze=str(w.sample_freeze),
                           provenance=str(w.provenance), collision_ledger=str(w.collision_ledger),
                           macha_freeze=str(w.macha_freeze))
    replay, sample_a, _, _, _ = w.g7.load_inputs(args)
    return {"replay_addresses": set(replay.molecular_address_index.astype(int)), "sample_a": sample_a}


# S174 cache shards per stem: the S174 cell ids each shard holds. h1 and s1 overlap Sample A naturally (2 cells each);
# s2 holds no Sample-A cell; x9 belongs to no Sample-A matrix but is still under the global G1b hash pass.
S174_CELLS_OVERLAP = {"h1": ["other_h1", "h1_cell2", "h1_cell0"], "s1": ["s1_cell3", "s1_cell1"],
                      "s2": ["zz_a", "zz_b"], "x9": ["q0"]}
S174_CELLS_NO_OVERLAP = {"h1": ["other_h1"], "s1": ["s1_none"], "s2": ["zz_a"], "x9": ["q0"]}


def s174_row(stem: str, cid: str) -> dict:
    """S174 counts in address space: the physical row's replay-address raw counts, plus non-replay noise."""
    mid = next((m for m, spec in MATRICES.items() if spec["stem"] == stem), None)
    row = {0: 7}  # a non-replay address that G7 must ignore
    if mid is not None and cid.startswith(f"{stem}_cell"):
        local = int(cid.split("_cell")[1])
        col_addr = column_address(mid)
        for j, raw in physical_row(mid, local).items():
            a = col_addr.get(j)
            if a is not None:
                row[a] = raw
    return row


def build_s174_cache(root: Path, cells: dict, *, perturb: tuple | None = None) -> tuple:
    """Write synthetic S174 shards; perturb=(stem, cell_id, address, delta) plants one count mismatch."""
    root = Path(root)
    root.mkdir(parents=True)
    shards = {}
    for stem, ids in cells.items():
        data, indices, indptr = [], [], [0]
        for cid in ids:
            row = s174_row(stem, cid)
            if perturb and perturb[0] == stem and perturb[1] == cid:
                row[perturb[2]] = row.get(perturb[2], 0) + perturb[3]
            for a in sorted(row):
                indices.append(a)
                data.append(row[a])
            indptr.append(len(indices))
        np.savez(root / f"{stem}.counts.npz", data=np.asarray(data, dtype=np.float32),
                 indices=np.asarray(indices, dtype=np.int32), indptr=np.asarray(indptr, dtype=np.int64),
                 shape=np.asarray([len(ids), N_ADDR], dtype=np.int64))
        np.savez(root / f"{stem}.meta.npz", cell_id=np.asarray(ids))
        shards[stem] = {"counts": sha(root / f"{stem}.counts.npz"), "meta": sha(root / f"{stem}.meta.npz")}
    freeze = {"schema": "S174_REBUILD_G1B_FREEZE_V1", "status": "FROZEN__NO_COUNT_READ",
              "rebuilt_cache": {"shards": shards}}
    result = {"schema": "S174_REBUILD_G1B_RESULT_V1", "G1b_pass": True, "synthetic": True}
    return freeze, result


def g7_argv(w, out: Path, cache_root: Path) -> list:
    b = w.gate
    return ["audit_td_relational_g7_s174_overlap_v2.py",
            "--preflight-result", str(b.preflight), "--mapping-receipt", str(b.mapping),
            "--value-authorization", str(b.auth), "--owner-decision", str(b.owner_decision),
            "--g6-receipt", str(w.g6_receipt), "--replay-manifest", str(b.replay_manifest),
            "--sample-freeze", str(w.sample_freeze), "--provenance", str(w.provenance),
            "--collision-ledger", str(w.collision_ledger), "--macha-freeze", str(w.macha_freeze),
            "--s174-cache-root", str(cache_root), "--source-root", str(w.source_root), "--out", str(out)]


def run_g7(w, monkeypatch, tmp_path, *, cells: dict, perturb: tuple | None = None, name: str = "g7") -> tuple:
    """Run the REAL G7 main on the synthetic world; the G1b authority (read from git in production) is replaced by
    the synthetic freeze for this test only. Returns (exit code, receipt path)."""
    cache_root = Path(tmp_path) / f"s174_{name}"
    freeze, result = build_s174_cache(cache_root, cells, perturb=perturb)
    monkeypatch.setattr(w.g7, "load_g1b_authority_from_pass_commit",
                        lambda anchor: (result, freeze, "synthetic-g1b-result", "synthetic-g1b-freeze"))
    out = Path(tmp_path) / f"{name}_out" / "G7_RECEIPT.json"
    monkeypatch.setattr(sys, "argv", g7_argv(w, out, cache_root))
    return w.g7.main(), out
