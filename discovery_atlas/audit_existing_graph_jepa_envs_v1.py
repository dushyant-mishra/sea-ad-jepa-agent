"""Audit existing Graph-JEPA conda environments for v3 runtime planning.

This script is intentionally read-only with respect to Python environments:
it does not create environments, install packages, train models, or run
benchmarks. It imports requested packages in the current interpreter and in
project-related conda environments, then writes a compact CSV and two Markdown
reports for environment selection.
"""

from __future__ import annotations

import csv
import json
import os
import platform
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "results" / "tables" / "existing_graph_jepa_env_package_audit_v1.csv"
REPORT_PATH = ROOT / "results" / "reports" / "existing_graph_jepa_env_package_audit_v1.md"
RECOMMENDATION_PATH = (
    ROOT / "results" / "reports" / "existing_graph_jepa_env_selection_recommendation_v1.md"
)


PACKAGE_CHECKS = [
    ("numpy", "numpy", "core_scientific", "yes"),
    ("pandas", "pandas", "core_scientific", "yes"),
    ("scipy", "scipy", "core_scientific", "yes"),
    ("sklearn", "sklearn", "core_scientific", "yes"),
    ("networkx", "networkx", "graph_runtime", "yes"),
    ("matplotlib", "matplotlib", "reporting", "baseline_only"),
    ("statsmodels", "statsmodels", "statistics", "baseline_only"),
    ("pyarrow", "pyarrow", "data_io", "baseline_only"),
    ("h5py", "h5py", "data_io", "baseline_only"),
    ("anndata", "anndata", "single_cell_io", "baseline_only"),
    ("scanpy", "scanpy", "single_cell_analysis", "baseline_only"),
    ("torch", "torch", "v3_neural_model", "yes"),
    ("torch_geometric", "torch_geometric", "v3_graph_model", "yes"),
    ("umap", "umap", "manifold_baseline", "baseline_only"),
    ("openTSNE", "openTSNE", "manifold_baseline", "baseline_only"),
    ("phate", "phate", "manifold_baseline", "baseline_only"),
    ("pydiffmap", "pydiffmap", "manifold_baseline", "baseline_only"),
    ("scvi", "scvi", "optional_single_cell_model", "no"),
    ("xgboost", "xgboost", "boosting_baseline", "baseline_only"),
    ("lightgbm", "lightgbm", "boosting_baseline", "baseline_only"),
    ("dowhy", "dowhy", "causal_optional", "baseline_only"),
    ("econml", "econml", "causal_optional", "baseline_only"),
]


PROJECT_IMPORT_CHECKS = [
    ("sea_ad_jepa", "src_package_import", "v2_runtime_code", "yes"),
    ("sea_ad_jepa.graph_jepa", "graph_jepa_module_import", "v2_runtime_code", "yes"),
]


AUDIT_CODE = r"""
import importlib
import json
import platform
import sys
from pathlib import Path

root = Path.cwd()
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

checks = __CHECKS__
project_checks = __PROJECT_CHECKS__
rows = []

for package_name, import_name, needed_for_v3, blocking_if_missing in checks:
    row = {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "package_name": package_name,
        "import_name": import_name,
        "available": False,
        "version": "",
        "cuda_available_if_torch": "",
        "needed_for_v3": needed_for_v3,
        "blocking_if_missing": blocking_if_missing,
        "notes": "",
    }
    try:
        mod = importlib.import_module(import_name)
        row["available"] = True
        row["version"] = str(getattr(mod, "__version__", "unknown"))
        if package_name == "torch":
            cuda_available = bool(mod.cuda.is_available())
            row["cuda_available_if_torch"] = str(cuda_available)
            cuda_version = getattr(mod.version, "cuda", None)
            gpu_name = ""
            if cuda_available:
                try:
                    gpu_name = mod.cuda.get_device_name(0)
                except Exception as exc:
                    gpu_name = f"gpu_name_error={type(exc).__name__}: {exc}"
            row["notes"] = f"torch_cuda={cuda_version}; gpu={gpu_name}".strip()
    except Exception as exc:
        row["notes"] = f"{type(exc).__name__}: {str(exc)[:240]}"
    rows.append(row)

for import_name, package_name, needed_for_v3, blocking_if_missing in project_checks:
    row = {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "package_name": package_name,
        "import_name": import_name,
        "available": False,
        "version": "",
        "cuda_available_if_torch": "",
        "needed_for_v3": needed_for_v3,
        "blocking_if_missing": blocking_if_missing,
        "notes": "",
    }
    try:
        importlib.import_module(import_name)
        row["available"] = True
        row["version"] = "import_ok"
    except Exception as exc:
        row["notes"] = f"{type(exc).__name__}: {str(exc)[:240]}"
    rows.append(row)

print(json.dumps(rows))
"""


@dataclass
class EnvSpec:
    name: str
    path: str
    command_prefix: list[str]


def run_command(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:  # pragma: no cover - defensive runtime capture
        return 999, "", f"{type(exc).__name__}: {exc}"


def parse_conda_envs() -> list[EnvSpec]:
    code, out, err = run_command(["conda", "env", "list"], timeout=60)
    envs: list[EnvSpec] = []
    if code != 0:
        print(f"WARNING: conda env list failed: {err}")
    for line in out.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        if parts[1] == "*":
            name = parts[0]
            path = parts[2] if len(parts) > 2 else ""
        else:
            name = parts[0]
            path = parts[1]
        if name == "base":
            envs.append(EnvSpec(name="base_current", path=path, command_prefix=[sys.executable]))
        elif any(token in name.lower() for token in ("sea-ad", "jepa", "graph")):
            envs.append(
                EnvSpec(name=name, path=path, command_prefix=["conda", "run", "-n", name, "python"])
            )
    if not any(env.name == "base_current" for env in envs):
        envs.insert(0, EnvSpec(name="base_current", path="", command_prefix=[sys.executable]))
    return envs


def audit_env(env: EnvSpec) -> list[dict[str, str]]:
    code = AUDIT_CODE.replace("__CHECKS__", repr(PACKAGE_CHECKS)).replace(
        "__PROJECT_CHECKS__", repr(PROJECT_IMPORT_CHECKS)
    )
    payload_path = Path(tempfile.gettempdir()) / f"graph_jepa_env_audit_{env.name}.py"
    payload_path.write_text(code, encoding="utf-8")
    try:
        rc, out, err = run_command(env.command_prefix + [str(payload_path)], timeout=180)
    finally:
        try:
            payload_path.unlink()
        except FileNotFoundError:
            pass
    if rc != 0:
        rows = []
        for package_name, import_name, needed_for_v3, blocking_if_missing in PACKAGE_CHECKS:
            rows.append(
                {
                    "env_name": env.name,
                    "python_executable": "",
                    "python_version": "",
                    "package_name": package_name,
                    "import_name": import_name,
                    "available": "False",
                    "version": "",
                    "cuda_available_if_torch": "",
                    "needed_for_v3": needed_for_v3,
                    "blocking_if_missing": blocking_if_missing,
                    "notes": f"audit_failed rc={rc}; {err[:240]}",
                }
            )
        return rows
    json_line = out.splitlines()[-1] if out else "[]"
    parsed = json.loads(json_line)
    for row in parsed:
        row["env_name"] = env.name
        row["available"] = str(bool(row["available"]))
    return parsed


def package_lookup(rows: list[dict[str, str]], env_name: str, package: str) -> dict[str, str]:
    for row in rows:
        if row["env_name"] == env_name and row["package_name"] == package:
            return row
    return {}


def is_available(rows: list[dict[str, str]], env_name: str, package: str) -> bool:
    row = package_lookup(rows, env_name, package)
    return str(row.get("available", "")).lower() == "true"


def missing_packages(rows: list[dict[str, str]], env_name: str) -> list[str]:
    return [
        row["package_name"]
        for row in rows
        if row["env_name"] == env_name
        and row["package_name"] in {p[0] for p in PACKAGE_CHECKS}
        and str(row["available"]).lower() != "true"
    ]


def choose_recommendation(rows: list[dict[str, str]], env_names: list[str]) -> tuple[str, str]:
    if "sea-ad-jepa" not in env_names:
        return (
            "create fresh `sea-ad-jepa-v3`",
            "`sea-ad-jepa` was not found, so there is no confirmed v2 runtime to clone.",
        )
    has_torch = is_available(rows, "sea-ad-jepa", "torch")
    has_project = is_available(rows, "sea-ad-jepa", "src_package_import") and is_available(
        rows, "sea-ad-jepa", "graph_jepa_module_import"
    )
    missing = set(missing_packages(rows, "sea-ad-jepa"))
    optional_missing = {
        "anndata",
        "scanpy",
        "umap",
        "openTSNE",
        "phate",
        "pydiffmap",
        "scvi",
        "xgboost",
        "lightgbm",
        "dowhy",
        "econml",
    }
    if has_torch and has_project:
        if missing and missing.issubset(optional_missing | {"torch_geometric"}):
            return (
                "clone `sea-ad-jepa` to `sea-ad-jepa-v3`, then install missing v3 optional/baseline packages into the clone",
                "`sea-ad-jepa` imports torch and project runtime code, so it is the safest continuity base.",
            )
        return (
            "clone `sea-ad-jepa` to `sea-ad-jepa-v3`",
            "`sea-ad-jepa` already has the core v2 runtime and should preserve training compatibility.",
        )
    if not has_torch or not has_project:
        return (
            "create fresh `sea-ad-jepa-v3`",
            "`sea-ad-jepa` is missing torch or cannot import the lightweight project runtime checks.",
        )
    return (
        "use current `sea-ad-jepa`",
        "`sea-ad-jepa` appears complete, but cloning remains safer for v3 changes.",
    )


def write_csv(rows: list[dict[str, str]]) -> None:
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "env_name",
        "python_executable",
        "python_version",
        "package_name",
        "import_name",
        "available",
        "version",
        "cuda_available_if_torch",
        "needed_for_v3",
        "blocking_if_missing",
        "notes",
    ]
    with TABLE_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_reports(envs: list[EnvSpec], rows: list[dict[str, str]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    env_names = [env.name for env in envs]
    recommendation, rationale = choose_recommendation(rows, env_names)
    sea_missing = missing_packages(rows, "sea-ad-jepa") if "sea-ad-jepa" in env_names else []
    v3_presence_note = (
        "`sea-ad-jepa-v3` was already present at audit time. It should not be treated as the historical v2 runtime; use the `sea-ad-jepa` rows to decide whether cloning preserves continuity."
        if "sea-ad-jepa-v3" in env_names
        else "`sea-ad-jepa-v3` was not present at audit time."
    )

    def yn(env: str, package: str) -> str:
        return "yes" if is_available(rows, env, package) else "no"

    summary_lines = []
    for env in envs:
        available = sum(
            1
            for row in rows
            if row["env_name"] == env.name
            and row["package_name"] in {p[0] for p in PACKAGE_CHECKS}
            and str(row["available"]).lower() == "true"
        )
        total = len(PACKAGE_CHECKS)
        py_row = next((row for row in rows if row["env_name"] == env.name), {})
        summary_lines.append(
            f"| {env.name} | {py_row.get('python_version', '')} | {available}/{total} | {env.path} |"
        )

    package_lines = []
    focus_packages = [
        "torch",
        "torch_geometric",
        "scanpy",
        "anndata",
        "umap",
        "phate",
        "dowhy",
        "econml",
    ]
    for env in envs:
        for pkg in focus_packages:
            row = package_lookup(rows, env.name, pkg)
            package_lines.append(
                f"| {env.name} | {pkg} | {row.get('available', '')} | {row.get('version', '')} | {row.get('notes', '')} |"
            )

    REPORT_PATH.write_text(
        "\n".join(
            [
                "# Existing Graph-JEPA environment package audit v1",
                "",
                "This audit is read-only: no package installs, model training, benchmarks, evidence-level changes, or external validation were run by this script.",
                "",
                "## Existing environments audited",
                "",
                "| env_name | python_version | requested packages available | path |",
                "|---|---:|---:|---|",
                *summary_lines,
                "",
                "## V2 training environment",
                "",
                "`sea-ad-jepa` is treated as the v2 training/runtime environment because prior project commands used `conda run -n sea-ad-jepa ...`.",
                "",
                "## Focus package availability",
                "",
                "| env_name | package | available | version | notes |",
                "|---|---|---:|---|---|",
                *package_lines,
                "",
                "## `sea-ad-jepa` key checks",
                "",
                f"- torch available: {yn('sea-ad-jepa', 'torch') if 'sea-ad-jepa' in env_names else 'env missing'}",
                f"- torch_geometric available: {yn('sea-ad-jepa', 'torch_geometric') if 'sea-ad-jepa' in env_names else 'env missing'}",
                f"- scanpy available: {yn('sea-ad-jepa', 'scanpy') if 'sea-ad-jepa' in env_names else 'env missing'}",
                f"- anndata available: {yn('sea-ad-jepa', 'anndata') if 'sea-ad-jepa' in env_names else 'env missing'}",
                f"- lightweight `sea_ad_jepa` import available: {yn('sea-ad-jepa', 'src_package_import') if 'sea-ad-jepa' in env_names else 'env missing'}",
                f"- lightweight `sea_ad_jepa.graph_jepa` import available: {yn('sea-ad-jepa', 'graph_jepa_module_import') if 'sea-ad-jepa' in env_names else 'env missing'}",
                "",
                "## Missing packages from `sea-ad-jepa`",
                "",
                ", ".join(sea_missing) if sea_missing else "None among requested checks.",
                "",
                "## Recommendation",
                "",
                f"Recommended strategy: {recommendation}.",
                "",
                f"Rationale: {rationale}",
                "",
                "Stage 23 availability checks using the current/base interpreter should not be treated as the true project runtime if they did not use `conda run -n sea-ad-jepa`.",
                "",
                "## Note on `sea-ad-jepa-v3` presence",
                "",
                v3_presence_note,
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    install_lines = []
    if "sea-ad-jepa" in env_names:
        for pkg in sea_missing:
            install_lines.append(f"- Install or validate `{pkg}` only after cloning/choosing the target v3 environment.")
    if not install_lines:
        install_lines.append("- No missing requested packages were detected in `sea-ad-jepa`.")

    RECOMMENDATION_PATH.write_text(
        "\n".join(
            [
                "# Existing Graph-JEPA environment selection recommendation v1",
                "",
                f"Recommendation: {recommendation}.",
                "",
                f"Rationale: {rationale}",
                "",
                "## Exact install strategy",
                "",
                "Do not install into `base/current`. Prefer preserving the existing v2 runtime lineage.",
                "",
                *install_lines,
                "",
                "If cloning is selected, clone `sea-ad-jepa` first and install only missing v3 optional/baseline packages into the clone. If a fresh environment is selected, recreate the core v2 neural stack before adding optional benchmark packages.",
                "",
                "## Boundaries",
                "",
                "- No training was run.",
                "- No benchmarks were run.",
                "- No external validation was run.",
                "- No evidence levels or conclusions were modified.",
                "- This audit did not install packages.",
                f"- {v3_presence_note}",
                "- Note: `sea-ad-jepa-v3` is included if present, but selection is based on audited compatibility rather than assuming the current/base interpreter represented the project runtime.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    envs = parse_conda_envs()
    rows: list[dict[str, str]] = []
    for env in envs:
        rows.extend(audit_env(env))
    write_csv(rows)
    write_reports(envs, rows)
    print(f"Wrote {TABLE_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {RECOMMENDATION_PATH}")


if __name__ == "__main__":
    main()
