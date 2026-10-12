#!/usr/bin/env python3
"""Launch-authority gate for V2_CORE synthetic qualification (PR #288 controller ruling 6114753697).

Every V2_CORE world generator, benchmark and qualification runner must obtain its contract through
require_launch_authority(). Only the final immutable V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json is accepted:
- its bytes must hash to FINAL_CONTRACT_SHA256 (pinned here) and to its own .sha256 file;
- its content must pass validate_launch_semantics();
- when a repository root is given, every evidence file it binds must hash to the recorded value.

The historical V1 contract and the V2 draft are refused by name, by hash and by content. This module is the single
authority for the controller-accepted values the gate checks. The contract builder imports them and fails closed if
its inputs or its own arithmetic disagree with them.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FINAL_CONTRACT_NAME = "V79_V2_CORE_QUALIFICATION_CONTRACT_V2.json"
FINAL_CONTRACT_SHA256 = "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
FINAL_STATUS = "FROZEN_PROSPECTIVE_LAUNCH_AUTHORITY__NO_QUALIFICATION_FIT_RUN"
SCHEMA = "V79_V2_CORE_QUALIFICATION_CONTRACT_V2"
CONTROLLER_RULING = {"pr": 288, "comment_id": "6114753697"}
CONTROLLER_MODEL_DECISION = "FROZEN_UNCHANGED_AFTER_MASK_CORRECTED_S174_REPLAY"

# Controller-accepted evidence (PR #286 ruling 6113874774 and PR #288 rulings 6114694791 / 6114753697).
ACCEPTED_EVIDENCE = {
    "contract_v1": {"path": "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json",
                    "sha256": "70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540",
                    "status": "HISTORICAL_PRE_CONTROLLER_DRAFT__NOT_LAUNCH_AUTHORITY"},
    "contract_v2_draft": {"path": "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json",
                          "sha256": "cbfa332b419f12205d26b7f1ebd645299acb9ecc7f1ed8cdccc526ebf88477b3",
                          "status": "PENDING_CONTROLLER_ACCEPTANCE__NO_WORLD_GENERATION"},
    "masked_replay": {"sha256": "caf2413cdd4f9a616be84fe3fb976cf40c496df0732530cbf9775659361e4683"},
    "masking_audit": {"sha256": "6bd0bfc7534635204c24691e754d335df7c586104a126f1d0e6d84583029ad41"},
    "support_mask": {"measured_op_gene_sha256": "12ad275ef5e1ca094ab82cbcd871e29a6e1f7648cad4cebb57ae234042b74fab",
                     "npz_sha256": "6203fb2c5008c71e5275a3cec7e85d52e041787a058149efbf27f15c591a1017",
                     "record_sha256": "a6023902d953f98fb0fbd2a22d53361627f9b6a299c8730ef2ba7b9776a9f286"},
    "g500_cache": {"sha256": "2f922c08e38c104ed7149a2ee74a5e3adc8c287ef5b5c07ea1b5b862f92a6a62",
                   "receipt_sha256": "3a5ed9ef40e849ab9aa78b324cbca406772f412e1844fd327e12d04507587351"},
    "structural_support_authority": {
        "path": "results/v4/stage81a2r_foundation_molecular_address_measurement_support_candidate.csv.gz",
        "commit": "95d2cafe5cde68773f81c4aa64afc5788ae1d73b",
        "sha256": "ee5d12c144536efdacb983f6b9aa2acb46d47d395b2aa9c556ad10b191f3cdaa"},
    "s174_operator_bridge": {"path": "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json",
                             "sha256": "b83c35e6940734a7756627d91e3ce982cb4062e9cdeb2fd6035a090abdface92"},
    "planting_calibration_masked": {"sha256": "49379ee09fcf7496919e570f83710ee772ca407ca0d20268a9af1f4e132f533c"},
    "s174_design_only": {"sha256": "10e3c472543d948d673d91f7dadd15dbd77809a7b0d15f528eb9fd38d0c85a62"},
    "s174_design_only_record": {"sha256": "1a1295c34157b2d8629732a36cf1fe6592f6181872b41bd7d19151092b413fbb"},
    "structural_support_dev": {"sha256": "d70781af34ec5263d515ee1ad7f9410b426a6516cd7a7d46e0a69c32ae6f41c2"},
    "env_lock": {"sha256": "5253ddca79c5f1b11eff2432b39679f16a68a885486a333d244357452261c782"},
}
# Contract input key -> accepted-evidence key, for every input the builder hashes.
INPUT_EVIDENCE = {
    "s174_design_only": ("s174_design_only", "sha256"),
    "s174_design_only_record": ("s174_design_only_record", "sha256"),
    "planting_calibration_masked": ("planting_calibration_masked", "sha256"),
    "structural_support_dev": ("structural_support_dev", "sha256"),
    "structural_support_v1_record": ("support_mask", "record_sha256"),
    "masked_replay": ("masked_replay", "sha256"),
    "masking_audit": ("masking_audit", "sha256"),
    "env_lock": ("env_lock", "sha256"),
}
ACCEPTED_ARITHMETIC = {"worlds": 12, "genes_per_world": 44, "n_fits": 1056, "total_gates": 292,
                       "hard_statistical": 260, "hard_rule": 28, "limit_statistical": 4, "limit_rule": 0,
                       "familywise_false_fail": 0.05, "alpha_per_gate": 0.05 / 260}
APPROVED_LIMIT_GATES = frozenset({("Q01_WEAK_DONOR", "detection", "BIAS_DONOR_SD"),
                                  ("Q01_WEAK_DONOR", "positive", "BIAS_DONOR_SD"),
                                  ("Q08_SPARSE_DETECTION", "positive", "BIAS_DONOR_SD"),
                                  ("Q09_POSITIVE_TAIL", "positive", "BIAS_DONOR_SD")})
POST_TERMINAL_LABEL = "POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION"
Q11 = "Q11_OMITTED_OPERATOR"


class LaunchAuthorityRefused(Exception):
    """The contract offered is not the controller-accepted launch authority."""


def _refuse(why: str):
    raise LaunchAuthorityRefused(f"REFUSED as V2_CORE launch authority: {why}")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_launch_semantics(c: dict) -> dict:
    """Content checks, independent of any file hash."""
    if not isinstance(c, dict):
        _refuse("not a JSON object")
    if c.get("schema") != SCHEMA:
        _refuse(f"schema {c.get('schema')!r}")
    if c.get("status") != FINAL_STATUS:
        _refuse(f"status {c.get('status')!r} is not {FINAL_STATUS}")
    if c.get("launch_authority") is not True:
        _refuse("launch_authority is not true")
    if c.get("controller_ruling", {}).get("pr") != CONTROLLER_RULING["pr"] or \
            c.get("controller_ruling", {}).get("comment_id") != CONTROLLER_RULING["comment_id"]:
        _refuse("controller ruling binding differs")
    if c.get("controller_model_decision") != CONTROLLER_MODEL_DECISION:
        _refuse("controller model decision differs")
    if c.get("qualification_worlds_generated") != 0 or c.get("qualification_fits_run") != 0:
        _refuse("contract does not record a pre-generation state")
    if c.get("boundaries", {}).get("training_authorized") is not False:
        _refuse("training_authorized is not false")
    ev = c.get("accepted_evidence", {})
    for key, want in ACCEPTED_EVIDENCE.items():
        got = ev.get(key, {})
        for field, value in want.items():
            if got.get(field) != value:
                _refuse(f"accepted evidence {key}.{field} differs")
    for ikey, (ekey, field) in INPUT_EVIDENCE.items():
        if c.get("inputs", {}).get(ikey, {}).get("sha256") != ACCEPTED_EVIDENCE[ekey][field]:
            _refuse(f"input {ikey} hash differs from accepted evidence")
    a = ACCEPTED_ARITHMETIC
    m = c.get("gates", {}).get("multiplicity", {})
    counts = m.get("gate_counts", {})
    gates = c.get("gates", {}).get("list", [])
    checks = {
        "worlds": len(c.get("worlds", {}).get("world_list", [])),
        "genes_per_world": c.get("worlds", {}).get("genes_per_world"),
        "n_fits": c.get("resources", {}).get("estimate", {}).get("n_fits"),
        "total_gates": len(gates),
        "hard_statistical": counts.get("hard_statistical"), "hard_rule": counts.get("hard_rule"),
        "limit_statistical": counts.get("limit_statistical"), "limit_rule": counts.get("limit_rule"),
        "familywise_false_fail": m.get("familywise_false_fail"), "alpha_per_gate": m.get("alpha_per_gate"),
    }
    for k, v in checks.items():
        if v != a[k]:
            _refuse(f"{k} = {v!r}, accepted {a[k]!r}")
    observed = {"hard_statistical": sum(g["kind"] == "STAT" and g["verdict_class"] == "FAIL" for g in gates),
                "hard_rule": sum(g["kind"] == "RULE" and g["verdict_class"] == "FAIL" for g in gates),
                "limit_statistical": sum(g["kind"] == "STAT" and g["verdict_class"] == "LIMIT" for g in gates),
                "limit_rule": sum(g["kind"] == "RULE" and g["verdict_class"] == "LIMIT" for g in gates)}
    if any(observed[k] != a[k] for k in observed):
        _refuse(f"gate list does not reproduce the accepted counts: {observed}")
    limit = {(g["world"], g["part"], g["gate"]) for g in gates if g["verdict_class"] == "LIMIT"}
    if limit != APPROVED_LIMIT_GATES:
        _refuse(f"LIMIT gates differ from the four approved donor-SD bias gates: {sorted(limit)}")
    if any(g["verdict_class"] != "FAIL" for g in gates if g["world"] == Q11):
        _refuse("a Q11 gate is not hard FAIL")
    t = c.get("terminal_logic", {})
    if "terminal_lock" not in t or t.get("post_terminal_label") != POST_TERMINAL_LABEL:
        _refuse("first-FAIL terminal lock is missing")
    return c


def require_launch_authority(path, root=None) -> dict:
    """Return the contract only if it is the controller-accepted final V2 launch authority."""
    path = Path(path)
    if path.name != FINAL_CONTRACT_NAME:
        _refuse(f"{path.name} is not {FINAL_CONTRACT_NAME}")
    if not path.is_file():
        _refuse(f"missing {path}")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != FINAL_CONTRACT_SHA256:
        _refuse(f"contract bytes hash {digest}, accepted {FINAL_CONTRACT_SHA256}")
    side = path.with_suffix(".sha256")
    if not side.is_file() or side.read_text(encoding="utf-8").split()[:1] != [digest]:
        _refuse("the .sha256 file does not match the contract bytes")
    c = validate_launch_semantics(json.loads(raw.decode("utf-8")))
    if root is not None:
        root = Path(root)
        for key, spec in c["inputs"].items():
            if _sha(root / spec["path"]) != spec["sha256"]:
                _refuse(f"evidence file {spec['path']} differs from its bound hash")
    return c
