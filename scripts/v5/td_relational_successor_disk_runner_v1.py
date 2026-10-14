from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping

import numpy as np

import td_relational_successor_qualification_runner_v1 as Q
import td_relational_successor_readiness_v1 as R
import td_relational_successor_synthetic_adapter_v1 as A
import td_test_qualification_package_v1 as P


class DiskRunnerError(ValueError):
    pass


RUN_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_DISK_QUALIFICATION_RUN_V1"
FIT_VIEW_NPZ_FIELDS = frozenset({
    "source", "panel_id",
    "z_values", "x_values", "y_values",
    "z_measured", "x_measured", "y_measured",
    "z_feature_ids", "x_feature_ids", "y_feature_ids",
    "donor_ids", "operator_ids", "global_rows",
    "source_library", "detected_genes",
    "focal_mask", "neighbor_pool_mask", "min_focal_anchors_per_donor",
    "control_ids", "control_focal_masks", "control_neighbor_pool_masks",
    "control_min_focal_anchors_per_donor",
})


def _sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path | str):
    p=Path(path)
    if not p.is_file():
        raise DiskRunnerError(f"JSON file missing: {p}")
    try:
        with p.open("r",encoding="utf-8") as fh:
            value=json.load(fh)
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        raise DiskRunnerError(f"cannot read JSON file: {p}") from exc
    if not isinstance(value,Mapping):
        raise DiskRunnerError(f"JSON root must be an object: {p}")
    return value


def _load_npz_arrays(path: Path) -> dict[str,np.ndarray]:
    try:
        with np.load(path,allow_pickle=False) as z:
            if set(z.files) != FIT_VIEW_NPZ_FIELDS:
                raise DiskRunnerError(f"fit view must use the exact frozen NPZ schema: {path.name}")
            arrays={}
            for key in sorted(FIT_VIEW_NPZ_FIELDS):
                try:
                    arr=np.asarray(z[key])
                except ValueError as exc:
                    if "Object arrays" in str(exc) or "allow_pickle=False" in str(exc):
                        raise DiskRunnerError(f"object arrays are forbidden in fit views: {path.name}") from exc
                    raise
                if arr.dtype.kind == "O":
                    raise DiskRunnerError(f"object arrays are forbidden in fit views: {path.name}")
                arrays[key]=arr
            return arrays
    except DiskRunnerError:
        raise
    except (OSError,ValueError,EOFError) as exc:
        raise DiskRunnerError(f"cannot safely load fit-view NPZ: {path.name}") from exc


def _scalar_string(arr: np.ndarray, label: str) -> str:
    if arr.shape != () or arr.dtype.kind not in {"U","S"}:
        raise DiskRunnerError(f"{label} must be a scalar string")
    value=arr.item()
    if isinstance(value,bytes):
        value=value.decode("utf-8")
    value=str(value)
    if not value:
        raise DiskRunnerError(f"{label} must be nonempty")
    return value


def _scalar_positive_int(arr: np.ndarray, label: str) -> int:
    if arr.shape != () or arr.dtype.kind not in {"i","u"}:
        raise DiskRunnerError(f"{label} must be a scalar integer")
    value=int(arr.item())
    if value < 1:
        raise DiskRunnerError(f"{label} must be positive")
    return value


def _string_vector(arr: np.ndarray, label: str) -> np.ndarray:
    if arr.ndim != 1 or arr.dtype.kind not in {"U","S"}:
        raise DiskRunnerError(f"{label} must be a one-dimensional string array")
    if arr.size and any(not str(v.decode("utf-8") if isinstance(v,bytes) else v) for v in arr.tolist()):
        raise DiskRunnerError(f"{label} cannot contain empty strings")
    return arr.astype(str)


def _bool_array(arr: np.ndarray, label: str, ndim: int) -> np.ndarray:
    if arr.ndim != ndim or arr.dtype.kind != "b":
        raise DiskRunnerError(f"{label} must be a {ndim}D boolean array")
    return arr


def _integer_array(arr: np.ndarray, label: str, ndim: int) -> np.ndarray:
    if arr.ndim != ndim or arr.dtype.kind not in {"i","u"}:
        raise DiskRunnerError(f"{label} must be a {ndim}D integer array")
    return arr


def _numeric_array(arr: np.ndarray, label: str, ndim: int) -> np.ndarray:
    if arr.ndim != ndim or arr.dtype.kind not in {"i","u","f"}:
        raise DiskRunnerError(f"{label} must be a {ndim}D numeric array")
    return arr


def _executor_input_from_npz(arrays: Mapping[str,np.ndarray]) -> dict:
    source=_scalar_string(arrays["source"],"source")
    panel_id=_scalar_string(arrays["panel_id"],"panel_id")
    z_values=_numeric_array(arrays["z_values"],"z_values",2)
    n=z_values.shape[0]
    x_values=_numeric_array(arrays["x_values"],"x_values",2)
    y_values=_numeric_array(arrays["y_values"],"y_values",2)
    z_measured=_bool_array(arrays["z_measured"],"z_measured",2)
    x_measured=_bool_array(arrays["x_measured"],"x_measured",2)
    y_measured=_bool_array(arrays["y_measured"],"y_measured",2)
    z_feature_ids=_string_vector(arrays["z_feature_ids"],"z_feature_ids")
    x_feature_ids=_string_vector(arrays["x_feature_ids"],"x_feature_ids")
    y_feature_ids=_string_vector(arrays["y_feature_ids"],"y_feature_ids")
    donor_ids=_string_vector(arrays["donor_ids"],"donor_ids")
    operator_ids=_string_vector(arrays["operator_ids"],"operator_ids")
    global_rows=_integer_array(arrays["global_rows"],"global_rows",1)
    source_library=_numeric_array(arrays["source_library"],"source_library",1)
    detected_genes=_integer_array(arrays["detected_genes"],"detected_genes",1)
    focal_mask=_bool_array(arrays["focal_mask"],"focal_mask",1)
    neighbor_pool_mask=_bool_array(arrays["neighbor_pool_mask"],"neighbor_pool_mask",1)
    primary_min=_scalar_positive_int(arrays["min_focal_anchors_per_donor"],"min_focal_anchors_per_donor")
    control_ids=_string_vector(arrays["control_ids"],"control_ids")
    control_focal=_bool_array(arrays["control_focal_masks"],"control_focal_masks",2)
    control_pool=_bool_array(arrays["control_neighbor_pool_masks"],"control_neighbor_pool_masks",2)
    control_min=_integer_array(arrays["control_min_focal_anchors_per_donor"],"control_min_focal_anchors_per_donor",1)

    row_vectors=(donor_ids,operator_ids,global_rows,source_library,detected_genes,focal_mask,neighbor_pool_mask)
    if any(len(v) != n for v in row_vectors):
        raise DiskRunnerError("fit-view row-vector length mismatch")
    if any(v.shape[0] != n for v in (x_values,y_values,z_measured,x_measured,y_measured)):
        raise DiskRunnerError("fit-view observation row count mismatch")
    c=len(control_ids)
    if control_focal.shape != (c,n) or control_pool.shape != (c,n) or control_min.shape != (c,):
        raise DiskRunnerError("control profile array shapes are inconsistent")
    if c != len(set(control_ids.tolist())):
        raise DiskRunnerError("control IDs must be unique")
    if np.any(control_min < 1):
        raise DiskRunnerError("control min_focal_anchors_per_donor must be positive")

    controls={}
    for i,control_id in enumerate(control_ids.tolist()):
        controls[str(control_id)]={
            "focal_mask":control_focal[i],
            "neighbor_pool_mask":control_pool[i],
            "min_focal_anchors_per_donor":int(control_min[i]),
        }
    return {
        "source":source,
        "panel_id":panel_id,
        "z_values":z_values,
        "x_values":x_values,
        "y_values":y_values,
        "z_measured":z_measured,
        "x_measured":x_measured,
        "y_measured":y_measured,
        "z_feature_ids":z_feature_ids.tolist(),
        "x_feature_ids":x_feature_ids.tolist(),
        "y_feature_ids":y_feature_ids.tolist(),
        "donor_ids":donor_ids,
        "operator_ids":operator_ids,
        "global_rows":global_rows,
        "source_library":source_library,
        "detected_genes":detected_genes,
        "focal_mask":focal_mask,
        "neighbor_pool_mask":neighbor_pool_mask,
        "min_focal_anchors_per_donor":primary_min,
        "control_profiles":controls,
    }


def load_authenticated_fit_payloads(
    package: P.ValidatedExternalPackage,
    fit_dir: Path | str,
) -> dict[str,dict]:
    if not isinstance(package,P.ValidatedExternalPackage):
        raise DiskRunnerError("package must be a ValidatedExternalPackage")
    root=Path(fit_dir)
    if not root.is_dir():
        raise DiskRunnerError(f"fit-view directory missing: {root}")
    payloads={}
    for challenge_id,expected_sha in package.fit_views.items():
        path=root/f"{expected_sha}.npz"
        if path.is_symlink() or not path.is_file():
            raise DiskRunnerError(f"authenticated fit-view file missing: {expected_sha}.npz")
        actual_sha=_sha256_file(path)
        if actual_sha != expected_sha:
            raise DiskRunnerError(f"fit-view SHA-256 mismatch: {challenge_id}")
        arrays=_load_npz_arrays(path)
        payloads[challenge_id]={
            "authenticated_fit_view_sha256":actual_sha,
            "executor_input":_executor_input_from_npz(arrays),
        }
    return payloads


def _jsonable(value):
    if dataclasses.is_dataclass(value):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value,np.generic):
        return value.item()
    if isinstance(value,np.ndarray):
        return value.tolist()
    if isinstance(value,Mapping):
        return {str(k):_jsonable(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        return [_jsonable(v) for v in value]
    return value


def _write_json_atomic(path: Path | str, value) -> None:
    target=Path(path)
    target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_name(target.name+".tmp")
    with tmp.open("w",encoding="utf-8",newline="\n") as fh:
        json.dump(_jsonable(value),fh,sort_keys=True,separators=(",",":"),ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp,target)


def run_disk_qualification(
    *,
    repo_root: Path | str,
    binding_path: Path | str,
    fit_dir: Path | str,
    controller_manifest_path: Path | str,
    authenticated_package_sha256: str,
    output_path: Path | str,
) -> dict:
    binding_document=_read_json(binding_path)
    try:
        package=P.validate_external_package_binding(
            binding_document,
            authenticated_package_sha256=authenticated_package_sha256,
        )
    except P.PackageBindingError as exc:
        raise DiskRunnerError(str(exc)) from exc

    payloads=load_authenticated_fit_payloads(package,fit_dir)
    try:
        adapter=A.build_relational_qualification_adapter(package,payloads)
    except A.RelationalAdapterError as exc:
        raise DiskRunnerError(str(exc)) from exc
    if adapter.status != "READY":
        raise DiskRunnerError(f"external package adapter is not READY: {adapter.status}")

    # Controller truth is deliberately not opened until every blinded fit completes.
    try:
        fit_receipt=Q.execute_blinded_fit(adapter)
    except Q.QualificationRunnerError as exc:
        raise DiskRunnerError(str(exc)) from exc

    controller_manifest=_read_json(controller_manifest_path)
    gate_binding=R.build_relational_gate_binding(repo_root)
    try:
        qualification=Q.adjudicate_blinded_qualification(
            package=package,
            fit_receipt=fit_receipt,
            controller_manifest=controller_manifest,
            gate_binding=gate_binding,
        )
    except Q.QualificationRunnerError as exc:
        raise DiskRunnerError(str(exc)) from exc
    readiness=R.assess_relational_successor_readiness(
        binding=gate_binding,
        external_package_present=True,
        qualification_receipt=qualification,
    )
    receipt={
        "schema":RUN_SCHEMA,
        "package_id":package.package_id,
        "package_sha256":package.package_sha256,
        "gate_binding":gate_binding,
        "qualification":qualification,
        "readiness":readiness,
        "authority":{
            "real_execution_authorized":False,
            "target_selection_authorized":False,
            "td60_authorized":False,
            "stage4_authorized":False,
            "training_authorized":False,
        },
    }
    _write_json_atomic(output_path,receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(description="Run blinded TD relational test-of-test qualification from an authenticated external package")
    p.add_argument("--repo-root",default=".")
    p.add_argument("--binding",required=True)
    p.add_argument("--fit-dir",required=True)
    p.add_argument("--controller-manifest",required=True)
    p.add_argument("--authenticated-package-sha256",required=True)
    p.add_argument("--output",required=True)
    return p


def main(argv=None) -> int:
    args=_parser().parse_args(argv)
    receipt=run_disk_qualification(
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
