"""Attacks on the T0 V20 pathology-blind feature-projection authority.

S2 must turn the accepted V20 feature split into an ordered projection over the
frozen 41,238-address space, and the ordering is the science: the split's own row
order is the authority, not address order. Every attack below encodes a way that
projection could look correct while silently reading different genes, in a
different order, or genes the matrix does not measure.

Pinned-source discipline carries over from the checkpoint validator repairs:
tracked authorities resolve from Git blob bytes at an explicit commit, a missing
object stops before any digest is taken, and a non-canonical path is refused.

Written before the implementation.
"""

from __future__ import annotations

import csv
import hashlib
import io
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import t0_v20_feature_projection_authority_v1 as fp  # noqa: E402

MATRIX_ID = "sea_ad_mtg_rna_final_2026"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "safe.directory=*", *args], cwd=repo, check=True,
        capture_output=True, text=True).stdout.strip()


def _split_bytes(rows: list[tuple[str, str, str]]) -> bytes:
    """`molecular_address_id, symbol, feature_role` in a deliberate order."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["molecular_address_index", "molecular_address_id", "symbol",
                     "biotype", "feature_role", "split_namespace", "split_hash"])
    for index, (address, symbol, role) in enumerate(rows):
        writer.writerow([index, address, symbol, "protein_coding", role,
                         "T0-MTG-FEATURE-SPLIT-V2", "deadbeef"])
    return buffer.getvalue().encode("utf-8")


def _registry_bytes(addresses: list[tuple[int, str]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["molecular_address_index", "molecular_address_id", "identity_class",
                     "symbol"])
    for index, address in addresses:
        writer.writerow([index, address, "current_exact", "SYM%d" % index])
    return buffer.getvalue().encode("utf-8")


def _support_bytes(entries: list[tuple[int, str, bool]], matrix_id: str = MATRIX_ID) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["matrix_id", "source_dataset_id", "molecular_address_index",
                     "molecular_address_id", "measured_address", "measurement_status"])
    for index, address, measured in entries:
        writer.writerow([matrix_id, "SEA_AD_COMMON", index, address, str(bool(measured)),
                         "addressable_measured_zero_or_nonzero_at_runtime" if measured
                         else "structurally_unmeasured"])
    return buffer.getvalue().encode("utf-8")


@pytest.fixture()
def world():
    """Split order deliberately differs from address-index order."""
    split = [("ENSG00000000005", "TNMD", "SCORING"),
             ("ENSG00000000003", "TSPAN6", "SCORING"),
             ("ENSG00000000419", "DPM1", "COHERENCE_HOLDOUT")]
    registry = [(0, "ENSG00000000003"), (1, "ENSG00000000005"), (2, "ENSG00000000419"),
                (3, "ENSG00000000457")]
    support = [(0, "ENSG00000000003", True), (1, "ENSG00000000005", True),
               (2, "ENSG00000000419", True), (3, "ENSG00000000457", False)]
    return _split_bytes(split), _registry_bytes(registry), _support_bytes(support)


def _build(world, **overrides):
    split, registry, support = world
    kwargs = dict(split_bytes=split, registry_bytes=registry, support_bytes=support,
                  matrix_id=MATRIX_ID)
    kwargs.update(overrides)
    return fp.build_feature_projection(**kwargs)


# --------------------------------------------------------------------------
# The ordering IS the science.
# --------------------------------------------------------------------------
def test_the_projection_preserves_exact_split_row_order(world) -> None:
    built = _build(world)
    assert [row["molecular_address_id"] for row in built["projection"]] == [
        "ENSG00000000005", "ENSG00000000003", "ENSG00000000419",
    ]
    assert [row["molecular_address_index"] for row in built["projection"]] == [1, 0, 2]
    assert [row["split_row_index"] for row in built["projection"]] == [0, 1, 2]
    assert built["projected_feature_count"] == 3


def test_sorting_by_address_index_is_a_different_projection(world) -> None:
    """Address order and split order genuinely differ, so the root must too."""
    built = _build(world)
    by_index = sorted(built["projection"], key=lambda row: row["molecular_address_index"])
    assert [row["molecular_address_id"] for row in by_index] != [
        row["molecular_address_id"] for row in built["projection"]
    ]
    assert fp.projection_root(by_index) != built["projection_root_sha256"]


def test_a_reordered_split_produces_a_different_root(world) -> None:
    split, registry, support = world
    reordered = _split_bytes([("ENSG00000000003", "TSPAN6", "SCORING"),
                              ("ENSG00000000005", "TNMD", "SCORING"),
                              ("ENSG00000000419", "DPM1", "COHERENCE_HOLDOUT")])
    first = _build(world)["projection_root_sha256"]
    second = fp.build_feature_projection(
        split_bytes=reordered, registry_bytes=registry, support_bytes=support,
        matrix_id=MATRIX_ID)["projection_root_sha256"]
    assert first != second


# --------------------------------------------------------------------------
# Structural refusals.
# --------------------------------------------------------------------------
def test_a_structurally_unmeasured_feature_stops(world) -> None:
    split, registry, support = world
    with_unmeasured = _split_bytes([("ENSG00000000457", "X", "SCORING")])
    with pytest.raises(AssertionError, match="FEATURE_NOT_MEASURED"):
        fp.build_feature_projection(
            split_bytes=with_unmeasured, registry_bytes=registry,
            support_bytes=support, matrix_id=MATRIX_ID)


def test_an_address_absent_from_the_registry_stops(world) -> None:
    split, registry, support = world
    foreign = _split_bytes([("ENSG_NOT_IN_REGISTRY", "X", "SCORING")])
    with pytest.raises(AssertionError, match="ADDRESS_NOT_IN_REGISTRY"):
        fp.build_feature_projection(
            split_bytes=foreign, registry_bytes=registry, support_bytes=support,
            matrix_id=MATRIX_ID)


def test_a_duplicate_split_address_stops(world) -> None:
    split, registry, support = world
    duplicated = _split_bytes([("ENSG00000000003", "TSPAN6", "SCORING"),
                               ("ENSG00000000003", "TSPAN6", "SCORING")])
    with pytest.raises(AssertionError, match="SPLIT_ADDRESS_NOT_UNIQUE"):
        fp.build_feature_projection(
            split_bytes=duplicated, registry_bytes=registry, support_bytes=support,
            matrix_id=MATRIX_ID)


def test_a_registry_with_a_duplicate_index_stops(world) -> None:
    split, _registry, support = world
    broken = _registry_bytes([(0, "ENSG00000000003"), (0, "ENSG00000000005"),
                              (2, "ENSG00000000419")])
    with pytest.raises(AssertionError, match="REGISTRY_INDEX_NOT_INJECTIVE"):
        fp.build_feature_projection(
            split_bytes=split, registry_bytes=broken, support_bytes=support,
            matrix_id=MATRIX_ID)


def test_an_out_of_range_index_stops(world) -> None:
    split, _registry, support = world
    bad = _registry_bytes([(0, "ENSG00000000003"), (99, "ENSG00000000005"),
                           (2, "ENSG00000000419")])
    with pytest.raises(AssertionError, match="ADDRESS_INDEX_OUT_OF_RANGE"):
        fp.build_feature_projection(
            split_bytes=split, registry_bytes=bad, support_bytes=support,
            matrix_id=MATRIX_ID, address_space_size=3)


def test_support_for_the_wrong_matrix_stops(world) -> None:
    split, registry, _support = world
    other = _support_bytes([(0, "ENSG00000000003", True), (1, "ENSG00000000005", True),
                            (2, "ENSG00000000419", True)], matrix_id="sea_ad_ang_rna_final_2026")
    with pytest.raises(AssertionError, match="NO_SUPPORT_ROWS_FOR_MATRIX"):
        fp.build_feature_projection(
            split_bytes=split, registry_bytes=registry, support_bytes=other,
            matrix_id=MATRIX_ID)


def test_a_mutated_feature_role_changes_the_root(world) -> None:
    split, registry, support = world
    mutated = _split_bytes([("ENSG00000000005", "TNMD", "SCORING"),
                            ("ENSG00000000003", "TSPAN6", "SCORING"),
                            ("ENSG00000000419", "DPM1", "SCORING")])
    assert _build(world)["projection_root_sha256"] != fp.build_feature_projection(
        split_bytes=mutated, registry_bytes=registry, support_bytes=support,
        matrix_id=MATRIX_ID)["projection_root_sha256"]


def test_an_unknown_feature_role_stops(world) -> None:
    split, registry, support = world
    bogus = _split_bytes([("ENSG00000000003", "TSPAN6", "INVENTED_ROLE")])
    with pytest.raises(AssertionError, match="FEATURE_ROLE_NOT_AUTHORIZED"):
        fp.build_feature_projection(
            split_bytes=bogus, registry_bytes=registry, support_bytes=support,
            matrix_id=MATRIX_ID)


def test_source_feature_index_is_never_consulted() -> None:
    """The provenance column is not an h5ad position and must not be used.

    Four of four spot checks showed it landing on unrelated genes, so a module
    that read it would silently project the wrong columns.
    """
    source = Path(fp.__file__).read_text(encoding="utf-8")
    assert "source_feature_index" not in source.replace(
        "source_feature_index is never", "")


# --------------------------------------------------------------------------
# Pinned-source resolution.
# --------------------------------------------------------------------------
@pytest.fixture()
def pinned_repo(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "T")
    _git(repo, "config", "user.email", "t@example.invalid")
    payload = b"authority,rows\nalpha,1\n"
    (repo / "authority.csv").write_bytes(payload)
    _git(repo, "add", "authority.csv")
    _git(repo, "commit", "-m", "init")
    return repo, hashlib.sha256(payload).hexdigest()


def test_a_pinned_blob_resolves_by_digest(pinned_repo) -> None:
    repo, digest = pinned_repo
    commit = _git(repo, "rev-parse", "HEAD")
    payload = fp.resolve_pinned_blob(repo, commit, "authority.csv", digest)
    assert hashlib.sha256(payload).hexdigest() == digest


def test_a_missing_pinned_object_stops_before_any_digest(pinned_repo) -> None:
    repo, _digest = pinned_repo
    commit = _git(repo, "rev-parse", "HEAD")
    empty = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    with pytest.raises(AssertionError, match="PINNED_OBJECT_ABSENT"):
        fp.resolve_pinned_blob(repo, commit, "not/there.csv", empty)


def test_a_wrong_pinned_digest_stops(pinned_repo) -> None:
    repo, _digest = pinned_repo
    commit = _git(repo, "rev-parse", "HEAD")
    with pytest.raises(AssertionError, match="PINNED_BLOB_DIGEST"):
        fp.resolve_pinned_blob(repo, commit, "authority.csv", "0" * 64)


def test_a_noncanonical_pinned_path_stops(pinned_repo) -> None:
    repo, digest = pinned_repo
    commit = _git(repo, "rev-parse", "HEAD")
    for hostile in (":authority.csv", "./authority.csv", "../authority.csv",
                    "C:/authority.csv"):
        with pytest.raises(AssertionError, match="PINNED_PATH_NOT_CANONICAL"):
            fp.resolve_pinned_blob(repo, commit, hostile, digest)


def test_the_wrong_pinned_commit_stops(pinned_repo) -> None:
    repo, digest = pinned_repo
    first = _git(repo, "rev-parse", "HEAD")
    (repo / "authority.csv").write_bytes(b"authority,rows\nbeta,2\n")
    _git(repo, "add", "authority.csv")
    _git(repo, "commit", "-m", "second")
    second = _git(repo, "rev-parse", "HEAD")
    assert first != second
    assert hashlib.sha256(
        fp.resolve_pinned_blob(repo, first, "authority.csv", digest)).hexdigest() == digest
    with pytest.raises(AssertionError, match="PINNED_BLOB_DIGEST"):
        fp.resolve_pinned_blob(repo, second, "authority.csv", digest)
