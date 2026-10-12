#!/usr/bin/env python3
"""Historical-fixture adapter equivalence for the corrected TD replay (adapter-qualification plan, Tasks 3-7).

The adapter is fed authenticated historical values, restricted to the frozen 9,216 replay addresses and the 25,000
Sample-A rows. Each exact frozen executor then runs through the same bootstrap the corrected replay will use. Every
decision-bearing output must equal the archived historical output: TD56 result arrays; TD57B/TD57C payloads
except `input_sha256`; TD59 per-case observed / null_p95 / null_max from the replay-closure table. Historical values
only; no corrected value is read.

  build      write the fixture inputs once into <work>/mnt and record their SHAs
  run        run one invocation (--stage, --source, --panel) and record the comparison under <work>/results
  canonical  from a clean committed checkout: build, run all 16 historical cases one at a time, and write the
             equivalence receipt that QUALIFY requires
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_corrected_replay_adapter_v1 as A  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXECUTORS = {  # stage -> (kind, archive member or repo path, SHA-256)
    ("TD56", "HVS"): ("td56", "run_td56_hvs.py", "a1ea8653e24213a3b14ccc52ea64011c92553aec4df5edb7b55d6ba309f61b43"),
    ("TD56", "NPH52"): ("td56", "run_td56_nph.py", "090134f0cc129559286f06d80a31a880c07c9841a7ef3f446b914a78c8cd7162"),
    ("TD56", "SEA_AD"): ("td56", "run_td56_sea_fast.py", "c77ceac26f0ff4c3ae7a3955c39218af56339adda0225b9c663c9d92710c8866"),
    "TD57B": ("module", "td57b_fixed_relational_recurrence.py", "1654011ca1aeb20dab8e707b229ec3de00106b937ed49b33b2432b789d8c4e0e"),
    "TD57C": ("module", "td57c_three_view_local_geometry.py", "530aa006595b9633147234538e9ad441787e4d80860da240d26b254f5e59b11c"),
    "TD59": ("module", "repo:target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/td59_replay_closure_executor_v1.py",
             "870ddea0f84f0c868cbce772c9f7506b4c1b35b55e4cd09f9f9e62dbf7425085"),
}
SOURCE_TAG = {"HVS": "hvs", "NPH52": "nph52", "SEA_AD": "seaad"}
TD59_CASES = ROOT / "target_discovery/iterations/td59_mesoscale_half_locality/replay_closure_20260908/TD59_REPLAY_CLOSURE_CASE_MATCH.csv"


def executor_file(work: Path, archive: Path, stage: str, source: str) -> tuple[str, Path, str]:
    kind, ref, sha = EXECUTORS[(stage, source)] if stage == "TD56" else EXECUTORS[stage]
    if ref.startswith("repo:"):
        path = ROOT / ref[len("repo:"):]
        A.require_sha(path, sha, f"{stage} executor")
        return kind, path, sha
    path = work / "executors" / ref
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(A.archive_member(archive, ref, sha))
    A.require_sha(path, sha, f"{stage} executor")
    return kind, path, sha


def compare_td56(out: Path, archive: Path, source: str) -> dict:
    ref = np.load(io.BytesIO(A.archive_member(archive, f"td56_{source}_result.npz")), allow_pickle=True)
    got = np.load(out, allow_pickle=True)
    diffs = []
    for k in ref.files:
        a, b = ref[k], got[k] if k in got.files else None
        same = b is not None and a.shape == b.shape and (np.array_equal(a, b) if a.dtype != object else a.tolist() == b.tolist())
        if not same:
            diffs.append(k)
    return {"compared_keys": sorted(ref.files), "mismatched_keys": diffs, "equal": not diffs,
            "historical_PASS": bool(float(ref["obs"]) > float(ref["p95"]) and float(ref["obs"]) > 0),
            "replay_PASS": bool(float(got["obs"]) > float(got["p95"]) and float(got["obs"]) > 0)}


def compare_payload(out: Path, archive: Path, stage: str, source: str, panel: int) -> dict:
    name = f"{stage.lower()}_p{panel}_{SOURCE_TAG[source]}.json"
    ref = json.loads(A.archive_member(archive, name))
    got = json.loads(out.read_text(encoding="utf-8"))
    keys = sorted((set(ref) | set(got)) - {"input_sha256"})
    diffs = [k for k in keys if ref.get(k) != got.get(k)]
    return {"archived_member": name, "compared_keys": keys, "mismatched_keys": diffs, "equal": not diffs,
            "historical_status": ref.get("status"), "replay_status": got.get("status"),
            "historical_terminal": ref.get("terminal"), "replay_terminal": got.get("terminal")}


def compare_td59(out: Path, source: str, panel: int) -> dict:
    """Exact per-case match against the committed historical values in the replay-closure table."""
    got = json.loads(out.read_text(encoding="utf-8"))
    rows = {(int(r["split"]), int(r["half"])): r for r in csv.DictReader(TD59_CASES.open(encoding="utf-8"))
            if r["source"] == source and int(r["panel"]) == panel}
    cases = {(int(c["split"]), int(c["half"])): c for c in got.get("cases", [])}
    diffs = []
    for key in sorted(set(rows) | set(cases)):
        r, c = rows.get(key), cases.get(key)
        if r is None or c is None:
            diffs.append({"case": key, "missing": "historical" if r is None else "replay"})
            continue
        pairs = (("committed_observed", "observed_median_donor_local_triplet_agreement"),
                 ("committed_null_p95", "null_p95_index60"), ("committed_null_max", "null_max"))
        bad = [h for h, k in pairs if float(r[h]) != float(c[k])]
        if (r["pass"] == "True") != bool(c["pass"]):
            bad.append("pass")
        if bad:
            diffs.append({"case": key, "fields": bad})
    return {"historical_cases": len(rows), "replay_cases": len(cases), "mismatches": diffs, "equal": not diffs,
            "replay_status": got.get("status"), "replay_terminal": got.get("terminal")}


def build(a) -> int:
    work = Path(a.work)
    cache = A.historical_fixture(Path(a.hist_csr), Path(a.sample_freeze), Path(a.replay_manifest), Path(a.archive))
    t0 = time.time()
    shas = A.write_inputs(cache, Path(a.archive), Path(a.support_bundle), work / "mnt")
    shas["support_rel"] = A.SUPPORT_REL
    (work / "INPUTS.json").write_text(json.dumps({"kind": cache["kind"], "input_sha256": shas,
                                                   "write_seconds": round(time.time() - t0, 1)}, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"kind": cache["kind"], "files": len(shas) - 1}))
    return 0


def run(a) -> int:
    work, archive = Path(a.work), Path(a.archive)
    inputs = json.loads((work / "INPUTS.json").read_text())
    kind, executor, sha = executor_file(work, archive, a.stage, a.source)
    case = f"{a.stage}_{a.source}" + ("" if a.stage == "TD56" else f"_P{a.panel}")
    res = work / "results"
    res.mkdir(exist_ok=True)
    out = (work / "mnt" / f"td56_{a.source}_result.npz") if a.stage == "TD56" else (res / f"{case}.output.json")
    if out.exists():
        raise SystemExit(f"STOP: output already exists: {out}")
    t0 = time.time()
    rc = A.run_executor(kind=kind, executor=executor, executor_sha=sha, mnt=work / "mnt", input_sha=inputs["input_sha256"],
                        python=a.python, source=a.source, panel=a.panel, output=out,
                        stdout=res / f"{case}.stdout.txt", stderr=res / f"{case}.stderr.txt")
    seconds = round(time.time() - t0, 1)
    record = {"case": case, "stage": a.stage, "source": a.source, "panel": a.panel, "executor_sha256": sha,
              "exit_code": rc, "seconds": seconds, "output_sha256": A.sha_file(out) if out.exists() else None}
    if out.exists():
        if a.stage == "TD56":
            record["comparison"] = compare_td56(out, archive, a.source)
        elif a.stage in ("TD57B", "TD57C"):
            record["comparison"] = compare_payload(out, archive, a.stage, a.source, a.panel)
        else:
            record["comparison"] = compare_td59(out, a.source, a.panel)
    (res / f"{case}.equivalence.json").write_text(json.dumps(record, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k != "comparison"} |
                     {"equal": (record.get("comparison") or {}).get("equal")}, default=str))
    return 0


CANONICAL_CASES = ([("TD56", s, 0) for s in A.SOURCES] + [("TD57B", s, p) for p in (0, 1) for s in A.SOURCES]
                   + [("TD57C", "HVS", 0)] + [("TD59", s, p) for p in (0, 1) for s in A.SOURCES])


def canonical(a) -> int:
    import platform
    import numpy, pandas, scipy  # noqa: E401
    # WSL git cannot read a worktree created by Windows git (its .git points at a D:/ path), so the caller (Git Bash)
    # verifies HEAD and cleanliness immediately before the run and passes the verified commit. The receipt records
    # that, and QUALIFY separately binds the adapter/bootstrap bytes by SHA.
    head = a.implementation_commit
    if len(head) != 40 or any(ch not in "0123456789abcdef" for ch in head):
        raise SystemExit("STOP: --implementation-commit must be a verified 40-hex commit")
    work = Path(a.work)
    if work.exists():
        raise SystemExit(f"STOP: work directory exists: {work}")
    work.mkdir(parents=True)
    build(a)
    cases = []
    for stage, source, panel in CANONICAL_CASES:
        run(argparse.Namespace(work=a.work, archive=a.archive, python=a.python, stage=stage, source=source, panel=panel))
        tag = f"{stage}_{source}" + ("" if stage == "TD56" else f"_P{panel}")
        rec = json.loads((work / "results" / f"{tag}.equivalence.json").read_text())
        cases.append({"case": tag, "exit_code": rec["exit_code"], "seconds": rec["seconds"], "executor_sha256": rec["executor_sha256"],
                      "output_sha256": rec["output_sha256"], "equal": bool((rec.get("comparison") or {}).get("equal"))})
    receipt = {
        "schema": "JEPA_TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1",
        "purpose": "historical-fixture adapter equivalence (adapter-qualification plan Tasks 3-7); historical values only; no corrected value read",
        "implementation_commit_sha": head,
        "commit_verification": "caller (Git Bash) verified git rev-parse HEAD == implementation commit and git status --porcelain --ignored empty immediately before this run",
        "code_sha256": {"adapter": A.sha_file(Path(A.__file__)), "bootstrap": A.sha_file(A.BOOTSTRAP),
                        "equivalence": A.sha_file(Path(__file__).resolve())},
        "environment": {"platform": platform.system(), "python": platform.python_version(), "numpy": numpy.__version__,
                        "scipy": scipy.__version__, "pandas": pandas.__version__},
        "fixture_input_sha256": json.loads((work / "INPUTS.json").read_text())["input_sha256"],
        "cases": cases, "n_cases": len(cases), "all_equal": all(c["equal"] for c in cases),
        "td57c_historical_fail_reproduced": next(c for c in cases if c["case"] == "TD57C_HVS_P0")["exit_code"] == 2,
        "comparison_rule": ("TD56 result arrays exactly equal; TD57B/TD57C payload exactly equal except input_sha256; "
                            "TD59 per-case observed, null_p95, null_max and pass exactly equal to the committed replay-closure table"),
        "corrected_values_read": False, "target_selection_authorized": False, "td60_authorized": False,
        "stage4_authorized": False, "training_authorized": False}
    out = work / "TD_CORRECTED_REPLAY_EQUIVALENCE_RECEIPT_V1.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_equal": receipt["all_equal"], "n_cases": receipt["n_cases"], "receipt_sha256": A.sha_file(out)}))
    return 0 if receipt["all_equal"] else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    for n in ("work", "hist-csr", "sample-freeze", "replay-manifest", "archive", "support-bundle"):
        b.add_argument(f"--{n}", required=True)
    r = sub.add_parser("run")
    r.add_argument("--work", required=True)
    r.add_argument("--archive", required=True)
    r.add_argument("--python", required=True)
    r.add_argument("--stage", choices=("TD56", "TD57B", "TD57C", "TD59"), required=True)
    r.add_argument("--source", choices=A.SOURCES, required=True)
    r.add_argument("--panel", type=int, choices=(0, 1), default=0)
    k = sub.add_parser("canonical")
    for n in ("work", "hist-csr", "sample-freeze", "replay-manifest", "archive", "support-bundle", "python", "implementation-commit"):
        k.add_argument(f"--{n}", required=True)
    a = ap.parse_args()
    return build(a) if a.cmd == "build" else run(a) if a.cmd == "run" else canonical(a)


if __name__ == "__main__":
    raise SystemExit(main())
