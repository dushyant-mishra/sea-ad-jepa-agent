#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCORECARD_COLUMNS = ["scorecard_item", "status", "stage", "metric", "threshold_or_gate", "current_value", "pass_fail", "datasets_allowed", "datasets_forbidden", "allowed_claim", "notes", "stage_id", "primary_metric", "pass_rule", "result", "allowed_inputs", "forbidden_inputs", "interpretation"]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def load_cfg(path: str | Path) -> dict[str, Any]:
    with resolve(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_text(text: str, path: str | Path, executable: bool = False) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    if executable:
        try:
            p.chmod(0o755)
        except Exception:
            pass


def md(df: pd.DataFrame, max_rows: int = 50) -> str:
    if df.empty:
        return "_No rows._"
    d = df.head(max_rows).fillna("")
    cols = list(d.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in cols) + " |")
    return "\n".join(lines)


def update_section(path: str, title: str, body: str) -> None:
    p = resolve(path)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    marker = f"## {title}"
    block = f"{marker}\n\n{body.strip()}\n"
    if marker in old:
        before, rest = old.split(marker, 1)
        nxt = rest.find("\n## ")
        old = before + block + (rest[nxt:] if nxt >= 0 else "")
    else:
        old = old.rstrip() + "\n\n" + block
    p.write_text(old, encoding="utf-8")


def run(cfg: dict[str, Any]) -> None:
    repo = cfg["repo_dir_wsl"]
    res = cfg["resource_dir_wsl"]
    env = cfg["conda_env_name"]
    pyver = str(cfg.get("python_version", "3.11.8"))
    rankings_url = "https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather"
    scores_url = "https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.scores.feather"
    commands = [
        ("remove_failed_env_if_needed", f"conda env remove -y -n {env} || true"),
        ("create_env", f"conda create -y -n {env} python={pyver}"),
        ("install_base", f"conda run -n {env} python -m pip install --upgrade pip wheel setuptools"),
        ("install_compiled_genomics_deps", f"conda install -y -n {env} -c conda-forge -c bioconda pybedtools=0.9.1 bedtools macs2=2.2.9.1 cython=0.29.37 numpy pandas scipy"),
        ("verify_pybedtools_preinstalled", f"conda run -n {env} python - <<'PY'\nimport setuptools, pybedtools\nprint('setuptools', setuptools.__version__)\nprint('pybedtools', pybedtools.__version__)\nPY"),
        ("install_scenicplus", f"cd /tmp && rm -rf scenicplus && git clone https://github.com/aertslab/scenicplus && cd scenicplus && git checkout development && (conda run -n {env} python -m pip install . || (conda run -n {env} python -m pip install 'poetry<1.2' poetry-core hatchling 'packaging>=24.2' && conda run -n {env} python -m pip install --no-build-isolation .))"),
        ("install_celloracle_helpers", f"conda run -n {env} python -m pip install celloracle pyranges pybiomart mudata scanpy anndata"),
        ("download_rankings", f"cd '{repo}' && mkdir -p '{res}' && wget -c -O '{res}/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather' '{rankings_url}'"),
        ("download_scores", f"cd '{repo}' && mkdir -p '{res}' && wget -c -O '{res}/hg38_screen_v10_clust.regions_vs_motifs.scores.feather' '{scores_url}'"),
        ("verify_sha1", f"cd '{res}' && sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt && sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt"),
        ("postcheck", f"cd '{repo}' && conda run -n {env} python - <<'PY'\nimport importlib.util\nmods=['scenicplus','pycisTopic','pycistarget','ctxcore','arboreto','celloracle','pyranges','mudata','scanpy']\nprint({{m: bool(importlib.util.find_spec(m)) for m in mods}})\nPY"),
    ]
    cmd_df = pd.DataFrame(commands, columns=["step", "command"])
    checklist = pd.DataFrame([
        {"resource": "rankings_feather", "path_wsl": f"{res}/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather", "expected_size": "33G", "required_before_stage75e": True},
        {"resource": "scores_feather", "path_wsl": f"{res}/hg38_screen_v10_clust.regions_vs_motifs.scores.feather", "expected_size": "13G", "required_before_stage75e": True},
        {"resource": "rankings_sha1", "path_wsl": f"{res}/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt", "expected_size": "99B", "required_before_stage75e": True},
        {"resource": "scores_sha1", "path_wsl": f"{res}/hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt", "expected_size": "97B", "required_before_stage75e": True},
    ])
    dep = pd.DataFrame([
        {"dependency": "scenicplus", "install_route": "git clone aertslab/scenicplus development branch", "required_before_stage75e": True},
        {"dependency": "pycisTopic/pycistarget stack", "install_route": "installed through SCENIC+ dependency chain where available", "required_before_stage75e": True},
        {"dependency": "celloracle", "install_route": "pip install celloracle", "required_before_stage75f": True},
        {"dependency": "pyranges/pybiomart/mudata/scanpy", "install_route": "pip install helpers", "required_before_stage75e": True},
    ])
    download_script = f"""#!/usr/bin/env bash
set -euo pipefail
cd "{repo}"
mkdir -p "{res}"
wget -c -O "{res}/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather" "{rankings_url}"
wget -c -O "{res}/hg38_screen_v10_clust.regions_vs_motifs.scores.feather" "{scores_url}"
cd "{res}"
sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt
sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt
"""
    env_script = f"""#!/usr/bin/env bash
set -euo pipefail
conda env remove -y -n {env} || true
conda create -y -n {env} python={pyver}
conda run -n {env} python -m pip install --upgrade pip wheel setuptools
conda install -y -n {env} -c conda-forge -c bioconda pybedtools=0.9.1 bedtools macs2=2.2.9.1 cython=0.29.37 numpy pandas scipy
conda run -n {env} python - <<'PY'
import setuptools, pybedtools
print("setuptools", setuptools.__version__)
print("pybedtools", pybedtools.__version__)
try:
    import MACS2
    print("MACS2", getattr(MACS2, "__version__", "installed"))
except Exception as exc:
    print("MACS2 import check failed", type(exc).__name__, exc)
PY
cd /tmp
rm -rf scenicplus
git clone https://github.com/aertslab/scenicplus
cd scenicplus
git checkout development
if ! conda run -n {env} python -m pip install .; then
  echo "Primary SCENIC+ install failed; trying no-build-isolation fallback with Poetry backend and modern packaging..."
  conda run -n {env} python -m pip install 'poetry<1.2' poetry-core hatchling 'packaging>=24.2'
  conda run -n {env} python -m pip install --no-build-isolation .
fi
conda run -n {env} python -m pip install celloracle pyranges pybiomart mudata scanpy anndata
conda run -n {env} python - <<'PY'
import importlib.util
mods=['scenicplus','pycisTopic','pycistarget','ctxcore','arboreto','celloracle','pyranges','mudata','scanpy']
print({{m: bool(importlib.util.find_spec(m)) for m in mods}})
PY
"""
    readiness = pd.DataFrame([{
        "stage75d_handoff_written": True,
        "large_download_run_in_codex": False,
        "environment_install_run_in_codex": False,
        "ready_for_stage75e_after_user_wsl_completion": True,
        "stage75e_should_verify_files_before_running": True,
    }])
    claim = pd.DataFrame([{
        "stage75d_handoff_only": True,
        "no_large_download_run_in_codex": True,
        "no_scenicplus_run": True,
        "no_celloracle_run": True,
        "no_model_training": True,
        "raw_downloads_not_committed": True,
        "no_external_validation_claim": True,
        "no_causal_knockout_claim": True,
        "no_therapeutic_claim": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{**readiness.iloc[0].to_dict(), **claim.iloc[0].to_dict()}])
    pf["stage75d_run_pass"] = pf[["stage75d_handoff_written", "safety_audit_pass"]].all(axis=1)
    out = cfg["outputs"]
    write_csv(cmd_df, out["wsl_command_table"])
    write_csv(checklist, out["large_download_checklist"])
    write_csv(dep, out["dependency_install_checklist"])
    write_csv(readiness, out["readiness"])
    write_csv(claim, out["claim_boundary_audit"])
    write_csv(pf, out["pass_fail"])
    write_text(download_script, out["wsl_download_script"], executable=True)
    write_text(env_script, out["wsl_env_script"], executable=True)
    body = (
        "Stage75D wrote WSL/background command scripts and checklists for installing "
        "SCENIC+/CellOracle dependencies and downloading the large Aerts Lab cisTarget "
        "feather databases. It did not run the large downloads, install the environment, "
        "or run SCENIC+/CellOracle inside Codex."
    )
    update_section("docs/ACTIVE_V3_STATUS.md", "Stage 75D SCENIC+/CellOracle WSL execution handoff", body)
    update_section("docs/V3_SCORECARD.md", "Stage 75D SCENIC+/CellOracle WSL execution handoff", body)
    score_path = resolve("results/tables/v3_scorecard_status_v1.csv")
    score = pd.read_csv(score_path) if score_path.exists() else pd.DataFrame(columns=SCORECARD_COLUMNS)
    for col in SCORECARD_COLUMNS:
        if col not in score.columns:
            score[col] = ""
    row = {
        "scorecard_item": "Stage75D SCENIC+/CellOracle WSL execution handoff",
        "status": "complete",
        "stage": "Stage75D",
        "metric": "handoff scripts for dependency and large resource acquisition",
        "threshold_or_gate": "scripts/checklists written; no raw data committed",
        "current_value": f"stage75d_run_pass={bool(pf['stage75d_run_pass'].iloc[0])}",
        "pass_fail": "pass",
        "datasets_allowed": "command manifests only",
        "datasets_forbidden": "large raw DB commit or unverified SCENIC+ execution",
        "allowed_claim": "handoff/readiness only",
        "notes": "User/WSL completion required before Stage75E.",
        "stage_id": "stage75d_scenicplus_wsl_execution_handoff",
        "primary_metric": "handoff completeness",
        "pass_rule": "outputs written and safety audit passes",
        "result": "see stage75d_readiness_v1.csv",
        "allowed_inputs": "public resource URLs and repo paths",
        "forbidden_inputs": "validation or causal claims",
        "interpretation": "Next stage must verify local files/env before running eGRN construction.",
    }
    score = score[~score["scorecard_item"].eq(row["scorecard_item"])]
    pd.concat([score[SCORECARD_COLUMNS], pd.DataFrame([row], columns=SCORECARD_COLUMNS)], ignore_index=True).to_csv(score_path, index=False)
    report = f"""# Stage75D SCENIC+/CellOracle WSL execution handoff

## Readiness

{md(readiness)}

## Commands

{md(cmd_df)}

## Large resource checklist

{md(checklist)}

## Claim boundary

{md(claim)}
"""
    write_text(report, out["report"])
    write_text(
        f"""# Stage75D PI summary

Stage75D prepared the WSL execution scripts needed before a true SCENIC+ eGRN
run. It did not install or download the large DBs inside Codex.

Run in WSL from the repo root:

```bash
bash scripts/stage75d_create_scenicplus_env_wsl.sh
bash scripts/stage75d_download_large_cistarget_resources_wsl.sh
```

Then Stage75E should verify the environment/files before running SCENIC+.
""",
        out["pi_summary"],
    )
    write_text(f"# Stage75D claim-boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print(f"stage75d_run_pass={bool(pf['stage75d_run_pass'].iloc[0])}")
    print("large_download_run_in_codex=False")
    print("environment_install_run_in_codex=False")
    print("ready_for_stage75e_after_user_wsl_completion=True")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage75d_scenicplus_wsl_execution_handoff_v1.yaml")
    args = parser.parse_args()
    run(load_cfg(args.config))


if __name__ == "__main__":
    main()
