"""Additive 15C repair that replaces only the legacy HC3 report and gate."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np


HERE = Path(__file__).resolve().parent
QR_PATH = HERE / "contextual_target_f1_hc3_stable_qr_v2.py"
EXPECTED = {
    "design": "5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3",
    "schema": "d7d0be302b455f7be0982d3e7906778c4fac59aee9b9f5c43e6017090d25e778",
    "effective": "37653ed4a21f513a7389630bffa7447f9022323e8240bb80f53394138f1917eb",
    "decision_v1": "204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34",
    "decision_v4": "5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913",
    "integration_v4": "5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a",
    "truth_table": "76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e",
}
INPUT_FIELDS = {"donor_records", "legal"}
VECTOR_FIELDS = ("overall_A", "qid_margin", "qid_win_minus_half", "draw0", "draw1")
FAMILY_FIELDS = ("program_A", "program_delta", "program_qid_margin")
RECORD_FIELDS = {*VECTOR_FIELDS, *FAMILY_FIELDS, "evidence_A"}
REAL_READER_FORWARD_AUTHORITY_SHA256 = None


def _load_qr():
    spec = importlib.util.spec_from_file_location("f1_hc3_stable_qr_v2", QR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def array_sha256(value) -> str:
    array = np.asarray(value, dtype="<f8")
    return sha256_bytes(array.tobytes(order="C"))


def _rank(x: np.ndarray) -> int:
    singular = np.linalg.svd(np.asarray(x, np.float64), compute_uv=False)
    tolerance = max(x.shape) * np.finfo(np.float64).eps * singular[0]
    return int(np.sum(singular > tolerance))


def verify_candidate_selected_design(schema_bytes: bytes, design_bytes: bytes):
    if sha256_bytes(schema_bytes) != EXPECTED["schema"] or sha256_bytes(design_bytes) != EXPECTED["design"]:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    schema = json.loads(schema_bytes.decode("utf-8"))
    if schema.get("selected_triple") != [5, 0, 4] or schema.get("shape") != [104, 16]:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    if len(schema.get("donor_order", [])) != 104 or len(set(schema["donor_order"])) != 104:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    raw = np.frombuffer(design_bytes, dtype="<f8")
    if raw.size != 104 * 16:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    raw = raw.reshape(104, 16).copy()
    if not np.isfinite(raw).all() or not np.array_equal(raw[:, 0], np.ones(104)) or _rank(raw) != 16:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    return schema, raw


def load_frozen_effective_design(authority_root: Path):
    directory = Path(authority_root) / "outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902"
    schema_bytes = (directory / "F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json").read_bytes()
    design_bytes = (directory / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin").read_bytes()
    schema, raw = verify_candidate_selected_design(schema_bytes, design_bytes)
    effective = np.ones((104, 1), dtype=np.float64)
    for index in range(1, 16):
        candidate = np.column_stack([effective, raw[:, index] - raw[:, index].mean()])
        if _rank(candidate) > _rank(effective):
            effective = candidate
    if effective.shape != (104, 16) or _rank(effective) != 16 or array_sha256(effective) != EXPECTED["effective"]:
        raise ValueError("STOP_F1_15C_EFFECTIVE_DESIGN_MISMATCH")
    if any(_rank(np.delete(effective, index, axis=0)) != 16 for index in range(104)):
        raise ValueError("STOP_F1_15C_LOO_RANK_MISMATCH")
    return schema, raw, effective


def _git_blob(repo_root: Path, relative: str, expected: str) -> bytes:
    data = subprocess.check_output(["git", "-C", str(repo_root), "show", "HEAD:" + relative])
    if sha256_bytes(data) != expected:
        raise ValueError("STOP_F1_15C_AUTHORITY_MISMATCH")
    return data


def _legacy_v4_decision(payload: dict, repo_root: Path) -> dict:
    v1 = _git_blob(repo_root, "scripts/v4/contextual_target_f1_decision_v1.py", EXPECTED["decision_v1"])
    v4 = _git_blob(repo_root, "scripts/v4/contextual_target_f1_decision_v4.py", EXPECTED["decision_v4"])
    _git_blob(repo_root, "scripts/v4/contextual_target_f1_decision_integration_v4.py", EXPECTED["integration_v4"])
    with tempfile.TemporaryDirectory(prefix="f1_15c_frozen_v4_") as temporary:
        directory = Path(temporary)
        (directory / "contextual_target_f1_decision_v1.py").write_bytes(v1)
        v4_path = directory / "contextual_target_f1_decision_v4.py"
        v4_path.write_bytes(v4)
        spec = importlib.util.spec_from_file_location("f1_15c_frozen_decision_v4", v4_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.qualify_current(payload)


def _decision_payload(synthetic: dict, schema: dict, raw: np.ndarray) -> dict:
    if set(synthetic) != INPUT_FIELDS or type(synthetic["legal"]) is not bool:
        raise ValueError("caller-supplied or invalid authority field")
    records = synthetic["donor_records"]
    if not isinstance(records, dict) or len(records) != 104 or set(records) != set(schema["donor_order"]):
        raise ValueError("donor population mismatch")
    if any(set(record) != RECORD_FIELDS for record in records.values()):
        raise ValueError("donor-keyed endpoint schema mismatch")
    ordered = [records[donor] for donor in schema["donor_order"]]
    aligned = {key: [record[key] for record in ordered] for key in VECTOR_FIELDS}
    evidence = np.asarray([record["evidence_A"] for record in ordered], dtype=np.float64)
    if evidence.shape != (104, 5) or not np.isfinite(evidence).all():
        raise ValueError("nonfinite or invalid decision endpoint")
    programs = set(ordered[0]["program_A"])
    families = {}
    for family in FAMILY_FIELDS:
        if any(set(record[family]) != programs for record in ordered):
            raise ValueError("protected-program family mismatch")
        families[family] = {}
        for program in sorted(programs):
            values = np.asarray([record[family][program] for record in ordered], dtype=np.float64)
            if values.shape != (104,) or not np.isfinite(values).all():
                raise ValueError("nonfinite or invalid decision endpoint")
            families[family][program] = values.tolist()
    if any(not np.isfinite(np.asarray(aligned[key], np.float64)).all() for key in VECTOR_FIELDS):
        raise ValueError("nonfinite or invalid decision endpoint")
    columns = {f"c{index:02d}_{schema['columns'][index]['identity']}": raw[:, index].tolist() for index in range(1, 16)}
    return {
        **aligned,
        **families,
        "evidence_A": evidence.tolist(),
        "nuisance_y": aligned["overall_A"],
        "source_group": [donor.split("::", 1)[0] for donor in schema["donor_order"]],
        "nuisance_columns": columns,
        "legal": synthetic["legal"],
    }


def qualify_synthetic(synthetic: dict, *, authority_root: Path, repo_root: Path) -> dict:
    schema, raw, effective = load_frozen_effective_design(authority_root)
    payload = _decision_payload(synthetic, schema, raw)
    legacy = _legacy_v4_decision(payload, repo_root)
    repaired = replace_hc3_only(legacy, payload["nuisance_y"], effective, expected_rank=16, expected_df=88)
    repaired.update({
        "truth_table_sha256": EXPECTED["truth_table"],
        "nuisance_design_sha256": EXPECTED["design"],
        "nuisance_schema_sha256": EXPECTED["schema"],
        "nuisance_effective_centered_design_sha256": EXPECTED["effective"],
        "nuisance_selected_triple": [5, 0, 4],
        "donor_order_sha256": sha256_bytes("\n".join(schema["donor_order"]).encode("utf-8")),
        "real_reader_forward_authority": REAL_READER_FORWARD_AUTHORITY_SHA256,
    })
    return repaired


def integrate_real_records(*_args, **_kwargs):
    raise ValueError("STOP_F1_REAL_READER_FORWARD_AUTHORITY_UNSET")


def replace_hc3_only(
    legacy_decision: dict,
    y,
    effective_design,
    *,
    expected_rank: int = 16,
    expected_df: int = 88,
) -> dict:
    """Return a copy with exactly the nuisance report and HC3 gate replaced."""
    if "gates" not in legacy_decision or "reports" not in legacy_decision:
        raise ValueError("decision structure mismatch")
    if list(legacy_decision["gates"]).count("hc3_nuisance_positive") != 1:
        raise ValueError("exactly one HC3 gate required")
    before_gates = copy.deepcopy(legacy_decision["gates"])
    before_reports = copy.deepcopy(legacy_decision["reports"])
    repaired = copy.deepcopy(legacy_decision)
    stable = _load_qr().hc3_intercept_qr(
        y,
        effective_design,
        expected_rank=expected_rank,
        expected_df=expected_df,
    )
    repaired["reports"]["nuisance"] = stable
    repaired["gates"]["hc3_nuisance_positive"] = bool(stable["estimable"] and stable["lower"] is not None and stable["lower"] > 0.0)
    repaired["qualified"] = bool(all(repaired["gates"].values()))
    repaired["legacy_hc3_nonauthoritative"] = True
    repaired["conclusion_bearing_hc3_method"] = stable["method"]

    if any(repaired["gates"][key] != value for key, value in before_gates.items() if key != "hc3_nuisance_positive"):
        raise RuntimeError("non-HC3 gate changed")
    if any(repaired["reports"][key] != value for key, value in before_reports.items() if key != "nuisance"):
        raise RuntimeError("non-HC3 report changed")
    return repaired
