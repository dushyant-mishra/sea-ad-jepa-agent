import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/v64/validate_v72_synthetic_pipeline_readiness.py"


def load():
    spec = importlib.util.spec_from_file_location("v72_ready", VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_current_repo_v72_readiness_passes():
    assert load().validate(ROOT) == []


def test_missing_v72_contract_fails(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(ROOT, root, dirs_exist_ok=True)
    (root / "results/v64/V72_COUPLED_MULTIDATASET_SYNTHETIC_TWIN_CONTRACT_V1.json").unlink()
    errors = load().validate(root)
    assert any(x.startswith("MISSING_REQUIRED_JSON:") for x in errors)


def test_g2_cannot_be_silently_closed(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(ROOT, root, dirs_exist_ok=True)
    p = root / "results/v64/V72_STAGE4_G2_SPECIFICATION_GAP_CONTRACT_V1.json"
    obj = json.loads(p.read_text())
    obj["status"] = "CLOSED"
    p.write_text(json.dumps(obj))
    assert "G2_SPECIFICATION_GAP_NOT_OPEN" in load().validate(root)


def test_successor_recipe_cannot_return_to_master(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(ROOT, root, dirs_exist_ok=True)
    p = root / "docker/scenicplus/Dockerfile.successor_pinned"
    p.write_text(p.read_text().replace(
        "ARG CREATE_CISTARGET_DATABASES_COMMIT=304d5dc1b15e5c923908a50a1ec291c3faaccf9c",
        "ARG CREATE_CISTARGET_DATABASES_REF=master"
    ))
    errors = load().validate(root)
    assert "SUCCESSOR_DOCKERFILE_STILL_USES_MASTER" in errors
