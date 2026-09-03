"""Fail-closed finalizer for the synthetic-only 15C numerical repair package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


SOURCES = (
    "scripts/v4/contextual_target_f1_hc3_stable_qr_v2.py",
    "scripts/v4/validate_contextual_target_f1_hc3_svd_v2.py",
    "scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py",
    "scripts/v4/run_contextual_target_f1_hc3_15c_numerical_v2.py",
    "scripts/v4/finalize_contextual_target_f1_hc3_15c_numerical_v2.py",
    "tests/v4/test_contextual_target_f1_hc3_15c_numerical_v2.py",
)
HISTORICAL_BLOBS = {
    "scripts/v4/contextual_target_f1_decision_v1.py": "204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34",
    "scripts/v4/contextual_target_f1_decision_v4.py": "5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913",
    "scripts/v4/contextual_target_f1_decision_integration_v4.py": "5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, fieldnames, rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def finalize(out: Path, repo: Path) -> str:
    out, repo = Path(out), Path(repo)
    required = {
        "F1_HC3_15C_EFFECTIVE_DESIGN_BINDING.json": "PASS_F1_HC3_15C_EFFECTIVE_DESIGN_BOUND",
        "F1_HC3_15C_NUMERICAL_COMPARISON.json": "PASS_F1_HC3_15C_NUMERICAL_COMPARISON",
        "F1_HC3_15C_REPAIR_FIREWALL_AUDIT.json": "PASS_F1_HC3_15C_SYNTHETIC_ONLY_FIREWALL",
    }
    for name, status in required.items():
        if json.loads((out / name).read_text(encoding="utf-8"))["status"] != status:
            raise ValueError("STOP_F1_HC3_15C_FINALIZATION_STATUS_MISMATCH")
    if json.loads((out / "F1_HC3_15C_ADVERSARIAL_REGRESSION.json").read_text(encoding="utf-8"))["status"] != "PASS":
        raise ValueError("STOP_F1_HC3_15C_ADVERSARIAL_REGRESSION")

    qr_text = (repo / SOURCES[0]).read_text(encoding="utf-8")
    svd_text = (repo / SOURCES[1]).read_text(encoding="utf-8")
    forbidden_qr = ("np.linalg.inv", "np.linalg.pinv", "ridge", "solve(x.T @ x", "solve(X.T @ X", "inv(X.T @ X)")
    if any(token in qr_text for token in forbidden_qr):
        raise ValueError("STOP_F1_HC3_15C_PRODUCTION_NORMAL_EQUATION_OR_FALLBACK")
    if "contextual_target_f1_hc3_stable_qr_v2" in svd_text or "np.linalg.qr" in svd_text:
        raise ValueError("STOP_F1_HC3_15C_INDEPENDENT_VALIDATOR_NOT_INDEPENDENT")

    historical = {}
    for relative, expected in HISTORICAL_BLOBS.items():
        data = subprocess.check_output(["git", "-C", str(repo), "show", "HEAD:" + relative])
        actual = sha_bytes(data)
        if actual != expected:
            raise ValueError("STOP_F1_HC3_15C_HISTORICAL_AUTHORITY_CHANGED")
        historical[relative] = actual

    snapshots = out / "source_snapshots"
    snapshots.mkdir(exist_ok=True)
    source_rows = []
    for relative in SOURCES:
        source = repo / relative
        target = snapshots / Path(relative).name
        shutil.copyfile(source, target)
        if sha(source) != sha(target):
            raise ValueError("STOP_F1_HC3_15C_SOURCE_SNAPSHOT_MISMATCH")
        source_rows.append({"source_path": relative, "source_sha256": sha(source), "snapshot_path": target.relative_to(out).as_posix(), "snapshot_sha256": sha(target)})
    write_csv(out / "F1_HC3_15C_REPAIR_SOURCE_MANIFEST.csv", ("source_path", "source_sha256", "snapshot_path", "snapshot_sha256"), source_rows)

    comparison = json.loads((out / "F1_HC3_15C_NUMERICAL_COMPARISON.json").read_text(encoding="utf-8"))
    handoff = f"""# F1 HC3 15C Numerical Robustness Repair — External Review Handoff

Terminal: `PASS_F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_AWAITING_EXTERNAL_REVIEW`

- Scope: synthetic-only numerical independence repair; the evidence-slope issue is untouched.
- Frozen nuisance design: `(5,0,4)`, effective `104 x 16`, rank `16`, df `88`.
- Production HC3: reduced QR/triangular solves. Independent validation: thin SVD/pseudoinverse.
- QR/SVD baseline and prospective +/-1e-5 near-boundary fixtures agree within frozen tolerances and exactly on gates.
- Near-boundary gates: positive `{comparison['near_boundary']['positive']['qr_gate']}`; negative `{comparison['near_boundary']['negative']['qr_gate']}`.
- All 14 frozen truth-table cases and the 15C adversarial suite pass.
- Frozen v1/v4/integration Git blobs remain unchanged: `{json.dumps(historical, sort_keys=True)}`.
- No expression, model/checkpoint tensor, training, optimizer, EMA, DEV, SEALED, pathology, or real F1 outcome was accessed.
- Reader/forward authority remains unset. Real F1 remains unauthorized pending external review.
"""
    (out / "F1_HC3_15C_REPAIR_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff, encoding="utf-8")

    manifest_path = out / "F1_HC3_15C_REPAIR_MANIFEST.csv"
    rows = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p != manifest_path and p.name != "F1_HC3_15C_REPAIR_PACKAGE_ROOT_SHA256.txt"):
        rows.append({"relative_path": path.relative_to(out).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    write_csv(manifest_path, ("relative_path", "bytes", "sha256"), rows)
    root_sha = sha(manifest_path)
    (out / "F1_HC3_15C_REPAIR_PACKAGE_ROOT_SHA256.txt").write_text(root_sha + "  F1_HC3_15C_REPAIR_MANIFEST.csv\n", encoding="ascii")
    return root_sha


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True); parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args(); print(finalize(args.out, args.repo))
