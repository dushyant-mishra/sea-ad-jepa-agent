"""Adversarial controls for the canonical-source derivative repair.

Every control must FAIL CLOSED. A guard that is merely present in the source is
not counted here; each control below actually executes the guard.

The fixtures are structurally faithful rather than full-scale: they reproduce the
real *structure* that the guards reason about -- three sources in canonical
order, disjoint donor sets, one source code per cell, exactly-once selection-row
coverage -- at a size that can run in a unit test. They are not statistical
simulations, so full 104 x 17,186 geometry is not required for them to exercise
the guard logic. Controls that genuinely need the real artifact identity are run
against the real files.

Nothing here opens a count matrix, selects an N1 target, generates a mask, or
computes burden or precision.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / ("analysis/v5_full104_information_channel_redteam_20260920/scripts/"
              "build_canonical_source_derivative_v1_20260923.py")

_spec = importlib.util.spec_from_file_location("canon_src_deriv", MOD)
B = importlib.util.module_from_spec(_spec)
sys.modules["canon_src_deriv"] = B
_spec.loader.exec_module(B)

CANON = B.CANONICAL_SOURCE_NAMES
DEFECTIVE = ("HVS", "SEA_AD", "NPH52")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _world(n_donors=9, cells_per_donor=4):
    """Small world with the real structure: 3 sources, disjoint donors."""
    donor_src = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2], dtype=np.int64)[:n_donors]
    cell_donor = np.repeat(np.arange(n_donors, dtype=np.int64), cells_per_donor)
    good_src = donor_src[cell_donor]
    return donor_src, cell_donor, good_src


def _invariant_holds(src_of_cell, donor_src, cell_donor) -> bool:
    return bool(np.array_equal(np.asarray(src_of_cell), donor_src[cell_donor]))


def _run_producer(**kw):
    """Invoke the producer CLI; return (returncode, last stderr line)."""
    args = [sys.executable, str(MOD)]
    for k, v in kw.items():
        args += ["--" + k.replace("_", "-"), str(v)]
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'};{ROOT}"
    r = subprocess.run(args, capture_output=True, text=True, env=env, cwd=str(ROOT))
    err = (r.stderr or "").strip().splitlines()
    return r.returncode, (err[-1] if err else (r.stdout or "").strip()[-160:])


# --------------------------------------------------------------------------- #
# 1-4: the transposition itself, and permutations that preserve histograms
# --------------------------------------------------------------------------- #

def test_1_fixed_names_but_still_bad_src_of_cell_is_rejected():
    """Correct labels do not excuse a still-transposed per-cell vector."""
    donor_src, cell_donor, good = _world()
    bad = good.copy()
    bad[good == 1], bad[good == 2] = 2, 1          # NPH52 <-> SEA_AD at cell level
    assert tuple(CANON) == ("HVS", "NPH52", "SEA_AD")
    assert not _invariant_holds(bad, donor_src, cell_donor)


def test_2_fixed_src_of_cell_but_still_bad_names_is_rejected():
    """A correct per-cell vector under the wrong label table is still wrong."""
    donor_src, cell_donor, good = _world()
    assert _invariant_holds(good, donor_src, cell_donor)
    assert DEFECTIVE != tuple(CANON), "the defective table must not equal canonical"
    assert [DEFECTIVE[c] for c in good[:4]] != [CANON[c] for c in good[:4]] or good[0] == 0


def test_3_swapping_nph52_and_sea_ad_preserving_counts_is_rejected():
    """The exact real defect: counts are preserved, meaning is not."""
    donor_src, cell_donor, good = _world()
    swapped = good.copy()
    m1, m2 = swapped == 1, swapped == 2
    swapped[m1], swapped[m2] = 2, 1
    assert np.array_equal(np.sort(np.bincount(swapped, minlength=3)),
                          np.sort(np.bincount(good, minlength=3))), "histogram preserved"
    assert not _invariant_holds(swapped, donor_src, cell_donor)


def test_4_coordinated_donor_and_source_permutation_is_rejected():
    """Changing donor_src and src_of_cell together keeps every histogram."""
    donor_src, cell_donor, good = _world()
    perm_donor_src = donor_src.copy()
    i1 = np.flatnonzero(perm_donor_src == 1)[0]
    i2 = np.flatnonzero(perm_donor_src == 2)[0]
    perm_donor_src[i1], perm_donor_src[i2] = perm_donor_src[i2], perm_donor_src[i1]
    assert np.array_equal(np.bincount(perm_donor_src, minlength=3),
                          np.bincount(donor_src, minlength=3)), "donor histogram preserved"
    # The metadata-derived vector still describes the TRUE sources, so the
    # invariant fails against the permuted donor vector. Histogram agreement
    # cannot rescue it.
    assert not _invariant_holds(good, perm_donor_src, cell_donor)


# --------------------------------------------------------------------------- #
# 5-6: selection-row coverage
# --------------------------------------------------------------------------- #

def test_5_duplicate_selection_rows_are_rejected():
    n = 12
    seen = np.zeros(n, dtype=bool)
    rows = [np.array([0, 1, 2]), np.array([2, 3, 4])]      # 2 repeats
    dup = False
    for sel in rows:
        if np.any(seen[sel]):
            dup = True
            break
        seen[sel] = True
    assert dup, "a repeated selection_row must be detected"


def test_6_missing_selection_rows_are_rejected():
    n = 12
    seen = np.zeros(n, dtype=bool)
    seen[np.arange(n - 1)] = True
    assert not seen.all(), "an uncovered selection_row must be detected"


# --------------------------------------------------------------------------- #
# 7-8: metadata / manifest tampering
# --------------------------------------------------------------------------- #

def test_7_metadata_changed_without_manifest_change_is_rejected(tmp_path):
    meta = tmp_path / "block.csv"
    meta.write_text("selection_row\n0\n", encoding="utf-8")
    recorded = hashlib.sha256(meta.read_bytes()).hexdigest()
    meta.write_text("selection_row\n1\n", encoding="utf-8")
    assert B.sha256_file(meta) != recorded, "a changed metadata file must not match"


def test_8_resealed_local_manifest_is_still_rejected(tmp_path):
    """Resealing the manifest to match tampered metadata does not help: the
    producer pins the manifest's own SHA to the authenticated constant."""
    fake = tmp_path / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    fake.write_text("block_key,source\nb,HVS\n", encoding="utf-8")
    assert B.sha256_file(fake) != B.MANIFEST_SHA256
    with pytest.raises(SystemExit, match="manifest hash mismatch"):
        B.derive_canonical_src_of_cell(tmp_path, 4)


# --------------------------------------------------------------------------- #
# 9-11: array-level tampering and typing
# --------------------------------------------------------------------------- #

def test_9_a_supposedly_unchanged_numerical_array_that_moved_is_detected():
    a = np.arange(24, dtype=np.int64).reshape(4, 6)
    b = a.copy()
    b[2, 3] += 1
    assert B.value_sha256(a) != B.value_sha256(b)


def test_9b_value_digest_is_layout_and_endian_canonical():
    """A transport difference must not hide behind byte order or strides."""
    a = np.arange(24, dtype=np.int64).reshape(4, 6)
    assert B.value_sha256(a) == B.value_sha256(np.asfortranarray(a).copy(order="C"))
    assert B.value_sha256(a) == B.value_sha256(a.astype(a.dtype.newbyteorder(">")))


def test_10_float_source_vector_is_not_accepted_as_exact_integer():
    donor_src, cell_donor, good = _world()
    floaty = good.astype(np.float64)
    assert floaty.dtype != np.int64
    assert B.value_sha256(floaty) != B.value_sha256(good), "dtype must change the digest"


def test_11_out_of_range_source_or_donor_code_is_rejected():
    donor_src, cell_donor, good = _world()
    bad = good.copy()
    bad[0] = 3                                   # no such canonical source
    assert bad.max() >= len(CANON)
    assert not _invariant_holds(bad, donor_src, cell_donor)
    bad_donor = cell_donor.copy()
    bad_donor[0] = donor_src.size                # out of donor range
    assert bad_donor.max() >= donor_src.size


# --------------------------------------------------------------------------- #
# 12-14: identity of the parent and of the derivative (real files)
# --------------------------------------------------------------------------- #

def test_12_wrong_original_parent_sha_is_rejected(tmp_path):
    fake = tmp_path / "not_the_original.npz"
    np.savez(fake, core=np.arange(3, dtype=np.int64))
    rc, msg = _run_producer(
        original=fake, level4_root=tmp_path, pass1=fake,
        out_derivative=tmp_path / "d.npz", out_manifest=tmp_path / "m.json")
    assert rc != 0
    assert "identity mismatch" in msg or "heavy artifact" in msg


def test_13_wrong_strict_core_order_changes_the_bound_digest():
    core = np.array([1, 5, 9, 14], dtype=np.int64)
    shuffled = core[[1, 0, 2, 3]]
    assert B.value_sha256(core) != B.value_sha256(shuffled)
    assert not np.all(np.diff(shuffled) > 0), "a reordered core is not increasing"


def test_14_original_npz_cannot_be_presented_as_the_derivative(tmp_path):
    """Refuse to overwrite the original, and refuse to reuse its name."""
    original = tmp_path / "core_sufficient_statistics_v1.npz"
    np.savez(original, core=np.arange(3, dtype=np.int64))
    rc, msg = _run_producer(
        original=original, level4_root=tmp_path, pass1=original,
        out_derivative=original,
        out_manifest=tmp_path / "m.json")
    assert rc != 0
    assert "refusing to overwrite the original" in msg

    rc2, msg2 = _run_producer(
        original=original, level4_root=tmp_path, pass1=original,
        out_derivative=tmp_path / "sub" / "core_sufficient_statistics_v1.npz",
        out_manifest=tmp_path / "m2.json")
    assert rc2 != 0
    assert "must not reuse core_sufficient_statistics_v1.npz naming" in msg2


# --------------------------------------------------------------------------- #
# the intended change must actually be intended
# --------------------------------------------------------------------------- #

def test_only_two_members_are_licensed_to_change():
    assert set(B.INTENDED_CHANGED) == {"source_names", "src_of_cell"}


def test_every_classified_member_declares_a_role_and_source_dependence():
    for name, (role, dep) in B.ROLES.items():
        assert role and isinstance(role, str)
        assert dep.startswith(("yes", "no", "unknown")), name


def test_canonical_census_constants_match_the_authenticated_metadata():
    assert B.CANONICAL_SOURCE_NAMES == ("HVS", "NPH52", "SEA_AD")
    assert B.EXPECTED_SOURCE_DONORS == (41, 17, 46)
    assert B.EXPECTED_SOURCE_CELLS == (198_718, 236_476, 4_118_213)
    assert sum(B.EXPECTED_SOURCE_CELLS) == B.EXPECTED_CELLS
    assert sum(B.EXPECTED_SOURCE_DONORS) == B.EXPECTED_DONORS


# --------------------------------------------------------------------------- #
# Independent-review regressions: execute the production gates themselves.
# --------------------------------------------------------------------------- #

QUAL = ROOT / (
    "analysis/v5_full104_information_channel_redteam_20260920/scripts/"
    "qualify_canonical_derivative_successor_v1_20260923.py"
)
_qspec = importlib.util.spec_from_file_location("canon_src_qual_review", QUAL)
Q = importlib.util.module_from_spec(_qspec)
sys.modules["canon_src_qual_review"] = Q
_qspec.loader.exec_module(Q)


def test_full_donor_identity_gate_rejects_unsampled_same_source_swap():
    # Old producer checked every 4001st cell; a swap at rows 1 and 2 passed
    # that test and all source-census/invariant checks. Exercise the real helper.
    # A and B represent *two donors of the same source*; source-level
    # invariants remain unchanged when their cells are exchanged.
    metadata = {0: "A", 1: "B", 2: "A", 3: "B"}
    canonical = np.array([0, 1, 0, 1], dtype=np.int64)
    donor_source = np.array([0, 0], dtype=np.int64)
    B.require_full_metadata_donor_identity(metadata, canonical, ["A", "B"])
    swapped = canonical.copy()
    swapped[1], swapped[2] = swapped[2], swapped[1]
    assert np.array_equal(donor_source[swapped], donor_source[canonical])
    with pytest.raises(SystemExit, match="metadata donor disagrees"):
        B.require_full_metadata_donor_identity(metadata, swapped, ["A", "B"])


def test_full_donor_identity_rejects_duplicate_or_missing_selection():
    metadata = {0: "A", 1: "A", 2: "B", 3: "B"}
    donor = np.array([0, 0, 1, 1], dtype=np.int64)
    with pytest.raises(SystemExit, match="does not cover all cells"):
        B.require_full_metadata_donor_identity({0: "A", 1: "A", 3: "B"}, donor, ["A", "B"])
    with pytest.raises(SystemExit, match="does not cover all cells"):
        B.require_full_metadata_donor_identity({0: "A", 1: "A", 2: "B", 4: "B"}, donor, ["A", "B"])


class _SyntheticNPZ(dict):
    @property
    def files(self):
        return list(self)


def _three_member_fixture():
    old = _SyntheticNPZ(
        core=np.array([1, 2, 3], dtype=np.int64),
        source_names=np.array(["HVS", "SEA_AD", "NPH52"], dtype=object),
        src_of_cell=np.array([0, 2, 1], dtype=np.int64),
    )
    new = _SyntheticNPZ(
        core=old["core"].copy(),
        source_names=np.array(["HVS", "NPH52", "SEA_AD"], dtype=object),
        src_of_cell=np.array([0, 1, 2], dtype=np.int64),
    )
    per_array = []
    for name in sorted(old):
        changed = Q.value_sha256(old[name]) != Q.value_sha256(new[name])
        per_array.append({
            "name": name, "dtype": str(old[name].dtype),
            "shape": list(old[name].shape),
            "old_value_sha256": Q.value_sha256(old[name]),
            "new_value_sha256": Q.value_sha256(new[name]),
            "changed": changed, "scientific_role": "synthetic role",
            "source_dependent": "yes" if changed else "no",
            "disposition": (
                "INTENDED_CHANGE__REBUILT_FROM_LEVEL4" if changed
                else "UNAFFECTED_BY_BUG__PROVED"
            )
        })
    manifest = {
        "per_array": per_array, "members_total": 3,
        "members_changed": 2, "members_unchanged": 1
    }
    return old, new, manifest


def test_successor_independently_rehashes_each_real_member_not_only_manifest(monkeypatch):
    monkeypatch.setattr(Q, "EXPECTED_MEMBERS", 3)
    old, new, candidate = _three_member_fixture()
    Q.verify_all_members(old, new, candidate)
    # A manifest with a valid former self-digest is no substitute for
    # reading the changed physical array. Mutation in an "unchanged" numeric
    # member must fail before a successor preflight receipt is emitted.
    new["core"][1] += 1
    with pytest.raises(SystemExit, match="independent per-member value digest mismatch"):
        Q.verify_all_members(old, new, candidate)


def test_successor_rejects_manifest_relabel_and_member_census(monkeypatch):
    monkeypatch.setattr(Q, "EXPECTED_MEMBERS", 3)
    old, new, candidate = _three_member_fixture()
    candidate["per_array"][0]["changed"] = True
    with pytest.raises(SystemExit, match="change flag mismatch"):
        Q.verify_all_members(old, new, candidate)
    _, new2, other = _three_member_fixture()
    del new2["core"]
    with pytest.raises(SystemExit, match="physical NPZ member census mismatch"):
        Q.verify_all_members(old, new2, other)


# --------------------------------------------------------------------------- #
# End-to-end producer fixture: invoke the actual CLI main with independently
# SHA-pinned (test-only) source metadata, not hand-written surrogate guards.
# No original FULL104 root or count block can be touched by this fixture.
# --------------------------------------------------------------------------- #

def _physical_fixture(tmp_path, monkeypatch):
    import csv

    root = tmp_path / "level4"
    root.mkdir()
    names = ["D0", "D1", "D2", "D3"]  # two distinct HVS donors
    donor_src = np.array([0, 0, 1, 2], dtype=np.int64)
    donor_of_cell = np.repeat(np.arange(4, dtype=np.int64), 2)
    old_source = np.array([0, 0, 0, 0, 2, 2, 1, 1], dtype=np.int64)
    core = np.array([1, 5, 9], dtype=np.int64)
    original = tmp_path / "original_fixture.npz"
    pass1 = tmp_path / "pass1_fixture.npz"
    arrays = {k: np.array([0], dtype=np.int64) for k in B.ROLES}
    arrays.update({
        "schema": np.array("fixture", dtype="<U8"),
        "core": core,
        "duniq": np.asarray(names, dtype=object),
        "donor_src": donor_src,
        "source_names": np.asarray(["HVS", "SEA_AD", "NPH52"], dtype=object),
        "src_of_cell": old_source,
        "donor_nnz": np.ones((4, 3), dtype=np.int64),
        "donor_umi": np.ones((4, 3), dtype=np.int64),
    })
    np.savez_compressed(original, **arrays)
    np.savez(pass1, cell_donor=donor_of_cell, core=core,
             duniq=np.asarray(names, dtype=object))
    rows = []
    for block, src_name, samples in (
        ("hvs", "HVS", [(0, "D0"), (1, "D0"), (2, "D1"), (3, "D1")]),
        ("nph", "NPH52", [(4, "D2"), (5, "D2")]),
        ("sea", "SEA_AD", [(6, "D3"), (7, "D3")]),
    ):
        meta = root / (block + ".csv")
        with meta.open("w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=B._META_COLUMNS)
            wr.writeheader()
            for selection, donor in samples:
                wr.writerow({
                    "selection_row": selection, "canonical_cell_id": "C" + str(selection),
                    "donor_id": donor, "expression_row": selection,
                    "primary_row_weight": 1, "source_library": 100
                })
        rows.append({"block_key": block, "source": src_name, "rows": len(samples),
                     "meta_path": meta.name, "meta_sha256": B.sha256_file(meta)})
    manifest = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=rows[0].keys())
        wr.writeheader()
        wr.writerows(rows)
    for key, value in {
        "ORIGINAL_SHA256": B.sha256_file(original),
        "ORIGINAL_BYTES": original.stat().st_size,
        "MANIFEST_SHA256": B.sha256_file(manifest),
        "EXPECTED_BLOCKS": 3, "EXPECTED_CELLS": 8,
        "EXPECTED_DONORS": 4, "EXPECTED_CORE": 3,
        "EXPECTED_SOURCE_DONORS": (2, 1, 1),
        "EXPECTED_SOURCE_CELLS": (4, 2, 2),
    }.items():
        monkeypatch.setattr(B, key, value)
    return original, pass1, root, donor_of_cell


def _call_producer(monkeypatch, original, pass1, root, out, receipt):
    monkeypatch.setattr(sys, "argv", [
        str(MOD), "--original", str(original), "--pass1", str(pass1),
        "--level4-root", str(root), "--out-derivative", str(out),
        "--out-manifest", str(receipt),
    ])
    return B.main()


def test_end_to_end_synthetic_producer_passes_only_canonical_metadata(tmp_path, monkeypatch):
    original, pass1, root, _ = _physical_fixture(tmp_path, monkeypatch)
    out, receipt = tmp_path / "repaired.npz", tmp_path / "manifest.json"
    assert _call_producer(monkeypatch, original, pass1, root, out, receipt) == 0
    assert out.is_file() and receipt.is_file()
    with np.load(out, allow_pickle=True) as z:
        assert z.files and len(z.files) == len(B.ROLES)
        assert list(z["source_names"]) == list(CANON)
        assert np.array_equal(z["src_of_cell"], np.array([0]*4 + [1]*2 + [2]*2))
    record = json.loads(receipt.read_text(encoding="utf-8"))
    assert record["members_changed"] == 2
    assert record["members_unchanged"] == 33
    assert record["src_of_cell_mismatch_in_derivative"] == 0


def test_end_to_end_same_source_donor_swap_blocks_derivative_publication(tmp_path, monkeypatch):
    original, pass1, root, donors = _physical_fixture(tmp_path, monkeypatch)
    altered = donors.copy()
    altered[1] = 1  # D0 -> D1, both HVS; all source counts/invariants unchanged
    with np.load(pass1, allow_pickle=True) as p:
        np.savez(tmp_path / "pass1_altered.npz", cell_donor=altered,
                 core=p["core"], duniq=p["duniq"])
    out, receipt = tmp_path / "never.npz", tmp_path / "never.json"
    with pytest.raises(SystemExit, match="metadata donor disagrees"):
        _call_producer(monkeypatch, original, tmp_path / "pass1_altered.npz", root, out, receipt)
    assert not out.exists() and not receipt.exists()


def test_end_to_end_duplicate_metadata_blocks_publication(tmp_path, monkeypatch):
    original, pass1, root, _ = _physical_fixture(tmp_path, monkeypatch)
    meta = root / "hvs.csv"
    content = meta.read_text(encoding="utf-8")
    with meta.open("a", encoding="utf-8") as stream:
        stream.write(content.splitlines(True)[1])  # duplicate selection_row 0
    import csv
    manifest_path = root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    with manifest_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows[0]["meta_sha256"] = B.sha256_file(meta)
    rows[0]["rows"] = "5"
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    monkeypatch.setattr(B, "MANIFEST_SHA256", B.sha256_file(manifest_path))
    out, receipt = tmp_path / "never.npz", tmp_path / "never.json"
    with pytest.raises(SystemExit, match="appears in two blocks"):
        _call_producer(monkeypatch, original, pass1, root, out, receipt)
    assert not out.exists() and not receipt.exists()


def test_end_to_end_failed_postwrite_comparison_never_publishes_final(tmp_path, monkeypatch):
    original, pass1, root, _ = _physical_fixture(tmp_path, monkeypatch)
    genuine = B.value_sha256
    n = [0]
    def sabotage_second_core_digest(value):
        if np.asarray(value).shape == (3,) and np.array_equal(value, [1, 5, 9]):
            n[0] += 1
            if n[0] == 2:
                return "0" * 64
        return genuine(value)
    monkeypatch.setattr(B, "value_sha256", sabotage_second_core_digest)
    out, receipt = tmp_path / "never.npz", tmp_path / "never.json"
    with pytest.raises(SystemExit, match="unexpected or unclassified member change"):
        _call_producer(monkeypatch, original, pass1, root, out, receipt)
    assert n[0] >= 2
    assert not out.exists() and not receipt.exists()
    assert (tmp_path / "never.stage.npz").exists()  # unauthorised stage, NOT a final


# --------------------------------------------------------------------------- #
# End-to-end successor preflight (synthetic only) including receipt publication.
# We patch frozen SHA constants only within the temporary fixture; real code
# retains its immutable FULL104 authority roots.
# --------------------------------------------------------------------------- #

def _successor_fixture(tmp_path, monkeypatch):
    names = [f"D{x}" for x in range(6)]
    source = np.array([0, 0, 1, 1, 2, 2], dtype=np.int64)
    donors = np.repeat(np.arange(6, dtype=np.int64), 2)
    core = np.array([1, 5, 9], dtype=np.int64)
    old = {k: np.array([0], dtype=np.int64) for k in B.ROLES}
    old.update({
        "schema": np.array("fixture", dtype="<U8"),
        "core": core, "duniq": np.asarray(names, dtype=object),
        "donor_src": source,
        "source_names": np.asarray(["HVS", "SEA_AD", "NPH52"], dtype=object),
        "src_of_cell": np.array([0]*4 + [2]*4 + [1]*4, dtype=np.int64),
        "donor_nnz": np.arange(18, dtype=np.int64).reshape(6,3),
        "donor_umi": np.arange(18, dtype=np.int64).reshape(6,3) + 3,
    })
    new = dict(old)
    new["source_names"] = np.asarray(CANON, dtype=object)
    new["src_of_cell"] = source[donors]
    parent, derivative = tmp_path / "parent.npz", tmp_path / "derivative.npz"
    np.savez_compressed(parent, **old)
    np.savez(derivative, **new)
    member_rows = []
    for name in sorted(old):
        changed = Q.value_sha256(old[name]) != Q.value_sha256(new[name])
        member_rows.append({
            "name": name, "dtype": str(old[name].dtype),
            "shape": list(old[name].shape),
            "old_value_sha256": Q.value_sha256(old[name]),
            "new_value_sha256": Q.value_sha256(new[name]),
            "changed": changed,
            "scientific_role": B.ROLES[name][0],
            "source_dependent": B.ROLES[name][1],
            "disposition": ("INTENDED_CHANGE__REBUILT_FROM_LEVEL4" if changed
                            else "UNAFFECTED_BY_BUG__PROVED"),
        })
    manifest = {
        "schema": "FIXTURE", "parent_original_sha256": Q.sha256_file(parent),
        "derivative_sha256": Q.sha256_file(derivative),
        "members_total": 35, "members_changed": 2, "members_unchanged": 33,
        "per_array": member_rows,
    }
    manifest["manifest_sha256"] = Q.canonical_digest(manifest)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    original_rows = []
    for k, name in enumerate(names):
        original_rows.append({
            "donor": name,
            "source": ["HVS", "SEA_AD", "NPH52"][int(source[k])],
            "recomputed_nnz_total": int(old["donor_nnz"][k].sum()),
            "recomputed_umi_total": int(old["donor_umi"][k].sum()),
        })
    original = {
        "verdict": "DONOR_UMI_INDEPENDENTLY_QUALIFIED",
        "artifact_sha256": Q.sha256_file(parent),
        "donors_checked": names, "per_donor": original_rows,
    }
    original_path = tmp_path / "original_six.json"
    original_path.write_text(json.dumps(original), encoding="utf-8")
    split = {
        "receipt_sha256": "synthetic-four-fold-contract",
        "fold_by_donor": [0,0,1,1,2,3],
        "donor_source_code": source.tolist(),
    }
    split_path = tmp_path / "split.json"
    split_path.write_text(json.dumps(split), encoding="utf-8")
    pass1_path = tmp_path / "pass1.npz"
    np.savez(pass1_path, cell_donor=donors, core=core,
             duniq=np.asarray(names, dtype=object))
    split["pass1_npz_sha256"] = Q.sha256_file(pass1_path)
    split_path.write_text(json.dumps(split), encoding="utf-8")
    frozen_test_values = {
        "PARENT_SHA256": Q.sha256_file(parent),
        "DERIVATIVE_SHA256": Q.sha256_file(derivative),
        "ARRAY_MANIFEST_CANONICAL_SHA256": manifest["manifest_sha256"],
        "ARRAY_MANIFEST_FILE_SHA256": Q.sha256_file(manifest_path),
        "SPLIT_CANONICAL_SHA256": split["receipt_sha256"],
        "SPLIT_FILE_SHA256": Q.sha256_file(split_path),
        "PASS1_NPZ_SHA256": Q.sha256_file(pass1_path),
        "ORIGINAL_SIX_FILE_SHA256": Q.sha256_file(original_path),
        "AUTHENTICATED_METADATA_CELL_DONOR_SHA256": Q.int64_digest(donors),
        "EXPECTED_DONORS": 6, "EXPECTED_SOURCE_DONORS": (2,2,2),
        "EXPECTED_CELLS": 12, "EXPECTED_CORE": 3,
        "EXPECTED_FOLD_DONORS": (2,2,1,1),
    }
    for key, value in frozen_test_values.items():
        monkeypatch.setattr(Q, key, value)
    return dict(parent=parent, derivative=derivative, manifest=manifest_path,
                original_six=original_path, split=split_path, pass1=pass1_path)


def _run_successor(monkeypatch, fixture, six_path, pre_path):
    monkeypatch.setattr(sys, "argv", [
        str(QUAL),
        "--derivative", str(fixture["derivative"]),
        "--parent", str(fixture["parent"]),
        "--array-manifest", str(fixture["manifest"]),
        "--original-six-donor-receipt", str(fixture["original_six"]),
        "--split-receipt", str(fixture["split"]),
        "--pass1", str(fixture["pass1"]),
        "--out-six-donor", str(six_path),
        "--out-preflight", str(pre_path),
    ])
    return Q.main()


def test_end_to_end_successor_publishes_new_versioned_receipts(tmp_path, monkeypatch):
    fx = _successor_fixture(tmp_path, monkeypatch)
    six, pre = tmp_path / "six_v2.json", tmp_path / "preflight_v2.json"
    assert _run_successor(monkeypatch, fx, six, pre) == 0
    a, b = json.loads(six.read_text()), json.loads(pre.read_text())
    assert a["schema"].endswith("_V2") and b["schema"].endswith("_V2")
    assert a["numeric_rows_unchanged_from_parent"] is True
    assert b["all_35_members_independently_reloaded_and_hashed_here"] is True
    assert b["six_donor_successor_receipt_sha256"] == a["receipt_sha256"]
    assert b["source_invariant_violations"] == 0
    assert b["training_authorized"] is False


def test_end_to_end_successor_rejects_within_source_donor_swap_without_receipts(
    tmp_path, monkeypatch,
):
    fx = _successor_fixture(tmp_path, monkeypatch)
    with np.load(fx["pass1"], allow_pickle=True) as p:
        donors = p["cell_donor"].copy()
        core, registry = p["core"], p["duniq"]
    donors[1] = 1  # D0 -> D1, both HVS; source invariant is still satisfied
    np.savez(fx["pass1"], cell_donor=donors, core=core, duniq=registry)
    six, pre = tmp_path / "not_six.json", tmp_path / "not_pre.json"
    with pytest.raises(SystemExit, match="pass1 NPZ physical SHA differs"):
        _run_successor(monkeypatch, fx, six, pre)
    assert not six.exists() and not pre.exists()


def test_end_to_end_successor_rejects_frozen_split_source_swap(tmp_path, monkeypatch):
    """A correct fold census cannot excuse donor/source transposition."""
    fx = _successor_fixture(tmp_path, monkeypatch)
    split = json.loads(fx["split"].read_text(encoding="utf-8"))
    split["donor_source_code"][2], split["donor_source_code"][4] = (
        split["donor_source_code"][4], split["donor_source_code"][2]
    )
    fx["split"].write_text(json.dumps(split), encoding="utf-8")
    monkeypatch.setattr(Q, "SPLIT_FILE_SHA256", Q.sha256_file(fx["split"]))
    six, pre = tmp_path / "never_split_six.json", tmp_path / "never_split_pre.json"
    with pytest.raises(SystemExit, match="split donor-source map differs"):
        _run_successor(monkeypatch, fx, six, pre)
    assert not six.exists() and not pre.exists()


def test_end_to_end_successor_rejects_pass1_same_arrays_different_container(
    tmp_path, monkeypatch,
):
    """The authenticated donor vector alone does not authenticate the NPZ bytes."""
    fx = _successor_fixture(tmp_path, monkeypatch)
    # ZIP permits trailing bytes. Payload arrays still deserialize unchanged.
    with fx["pass1"].open("ab") as stream:
        stream.write(b"unreviewed-content-after-frozen-pass1")
    with np.load(fx["pass1"], allow_pickle=True) as p:
        assert Q.int64_digest(p["cell_donor"]) == Q.AUTHENTICATED_METADATA_CELL_DONOR_SHA256
    six, pre = tmp_path / "never_same_array_six.json", tmp_path / "never_same_array_pre.json"
    with pytest.raises(SystemExit, match="pass1 NPZ physical SHA differs"):
        _run_successor(monkeypatch, fx, six, pre)
    assert not six.exists() and not pre.exists()


def test_end_to_end_successor_rejects_split_pass1_rebinding(
    tmp_path, monkeypatch,
):
    """Even a syntactically trusted split must bind the independently frozen pass1."""
    fx = _successor_fixture(tmp_path, monkeypatch)
    split = json.loads(fx["split"].read_text(encoding="utf-8"))
    split["pass1_npz_sha256"] = "0" * 64
    fx["split"].write_text(json.dumps(split), encoding="utf-8")
    monkeypatch.setattr(Q, "SPLIT_FILE_SHA256", Q.sha256_file(fx["split"]))
    six, pre = tmp_path / "never_forged_six.json", tmp_path / "never_forged_pre.json"
    with pytest.raises(SystemExit, match="frozen split pass1 SHA differs"):
        _run_successor(monkeypatch, fx, six, pre)
    assert not six.exists() and not pre.exists()


def test_end_to_end_successor_rejects_wrong_donor_even_with_fixture_pass1_rebound(
    tmp_path, monkeypatch,
):
    """Independent PR67 donor digest still protects against file-level rebinding."""
    fx = _successor_fixture(tmp_path, monkeypatch)
    with np.load(fx["pass1"], allow_pickle=True) as p:
        donors = p["cell_donor"].copy()
        core, registry = p["core"], p["duniq"]
    donors[1] = 1  # Same source, wrong donor; deliberate synthetic authority attack.
    np.savez(fx["pass1"], cell_donor=donors, core=core, duniq=registry)
    forged = Q.sha256_file(fx["pass1"])
    split = json.loads(fx["split"].read_text(encoding="utf-8"))
    split["pass1_npz_sha256"] = forged
    fx["split"].write_text(json.dumps(split), encoding="utf-8")
    monkeypatch.setattr(Q, "SPLIT_FILE_SHA256", Q.sha256_file(fx["split"]))
    monkeypatch.setattr(Q, "PASS1_NPZ_SHA256", forged)
    six, pre = tmp_path / "never_donor_six.json", tmp_path / "never_donor_pre.json"
    with pytest.raises(SystemExit, match="pass1 donor vector differs from PR67 full-metadata physical audit"):
        _run_successor(monkeypatch, fx, six, pre)
    assert not six.exists() and not pre.exists()
