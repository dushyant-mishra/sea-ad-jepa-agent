"""Attacks on the T0 V20 pathology-blind feature-projection authority.

S2 must turn the accepted V20 feature split into an ordered projection over the
frozen 41,238-address space, and the ordering is the science: the split's own row
order is the authority, not address order. Every adversarial case below encodes a way that
projection could look correct while silently reading different genes, in a
different order, or genes the matrix does not measure.

Pinned-source discipline carries over from the checkpoint validator repairs:
tracked authorities resolve from Git blob bytes at an explicit commit, a missing
object stops before any digest is taken, and a non-canonical path is refused.

Written before the implementation.

Scope: this module verifies the integrity of this project's own data-provenance
records, in this repository. No third-party system, no network, no credentials,
no cryptanalysis, and no security control belonging to any system is
circumvented. The only check being probed is our own SHA-256 comparison, and
these cases exist to show it cannot be satisfied by anything but the bytes it
claims to describe. See docs/agent/T0_LANE_SECURITY_SCOPE.md.
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


# The real split carries a molecular_address_index column, and the projection
# now STOPs if it disagrees with the frozen registry rather than letting the
# registry quietly win. So a fixture must declare the index it actually means.
SPLIT_INDEX = {
    "ENSG00000000003": 0,
    "ENSG00000000005": 1,
    "ENSG00000000419": 2,
    "ENSG00000000457": 3,
    "ENSG_NOT_IN_REGISTRY": "",
}


def _split_bytes(rows: list[tuple[str, str, str]],
                 index_override: dict[str, object] | None = None) -> bytes:
    """`molecular_address_id, symbol, feature_role` in a deliberate order."""
    lookup = dict(SPLIT_INDEX)
    lookup.update(index_override or {})
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["molecular_address_index", "molecular_address_id", "symbol",
                     "biotype", "feature_role", "split_namespace", "split_hash",
                     "source_feature_index"])
    for address, symbol, role in rows:
        # source_feature_index is deliberately bogus: it is provenance for a
        # different feature universe and must never reach the projection.
        writer.writerow([lookup.get(address, ""), address, symbol, "protein_coding",
                         role, "T0-MTG-FEATURE-SPLIT-V2", "deadbeef", 999999])
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
    # Split, registry and support must all AGREE on the index here, otherwise a
    # disagreement check fires first and the range guard is never exercised.
    agreeing = _split_bytes(
        [("ENSG00000000005", "TNMD", "SCORING"),
         ("ENSG00000000003", "TSPAN6", "SCORING"),
         ("ENSG00000000419", "DPM1", "COHERENCE_HOLDOUT")],
        index_override={"ENSG00000000005": 99})
    bad = _registry_bytes([(0, "ENSG00000000003"), (99, "ENSG00000000005"),
                           (2, "ENSG00000000419")])
    matching_support = _support_bytes([(0, "ENSG00000000003", True),
                                       (99, "ENSG00000000005", True),
                                       (2, "ENSG00000000419", True)])
    with pytest.raises(AssertionError, match="ADDRESS_INDEX_OUT_OF_RANGE"):
        fp.build_feature_projection(
            split_bytes=agreeing, registry_bytes=bad, support_bytes=matching_support,
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


def test_bogus_source_feature_index_values_cannot_reach_the_projection(world) -> None:
    """Behavioural, replacing an earlier static substring check.

    The substring test was the same fail-open class already condemned in F1B: it
    passed on the text of the module rather than on what the module does, and it
    broke as soon as an unrelated field name mentioned the token. Here every
    split row carries `source_feature_index = 999999`, which is out of range for
    the address space, and the emitted indices must still come exclusively from
    the Stage81A2R registry.
    """
    split, registry, support = world
    assert b"999999" in split, "the fixture must actually carry the bogus provenance"
    built = _build(world)
    assert [row["molecular_address_index"] for row in built["projection"]] == [1, 0, 2]
    assert all(row["molecular_address_index"] != 999999 for row in built["projection"])
    # And the projection carries no field derived from it.
    for row in built["projection"]:
        assert set(row) == {"split_row_index", "molecular_address_id",
                            "molecular_address_index", "feature_role"}
    assert built["source_feature_index_used"] is False


def test_a_split_index_disagreeing_with_the_registry_stops(world) -> None:
    """Ignoring the split's own index column let a disagreement pass silently."""
    split, registry, support = world
    conflicting = _split_bytes(
        [("ENSG00000000003", "TSPAN6", "SCORING")],
        index_override={"ENSG00000000003": 7})
    with pytest.raises(AssertionError, match="SPLIT_INDEX_DISAGREES_WITH_REGISTRY"):
        fp.build_feature_projection(
            split_bytes=conflicting, registry_bytes=registry, support_bytes=support,
            matrix_id=MATRIX_ID)


def test_a_support_index_disagreeing_with_the_registry_stops(world) -> None:
    split, registry, _support = world
    conflicting = _support_bytes([(0, "ENSG00000000003", True),
                                  (5, "ENSG00000000005", True),
                                  (2, "ENSG00000000419", True)])
    with pytest.raises(AssertionError, match="SUPPORT_INDEX_DISAGREES_WITH_REGISTRY"):
        fp.build_feature_projection(
            split_bytes=split, registry_bytes=registry, support_bytes=conflicting,
            matrix_id=MATRIX_ID)


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
    for invalid in (":authority.csv", "./authority.csv", "../authority.csv",
                    "C:/authority.csv"):
        with pytest.raises(AssertionError, match="PINNED_PATH_NOT_CANONICAL"):
            fp.resolve_pinned_blob(repo, commit, invalid, digest)


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


# --------------------------------------------------------------------------
# The authority root must bind what the rows MEAN, not only the rows.
#
# `projection_root_sha256` binds the ordered rows and nothing else, so the same
# root still verified after altering the matrix id, the address-space size, the
# split, registry or support digests, the schema, the role counts, or
# `real_execution_ready`. Independent review found exactly that.
# --------------------------------------------------------------------------
BINDING = {
    "split_member_path": "current/authority/T0_MTG_FEATURE_ROLE_SPLIT_V2.csv",
    "split_sha256": "a" * 64,
    "registry_sha256": "b" * 64,
    "support_gzip_sha256": "c" * 64,
    "support_plain_sha256": "d" * 64,
    "stage81a2r_pin": "95d2cafe5cde68773f81c4aa64afc5788ae1d73b",
}


def _bound(world, **overrides):
    binding = dict(BINDING)
    binding.update(overrides.pop("binding", {}))
    return _build(world, authority_binding=binding, **overrides)


def test_an_unbound_projection_has_no_authority_root(world) -> None:
    built = _build(world)
    assert "feature_authority_root_sha256" not in built
    with pytest.raises(AssertionError, match="FEATURE_AUTHORITY_BINDING_ABSENT"):
        fp.feature_authority_root(built)


def test_a_bound_projection_verifies_against_both_external_roots(world) -> None:
    built = _bound(world)
    checked = fp.assert_feature_authority_lawful(
        built,
        expected_feature_authority_root_sha256=built["feature_authority_root_sha256"],
        expected_projection_root_sha256=built["projection_root_sha256"])
    assert checked["features"] == 3


@pytest.mark.parametrize("field,value", [
    ("matrix_id", "sea_ad_ang_rna_final_2026"),
    ("address_space_size", 999),
    ("schema", "FORGED_SCHEMA"),
    ("namespace", "FORGED_NAMESPACE"),
    ("ordering", "ADDRESS_INDEX_ORDER"),
    ("source_feature_index_used", True),
])
def test_mutating_authority_metadata_moves_the_authority_root(world, field, value) -> None:
    """Each of these left the projection root untouched before this repair."""
    built = _bound(world)
    original_projection = built["projection_root_sha256"]
    original_authority = built["feature_authority_root_sha256"]
    substituted = dict(built)
    substituted[field] = value
    assert fp.projection_root(substituted["projection"]) == original_projection, (
        "the rows are untouched, which is exactly why row-only binding failed"
    )
    assert fp.feature_authority_root(substituted) != original_authority
    with pytest.raises(AssertionError, match="FEATURE_AUTHORITY_ROOT_MISMATCH"):
        fp.assert_feature_authority_lawful(
            substituted,
            expected_feature_authority_root_sha256=original_authority,
            expected_projection_root_sha256=original_projection)


@pytest.mark.parametrize("field", ["split_sha256", "registry_sha256",
                                   "support_gzip_sha256", "support_plain_sha256",
                                   "stage81a2r_pin", "split_member_path"])
def test_mutating_a_bound_provenance_digest_moves_the_authority_root(world, field) -> None:
    built = _bound(world)
    substituted = dict(built)
    substituted["authority_binding"] = dict(built["authority_binding"])
    substituted["authority_binding"][field] = "f" * 64
    assert fp.feature_authority_root(substituted) != built["feature_authority_root_sha256"]
    with pytest.raises(AssertionError, match="FEATURE_AUTHORITY_ROOT_MISMATCH"):
        fp.assert_feature_authority_lawful(
            substituted,
            expected_feature_authority_root_sha256=built["feature_authority_root_sha256"],
            expected_projection_root_sha256=built["projection_root_sha256"])


def test_mutated_role_counts_move_the_authority_root(world) -> None:
    built = _bound(world)
    substituted = dict(built)
    substituted["role_counts"] = {"SCORING": 99, "COHERENCE_HOLDOUT": 1}
    assert fp.feature_authority_root(substituted) != built["feature_authority_root_sha256"]


def test_claiming_execution_readiness_is_refused(world) -> None:
    built = _bound(world)
    substituted = dict(built)
    substituted["real_execution_ready"] = True
    with pytest.raises(AssertionError, match="FEATURE_AUTHORITY_CLAIMS_READINESS"):
        fp.assert_feature_authority_lawful(
            substituted,
            expected_feature_authority_root_sha256=fp.feature_authority_root(substituted),
            expected_projection_root_sha256=built["projection_root_sha256"])


def test_an_incomplete_binding_is_refused(world) -> None:
    """The builder itself refuses a partial binding, which is stricter."""
    for missing in BINDING:
        partial = {key: value for key, value in BINDING.items() if key != missing}
        with pytest.raises(AssertionError, match="FEATURE_AUTHORITY_BINDING_ABSENT"):
            _build(world, authority_binding=partial)


def test_the_production_constructor_enforces_the_frozen_geometry(
    pinned_repo, world, tmp_path: Path
) -> None:
    """A silently different split must not pass as the accepted one."""
    repo, digest = pinned_repo
    commit = _git(repo, "rev-parse", "HEAD")
    split, registry, support = world
    import gzip
    gz = gzip.compress(support)
    (repo / "registry.csv").write_bytes(registry)
    (repo / "support.csv.gz").write_bytes(gz)
    _git(repo, "add", "registry.csv", "support.csv.gz")
    _git(repo, "commit", "-m", "authorities")
    pin = _git(repo, "rev-parse", "HEAD")

    kwargs = dict(
        repo=repo, split_bytes=split,
        split_member_path="current/authority/T0_MTG_FEATURE_ROLE_SPLIT_V2.csv",
        expected_split_sha256=hashlib.sha256(split).hexdigest(),
        stage81a2r_pin=pin,
        registry_relative_path="registry.csv",
        expected_registry_sha256=hashlib.sha256(registry).hexdigest(),
        support_relative_path="support.csv.gz",
        expected_support_gzip_sha256=hashlib.sha256(gz).hexdigest(),
        matrix_id=MATRIX_ID,
    )
    # The three-feature fixture is not the production geometry.
    with pytest.raises(AssertionError, match="PRODUCTION_GEOMETRY_UNEXPECTED"):
        fp.build_production_feature_authority(**kwargs)

    built = fp.build_production_feature_authority(
        expect_production_geometry=False, **kwargs)
    assert built["feature_authority_root_sha256"]
    assert built["authority_binding"]["stage81a2r_pin"] == pin
    assert built["authority_binding"]["split_sha256"] == hashlib.sha256(split).hexdigest()

    # A wrong declared split digest stops before anything is resolved.
    with pytest.raises(AssertionError, match="PINNED_BLOB_DIGEST"):
        fp.build_production_feature_authority(
            **{**kwargs, "expected_split_sha256": "0" * 64,
               "expect_production_geometry": False})
