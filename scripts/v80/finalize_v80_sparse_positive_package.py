from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
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


def _load_contract(contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("schema") != "V80_SPARSE_POSITIVE_QUALIFICATION_CONTRACT_V1":
        raise ValueError("V80 contract schema differs")
    binding = contract.get("v79_immutable_binding")
    if binding != _V79_BINDING:
        raise ValueError("V79 immutable historical binding differs")
    authority = contract.get("authority")
    if authority != _AUTHORITY:
        raise ValueError("authority boundary differs")
    return contract


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
    try:
        path.resolve(strict=True).relative_to(root)
    except Exception as exc:
        raise ValueError("contract must be inside repository custody") from exc
    contract = _load_contract(path)
    fit = serialize_fit_transport(world_tuple)
    controller = serialize_controller_transport(world_tuple)
    return {
        "schema": "V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1",
        "status": "BENCHMARK_PACKAGE_ONLY__NO_ESTIMATOR_RUN",
        "contract_sha256": _sha_file(path),
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
