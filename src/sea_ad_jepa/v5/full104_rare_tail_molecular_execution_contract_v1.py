"""Execution contract for FULL104 rare-tail molecular prequalification V1.

Frozen before expression outcomes are opened. Binds the scientific molecular
authority to the exact executor/primitives and helper source identities.

The executor must report all 24 panel x source x fold cases even if one fails,
so a failure cannot hide later estimability diagnostics. PASS remains 24/24.
Any NOT_ESTIMABLE case dominates the full terminal.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Tuple

MOLECULAR_AUTHORITY_SHA256 = (
    "0b5629ca5e7087b1535e006021ec35d24a981986d5096eb4c99f001294c4c000"
)
STRUCTURAL_PREFLIGHT_SHA256 = (
    "f0d71c9b2f25d31a0b277b9a55f2a31f44d9084b924c3c14c67ef0c4c4a4bc89"
)
STRUCTURAL_PREFLIGHT_SOURCE_SHA = (
    "5503cd8c99506d172616b1e2edd8090eeaa41a05"
)
SAMPLE_RECEIPT_SHA256 = (
    "7220654284fe07c1abcf97a77d818700b46e3fe577fca4fd5bc4b99df6a4d6f6"
)
FULL104_MANIFEST_SHA256 = (
    "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
)
OUTER_SPLIT_RECEIPT_SHA256 = (
    "5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4"
)
TARGET_ELIGIBILITY_FILE_SHA256 = (
    "3723ec4a3fe0e2d0f5b07cc2c6c296bd956ad7d89877621d974eff7b00e7eb3e"
)

RUNNER_NORMALIZED_TEXT_SHA256 = (
    "d2d3b029de377adf9e3dc1f3f882f08ce0ec44be69a2718da34175aeb53f459a"
)
PRIMITIVES_NORMALIZED_TEXT_SHA256 = (
    "9219cf06260bef8f7d298e48cb977fb75791e0b2e75616ab47779a6c332c77cd"
)
AUTHORITY_SOURCE_NORMALIZED_TEXT_SHA256 = (
    "bd921546494ec5992fcf2b6f7bd9fba44aaef29d9688f1c9c6d60ed586f94837"
)
TAIL_SELECTOR_SOURCE_NORMALIZED_TEXT_SHA256 = (
    "8e053d4dc5817e9684fd4681e85ae66d49dffb83cf57eb45346edb41336fecd2"
)
SOURCE_LIBRARY_PARSER_SOURCE_NORMALIZED_TEXT_SHA256 = (
    "143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d"
)
SOURCE_HASH_NORMALIZATION = "UTF8_TEXT__CRLF_CR_TO_LF_V1"

ZERO_SLACK_STRUCTURAL_CASES: Tuple[Tuple[int, int], ...] = (
    (1, 1),
    (1, 2),
    (1, 3),
)
EXPECTED_ZERO_SLACK_DONORS = 4
REQUIRED_CASES = 24


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _git_commit_sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase 40-hex Git commit SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase 40-hex Git commit SHA") from exc
    return value


@dataclass(frozen=True)
class Full104RareTailMolecularExecutionContractV1:
    contract_id: str

    molecular_authority_sha256: str = MOLECULAR_AUTHORITY_SHA256
    structural_preflight_sha256: str = STRUCTURAL_PREFLIGHT_SHA256
    structural_preflight_source_sha: str = STRUCTURAL_PREFLIGHT_SOURCE_SHA
    sample_receipt_sha256: str = SAMPLE_RECEIPT_SHA256
    full104_manifest_sha256: str = FULL104_MANIFEST_SHA256
    outer_split_receipt_sha256: str = OUTER_SPLIT_RECEIPT_SHA256
    target_eligibility_file_sha256: str = TARGET_ELIGIBILITY_FILE_SHA256

    runner_normalized_text_sha256: str = RUNNER_NORMALIZED_TEXT_SHA256
    primitives_normalized_text_sha256: str = PRIMITIVES_NORMALIZED_TEXT_SHA256
    authority_source_normalized_text_sha256: str = (
        AUTHORITY_SOURCE_NORMALIZED_TEXT_SHA256
    )
    tail_selector_source_normalized_text_sha256: str = (
        TAIL_SELECTOR_SOURCE_NORMALIZED_TEXT_SHA256
    )
    source_library_parser_source_normalized_text_sha256: str = (
        SOURCE_LIBRARY_PARSER_SOURCE_NORMALIZED_TEXT_SHA256
    )
    source_hash_normalization: str = SOURCE_HASH_NORMALIZATION

    required_cases: int = REQUIRED_CASES
    zero_slack_structural_cases: Tuple[Tuple[int, int], ...] = (
        ZERO_SLACK_STRUCTURAL_CASES
    )
    expected_zero_slack_donors: int = EXPECTED_ZERO_SLACK_DONORS

    evaluate_all_24_cases_even_after_failure: bool = True
    not_estimable_dominates_full_terminal: bool = True
    post_outcome_tail_threshold_adaptation_allowed: bool = False
    alternate_q90_q99_rescue_allowed: bool = False

    molecular_execution_authorized: bool = True
    teacher_tail_evaluation_authorized: bool = False
    td60_authorized: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        if not isinstance(self.contract_id, str) or not self.contract_id.strip():
            raise ValueError("contract_id must be nonempty")
        expected_hashes = {
            "molecular_authority_sha256": MOLECULAR_AUTHORITY_SHA256,
            "structural_preflight_sha256": STRUCTURAL_PREFLIGHT_SHA256,
            "sample_receipt_sha256": SAMPLE_RECEIPT_SHA256,
            "full104_manifest_sha256": FULL104_MANIFEST_SHA256,
            "outer_split_receipt_sha256": OUTER_SPLIT_RECEIPT_SHA256,
            "target_eligibility_file_sha256": TARGET_ELIGIBILITY_FILE_SHA256,
            "runner_normalized_text_sha256": RUNNER_NORMALIZED_TEXT_SHA256,
            "primitives_normalized_text_sha256": PRIMITIVES_NORMALIZED_TEXT_SHA256,
            "authority_source_normalized_text_sha256":
                AUTHORITY_SOURCE_NORMALIZED_TEXT_SHA256,
            "tail_selector_source_normalized_text_sha256":
                TAIL_SELECTOR_SOURCE_NORMALIZED_TEXT_SHA256,
            "source_library_parser_source_normalized_text_sha256":
                SOURCE_LIBRARY_PARSER_SOURCE_NORMALIZED_TEXT_SHA256,
        }
        for name, expected in expected_hashes.items():
            if _sha(getattr(self, name), name) != expected:
                raise ValueError(f"{name} drifted from frozen molecular execution code")
        if (
            _git_commit_sha(
                self.structural_preflight_source_sha,
                "structural_preflight_source_sha",
            )
            != STRUCTURAL_PREFLIGHT_SOURCE_SHA
        ):
            raise ValueError("structural-preflight receipt commit drifted")
        if self.source_hash_normalization != SOURCE_HASH_NORMALIZATION:
            raise ValueError("source hash normalization drifted")
        if self.required_cases != REQUIRED_CASES:
            raise ValueError("required_cases must remain 24")
        if tuple(tuple(x) for x in self.zero_slack_structural_cases) != (
            ZERO_SLACK_STRUCTURAL_CASES
        ):
            raise ValueError("zero-slack NPH52 structural cases drifted")
        if self.expected_zero_slack_donors != EXPECTED_ZERO_SLACK_DONORS:
            raise ValueError("zero-slack donor count drifted")

        required_true = (
            "evaluate_all_24_cases_even_after_failure",
            "not_estimable_dominates_full_terminal",
            "molecular_execution_authorized",
        )
        for name in required_true:
            if getattr(self, name) is not True:
                raise ValueError(f"{name} must remain true")

        required_false = (
            "post_outcome_tail_threshold_adaptation_allowed",
            "alternate_q90_q99_rescue_allowed",
            "teacher_tail_evaluation_authorized",
            "td60_authorized",
            "training_authorized",
        )
        for name in required_false:
            if getattr(self, name) is not False:
                raise ValueError(f"{name} must remain false")

    def canonical_digest(self) -> str:
        self.validate()
        payload = asdict(self)
        payload["zero_slack_structural_cases"] = [
            list(x) for x in self.zero_slack_structural_cases
        ]
        return hashlib.sha256(
            _canonical(
                {
                    "schema": "V5_FULL104_RARE_TAIL_MOLECULAR_EXECUTION_CONTRACT_V1",
                    **payload,
                }
            )
        ).hexdigest()
