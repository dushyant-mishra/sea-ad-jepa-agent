from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile


MODULE_NAME = "jepa_post_td_harness_contract_v1"
if MODULE_NAME in sys.modules:
    C = sys.modules[MODULE_NAME]
else:
    module_path = Path(__file__).with_name(f"{MODULE_NAME}.py")
    spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    C = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = C
    spec.loader.exec_module(C)


class RehearsalPreflightError(ValueError):
    pass


def _read_json(path: Path | str) -> dict:
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise RehearsalPreflightError(f"required JSON input missing or symlinked: {p}")
    try:
        value = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RehearsalPreflightError(f"cannot read JSON input: {p}") from exc
    if not isinstance(value, dict):
        raise RehearsalPreflightError(f"JSON input must be an object: {p}")
    return value


def _write_json_write_once(path: Path | str, value: dict) -> None:
    target = Path(path)
    if target.exists() or target.is_symlink():
        raise RehearsalPreflightError(f"receipt already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp, target)
        try:
            directory_fd = os.open(target.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temp.exists():
            temp.unlink()


def run_preflight_from_paths(
    *,
    repo_root: Path | str,
    portfolio_path: Path | str,
    architecture_path: Path | str,
    synthetic_package_sha256: str,
    output_root: Path | str,
    receipt_path: Path | str,
) -> dict:
    portfolio = _read_json(portfolio_path)
    architecture = _read_json(architecture_path)
    receipt = C.build_synthetic_rehearsal_preflight(
        repo_root=repo_root,
        portfolio=portfolio,
        architecture_plan=architecture,
        synthetic_package_sha256=synthetic_package_sha256,
        output_root=output_root,
    )
    _write_json_write_once(receipt_path, receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a non-authorizing post-TD synthetic rehearsal preflight receipt"
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--portfolio", required=True)
    parser.add_argument("--architecture", required=True)
    parser.add_argument("--synthetic-package-sha256", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--receipt", required=True)
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    receipt = run_preflight_from_paths(
        repo_root=args.repo_root,
        portfolio_path=args.portfolio,
        architecture_path=args.architecture,
        synthetic_package_sha256=args.synthetic_package_sha256,
        output_root=args.output_root,
        receipt_path=args.receipt,
    )
    print(receipt["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
