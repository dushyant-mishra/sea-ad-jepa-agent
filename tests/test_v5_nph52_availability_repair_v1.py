"""Tests for the NPH52 availability repair and the successor census audit.

EVERY REFUSAL TEST IS PAIRED WITH A PASSING BASELINE

  A test that asserts "this refuses" proves nothing unless the same fixture,
  unmutated, is shown to succeed - otherwise the refusal could be firing for a
  reason that has nothing to do with the mutation. Each negative control below
  mutates exactly one thing away from a baseline that is asserted to pass in
  the same test.

  The fixtures are synthetic. Where a reserved readout ADDRESS NUMBER appears
  it is a label in fabricated data used to exercise the governance branch; no
  real readout is read anywhere in this file.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V5 = os.path.join(REPO, "scripts", "v5")
REPAIR = os.path.join(V5, "full104_nph52_availability_repair_v1.py")
AUDIT_V1 = os.path.join(V5, "audit_candidate_pool_census_v1.py")
AUDIT_V2 = os.path.join(V5, "audit_candidate_pool_census_v2.py")

N_ADDR = 41238
MATRIX_ID = "NPH52::matrix::TEST_object.qs"
DATASET_ID = "NPH52::TEST_object.qs"
OTHER_MATRIX_ID = "SEA_AD::matrix::other"
VERDICT = "FEATURE_AXIS_VERIFIED__ZERO_BASED__MATERIALIZER_INDEXING_CORRECT"

# 2810 is a reserved readout number, used here only as a label on fabricated
# counts so the governance branch can be exercised.
ADDR_PRESENT = 100
ADDR_ABSENT = 200
ADDR_ABSENT_RESERVED = 2810


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(script, *args):
    return subprocess.run([sys.executable, script, *args],
                          capture_output=True, text=True)


# --------------------------------------------------------------------------
# fixtures for the repair
# --------------------------------------------------------------------------
def write_provenance(path, addresses, dataset_id=DATASET_ID, blocked_sfi=()):
    """One provenance row per address; blocked_sfi rows get their own index."""
    rows = []
    for k, a in enumerate(addresses):
        rows.append({"molecular_address_index": int(a),
                     "source_dataset_id": dataset_id,
                     "source_feature_index": int(k)})
    for k, a in enumerate(blocked_sfi):
        rows.append({"molecular_address_index": int(a),
                     "source_dataset_id": dataset_id,
                     "source_feature_index": 10_000 + k})
    pd.DataFrame(rows).to_csv(path, index=False, compression="gzip")


def write_collision_tables(ledger, unreg, blocked_indices, matrix_id=MATRIX_ID):
    pd.DataFrame({"matrix_id": [matrix_id] * len(blocked_indices),
                  "source_feature_index": list(blocked_indices)}
                 ).to_csv(ledger, index=False, compression="gzip")
    pd.DataFrame({"matrix_id": [], "source_dataset_id": [],
                  "molecular_address_id": [], "source_feature_indices": []}
                 ).to_csv(unreg, index=False)


def write_artifact(path, cols, avail, counts, matrix_ids):
    n = len(matrix_ids)
    np.savez_compressed(
        path,
        cell_id=np.asarray([f"c{i}" for i in range(n)], dtype=object),
        source=np.asarray(["NPH52" if m == MATRIX_ID else "SEA_AD"
                           for m in matrix_ids], dtype=object),
        donor_id=np.asarray([f"d{i % 3}" for i in range(n)], dtype=object),
        matrix_id=np.asarray(matrix_ids, dtype=object),
        total_excluding_29=np.arange(n, dtype=np.int64) + 100,
        address_columns=np.asarray(cols, dtype=np.int64),
        counts=np.asarray(counts, dtype=np.int32),
        address_available=np.asarray(avail, dtype=bool))


def write_axis_receipt(path, provenance_sha, verdict=VERDICT, agreement=1.0,
                       dataset_id=DATASET_ID):
    json.dump({"schema": "V5_NPH52_FEATURE_AXIS_VERIFIER_V1",
               "source_dataset_id": dataset_id,
               "verdict": verdict,
               "agreement_zero_based": agreement,
               "digests": {"provenance": provenance_sha}},
              open(path, "w"))


def build_repair_fixture(tmp_path, counts_at_absent=0, blocked=()):
    """Baseline: 4 NPH52 rows + 2 other rows; ADDR_ABSENT/RESERVED off-axis."""
    cols = [ADDR_PRESENT, ADDR_ABSENT, ADDR_ABSENT_RESERVED]
    matrix_ids = [MATRIX_ID] * 4 + [OTHER_MATRIX_ID] * 2
    counts = np.array([[5, counts_at_absent, 0]] * 4 + [[7, 3, 1]] * 2)
    avail = np.ones((6, 3), dtype=bool)

    prov = str(tmp_path / "prov.csv.gz")
    on_axis = [ADDR_PRESENT] + list(blocked)
    write_provenance(prov, on_axis, blocked_sfi=())
    ledger = str(tmp_path / "ledger.csv.gz")
    unreg = str(tmp_path / "unreg.csv")
    # every blocked address's only row is source_feature_index >= 1
    blocked_idx = [i for i, a in enumerate(on_axis) if a in set(blocked)]
    write_collision_tables(ledger, unreg, blocked_idx)

    art = str(tmp_path / "artifact.npz")
    write_artifact(art, cols, avail, counts, matrix_ids)
    rec = str(tmp_path / "extraction.json")
    json.dump({"schema": "V5_FULL104_MYELOID_R8_PANEL_EXTRACTION_V1",
               "decoder_status_by_matrix": {MATRIX_ID: {"status": "IDENTITY"}}},
              open(rec, "w"))
    axis = str(tmp_path / "axis.json")
    write_axis_receipt(axis, sha_file(prov))
    return {"artifact": art, "receipt": rec, "prov": prov, "axis": axis,
            "ledger": ledger, "unreg": unreg, "cols": cols}


def repair_args(f, out, with_collisions=False):
    a = ["--artifact", f["artifact"], "--extraction-receipt", f["receipt"],
         "--nph52-provenance", f["prov"], "--axis-receipt", f["axis"],
         "--source-dataset-id", DATASET_ID, "--matrix-id", MATRIX_ID,
         "--out-dir", out]
    if with_collisions:
        a += ["--collision-ledger", f["ledger"],
              "--unregistered-collisions", f["unreg"]]
    return a


# --------------------------------------------------------------------------
# the repair does what it says
# --------------------------------------------------------------------------
def test_repair_derives_availability_and_leaves_everything_else_alone(tmp_path):
    f = build_repair_fixture(tmp_path)
    out = str(tmp_path / "out")
    r = run(REPAIR, *repair_args(f, out))
    assert r.returncode == 0, r.stderr

    rec = json.load(open(os.path.join(
        out, "FULL104_NPH52_AVAILABILITY_REPAIR_V1.json")))
    assert rec["addresses_absent_from_authenticated_axis"] == [
        ADDR_ABSENT, ADDR_ABSENT_RESERVED]
    assert rec["nuclei_in_target_matrix"] == 4
    assert rec["mask_elements_changed"] == 4 * 2 == rec[
        "mask_elements_changed_expected"]

    old = np.load(f["artifact"], allow_pickle=True)
    new = np.load(os.path.join(out, "FULL104_MYELOID_R8_PANEL_COUNTS_V2.npz"),
                  allow_pickle=True)
    j_present = f["cols"].index(ADDR_PRESENT)
    j_absent = f["cols"].index(ADDR_ABSENT)
    tgt = new["matrix_id"].astype(str) == MATRIX_ID

    # the off-axis addresses become unavailable for the target matrix only
    assert not new["address_available"][tgt, j_absent].any()
    assert new["address_available"][tgt, j_present].all()
    assert new["address_available"][~tgt, j_absent].all()
    # counts and every other array are carried verbatim
    assert np.array_equal(old["counts"], new["counts"])
    assert np.array_equal(old["total_excluding_29"], new["total_excluding_29"])
    assert list(old.keys()) == list(new.keys())


def test_reserved_readout_flip_is_recorded_unchecked_not_passing(tmp_path):
    f = build_repair_fixture(tmp_path)
    out = str(tmp_path / "out")
    assert run(REPAIR, *repair_args(f, out)).returncode == 0
    rec = json.load(open(os.path.join(
        out, "FULL104_NPH52_AVAILABILITY_REPAIR_V1.json")))
    by_addr = {c["address"]: c for c in rec["mask_value_consistency"]}
    assert by_addr[ADDR_ABSENT_RESERVED]["check"] == "UNCHECKED_BY_GOVERNANCE"
    assert "pass" not in by_addr[ADDR_ABSENT_RESERVED]
    # the non-reserved one IS checked, so the governance branch is not a
    # blanket excuse for skipping the check
    assert by_addr[ADDR_ABSENT]["check"] == "COUNTS_ALL_ZERO"
    assert by_addr[ADDR_ABSENT]["pass"] is True
    assert rec["protected_outcomes_opened"] is False


# --------------------------------------------------------------------------
# negative controls, each against a baseline shown to pass
# --------------------------------------------------------------------------
def test_refuses_when_a_nonreserved_absent_address_carries_a_nonzero_count(tmp_path):
    ok_dir = tmp_path / "ok"
    ok_dir.mkdir()
    ok = build_repair_fixture(ok_dir)
    assert run(REPAIR, *repair_args(ok, str(tmp_path / "ok_out"))).returncode == 0

    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    bad = build_repair_fixture(bad_dir, counts_at_absent=9)
    r = run(REPAIR, *repair_args(bad, str(tmp_path / "bad_out")))
    assert r.returncode != 0
    assert "REFUSED_MASK_AND_VALUES_DISAGREE" in (r.stdout + r.stderr)


def test_refuses_an_unverified_axis_receipt(tmp_path):
    f = build_repair_fixture(tmp_path)
    assert run(REPAIR, *repair_args(f, str(tmp_path / "ok"))).returncode == 0
    write_axis_receipt(f["axis"], sha_file(f["prov"]),
                       verdict="FEATURE_AXIS_MISMATCH__SHARES_THE_LEVEL4_DEFECT")
    r = run(REPAIR, *repair_args(f, str(tmp_path / "bad")))
    assert r.returncode != 0
    assert "REFUSE_AXIS_NOT_VERIFIED" in (r.stdout + r.stderr)


def test_refuses_a_provenance_file_the_verifier_did_not_verify(tmp_path):
    f = build_repair_fixture(tmp_path)
    assert run(REPAIR, *repair_args(f, str(tmp_path / "ok"))).returncode == 0
    write_axis_receipt(f["axis"], "0" * 64)
    r = run(REPAIR, *repair_args(f, str(tmp_path / "bad")))
    assert r.returncode != 0
    assert "REFUSE_PROVENANCE_NOT_THE_VERIFIED_COPY" in (r.stdout + r.stderr)


def test_refuses_when_raw_and_materialized_axes_disagree(tmp_path):
    """ADDR_PRESENT is on the raw axis but entirely collision-blocked, so the
    materializer could never have written it. The two axes disagree and the
    mask is ambiguous."""
    cols = [ADDR_PRESENT, ADDR_ABSENT, ADDR_ABSENT_RESERVED]
    matrix_ids = [MATRIX_ID] * 4 + [OTHER_MATRIX_ID] * 2
    counts = np.zeros((6, 3), dtype=np.int32)
    prov = str(tmp_path / "prov.csv.gz")
    write_provenance(prov, [ADDR_PRESENT])
    ledger = str(tmp_path / "ledger.csv.gz")
    unreg = str(tmp_path / "unreg.csv")
    art = str(tmp_path / "artifact.npz")
    write_artifact(art, cols, np.ones((6, 3), bool), counts, matrix_ids)
    rec = str(tmp_path / "extraction.json")
    json.dump({"decoder_status_by_matrix": {}}, open(rec, "w"))
    axis = str(tmp_path / "axis.json")
    write_axis_receipt(axis, sha_file(prov))
    f = {"artifact": art, "receipt": rec, "prov": prov, "axis": axis,
         "ledger": ledger, "unreg": unreg, "cols": cols}

    # baseline: nothing blocked -> the axes agree and the repair succeeds
    write_collision_tables(ledger, unreg, [])
    assert run(REPAIR, *repair_args(f, str(tmp_path / "ok"),
                                    with_collisions=True)).returncode == 0
    # mutate one thing: block the only row carrying ADDR_PRESENT
    write_collision_tables(ledger, unreg, [0])
    r = run(REPAIR, *repair_args(f, str(tmp_path / "bad"), with_collisions=True))
    assert r.returncode != 0
    assert "REFUSED_AXES_DISAGREE_ON_A_TARGET_ADDRESS" in (r.stdout + r.stderr)


def test_refuses_a_nonempty_output_directory(tmp_path):
    f = build_repair_fixture(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    (out / "something").write_text("x")
    r = run(REPAIR, *repair_args(f, str(out)))
    assert r.returncode != 0 and "STOP_OUTPUT_EXISTS" in (r.stdout + r.stderr)


# --------------------------------------------------------------------------
# the successor audit's denominator
# --------------------------------------------------------------------------
sys.path.insert(0, V5)


def build_census_fixture(tmp_path, s2_artifact_marks_available):
    """Two sources; address ADDR_ABSENT is structurally absent for S2 in the
    census. `s2_artifact_marks_available` decides whether the artifact agrees.
    """
    from full104_candidate_pool_census_v1 import split_donors

    cols = [ADDR_PRESENT, ADDR_ABSENT, ADDR_ABSENT_RESERVED]
    srcs, donors, mids = [], [], []
    for s, mid in (("NPH52", MATRIX_ID), ("SEA_AD", OTHER_MATRIX_ID)):
        for d in ("d0", "d1", "d2"):
            for _ in range(2):
                srcs.append(s); donors.append(d); mids.append(mid)
    n = len(srcs)
    rng = np.random.default_rng(7)
    counts = rng.integers(0, 5, size=(n, 3)).astype(np.int32)
    avail = np.ones((n, 3), dtype=bool)
    src = np.asarray(srcs)
    avail[(src == "SEA_AD"), cols.index(ADDR_ABSENT)] = s2_artifact_marks_available

    art = str(tmp_path / "artifact.npz")
    np.savez_compressed(
        art,
        cell_id=np.asarray([f"c{i}" for i in range(n)], dtype=object),
        source=np.asarray(srcs, dtype=object),
        donor_id=np.asarray(donors, dtype=object),
        matrix_id=np.asarray(mids, dtype=object),
        total_excluding_29=np.full(n, 100, dtype=np.int64),
        address_columns=np.asarray(cols, dtype=np.int64),
        counts=counts, address_available=avail)

    assign = split_donors(zip(srcs, donors))
    is_fit = np.array([assign[(s, d)] == "FIT" for s, d in zip(srcs, donors)])

    payload = {"sources": np.asarray(["NPH52", "SEA_AD"], dtype=object)}
    for s in ("NPH52", "SEA_AD"):
        mean = np.full(N_ADDR, np.nan); det = np.full(N_ADDR, np.nan)
        fano = np.full(N_ADDR, np.nan); nav = np.zeros(N_ADDR, np.int64)
        for a in (ADDR_PRESENT, ADDR_ABSENT):
            if s == "SEA_AD" and a == ADDR_ABSENT:
                continue                       # census: structurally absent
            j = cols.index(a)
            cells = is_fit & (src == s) & avail[:, j]
            v = counts[cells, j].astype(np.float64)
            nav[a] = int(cells.sum())
            mean[a] = v.mean()
            det[a] = (v > 0).mean()
            fano[a] = v.var() / v.mean() if v.mean() > 0 else np.nan
        payload[f"{s}__mean"] = mean; payload[f"{s}__detect"] = det
        payload[f"{s}__fano"] = fano; payload[f"{s}__n_available"] = nav
    cen = str(tmp_path / "census.npz")
    np.savez_compressed(cen, **payload)

    fit = sorted({f"{s}|{d}" for s, d, k in zip(srcs, donors, is_fit) if k})
    ev = sorted({f"{s}|{d}" for s, d, k in zip(srcs, donors, is_fit) if not k})
    rec = str(tmp_path / "census.json")
    json.dump({"fitting_donors": fit, "evaluation_donors_never_used": ev,
               "fitting_nuclei": int(is_fit.sum())}, open(rec, "w"))
    return art, cen, rec


def _cross(out_dir, name):
    j = json.load(open(os.path.join(out_dir, name)))
    return j["checks"]["cross_path_agreement"], j


def test_v2_counts_the_both_unavailable_pair_that_v1_drops(tmp_path):
    """The whole point of the successor: a fixed denominator."""
    art, cen, rec = build_census_fixture(tmp_path, s2_artifact_marks_available=False)
    common = ["--census", cen, "--receipt", rec, "--artifact", art]

    o1 = str(tmp_path / "v1")
    assert run(AUDIT_V1, *common, "--out-dir", o1).returncode == 0
    c1, _ = _cross(o1, "AUDIT_CANDIDATE_POOL_CENSUS_V1.json")

    o2 = str(tmp_path / "v2")
    assert run(AUDIT_V2, *common, "--out-dir", o2).returncode == 0
    c2, _ = _cross(o2, "AUDIT_CANDIDATE_POOL_CENSUS_V2.json")

    # 2 sources x 2 non-reserved addresses
    assert c2["comparisons"] == c2["comparisons_expected"] == 4
    assert c2["agreeing"] == 4 and c2["both_structurally_unavailable"] == 1
    assert c2["denominator_is_fixed"] is True
    # v1 silently drops the both-unavailable pair from BOTH sides
    assert c1["comparisons"] == 3 and c1["agreeing"] == 3
    assert c1["comparisons"] < c2["comparisons"]


def test_v2_still_fails_a_real_availability_disagreement(tmp_path):
    """Positive control for the check itself: it must be able to fail."""
    art, cen, rec = build_census_fixture(tmp_path, s2_artifact_marks_available=True)
    o2 = str(tmp_path / "v2")
    r = run(AUDIT_V2, "--census", cen, "--receipt", rec, "--artifact", art,
            "--out-dir", o2)
    assert r.returncode != 0
    c2, j = _cross(o2, "AUDIT_CANDIDATE_POOL_CENSUS_V2.json")
    assert c2["comparisons"] == 4 and c2["agreeing"] == 3
    assert any("AVAILABILITY DISAGREEMENT" in f for f in j["failures"])


def test_v2_axis_check_catches_an_over_claim_the_census_cannot_see(tmp_path):
    """The census comparison is blind to an address both paths call available
    wrongly, and to every reserved readout. The axis check is not."""
    art, cen, rec = build_census_fixture(tmp_path, s2_artifact_marks_available=False)
    prov = str(tmp_path / "prov.csv.gz")

    # baseline: the axis carries every address the artifact marks available
    write_provenance(prov, [ADDR_PRESENT, ADDR_ABSENT, ADDR_ABSENT_RESERVED])
    ok = str(tmp_path / "axis_ok")
    r = run(AUDIT_V2, "--census", cen, "--receipt", rec, "--artifact", art,
            "--nph52-provenance", prov, "--nph52-matrix-id", MATRIX_ID,
            "--nph52-source-dataset-id", DATASET_ID, "--out-dir", ok)
    assert r.returncode == 0, r.stdout + r.stderr
    j = json.load(open(os.path.join(ok, "AUDIT_CANDIDATE_POOL_CENSUS_V2.json")))
    assert j["checks"]["nph52_artifact_availability_matches_axis"]["pass"]

    # mutate one thing: drop the reserved address from the axis. The census
    # never compares it, so only the axis check can catch this.
    write_provenance(prov, [ADDR_PRESENT, ADDR_ABSENT])
    bad = str(tmp_path / "axis_bad")
    r = run(AUDIT_V2, "--census", cen, "--receipt", rec, "--artifact", art,
            "--nph52-provenance", prov, "--nph52-matrix-id", MATRIX_ID,
            "--nph52-source-dataset-id", DATASET_ID, "--out-dir", bad)
    assert r.returncode != 0
    j = json.load(open(os.path.join(bad, "AUDIT_CANDIDATE_POOL_CENSUS_V2.json")))
    chk = j["checks"]["nph52_artifact_availability_matches_axis"]
    assert chk["pass"] is False
    assert any(str(ADDR_ABSENT_RESERVED) in p for p in chk["problems"])
    # and the cross-path comparison still says everything agrees, which is
    # exactly why the axis check had to be added
    assert j["checks"]["cross_path_agreement"]["pass"] is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
