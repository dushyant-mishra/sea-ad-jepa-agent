from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Mapping

import td_relational_successor_disk_runner_v3 as V3
import td_relational_successor_qualification_runner_v3 as Q3
import td_relational_successor_readiness_v2 as R
import td_test_qualification_package_v2 as P


class DiskRunnerV4Error(ValueError):
    pass


BLINDED_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_BLINDED_FIT_RECEIPT_V4"
ADJUDICATION_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V4"

FIT_ENGINE_FILES = (
    "scripts/v5/td_test_qualification_package_v2.py",
    "scripts/v5/td_relational_successor_synthetic_adapter_v2.py",
    "scripts/v5/td_relational_successor_estimability_v1.py",
    "scripts/v5/td_relational_successor_gate_v2.py",
    "scripts/v5/td_relational_successor_observed_executor_v2.py",
    "scripts/v5/td_relational_successor_capability_reducer_v1.py",
    "scripts/v5/td_relational_successor_qualification_runner_v3.py",
    "scripts/v5/td_relational_successor_disk_runner_v4.py",
)


def _sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fit_engine_identity(repo_root: Path | str) -> dict[str, str]:
    root = Path(repo_root).resolve()
    identity: dict[str, str] = {}
    for relative in FIT_ENGINE_FILES:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise DiskRunnerV4Error(f"fit-engine source missing or symlinked: {relative}")
        identity[relative] = _sha256_file(path)
    return identity


def _validate_identity(value: object, expected: Mapping[str, str]) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise DiskRunnerV4Error("blinded receipt fit-engine identity keys mismatch")
    for key, digest in expected.items():
        if value.get(key) != digest:
            raise DiskRunnerV4Error(f"blinded receipt fit-engine identity mismatch: {key}")


def run_blinded_fit_phase(
    *, repo_root: Path | str, binding_path: Path | str, fit_dir: Path | str,
    authenticated_package_sha256: str, blinded_output_path: Path | str,
+) -> tuple[dict, str]:
    """Phase 1 with no controller input and an explicit science-code identity binding."""
    output = V3._guard_new_output(
        blinded_output_path,
        protected_files=(binding_path,),
        fit_dir=fit_dir,
    )
    package, adapter, _ = V3.preflight_disk_package(
        binding_path=binding_path,
        fit_dir=fit_dir,
        authenticated_package_sha256=authenticated_package_sha256,
    )
    try:
        fit_receipt = Q3.execute_blinded_fit(adapter)
    except Exception as exc:
        if exc.__class__.__name__ in {"QualificationRunnerError", "QualificationRunnerV3Error"}:
            raise DiskRunnerV4Error(str(exc)) from exc
        raise
    document = {
        "schema": BLINDED_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "fit_engine_identity": fit_engine_identity(repo_root),
        "fit_receipt": fit_receipt,
        "authority": {
            **V3._PHASE_AUTHORITY,
            "controller_truth_opened": False,
        },
    }
    V3._write_json_durable(output, document)
    return document, _sha256_file(output)


def _fit_receipt_from_v4_document(
    document: Mapping, package: P.ValidatedExternalPackage, *, repo_root: Path | str,
):
    expected_fields = {
        "schema", "package_id", "package_sha256", "fit_engine_identity", "fit_receipt", "authority"
    }
    if not isinstance(document, Mapping) or set(document) != expected_fields:
        raise DiskRunnerV4Error("invalid frozen V4 blinded receipt shape")
    if document.get("schema") != BLINDED_SCHEMA:
        raise DiskRunnerV4Error("wrong blinded-fit V4 receipt schema")
    expected_identity = fit_engine_identity(repo_root)
    _validate_identity(document.get("fit_engine_identity"), expected_identity)
    v3_document = {
        "schema": V3.BLINDED_SCHEMA,
        "package_id": document.get("package_id"),
        "package_sha256": document.get("package_sha256"),
        "fit_receipt": document.get("fit_receipt"),
        "authority": document.get("authority"),
    }
    try:
        return V3._fit_receipt_from_document(v3_document, package)
    except V3.DiskRunnerV3Error as exc:
        raise DiskRunnerV4Error(str(exc)) from exc


def authenticate_blinded_phase_inputs(
    *, repo_root: Path | str, binding_path: Path | str, authenticated_package_sha256: str,
    blinded_receipt_path: Path | str, expected_blinded_receipt_sha256: str,
):
    binding = V3._read_json(binding_path)
    try:
        package = P.validate_external_package_binding(
            binding,
            authenticated_package_sha256=authenticated_package_sha256,
        )
    except P.PackageBindingError as exc:
        raise DiskRunnerV4Error(str(exc)) from exc
    if not isinstance(expected_blinded_receipt_sha256, str) or len(expected_blinded_receipt_sha256) != 64:
        raise DiskRunnerV4Error("expected blinded receipt SHA-256 is required")
    actual_blinded_sha = _sha256_file(blinded_receipt_path)
    if actual_blinded_sha != expected_blinded_receipt_sha256:
        raise DiskRunnerV4Error("blinded receipt SHA-256 mismatch; controller truth remains closed")
    blinded_document = V3._read_json(blinded_receipt_path)
    fit_receipt = _fit_receipt_from_v4_document(
        blinded_document,
        package,
        repo_root=repo_root,
    )
    return package, fit_receipt, actual_blinded_sha


def adjudicate_frozen_blinded_phase(
    *, repo_root: Path | str, binding_path: Path | str, fit_dir: Path | str,
    authenticated_package_sha256: str, blinded_receipt_path: Path | str,
    expected_blinded_receipt_sha256: str, controller_manifest_path: Path | str,
    output_path: Path | str,
) -> dict:
    """Phase 2 verifies bytes and fit-engine identity before any controller read."""
    output = V3._guard_new_output(
        output_path,
        protected_files=(binding_path, blinded_receipt_path, controller_manifest_path),
        fit_dir=fit_dir,
    )
    package, fit_receipt, actual_blinded_sha = authenticate_blinded_phase_inputs(
        repo_root=repo_root,
        binding_path=binding_path,
        authenticated_package_sha256=authenticated_package_sha256,
        blinded_receipt_path=blinded_receipt_path,
        expected_blinded_receipt_sha256=expected_blinded_receipt_sha256,
    )

    # First controller-truth access occurs only after both receipt bytes and fit-engine identity authenticate.
    controller_manifest = V3._read_controller_json(controller_manifest_path)
    gate_binding = R.build_relational_gate_binding(repo_root)
    try:
        qualification = Q3.adjudicate_blinded_qualification(
            package=package,
            fit_receipt=fit_receipt,
            controller_manifest=controller_manifest,
            gate_binding=gate_binding,
        )
    except Q3.QualificationRunnerV3Error as exc:
        raise DiskRunnerV4Error(str(exc)) from exc
    readiness = R.assess_relational_successor_readiness(
        binding=gate_binding,
        external_package_present=True,
        qualification_receipt=qualification,
    )
    receipt = {
        "schema": ADJUDICATION_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "blinded_fit_receipt_sha256": actual_blinded_sha,
        "fit_engine_identity": fit_engine_identity(repo_root),
        "gate_binding": gate_binding,
        "qualification": qualification,
        "readiness": readiness,
        "authority": dict(V3._PHASE_AUTHORITY),
    }
    V3._write_json_durable(output, receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Two-phase TD relational qualification with engine-bound blind custody")
    sub = parser.add_subparsers(dest="phase", required=True)

    pre = sub.add_parser("preflight")
    pre.add_argument("--binding", required=True)
    pre.add_argument("--fit-dir", required=True)
    pre.add_argument("--authenticated-package-sha256", required=True)
    pre.add_argument("--output", required=True)

    blind = sub.add_parser("blinded-fit")
    blind.add_argument("--repo-root", default=".")
    blind.add_argument("--binding", required=True)
    blind.add_argument("--fit-dir", required=True)
    blind.add_argument("--authenticated-package-sha256", required=True)
    blind.add_argument("--output", required=True)

    adj = sub.add_parser("adjudicate")
    adj.add_argument("--repo-root", default=".")
    adj.add_argument("--binding", required=True)
    adj.add_argument("--fit-dir", required=True)
    adj.add_argument("--authenticated-package-sha256", required=True)
    adj.add_argument("--blinded-receipt", required=True)
    adj.add_argument("--blinded-receipt-sha256", required=True)
    adj.add_argument("--controller-manifest", required=True)
    adj.add_argument("--output", required=True)
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.phase == "preflight":
        output = V3._guard_new_output(args.output, protected_files=(args.binding,), fit_dir=args.fit_dir)
        _, _, receipt = V3.preflight_disk_package(
            binding_path=args.binding,
            fit_dir=args.fit_dir,
            authenticated_package_sha256=args.authenticated_package_sha256,
        )
        V3._write_json_durable(output, receipt)
        print(receipt["status"])
        return 0
    if args.phase == "blinded-fit":
        _, digest = run_blinded_fit_phase(
            repo_root=args.repo_root,
            binding_path=args.binding,
            fit_dir=args.fit_dir,
            authenticated_package_sha256=args.authenticated_package_sha256,
            blinded_output_path=args.output,
        )
        print(digest)
        return 0
    receipt = adjudicate_frozen_blinded_phase(
        repo_root=args.repo_root,
        binding_path=args.binding,
        fit_dir=args.fit_dir,
        authenticated_package_sha256=args.authenticated_package_sha256,
        blinded_receipt_path=args.blinded_receipt,
        expected_blinded_receipt_sha256=args.blinded_receipt_sha256,
        controller_manifest_path=args.controller_manifest,
        output_path=args.output,
    )
    print(receipt["qualification"].status)
    print(receipt["readiness"].status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
