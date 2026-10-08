"""Tests for Audit A -- normalization-denominator channel.

Structure required by the audit protocol:

* unit tests of the exact parser and the unconditional summary;
* a **positive control** -- a synthetic store whose outside-ledger mass is known
  by construction, where the audit must recover it exactly;
* **negative controls** -- stores that violate each fail-closed invariant, where
  the audit must abort rather than report a number.

The negative controls matter more than the positive one. An audit that cannot
fail is not evidence, and the specific risk here is an audit that silently
reports ``fraction_outside_ledger = 0`` because it computed the wrong thing.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/scripts/audit_a_normalization_denominator_20260920.py"

_spec = importlib.util.spec_from_file_location("audit_a", SCRIPT)
audit_a = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit_a)

META_FIELDS = ("selection_row", "canonical_cell_id", "donor_id",
               "expression_row", "primary_row_weight", "source_library")
MANIFEST_FIELDS = ("block_key", "source", "operator_index", "matrix_id", "rows", "nnz",
                   "counts_path", "counts_sha256", "meta_path", "meta_sha256")

N_DONORS = 4
CELLS_PER_DONOR = 5
N_CELLS = N_DONORS * CELLS_PER_DONOR
CORE = np.arange(0, 100, dtype=np.int64)          # 100 core addresses of 41,238


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_store(tmp: Path, ledger_counts: np.ndarray, libraries: np.ndarray) -> Path:
    """Materialize a Level-4-shaped store.

    ``ledger_counts`` is the dense (cells x 41238) raw ledger matrix that the
    materializer would have written; ``libraries`` is the independently recorded
    ``source_library``, which in real data is computed BEFORE ledger mapping and
    so may exceed the ledger row sum.
    """
    root = tmp / "expression_level4"
    root.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for d in range(N_DONORS):
        opdir = root / f"op{d:02d}"
        opdir.mkdir(exist_ok=True)
        begin, end = d * CELLS_PER_DONOR, (d + 1) * CELLS_PER_DONOR
        matrix = sp.csr_matrix(ledger_counts[begin:end].astype(np.int32))
        counts_rel = f"op{d:02d}/block-00000.counts.npz"
        meta_rel = f"op{d:02d}/block-00000.meta.csv"
        sp.save_npz(root / counts_rel, matrix)
        with (root / meta_rel).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(META_FIELDS), lineterminator="\n")
            writer.writeheader()
            for local, selection in enumerate(range(begin, end)):
                writer.writerow({
                    "selection_row": selection,
                    "canonical_cell_id": f"D{d:02d}-{local:03d}",
                    "donor_id": f"D{d:02d}",
                    "expression_row": selection,
                    "primary_row_weight": 1.0,
                    "source_library": int(libraries[selection]),
                })
        manifest_rows.append({
            "block_key": f"op{d:02d}/block-00000", "source": "SRC_A" if d < 2 else "SRC_B",
            "operator_index": d, "matrix_id": f"m{d:02d}",
            "rows": matrix.shape[0], "nnz": int(matrix.nnz),
            "counts_path": counts_rel, "counts_sha256": _sha(root / counts_rel),
            "meta_path": meta_rel, "meta_sha256": _sha(root / meta_rel),
        })
    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(MANIFEST_FIELDS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest_rows)
    return root


def _build_pass1(tmp: Path, ledger_counts: np.ndarray) -> Path:
    """pass1 produced by a DIFFERENT route, so the cross-check is meaningful."""
    core_block = ledger_counts[:, CORE]
    path = tmp / "pass1.npz"
    np.savez_compressed(
        path,
        core=CORE,
        cell_donor=np.repeat(np.arange(N_DONORS, dtype=np.int64), CELLS_PER_DONOR),
        cell_nnz_core=(core_block > 0).sum(axis=1).astype(np.int64),
        donor_src=np.array([0, 0, 1, 1], dtype=np.int64),
        duniq=np.array([f"D{d:02d}" for d in range(N_DONORS)], dtype=object),
        donor_addr_nnz=np.zeros((N_DONORS, 41238), dtype=np.int64),
    )
    return path


def _dense_counts(seed: int = 20260920) -> np.ndarray:
    rng = np.random.default_rng(seed)
    dense = np.zeros((N_CELLS, 41238), dtype=np.int64)
    for i in range(N_CELLS):
        cols = rng.choice(41238, size=60, replace=False)
        dense[i, cols] = rng.integers(1, 40, size=60)
        dense[i, CORE[: 20 + (i % 10)]] = rng.integers(1, 30, size=20 + (i % 10))
    return dense


def _run(tmp: Path, root: Path, pass1: Path) -> subprocess.CompletedProcess:
    out = tmp / "out"
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--level4-root", str(root),
         "--pass1", str(pass1), "--out-dir", str(out),
         "--expect-core-size", str(CORE.size)],
        capture_output=True, text=True, timeout=900,
    )


# --------------------------------------------------------------------------- #
# Unit: exact parser
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(("raw", "expected"), [
    ("61129", 61129), ("61129.0", 61129), ("  61129.0 ", 61129),
    ("6.1129E4", 61129), ("6.1129E+4", 61129), ("61129.00000", 61129),
])
def test_parse_library_accepts_exact_positive_integral(raw, expected):
    assert audit_a.parse_library(raw) == expected


@pytest.mark.parametrize("raw", [
    "1_000", "0x10", "0", "0.0", "-5", "-61129.0", "0.5", "61129.5",
    "nan", "NaN", "inf", "Infinity", "-inf", "", "abc", None,
])
def test_parse_library_rejects_everything_else(raw):
    with pytest.raises(ValueError):
        audit_a.parse_library(raw)


def test_describe_is_unconditional_and_reports_every_required_statistic():
    values = np.arange(1, 101, dtype=np.float64)
    d = audit_a.describe(values)
    for key in ("n", "min", "p01", "p05", "p25", "median", "p75", "p95", "p99", "max", "mean"):
        assert key in d, f"missing required statistic {key}"
    assert d["n"] == 100            # every attempted unit in the denominator
    assert d["min"] == 1.0 and d["max"] == 100.0


# --------------------------------------------------------------------------- #
# Positive control: known outside-ledger mass must be recovered exactly
# --------------------------------------------------------------------------- #

def test_positive_control_recovers_known_outside_ledger_mass(tmp_path: Path):
    dense = _dense_counts()
    ledger_row_sum = dense.sum(axis=1)
    # Construct a KNOWN outside-ledger mass per cell, varying by donor so the
    # by-source and by-donor tables have something real to separate.
    known_outside = np.array([100 * (1 + (i // CELLS_PER_DONOR)) + i for i in range(N_CELLS)],
                             dtype=np.int64)
    libraries = ledger_row_sum + known_outside

    root = _build_store(tmp_path, dense, libraries)
    pass1 = _build_pass1(tmp_path, dense)
    proc = _run(tmp_path, root, pass1)
    assert proc.returncode == 0, proc.stderr[-2000:]

    summary = json.loads((tmp_path / "out" / "NORMALIZATION_DENOMINATOR_SUMMARY.json").read_text())
    assert summary["cells_measured"] == N_CELLS
    assert summary["identity_space_closed"] is True
    assert summary["invariants"]["core_nonzero_count_matches_authenticated_pass1"] is True
    assert summary["invariants"]["independent_ledger_sum_routes_agree"] is True

    assert summary["aggregate_mass"]["total_outside_ledger_mass"] == int(known_outside.sum())
    assert summary["aggregate_mass"]["total_ledger_mass"] == int(ledger_row_sum.sum())
    assert summary["aggregate_mass"]["total_source_library"] == int(libraries.sum())
    expected_pooled = float(known_outside.sum() / libraries.sum())
    assert summary["aggregate_mass"]["pooled_fraction_outside_ledger"] == pytest.approx(expected_pooled)
    assert summary["cells_with_any_outside_ledger_mass"] == N_CELLS

    for name in ("BY_SOURCE", "BY_OPERATOR", "BY_DONOR", "BY_DEPTH_DECILE",
                 "BY_CORE_NNZ_DECILE", "BY_SOURCE_OPERATOR"):
        path = tmp_path / "out" / f"NORMALIZATION_DENOMINATOR_{name}.csv"
        assert path.is_file(), f"missing {name}"
        rows = list(csv.DictReader(path.open(newline="")))
        assert rows and sum(int(r["n"]) for r in rows) == N_CELLS, (
            f"{name} must partition every cell exactly once")


def test_positive_control_zero_outside_mass_is_reported_as_zero(tmp_path: Path):
    """Complement: when nothing is outside the ledger, the audit must say so.

    Guards against an implementation that manufactures an apparent channel.
    """
    dense = _dense_counts(seed=7)
    libraries = dense.sum(axis=1)          # exactly the ledger mass
    root = _build_store(tmp_path, dense, libraries)
    pass1 = _build_pass1(tmp_path, dense)
    proc = _run(tmp_path, root, pass1)
    assert proc.returncode == 0, proc.stderr[-2000:]
    summary = json.loads((tmp_path / "out" / "NORMALIZATION_DENOMINATOR_SUMMARY.json").read_text())
    assert summary["aggregate_mass"]["total_outside_ledger_mass"] == 0
    assert summary["aggregate_mass"]["pooled_fraction_outside_ledger"] == 0.0
    assert summary["cells_with_any_outside_ledger_mass"] == 0
    assert summary["global"]["fraction_inside_ledger"]["min"] == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# Negative controls: each fail-closed invariant must actually fire
# --------------------------------------------------------------------------- #

def test_negative_control_ledger_mass_exceeding_source_library_aborts(tmp_path: Path):
    dense = _dense_counts()
    libraries = dense.sum(axis=1)
    libraries[3] -= 1                       # ledger now exceeds the library by 1
    root = _build_store(tmp_path, dense, libraries)
    pass1 = _build_pass1(tmp_path, dense)
    proc = _run(tmp_path, root, pass1)
    assert proc.returncode != 0, "audit accepted ledger mass exceeding the source library"
    assert ("exceeds source library" in proc.stderr
            or "negative outside-ledger" in proc.stderr), proc.stderr[-1500:]


def test_negative_control_nonpositive_source_library_aborts(tmp_path: Path):
    dense = _dense_counts()
    libraries = dense.sum(axis=1) + 10
    libraries[0] = 0
    root = _build_store(tmp_path, dense, libraries)
    pass1 = _build_pass1(tmp_path, dense)
    proc = _run(tmp_path, root, pass1)
    assert proc.returncode != 0, "audit accepted a non-positive source_library"
    # A negative control that fires for the WRONG reason is worthless, so pin
    # the reason, not merely the exit status.
    # It fails closed at PARSE time, before any aggregation -- earlier than the
    # collected-invariant stage, which is the stronger behaviour.
    assert "source_library must be positive" in proc.stderr, proc.stderr[-1500:]


def test_negative_control_pass1_core_disagreement_aborts(tmp_path: Path):
    """The cross-producer corroboration must be load-bearing, not decorative."""
    dense = _dense_counts()
    libraries = dense.sum(axis=1) + 25
    root = _build_store(tmp_path, dense, libraries)
    pass1_path = _build_pass1(tmp_path, dense)
    with np.load(pass1_path, allow_pickle=True) as z:
        payload = {k: z[k] for k in z.files}
    payload["cell_nnz_core"] = payload["cell_nnz_core"].copy()
    payload["cell_nnz_core"][2] += 1        # one cell disagrees
    np.savez_compressed(pass1_path, **payload)
    proc = _run(tmp_path, root, pass1_path)
    assert proc.returncode != 0, "audit accepted disagreement with authenticated pass1"
    assert "pass1" in proc.stderr.lower()


def test_negative_control_tampered_block_digest_aborts(tmp_path: Path):
    dense = _dense_counts()
    libraries = dense.sum(axis=1) + 5
    root = _build_store(tmp_path, dense, libraries)
    pass1 = _build_pass1(tmp_path, dense)
    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    rows = list(csv.DictReader(manifest.open(newline="")))
    rows[0]["counts_sha256"] = "0" * 64
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    proc = _run(tmp_path, root, pass1)
    assert proc.returncode != 0, "audit ran against an unauthenticated block"
    assert "digest mismatch" in proc.stderr, proc.stderr[-1500:]


def test_negative_control_incomplete_identity_space_aborts(tmp_path: Path):
    """A cell never written must abort, not silently summarize the rest."""
    dense = _dense_counts()
    libraries = dense.sum(axis=1) + 5
    root = _build_store(tmp_path, dense, libraries)
    pass1_path = _build_pass1(tmp_path, dense)
    with np.load(pass1_path, allow_pickle=True) as z:
        payload = {k: z[k] for k in z.files}
    # Claim one more cell than the store contains.
    payload["cell_donor"] = np.concatenate([payload["cell_donor"], np.array([0], np.int64)])
    payload["cell_nnz_core"] = np.concatenate([payload["cell_nnz_core"], np.array([0], np.int64)])
    np.savez_compressed(pass1_path, **payload)
    proc = _run(tmp_path, root, pass1_path)
    assert proc.returncode != 0, "audit summarized an unclosed identity space"
    assert "identity space" in proc.stderr.lower() or "never written" in proc.stderr.lower()


def test_int32_row_sum_would_overflow_but_audit_uses_int64(tmp_path: Path):
    """Regression for the int32 overflow that once produced 0.009717 vs 0.832983.

    A single cell carrying more than 2**31 total counts makes an int32 row sum
    wrap negative. The audit must still report exact positive mass.
    """
    dense = np.zeros((N_CELLS, 41238), dtype=np.int64)
    for i in range(N_CELLS):
        dense[i, CORE[:10]] = 5
    # 40 columns x 60,000,000 = 2.4e9 > 2**31 in one row, each value < 2**31.
    dense[0, 200:240] = 60_000_000
    libraries = dense.sum(axis=1) + 17
    assert libraries[0] > 2**31

    root = _build_store(tmp_path, dense, libraries)
    pass1 = _build_pass1(tmp_path, dense)
    proc = _run(tmp_path, root, pass1)
    assert proc.returncode == 0, proc.stderr[-2000:]
    summary = json.loads((tmp_path / "out" / "NORMALIZATION_DENOMINATOR_SUMMARY.json").read_text())
    assert summary["aggregate_mass"]["total_ledger_mass"] == int(dense.sum())
    assert summary["aggregate_mass"]["total_outside_ledger_mass"] == 17 * N_CELLS
    assert summary["global"]["L_ledger"]["max"] == float(dense.sum(axis=1).max())
