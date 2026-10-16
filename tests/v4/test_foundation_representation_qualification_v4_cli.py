import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v4" / "requalify_foundation_representation_v4.py"


def load_cli():
    spec = importlib.util.spec_from_file_location("foundation_representation_v4_cli", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def historical_report():
    return {
        "all_hard_gates_pass": True,
        "foundation_datasets": 13,
        "foundation_matrices": 36,
        "classifications": {
            "balanced_pca160": "QUALIFIED",
            "biological_evidence_response": "DISTINCT",
            "biology_measurement_separation": "SUPPORTED",
            "coordinate_uncertainty": "SUBSPACE-ONLY",
            "cross_dataset_transfer": "STRONG",
            "cross_donor_transfer": "WEAK",
            "cross_matrix_transfer": "WEAK",
            "cross_technology_transfer": "STRONG",
            "measurement_depth_response": "SUPPORTED",
            "state_axes": "ROTATING-WITHIN-STABLE-SUBSPACE",
            "state_subspace": "STABLE",
            "two_axis_domain_support": "INFORMATIVE"
        },
        "governance": {
            "pathology_blind": True,
            "neural_optimizer_updates": 0,
            "production_basis_frozen": False,
            "stage81b_started": False,
            "train_expression_only": True,
            "development_expression_forbidden": True,
            "sealed_expression_forbidden": True
        },
        "performance": {}
    }


def test_cli_binds_source_sha_and_writes_atomic_non_authorizing_receipt(tmp_path: Path):
    m = load_cli()
    src = tmp_path / "historical.json"
    src.write_text(json.dumps(historical_report(), sort_keys=True) + "\n", encoding="utf-8")
    out = tmp_path / "receipt.json"
    rec = m.run(src, out)
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved == rec
    assert saved["source_report_sha256"] == m.sha256_file(src)
    assert saved["training_authorized"] is False
    assert saved["target_discovery_value_read_authorized"] is False
    assert saved["representation_freeze_authorized"] is False
    assert not list(tmp_path.glob("*.tmp"))


def test_cli_refuses_to_overwrite_existing_receipt(tmp_path: Path):
    m = load_cli()
    src = tmp_path / "historical.json"
    src.write_text(json.dumps(historical_report()) + "\n", encoding="utf-8")
    out = tmp_path / "receipt.json"
    out.write_text("already here\n", encoding="utf-8")
    try:
        m.run(src, out)
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing receipt was overwritten")
