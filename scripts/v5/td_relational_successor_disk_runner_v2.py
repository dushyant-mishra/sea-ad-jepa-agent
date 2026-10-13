from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping

import numpy as np

import td_relational_successor_disk_runner_v1 as D1
import td_relational_successor_qualification_runner_v2 as Q
import td_relational_successor_readiness_v2 as R
import td_relational_successor_synthetic_adapter_v2 as A
import td_test_qualification_package_v1 as P1
import td_test_qualification_package_v2 as P


class DiskRunnerError(ValueError):
    pass


RUN_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_DISK_QUALIFICATION_RUN_V2"
PREFLIGHT_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_DISK_PREFLIGHT_V2"
BLINDED_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_BLINDED_FIT_RECEIPT_V2"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _jsonable(value):
    if dataclasses.is_dataclass(value):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _write_json_durable(path: Path | str, value) -> None:
    """Atomic write with fsync before any controller-truth read."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    payload = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, target)
    try:
        dir_fd = os.open(target.parent, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _bridge_for_v1_loader(package: P.ValidatedExternalPackage) -> P1.ValidatedExternalPackage:
    return P1.ValidatedExternalPackage(
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        fit_views=dict(package.fit_views),
        controller_truth_sha256=package.controller_truth_sha256,
        capabilities={},
    )


def load_authenticated_fit_payloads(package: P.ValidatedExternalPackage, fit_dir: Path | str) -> dict[str, dict]:
    if not isinstance(package, P.ValidatedExternalPackage):
        raise DiskRunnerError("package must be a V2 ValidatedExternalPackage")
    if set(package.fit_view_fields) != set(D1.FIT_VIEW_NPZ_FIELDS):
        raise DiskRunnerError("binding fit_view_fields do not match the exact frozen NPZ disk schema")
    try:
        return D1.load_authenticated_fit_payloads(_bridge_for_v1_loader(package), fit_dir)
    except D1.DiskRunnerError as exc:
        raise DiskRunnerError(str(exc)) from exc


def preflight_disk_package(
    *,
    binding_path: Path | str,
    fit_dir: Path | str,
    authenticated_package_sha256: str,
) -> tuple[P.ValidatedExternalPackage, A.RelationalQualificationAdapterReceipt, dict]:
    binding_document = D1._read_json(binding_path)
    try:
        package = P.validate_external_package_binding(
            binding_document,
            authenticated_package_sha256=authenticated_package_sha256,
        )
    except P.PackageBindingError as exc:
        raise DiskRunnerError(str(exc)) from exc
    payloads = load_authenticated_fit_payloads(package, fit_dir)
    try:
        adapter = A.build_relational_qualification_adapter(package, payloads)
    except A.RelationalAdapterError as exc:
        raise DiskRunnerError(str(exc)) from exc
    if adapter.status != "READY":
        raise DiskRunnerError(f"external package adapter is not READY: {adapter.status}")
    receipt = {
        "schema": PREFLIGHT_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "challenge_count": len(package.fit_views),
        "challenge_ids": sorted(package.fit_views),
        "status": "READY_TO_EXECUTE_BLIND_FIT",
        "authority": {
            "biological_qualification_executed": False,
            "real_execution_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }
    return package, adapter, receipt


def _blinded_path(output_path: Path | str) -> Path:
    target = Path(output_path)
    return target.with_name(target.name + ".blinded_fit.json")


def _guard_paths(*, binding_path: Path | str, output_path: Path | str,
                 controller_manifest_path: Path | str | None = None) -> None:
    binding = Path(binding_path).resolve()
    output = Path(output_path).resolve()
    blind = _blinded_path(output_path).resolve()
    if output == blind:
        raise DiskRunnerError("final and blinded output paths must be distinct")
    protected = {binding}
    if controller_manifest_path is not None:
        controller = Path(controller_manifest_path).resolve()
        if controller == binding:
            raise DiskRunnerError("binding and controller manifest paths must be distinct")
        protected.add(controller)
    if output in protected or blind in protected:
        raise DiskRunnerError("qualification outputs cannot overwrite binding or controller inputs")


def run_disk_qualification(
    *,
    repo_root: Path | str,
    binding_path: Path | str,
    fit_dir: Path | str,
    controller_manifest_path: Path | str,
    authenticated_package_sha256: str,
    output_path: Path | str,
) -> dict:
    _guard_paths(
        binding_path=binding_path,
        controller_manifest_path=controller_manifest_path,
        output_path=output_path,
    )
    package, adapter, _ = preflight_disk_package(
        binding_path=binding_path,
        fit_dir=fit_dir,
        authenticated_package_sha256=authenticated_package_sha256,
    )

    # Phase 1: execute every opaque fit/control without controller semantics.
    try:
        fit_receipt = Q.execute_blinded_fit(adapter)
    except Q.QualificationRunnerError as exc:
        raise DiskRunnerError(str(exc)) from exc

    blind_path = _blinded_path(output_path)
    blinded_document = {
        "schema": BLINDED_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "fit_receipt": fit_receipt,
        "authority": {
            "controller_truth_opened": False,
            "real_execution_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }
    _write_json_durable(blind_path, blinded_document)
    blinded_sha256 = _sha256_file(blind_path)

    # Phase 2: only after the blinded artifact exists durably do we open controller truth.
    controller_manifest = D1._read_json(controller_manifest_path)
    gate_binding = R.build_relational_gate_binding(repo_root)
    try:
        qualification = Q.adjudicate_blinded_qualification(
            package=package,
            fit_receipt=fit_receipt,
            controller_manifest=controller_manifest,
            gate_binding=gate_binding,
        )
    except Q.QualificationRunnerError as exc:
        raise DiskRunnerError(str(exc)) from exc
    readiness = R.assess_relational_successor_readiness(
        binding=gate_binding,
        external_package_present=True,
        qualification_receipt=qualification,
    )
    receipt = {
        "schema": RUN_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "blinded_fit_receipt": {
            "path": blind_path.name,
            "sha256": blinded_sha256,
        },
        "gate_binding": gate_binding,
        "qualification": qualification,
        "readiness": readiness,
        "authority": {
            "real_execution_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }
    _write_json_durable(output_path, receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Authenticate/preflight or run the blinded TD relational V2 test-of-test qualification"
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--binding", required=True)
    parser.add_argument("--fit-dir", required=True)
    parser.add_argument("--authenticated-package-sha256", required=True)
    parser.add_argument("--controller-manifest")
    parser.add_argument("--output", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.preflight_only:
        _guard_paths(binding_path=args.binding, output_path=args.output)
        _, _, receipt = preflight_disk_package(
            binding_path=args.binding,
            fit_dir=args.fit_dir,
            authenticated_package_sha256=args.authenticated_package_sha256,
        )
        _write_json_durable(args.output, receipt)
        print(receipt["status"])
        return 0
    if not args.controller_manifest:
        raise SystemExit("--controller-manifest is required unless --preflight-only is used")
    receipt = run_disk_qualification(
        repo_root=args.repo_root,
        binding_path=args.binding,
        fit_dir=args.fit_dir,
        controller_manifest_path=args.controller_manifest,
        authenticated_package_sha256=args.authenticated_package_sha256,
        output_path=args.output,
    )
    print(receipt["qualification"].status)
    print(receipt["readiness"].status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
