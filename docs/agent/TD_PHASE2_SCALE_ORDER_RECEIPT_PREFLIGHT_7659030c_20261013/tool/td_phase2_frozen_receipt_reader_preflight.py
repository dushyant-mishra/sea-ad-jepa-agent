"""Read-only preflight: can the phase-2 reader at a given TD head parse the frozen V4 blinded receipt?

Runs only the pre-controller phase-2 path (V4.authenticate_blinded_phase_inputs). It never receives a
controller path; an audit hook records every file opened or listed so the absence of any access under the
forbidden (controller) directory is evidenced rather than asserted. V3._read_controller_json is also
replaced with a sentinel that aborts if called.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

_EVENTS: list[tuple[str, str]] = []


def _norm(p) -> str | None:
    if isinstance(p, int):
        return None
    if isinstance(p, bytes):
        p = os.fsdecode(p)
    if not isinstance(p, (str, os.PathLike)):
        return None
    try:
        return os.path.normcase(os.path.abspath(os.fspath(p)))
    except Exception:
        return None


def _hook(event, args):
    if event in ("open", "os.listdir", "os.scandir") and args:
        p = _norm(args[0])
        if p is not None:
            _EVENTS.append((event, p))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--binding", required=True)
    ap.add_argument("--binding-sha256", required=True)
    ap.add_argument("--authenticated-package-sha256", required=True)
    ap.add_argument("--blinded-receipt", required=True)
    ap.add_argument("--blinded-receipt-sha256", required=True)
    ap.add_argument("--forbidden-dir", required=True, help="controller directory that must never be accessed")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    repo = Path(a.repo_root).resolve()
    binding = Path(a.binding)
    receipt = Path(a.blinded_receipt)
    forbidden = os.path.normcase(os.path.abspath(a.forbidden_dir))
    result: dict = {"schema": "JEPA_TD_PHASE2_FROZEN_RECEIPT_READER_PREFLIGHT_V1", "repo_root": str(repo)}

    pre = {"binding": _sha(binding), "blinded_receipt": _sha(receipt)}
    result["inputs_pre"] = pre
    result["binding_sha256_match"] = pre["binding"] == a.binding_sha256
    result["blinded_receipt_sha256_match"] = pre["blinded_receipt"] == a.blinded_receipt_sha256
    if not (result["binding_sha256_match"] and result["blinded_receipt_sha256_match"]):
        result["status"] = "INPUT_IDENTITY_MISMATCH__STOPPED"
        Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2

    sys.addaudithook(_hook)
    sys.path.insert(0, str(repo / "scripts" / "v5"))
    import td_relational_successor_disk_runner_v4 as D4  # noqa: E402
    import td_relational_successor_gate_v2 as G  # noqa: E402

    V3 = D4.V3
    result["loaded_modules"] = {
        name: os.path.normcase(os.path.abspath(mod.__file__))
        for name, mod in (("disk_runner_v4", D4), ("disk_runner_v3", V3), ("gate_v2", G))
    }

    sentinel = {"triggered": False}

    def _forbidden_controller_read(*_args, **_kwargs):
        sentinel["triggered"] = True
        raise AssertionError("controller truth read attempted during read-only preflight")

    V3._read_controller_json = _forbidden_controller_read

    try:
        package, fit, actual_sha = D4.authenticate_blinded_phase_inputs(
            repo_root=repo,
            binding_path=binding,
            authenticated_package_sha256=a.authenticated_package_sha256,
            blinded_receipt_path=receipt,
            expected_blinded_receipt_sha256=a.blinded_receipt_sha256,
        )
    except Exception as exc:  # recorded, not swallowed: status says REFUSED
        result["status"] = "READER_REFUSED"
        result["exception_type"] = type(exc).__name__
        result["exception_message"] = str(exc)
        result["exception_chain"] = traceback.format_exception_only(type(exc), exc)
        cause = exc.__cause__
        result["exception_cause"] = None if cause is None else f"{type(cause).__name__}: {cause}"
    else:
        doc = json.loads(receipt.read_text(encoding="utf-8"))
        raw_fit = doc["fit_receipt"]
        raw_orders = set()
        for prof in raw_fit["profiles"].values():
            raw_orders.add(tuple(prof["scale_results"]))
        for local in raw_fit["controls"].values():
            for prof in local.values():
                raw_orders.add(tuple(prof["scale_results"]))
        rebuilt_orders = set()
        for prof in fit.profiles.values():
            rebuilt_orders.add(tuple(prof.scale_results))
        for local in fit.controls.values():
            for prof in local.values():
                rebuilt_orders.add(tuple(prof.scale_results))
        reserialized = (
            json.dumps(
                V3._jsonable({**doc, "fit_receipt": fit}),
                sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            ) + "\n"
        ).encode("utf-8")
        file_bytes = receipt.read_bytes()
        result.update({
            "status": "READER_ACCEPTED",
            "authenticated_blinded_receipt_sha256": actual_sha,
            "package_id": package.package_id,
            "package_sha256": package.package_sha256,
            "n_challenges": len(package.fit_views),
            "n_primary_profiles": len(fit.profiles),
            "controls_per_challenge": sorted({len(v) for v in fit.controls.values()}),
            "n_control_profiles": sum(len(v) for v in fit.controls.values()),
            "raw_on_disk_scale_key_orders": sorted(list(o) for o in raw_orders),
            "reconstructed_scale_key_orders": sorted(list(o) for o in rebuilt_orders),
            "frozen_scale_labels": list(G.SCALE_LABELS),
            "fit_engine_identity_bound_in_receipt": doc["fit_engine_identity"],
            "fit_engine_identity_at_repo_root": D4.fit_engine_identity(repo),
            "fit_engine_identity_match": D4.fit_engine_identity(repo) == doc["fit_engine_identity"],
            "fit_receipt_authority": dict(fit.authority),
            "lossless_reserialization_byte_identical": reserialized == file_bytes,
            "reserialized_sha256": hashlib.sha256(reserialized).hexdigest(),
        })

    post = {"binding": _sha(binding), "blinded_receipt": _sha(receipt)}
    result["inputs_post"] = post
    result["inputs_unchanged"] = post == pre

    stdlib_roots = {os.path.normcase(os.path.abspath(p)) for p in {sys.prefix, sys.base_prefix, sys.exec_prefix}}
    accessed = sorted({p for _, p in _EVENTS if not any(p.startswith(r + os.sep) or p == r for r in stdlib_roots)})
    result["non_stdlib_paths_accessed"] = accessed
    result["forbidden_dir"] = forbidden
    result["forbidden_dir_accessed"] = any(p == forbidden or p.startswith(forbidden + os.sep) for _, p in _EVENTS)
    result["controller_read_sentinel_triggered"] = sentinel["triggered"]

    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "inputs_unchanged", "forbidden_dir_accessed")}))
    if sentinel["triggered"] or result["forbidden_dir_accessed"]:
        return 3
    return 0 if result["status"] == "READER_ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
