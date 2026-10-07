import importlib
import subprocess
import sys

from sea_ad_jepa.v5.inactive_checkpoint_binding_v1 import CANONICAL_RUNTIME_SOURCE_FILES


def test_runtime_provenance_covers_authenticated_ema_mechanics_and_successor_binding():
    assert "ema_presentation_v1.py" in CANONICAL_RUNTIME_SOURCE_FILES
    assert "ema_bound_runtime_proof_v1.py" in CANONICAL_RUNTIME_SOURCE_FILES
    assert "_ema_bound_runtime_proof_impl_v1.py" in CANONICAL_RUNTIME_SOURCE_FILES, (
        "canonical EMA wrapper delegates to an implementation blob that is absent from runtime provenance"
    )


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


def test_private_ema_implementation_cannot_reopen_retired_dictionary_persistence_in_fresh_process():
    code = (
        "import sea_ad_jepa.v5._ema_bound_runtime_proof_impl_v1 as m; "
        "raise SystemExit(1 if hasattr(m, 'persist_and_verify_presentation_ema_checkpoint') else 0)"
    )
    result = subprocess.run([sys.executable, "-c", code], check=False)
    assert result.returncode == 0, (
        "fresh direct import of private EMA implementation reopens the retired dictionary persistence route"
    )
