"""G7 successor: historical-row binding and the accepted-G6 predecessor bridge (external code audit, 2026-10-12).

1. The authenticated Sample-A freeze has no physical global_row. G7, like the repaired G6, must assign global_row
   from the original freeze-file row position BEFORE filtering or sorting. At ff4a21f9 G7's own select_sample_a()
   never did, and the one authorized G7 run stopped before its marker with AttributeError 'global_row'
   (evidence 9ab54211).
2. A repaired G7 has a new code identity. The accepted G6 execution stays bound to ff4a21f9. Successor G7 therefore
   accepts exactly that one externally accepted G6 execution through pinned predecessor constants. Its own execution
   authority stays separate: an owner decision and runtime authorization bound to the successor's exact commit and
   code hashes. The old ff4a21f9 authorization cannot authorize successor code.
No biological replay, target selection, TD60 or training authority is introduced.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from types import SimpleNamespace
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_g6g7_synthetic_world as W  # noqa: E402

FF4A = "ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0"
FIX = Path(__file__).resolve().parent / "fixtures" / "td_g7_successor"
REAL_PREDECESSOR = {
    "implementation_commit_sha": FF4A,
    "external_acceptance_sha256": "89932183a2c7b56d1e3ae42264ea3f3b3ae9001d865cfa93604b46f0db2129fb",
    "external_acceptance_disposition": "ACCEPT_G6_PASS__VALUE_SUBSTRATE_AND_SOURCE_CUSTODY_CONFIRMED__NO_BIOLOGICAL_TARGET_AUTHORITY",
    "artifact_sha256": {
        "G6_EXECUTION_START.json": "49bdff31a1a055b1bbf1ff539a49a93413c83bf0ab8838494485bc56492bd4f1",
        "G6_RECEIPT.json": "2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b",
        "MANIFEST.json": "4fbc14ceda829cca7446e67b9ad25d428608c5aaa5e87d08ae07c412279427bf",
        "TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz": "fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9",
        "TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz": "bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74",
    },
    "authority_trace": {
        "authorization_schema": "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2",
        "authorization_sha256": "28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7",
        "authorization_token": "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY",
        "common_entrypoint": "scripts/v5/td_relational_value_read_v2_common.py",
        "common_script_sha256": "23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea",
        "g6_entrypoint": "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py",
        "g6_script_sha256": "8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d",
        "g7_entrypoint": "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py",
        "g7_script_sha256": "f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe",
        "implementation_commit_sha": FF4A,
        "mapping_receipt_sha256": "6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0",
        "owner_decision_sha256": "3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a",
        "preflight_result_sha256": "62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae",
    },
}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------- 1. historical-row binding
def _row(sample: str, sample_row: int, source: str, cid: str) -> dict:
    """Real Sample-A freeze schema (every column G6 and G7 require); like the real file, no physical global_row."""
    return {"sample": sample, "sample_row": str(sample_row), "source": source, "matrix_id": f"{source}::m",
            "operator_index": "0", "local_row": str(sample_row), "donor_id": f"donor_{cid}", "cell_id": cid}


# Sample-B rows interleaved before and between Sample-A rows, and Sample-A rows out of sample_row order, so the
# freeze-file position (global_row) differs from sample_row for every Sample-A row.
FREEZE_ROWS = [
    _row("B_COVERAGE_DISCOVERY", 0, "HVS", "b0"),        # file position 0
    _row("A_NATURAL_MIXTURE", 2, "SEA_AD", "a2"),         # 1
    _row("B_COVERAGE_DISCOVERY", 1, "SEA_AD", "b1"),      # 2
    _row("A_NATURAL_MIXTURE", 0, "HVS", "a0"),            # 3
    _row("B_COVERAGE_DISCOVERY", 2, "NPH52", "b2"),       # 4
    _row("A_NATURAL_MIXTURE", 1, "NPH52", "a1"),          # 5
]
EXPECTED_GLOBAL_ROW_BY_SAMPLE_ROW = [3, 5, 1]             # a0 at 3, a1 at 5, a2 at 1


def _frame() -> pd.DataFrame:
    f = pd.DataFrame(FREEZE_ROWS).astype(str)
    assert "global_row" not in f.columns
    return f


def _small_geometry(monkeypatch, m) -> None:
    monkeypatch.setattr(m, "N_SAMPLE_A", 3)
    monkeypatch.setattr(m, "SOURCE_COUNTS", {"HVS": 1, "NPH52": 1, "SEA_AD": 1})


def test_g7_binds_global_row_from_freeze_file_position_before_filtering(monkeypatch):
    g7 = W.load_script(W.G7_SCRIPT, "g7_global_row_regression")
    _small_geometry(monkeypatch, g7)
    selected = g7.select_sample_a(_frame())
    assert selected.sample_row.astype(int).tolist() == [0, 1, 2]
    assert selected["global_row"].astype(int).tolist() == EXPECTED_GLOBAL_ROW_BY_SAMPLE_ROW
    assert selected["global_row"].astype(int).tolist() != selected.sample_row.astype(int).tolist()


def test_g7_and_accepted_g6_selectors_agree_on_historical_rows(monkeypatch):
    g6 = W.load_script(W.G6_SCRIPT, "g6_selector_reference")
    g7 = W.load_script(W.G7_SCRIPT, "g7_selector_candidate")
    for m in (g6, g7):
        _small_geometry(monkeypatch, m)
    a = g6.select_sample_a(_frame(), enforce_geometry=True)
    b = g7.select_sample_a(_frame())
    assert a["global_row"].astype(int).tolist() == b["global_row"].astype(int).tolist() == EXPECTED_GLOBAL_ROW_BY_SAMPLE_ROW
    assert a.cell_id.tolist() == b.cell_id.tolist()


def test_g7_refuses_a_freeze_missing_required_columns(monkeypatch):
    g7 = W.load_script(W.G7_SCRIPT, "g7_required_columns")
    _small_geometry(monkeypatch, g7)
    with pytest.raises(RuntimeError, match="missing required columns"):
        g7.select_sample_a(_frame().drop(columns=["local_row"]))


def test_g7_validates_an_explicit_global_row_like_g6(monkeypatch):
    g7 = W.load_script(W.G7_SCRIPT, "g7_explicit_global_row")
    _small_geometry(monkeypatch, g7)
    f = _frame()
    f["global_row"] = ["9", "9", "1", "2", "3", "4"]                    # duplicate identities
    with pytest.raises(RuntimeError, match="global_row"):
        g7.select_sample_a(f)


# --------------------------------------------------------------------------------- 2. accepted-G6 predecessor bridge
def _bridge(w, receipt=None, acceptance=None):
    return w.g7.load_accepted_g6_predecessor(receipt or w.g6_receipt, acceptance or w.g6_acceptance,
                                             **W.g7_prerequisite_inputs(w))


def test_production_predecessor_pins_are_exactly_the_accepted_g6(tmp_path, monkeypatch):
    g7 = W.load_script(W.G7_SCRIPT, "g7_pins")
    assert g7.ACCEPTED_G6_PREDECESSOR == REAL_PREDECESSOR
    assert set(REAL_PREDECESSOR["artifact_sha256"]) == set(g7.common.G6_PASS_FILES)
    acc = FIX / "TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json"
    assert sha(acc) == REAL_PREDECESSOR["external_acceptance_sha256"]
    rec = json.loads(acc.read_text(encoding="utf-8"))
    assert rec["g6_artifact_sha256"] == REAL_PREDECESSOR["artifact_sha256"]
    assert rec["implementation_commit_sha"] == FF4A


def test_exact_accepted_predecessor_passes(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    out = _bridge(w)
    assert out["g7_verified_g6_execution_sha256"]["receipt"] == sha(w.g6_receipt)
    p = out["g7_g6_predecessor"]
    assert p["external_acceptance_sha256"] == sha(w.g6_acceptance)
    assert p["authority_trace"] == w.g7.ACCEPTED_G6_PREDECESSOR["authority_trace"]


@pytest.mark.parametrize("name", sorted(W.load_script(W.G6_SCRIPT, "g6_names").common.G6_PASS_FILES))
def test_any_altered_predecessor_artifact_fails(tmp_path, monkeypatch, name):
    w = W.build_g7_world(tmp_path, monkeypatch)
    victim = w.g6_out / name
    b = bytearray(victim.read_bytes()); b[len(b) // 2] ^= 1
    victim.write_bytes(bytes(b))
    with pytest.raises(RuntimeError, match="differs from the accepted execution"):
        _bridge(w)


def _second_authorized_g6_execution(root, monkeypatch):
    """A second genuine G6 PASS execution of the same synthetic world, under its own separately written owner
    decision and runtime authorization. The synthetic world and gate are deterministic, so without a distinct
    authority the second run reproduces the accepted bytes exactly (see the relocated-copy test below)."""
    other = W.build_g6_world(root, monkeypatch)
    decision = json.loads(other.gate.owner_decision.read_text(encoding="utf-8"))
    decision["synthetic_execution"] = "second_historical_g6_execution"
    other.gate.owner_decision.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    W.F.rewrite_authorization(other.g6.common, other.gate)
    assert W.run_g6(other, monkeypatch) == 0
    return other


def test_another_historical_g6_receipt_fails(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path / "accepted", monkeypatch)
    other = _second_authorized_g6_execution(tmp_path / "other", monkeypatch)
    other_receipt = other.g6_out / "G6_RECEIPT.json"
    assert json.loads(other_receipt.read_text(encoding="utf-8"))["status"] == "PASS_TD_G6_SOURCE_LIBRARY_EXACT"
    assert sha(other_receipt) != sha(w.g6_receipt)
    with pytest.raises(RuntimeError, match="differs from the accepted execution"):
        _bridge(w, receipt=other_receipt)


def test_a_byte_identical_relocated_copy_is_the_same_accepted_execution(tmp_path, monkeypatch):
    """Provenance is content-addressed: the five accepted files copied elsewhere are the same evidence."""
    w = W.build_g7_world(tmp_path, monkeypatch)
    copy = tmp_path / "relocated" / "G6_OUT"
    shutil.copytree(w.g6_out, copy)
    assert _bridge(w, receipt=copy / "G6_RECEIPT.json")["g7_verified_g6_execution_sha256"]["receipt"] == sha(w.g6_receipt)
    (copy / "EXTRA.txt").write_text("foreign\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not the accepted predecessor execution"):
        _bridge(w, receipt=copy / "G6_RECEIPT.json")


def test_real_predecessor_pins_refuse_any_other_g6_execution(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    monkeypatch.setattr(w.g7, "ACCEPTED_G6_PREDECESSOR", REAL_PREDECESSOR)
    shutil.copy(FIX / "TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json", tmp_path / "acc.json")
    with pytest.raises(RuntimeError, match="differs from the accepted execution"):   # the real acceptance passes
        _bridge(w, acceptance=tmp_path / "acc.json")


ACCEPTANCE_REFUSAL = {"disposition": "external_audit_disposition", "commit": "accept this predecessor: implementation_commit_sha",
                      "artifacts": "g6_artifact_sha256", "authorizes_training": "training_authorized=false",
                      "authorizes_td60": "td60_authorized=false", "authorizes_biology": "biological_replay_authorized=false",
                      "authorizes_targets": "target_selection_authorized=false", "missing": "missing G6 external acceptance"}


@pytest.mark.parametrize("change", sorted(ACCEPTANCE_REFUSAL))
def test_altered_or_missing_external_acceptance_fails(tmp_path, monkeypatch, change):
    w = W.build_g7_world(tmp_path, monkeypatch)
    rec = json.loads(w.g6_acceptance.read_text(encoding="utf-8"))
    mutate = {"disposition": ("external_audit_disposition", "REJECT"), "commit": ("implementation_commit_sha", "b" * 40),
              "artifacts": ("g6_artifact_sha256", {}), "authorizes_training": ("training_authorized", True),
              "authorizes_td60": ("td60_authorized", True), "authorizes_biology": ("biological_replay_authorized", True),
              "authorizes_targets": ("target_selection_authorized", True)}
    bad = tmp_path / "bad_acceptance.json"
    if change == "missing":
        bad = tmp_path / "absent.json"
    else:
        key, value = mutate[change]
        rec[key] = value
        bad.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # rehash: even an acceptance whose pin is updated must still carry the accepted content
        pins = dict(w.g7.ACCEPTED_G6_PREDECESSOR, external_acceptance_sha256=sha(bad))
        monkeypatch.setattr(w.g7, "ACCEPTED_G6_PREDECESSOR", pins)
    with pytest.raises(RuntimeError, match=ACCEPTANCE_REFUSAL[change]):
        _bridge(w, acceptance=bad)


def test_unrehashed_acceptance_edit_fails_on_the_pinned_acceptance_sha(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    rec = json.loads(w.g6_acceptance.read_text(encoding="utf-8"))
    rec["note"] = "edited after acceptance"
    w.g6_acceptance.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="not the accepted record"):
        _bridge(w)


def test_g7_main_consumes_only_the_accepted_predecessor_and_records_both_identities(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    rc, out = W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP)
    assert rc == 0
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["g6_predecessor"]["external_acceptance_sha256"] == sha(w.g6_acceptance)
    assert r["g6_predecessor"]["authority_trace"] == w.g7.ACCEPTED_G6_PREDECESSOR["authority_trace"]
    assert r["authority_trace"]["g6_receipt_sha256"] == sha(w.g6_receipt)
    for key in ("biological_replay_authorized", "target_selection_authorized", "td60_authorized", "training_authorized"):
        assert r[key] is False
    marker = json.loads(out.with_name(out.name + ".STARTED_NOT_A_PASS.json").read_text(encoding="utf-8"))
    assert marker["g6_predecessor"] == r["g6_predecessor"]                        # GREEN-only addition
    assert marker["g6_receipt_sha256"] == sha(w.g6_receipt)


def test_g7_main_refuses_without_the_external_acceptance(tmp_path, monkeypatch):
    w = W.build_g7_world(tmp_path, monkeypatch)
    w.g6_acceptance = tmp_path / "missing_acceptance.json"
    with pytest.raises(RuntimeError, match="missing G6 external acceptance"):
        W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP)
    assert not (tmp_path / "g7_out").exists()                      # refused before the attempt marker


@pytest.mark.parametrize("key", ["common_script_sha256", "g6_script_sha256"])
def test_g7_main_refuses_successor_code_that_is_not_the_accepted_g6_producer(tmp_path, monkeypatch, key):
    """GREEN-only addition: the successor replaces G7 only; common and G6 must stay the producer's exact code."""
    w = W.build_g7_world(tmp_path, monkeypatch)
    pins = json.loads(json.dumps(w.g7.ACCEPTED_G6_PREDECESSOR))
    pins["authority_trace"][key] = "0" * 64
    monkeypatch.setattr(w.g7, "ACCEPTED_G6_PREDECESSOR", pins)
    with pytest.raises(RuntimeError, match=f"differs from the accepted G6 producer: {key}"):
        W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP)
    assert not (tmp_path / "g7_out").exists()


# ------------------------------------------------------------------------------- 3. authority stays separate
SUCCESSOR_COMMIT = "b" * 40          # the synthetic G6 producer ran at "a" * 40 (fake_code_identity default)


def _as_successor_code(w, monkeypatch) -> None:
    """G7 now executes as a different commit than the G6 producer, as in the real successor run."""
    common = w.g7.common
    monkeypatch.setattr(common, "code_identity",
                        lambda left, right: W.F.fake_code_identity(common, left, right, commit=SUCCESSOR_COMMIT))


def _fresh_successor_authority(w, root: Path) -> SimpleNamespace:
    """A synthetic stand-in for the owner's fresh successor authority: a new owner decision for the successor commit
    and a runtime authorization bound to it, beside the same PR #259 receipts and replay manifest."""
    root.mkdir()
    gate = SimpleNamespace(**vars(w.gate))
    gate.owner_decision, gate.auth = root / "owner_decision.json", root / "auth.json"
    W.F.write_json(gate.owner_decision, W.F.synthetic_owner_decision(w.g7.common, commit=SUCCESSOR_COMMIT))
    W.F.rewrite_authorization(w.g7.common, gate)
    return gate


def test_g7_runs_under_its_own_authority_distinct_from_the_g6_producer(tmp_path, monkeypatch):
    """GREEN-only addition after independent review. In the shared synthetic gate the successor trace equals the
    producer trace, so a bridge validating G6 against the successor's trace would pass every other test. Here the
    two traces differ, as in the real run: G6 stays bound to its producer trace, and G7 runs under its own."""
    w = W.build_g7_world(tmp_path, monkeypatch)
    producer = w.g7.ACCEPTED_G6_PREDECESSOR["authority_trace"]
    _as_successor_code(w, monkeypatch)
    w.gate = _fresh_successor_authority(w, tmp_path / "successor_authority")
    rc, out = W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP)
    assert rc == 0
    r = json.loads(out.read_text(encoding="utf-8"))
    t = r["authority_trace"]
    assert t["implementation_commit_sha"] == SUCCESSOR_COMMIT != producer["implementation_commit_sha"]
    assert t["owner_decision_sha256"] == sha(w.gate.owner_decision) != producer["owner_decision_sha256"]
    assert t["authorization_sha256"] == sha(w.gate.auth) != producer["authorization_sha256"]
    assert {k: v for k, v in t.items() if k not in ("g6_receipt_sha256", "g6_execution_sha256")} != producer
    assert r["g6_predecessor"]["authority_trace"] == producer
    assert t["g6_receipt_sha256"] == sha(w.g6_receipt)


def test_producer_authority_cannot_run_successor_code(tmp_path, monkeypatch):
    """The synthetic counterpart of the real gate's N1: the producer's own owner decision and authorization, with the
    G7 code executing as a different commit, are refused before the attempt marker."""
    w = W.build_g7_world(tmp_path, monkeypatch)
    _as_successor_code(w, monkeypatch)
    with pytest.raises(RuntimeError, match="qualified implementation commit"):
        W.run_g7(w, monkeypatch, tmp_path, cells=W.S174_CELLS_OVERLAP)
    assert not (tmp_path / "g7_out").exists()


def test_old_ff4a21f9_authority_cannot_authorize_successor_g7():
    common = W.load_script(W.F.COMMON, "common_successor_authority")
    old_owner = FIX / "TD_G6G7_OWNER_DECISION_ff4a21f9.json"
    old_auth = FIX / "TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json"
    assert sha(old_owner) == REAL_PREDECESSOR["authority_trace"]["owner_decision_sha256"]
    assert sha(old_auth) == REAL_PREDECESSOR["authority_trace"]["authorization_sha256"]
    auth = json.loads(old_auth.read_text(encoding="utf-8"))
    assert auth["implementation_commit_sha"] == FF4A
    assert auth["g7_script_sha256"] != common.canonical_text_sha256(W.G7_SCRIPT)      # successor G7 code differs
    head = common.git_commit_sha(W.G7_SCRIPT)
    assert head != FF4A
    with pytest.raises(RuntimeError, match="qualified implementation commit"):
        common.load_owner_decision(old_owner, implementation_commit_sha=head)


def test_successor_keeps_common_and_g6_byte_identical_to_the_accepted_execution():
    common = W.load_script(W.F.COMMON, "common_identity_check")
    t = REAL_PREDECESSOR["authority_trace"]
    assert common.canonical_text_sha256(W.F.COMMON) == t["common_script_sha256"]
    assert common.canonical_text_sha256(W.G6_SCRIPT) == t["g6_script_sha256"]
