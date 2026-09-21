"""Controls for the heavy B/C/E sufficient-statistics reuse qualification.

Parser equivalence proves the artifact's *inputs* were parsed identically. This
instrument proves the artifact's *contents* are consistent with the authenticated
substrate, by recomputing aggregates from metadata along a second route.

A qualification instrument that cannot fail is worthless, so the negative
controls carry the weight here: each corrupts exactly one invariant and requires
the instrument to refuse. Without them, a script that printed
``HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE`` unconditionally would look identical.

The real-substrate test FAILS rather than skips when artifacts are absent. A skip
would silently drop the reuse gate that the whole B/C/E lane depends on.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ("analysis/v5_full104_information_channel_redteam_20260920/scripts/"
                 "qualify_heavy_sufficient_statistics_20260920.py")
EVIDENCE = ROOT / ("analysis/v5_full104_information_channel_redteam_20260920/evidence/"
                   "parser_equivalence")

N_DONORS = 4
CELLS_PER_DONOR = 5
N_CELLS = N_DONORS * CELLS_PER_DONOR
N_CORE = 9
LEDGER = 41238
SOURCES = ("SRC_A", "SRC_A", "SRC_B", "SRC_B")

META_FIELDS = ("selection_row", "canonical_cell_id", "donor_id",
               "expression_row", "primary_row_weight", "source_library")
MANIFEST_FIELDS = ("block_key", "source", "operator_index", "matrix_id", "rows", "nnz",
                   "counts_path", "counts_sha256", "meta_path", "meta_sha256")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_store(tmp: Path, libraries: np.ndarray) -> tuple[Path, Path]:
    root = tmp / "expression_level4"
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in range(N_DONORS):
        opdir = root / f"op{d:02d}"
        opdir.mkdir(exist_ok=True)
        begin, end = d * CELLS_PER_DONOR, (d + 1) * CELLS_PER_DONOR
        matrix = sp.csr_matrix((CELLS_PER_DONOR, LEDGER), dtype=np.int32)
        counts_rel = f"op{d:02d}/block-00000.counts.npz"
        meta_rel = f"op{d:02d}/block-00000.meta.csv"
        sp.save_npz(root / counts_rel, matrix)
        with (root / meta_rel).open("w", newline="", encoding="utf-8") as h:
            w = csv.DictWriter(h, fieldnames=list(META_FIELDS), lineterminator="\n")
            w.writeheader()
            for local, sel in enumerate(range(begin, end)):
                w.writerow({"selection_row": sel, "canonical_cell_id": f"D{d:02d}-{local}",
                            "donor_id": f"D{d:02d}", "expression_row": sel,
                            "primary_row_weight": 1.0, "source_library": int(libraries[sel])})
        rows.append({"block_key": f"op{d:02d}/block-00000", "source": SOURCES[d],
                     "operator_index": d, "matrix_id": f"m{d:02d}",
                     "rows": CELLS_PER_DONOR, "nnz": int(matrix.nnz),
                     "counts_path": counts_rel, "counts_sha256": _sha(root / counts_rel),
                     "meta_path": meta_rel, "meta_sha256": _sha(root / meta_rel)})
    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=list(MANIFEST_FIELDS), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return root, manifest


def _build_artifact(tmp: Path, libraries: np.ndarray, *, donor_cells=None,
                    core_size=N_CORE) -> Path:
    path = tmp / "stats.npz"
    cells = donor_cells if donor_cells is not None else np.full(N_DONORS, CELLS_PER_DONOR, np.int64)
    np.savez_compressed(
        path,
        duniq=np.array([f"D{d:02d}" for d in range(N_DONORS)], dtype=object),
        donor_cells=cells,
        libraries=libraries.astype(np.int64),
        core=np.arange(core_size, dtype=np.int64),
        donor_nnz=np.zeros((N_DONORS, core_size), dtype=np.int64),
        src_of_cell=np.repeat(np.array([0, 0, 1, 1], np.int64), CELLS_PER_DONOR),
        source_names=np.array(["SRC_A", "SRC_B"], dtype=object),
    )
    return path


def _build_pass1(tmp: Path) -> Path:
    path = tmp / "pass1.npz"
    np.savez_compressed(path, cell_donor=np.repeat(np.arange(N_DONORS, dtype=np.int64),
                                                   CELLS_PER_DONOR))
    return path


def _run(tmp: Path, root: Path, manifest: Path, artifact: Path, pass1: Path,
         *, bound_sha=None, audit_a_total=None, source_cells=None) -> subprocess.CompletedProcess:
    out = tmp / "out.json"
    cmd = [sys.executable, str(SCRIPT),
           "--level4-root", str(root), "--artifact", str(artifact), "--pass1", str(pass1),
           "--out", str(out), "--workers", "1",
           "--expect-cells", str(N_CELLS), "--expect-donors", str(N_DONORS),
           "--expect-core", str(N_CORE),
           "--expect-manifest-sha256", _sha(manifest),
           "--bound-artifact-sha256", bound_sha or _sha(artifact),
           "--expect-source-cells", json.dumps(source_cells or {"SRC_A": 10, "SRC_B": 10}),
           "--audit-a-total", str(audit_a_total if audit_a_total is not None
                                  else int(np.load(artifact)["libraries"].sum()))]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=900)


def _libs() -> np.ndarray:
    return np.arange(1000, 1000 + N_CELLS, dtype=np.int64)


# --------------------------------------------------------------------------- #
# Positive control
# --------------------------------------------------------------------------- #

def test_consistent_artifact_qualifies(tmp_path: Path):
    libs = _libs()
    root, manifest = _build_store(tmp_path, libs)
    artifact = _build_artifact(tmp_path, libs)
    pass1 = _build_pass1(tmp_path)
    proc = _run(tmp_path, root, manifest, artifact, pass1)
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    payload = json.loads((tmp_path / "out.json").read_text())
    assert payload["verdict"] == "HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE"
    assert payload["failures"] == []
    assert payload["three_route_total_agreement"] is True
    assert payload["rows_traversed"] == N_CELLS


# --------------------------------------------------------------------------- #
# Negative controls -- each corrupts exactly one invariant
# --------------------------------------------------------------------------- #

def test_artifact_sha_mismatch_is_refused(tmp_path: Path):
    libs = _libs()
    root, manifest = _build_store(tmp_path, libs)
    artifact = _build_artifact(tmp_path, libs)
    pass1 = _build_pass1(tmp_path)
    proc = _run(tmp_path, root, manifest, artifact, pass1, bound_sha="0" * 64)
    assert proc.returncode != 0
    payload = json.loads((tmp_path / "out.json").read_text())
    assert payload["verdict"] == "HEAVY_ARTIFACT_NOT_QUALIFIED"
    assert any("SHA-256" in f for f in payload["failures"]), payload["failures"]


def test_library_value_drift_between_artifact_and_metadata_is_refused(tmp_path: Path):
    """The substantive check: artifact contents must match the source metadata."""
    libs = _libs()
    root, manifest = _build_store(tmp_path, libs)
    drifted = libs.copy()
    drifted[3] += 1                       # one cell differs by one count
    artifact = _build_artifact(tmp_path, drifted)
    pass1 = _build_pass1(tmp_path)
    proc = _run(tmp_path, root, manifest, artifact, pass1,
                audit_a_total=int(libs.sum()))
    assert proc.returncode != 0
    payload = json.loads((tmp_path / "out.json").read_text())
    assert payload["three_route_total_agreement"] is False
    assert any("total source library" in f for f in payload["failures"]), payload["failures"]


def test_per_donor_cell_total_mismatch_is_refused(tmp_path: Path):
    libs = _libs()
    root, manifest = _build_store(tmp_path, libs)
    bad_cells = np.full(N_DONORS, CELLS_PER_DONOR, np.int64)
    bad_cells[1] += 1
    artifact = _build_artifact(tmp_path, libs, donor_cells=bad_cells)
    pass1 = _build_pass1(tmp_path)
    proc = _run(tmp_path, root, manifest, artifact, pass1)
    assert proc.returncode != 0
    payload = json.loads((tmp_path / "out.json").read_text())
    assert any("per-donor cell totals" in f for f in payload["failures"]), payload["failures"]


def test_core_dimension_mismatch_is_refused(tmp_path: Path):
    libs = _libs()
    root, manifest = _build_store(tmp_path, libs)
    artifact = _build_artifact(tmp_path, libs, core_size=N_CORE + 1)
    pass1 = _build_pass1(tmp_path)
    proc = _run(tmp_path, root, manifest, artifact, pass1)
    assert proc.returncode != 0
    payload = json.loads((tmp_path / "out.json").read_text())
    assert any("core" in f for f in payload["failures"]), payload["failures"]


def test_tampered_metadata_hash_aborts(tmp_path: Path):
    libs = _libs()
    root, manifest = _build_store(tmp_path, libs)
    rows = list(csv.DictReader(manifest.open(newline="")))
    rows[0]["meta_sha256"] = "0" * 64
    with manifest.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    artifact = _build_artifact(tmp_path, libs)
    pass1 = _build_pass1(tmp_path)
    proc = _run(tmp_path, root, manifest, artifact, pass1)
    assert proc.returncode != 0, "qualification ran against unauthenticated metadata"


# --------------------------------------------------------------------------- #
# Real-substrate result, pinned
# --------------------------------------------------------------------------- #

def test_real_full104_qualification_result_is_recorded_and_passing():
    path = EVIDENCE / "HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION.json"
    if not path.is_file():
        pytest.fail(
            f"{path} missing. This test is deliberately not skipped: the B/C/E lane "
            "depends on this reuse gate, and a skip would silently drop it.")
    d = json.loads(path.read_text())
    assert d["verdict"] == "HEAVY_ARTIFACT_QUALIFIED_FOR_REUSE", d["failures"]
    assert d["rows_traversed"] == 4_553_407
    assert d["donors"] == 104
    assert d["core_addresses"] == 17_186
    assert d["selection_row_range"] == [0, 4_553_406]
    assert d["artifact_sha_matches_bound"] is True
    assert d["three_route_total_agreement"] is True
    assert d["total_source_library_recomputed_from_metadata"] == 122_517_308_792
    assert d["failures"] == []
    assert d["scope_class"] == "CURRENT_FULL104_RECONNAISSANCE"


def test_real_parser_equivalence_result_is_recorded_and_passing():
    path = EVIDENCE / "SOURCE_LIBRARY_PARSER_EQUIVALENCE.json"
    if not path.is_file():
        pytest.fail(f"{path} missing; the reuse decision has no evidence behind it.")
    d = json.loads(path.read_text())
    assert d["rows_checked"] == 4_553_407
    assert d["blocks_checked"] == 8_915
    assert d["strict_rejections"] == 0
    assert d["legacy_rejections"] == 0
    assert d["value_or_parse_mismatches"] == 0
    assert d["reuse_decision"] == "ALLOW_CONTENT_ADDRESSED_REUSE_WITH_CURRENT_PARSER"
    # 512 decimal-syntax tokens exist: exactly the case where the two parsers
    # could diverge. They agree, which is what makes the reuse decision non-trivial.
    assert d["token_syntax_counts"]["decimal"] == 512
    assert d["token_syntax_counts"]["integer"] == 4_552_895
