import importlib
import subprocess
import sys

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import CANONICAL_RUNTIME_SOURCE_FILES


def test_runtime_provenance_covers_authenticated_ema_mechanics_and_successor_binding():
    assert "__init__.py" in CANONICAL_RUNTIME_SOURCE_FILES, (
        "package import gate affects runtime safety but is absent from provenance"
    )
    assert "ema_presentation_v1.py" in CANONICAL_RUNTIME_SOURCE_FILES
    assert "ema_bound_runtime_proof_v1.py" in CANONICAL_RUNTIME_SOURCE_FILES
    assert "_ema_bound_runtime_proof_impl_v1.py" in CANONICAL_RUNTIME_SOURCE_FILES, (
        "canonical EMA wrapper delegates to an implementation blob that is absent from runtime provenance"
    )
    assert "_inactive_checkpoint_binding_impl_v1.py" in CANONICAL_RUNTIME_SOURCE_FILES


def test_constant_momentum_authority_route_is_not_canonical():
    proof = importlib.import_module("sea_ad_jepa.v5.ema_bound_runtime_proof_v1")
    assert not hasattr(proof, "issue_ema_bound_authority_from_checkpoint"), (
        "constant-momentum EMA authority remains an alternate executable route"
    )
    assert not hasattr(proof, "run_ema_bound_guarded_reference_update"), (
        "constant-momentum EMA runner remains an alternate executable route"
    )
    assert not hasattr(proof, "persist_and_verify_presentation_ema_checkpoint"), (
        "legacy dictionary EMA persistence remains an alternate executable route"
    )
    assert callable(getattr(proof, "issue_presentation_ema_bound_authority_from_checkpoint", None))
    assert callable(getattr(proof, "run_presentation_ema_bound_guarded_reference_update", None))


def _fresh_private_import_is_blocked(module_name: str) -> bool:
    code = (
        "import importlib; "
        "name=" + repr(module_name) + "; "
        "\ntry:\n importlib.import_module(name)\nexcept ImportError:\n raise SystemExit(0)\nelse:\n raise SystemExit(1)"
    )
    result = subprocess.run([sys.executable, "-c", code], check=False)
    return result.returncode == 0


def test_private_ema_implementation_cannot_be_imported_directly_in_fresh_process():
    assert _fresh_private_import_is_blocked(
        "sea_ad_jepa.v5._ema_bound_runtime_proof_impl_v1"
    ), "fresh direct import can bypass the canonical EMA export surface"


def test_private_checkpoint_implementation_cannot_be_imported_directly_in_fresh_process():
    assert _fresh_private_import_is_blocked(
        "sea_ad_jepa.v5._inactive_checkpoint_binding_impl_v1"
    ), "fresh direct import can bypass the canonical checkpoint provenance wrapper"
