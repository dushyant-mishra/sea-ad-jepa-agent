"""Regression tests for the exhaustive Phase-I heavy-statistics qualifier V2.

V1 is preserved as historical evidence. V2 closes two audit gaps without
changing the qualified heavy artifact bytes:
1. all donor source-library totals are checked, not only a 12-donor sample;
2. the full per-cell source vector is checked against authenticated donor/source
   identity.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
V1_TEST = ROOT / "tests/test_v5_heavy_sufficient_statistics_qualification_v1.py"
_spec = importlib.util.spec_from_file_location("heavy_v1_fixture", V1_TEST)
F = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(F)

SCRIPT = ROOT / (
    "analysis/v5_full104_information_channel_redteam_20260920/scripts/"
    "qualify_heavy_sufficient_statistics_v2_20260921.py"
)


def _run_v2(
    tmp: Path,
    root: Path,
    manifest: Path,
    artifact: Path,
    pass1: Path,
    *,
    donor_sample: int = 0,
    audit_a_total: int | None = None,
) -> subprocess.CompletedProcess:
    out = tmp / "out-v2.json"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--level4-root",
        str(root),
        "--artifact",
        str(artifact),
        "--pass1",
        str(pass1),
        "--out",
        str(out),
        "--workers",
        "1",
        "--donor-sample",
        str(donor_sample),
        "--expect-cells",
        str(F.N_CELLS),
        "--expect-donors",
        str(F.N_DONORS),
        "--expect-core",
        str(F.N_CORE),
        "--expect-manifest-sha256",
        F._sha(manifest),
        "--bound-artifact-sha256",
        F._sha(artifact),
        "--expect-source-cells",
        json.dumps({"SRC_A": 10, "SRC_B": 10}),
        "--audit-a-total",
        str(
            audit_a_total
            if audit_a_total is not None
            else int(np.load(artifact, allow_pickle=True)["libraries"].sum())
        ),
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=900)


def test_v2_consistent_artifact_checks_every_donor_and_source_cell(tmp_path: Path) -> None:
    libs = F._libs()
    root, manifest = F._build_store(tmp_path, libs)
    artifact = F._build_artifact(tmp_path, libs)
    pass1 = F._build_pass1(tmp_path)
    proc = _run_v2(tmp_path, root, manifest, artifact, pass1, donor_sample=0)
    assert proc.returncode == 0, proc.stdout[-3000:] + proc.stderr[-3000:]
    d = json.loads((tmp_path / "out-v2.json").read_text())
    assert d["schema"] == "V5_FULL104_HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2"
    assert d["all_104_donor_library_totals_agree"] is True
    assert d["per_cell_source_vector_agrees"] is True
    assert d["failures"] == []


def test_v2_catches_cross_donor_library_swap_even_when_global_total_is_identical(
    tmp_path: Path,
) -> None:
    metadata_libs = F._libs()
    root, manifest = F._build_store(tmp_path, metadata_libs)

    artifact_libs = metadata_libs.copy()
    artifact_libs[0] += 7
    artifact_libs[F.CELLS_PER_DONOR] -= 7
    assert artifact_libs.sum() == metadata_libs.sum()

    artifact = F._build_artifact(tmp_path, artifact_libs)
    pass1 = F._build_pass1(tmp_path)
    proc = _run_v2(
        tmp_path,
        root,
        manifest,
        artifact,
        pass1,
        donor_sample=0,
        audit_a_total=int(metadata_libs.sum()),
    )
    assert proc.returncode != 0
    d = json.loads((tmp_path / "out-v2.json").read_text())
    assert d["three_route_total_agreement"] is True
    assert d["all_104_donor_library_totals_agree"] is False
    assert any("per-donor source-library totals" in x for x in d["failures"])


def test_v2_catches_per_cell_source_vector_corruption_that_preserves_source_counts(
    tmp_path: Path,
) -> None:
    libs = F._libs()
    root, manifest = F._build_store(tmp_path, libs)
    artifact = F._build_artifact(tmp_path, libs)
    pass1 = F._build_pass1(tmp_path)

    with np.load(artifact, allow_pickle=True) as d:
        payload = {name: np.array(d[name], copy=True) for name in d.files}
    src = payload["src_of_cell"]
    # Swap one SRC_A and one SRC_B code: aggregate source counts are unchanged.
    a = 0
    b = 2 * F.CELLS_PER_DONOR
    src[a], src[b] = src[b], src[a]
    np.savez_compressed(artifact, **payload)

    proc = _run_v2(tmp_path, root, manifest, artifact, pass1, donor_sample=0)
    assert proc.returncode != 0
    d = json.loads((tmp_path / "out-v2.json").read_text())
    assert d["per_cell_source_vector_agrees"] is False
    assert any("per-cell source vector" in x for x in d["failures"])
