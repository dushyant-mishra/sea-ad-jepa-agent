from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v77" / "build_v77_class_composition_authority.py"
CALIBRATION = ROOT / "results" / "v77" / "s174_replay" / "V77_REAL_TRAIN_EXPRESSION_CALIBRATION_V1.json"
AUTHORITY = ROOT / "results" / "v77" / "V77_CLASS_COMPOSITION_AUTHORITY_V1.json"


def _load_builder():
    spec = importlib.util.spec_from_file_location("v77_class_authority_artifact", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_committed_authority_is_exact_builder_output_for_corrected_calibration():
    A = _load_builder()
    expected = A.build_authority(CALIBRATION)
    committed = json.loads(AUTHORITY.read_text())
    assert committed == expected
    assert committed["calibration_sha256"] == "f6ba2c725a5437cc8455fff418027d36efe9ea9430fbd0a5765df62dedca6068"
    assert committed["train_n_cells"] == 4726
    assert sum(committed["class_counts"]) == 4726
    assert len(committed["class_labels"]) == 24
