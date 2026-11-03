"""Read-only V79/V80 terminal-lock conflict preflight: NO model-selection authority.

Inspects exact frozen *raw* V79 V2 contract and V80 binding/receipt bytes.
It never reads V79 controller gate outcomes or fits, never calls an estimator,
and never changes the original V79 or V80 artifacts.

The result identifies the prospective contract conflict and always BLOCKS
successor estimator qualification pending a separately accepted, precommitted
selection-law successor. Do not use this diagnostic to accept any estimator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


V79_CONTRACT_SHA256 = "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
V80_BINDING_SHA256 = "b83d7e0becbe5480353db657b553b7bb65251d3b88136be1d6c3cdda365c4819"
V80_RECEIPT_SHA256 = "346407af801a7fabc5dbd27136dcf5c9abe61e87d438018b98da192333eb9c32"
FAILED_GATE = "Q08_SPARSE_DETECTION_POSITIVE__CONVERGENCE_ALL_FITS_DIAGNOSED"
LOCK_LABEL = "POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION"
TERMINAL_INDEX = 206
AUTHORITY = {
    "successor_estimator_qualification_authorized": False,
    "training_authorized": False,
    "real_data_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "stage4_authorized": False,
}


class TerminalSelectionPreflightError(ValueError):
    pass


def _reject(message: str) -> None:
    raise TerminalSelectionPreflightError(message)


def _decode_pinned(raw: bytes, expected_sha: str, schema: str) -> dict:
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != expected_sha:
        _reject(f"frozen {schema} bytes/identity mismatch")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise TerminalSelectionPreflightError(f"invalid frozen {schema} JSON") from exc
    if type(result) is not dict or result.get("schema") != schema:
        _reject(f"frozen {schema} schema mismatch")
    return result


def _row_id(row: dict) -> str:
    if type(row) is not dict or any(type(row.get(k)) is not str for k in
                                    ("world", "part", "gate", "kind", "verdict_class")):
        _reject("V79 gate identity fields malformed")
    if row["kind"] not in ("STAT", "RULE") or row["verdict_class"] not in ("FAIL", "LIMIT"):
        _reject("V79 gate verdict class malformed")
    return f"{row['world']}_{row['part'].upper()}__{row['gate']}"


def _scope_digest(rows: list[dict]) -> str:
    # Diagnostic digest over frozen gate identity + kind + class; no outcomes.
    view = [
        {"row_index": i, "gate": _row_id(row), "kind": row["kind"],
         "verdict_class": row["verdict_class"]}
        for i, row in enumerate(rows)
    ]
    return hashlib.sha256(
        json.dumps(view, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest()


def analyze_terminal_scope(v79_contract: bytes, v80_binding: bytes, v80_receipt: bytes) -> dict:
    old = _decode_pinned(v79_contract, V79_CONTRACT_SHA256,
                         "V79_V2_CORE_QUALIFICATION_CONTRACT_V2")
    binding = _decode_pinned(v80_binding, V80_BINDING_SHA256,
                             "V80_V79_NONREGRESSION_BINDING_V1")
    receipt = _decode_pinned(v80_receipt, V80_RECEIPT_SHA256,
                             "V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1")

    if (type(binding.get("v79")) is not dict
            or binding["v79"].get("contract_sha256") != V79_CONTRACT_SHA256
            or binding["v79"].get("historical_result") != "NOT_QUALIFIED"
            or binding["v79"].get("passed_gates") != 291
            or binding["v79"].get("total_gates") != 292
            or binding["v79"].get("failed_gate") != FAILED_GATE
            or binding["v79"].get("failed_fit_count") != 3):
        _reject("V80 frozen V79 custody or terminal gate differs")
    successor = binding.get("successor_rule")
    if (type(successor) is not dict
            or successor.get("require_prior_v79_hard_passes_to_remain_pass") is not True
            or successor.get("evaluate_successor_on_existing_v79_worlds") is not True
            or successor.get("modify_v79_contract") is not False
            or successor.get("regenerate_v79_worlds") is not False):
        _reject("V80 non-regression law differs")
    if (receipt.get("status") != "BENCHMARK_PACKAGE_ONLY__NO_ESTIMATOR_RUN"
            or receipt.get("nonregression_binding_sha256") != V80_BINDING_SHA256
            or type(receipt.get("v79_immutable_binding")) is not dict
            or receipt["v79_immutable_binding"].get("contract_sha256") != V79_CONTRACT_SHA256
            or type(receipt.get("authority")) is not dict
            or not receipt["authority"]
            or any(value is not False for value in receipt["authority"].values())):
        _reject("V80 benchmark receipt, custody or authority mismatch")

    gates_obj = old.get("gates")
    if type(gates_obj) is not dict or type(gates_obj.get("list")) is not list:
        _reject("V79 gate roster unavailable")
    gates = gates_obj["list"]
    if len(gates) != 292:
        _reject("V79 roster not 292")
    ids = [_row_id(row) for row in gates]
    if len(set(ids)) != 292:
        _reject("duplicate V79 gate identities")
    if ids.count(FAILED_GATE) != 1 or ids.index(FAILED_GATE) != TERMINAL_INDEX:
        _reject("terminal gate is not at the frozen V79 index 206")
    if gates[TERMINAL_INDEX]["kind"] != "RULE" or gates[TERMINAL_INDEX]["verdict_class"] != "FAIL":
        _reject("terminal convergence gate not FAIL-class rule")
    t = old.get("terminal_logic")
    if (type(t) is not dict or t.get("post_terminal_label") != LOCK_LABEL
            or "first FAIL-class gate failure" not in str(t.get("terminal_lock", ""))
            or LOCK_LABEL not in t.get("terminal_lock", "")):
        _reject("V79 terminal-lock semantics unavailable")

    before, terminal, after = gates[:TERMINAL_INDEX], gates[TERMINAL_INDEX], gates[TERMINAL_INDEX+1:]
    def profile(rows):
        return {
            "rows": len(rows),
            "hard_fail_class": sum(r["verdict_class"] == "FAIL" for r in rows),
            "nonhard_limit_class": sum(r["verdict_class"] == "LIMIT" for r in rows),
        }
    if (profile(before) != {"rows": 206, "hard_fail_class": 204, "nonhard_limit_class": 2}
            or profile(after) != {"rows": 85, "hard_fail_class": 83, "nonhard_limit_class": 2}
            or profile(gates) != {"rows": 292, "hard_fail_class": 288, "nonhard_limit_class": 4}):
        _reject("V79 terminal gate class partition changed")

    return {
        "schema": "V79_V80_TERMINAL_SELECTION_SCOPE_PREFLIGHT_V1",
        "status": "BLOCKED_EXTERNAL_V79_TERMINAL_LOCK_VS_V80_291_NONREGRESSION_SELECTION",
        "scope": "READ_ONLY_ORIGINAL_CONTRACT_BOUNDARY_NO_FITS_NO_CONTROLLER_OUTCOMES",
        "v79_contract_sha256": V79_CONTRACT_SHA256,
        "v80_binding_sha256": V80_BINDING_SHA256,
        "v80_receipt_sha256": V80_RECEIPT_SHA256,
        "frozen_terminal": {
            "index_zero_based": TERMINAL_INDEX,
            "gate": FAILED_GATE,
            "historical_result": "NOT_QUALIFIED",
            "before_terminal": profile(before),
            "terminal_gate": {"rows": 1, "hard_fail_class": 1, "nonhard_limit_class": 0},
            "post_terminal_forensic_only": profile(after),
            "original_total": profile(gates),
            "confirmatory_inclusive_boundary_row_count": len(before)+1,
            "hard_nonregression_preterminal_pass_count": 204,
            "terminal_hard_fail_requiring_successor_repair": FAILED_GATE,
            "preterminal_limit_gates_are_not_hard": True,
            "post_terminal_may_select_reject_or_qualify": False,
            "confirmatory_roster_sha256": _scope_digest(gates[:TERMINAL_INDEX+1]),
            "forensic_roster_sha256": _scope_digest(after),
        },
        "frozen_v80_requirement": {
            "historical_pass_rows_claimed": binding["v79"]["passed_gates"],
            "requires_all_original_passes": True,
            "reconciliation_issued": False,
        },
        "proposed_prospective_rule_NOT_IN_FORCE": {
            "selection_scope": "V79_GATE_ROWS_0_THROUGH_206_INCLUSIVE",
            "preserve_preterminal_hard_gate_passes": 204,
            "terminal_hard_failure_must_be_repaired": True,
            "honor_original_two_nonhard_LIMIT_classes": True,
            "never_use_post_terminal_85_for_QUALIFICATION_OR_MODEL_SELECTION": True,
            "requires_independently_frozen_authorized_successor_law": True,
            "must_not_modify_frozen_v79_v80_artifacts": True,
        },
        "authority": dict(AUTHORITY),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only frozen V79/V80 conflict preflight")
    parser.add_argument("--v79-contract", type=Path, required=True)
    parser.add_argument("--v80-binding", type=Path, required=True)
    parser.add_argument("--v80-receipt", type=Path, required=True)
    args = parser.parse_args()
    result = analyze_terminal_scope(
        args.v79_contract.read_bytes(), args.v80_binding.read_bytes(), args.v80_receipt.read_bytes()
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
