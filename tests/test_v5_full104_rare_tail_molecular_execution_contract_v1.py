from __future__ import annotations

from dataclasses import fields
import hashlib
import json
from pathlib import Path

import pytest

from sea_ad_jepa.v5.full104_rare_tail_molecular_execution_contract_v1 import (
    Full104RareTailMolecularExecutionContractV1,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "analysis/v5_full104_target_qualification_20260921/evidence/real_sample/"
    / "RARE_TAIL_MOLECULAR_EXECUTION_CONTRACT_V1.json"
)


def normalized_text_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_contract() -> Full104RareTailMolecularExecutionContractV1:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    names = {f.name for f in fields(Full104RareTailMolecularExecutionContractV1)}
    c = Full104RareTailMolecularExecutionContractV1(
        **{name: payload[name] for name in names}
    )
    c.validate()
    assert payload["contract_sha256"] == c.canonical_digest()
    return c


def test_committed_execution_contract_round_trips() -> None:
    c = load_contract()
    assert c.canonical_digest() == (
        "e834285f652d35fe335d16c0e58eadf7ee2b0ffc11fb11035c4ba17a94b80c02"
    )
    assert c.molecular_execution_authorized is True
    assert c.teacher_tail_evaluation_authorized is False
    assert c.td60_authorized is False
    assert c.training_authorized is False


def test_execution_contract_binds_exact_normalized_code_sources() -> None:
    c = load_contract()
    observed = {
        "runner_normalized_text_sha256": normalized_text_sha256(
            ROOT / "scripts/agent/run_full104_rare_tail_molecular_prequalification_v1_20260922.py"
        ),
        "primitives_normalized_text_sha256": normalized_text_sha256(
            ROOT / "src/sea_ad_jepa/v5/full104_rare_tail_molecular_primitives_v1.py"
        ),
        "authority_source_normalized_text_sha256": normalized_text_sha256(
            ROOT / "src/sea_ad_jepa/v5/full104_rare_tail_molecular_authority_v1.py"
        ),
        "tail_selector_source_normalized_text_sha256": normalized_text_sha256(
            ROOT / "src/sea_ad_jepa/v5/full104_rare_biology_preservation_authority_v1.py"
        ),
        "source_library_parser_source_normalized_text_sha256": normalized_text_sha256(
            ROOT / "src/sea_ad_jepa/v5/full104_masking_streaming_executor_v1.py"
        ),
    }
    for name, value in observed.items():
        assert getattr(c, name) == value, name


def test_zero_slack_nph52_cases_are_explicitly_bound_not_relaxed() -> None:
    c = load_contract()
    assert tuple(tuple(x) for x in c.zero_slack_structural_cases) == ((1, 1), (1, 2), (1, 3))
    assert c.expected_zero_slack_donors == 4
    assert c.evaluate_all_24_cases_even_after_failure is True
    assert c.not_estimable_dominates_full_terminal is True

    with pytest.raises(ValueError, match="zero-slack"):
        type(c)(
            contract_id=c.contract_id,
            zero_slack_structural_cases=((1, 1), (1, 2)),
        ).validate()


def test_no_post_outcome_threshold_rescue_or_scope_expansion() -> None:
    c = load_contract()
    with pytest.raises(ValueError, match="alternate_q90_q99_rescue_allowed"):
        type(c)(
            contract_id=c.contract_id,
            alternate_q90_q99_rescue_allowed=True,
        ).validate()
    with pytest.raises(ValueError, match="teacher_tail_evaluation_authorized"):
        type(c)(
            contract_id=c.contract_id,
            teacher_tail_evaluation_authorized=True,
        ).validate()
