#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PASS = "PASS_TEACHER_STUDENT_V5_PROPOSAL_HORIZON_GATE_V1__TRAINING_UNAUTHORIZED"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def main() -> int:
    manifest = ROOT / "docs/agent/TEACHER_STUDENT_V5_PROPOSAL_HORIZON_GATE_MANIFEST.csv"
    root = ROOT / "docs/agent/TEACHER_STUDENT_V5_PROPOSAL_HORIZON_GATE_ROOT.txt"
    with manifest.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    require(rows and len(rows) == len({r["path"] for r in rows}), "gate manifest empty/duplicate")
    for row in rows:
        p = ROOT / row["path"]
        require(p.is_file(), f"missing gate payload {p}")
        require(int(row["bytes"]) == p.stat().st_size, f"byte-size drift {p}")
        require(row["sha256"] == sha256(p), f"SHA drift {p}")
    require(root.read_text().strip() == sha256(manifest), "gate root does not bind manifest bytes")

    horizon_path = ROOT / "docs/agent/TEACHER_STUDENT_V5_PRESENTATION_HORIZON_AUTHORITY_V1.json"
    proposal_path = ROOT / "docs/agent/TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V3.json"
    counts_path = ROOT / "docs/agent/READER_FIT_DONOR_OPERATOR_COUNTS_V1.csv.gz.b64"
    horizon = json.loads(horizon_path.read_text())
    proposal = json.loads(proposal_path.read_text())

    require(horizon["total_presentations"] == 4553407, "horizon drift")
    c = horizon["constraints_frozen_before_q_selection"]
    require(c["max_expected_per_cell_exposure"] == 32, "repeat cap drift")
    require(c["min_expected_donor_operator_group_presentations"] == 16, "group coverage drift")
    require(c["min_importance_ess_fraction"] == 0.5, "ESS floor drift")
    require(c["max_importance_weight_max_to_min_ratio"] == 64.0, "weight ratio ceiling drift")
    require(horizon["training_authorized"] is False and horizon["execution_authorized"] is False, "horizon opened execution")

    require(proposal["schema"] == "TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V3", "proposal V3 missing")
    require(proposal["supersedes"] == "docs/agent/TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V2.json", "proposal lineage drift")
    require(proposal["presentation_horizon_authority"]["sha256"] == sha256(horizon_path), "horizon SHA binding drift")
    transport = counts_path.read_bytes()
    require(proposal["reader_fit_group_counts"]["transport_sha256"] == hashlib.sha256(transport).hexdigest(), "group-count transport SHA binding drift")
    gz = base64.b64decode(transport)
    decoded_csv = gzip.decompress(gz)
    require(proposal["reader_fit_group_counts"]["decoded_gzip_sha256"] == hashlib.sha256(gz).hexdigest(), "group-count gzip SHA binding drift")
    require(proposal["reader_fit_group_counts"]["decoded_csv_sha256"] == hashlib.sha256(decoded_csv).hexdigest(), "group-count decoded CSV SHA binding drift")
    require(proposal["reader_fit_group_counts"]["rows"] == 1400, "group row count drift")
    require(proposal["base"]["scientific_target_policy_id"] == "DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1", "base target drift")
    require(proposal["base"]["proposal_policy_id"] == "MAX_TARGET_MASS_SUBJECT_TO_EXPOSURE_COVERAGE_CONDITIONING_V1", "base q rule drift")
    m = proposal["base"]["derived_metrics"]
    require(m["importance_ess_fraction"] >= 0.5, "frozen q violates ESS floor")
    require(m["importance_weight_max_to_min_ratio"] <= 64.0, "frozen q violates weight ratio ceiling")
    require(m["max_expected_per_cell_exposure"] <= 32.0, "frozen q violates repeat cap")
    require(m["min_expected_donor_operator_group_presentations"] >= 16.0, "frozen q violates group coverage floor")
    require(proposal["relational"]["proposal_policy_id"] == "DIRECT_DONOR_ANCHOR_CELL_TRIPLET_TARGET_PROPOSAL_V2", "relational proposal drift")
    require(proposal["relational"]["triplet_budget"] is None, "triplet budget backdoor-frozen")
    require(proposal["training_authorized"] is False and proposal["execution_authorized"] is False, "proposal opened execution")

    # The original 66-pass prototype remains immutable and independently governed.
    frozen_root = (ROOT / "docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_PROTOTYPE_ROOT.txt").read_text().strip()
    require(frozen_root == "9684f4c2b7eff1da863ae50124c6aad49d25f137a84898e05e98d2ae1f0c67ad", "66-pass prototype root drift")

    print(PASS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
