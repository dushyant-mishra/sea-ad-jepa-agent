"""Fail-closed target-discovery adapter for the separate V79 synthetic lane.

This module creates no biological, target-selection, representation-selection,
TD60, Stage4, training, corrected-replay, synthetic-world-generation, or
synthetic-qualification authority.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class CrosswalkError(ValueError):
    pass


EXACT_WORLDS = (
    "Q00_BASELINE",
    "Q01_WEAK_DONOR",
    "Q02_STRONG_DONOR",
    "Q03_WEAK_SOURCE",
    "Q04_SOURCE_ABSENT",
    "Q05_CLASS_ABSENT",
    "Q06_QUADRATIC_DEPTH_ABSENT",
    "Q07_DONOR_ABSENT",
    "Q08_SPARSE_DETECTION",
    "Q09_POSITIVE_TAIL",
    "Q10_S174_DESIGN_IMBALANCE",
    "Q11_OMITTED_OPERATOR",
)
EXACT_CANDIDATES = (
    "C1_SHARED_EMERGENT",
    "C2_RELATIONAL_SHARED",
    "C3_QUERY_MEASURED",
    "C4_STRUCTURED_COMPOSITE",
    "C5_REGULATORY_SPECIALIST",
)
FOUNDATION_CANDIDATES = EXACT_CANDIDATES[:4]
SPECIALIST_CANDIDATES = EXACT_CANDIDATES[4:]
EVIDENCE_CLASSES = (
    "DECISIVE_POSITIVE",
    "DECISIVE_NEGATIVE",
    "DIAGNOSTIC",
    "NOT_ESTIMABLE",
)
REAL_STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})
SYNTHETIC_STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})
ELIGIBLE = "ELIGIBLE_PENDING_TARGET_SELECTION"

EXPECTED_SCHEMA = "JEPA_TD_V79_SYNTHETIC_CROSSWALK_V1"
EVIDENCE_RECEIPT_SCHEMA = "JEPA_TD_V79_SYNTHETIC_EVIDENCE_RECEIPT_V1"
EXPECTED_CONTRACT_SHA256 = "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
EXPECTED_PAIR = ["Q10_S174_DESIGN_IMBALANCE", "Q11_OMITTED_OPERATOR"]
AUTHORITY_KEYS = frozenset({
    "synthetic_world_generation_authorized",
    "synthetic_qualification_fitting_authorized",
    "corrected_biological_replay_authorized",
    "target_selection_authorized",
    "representation_selection_authorized",
    "td60_authorized",
    "stage4_authorized",
    "training_authorized",
})
TOP_LEVEL_FIELDS = frozenset({
    "schema",
    "status",
    "source_design_commit",
    "synthetic_contract_sha256",
    "generator_head_at_freeze",
    "evidence_classes",
    "worlds",
    "candidates",
    "paired_counterfactual",
    "new_donor_rule",
    "claims",
    "authority",
})
CLAIM_FIELDS = frozenset({
    "candidate",
    "claim",
    "worlds",
    "evidence_class",
    "target_gates",
    "required_truth_fields",
    "expected_behavior",
    "failure_effect",
})
RECEIPT_FIELDS = frozenset({
    "schema",
    "candidate_id",
    "crosswalk_sha256",
    "synthetic_contract_sha256",
    "claim_results",
    "authority",
})
CLAIM_RESULT_FIELDS = frozenset({"claim", "evidence_class", "status", "world_evidence"})
WORLD_EVIDENCE_FIELDS = frozenset({"world", "truth_manifest_sha256", "result_sha256"})
MANDATORY_NOT_ESTIMABLE = {
    ("C1_SHARED_EMERGENT", "SHARED_MULTIGENE_LATENT_RECOVERY"),
    ("C2_RELATIONAL_SHARED", "RELATIONAL_GEOMETRY_RECOVERY"),
    ("C3_QUERY_MEASURED", "QUERY_CONDITIONED_BIOLOGICAL_RECOVERY"),
    ("C4_STRUCTURED_COMPOSITE", "INCREMENT_OVER_CONSTITUENTS_BIOLOGICAL_TRUTH"),
    ("C5_REGULATORY_SPECIALIST", "REGULATORY_CHROMATIN_RECOVERY"),
}


def canonical_sha256(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def load_crosswalk(path: Path | str) -> dict:
    path = Path(path)
    if not path.is_file():
        raise CrosswalkError(f"crosswalk registry missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CrosswalkError(f"invalid crosswalk JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CrosswalkError("crosswalk top level must be an object")
    return value


def _require_unique_strings(values, label: str, *, allow_empty: bool = False) -> None:
    if not isinstance(values, list):
        raise CrosswalkError(f"{label} must be a list")
    if not allow_empty and not values:
        raise CrosswalkError(f"{label} must be nonempty")
    if any(not isinstance(v, str) or not v for v in values):
        raise CrosswalkError(f"{label} must contain nonempty strings")
    if len(values) != len(set(values)):
        raise CrosswalkError(f"{label} must contain unique strings")


def _validate_authority(authority, label: str) -> None:
    if not isinstance(authority, dict) or set(authority) != AUTHORITY_KEYS:
        raise CrosswalkError(f"{label} authority keys must exactly match V1 boundary")
    if any(value is not False for value in authority.values()):
        raise CrosswalkError(f"{label} cannot carry execution or selection authority")


def validate_crosswalk(crosswalk: dict) -> None:
    if not isinstance(crosswalk, dict) or set(crosswalk) != TOP_LEVEL_FIELDS:
        raise CrosswalkError("crosswalk fields must exactly match V1 schema")
    if crosswalk.get("schema") != EXPECTED_SCHEMA:
        raise CrosswalkError("wrong crosswalk schema")
    if crosswalk.get("synthetic_contract_sha256") != EXPECTED_CONTRACT_SHA256:
        raise CrosswalkError("wrong canonical V79 Contract V2 SHA-256")
    if not isinstance(crosswalk.get("source_design_commit"), str) or len(crosswalk["source_design_commit"]) != 40:
        raise CrosswalkError("source design commit must be a 40-character git SHA")
    if not isinstance(crosswalk.get("generator_head_at_freeze"), str) or len(crosswalk["generator_head_at_freeze"]) != 40:
        raise CrosswalkError("generator head at freeze must be a 40-character git SHA")

    if tuple(crosswalk.get("evidence_classes", ())) != EVIDENCE_CLASSES:
        raise CrosswalkError("evidence-class registry differs from frozen V1 order")
    worlds = crosswalk.get("worlds")
    if not isinstance(worlds, dict) or tuple(worlds) != EXACT_WORLDS:
        raise CrosswalkError("world registry must be exactly Q00-Q11 in frozen order")
    for index, world in enumerate(EXACT_WORLDS):
        rec = worlds[world]
        if not isinstance(rec, dict) or set(rec) != {"index", "perturbation"}:
            raise CrosswalkError(f"invalid world record: {world}")
        if rec.get("index") != index or not isinstance(rec.get("perturbation"), str) or not rec["perturbation"]:
            raise CrosswalkError(f"world index/perturbation mismatch: {world}")

    candidates = crosswalk.get("candidates")
    if not isinstance(candidates, dict) or tuple(candidates) != EXACT_CANDIDATES:
        raise CrosswalkError("candidate registry must be exactly C1-C5 in frozen order")
    for cid in EXACT_CANDIDATES:
        rec = candidates[cid]
        if not isinstance(rec, dict) or set(rec) != {"foundation"} or not isinstance(rec["foundation"], bool):
            raise CrosswalkError(f"invalid candidate record: {cid}")
        if rec["foundation"] is not (cid in FOUNDATION_CANDIDATES):
            raise CrosswalkError(f"candidate foundation role mismatch: {cid}")

    _validate_authority(crosswalk.get("authority"), "synthetic crosswalk")

    pair = crosswalk.get("paired_counterfactual")
    required_pair_fields = {
        "worlds",
        "non_operator_truth_identical_required",
        "operator_perturbation_is_designated_difference",
        "single_world_operator_invariance_allowed",
        "collapse_cannot_satisfy_invariance",
    }
    if not isinstance(pair, dict) or set(pair) != required_pair_fields:
        raise CrosswalkError("invalid Q10/Q11 paired-counterfactual record")
    if pair.get("worlds") != EXPECTED_PAIR:
        raise CrosswalkError("Q10/Q11 paired-counterfactual worlds must remain canonical")
    if pair.get("non_operator_truth_identical_required") is not True:
        raise CrosswalkError("Q10/Q11 requires identical non-operator truth")
    if pair.get("operator_perturbation_is_designated_difference") is not True:
        raise CrosswalkError("Q10/Q11 requires operator perturbation as designated difference")
    if pair.get("single_world_operator_invariance_allowed") is not False:
        raise CrosswalkError("single-world operator invariance is forbidden")
    if pair.get("collapse_cannot_satisfy_invariance") is not True:
        raise CrosswalkError("collapse cannot satisfy operator invariance")

    new_donor = crosswalk.get("new_donor_rule")
    if not isinstance(new_donor, dict) or set(new_donor) != {
        "training_donor_identity_overlap_allowed",
        "fixed_non_donor_truth_binding_required",
        "new_donor_realization_required",
    }:
        raise CrosswalkError("invalid new-donor rule")
    if new_donor["training_donor_identity_overlap_allowed"] is not False:
        raise CrosswalkError("new-donor transfer cannot reuse training donor identities")
    if new_donor["fixed_non_donor_truth_binding_required"] is not True or new_donor["new_donor_realization_required"] is not True:
        raise CrosswalkError("new-donor transfer requires fixed truth binding and a new realization")

    claims = crosswalk.get("claims")
    if not isinstance(claims, list) or not claims:
        raise CrosswalkError("claims must be a nonempty list")
    seen = set()
    for rec in claims:
        if not isinstance(rec, dict) or set(rec) != CLAIM_FIELDS:
            raise CrosswalkError("claim fields must exactly match V1 schema")
        cid = rec.get("candidate")
        claim = rec.get("claim")
        evidence_class = rec.get("evidence_class")
        if cid not in EXACT_CANDIDATES:
            raise CrosswalkError(f"unknown claim candidate: {cid}")
        if not isinstance(claim, str) or not claim:
            raise CrosswalkError("claim identifier must be nonempty")
        key = (cid, claim)
        if key in seen:
            raise CrosswalkError(f"duplicate candidate claim: {key}")
        seen.add(key)
        if evidence_class not in EVIDENCE_CLASSES:
            raise CrosswalkError(f"invalid evidence class: {key}")
        _require_unique_strings(rec.get("worlds"), f"claim worlds {key}", allow_empty=True)
        if any(world not in EXACT_WORLDS for world in rec["worlds"]):
            raise CrosswalkError(f"claim references unknown world: {key}")
        _require_unique_strings(rec.get("target_gates"), f"target gates {key}")
        _require_unique_strings(rec.get("required_truth_fields"), f"truth fields {key}", allow_empty=True)
        if not isinstance(rec.get("expected_behavior"), str) or not rec["expected_behavior"]:
            raise CrosswalkError(f"expected behavior missing: {key}")
        if not isinstance(rec.get("failure_effect"), str) or not rec["failure_effect"]:
            raise CrosswalkError(f"failure effect missing: {key}")
        if evidence_class.startswith("DECISIVE"):
            if not rec["worlds"] or not rec["required_truth_fields"]:
                raise CrosswalkError(f"decisive claim requires explicit world and truth binding: {key}")
        if evidence_class == "NOT_ESTIMABLE":
            if rec["worlds"] or rec["required_truth_fields"]:
                raise CrosswalkError(f"NOT_ESTIMABLE claim cannot pretend to have current V79 truth: {key}")
            if rec["failure_effect"] != "NO_SYNTHETIC_VERDICT":
                raise CrosswalkError(f"NOT_ESTIMABLE claim cannot create a synthetic verdict: {key}")

    for key in MANDATORY_NOT_ESTIMABLE:
        rec = next((item for item in claims if (item["candidate"], item["claim"]) == key), None)
        if rec is None or rec["evidence_class"] != "NOT_ESTIMABLE":
            raise CrosswalkError(f"mandatory current-V79 NOT_ESTIMABLE claim missing: {key}")


def validate_synthetic_evidence_receipt(receipt: dict, crosswalk: dict) -> dict:
    """Authenticate one candidate's complete frozen V79 claim set before combination."""
    validate_crosswalk(crosswalk)
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_FIELDS:
        raise CrosswalkError("synthetic evidence receipt fields must exactly match V1 schema")
    if receipt.get("schema") != EVIDENCE_RECEIPT_SCHEMA:
        raise CrosswalkError("wrong synthetic evidence receipt schema")
    candidate_id = receipt.get("candidate_id")
    if candidate_id not in EXACT_CANDIDATES:
        raise CrosswalkError("unknown synthetic evidence receipt candidate")
    if receipt.get("crosswalk_sha256") != canonical_sha256(crosswalk):
        raise CrosswalkError("synthetic evidence receipt crosswalk binding mismatch")
    if receipt.get("synthetic_contract_sha256") != EXPECTED_CONTRACT_SHA256:
        raise CrosswalkError("synthetic evidence receipt V79 contract binding mismatch")
    _validate_authority(receipt.get("authority"), "synthetic evidence receipt")

    frozen = [entry for entry in crosswalk["claims"] if entry["candidate"] == candidate_id]
    expected_by_claim = {entry["claim"]: entry for entry in frozen}
    results = receipt.get("claim_results")
    if not isinstance(results, list) or len(results) != len(frozen):
        raise CrosswalkError("synthetic evidence receipt must contain the complete frozen candidate claim set")
    if [record.get("claim") if isinstance(record, dict) else None for record in results] != [entry["claim"] for entry in frozen]:
        raise CrosswalkError("synthetic evidence receipt claim order/set differs from frozen crosswalk")

    for record in results:
        if not isinstance(record, dict) or set(record) != CLAIM_RESULT_FIELDS:
            raise CrosswalkError("invalid synthetic claim-result shape")
        claim = record["claim"]
        frozen_entry = expected_by_claim[claim]
        if record.get("evidence_class") != frozen_entry["evidence_class"]:
            raise CrosswalkError(f"synthetic evidence class differs from frozen crosswalk: {claim}")
        status = record.get("status")
        if status not in SYNTHETIC_STATUS:
            raise CrosswalkError(f"invalid synthetic claim status: {claim}")
        world_evidence = record.get("world_evidence")
        if not isinstance(world_evidence, list):
            raise CrosswalkError(f"world_evidence must be a list: {claim}")

        if frozen_entry["evidence_class"] == "NOT_ESTIMABLE":
            if status != "NOT_ESTIMABLE" or world_evidence:
                raise CrosswalkError(f"current-V79 NOT_ESTIMABLE claim cannot carry PASS/FAIL evidence: {claim}")
            continue

        if status == "NOT_ESTIMABLE":
            if world_evidence:
                raise CrosswalkError(f"NOT_ESTIMABLE result cannot carry world evidence: {claim}")
            continue

        expected_worlds = frozen_entry["worlds"]
        if [item.get("world") if isinstance(item, dict) else None for item in world_evidence] != expected_worlds:
            raise CrosswalkError(f"world evidence must exactly match frozen worlds: {claim}")
        for item in world_evidence:
            if not isinstance(item, dict) or set(item) != WORLD_EVIDENCE_FIELDS:
                raise CrosswalkError(f"invalid world evidence shape: {claim}")
            if item["world"] not in EXACT_WORLDS:
                raise CrosswalkError(f"unknown world evidence: {claim}")
            if not _is_sha256(item["truth_manifest_sha256"]):
                raise CrosswalkError(f"invalid truth-manifest SHA-256: {claim}")
            if not _is_sha256(item["result_sha256"]):
                raise CrosswalkError(f"invalid synthetic-result SHA-256: {claim}")
    return receipt


def combine_candidate_evidence(
    candidate_id: str,
    real_status: str,
    synthetic_results: list[dict],
    crosswalk: dict,
) -> str:
    """Combine real and synthetic evidence asymmetrically without granting target authority."""
    validate_crosswalk(crosswalk)
    if candidate_id not in EXACT_CANDIDATES:
        raise CrosswalkError(f"unknown candidate: {candidate_id}")
    if real_status not in REAL_STATUS:
        raise CrosswalkError(f"invalid real status: {real_status}")
    if not isinstance(synthetic_results, list):
        raise CrosswalkError("synthetic_results must be a list")
    for record in synthetic_results:
        if not isinstance(record, dict) or set(record) != {"evidence_class", "status"}:
            raise CrosswalkError("synthetic result must contain exactly evidence_class/status")
        if record["evidence_class"] not in EVIDENCE_CLASSES:
            raise CrosswalkError("invalid synthetic evidence class")
        if record["status"] not in SYNTHETIC_STATUS:
            raise CrosswalkError("invalid synthetic status")

    if real_status == "FAIL":
        return "ELIMINATED_REAL_FAIL"
    if real_status == "NOT_ESTIMABLE":
        return "UNRESOLVED_REAL_NOT_ESTIMABLE"

    if any(
        record["status"] == "FAIL"
        and record["evidence_class"] in {"DECISIVE_POSITIVE", "DECISIVE_NEGATIVE"}
        for record in synthetic_results
    ):
        return "ELIMINATED_SYNTHETIC_FALSIFIER"
    return ELIGIBLE


def combine_candidate_receipt(real_status: str, receipt: dict, crosswalk: dict) -> str:
    """Validate a complete synthetic receipt, then apply the asymmetric evidence rule."""
    validate_synthetic_evidence_receipt(receipt, crosswalk)
    synthetic_results = [
        {"evidence_class": record["evidence_class"], "status": record["status"]}
        for record in receipt["claim_results"]
    ]
    return combine_candidate_evidence(receipt["candidate_id"], real_status, synthetic_results, crosswalk)


def adjudicate_foundation(candidate_statuses: dict, specialist_status: str | None = None) -> dict:
    """Return a no-authority contingency terminal for the foundation candidates."""
    if not isinstance(candidate_statuses, dict) or set(candidate_statuses) != set(FOUNDATION_CANDIDATES):
        raise CrosswalkError("candidate_statuses must contain exactly the four foundation candidates")
    allowed = {
        ELIGIBLE,
        "ELIMINATED_REAL_FAIL",
        "UNRESOLVED_REAL_NOT_ESTIMABLE",
        "ELIMINATED_SYNTHETIC_FALSIFIER",
        "BLOCKED_BY_CONSTITUENT",
    }
    if any(status not in allowed for status in candidate_statuses.values()):
        raise CrosswalkError("invalid foundation candidate status")
    if specialist_status is not None and specialist_status not in allowed:
        raise CrosswalkError("invalid specialist status")

    statuses = dict(candidate_statuses)
    if statuses["C4_STRUCTURED_COMPOSITE"] == ELIGIBLE:
        if statuses["C2_RELATIONAL_SHARED"] != ELIGIBLE or statuses["C3_QUERY_MEASURED"] != ELIGIBLE:
            statuses["C4_STRUCTURED_COMPOSITE"] = "BLOCKED_BY_CONSTITUENT"

    eligible = [cid for cid in FOUNDATION_CANDIDATES if statuses[cid] == ELIGIBLE]
    if not eligible:
        terminal = "NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION"
    elif len(eligible) == 1:
        terminal = "SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY"
    else:
        terminal = "MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY"

    specialists = []
    if specialist_status == ELIGIBLE:
        specialists.append("C5_REGULATORY_SPECIALIST")

    return {
        "schema": "JEPA_TD_V79_SYNTHETIC_FOUNDATION_ADJUDICATION_V1",
        "candidate_statuses": statuses,
        "eligible_foundation_candidates": eligible,
        "optional_specialists_eligible": specialists,
        "terminal": terminal,
        "target_selected": False,
        "representation_selected": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }
