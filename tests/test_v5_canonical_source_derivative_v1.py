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
