"""Additive, synthetic-only binding of the frozen 15B HC3 design to decision v4."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
P15A4 = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_replication_frontier_complete_20260902"
P15B = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902"
PPROV = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_15b_provenance_repair_20260902"
DECISION = HERE / "contextual_target_f1_decision_v4.py"
INTEGRATION = HERE / "contextual_target_f1_decision_integration_v4.py"

EXPECTED = {
    "15a4_manifest": "a112bd4907f2c20b4346179264391ceb8d3e9ceee42f7a8bcb1bcd153e4cb09f",
    "15b_manifest": "a9d10fa17f162f3552c15095f3ef3ed7111f71c7a83978682303a2138088e174",
    "provenance_manifest": "6b0abab515b847fda5724b3194efdd4ad1f58ec0a7e3ad20fa9941f24e6e513d",
    "schema": "d7d0be302b455f7be0982d3e7906778c4fac59aee9b9f5c43e6017090d25e778",
    "design": "5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3",
    "triple": "33874fa03afd820c6460c3561dabf75094ff79b512b8efa5f4bfdd4aaa611206",
    "geometry": "830db158e44aa6705f0811af71a4dfcb19276a076027d8c2bc6e8c07db4a3cdd",
    "decision": "5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913",
    "integration": "5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a",
    "truth_table": "76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e",
    "component": "ac8157105b66ccd1617efb3740768a91711b429e5288afc34fb9a54adedcc462",
    "legal_manifest": "e95aac28c3dacaeba94b202a2be53b46e94c848dd7fbb433b9d99b58efa94976",
    "assignment": "12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617",
    "null_map": "aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6",
    "namespace_semantic": "595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f",
    "namespace_audit": "14b423d5ebca3cdda9a71d0d8b1974e7fe00aaaf84711355312cca01f5085384",
}
REAL_READER_FORWARD_AUTHORITY_SHA256 = None
INPUT_FIELDS = {"donor_records", "legal"}
RECORD_FIELDS = {
    "overall_A", "program_A", "program_delta", "evidence_A", "qid_margin",
    "qid_win_minus_half", "program_qid_margin", "draw0", "draw1",
}
VECTOR_FIELDS = ("overall_A", "qid_margin", "qid_win_minus_half", "draw0", "draw1")
FAMILY_FIELDS = ("program_A", "program_delta", "program_qid_margin")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_manifest(directory: Path, manifest_name: str, expected_sha: str) -> int:
    manifest = directory / manifest_name
    if sha256(manifest) != expected_sha:
        raise ValueError("STOP_F1_15C_AUTHORITY_MISMATCH")
    rows = list(csv.DictReader(manifest.open(newline="", encoding="utf-8-sig")))
    for row in rows:
        artifact = directory / row["relative_path"]
        if not artifact.is_file() or artifact.stat().st_size != int(row["bytes"]) or sha256(artifact) != row["sha256"].lower():
            raise ValueError("STOP_F1_15C_AUTHORITY_MISMATCH")
    return len(rows)


def verify_authorities() -> dict:
    counts = {
        "15a4": verify_manifest(P15A4, "F1_HC3_15A4_MANIFEST.csv", EXPECTED["15a4_manifest"]),
        "15b": verify_manifest(P15B, "F1_HC3_15B_MANIFEST.csv", EXPECTED["15b_manifest"]),
        "provenance": verify_manifest(PPROV, "F1_HC3_15B_PROVENANCE_REPAIR_MANIFEST.csv", EXPECTED["provenance_manifest"]),
    }
    paths = {
        "schema": P15B / "F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json",
        "design": P15B / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin",
        "triple": P15B / "F1_HC3_SELECTED_TRIPLE.json",
        "geometry": P15B / "F1_HC3_SELECTED_GEOMETRY.json",
        "decision": DECISION,
        "integration": INTEGRATION,
    }
    if any(sha256(path) != EXPECTED[key] for key, path in paths.items()):
        raise ValueError("STOP_F1_15C_AUTHORITY_MISMATCH")
    external_paths = {
        "component": HERE / "contextual_target_f1_querydesign_decision_v2.py",
        "legal_manifest": ROOT / "outputs/contextual_teacher_target_v1_f1_legal_boolean_repair_20260902/F1_LEGAL_BOOLEAN_REPAIR_MANIFEST.csv",
        "assignment": ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv",
        "null_map": ROOT / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv",
        "truth_table": ROOT / "outputs/contextual_teacher_target_v1_f1_decision_truth_table_repair_20260902/F1_FINAL_DECISION_TRUTH_TABLE_V2.json",
        "namespace_audit": ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_ADDRESS_NAMESPACE_AUDIT.json",
    }
    if any(sha256(path) != EXPECTED[key] for key, path in external_paths.items()):
        raise ValueError("STOP_F1_15C_AUTHORITY_MISMATCH")
    namespace = json.loads((ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_ADDRESS_NAMESPACE_AUDIT.json").read_text(encoding="utf-8"))
    if namespace.get("ordered_namespace_semantic_sha256") != EXPECTED["namespace_semantic"] or namespace.get("length") != 41238:
        raise ValueError("STOP_F1_15C_AUTHORITY_MISMATCH")
    chronology = json.loads((PPROV / "F1_HC3_15B_CHRONOLOGY_RECORD.json").read_text(encoding="utf-8"))
    if "EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE" not in json.dumps(chronology):
        raise ValueError("STOP_F1_15C_AUTHORITY_MISMATCH")
    return {"manifest_file_counts": counts, "chronology_limit_preserved": True, "external_authorities": {key: EXPECTED[key] for key in external_paths}, "address_namespace_semantic_root": EXPECTED["namespace_semantic"]}


def _rank(x: np.ndarray) -> tuple[int, float]:
    s = np.linalg.svd(np.asarray(x, np.float64), compute_uv=False)
    tol = max(x.shape) * np.finfo(np.float64).eps * s[0]
    return int(np.sum(s > tol)), float(tol)


def verify_candidate_selected_design(schema_bytes: bytes, design_bytes: bytes) -> tuple[dict, np.ndarray]:
    if hashlib.sha256(schema_bytes).hexdigest() != EXPECTED["schema"] or hashlib.sha256(design_bytes).hexdigest() != EXPECTED["design"]:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    schema = json.loads(schema_bytes.decode("utf-8"))
    if schema.get("selected_triple") != [5, 0, 4] or schema.get("shape") != [104, 16]:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    x = np.frombuffer(design_bytes, dtype="<f8")
    if x.size != 104 * 16:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    x = x.reshape(104, 16).copy()
    if not np.isfinite(x).all() or not np.array_equal(x[:, 0], np.ones(104)):
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    rank, _ = _rank(x)
    if rank != 16 or len(set(schema["donor_order"])) != 104:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    return schema, x


def load_selected_design() -> tuple[dict, np.ndarray]:
    schema_path = P15B / "F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json"
    design_path = P15B / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin"
    return verify_candidate_selected_design(schema_path.read_bytes(), design_path.read_bytes())


def reverify_selected_design() -> dict:
    schema, x = load_selected_design()
    rank, tol = _rank(x)
    q_svd = np.linalg.svd(x, full_matrices=False)[0]
    h_svd = np.sum(q_svd * q_svd, axis=1)
    q_qr = np.linalg.qr(x, mode="reduced")[0]
    h_qr = np.sum(q_qr * q_qr, axis=1)
    loo = [i for i in range(104) if _rank(np.delete(x, i, axis=0))[0] != rank]
    geometry = json.loads((P15B / "F1_HC3_SELECTED_GEOMETRY.json").read_text(encoding="utf-8"))
    result = {
        "status": "PASS_F1_15C_SELECTED_DESIGN_REVERIFIED",
        "selected_triple": schema["selected_triple"], "design_sha256": EXPECTED["design"],
        "schema_sha256": EXPECTED["schema"], "shape": list(x.shape), "rank": rank, "df": 104-rank,
        "all_finite": bool(np.isfinite(x).all()), "rank_tolerance": tol,
        "max_leverage_svd": float(h_svd.max()), "max_leverage_qr": float(h_qr.max()),
        "svd_qr_max_abs_difference": float(np.max(np.abs(h_svd-h_qr))),
        "min_one_minus_h": float(np.min(1-h_svd)), "hc3_boundary": geometry["hc3_boundary"],
        "loo_critical_indices": loo, "loo_stable_count": 104-len(loo),
        "basis_scaling_invariance_bound_by_15b": bool(geometry["invertible_reparameterization_hat_invariant"]),
    }
    if loo or result["df"] != 88 or result["min_one_minus_h"] <= result["hc3_boundary"] or result["svd_qr_max_abs_difference"] > 1e-12:
        raise ValueError("STOP_F1_15C_SELECTED_DESIGN_MISMATCH")
    return result


def qualify_synthetic(synthetic: dict) -> dict:
    if set(synthetic) != INPUT_FIELDS:
        raise ValueError("caller-supplied or missing authority field")
    if type(synthetic["legal"]) is not bool:
        raise ValueError("legal provenance authority must be built-in bool")
    schema, x = load_selected_design()
    records = synthetic["donor_records"]
    if not isinstance(records, dict) or len(records) != 104 or set(records) != set(schema["donor_order"]):
        raise ValueError("donor population mismatch")
    if any(set(record) != RECORD_FIELDS for record in records.values()):
        raise ValueError("donor-keyed endpoint schema mismatch")
    ordered = [records[d] for d in schema["donor_order"]]
    aligned = {key: [record[key] for record in ordered] for key in VECTOR_FIELDS}
    evidence = np.asarray([record["evidence_A"] for record in ordered], np.float64)
    if evidence.shape != (104, 5) or not np.isfinite(evidence).all():
        raise ValueError("nonfinite or invalid decision endpoint")
    families = {}
    for family in FAMILY_FIELDS:
        if any(set(record[family]) != set(_load(DECISION, "f1_15c_schema").PROGRAMS) for record in ordered):
            raise ValueError("protected-program family mismatch")
        families[family] = {}
        for program in ordered[0][family]:
            a = np.asarray([record[family][program] for record in ordered], np.float64)
            if a.shape != (104,) or not np.isfinite(a).all():
                raise ValueError("nonfinite or invalid decision endpoint")
            families[family][program] = a.tolist()
    if any(not np.isfinite(np.asarray(aligned[key], np.float64)).all() for key in VECTOR_FIELDS):
        raise ValueError("nonfinite or invalid decision endpoint")
    columns = {f"c{i:02d}_{schema['columns'][i]['identity']}": x[:, i].tolist() for i in range(1, 16)}
    payload = {
        **aligned, **families, "evidence_A": evidence.tolist(),
        "nuisance_y": aligned["overall_A"],
        "source_group": [d.split("::", 1)[0] for d in schema["donor_order"]],
        "nuisance_columns": columns, "legal": synthetic["legal"],
    }
    decision_module = _load(DECISION, "f1_15c_decision_v4")
    effective, kept = decision_module.arithmetic().nuisance_design(columns, 104)
    decision = decision_module.qualify_current(payload)
    decision["truth_table_sha256"] = EXPECTED["truth_table"]
    decision["nuisance_design_sha256"] = EXPECTED["design"]
    decision["nuisance_effective_centered_design_sha256"] = hashlib.sha256(effective.astype("<f8",copy=False).tobytes(order="C")).hexdigest()
    decision["nuisance_design_transform"] = "exact frozen binary columns followed by the pre-existing decision-v1 mean-centering operation"
    decision["nuisance_effective_kept_columns"] = kept
    decision["nuisance_selected_triple"] = [5, 0, 4]
    decision["donor_order_sha256"] = hashlib.sha256("\n".join(schema["donor_order"]).encode()).hexdigest()
    decision["real_reader_forward_authority"] = REAL_READER_FORWARD_AUTHORITY_SHA256
    return decision


def integrate_real_records(records, forward_authority_sha256):
    raise ValueError("STOP_F1_REAL_READER_FORWARD_AUTHORITY_UNSET")
