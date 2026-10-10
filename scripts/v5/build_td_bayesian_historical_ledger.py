#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

SUBSTRATE_FAMILY = "A_NATURAL_MIXTURE_25K"
PLANNED_STAGES = ("TD57B", "TD57C", "TD59")
TD57C_LINE = re.compile(
    r"-\s*split(?P<split>\d+)/half(?P<half>\d+)\s+observed\s+"
    r"(?P<observed>[-+0-9.eE]+);\s+null p95\s+(?P<null_p95>[-+0-9.eE]+)"
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def decorate_dependencies(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    stage = str(out["stage"])
    source = str(out["source"])
    panel = int(out["panel"])
    split = int(out["split"])
    half = int(out["half"])
    out.update(
        {
            "stage": stage,
            "source": source,
            "panel": panel,
            "split": split,
            "half": half,
            "substrate_family": SUBSTRATE_FAMILY,
            "substrate_source_root": f"{SUBSTRATE_FAMILY}::{source}",
            "stage_source_block": f"{stage}::{source}",
            "panel_dependency_root": f"{stage}::{source}::P{panel}",
            "case_identity": f"{stage}::{source}::P{panel}::S{split}::H{half}",
        }
    )
    return out


def parse_case_table(text: str, stage: str, source_path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    reader = csv.DictReader(text.splitlines())
    required = {"panel", "source", "split", "half", "observed", "null_p95"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise ValueError(f"case table missing required columns: {sorted(required)}")
    for raw in reader:
        observed = float(raw["observed"])
        comparator = float(raw["null_p95"])
        margin = float(raw["margin_p95"]) if raw.get("margin_p95") not in (None, "") else observed - comparator
        row = {
            "stage": stage,
            "source": raw["source"],
            "panel": int(raw["panel"]),
            "split": int(raw["split"]),
            "half": int(raw["half"]),
            "observed": observed,
            "comparator_name": "null_p95",
            "comparator_value": comparator,
            "margin": margin,
            "evidence_precision": "committed_case_table",
            "model_eligible": True,
            "source_path": source_path,
        }
        rows.append(decorate_dependencies(row))
    return rows


def parse_td57c_result_markdown(text: str, source_path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        m = TD57C_LINE.search(line)
        if not m:
            continue
        observed = float(m.group("observed"))
        comparator = float(m.group("null_p95"))
        row = {
            "stage": "TD57C",
            "source": "HVS",
            "panel": 0,
            "split": int(m.group("split")),
            "half": int(m.group("half")),
            "observed": observed,
            "comparator_name": "null_p95",
            "comparator_value": comparator,
            "margin": observed - comparator,
            "evidence_precision": "rounded_result_markdown_7dp",
            "model_eligible": False,
            "source_path": source_path,
        }
        rows.append(decorate_dependencies(row))
    if len(rows) != 4:
        raise ValueError(f"expected exactly four frozen TD57C HVS Panel-0 rows, found {len(rows)}")
    return rows


def aggregate_stage_source_blocks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        identity = str(row["case_identity"])
        if identity in seen:
            raise ValueError(f"duplicate case identity: {identity}")
        seen.add(identity)
        grouped[str(row["stage_source_block"])].append(row)

    blocks: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        margins = [float(x["margin"]) for x in members]
        med = statistics.median(margins)
        abs_dev = [abs(x - med) for x in margins]
        blocks.append(
            {
                "stage_source_block": key,
                "stage": members[0]["stage"],
                "source": members[0]["source"],
                "substrate_source_root": members[0]["substrate_source_root"],
                "n_related_cases": len(members),
                "effective_replication_units": 1,
                "block_margin_median": med,
                "block_margin_mad": statistics.median(abs_dev),
                "block_margin_min": min(margins),
                "block_margin_max": max(margins),
                "all_cases_model_eligible": all(bool(x.get("model_eligible", False)) for x in members),
                "panels": ";".join(str(x) for x in sorted({int(r["panel"]) for r in members})),
                "case_identities": ";".join(sorted(str(r["case_identity"]) for r in members)),
            }
        )
    return blocks


def build_receipt(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_td57c = [r for r in rows if r.get("stage") == "TD57C" and bool(r.get("model_eligible", False))]
    rounded_td57c = [r for r in rows if r.get("stage") == "TD57C" and not bool(r.get("model_eligible", False))]
    if rounded_td57c and not exact_td57c:
        status = "BLOCKED_EXACT_TD57C_CASE_VALUES_REQUIRED"
    else:
        status = "LEDGER_READY_FOR_SYNTHETIC_CALIBRATION__NO_HISTORICAL_FIT_YET"
    return {
        "schema": "JEPA_TD_BAYESIAN_HISTORICAL_LEDGER_RECEIPT_V1",
        "status": status,
        "planned_stages": list(PLANNED_STAGES),
        "case_rows": len(rows),
        "stage_source_blocks": len({r["stage_source_block"] for r in rows}),
        "historical_verdict_labels_used_for_fit": False,
        "corrected_replay_ingested": False,
        "target_ranking_allowed": False,
        "fit_authorized": False,
        "dependency_rule": "case rows collapse to one effective replication unit per stage×source; shared substrate_source_root links stages using the same source/substrate",
        "td57c_reporting_rule": "HVS-only until lawful additional-source evidence exists; source-general TD57C claims are not empirically replicated",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot write empty ledger")
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    root = args.repo_root
    b_path = root / "target_discovery/iterations/td57b_independent_triplet_recurrence/TD57B_CASE_TABLE.csv"
    c_path = root / "target_discovery/iterations/td57c_three_view_local_geometry/TD57C_RESULT.md"
    m_path = root / "target_discovery/iterations/td59_mesoscale_half_locality/TD59_CASE_TABLE.csv"
    b_text = b_path.read_text(encoding="utf-8")
    c_text = c_path.read_text(encoding="utf-8")
    m_text = m_path.read_text(encoding="utf-8")
    rows = []
    rows.extend(parse_case_table(b_text, "TD57B", str(b_path.relative_to(root))))
    rows.extend(parse_td57c_result_markdown(c_text, str(c_path.relative_to(root))))
    rows.extend(parse_case_table(m_text, "TD59", str(m_path.relative_to(root))))
    blocks = aggregate_stage_source_blocks(rows)
    receipt = build_receipt(rows)
    receipt["source_sha256"] = {
        "TD57B_CASE_TABLE.csv": sha256_text(b_text),
        "TD57C_RESULT.md": sha256_text(c_text),
        "TD59_CASE_TABLE.csv": sha256_text(m_text),
    }
    out = args.out_dir
    write_csv(out / "TD_BAYESIAN_HISTORICAL_CASE_LEDGER.csv", rows)
    write_csv(out / "TD_BAYESIAN_HISTORICAL_STAGE_SOURCE_BLOCKS.csv", blocks)
    (out / "TD_BAYESIAN_HISTORICAL_LEDGER_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": receipt["status"], "case_rows": len(rows), "blocks": len(blocks)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
