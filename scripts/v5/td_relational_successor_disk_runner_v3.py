from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping

import td_relational_successor_disk_runner_v2 as D2
import td_relational_successor_gate_v2 as G
import td_relational_successor_qualification_runner_v2 as Q2
import td_relational_successor_qualification_runner_v3 as Q3
import td_relational_successor_readiness_v2 as R
import td_test_qualification_package_v2 as P


class DiskRunnerV3Error(ValueError):
    pass


PREFLIGHT_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_DISK_PREFLIGHT_V3"
BLINDED_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_BLINDED_FIT_RECEIPT_V3"
ADJUDICATION_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_DISK_ADJUDICATION_V3"

_PHASE_AUTHORITY = {
    "real_execution_authorized": False,
    "target_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def _sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _jsonable(value):
    if dataclasses.is_dataclass(value):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _write_json_durable(path: Path | str, value) -> None:
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


def _read_json(path: Path | str) -> dict:
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise DiskRunnerV3Error(f"JSON input missing or symlinked: {p}")
    try:
        value = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DiskRunnerV3Error(f"cannot read JSON input: {p}") from exc
    if not isinstance(value, dict):
        raise DiskRunnerV3Error(f"JSON root must be an object: {p}")
    return value


def _read_controller_json(path: Path | str) -> dict:
    # Kept separate so tests can prove no controller read occurs before blinded-receipt authentication.
    return _read_json(path)


def _within(path: Path | str, root: Path | str) -> bool:
    child = Path(path).resolve()
    parent = Path(root).resolve()
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _guard_new_output(output_path: Path | str, *, protected_files=(), fit_dir: Path | str | None = None) -> Path:
    output = Path(output_path).resolve()
    for protected in protected_files:
        if output == Path(protected).resolve():
            raise DiskRunnerV3Error("qualification output cannot overwrite an input artifact")
    if fit_dir is not None and _within(output, fit_dir):
        raise DiskRunnerV3Error("qualification output cannot be written inside authenticated fit custody")
    if output.exists():
        raise DiskRunnerV3Error("qualification output already exists; overwrite is forbidden")
    return output


def preflight_disk_package(
    *, binding_path: Path | str, fit_dir: Path | str, authenticated_package_sha256: str,
) -> tuple[P.ValidatedExternalPackage, object, dict]:
    try:
        package, adapter, receipt = D2.preflight_disk_package(
            binding_path=binding_path,
            fit_dir=fit_dir,
            authenticated_package_sha256=authenticated_package_sha256,
        )
    except D2.DiskRunnerError as exc:
        raise DiskRunnerV3Error(str(exc)) from exc
    out = dict(receipt)
    out["schema"] = PREFLIGHT_SCHEMA
    return package, adapter, out


def run_blinded_fit_phase(
    *, binding_path: Path | str, fit_dir: Path | str, authenticated_package_sha256: str,
    blinded_output_path: Path | str,
) -> tuple[dict, str]:
    """Execute phase 1 with no controller path or controller artifact in the API."""
    output = _guard_new_output(
        blinded_output_path,
        protected_files=(binding_path,),
        fit_dir=fit_dir,
    )
    package, adapter, _ = preflight_disk_package(
        binding_path=binding_path,
        fit_dir=fit_dir,
        authenticated_package_sha256=authenticated_package_sha256,
    )
    try:
        fit_receipt = Q3.execute_blinded_fit(adapter)
    except Q2.QualificationRunnerError as exc:
        raise DiskRunnerV3Error(str(exc)) from exc
    document = {
        "schema": BLINDED_SCHEMA,
        "package_id": package.package_id,
        "package_sha256": package.package_sha256,
        "fit_receipt": fit_receipt,
        "authority": {
            **_PHASE_AUTHORITY,
            "controller_truth_opened": False,
        },
    }
    _write_json_durable(output, document)
    return document, _sha256_file(output)


def _expect_fields(value: Mapping, expected: set[str], label: str) -> None:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise DiskRunnerV3Error(f"invalid frozen blinded receipt shape: {label}")


def _scale_result(value: Mapping) -> G.ScaleResult:
    fields = {
        "scale_label", "numerator", "denominator", "status", "reason", "observed_statistic",
        "family_null_p95", "n_observed_donors", "observed_donor_agreements",
        "observed_resolved_relations", "null_source_statistics", "n_sampled_triplets", "eligible_donors",
    }
    _expect_fields(value, fields, "scale_result")
    return G.ScaleResult(
        scale_label=str(value["scale_label"]),
        numerator=int(value["numerator"]),
        denominator=int(value["denominator"]),
        status=str(value["status"]),
        reason=str(value["reason"]),
        observed_statistic=None if value["observed_statistic"] is None else float(value["observed_statistic"]),
        family_null_p95=None if value["family_null_p95"] is None else float(value["family_null_p95"]),
        n_observed_donors=int(value["n_observed_donors"]),
        observed_donor_agreements={str(k): float(v) for k, v in value["observed_donor_agreements"].items()},
        observed_resolved_relations={str(k): int(v) for k, v in value["observed_resolved_relations"].items()},
        null_source_statistics=tuple(None if v is None else float(v) for v in value["null_source_statistics"]),
        n_sampled_triplets=int(value["n_sampled_triplets"]),
        eligible_donors=tuple(str(v) for v in value["eligible_donors"]),
    )


def _profile(value: Mapping) -> G.RelationalProfileReceipt:
    fields = {
        "source", "panel_id", "profile_id", "scale_results", "characterization",
        "focal_anchor_count", "failure_scope", "authority",
    }
    _expect_fields(value, fields, "profile")
    scales = value["scale_results"]
    # Durable receipts are written with sort_keys=True, so validate the exact label set, not JSON key order.
    if (
        not isinstance(scales, Mapping)
        or len(scales) != len(G.SCALE_LABELS)
        or set(scales) != set(G.SCALE_LABELS)
    ):
        raise DiskRunnerV3Error("frozen profile scale grid mismatch")
    return G.RelationalProfileReceipt(
        source=str(value["source"]),
        panel_id=str(value["panel_id"]),
        profile_id=str(value["profile_id"]),
        scale_results={label: _scale_result(scales[label]) for label in G.SCALE_LABELS},
        characterization=tuple(str(v) for v in value["characterization"]),
        focal_anchor_count=int(value["focal_anchor_count"]),
        failure_scope=str(value["failure_scope"]),
        authority={str(k): bool(v) for k, v in value["authority"].items()},
    )


def _fit_receipt_from_document(document: Mapping, package: P.ValidatedExternalPackage) -> Q2.BlindedFitReceipt:
    _expect_fields(document, {"schema", "package_id", "package_sha256", "fit_receipt", "authority"}, "document")
    if document.get("schema") != BLINDED_SCHEMA:
        raise DiskRunnerV3Error("wrong blinded-fit receipt schema")
    if document.get("package_id") != package.package_id or document.get("package_sha256") != package.package_sha256:
        raise DiskRunnerV3Error("blinded receipt package identity mismatch")
    authority = document.get("authority")
    expected_authority = {**_PHASE_AUTHORITY, "controller_truth_opened": False}
    if authority != expected_authority:
        raise DiskRunnerV3Error("blinded receipt authority boundary mismatch")
    fit = document.get("fit_receipt")
    _expect_fields(fit, {"package_id", "package_sha256", "profiles", "controls", "authority"}, "fit_receipt")
    if fit.get("package_id") != package.package_id or fit.get("package_sha256") != package.package_sha256:
        raise DiskRunnerV3Error("fit receipt package identity mismatch")
    profiles_raw = fit.get("profiles")
    controls_raw = fit.get("controls")
    if not isinstance(profiles_raw, Mapping) or set(profiles_raw) != set(package.fit_views):
        raise DiskRunnerV3Error("fit receipt profiles do not cover exact opaque challenge set")
    if not isinstance(controls_raw, Mapping) or set(controls_raw) != set(package.fit_views):
        raise DiskRunnerV3Error("fit receipt controls do not cover exact opaque challenge set")
    profiles = {cid: _profile(profiles_raw[cid]) for cid in package.fit_views}
    controls = {}
    for cid in package.fit_views:
        local = controls_raw[cid]
        if not isinstance(local, Mapping) or len(local) != 5:
            raise DiskRunnerV3Error("each frozen challenge must contain exactly five control results")
        controls[cid] = {str(control_id): _profile(rec) for control_id, rec in local.items()}
    run_authority = fit.get("authority")
    if not isinstance(run_authority, Mapping) or set(run_authority) != Q2.RUN_AUTHORITY_KEYS:
        raise DiskRunnerV3Error("fit receipt authority keys mismatch")
    if any(value is not False for value in run_authority.values()):
        raise DiskRunnerV3Error("fit receipt cannot carry downstream authority")
    return Q2.BlindedFitReceipt(
        package_id=package.package_id,
        package_sha256=package.package_sha256,
        profiles=profiles,
        controls=controls,
        authority={str(k): bool(v) for k, v in run_authority.items()},
    )


def adjudicate_frozen_blinded_phase(
    *, repo_root: Path | str, binding_path: Path | str, fit_dir: Path | str,
    authenticated_package_sha256: str, blinded_receipt_path: Path | str,
    expected_blinded_receipt_sha256: str, controller_manifest_path: Path | str,
    output_path: Path | str,
) -> dict:
    """Phase 2: authenticate the frozen blinded output before controller truth is opened."""
    output = _guard_new_output(
        output_path,
        protected_files=(binding_path, blinded_receipt_path, controller_manifest_path),
        fit_dir=fit_dir,
    )
    binding = _read_json(binding_path)
    try:
        package = P.validate_external_package_binding(
            binding,
            authenticated_package_sha256=authenticated_package_sha256,
        )
    except P.PackageBindingError as exc:
        raise DiskRunnerV3Error(str(exc)) from exc

    if not isinstance(expected_blinded_receipt_sha256, str) or len(expected_blinded_receipt_sha256) != 64:
        raise DiskRunnerV3Error("expected blinded receipt SHA-256 is required")
    actual_blinded_sha = _sha256_file(blinded_receipt_path)
    if actual_blinded_sha != expected_blinded_receipt_sha256:
        raise DiskRunnerV3Error("blinded receipt SHA-256 mismatch; controller truth remains closed")
    blinded_document = _read_json(blinded_receipt_path)
    fit_receipt = _fit_receipt_from_document(blinded_document, package)

    # This is the first controller-truth access in the phase-2 code path.
    controller_manifest = _read_controller_json(controller_manifest_path)
    gate_binding = R.build_relational_gate_binding(repo_root)
    try:
        qualification = Q3.adjudicate_blinded_qualification(
            package=package,
            fit_receipt=fit_receipt,
            controller_manifest=controller_manifest,
            gate_binding=gate_binding,
        )
    except Q3.QualificationRunnerV3Error as exc:
        raise DiskRunnerV3Error(str(exc)) from exc
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
        "gate_binding": gate_binding,
        "qualification": qualification,
        "readiness": readiness,
        "authority": dict(_PHASE_AUTHORITY),
    }
    _write_json_durable(output, receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Two-phase TD relational qualification with controller custody")
    sub = parser.add_subparsers(dest="phase", required=True)

    pre = sub.add_parser("preflight")
    pre.add_argument("--binding", required=True)
    pre.add_argument("--fit-dir", required=True)
    pre.add_argument("--authenticated-package-sha256", required=True)
    pre.add_argument("--output", required=True)

    blind = sub.add_parser("blinded-fit")
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
        output = _guard_new_output(args.output, protected_files=(args.binding,), fit_dir=args.fit_dir)
        _, _, receipt = preflight_disk_package(
            binding_path=args.binding,
            fit_dir=args.fit_dir,
            authenticated_package_sha256=args.authenticated_package_sha256,
        )
        _write_json_durable(output, receipt)
        print(receipt["status"])
        return 0
    if args.phase == "blinded-fit":
        _, digest = run_blinded_fit_phase(
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
