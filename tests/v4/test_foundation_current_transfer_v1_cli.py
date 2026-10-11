from pathlib import Path
import csv
import importlib.util
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v4" / "run_foundation_current_transfer_v1.py"


def load_script():
    spec = importlib.util.spec_from_file_location("run_foundation_current_transfer_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cli_run_binds_rows_and_emits_non_authorizing_receipt(tmp_path):
    mod = load_script()
    metadata = tmp_path / "meta.csv"
    rows = []
    for group in ("g1", "g2"):
        for label, source, x in (("A", "HVS", -3.0), ("B", "SEA_AD", 3.0)):
            rows.append({
                "stable_key": f"{group}-{label}",
                "donor_id": group,
                "matrix_id": group,
                "source": source,
                "broad_class": label,
            })
    with metadata.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    state = tmp_path / "state.npz"
    np.savez_compressed(
        state,
        stable_key=np.asarray([r["stable_key"] for r in rows]),
        cell_state=np.asarray([[-3.0, -2.0], [3.0, 2.0], [-3.1, -2.1], [3.1, 2.1]]),
    )
    ident = tmp_path / "ident.csv"
    with ident.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "broad_label_identifiability"])
        w.writeheader()
        w.writerow({"source": "HVS", "broad_label_identifiability": "AVAILABLE"})
        w.writerow({"source": "SEA_AD", "broad_label_identifiability": "AVAILABLE"})

    out = tmp_path / "receipt.json"
    rec = mod.run(metadata, [state], ident, out, main_broad_classes=["A", "B"])
    assert out.exists()
    saved = json.loads(out.read_text())
    assert saved == rec
    assert rec["cohort"]["cells"] == 4
    assert rec["broad_biology_transfer"]["donor"]["balanced_accuracy"] == 1.0
    assert rec["representation_freeze_authorized"] is False
    assert rec["training_authorized"] is False
    assert rec["factorial_execution_authorized"] is False
