"""Finalize and hash-bind the synthetic-only evidence-trend repair package."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


SOURCES = (
    "scripts/v4/contextual_target_f1_evidence_slope_v1.py",
    "scripts/v4/contextual_target_f1_evidence_trend_decision_v1.py",
    "scripts/v4/validate_contextual_target_f1_evidence_trend_v1.py",
    "scripts/v4/run_contextual_target_f1_evidence_trend_repair_v1.py",
    "scripts/v4/finalize_contextual_target_f1_evidence_trend_repair_v1.py",
    "tests/v4/test_contextual_target_f1_evidence_trend_numerical_v1.py",
)
HISTORICAL = {
    "scripts/v4/contextual_target_f1_decision_v1.py": "204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34",
    "scripts/v4/contextual_target_f1_decision_v4.py": "5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913",
    "scripts/v4/contextual_target_f1_decision_integration_v4.py": "5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a",
    "scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py": "c5432f84cb51105419a68c4d14e81d52d84818bad206af0458b4ba6fc37d5a3d",
    "scripts/v4/contextual_target_f1_hc3_stable_qr_v2.py": "8a4a18314687f410b01a3e798670d9cffb6ee377abe9217c719dfceaec941961",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, fields, rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def finalize(out: Path, *, repo_root: Path) -> str:
    out, repo_root = Path(out), Path(repo_root)
    expected = {
        "F1_EVIDENCE_TREND_REPAIRED_SLOPE_RESULTS.json": "PASS",
        "F1_EVIDENCE_TREND_INDEPENDENT_REFERENCE_RESULTS.json": "PASS",
        "F1_EVIDENCE_TREND_NUMERICAL_COMPARISON.json": "PASS",
        "F1_EVIDENCE_TREND_LEGACY_DEFECT_DEMONSTRATION.json": "PASS",
        "F1_EVIDENCE_TREND_COMPLETE_GATE_VECTOR_COMPARISON.json": "PASS",
        "F1_EVIDENCE_TREND_REGRESSION_RESULTS.json": "PASS",
        "F1_EVIDENCE_TREND_REPAIR_FIREWALL_AUDIT.json": "PASS_SYNTHETIC_ONLY_FIREWALL",
    }
    for name, status in expected.items():
        if json.loads((out / name).read_text(encoding="utf-8"))["status"] != status:
            raise ValueError("STOP_F1_EVIDENCE_TREND_FINALIZATION_STATUS_MISMATCH")

    production_text = (repo_root / SOURCES[0]).read_text(encoding="utf-8")
    independent_text = (repo_root / SOURCES[2]).read_text(encoding="utf-8")
    decision_text = (repo_root / SOURCES[1]).read_text(encoding="utf-8")
    if "(row[4] - row[0])" not in production_text or "(row[3] - row[1])" not in production_text or "row[2]" in production_text:
        raise ValueError("STOP_F1_EVIDENCE_TREND_PRODUCTION_ARITHMETIC_MISMATCH")
    if "contextual_target_f1_evidence_slope_v1" in independent_text or "evidence_slopes(" in independent_text or "math.fsum" not in independent_text:
        raise ValueError("STOP_F1_EVIDENCE_TREND_INDEPENDENT_REFERENCE_NOT_INDEPENDENT")
    if "contextual_target_f1_hc3_15c_adapter_v2.py" not in decision_text:
        raise ValueError("STOP_F1_EVIDENCE_TREND_ACCEPTED_HC3_NOT_COMPOSED")

    safe_repo = repo_root.resolve().as_posix()
    historical = {}
    for relative, expected_sha in HISTORICAL.items():
        data = subprocess.check_output(["git", "-c", f"safe.directory={safe_repo}", "-C", str(repo_root), "show", "HEAD:" + relative])
        actual = sha_bytes(data)
        if actual != expected_sha: raise ValueError("STOP_F1_EVIDENCE_TREND_HISTORICAL_AUTHORITY_CHANGED")
        historical[relative] = actual

    snapshots = out / "source_snapshots"; snapshots.mkdir(exist_ok=True)
    source_rows = []
    for relative in SOURCES:
        source = repo_root / relative; target = snapshots / Path(relative).name
        shutil.copyfile(source, target)
        if sha(source) != sha(target): raise ValueError("STOP_F1_EVIDENCE_TREND_SOURCE_SNAPSHOT_MISMATCH")
        source_rows.append({"source_path": relative, "source_sha256": sha(source), "snapshot_path": target.relative_to(out).as_posix(), "snapshot_sha256": sha(target)})
    write_csv(out / "F1_EVIDENCE_TREND_REPAIR_SOURCE_MANIFEST.csv", ("source_path", "source_sha256", "snapshot_path", "snapshot_sha256"), source_rows)

    comparison = json.loads((out / "F1_EVIDENCE_TREND_NUMERICAL_COMPARISON.json").read_text(encoding="utf-8"))
    defect = json.loads((out / "F1_EVIDENCE_TREND_LEGACY_DEFECT_DEMONSTRATION.json").read_text(encoding="utf-8"))
    gate = json.loads((out / "F1_EVIDENCE_TREND_COMPLETE_GATE_VECTOR_COMPARISON.json").read_text(encoding="utf-8"))
    handoff = f"""# F1 Evidence-Trend Numerical Repair — External Review Handoff

Terminal: `PASS_F1_EVIDENCE_TREND_NUMERICAL_REPAIR_AWAITING_EXTERNAL_REVIEW`

- Scope is synthetic-only. Real F1 and reader/forward authority remain forbidden.
- Production slope is exactly `(A100-A20)+0.5*(A80-A40)` in float64; A60 has coefficient zero.
- Independent reference uses a separate `math.fsum` implementation.
- Maximum per-donor slope difference: `{comparison['maximum_per_donor_slope_abs_difference']}`.
- Exact-flat fixtures return exact zero in both implementations.
- Near-boundary positive gates: `{comparison['near_boundary']['positive']}`.
- Near-boundary negative gates: `{comparison['near_boundary']['negative']}`.
- Legacy donor-varying flat fixture produced `{defect['legacy_nonzero_count']}` nonzero historical slopes and a historical PASS; repaired slopes are all exact zero and non-estimable/vetoed.
- Complete gate-vector agreement: `{gate['complete_gate_vector_exact']}`.
- Every non-evidence gate/report and the accepted QR-HC3 report/gate are unchanged.
- Historical Git-blob authorities remain byte-for-byte unchanged: `{json.dumps(historical, sort_keys=True)}`.
- No expression, protected outcomes, model/checkpoint, training, optimizer, EMA, DEV, SEALED, or pathology data were accessed.
"""
    (out / "F1_EVIDENCE_TREND_REPAIR_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff, encoding="utf-8")

    manifest = out / "F1_EVIDENCE_TREND_REPAIR_MANIFEST.csv"
    root_anchor = out / "F1_EVIDENCE_TREND_REPAIR_PACKAGE_ROOT_SHA256.txt"
    rows = []
    for path in sorted(item for item in out.rglob("*") if item.is_file() and item not in (manifest, root_anchor)):
        rows.append({"relative_path": path.relative_to(out).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    write_csv(manifest, ("relative_path", "bytes", "sha256"), rows)
    manifest_sha = sha(manifest)
    root_anchor.write_text(manifest_sha + "  F1_EVIDENCE_TREND_REPAIR_MANIFEST.csv\n", encoding="ascii")
    return manifest_sha


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True); parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args(); print(finalize(args.out, repo_root=args.repo_root))
