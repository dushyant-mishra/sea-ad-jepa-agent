"""Demonstrate on synthetic files whether the gate (current signature, replay manifest supplied) accepts an
authorization that is bound to no owner-decision record. Semantic RED evidence for item 1."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tests" / "v5"))
import td_g6g7_gate_fixtures as F  # noqa: E402


class MP:
    def setattr(self, obj, name, value, raising=True):
        setattr(obj, name, value)

    def setitem(self, mapping, key, value):
        mapping[key] = value


m = F.load_common("demo_no_owner_decision")
with tempfile.TemporaryDirectory() as tmp:
    b = F.build_gate(Path(tmp), m, MP())
    try:
        m.load_runtime_authorization(b.auth, preflight_path=b.preflight, mapping_path=b.mapping,
                                     replay_manifest_path=b.replay_manifest, g6_path=b.g6, g7_path=b.g7)
        print("authorization with no owner-decision record: ACCEPTED by the gate (defect)")
    except Exception as exc:  # noqa: BLE001
        print(f"authorization with no owner-decision record: refused: {type(exc).__name__}: {exc}")
