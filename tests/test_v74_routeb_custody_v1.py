"""V74 LANE 1: behavioural adversarial tests for Route-B custody.

Every test here drives a real producer into a real failure state with real bytes on
disk. None of them asserts that the source code "looks right".

The discipline this file is written to: for each check, what result would make the test
FAIL, and is that result reachable? A test that cannot fail is the specific defect this
project keeps finding -- the V69 barcode guard contained one (it looped over a dict
looking for a key bound to two values), and `test_the_removed_duplicate_check_could_not_
have_fired` below pins that fact so it cannot quietly come back.

So each adversarial test is paired with its positive control: the same harness, the same
inputs, one thing changed, and the unmutated run must PASS. If the harness were broken
the positive control would fail and the adversarial tests would be meaningless.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "v69"

# The producers import v69_custody / v69_barcode_identity by their real names after
# inserting scripts/v69 on sys.path. The tests must import the SAME module objects,
# not private copies: two copies of v69_custody give two distinct CustodyError classes,
# and `pytest.raises(CustodyError)` would then miss the real one and the test would
# report a harness artefact instead of the behaviour under test.
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import v69_custody as custody            # noqa: E402
import v69_barcode_identity as bid       # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
extractor = _load("v69_extract_t",
                  _SCRIPTS / "routeb_extract_pseudobulk_fragments_v1.py")
consensus = _load("v69_consensus_t",
                  _SCRIPTS / "routeb_call_peaks_and_consensus_v1.py")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# =============================================================================
# A synthetic Route-B universe: small, but the same shape as the real one.
#
# It reproduces the one property of GSE214979 that makes barcode identity hard --
# an aggregation suffix carrying two donors -- because the suffix guard refuses to
# run on a cohort where that distinction is absent.
# =============================================================================

ROWS = [
    # barcode, donor, subcluster
    ("AAAA-5", "D1", "Mic_0"),
    ("AAAB-5", "D2", "Mic_0"),   # suffix 5 carries D1 and D2
    ("AAAC-6", "D1", "Mic_1"),
    ("AAAD-6", "D3", "Mic_1"),
]
FAILING_QC_BARCODE = "AAAD-6"

# The per-cell fragment counts the fixture actually writes. The QC table declares these
# same numbers, so the producer's re-count from the digested bytes agrees -- which is
# what makes the disagreement test below a real mutation rather than a broken fixture.
N_FRAGMENTS = {"AAAA-5": 5, "AAAB-5": 5, "AAAC-6": 5, FAILING_QC_BARCODE: 2}


def _write_fragments(path: Path) -> None:
    lines = []
    for bc, _d, _s in ROWS:
        for i in range(N_FRAGMENTS.get(bc, 5)):
            lines.append("chr1\t%d\t%d\t%s\t1" % (1000 + i * 10, 1050 + i * 10, bc))
    lines.append("chr1\t9000\t9050\tNOT_A_COHORT_BARCODE-99\t1")
    with gzip.GzipFile(filename=str(path), mode="wb", mtime=1) as gz:
        gz.write(("\n".join(lines) + "\n").encode())


def build_universe(tmp: Path, rows=None, qc_rows=None) -> dict:
    """Materialise a complete, internally consistent set of Route-B inputs."""
    rows = ROWS if rows is None else rows
    tmp.mkdir(parents=True, exist_ok=True)

    frags = tmp / "fragments.tsv.gz"
    _write_fragments(frags)

    bc_csv = tmp / "barcodes.csv"
    pd.DataFrame(rows, columns=["barcode", "donor", "subcluster"]).to_csv(
        bc_csv, index=False)

    if qc_rows is None:
        qc_rows = [(b, d, N_FRAGMENTS.get(b, 5), b != FAILING_QC_BARCODE)
                   for b, d, _s in rows]
    qc_csv = tmp / "qc_per_barcode.csv.gz"
    pd.DataFrame(qc_rows,
                 columns=["barcode", "donor", "n_fragments",
                          "passes_min_fragments"]).to_csv(
        qc_csv, index=False, compression="gzip")

    acq = tmp / "ACQ.json"
    acq.write_text(json.dumps({
        "schema": "V69_REMOTE_OBJECT_ACQUISITION_RECEIPT_V1",
        "local_bytes": frags.stat().st_size,
        "sha256": _sha(frags),
        "status": "PASS__BYTE_COMPLETE_AND_DIGESTED"}, indent=2))

    coh = tmp / "COHORT.json"
    coh.write_text(json.dumps({
        "schema": "V69_GSE214979_COHORT_FREEZE_V1",
        "status": "PASS__COHORT_FROZEN_PATHOLOGY_BLIND",
        "populations": {"TESTPOP": {
            "population_id": "TESTPOP",
            "n_cells": len({r[0] for r in rows}),
            "barcode_file": str(bc_csv),
            "barcode_file_sha256": _sha(bc_csv)}}}, indent=2))

    qcr = tmp / "QC.json"
    qcr.write_text(json.dumps({
        "schema": "V69_ROUTEB_FRAGMENT_QC_V1",
        "status": "PASS__ROUTEB_FRAGMENT_QC_COMPLETE",
        "PARTIAL_SCAN": False,
        "fragments_sha256": _sha(frags),
        "per_barcode_table": {"path": str(qc_csv), "sha256": _sha(qc_csv)}}, indent=2))

    return {"fragments": frags, "acq": acq, "qc_receipt": qcr, "qc_table": qc_csv,
            "cohort": coh, "barcodes": bc_csv, "out": tmp / "pseudobulk"}


def go(u: dict, **kw) -> dict:
    """Run the extractor the way the CLI does, returning the receipt it would write."""
    try:
        return extractor.run(u["fragments"], u["acq"], u["qc_receipt"], u["cohort"],
                             "TESTPOP", u["out"], kw.pop("max_records", 0))
    except extractor.FailClosed as e:
        return {"status": e.status, **e.detail}
    except custody.CustodyError as e:
        return {"status": e.status, **e.detail}


def _rebind_cohort(u: dict) -> None:
    """Re-stamp the cohort receipt's digest after deliberately editing the CSV.

    Without this, mutating the barcode table would trip the DIGEST check and the test
    would silently stop exercising the duplicate-collapse defect it is aimed at. Each
    adversarial test must fail for the reason it names.
    """
    coh = json.loads(u["cohort"].read_text())
    coh["populations"]["TESTPOP"]["barcode_file_sha256"] = _sha(u["barcodes"])
    coh["populations"]["TESTPOP"]["n_cells"] = int(
        pd.read_csv(u["barcodes"])["barcode"].nunique())
    u["cohort"].write_text(json.dumps(coh, indent=2))


# =============================================================================
# POSITIVE CONTROL -- without this the adversarial tests prove nothing.
# =============================================================================

def test_positive_control_a_clean_universe_passes_and_verifies_the_bytes(tmp_path):
    u = build_universe(tmp_path)
    r = go(u)
    assert r["status"] == "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED", r
    assert r["fragment_identity"]["verified"] is True
    assert r["fragment_identity"]["observed_sha256"] == _sha(u["fragments"])
    assert (r["fragment_identity"]["digest_source"]
            == "COMPUTED_FROM_THE_COMPRESSED_BYTES_READ_BY_THIS_RUN")
    # 3 of 4 cells pass QC; the failing one is excluded and SAID to be excluded.
    assert r["cell_qc"]["n_cells_used"] == 3
    assert r["cell_qc"]["n_cells_excluded_by_qc"] == 1
    assert r["cell_qc"]["n_cells_with_no_qc_verdict"] == 0
    assert r["records_written_to_a_pseudobulk"] == 15
    assert r["records_discarded_out_of_cohort"] == 1
    assert r["records_discarded_because_the_cell_failed_qc"] == 2
    assert r["records_discarded_out_of_cohort_or_failing_qc"] == 3
    # C5: the QC table re-derived from the bytes this run digested
    rc = r["qc_table_recount"]
    assert rc["performed"] is True
    assert rc["n_cells_compared"] == 4 and rc["n_cells_disagreeing"] == 0
    assert rc["total_cohort_fragments_in_verified_pass"] == 17
    # every input bound by content, not by path
    for key in ("producer", "barcode_identity_module", "custody_module",
                "fragments_acquisition_receipt", "routeb_qc_receipt",
                "cohort_freeze_receipt", "routeb_qc_per_barcode_table",
                "cohort_barcode_authority"):
        rec = r["bound_inputs"][key]
        assert len(rec["sha256"]) == 64, key
        assert rec["bytes"] > 0, key
    assert r["bound_inputs"]["cohort_barcode_authority"][
        "digest_checked_against_authority"] is True
    assert not (u["out"].parent / (u["out"].name + "__STAGING")).exists()


# =============================================================================
# REPAIR 1 -- fragment byte identity. SIZE IS NOT IDENTITY.
# =============================================================================

def test_same_size_different_bytes_is_refused(tmp_path):
    """The whole point of repair 1.

    The gzip MTIME field is mutated. The file keeps its exact byte LENGTH, still
    decompresses, and still yields byte-identical fragment records -- so a size check
    passes, decompression succeeds, and every downstream count would look perfect. Only
    the digest can tell that these are not the authenticated bytes.
    """
    u = build_universe(tmp_path)
    b = bytearray(u["fragments"].read_bytes())
    before_len = len(b)
    b[4] ^= 0xFF                      # gzip header MTIME: not covered by the CRC
    u["fragments"].write_bytes(bytes(b))
    assert u["fragments"].stat().st_size == before_len, "the size must be unchanged"
    expected_records = sum(N_FRAGMENTS.values()) + 1   # + out-of-cohort record
    with gzip.open(u["fragments"], "rb") as gz:        # still perfectly readable
        assert gz.read().count(b"\n") == expected_records

    r = go(u)
    assert r["status"] == "FAIL__FRAGMENT_BYTES_DO_NOT_MATCH_AUTHENTICATED_DIGEST", r
    assert r["observed_sha256"] != r["expected_sha256"]
    assert not u["out"].exists(), "no output directory may survive a custody failure"
    assert Path(r["quarantined_outputs"]).name.endswith("__QUARANTINE_FAILED_CUSTODY")


def test_truncated_file_fails_before_any_work(tmp_path):
    u = build_universe(tmp_path)
    b = u["fragments"].read_bytes()
    u["fragments"].write_bytes(b[:-20])
    r = go(u)
    assert r["status"] == "FAIL__FRAGMENT_FILE_SIZE_CHANGED_SINCE_ACQUISITION", r
    assert not u["out"].exists()


def test_corrupt_payload_is_a_named_state_not_a_traceback(tmp_path):
    u = build_universe(tmp_path)
    b = bytearray(u["fragments"].read_bytes())
    b[len(b) // 2] ^= 0xFF            # inside the deflate stream
    u["fragments"].write_bytes(bytes(b))
    r = go(u)
    assert r["status"] in ("FAIL__FRAGMENT_STREAM_DECOMPRESSION_FAILED",
                           "FAIL__FRAGMENT_BYTES_DO_NOT_MATCH_AUTHENTICATED_DIGEST"), r
    assert not u["out"].exists()


def test_an_acquisition_receipt_without_a_digest_is_refused(tmp_path):
    u = build_universe(tmp_path)
    acq = json.loads(u["acq"].read_text())
    acq.pop("sha256")
    u["acq"].write_text(json.dumps(acq))
    r = go(u)
    assert r["status"] == "FAIL__ACQUISITION_RECEIPT_CARRIES_NO_FRAGMENT_DIGEST", r


def test_qc_scan_bound_to_a_different_fragment_file_is_refused(tmp_path):
    u = build_universe(tmp_path)
    qc = json.loads(u["qc_receipt"].read_text())
    qc["fragments_sha256"] = "0" * 64
    u["qc_receipt"].write_text(json.dumps(qc))
    r = go(u)
    assert r["status"] == "FAIL__QC_SCAN_IS_BOUND_TO_A_DIFFERENT_FRAGMENT_FILE", r


def test_a_partial_scan_records_unverified_and_never_a_copied_digest(tmp_path):
    """A smoke scan must not inherit a digest it did not compute."""
    u = build_universe(tmp_path)
    r = go(u, max_records=3)
    assert r["status"] == "PASS__PARTIAL_SMOKE_SCAN", r
    assert r["fragments_sha256"] == custody.UNVERIFIED_PARTIAL
    assert r["fragment_identity"]["verified"] is False
    assert r["fragments_sha256"] != _sha(u["fragments"]), (
        "a partial scan must never present the authenticated digest as its own")
    # A partial scan cannot bind the QC table, and says so rather than reporting zero
    # disagreements -- "not measured" must never be encoded as a clean result.
    assert r["qc_table_recount"]["performed"] is False
    assert r["qc_table_recount"]["n_cells_disagreeing"] == custody.UNMEASURED
    assert r["cell_qc"]["qc_counts_rederived_from_the_verified_pass"] is False


def test_hashing_reader_digests_the_whole_file_and_knows_when_it_did_not(tmp_path):
    p = tmp_path / "blob.bin"
    p.write_bytes(b"x" * 100000 + b"tail")
    rd = custody.HashingReader(p)
    rd.read(10)
    assert rd.complete is False, "a partial read must never report completeness"
    rd.drain()
    assert rd.complete is True
    assert rd.hexdigest() == _sha(p)
    rd.close()


def test_bind_file_refuses_a_changed_file(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("one")
    good = custody.bind_file(p, label="a", role="T", expected_sha256=_sha(p))
    assert good["digest_checked_against_authority"] is True
    p.write_text("two")
    with pytest.raises(custody.CustodyError) as e:
        custody.bind_file(p, label="a", role="T", expected_sha256=good["sha256"])
    assert e.value.status == "FAIL__BOUND_FILE_DIGEST_MISMATCH"


# =============================================================================
# REPAIR 2 -- barcode authority audited BEFORE the dictionary collapse.
# =============================================================================

def test_the_removed_duplicate_check_could_not_have_fired():
    """Pins the V69 defect so it cannot return.

    The old guard looked for a barcode bound to two donors by iterating a dict. This
    demonstrates with real values that the conflict is already gone by then -- the dict
    silently keeps the LAST row -- and that the pre-collapse audit catches what the
    post-collapse check structurally could not.
    """
    conflicting = [("AAAA-5", "D1", "Mic_0"), ("AAAA-5", "D2", "Mic_0"),
                   ("AAAB-5", "D2", "Mic_0")]
    collapsed = dict((b, d) for b, d, _s in conflicting)
    assert collapsed["AAAA-5"] == "D2", "dict(zip(...)) keeps the last row"
    assert len(collapsed) == 2, "the conflicting row vanished without a trace"

    with pytest.raises(bid.BarcodeAuthorityError) as e:
        bid.audit_barcode_authority_rows(conflicting)
    assert e.value.status == "FAIL__BARCODE_MAPS_TO_MULTIPLE_DONORS"
    assert e.value.detail["examples"]["AAAA-5"] == ["D1", "D2"]


def test_conflicting_donor_mapping_fails_the_real_producer_closed(tmp_path):
    u = build_universe(tmp_path)
    df = pd.read_csv(u["barcodes"])
    df.loc[len(df)] = ["AAAA-5", "D9", "Mic_0"]     # same barcode, different donor
    df.to_csv(u["barcodes"], index=False)
    _rebind_cohort(u)
    r = go(u)
    assert r["status"] == "FAIL__BARCODE_MAPS_TO_MULTIPLE_DONORS", r
    assert not u["out"].exists()


def test_conflicting_subcluster_mapping_fails_the_real_producer_closed(tmp_path):
    u = build_universe(tmp_path)
    df = pd.read_csv(u["barcodes"])
    df.loc[len(df)] = ["AAAA-5", "D1", "Mic_9"]     # same barcode, 2 subclusters
    df.to_csv(u["barcodes"], index=False)
    _rebind_cohort(u)
    r = go(u)
    assert r["status"] == "FAIL__BARCODE_MAPS_TO_MULTIPLE_SUBCLUSTERS", r


def test_benign_exact_duplicate_rows_are_allowed_and_counted(tmp_path):
    """The declared policy, exercised: identical rows carry no contradiction."""
    u = build_universe(tmp_path)
    df = pd.read_csv(u["barcodes"])
    df.loc[len(df)] = list(df.iloc[0])              # byte-identical repeat
    df.to_csv(u["barcodes"], index=False)
    _rebind_cohort(u)
    r = go(u)
    assert r["status"] == "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED", r
    audit = r["barcode_authority_audit"]
    assert audit["n_rows_in"] == 5
    assert audit["n_distinct_barcodes"] == 4
    assert audit["n_exact_duplicate_rows_collapsed"] == 1
    assert r["donor_identity_guard"]["pre_collapse_authority_audit"]["performed"] is True


def test_a_blank_identifier_is_not_coerced_into_a_value(tmp_path):
    u = build_universe(tmp_path)
    df = pd.read_csv(u["barcodes"])
    df.loc[len(df)] = ["AAAE-5", None, "Mic_0"]
    df.to_csv(u["barcodes"], index=False)
    _rebind_cohort(u)
    r = go(u)
    assert r["status"] == "FAIL__BARCODE_AUTHORITY_HAS_NULL_OR_BLANK_IDENTIFIERS", r


def test_an_empty_authority_fails_closed():
    with pytest.raises(bid.BarcodeAuthorityError) as e:
        bid.audit_barcode_authority_rows([])
    assert e.value.status == "FAIL__BARCODE_AUTHORITY_IS_EMPTY"


def test_a_missing_column_fails_closed():
    with pytest.raises(bid.BarcodeAuthorityError) as e:
        bid.audit_barcode_authority_frame(pd.DataFrame({"barcode": ["a-1"]}))
    assert e.value.status == "FAIL__BARCODE_AUTHORITY_MISSING_COLUMN"


def test_qc_table_with_two_verdicts_for_one_barcode_fails_closed(tmp_path):
    u = build_universe(tmp_path)
    qc = pd.read_csv(u["qc_table"])
    qc.loc[len(qc)] = ["AAAA-5", "D1", 0, False]    # second, contradictory verdict
    qc.to_csv(u["qc_table"], index=False, compression="gzip")
    rec = json.loads(u["qc_receipt"].read_text())
    rec["per_barcode_table"]["sha256"] = _sha(u["qc_table"])
    u["qc_receipt"].write_text(json.dumps(rec))
    r = go(u)
    assert r["status"] == "FAIL__QC_TABLE_BARCODE_DUPLICATED_WITH_CONFLICTING_VALUES", r


def test_a_cohort_cell_with_no_qc_row_is_not_treated_as_a_qc_failure(tmp_path):
    """NOT_MEASURED must not be silently encoded as a measured exclusion."""
    u = build_universe(tmp_path)
    qc = pd.read_csv(u["qc_table"])
    qc = qc[qc["barcode"] != "AAAC-6"]
    qc.to_csv(u["qc_table"], index=False, compression="gzip")
    rec = json.loads(u["qc_receipt"].read_text())
    rec["per_barcode_table"]["sha256"] = _sha(u["qc_table"])
    u["qc_receipt"].write_text(json.dumps(rec))
    r = go(u)
    assert r["status"] == "FAIL__COHORT_BARCODE_HAS_NO_QC_VERDICT", r
    assert r["examples"] == ["AAAC-6"]


def test_qc_counts_that_disagree_with_the_verified_pass_fail_closed(tmp_path):
    """C5: the QC table is re-derived from the digested bytes, not merely trusted.

    V69_ROUTEB_FRAGMENT_QC_V1 copied its fragments_sha256 from the acquisition receipt,
    so its per-cell verdicts rest on a scan of bytes nothing digested. Requiring the two
    copied fields to be equal proves only that two strings match. This re-counts.
    """
    u = build_universe(tmp_path)
    qc = pd.read_csv(u["qc_table"])
    qc.loc[qc["barcode"] == "AAAA-5", "n_fragments"] = 999     # not what the file holds
    qc.to_csv(u["qc_table"], index=False, compression="gzip")
    rec = json.loads(u["qc_receipt"].read_text())
    rec["per_barcode_table"]["sha256"] = _sha(u["qc_table"])   # digest check must pass
    u["qc_receipt"].write_text(json.dumps(rec))

    r = go(u)
    assert r["status"] == (
        "FAIL__QC_TABLE_FRAGMENT_COUNTS_DISAGREE_WITH_THE_VERIFIED_PASS"), r
    assert r["n_cells_disagreeing"] == 1
    assert r["examples"]["AAAA-5"] == {"qc_table": 999, "verified_pass": 5}
    assert not u["out"].exists(), "nothing may be promoted when the QC table is wrong"


# =============================================================================
# REPAIR 3 -- content binding, not path binding.
# =============================================================================

def test_editing_the_barcode_authority_without_restamping_it_refuses_the_run(tmp_path):
    """Paths are mutable. The cohort freeze names a path AND a digest; only the digest
    is evidence."""
    u = build_universe(tmp_path)
    df = pd.read_csv(u["barcodes"])
    df.loc[0, "donor"] = "D_SWAPPED"
    df.to_csv(u["barcodes"], index=False)           # deliberately NOT re-stamped
    r = go(u)
    assert r["status"] == "FAIL__BOUND_FILE_DIGEST_MISMATCH", r
    assert r["label"] == "barcode_authority_csv"


def test_editing_the_qc_table_without_restamping_it_refuses_the_run(tmp_path):
    u = build_universe(tmp_path)
    qc = pd.read_csv(u["qc_table"])
    qc.loc[qc["barcode"] == FAILING_QC_BARCODE, "passes_min_fragments"] = True
    qc.to_csv(u["qc_table"], index=False, compression="gzip")
    r = go(u)
    assert r["status"] == "FAIL__BOUND_FILE_DIGEST_MISMATCH", r
    assert r["label"] == "per_barcode_qc_table"


def test_pointing_the_cohort_receipt_at_a_different_file_refuses_the_run(tmp_path):
    """Same digest in the authority, different path on disk: the swap is caught."""
    u = build_universe(tmp_path)
    other = tmp_path / "other_barcodes.csv"
    pd.DataFrame([("ZZZZ-5", "DX", "Mic_0")],
                 columns=["barcode", "donor", "subcluster"]).to_csv(other, index=False)
    coh = json.loads(u["cohort"].read_text())
    coh["populations"]["TESTPOP"]["barcode_file"] = str(other)
    u["cohort"].write_text(json.dumps(coh, indent=2))
    r = go(u)
    assert r["status"] == "FAIL__BOUND_FILE_DIGEST_MISMATCH", r


def test_consensus_refuses_a_pseudobulk_receipt_from_before_the_custody_contract(
        tmp_path):
    rec = tmp_path / "pb.json"
    rec.write_text(json.dumps({
        "status": "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED", "PARTIAL_SCAN": False,
        "pseudobulks": {}}))
    with pytest.raises(consensus.FailClosed) as e:
        consensus.run(rec, tmp_path / "cs.txt", tmp_path / "o", "macs2", 1, None)
    assert e.value.status == "FAIL__PSEUDOBULK_RECEIPT_PREDATES_THE_CUSTODY_CONTRACT"


def test_consensus_refuses_when_the_upstream_never_verified_the_fragment_bytes(
        tmp_path):
    rec = tmp_path / "pb.json"
    rec.write_text(json.dumps({
        "status": "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED", "PARTIAL_SCAN": False,
        "custody_contract": "V74_ROUTEB_CUSTODY_V1",
        "fragment_identity": {"verified": False,
                              "observed_sha256": custody.UNVERIFIED_PARTIAL,
                              "expected_sha256": "a" * 64},
        "bound_inputs": {}, "pseudobulks": {}}))
    with pytest.raises(consensus.FailClosed) as e:
        consensus.run(rec, tmp_path / "cs.txt", tmp_path / "o", "macs2", 1, None)
    assert e.value.status == "FAIL__UPSTREAM_FRAGMENT_BYTES_WERE_NEVER_VERIFIED"


def test_consensus_refuses_when_a_bound_input_changed_on_disk(tmp_path):
    victim = tmp_path / "authority.csv"
    victim.write_text("barcode,donor\na-1,D1\n")
    rec = tmp_path / "pb.json"
    rec.write_text(json.dumps({
        "status": "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED", "PARTIAL_SCAN": False,
        "custody_contract": "V74_ROUTEB_CUSTODY_V1",
        "fragment_identity": {"verified": True, "observed_sha256": "b" * 64,
                              "expected_sha256": "b" * 64},
        "bound_inputs": {"cohort_barcode_authority": {
            "label": "barcode_authority_csv", "path": str(victim),
            "sha256": _sha(victim), "bytes": victim.stat().st_size}},
        "pseudobulks": {}}))
    # unmutated: passes the whole custody chain and stops for an unrelated reason
    cs = tmp_path / "cs.txt"
    cs.write_text("chr1\t1000\n")
    with pytest.raises(consensus.FailClosed) as clean:
        consensus.run(rec, cs, tmp_path / "o", "macs2", 1, None)
    assert clean.value.status == "FAIL__NO_NONEMPTY_PSEUDOBULKS"

    victim.write_text("barcode,donor\na-1,D2\n")
    with pytest.raises(custody.CustodyError) as e:
        consensus.run(rec, cs, tmp_path / "o", "macs2", 1, None)
    assert e.value.status == "FAIL__BOUND_FILE_DIGEST_MISMATCH"


# =============================================================================
# REPAIR 4 -- an empty consensus is a named state, computed before any width.
# =============================================================================

def _consensus_frame(n):
    return pd.DataFrame({"Chromosome": ["chr1"] * n,
                         "Start": list(range(0, 100 * n, 100))[:n],
                         "End": list(range(500, 100 * n + 500, 100))[:n]})


def test_zero_region_consensus_emits_the_named_state(tmp_path):
    empty = _consensus_frame(0)
    with pytest.raises(consensus.FailClosed) as e:
        consensus.assert_consensus_nonempty(empty, n_pseudobulks_used=4,
                                            n_pseudobulks_skipped_empty=1)
    assert e.value.status == "FAIL__CONSENSUS_PEAK_SET_IS_EMPTY"
    assert e.value.status == consensus.CONSENSUS_EMPTY_STATUS
    assert e.value.detail["n_consensus_regions"] == 0
    assert e.value.detail["n_pseudobulks_used"] == 4
    assert e.value.detail["n_pseudobulks_skipped_empty"] == 1


def test_a_nonempty_consensus_passes_the_same_check():
    """Positive control: the guard must not be a check that always fires."""
    assert consensus.assert_consensus_nonempty(_consensus_frame(3)) is None
    assert consensus.assert_consensus_nonempty(_consensus_frame(1)) is None


def test_the_width_statistic_really_does_blow_up_on_an_empty_frame():
    """Why repair 4 exists.

    This is the exact expression the V69 receipt builder reached with zero regions. It
    raises ValueError, which is NOT FailClosed, so main() did not catch it and NO
    RECEIPT WAS WRITTEN AT ALL -- the step vanished without leaving a record that it had
    been attempted. If this assertion ever stops holding, the named guard is no longer
    protecting anything and this test should be revisited rather than deleted.
    """
    empty = _consensus_frame(0)
    widths = empty["End"] - empty["Start"]
    with pytest.raises(ValueError):
        int(widths.min())


def test_none_is_treated_as_empty_not_as_a_crash():
    with pytest.raises(consensus.FailClosed) as e:
        consensus.assert_consensus_nonempty(None)
    assert e.value.status == "FAIL__CONSENSUS_PEAK_SET_IS_EMPTY"


# =============================================================================
# Staged outputs: a custody failure must not leave usable files behind.
# =============================================================================

def test_staged_outputs_are_quarantined_not_promoted_on_failure(tmp_path):
    s = custody.StagedOutputDir(tmp_path / "final")
    d = s.open()
    (d / "a.bed").write_text("chr1\t1\t2\n")
    where = s.quarantine_failed()
    assert not (tmp_path / "final").exists()
    assert Path(where).is_dir() and (Path(where) / "a.bed").exists()


def test_staged_outputs_are_promoted_on_success(tmp_path):
    s = custody.StagedOutputDir(tmp_path / "final")
    d = s.open()
    (d / "a.bed").write_text("chr1\t1\t2\n")
    final = s.promote()
    assert final.is_dir() and (final / "a.bed").exists()
    assert not s.staging.exists()


def test_the_suffix_guard_still_refuses_a_single_donor_per_suffix_cohort(tmp_path):
    """The V69 guard must keep working after the V74 signature change."""
    rows = [("AAAA-5", "D1", "Mic_0"), ("AAAB-5", "D1", "Mic_0"),
            ("AAAC-6", "D2", "Mic_1"), ("AAAD-6", "D2", "Mic_1")]
    u = build_universe(tmp_path, rows=rows)
    r = go(u)
    assert r["status"] == "FAIL__DONOR_IDENTITY_GUARD", r
    assert "INDISTINGUISHABLE_FROM_SUFFIX_DERIVED" in r["reason"]


def test_receipt_status_written_to_disk_matches_the_exit_code(tmp_path):
    """The verdict must exist in the bytes on disk, not only in stdout."""
    u = build_universe(tmp_path)
    receipt = tmp_path / "receipt.json"
    rc = extractor.main([
        "--fragments", str(u["fragments"]), "--fragments-receipt", str(u["acq"]),
        "--qc-receipt", str(u["qc_receipt"]), "--cohort-receipt", str(u["cohort"]),
        "--population", "TESTPOP", "--out-dir", str(u["out"]),
        "--receipt", str(receipt)])
    on_disk = json.loads(receipt.read_text())
    assert rc == 0 and on_disk["status"] == "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED"

    shutil.rmtree(u["out"])
    b = bytearray(u["fragments"].read_bytes())
    b[4] ^= 0xFF
    u["fragments"].write_bytes(bytes(b))
    rc2 = extractor.main([
        "--fragments", str(u["fragments"]), "--fragments-receipt", str(u["acq"]),
        "--qc-receipt", str(u["qc_receipt"]), "--cohort-receipt", str(u["cohort"]),
        "--population", "TESTPOP", "--out-dir", str(u["out"]),
        "--receipt", str(receipt)])
    on_disk2 = json.loads(receipt.read_text())
    assert rc2 == 1
    assert on_disk2["status"] == "FAIL__FRAGMENT_BYTES_DO_NOT_MATCH_AUTHENTICATED_DIGEST"


# =============================================================================
# Recurrence denominator: a donor that called no peak contributes a zero, it does
# not leave the denominator.
# =============================================================================

_PB_META = {
    "D1__Mic_0": {"donor": "D1", "subcluster": "Mic_0"},
    "D1__Mic_1": {"donor": "D1", "subcluster": "Mic_1"},
    "D2__Mic_0": {"donor": "D2", "subcluster": "Mic_0"},
    "D3__Mic_0": {"donor": "D3", "subcluster": "Mic_0"},
}


def test_a_donor_that_called_no_peak_stays_in_the_denominator():
    submitted = list(_PB_META)
    with_peaks = ["D1__Mic_0", "D1__Mic_1", "D2__Mic_0"]    # D3 called nothing
    den = consensus.recurrence_denominator(_PB_META, submitted, with_peaks)
    assert den["denominator"] == 3, "D3 submitted fragments and must not vanish"
    assert den["donors_submitted"] == ["D1", "D2", "D3"]
    assert den["donors_with_peaks"] == ["D1", "D2"]
    assert den["donors_submitted_without_peaks"] == ["D3"]
    assert den["pseudobulks_submitted_without_peaks"] == ["D3__Mic_0"]
    # The defect this prevents, stated numerically: a region carried by D1 and D2 is
    # 2/3 of the donors that could have shown it, not 2/2.
    assert 2 / den["denominator"] != 1.0


def test_the_denominator_is_unchanged_when_every_donor_calls_a_peak():
    """Positive control: the repair must not move the number in the normal case."""
    submitted = list(_PB_META)
    den = consensus.recurrence_denominator(_PB_META, submitted, submitted)
    assert den["denominator"] == 3
    assert den["donors_submitted_without_peaks"] == []
    assert den["pseudobulks_submitted_without_peaks"] == []


# =============================================================================
# Container path remapping: the receipt keeps the HOST path; the container reads
# the same bytes elsewhere and must still verify them there.
# =============================================================================

def test_remap_translates_only_the_host_prefix():
    r = custody.remap(r"D:\out\v69\raw\f.gz", r"D:\out", "/mnt/host")
    assert str(r).replace("\\", "/") == "/mnt/host/v69/raw/f.gz"
    # case-insensitive, because the host prefix is a Windows path
    r2 = custody.remap(r"d:/OUT/v69/raw/f.gz", r"D:\out", "/mnt/host")
    assert str(r2).replace("\\", "/") == "/mnt/host/v69/raw/f.gz"
    # a path outside the prefix is returned unchanged, never guessed at
    assert str(custody.remap("/already/container/f.gz", r"D:\out", "/mnt/host")) \
        .replace("\\", "/") == "/already/container/f.gz"
    # no prefix configured means no translation at all
    assert str(custody.remap(r"D:\out\f.gz", "", "/mnt/host")) == r"D:\out\f.gz"


def test_consensus_verifies_digests_at_the_remapped_location(tmp_path):
    """A remapped run must still catch a changed file -- and must still pass when the
    file is intact. Without the positive control, a remap that pointed at nothing would
    look identical to a successful verification."""
    host_root = tmp_path / "HOSTROOT"
    host_root.mkdir()
    victim = host_root / "authority.csv"
    victim.write_text("barcode,donor\na-1,D1\n")
    fake_host = r"D:\pretend\root"

    def receipt_for(sha):
        rec = tmp_path / "pb.json"
        rec.write_text(json.dumps({
            "status": "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED", "PARTIAL_SCAN": False,
            "custody_contract": "V74_ROUTEB_CUSTODY_V1",
            "fragment_identity": {"verified": True, "observed_sha256": "b" * 64,
                                  "expected_sha256": "b" * 64},
            "bound_inputs": {"cohort_barcode_authority": {
                "label": "barcode_authority_csv",
                "path": fake_host + r"\authority.csv",
                "sha256": sha, "bytes": victim.stat().st_size}},
            "pseudobulks": {}}))
        return rec

    cs = tmp_path / "cs.txt"
    cs.write_text("chr1\t1000\n")
    kw = dict(host_prefix=fake_host, container_prefix=str(host_root))
    # intact: the whole custody chain is satisfied THROUGH the remap, and the run
    # then stops for the unrelated reason that the fixture supplies no pseudobulks.
    with pytest.raises(consensus.FailClosed) as clean:
        consensus.run(receipt_for(_sha(victim)), cs, tmp_path / "o",
                      "macs2", 1, None, **kw)
    assert clean.value.status == "FAIL__NO_NONEMPTY_PSEUDOBULKS"

    # changed at the remapped location: caught there, not missed because of the remap
    victim.write_text("barcode,donor\na-1,D2\n")
    with pytest.raises(custody.CustodyError) as e:
        consensus.run(receipt_for("0" * 64), cs, tmp_path / "o",
                      "macs2", 1, None, **kw)
    assert e.value.status == "FAIL__BOUND_FILE_DIGEST_MISMATCH"


def test_hashing_reader_handles_a_multi_member_gzip(tmp_path):
    """A 63.6 GB deposit may be a concatenation of gzip members.

    HashingReader declares itself unseekable on purpose -- a backwards seek would make
    the digest double-count or skip bytes and stop being a whole-file digest. gzip's
    member transition uses prepend rather than seek, but that is a claim about CPython
    internals, so it is checked against real multi-member bytes rather than assumed.
    """
    a, b = tmp_path / "a.gz", tmp_path / "b.gz"
    with gzip.GzipFile(filename=str(a), mode="wb", mtime=1) as gz:
        gz.write(b"first member line\n" * 500)
    with gzip.GzipFile(filename=str(b), mode="wb", mtime=1) as gz:
        gz.write(b"second member line\n" * 500)
    both = tmp_path / "both.gz"
    both.write_bytes(a.read_bytes() + b.read_bytes())

    rd = custody.HashingReader(both)
    with gzip.GzipFile(fileobj=rd, mode="rb") as gz:
        payload = gz.read()
    rd.drain()
    assert payload.count(b"first member line") == 500
    assert payload.count(b"second member line") == 500, "the second member was reached"
    assert rd.complete is True
    assert rd.hexdigest() == _sha(both), "the digest must cover both members"
    rd.close()


# =============================================================================
# The byte-level loop must produce exactly what the str-level loop produced.
# This is an infrastructure change; the method must not move with it.
# =============================================================================

def test_byte_level_parsing_reproduces_the_str_level_result_exactly(tmp_path):
    """The V69 loop decoded each line to str. This one works in bytes for speed.

    The expected BED content is derived HERE from the fixture using the original
    str-based reading, independently of the producer, and compared byte for byte with
    what the producer wrote. If the two representations ever disagreed -- on a tab, a
    line ending, a field boundary -- this fails.
    """
    u = build_universe(tmp_path)
    r = go(u)
    assert r["status"] == "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED", r

    # Independent str-based reconstruction of what each pseudobulk should contain.
    donor_of = {b: d for b, d, _s in ROWS}
    sub_of = {b: s for b, _d, s in ROWS}
    expected = {}
    with gzip.open(u["fragments"], "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 4 or f[3] not in donor_of or f[3] == FAILING_QC_BARCODE:
                continue
            key = "%s__%s" % (donor_of[f[3]], sub_of[f[3]])
            expected.setdefault(key, []).append("%s\t%s\t%s\n" % (f[0], f[1], f[2]))

    assert expected, "the reconstruction must not be vacuously empty"
    for key, rows in expected.items():
        on_disk = (u["out"] / ("PSEUDOBULK_%s.bed" % key)).read_bytes()
        assert on_disk == "".join(rows).encode(), key
    # and every pseudobulk the producer reported is accounted for
    nonempty = {k for k, v in r["pseudobulks"].items() if v["n_fragments"] > 0}
    assert nonempty == set(expected)


def test_a_non_ascii_record_in_a_written_cell_fails_closed(tmp_path):
    """Working in bytes drops the incidental UTF-8 check that decoding performed.

    It is reinstated where it can matter -- the records actually written. This proves
    the replacement check fires, so the change traded no validation away silently.
    """
    u = build_universe(tmp_path)
    good = gzip.open(u["fragments"], "rb").read()
    bad = good.replace(b"chr1\t1000", b"chr\xff\t1000", 1)
    assert bad != good, "the fixture mutation must actually change the bytes"
    with gzip.GzipFile(filename=str(u["fragments"]), mode="wb", mtime=1) as gz:
        gz.write(bad)
    acq = json.loads(u["acq"].read_text())
    acq["sha256"] = _sha(u["fragments"])
    acq["local_bytes"] = u["fragments"].stat().st_size
    u["acq"].write_text(json.dumps(acq))
    qc = json.loads(u["qc_receipt"].read_text())
    qc["fragments_sha256"] = acq["sha256"]
    u["qc_receipt"].write_text(json.dumps(qc))

    r = go(u)
    assert r["status"] == "FAIL__NON_ASCII_FRAGMENT_RECORD_IN_A_WRITTEN_CELL", r


def test_a_four_field_fragment_record_is_parsed_not_skipped(tmp_path):
    """A record with no count column puts the newline on the BARCODE field.

    The fixture above writes five-column records, so the four-column branch was
    unreachable and a defect there could not be caught -- a stray `continue` in exactly
    that branch passed the whole suite. This makes the branch reachable.
    """
    u = build_universe(tmp_path)
    body = "\n".join("chr2\t%d\t%d\t%s" % (500 + i, 560 + i, bc)
                     for i, (bc, _d, _s) in enumerate(ROWS)
                     if bc != FAILING_QC_BARCODE) + "\n"
    with gzip.GzipFile(filename=str(u["fragments"]), mode="wb", mtime=1) as gz:
        gz.write(body.encode())
    acq = json.loads(u["acq"].read_text())
    acq["sha256"] = _sha(u["fragments"])
    acq["local_bytes"] = u["fragments"].stat().st_size
    u["acq"].write_text(json.dumps(acq))
    qc = pd.read_csv(u["qc_table"])
    qc["n_fragments"] = qc["barcode"].map(
        lambda b: 0 if b == FAILING_QC_BARCODE else 1)
    qc.to_csv(u["qc_table"], index=False, compression="gzip")
    rec = json.loads(u["qc_receipt"].read_text())
    rec["fragments_sha256"] = acq["sha256"]
    rec["per_barcode_table"]["sha256"] = _sha(u["qc_table"])
    u["qc_receipt"].write_text(json.dumps(rec))

    r = go(u)
    assert r["status"] == "PASS__PSEUDOBULK_FRAGMENTS_EXTRACTED", r
    assert r["records_scanned"] == 3
    assert r["records_written_to_a_pseudobulk"] == 3, (
        "a four-field record must be routed, not skipped")
    assert r["records_discarded_out_of_cohort"] == 0
    written = b"".join(sorted(
        (u["out"] / ("PSEUDOBULK_%s.bed" % k)).read_bytes()
        for k in r["pseudobulks"]))
    assert written.count(b"\n") == 3
    assert b"chr2\t500\t560\n" in written, "the trailing newline must not leak into End"
