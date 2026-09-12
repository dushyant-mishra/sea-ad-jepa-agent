import importlib.util
import inspect
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "scripts" / "v5_anticheat" / "bind_full104_expression_blocks_v4.py"
spec = importlib.util.spec_from_file_location("full104_bind_v4_reconcile", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_production_metadata_authority_is_frozen_and_not_publicly_overridable():
    assert m.EXPECTED_METADATA_SQLITE_SHA256 == "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"
    signature = inspect.signature(m.bind_full104_blocks)
    assert "expected_metadata_sha256" not in signature.parameters
    assert signature.parameters["_expected_metadata_sha256"].default == m.EXPECTED_METADATA_SQLITE_SHA256
