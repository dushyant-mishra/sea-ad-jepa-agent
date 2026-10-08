from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.current_atomic_checkpoint_guard_v2 import (
    seal_current_atomic_checkpoint_v2,
    validate_current_atomic_checkpoint_v2,
)
from sea_ad_jepa.v5.current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def roots() -> dict[str, str]:
    return {name: h(name) for name in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2}


def test_checkpoint_v2_seals_exact_v2_roots_and_training_authority() -> None:
    r = roots()
    checkpoint = seal_current_atomic_checkpoint_v2(
        authority_roots=r,
        preexecution_authority_sha256=h("preexecution"),
        training_authority_sha256=h("training-authority"),
        critical_test_authority_sha256=r["critical_test_authority_sha256"],
        protected_registry_authority_sha256=r["protected_registry_authority_sha256"],
        telemetry_section_sha256_by_name={"loss": h("loss"), "gradient": h("gradient")},
        forbidden_gate_states={"protected_outcomes": False, "legacy_runtime": False},
    )
    verified = validate_current_atomic_checkpoint_v2(
        checkpoint,
        expected_authority_roots=r,
        expected_preexecution_authority_sha256=h("preexecution"),
        expected_training_authority_sha256=h("training-authority"),
        expected_critical_test_authority_sha256=r["critical_test_authority_sha256"],
        expected_protected_registry_authority_sha256=r["protected_registry_authority_sha256"],
        required_telemetry_sections=("loss", "gradient"),
        forbidden_gate_names=("protected_outcomes", "legacy_runtime"),
    )
    assert tuple(verified["authority_roots"]) == CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
    assert verified["training_authorized"] is False


def test_checkpoint_v2_rejects_root_splice_and_open_forbidden_gate() -> None:
    r = roots()
    checkpoint = seal_current_atomic_checkpoint_v2(
        authority_roots=r,
        preexecution_authority_sha256=h("preexecution"),
        training_authority_sha256=h("training-authority"),
        critical_test_authority_sha256=r["critical_test_authority_sha256"],
        protected_registry_authority_sha256=r["protected_registry_authority_sha256"],
        telemetry_section_sha256_by_name={"loss": h("loss")},
        forbidden_gate_states={"protected_outcomes": False},
    )
    bad_roots = dict(r)
    bad_roots["masking_authority_sha256"] = h("splice")
    with pytest.raises(ValueError, match="authority_roots"):
        validate_current_atomic_checkpoint_v2(
            checkpoint,
            expected_authority_roots=bad_roots,
            expected_preexecution_authority_sha256=h("preexecution"),
            expected_training_authority_sha256=h("training-authority"),
            expected_critical_test_authority_sha256=r["critical_test_authority_sha256"],
            expected_protected_registry_authority_sha256=r["protected_registry_authority_sha256"],
            required_telemetry_sections=("loss",),
            forbidden_gate_names=("protected_outcomes",),
        )
    with pytest.raises(ValueError, match="forbidden gate"):
        seal_current_atomic_checkpoint_v2(
            authority_roots=r,
            preexecution_authority_sha256=h("preexecution"),
            training_authority_sha256=h("training-authority"),
            critical_test_authority_sha256=r["critical_test_authority_sha256"],
            protected_registry_authority_sha256=r["protected_registry_authority_sha256"],
            telemetry_section_sha256_by_name={"loss": h("loss")},
            forbidden_gate_states={"protected_outcomes": True},
        )
