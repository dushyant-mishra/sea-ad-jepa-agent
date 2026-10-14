from __future__ import annotations

from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import sys
from typing import Iterable, Mapping

from .v80_sparse_positive_benchmark import (
    SparsePositiveWorld,
    benchmark_identity,
    serialize_controller_transport,
    serialize_fit_transport,
)


_V79_BINDING = {
    "scorer_orchestrator_head": "ac1e73d79489438634aaeeca035d229875f3186a",
    "contract_sha256": "57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26",
    "world_set_digest": "40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286",
    "final_receipt_sha256": "ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd",
    "historical_result": "NOT_QUALIFIED",
}

_AUTHORITY = {
    "real_data_authorized": False,
    "target_selection_authorized": False,
    "representation_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "synthetic_training_authorized": False,
    "real_training_authorized": False,
}

_RUNTIME = {"python": "3.11.9", "numpy": "2.3.5"}
_SOURCE_FILES = (
    "scripts/v80/v80_sparse_positive_benchmark.py",
    "scripts/v80/v80_sparse_positive_adjudicator.py",
    "scripts/v80/finalize_v80_sparse_positive_package.py",
)
_NONREG_PATH = "results/v80/sparse_positive/V80_V79_NONREGRESSION_BINDING_V1.json"


def _canon(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _sha_obj(value: object) -> str:
    return sha256(_canon(value)).hexdigest()


def _sha_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required file missing or symlinked: {path}")
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _inside(root: Path, path: Path) -> Path:
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except Exception as exc:
        raise ValueError(f"custody path escapes repository: {path}") from exc
    return resolved


def _runtime_identity() -> dict[str, str]:
    observed = {
        "python": ".".join(str(x) for x in sys.version_info[:3]),
        "numpy": version("numpy"),
    }
    if observed != _RUNTIME:
        raise ValueError(f"runtime environment drift detected: {observed}")
    return observed


def _load_contract(contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("schema") != "V80_SPARSE_POSITIVE_QUALIFICATION_CONTRACT_V1":
        raise ValueError("V80 contract schema differs")
    if contract.get("v79_immutable_binding") != _V79_BINDING:
        raise ValueError("V79 immutable historical binding differs")
    if contract.get("authority") != _AUTHORITY:
        raise ValueError("authority boundary differs")
    return contract


def _validate_nonreg(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "V80_V79_NONREGRESSION_BINDING_V1":
        raise ValueError("V79 non-regression binding schema differs")
    v79 = payload.get("v79", {})
    required = {
        "historical_result": "NOT_QUALIFIED",
        "contract_sha256": _V79_BINDING["contract_sha256"],
        "world_set_digest": _V79_BINDING["world_set_digest"],
        "scorer_orchestrator_head": _V79_BINDING["scorer_orchestrator_head"],
        "final_scoring_receipt_sha256": _V79_BINDING["final_receipt_sha256"],
    }
    for key, expected in required.items():
        if v79.get(key) != expected:
            raise ValueError(f"V79 non-regression binding differs: {key}")
    return payload


def build_package_receipt(
    *,
    worlds: Iterable[SparsePositiveWorld],
    repo_root: Path,
    contract_path: Path,
) -> dict[str, object]:
    world_tuple = tuple(worlds)
    root = Path(repo_root).resolve()
    path = Path(contract_path)
    if not path.is_absolute():
        path = root / path
    path = _inside(root, path)
    contract = _load_contract(path)
    nonreg_path = _inside(root, root / _NONREG_PATH)
    _validate_nonreg(nonreg_path)
    source_identity = {
        rel: _sha_file(_inside(root, root / rel))
        for rel in _SOURCE_FILES
    }
    runtime = _runtime_identity()
    fit = serialize_fit_transport(world_tuple)
    controller = serialize_controller_transport(world_tuple)
    return {
        "schema": "V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1",
        "status": "BENCHMARK_PACKAGE_ONLY__NO_ESTIMATOR_RUN",
        "contract_sha256": _sha_file(path),
        "nonregression_binding_sha256": _sha_file(nonreg_path),
        "source_sha256": source_identity,
        "runtime_environment": runtime,
        "benchmark_identity_sha256": benchmark_identity(world_tuple),
        "fit_transport_sha256": _sha_obj(fit),
        "controller_transport_sha256": _sha_obj(controller),
        "n_worlds": len(world_tuple),
        "n_fits": len(controller["fits"]),
        "v79_immutable_binding": dict(_V79_BINDING),
        "synthetic_recovery_thresholds": dict(contract["synthetic_recovery_thresholds"]),
        "authority": dict(_AUTHORITY),
    }


def write_transport_once(path: Path, payload: Mapping[str, object]) -> None:
    target = Path(path)
    if target.exists() or target.is_symlink():
        raise ValueError(f"target exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_canon(dict(payload)))
