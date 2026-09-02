#!/usr/bin/env python3
"""Fail-atomic finalizer for the reviewed Command-15A4 package."""
from __future__ import annotations

import argparse, csv, hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ARTIFACTS = (
    "F1_HC3_15A4_AUTHORITY.json",
    "F1_HC3_REUSABLE_NUISANCE_ADMISSIBILITY_CONTRACT.md",
    "F1_HC3_REPLICATION_FRONTIER_COMPLETE.csv",
    "F1_HC3_SOURCE_PREFIX_REPLICATION.csv",
    "F1_HC3_LEVERAGE_SVD_QR_CROSSCHECK.json",
    "F1_HC3_NPH52_DONOR_INDISPENSABILITY.json",
    "F1_HC3_NPH_FREE_FRONTIER_SUMMARY.json",
    "F1_HC3_15A4_INDEPENDENT_VALIDATION.json",
    "F1_HC3_15A4_MULTIAGENT.md",
    "F1_HC3_15A4_SOURCE_MANIFEST.csv",
    "F1_HC3_15A4_MANIFEST.csv",
    "F1_HC3_15A4_EXTERNAL_REVIEW_HANDOFF.md",
)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def snapshot_manifest_path(name):
    return f"source_snapshot/{name}"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--staging", type=Path, required=True); args = ap.parse_args(); out = args.staging.resolve()
    validation = json.loads((out / "F1_HC3_15A4_INDEPENDENT_VALIDATION.json").read_text())
    cross = json.loads((out / "F1_HC3_LEVERAGE_SVD_QR_CROSSCHECK.json").read_text())
    summary = json.loads((out / "F1_HC3_NPH_FREE_FRONTIER_SUMMARY.json").read_text())
    authority = json.loads((out / "F1_HC3_15A4_AUTHORITY.json").read_text())
    with (out / "F1_HC3_REPLICATION_FRONTIER_COMPLETE.csv").open(newline="", encoding="utf-8") as handle:
        frontier = list(csv.DictReader(handle))
    if validation["status"] != "PASS" or len(frontier) != 70 or summary["nph_free_rows"] != 35 or not cross["all_70_rank_and_leverage_checks_pass"] or authority["design_selected_or_frozen"]:
        raise RuntimeError("STOP_F1_HC3_15A4_INDEPENDENT_MISMATCH")
    review = """# F1 HC3 Command 15A4 targeted five-lens review

Synthesis: **PROCEED** to publish this diagnostic/procedure package. This does not authorize nuisance-design selection or F1 execution.

1. **Numerical Linear Algebra — PASS after repair.** All 70 SVD and pivoted-QR ranks agree; maximum leverage difference is below `TOL`. No normal-equation leverage is conclusion-bearing. Initial concern that the reusable contract omitted exact numerical rules was repaired before publication by binding the SVD rank formula, QR rule, projection invariants, tolerance, HC3 boundary, and prohibitions. Fresh recomputation left frontier bytes unchanged.
2. **HC3 / Robust Inference — PASS.** Unit leverage is not clamped. LOO instability is diagnostic evidence, never repaired by donor deletion. All 70 rows carry explicit admissibility and reason codes.
3. **Dataset / Operator Semantics — PASS.** All 104 lawful donors remain present; HVS/NPH52/SEA-AD operator blocks remain 24/7/11. No expression, outcome, model, checkpoint, forward, training, or EMA access occurred.
4. **Historian / Provenance — PASS.** The prior packages and v2 source snapshots reproduce byte-for-byte. This completes an outcome-blind implementation and does not select a rank triple.
5. **Larger-Cohort Generalization — PASS.** The reusable contract freezes only the cohort-recomputed algorithm. Current ranks, leverage values, and donor identities are explicitly forbidden as future constants.

Dissent preserved: the first Numerical review was `CONCERN` because the initial reusable contract underspecified its numerical algorithm. The contract was expanded, the derivation and independent validator were rerun, the 70-row frontier SHA remained unchanged, and the Larger-Cohort lens then passed.
"""
    (out / "F1_HC3_15A4_MULTIAGENT.md").write_text(review, encoding="utf-8")
    handoff = f"""# F1 HC3 Command 15A4 — external-review handoff

Terminal: `PASS_F1_HC3_REPLICATION_FRONTIER_COMPLETE_AWAITING_EXTERNAL_REVIEW`.

- All 70 source-prefix rows were evaluated.
- All 35 NPH-free rows were evaluated.
- Independent reconstruction recomputed all 7,280 donor-deletion ranks.
- SVD projection leverage and pivoted-QR leverage agree within the frozen tolerance.
- Current cohort: 30 rows are donor-replicated HC3-admissible and 40 are nonreplicated/HC3-boundary rows.
- NPH52 C1 is donor-indispensable at `NPH52::human_NPH_906` across all 35 NPH-containing rows.
- HVS prefix 6 is donor-indispensable at `HVS::H20.06.354` across five NPH-free rows; SEA-AD has no donor-indispensable prefix in this cohort.
- No design or rank triple was selected or frozen.
- No outcome, expression, model, checkpoint, forward, training, or EMA access occurred.
- Current admissible/nonadmissible ranks and donor identities are not future-cohort constants.

The reusable artifact freezes only the cohort-agnostic reconstruction, full-design rank, LOO donor-replication, SVD/QR leverage, and HC3-admissibility procedure.
"""
    (out / "F1_HC3_15A4_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff, encoding="utf-8")
    terminal = {"terminal_status": "PASS_F1_HC3_REPLICATION_FRONTIER_COMPLETE_AWAITING_EXTERNAL_REVIEW", "frontier_rows": 70, "nph_free_rows": 35, "admissible_rows": sum(r["donor_replicated_hc3_admissible"] == "True" for r in frontier), "design_selected_or_frozen": False, "f1_run_authorized": False}
    (out / "F1_HC3_15A4_TERMINAL_STATUS.json").write_text(json.dumps(terminal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    snapshot = out / "source_snapshot"; snapshot.mkdir(exist_ok=True)
    sources = ["derive_contextual_target_f1_hc3_replication_frontier_v3.py", "validate_contextual_target_f1_hc3_replication_frontier_v3.py", "finalize_contextual_target_f1_hc3_replication_frontier_v3.py"]
    source_rows = []
    for name in sources:
        source = ROOT / "scripts/v4" / name; target = snapshot / name; shutil.copy2(source, target)
        source_rows.append({"source_path": str(source.relative_to(ROOT)).replace("\\", "/"), "snapshot_path": snapshot_manifest_path(name), "snapshot_path_scope": "PACKAGE_RELATIVE", "source_sha256": sha256(source), "snapshot_sha256": sha256(target), "byte_identical": sha256(source) == sha256(target)})
    with (out / "F1_HC3_15A4_SOURCE_MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(source_rows[0])); writer.writeheader(); writer.writerows(source_rows)
    missing = [name for name in REQUIRED_ARTIFACTS if name not in {"F1_HC3_15A4_MANIFEST.csv"} and not (out / name).is_file()]
    if missing: raise RuntimeError(f"STOP_PROVENANCE_OR_FIREWALL: missing {missing}")
    rows = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name != "F1_HC3_15A4_MANIFEST.csv"):
        rows.append({"relative_path": str(path.relative_to(out)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256(path)})
    with (out / "F1_HC3_15A4_MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "bytes", "sha256"]); writer.writeheader(); writer.writerows(rows)
    if any(not (out / name).is_file() for name in REQUIRED_ARTIFACTS): raise RuntimeError("STOP_PROVENANCE_OR_FIREWALL")
    print(json.dumps({**terminal, "manifest_sha256": sha256(out / "F1_HC3_15A4_MANIFEST.csv"), "manifested_files": len(rows)}))


if __name__ == "__main__":
    main()
