from __future__ import annotations

import inspect
from pathlib import Path

from sea_ad_jepa.v5.current_authority_closure_v1 import validate_current_v5_authority_closure_v1


def test_current_closure_requires_live_target_and_execution_evidence_parameters() -> None:
    params = inspect.signature(validate_current_v5_authority_closure_v1).parameters
    for name in (
        "target_construction",
        "masking_qualification_execution",
        "remaining_rna_execution",
    ):
        assert name in params, f"current closure must require {name}"


def test_current_closure_source_requires_exact_current_successor_types() -> None:
    source = Path("src/sea_ad_jepa/v5/current_authority_closure_v1.py").read_text(encoding="utf-8")
    for token in (
        "TargetConstructionAuthorityV1",
        "MaskingQualificationExecutionAuthorityV1",
        "RemainingRnaExecutionAuthorityV1",
        "AntiCheatAuthorityBundleV2",
        "bind_teacher_semantics_to_target_construction_v1",
        "bind_execution_evidence",
    ):
        assert token in source, f"current closure missing successor binding: {token}"
    assert "AntiCheatAuthorityBundleV1" not in source
