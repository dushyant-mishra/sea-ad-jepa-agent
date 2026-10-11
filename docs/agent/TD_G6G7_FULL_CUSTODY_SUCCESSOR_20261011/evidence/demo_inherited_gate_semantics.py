"""Demonstrate, on synthetic files only, what the INHERITED runtime-authorization gate accepts (old signature).
Used as semantic RED evidence for items 1 and 2: run it against the code at a given commit."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tests" / "v5"))
import td_g6g7_gate_fixtures as F  # noqa: E402


class MP:  # minimal monkeypatch stand-in
    def setattr(self, obj, name, value, raising=True):
        setattr(obj, name, value)

    def setitem(self, mapping, key, value):
        mapping[key] = value


def old_gate(m, b):
    return m.load_runtime_authorization(b.auth, preflight_path=b.preflight, mapping_path=b.mapping,
                                        g6_path=b.g6, g7_path=b.g7)


for case in ("reserialized_preflight", "reserialized_mapping", "no_owner_decision_record"):
    m = F.load_common(f"demo_{case}")
    with tempfile.TemporaryDirectory() as tmp:
        b = F.build_gate(Path(tmp), m, MP())
        if case != "no_owner_decision_record":
            path = b.preflight if case == "reserialized_preflight" else b.mapping
            original = json.loads(path.read_text(encoding="utf-8"))
            F.write_json(path, original, indent=4)
            F.rewrite_authorization(m, b)
        try:
            old_gate(m, b)
            print(f"{case}: ACCEPTED by the gate (defect)")
        except Exception as exc:  # noqa: BLE001
            print(f"{case}: refused: {type(exc).__name__}: {exc}")
