"""Fail-closed synthetic evidence adapter for C6 shared+query composite.

This extends target-discovery evidence consumption without mutating the frozen C1-C5
crosswalk. It does not generate synthetic worlds, fit models, or grant target authority.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class C6SyntheticExtensionError(ValueError):
    pass


SCHEMA = "JEPA_TD_V79_C6_SYNTHETIC_EXTENSION_V1"
RECEIPT_SCHEMA = "JEPA_TD_V79_C6_SYNTHETIC_EVIDENCE_RECEIPT_V1"
CANDIDATE_ID = "C6_SHARED_QUERY_COMPOSITE"
BASE_SCHEMA = "JEPA_TD_V79_SYNTHETIC_CROSSWALK_V1"
EXPECTED_CONTRACT_SHA256 = "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26"
EXACT_WORLDS = (
    "Q00_BASELINE", "Q01_WEAK_DONOR", "Q02_STRONG_DONOR", "Q03_WEAK_SOURCE",
    "Q04_SOURCE_ABSENT", "Q05_CLASS_ABSENT", "Q06_QUADRATIC_DEPTH_ABSENT",
    "Q07_DONOR_ABSENT", "Q08_SPARSE_DETECTION", "Q09_POSITIVE_TAIL",
    "Q10_S174_DESIGN_IMBALANCE", "Q11_OMITTED_OPERATOR",
)
EVIDENCE_CLASSES = frozenset({"DECISIVE_POSITIVE", "DECISIVE_NEGATIVE", "DIAGNOSTIC", "NOT_ESTIMABLE"})
SYNTHETIC_STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})
REAL_STATUS = frozenset({"PASS", "FAIL", "NOT_ESTIMABLE"})
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
TOP_FIELDS = frozenset({
    "schema", "status", "candidate_id", "base_crosswalk_schema", "synthetic_contract_sha256", "claims", "authority"
})
CLAIM_FIELDS = frozenset({"claim", "worlds", "evidence_class", "required_truth_fields", "expected_behavior"})
RECEIPT_FIELDS = frozenset({
    "schema", "candidate_id", "registry_sha256", "synthetic_contract_sha256", "claim_results", "authority"
})
RESULT_FIELDS = frozenset({"claim", "evidence_class", "status", "world_evidence"})
WORLD_EVIDENCE_FIELDS = frozenset({"world", "truth_manifest_sha256", "result_sha256"})
MANDATORY_NE = "C6_INCREMENT_OVER_C1_C3_BIOLOGICAL_TRUTH"


def canonical_sha256(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_registry(path: Path | str) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise C6SyntheticExtensionError(f"invalid C6 synthetic registry: {exc}") from exc
    if not isinstance(value, dict):
        raise C6SyntheticExtensionError("C6 synthetic registry must be an object")
    return value


def _sha256_text(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _unique_strings(values, label: str, *, allow_empty=False):
    if not isinstance(values, list) or (not allow_empty and not values):
        raise C6SyntheticExtensionError(f"{label} must be {'a list' if allow_empty else 'a nonempty list'}")
    if any(not isinstance(v, str) or not v for v in values) or len(values) != len(set(values)):
        raise C6SyntheticExtensionError(f"{label} must contain unique nonempty strings")


def validate_registry(registry: dict) -> None:
    if not isinstance(registry, dict) or set(registry) != TOP_FIELDS:
        raise C6SyntheticExtensionError("C6 registry fields differ from frozen V1 extension schema")
    if registry["schema"] != SCHEMA or registry["candidate_id"] != CANDIDATE_ID:
        raise C6SyntheticExtensionError("wrong C6 extension schema/candidate")
    if registry["base_crosswalk_schema"] != BASE_SCHEMA:
        raise C6SyntheticExtensionError("wrong frozen base crosswalk schema")
    if registry["synthetic_contract_sha256"] != EXPECTED_CONTRACT_SHA256:
        raise C6SyntheticExtensionError("wrong canonical V79 contract SHA-256")
    authority = registry["authority"]
    if not isinstance(authority, dict) or set(authority) != AUTHORITY_KEYS or any(v is not False for v in authority.values()):
        raise C6SyntheticExtensionError("C6 extension cannot carry execution or selection authority")
    claims = registry["claims"]
    if not isinstance(claims, list) or not claims:
        raise C6SyntheticExtensionError("C6 extension requires frozen claims")
    seen = set()
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != CLAIM_FIELDS:
            raise C6SyntheticExtensionError("C6 claim fields differ from frozen schema")
        cid = claim["claim"]
        if not isinstance(cid, str) or not cid or cid in seen:
            raise C6SyntheticExtensionError("C6 claim identifiers must be unique nonempty strings")
        seen.add(cid)
        cls = claim["evidence_class"]
        if cls not in EVIDENCE_CLASSES:
            raise C6SyntheticExtensionError(f"invalid evidence class: {cid}")
        _unique_strings(claim["worlds"], f"worlds for {cid}", allow_empty=True)
        _unique_strings(claim["required_truth_fields"], f"truth fields for {cid}", allow_empty=True)
        if any(w not in EXACT_WORLDS for w in claim["worlds"]):
            raise C6SyntheticExtensionError(f"unknown V79 world in {cid}")
        if not isinstance(claim["expected_behavior"], str) or not claim["expected_behavior"]:
            raise C6SyntheticExtensionError(f"missing expected behavior: {cid}")
        if cls.startswith("DECISIVE") and (not claim["worlds"] or not claim["required_truth_fields"]):
            raise C6SyntheticExtensionError(f"decisive C6 claim lacks explicit world/truth binding: {cid}")
        if cls == "NOT_ESTIMABLE" and (claim["worlds"] or claim["required_truth_fields"]):
            raise C6SyntheticExtensionError(f"NOT_ESTIMABLE C6 claim cannot pretend to have current truth: {cid}")
    ne = [c for c in claims if c["claim"] == MANDATORY_NE]
    if len(ne) != 1 or ne[0]["evidence_class"] != "NOT_ESTIMABLE":
        raise C6SyntheticExtensionError("C6 biological increment must remain NOT_ESTIMABLE in current V79")


def validate_receipt(receipt: dict, registry: dict) -> None:
    validate_registry(registry)
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_FIELDS:
        raise C6SyntheticExtensionError("C6 receipt fields differ from frozen receipt schema")
    if receipt["schema"] != RECEIPT_SCHEMA or receipt["candidate_id"] != CANDIDATE_ID:
        raise C6SyntheticExtensionError("receipt is not a C6-specific evidence object")
    if receipt["registry_sha256"] != canonical_sha256(registry):
        raise C6SyntheticExtensionError("receipt is not bound to the exact C6 registry")
    if receipt["synthetic_contract_sha256"] != EXPECTED_CONTRACT_SHA256:
        raise C6SyntheticExtensionError("receipt is not bound to the canonical V79 contract")
    authority = receipt["authority"]
    if not isinstance(authority, dict) or set(authority) != AUTHORITY_KEYS or any(v is not False for v in authority.values()):
        raise C6SyntheticExtensionError("C6 receipt cannot carry execution or target authority")

    expected = {c["claim"]: c for c in registry["claims"]}
    results = receipt["claim_results"]
    if not isinstance(results, list) or len(results) != len(expected):
        raise C6SyntheticExtensionError("C6 receipt must contain the complete frozen claim set")
    seen = set()
    for result in results:
        if not isinstance(result, dict) or set(result) != RESULT_FIELDS:
            raise C6SyntheticExtensionError("invalid C6 receipt claim-result fields")
        cid = result["claim"]
        if cid not in expected or cid in seen:
            raise C6SyntheticExtensionError("missing/duplicate/foreign C6 receipt claim")
        seen.add(cid)
        frozen = expected[cid]
        if result["evidence_class"] != frozen["evidence_class"]:
            raise C6SyntheticExtensionError(f"C6 evidence class drift: {cid}")
        if result["status"] not in SYNTHETIC_STATUS:
            raise C6SyntheticExtensionError(f"invalid C6 synthetic status: {cid}")
        evidence = result["world_evidence"]
        if not isinstance(evidence, list):
            raise C6SyntheticExtensionError(f"world evidence must be a list: {cid}")
        if frozen["evidence_class"] == "NOT_ESTIMABLE":
            if result["status"] != "NOT_ESTIMABLE" or evidence:
                raise C6SyntheticExtensionError(f"current-V79 NOT_ESTIMABLE claim cannot carry fake evidence: {cid}")
            continue
        if result["status"] == "NOT_ESTIMABLE":
            if evidence:
                raise C6SyntheticExtensionError(f"NOT_ESTIMABLE result cannot carry world evidence: {cid}")
            continue
        if len(evidence) != len(frozen["worlds"]):
            raise C6SyntheticExtensionError(f"C6 receipt must bind every frozen world exactly once: {cid}")
        worlds = []
        for item in evidence:
            if not isinstance(item, dict) or set(item) != WORLD_EVIDENCE_FIELDS:
                raise C6SyntheticExtensionError(f"invalid world evidence object: {cid}")
            if not _sha256_text(item["truth_manifest_sha256"]) or not _sha256_text(item["result_sha256"]):
                raise C6SyntheticExtensionError(f"world evidence requires SHA-256 bindings: {cid}")
            worlds.append(item["world"])
        if worlds != frozen["worlds"]:
            raise C6SyntheticExtensionError(f"C6 receipt world order/set differs from frozen claim: {cid}")
    if seen != set(expected):
        raise C6SyntheticExtensionError("C6 receipt claim set is incomplete")


def combine(real_status: str, receipt: dict, registry: dict) -> str:
    validate_receipt(receipt, registry)
    if real_status not in REAL_STATUS:
        raise C6SyntheticExtensionError(f"invalid real C6 status: {real_status!r}")
    if real_status == "FAIL":
        return "ELIMINATED_REAL_FAIL"
    if real_status == "NOT_ESTIMABLE":
        return "UNRESOLVED_REAL_NOT_ESTIMABLE"
    if any(
        result["status"] == "FAIL" and result["evidence_class"] in {"DECISIVE_POSITIVE", "DECISIVE_NEGATIVE"}
        for result in receipt["claim_results"]
    ):
        return "ELIMINATED_SYNTHETIC_FALSIFIER"
    return "ELIGIBLE_PENDING_TARGET_SELECTION"
