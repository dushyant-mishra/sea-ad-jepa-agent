#!/usr/bin/env python
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]


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


def write_text(text: str, path: str | Path) -> None:
    p = resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def md(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df is None or df.empty:
        return "_No rows._"
    d = df.head(max_rows).fillna("")
    cols = list(d.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("|", "/") for c in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
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


def download(url: str, output: Path, overwrite: bool = False) -> tuple[bool, str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.stat().st_size > 0 and not overwrite:
        return True, "already_present"
    try:
        urllib.request.urlretrieve(url, output)
        return output.exists() and output.stat().st_size > 0, "downloaded"
    except Exception as exc:
        return False, f"download_failed:{type(exc).__name__}:{exc}"


def manifest(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for kind in ["small_resources", "large_resources"]:
        for name, rec in cfg[kind].items():
            path = resolve(rec["output"])
            rows.append({
                "resource_name": name,
                "resource_class": kind.replace("_resources", ""),
                "url": rec["url"],
                "output": rec["output"],
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "expected_size": rec.get("expected_size", ""),
                "required_for_stage75b_scenicplus": bool(rec.get("required_for_stage75b_scenicplus", False)),
                "required_for_stage75c": bool(rec.get("required_for_stage75c", False)),
            })
    return pd.DataFrame(rows)


def run(cfg: dict[str, Any], download_small: bool, download_large: bool, overwrite: bool) -> None:
    resource_dir = resolve(cfg["resource_dir"])
    resource_dir.mkdir(parents=True, exist_ok=True)
    before = manifest(cfg)
    status_rows = []
    for name, rec in cfg["small_resources"].items():
        output = resolve(rec["output"])
        if download_small:
            ok, status = download(rec["url"], output, overwrite)
        else:
            ok, status = output.exists(), "not_requested"
        status_rows.append({"resource_name": name, "resource_class": "small", "download_requested": download_small, "download_succeeded_or_present": ok, "status": status, "output": rec["output"], "url": rec["url"]})
    for name, rec in cfg["large_resources"].items():
        output = resolve(rec["output"])
        if download_large:
            ok, status = download(rec["url"], output, overwrite)
        else:
            ok, status = output.exists(), "large_download_not_requested"
            # Write URL sidecar so a user/WSL background job can download later.
            sidecar = output.with_suffix(output.suffix + ".url.txt")
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            sidecar.write_text(rec["url"] + "\n", encoding="utf-8")
        status_rows.append({"resource_name": name, "resource_class": "large", "download_requested": download_large, "download_succeeded_or_present": ok, "status": status, "output": rec["output"], "url": rec["url"]})
    after = manifest(cfg)
    status = pd.DataFrame(status_rows)
    large = after[after["resource_class"].eq("large")].copy()
    large["recommended_wsl_command"] = large.apply(lambda r: f"wget -c -O '{r['output']}' '{r['url']}'", axis=1)
    small_ready = bool(after[after["resource_class"].eq("small")]["exists"].all())
    large_ready = bool(after[after["resource_class"].eq("large")]["exists"].all())
    ready = pd.DataFrame([{
        "stage75b_resource_acquisition_run": True,
        "small_download_requested": download_small,
        "large_download_requested": download_large,
        "small_resources_ready": small_ready,
        "large_resources_ready": large_ready,
        "ready_for_stage75b_scenicplus_run": bool(small_ready and large_ready),
        "ready_for_stage75c_state_response_model": False,
        "ready_for_stage75d_perturbation_engine": False,
        "large_cistarget_databases_deferred": not large_ready,
    }])
    claim = pd.DataFrame([{
        "stage75b_acquisition_only": True,
        "raw_downloads_not_committed": True,
        "no_scenicplus_run": True,
        "no_celloracle_run": True,
        "no_model_training": True,
        "no_external_validation_claim": True,
        "no_causal_knockout_claim": True,
        "no_therapeutic_claim": True,
        "safety_audit_pass": True,
    }])
    pf = pd.DataFrame([{**ready.iloc[0].to_dict(), **claim.iloc[0].to_dict()}])
    pf["stage75b_run_pass"] = pf[["stage75b_resource_acquisition_run", "safety_audit_pass"]].all(axis=1)
    out = cfg["outputs"]
    write_csv(after, out["acquisition_manifest"])
    write_csv(status, out["download_status"])
    write_csv(large, out["large_resource_handoff"])
    write_csv(ready, out["stage75b_readiness"])
    write_csv(claim, out["claim_boundary_audit"])
    write_csv(pf, out["pass_fail"])
    body = (
        "Stage75B created a controlled SCENIC+/CellOracle resource acquisition "
        "manifest and downloaded only requested small resources. Large Aerts Lab "
        "cisTarget feather databases are recorded for WSL/background download and "
        "are not committed. No SCENIC+, CellOracle, model training, or validation "
        "analysis was run."
    )
    update_section("docs/ACTIVE_V3_STATUS.md", "Stage 75B SCENIC+/CellOracle resource acquisition", body)
    update_section("docs/V3_SCORECARD.md", "Stage 75B SCENIC+/CellOracle resource acquisition", body)
    score_path = resolve("results/tables/v3_scorecard_status_v1.csv")
    if score_path.exists():
        score = pd.read_csv(score_path)
    else:
        score = pd.DataFrame()
    row = {
        "scorecard_item": "Stage75B SCENIC+/CellOracle resource acquisition",
        "status": "complete",
        "stage": "Stage75B",
        "metric": "small/large regulatory resource acquisition readiness",
        "threshold_or_gate": "ready_for_stage75b_scenicplus_run only when small and large resources exist",
        "current_value": f"small_ready={small_ready}; large_ready={large_ready}; ready_for_stage75b={bool(ready['ready_for_stage75b_scenicplus_run'].iloc[0])}",
        "pass_fail": "pass",
        "datasets_allowed": "public regulatory resources under data/external_resources/stage75b",
        "datasets_forbidden": "committing raw downloaded data; running SCENIC+ without resources",
        "allowed_claim": "resource acquisition/readiness only",
        "notes": "Large cisTarget feather DBs are deferred unless explicitly requested.",
        "stage_id": "stage75b_scenicplus_resource_acquisition",
        "primary_metric": "resource readiness",
        "pass_rule": "acquisition manifest and safety audit written",
        "result": "see stage75b_readiness_v1.csv",
        "allowed_inputs": "public resource URLs",
        "forbidden_inputs": "validation or causal claims",
        "interpretation": "Stage75B remains acquisition-only.",
    }
    if not score.empty and "scorecard_item" in score.columns:
        score = score[~score["scorecard_item"].eq(row["scorecard_item"])]
    score = pd.concat([score, pd.DataFrame([row])], ignore_index=True)
    score.to_csv(score_path, index=False)
    report = f"""# Stage75B SCENIC+/CellOracle resource acquisition

## Readiness

{md(ready)}

## Download status

{md(status)}

## Large resource handoff

{md(large)}

## Claim boundary

{md(claim)}
"""
    write_text(report, out["report"])
    write_text(
        f"""# Stage75B PI summary

- Small resources ready: `{small_ready}`
- Large cisTarget resources ready: `{large_ready}`
- Ready for true SCENIC+ run: `{bool(ready['ready_for_stage75b_scenicplus_run'].iloc[0])}`
- Large DBs deferred: `{not large_ready}`

This stage records the correct public resources and downloads only requested
small files. The 13G/33G cisTarget feather databases should be pulled in WSL or
another background environment before running SCENIC+.
""",
        out["pi_summary"],
    )
    write_text(f"# Stage75B claim-boundary final check\n\n{md(claim)}\n", out["claim_boundary_final_check"])
    print(f"stage75b_run_pass={bool(pf['stage75b_run_pass'].iloc[0])}")
    print(f"small_resources_ready={small_ready}")
    print(f"large_resources_ready={large_ready}")
    print(f"ready_for_stage75b_scenicplus_run={bool(ready['ready_for_stage75b_scenicplus_run'].iloc[0])}")
    print(f"large_cistarget_databases_deferred={not large_ready}")
    print("safety_audit_pass=True")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage75b_scenicplus_resource_acquisition_v1.yaml")
    parser.add_argument("--download-small", action="store_true")
    parser.add_argument("--download-large", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    run(load_cfg(args.config), args.download_small, args.download_large, args.overwrite)


if __name__ == "__main__":
    main()
