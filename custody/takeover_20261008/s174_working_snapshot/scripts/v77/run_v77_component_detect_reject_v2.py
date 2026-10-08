#!/usr/bin/env python3
"""Component detect/reject on worlds with REPAIRED structural support (S146, S147 downstream).

The frozen component statistics (V77_COMPONENT_SUFFICIENT_STATISTIC_FREEZE_V1) were shown to
detect their planted components and reject the off twins, and later re-read with the signed
oracle (V77_ORACLE_INSTRUMENT_REPAIR_V4_SIGNED_V1). Every one of those measurements ran on
canonical V2 worlds whose structural support was swapped between HVS and SEA-AD and double
counted. This driver repeats the measurement on worlds built from committed code with the repaired
observer: the full world, and one off twin per component with that component suppressed in
OBSERVATION only (the truth keeps its latents, so the statistic still runs).

Nothing is re-tuned. Each statistic carries its own frozen pass rule and off-twin limit, and they
are applied as they come. The pre-repair signed values are reported beside the new ones.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

EXECUTOR_FILES = ("scripts/v77/run_v77_component_detect_reject_v2.py",
                  "scripts/v77/build_v77_extended_truth.py",
                  "scripts/v77/build_v77_fullscale_rna_observer_v2.py",
                  "scripts/v77/v77_component_oracle_v4_signed.py",
                  "scripts/v77/v77_component_oracle_v3.py",
                  "scripts/v77/v77_measure_oracle_ceilings_v2.py",
                  "scripts/v77/v77_address_universe.py",
                  "scripts/v64/v73_full104_qc_calibration.py",
                  "scripts/v64/v73_full104_population_geometry.py")
COMPONENTS = ("B4", "C1", "C2", "C3")
PRIMARY = {"B4": "r2_band", "C1": "gap", "C2": "r2_ratio_features", "C3": "max_abs_corr"}
TRUTH_ARGS = ["--cells", "2000", "--shard-size", "500", "--seed", "7302", "--world", "FULL"]
OBS_ARGS = ["--seed", "7302", "--background", "v1"]
RULE = "S146_S147_NAME_MAPPED_REGISTRY_RELATIVE_V1"


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def _run(cmd):
    r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"step failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    return " ".join(["python", *cmd])


def build(world: Path, suppress: str | None) -> dict:
    if world.exists():
        sys.exit(f"refusing to reuse {world}: every world in this receipt is built fresh")
    cmds = [_run(["scripts/v77/build_v77_extended_truth.py", "--root", str(world), *TRUTH_ARGS])]
    cmds.append(_run(["scripts/v77/build_v77_fullscale_rna_observer_v2.py", "--root", str(world),
                      *OBS_ARGS, *(["--suppress", suppress] if suppress else [])]))
    man = json.loads((world / "observable_raw" / "FULLSCALE_V2_CANONICAL_sharded" /
                      "FULLSCALE_V2_MANIFEST.json").read_text())
    if man.get("structural_support_rule") != RULE:
        sys.exit(f"{world}: built with support rule {man.get('structural_support_rule')}, not {RULE}")
    return dict(root=str(world), suppress=suppress, commands=cmds, support_rule=man["structural_support_rule"],
                realized_support_fraction_by_source=man["realized_support_fraction_by_source"],
                observer_shard_sha256=[s["sha256"] for s in man["shards"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds-dir", required=True, help="fresh custody folder for the five worlds")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    for rel in EXECUTOR_FILES:
        if subprocess.run(["git", "ls-files", "--error-unmatch", rel], capture_output=True, cwd=ROOT).returncode:
            sys.exit(f"refusing: {rel} is not tracked")
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode:
            sys.exit(f"refusing: {rel} differs from HEAD")
    if _git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("refusing: tracked files are modified")
    head = _git("rev-parse", "HEAD")
    digests = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in EXECUTOR_FILES}

    wd = Path(a.worlds_dir)
    worlds = {"ON_full": build(wd / "on_full", None)}
    for c in COMPONENTS:
        worlds[f"OFF_{c}"] = build(wd / f"off_{c}", c)
        print(f"built off twin {c}", flush=True)

    import v77_component_oracle_v4_signed as V4
    measured = {k: V4.measure(Path(w["root"]))["v4_signed"]["component_specific"] for k, w in worlds.items()}
    pre = json.loads((ROOT / "results/v77/V77_ORACLE_INSTRUMENT_REPAIR_V4_SIGNED_V1.json").read_text())["COMPONENT_SPECIFIC"]

    results = {}
    for c in COMPONENTS:
        on, off = measured["ON_full"][c], measured[f"OFF_{c}"][c]
        limit = on["off_twin_must_be_below"]
        off_val = off[PRIMARY[c]]
        results[c] = dict(statistic=on["statistic"], primary=PRIMARY[c],
                          on_value=on[PRIMARY[c]], detect=bool(on["passes"]),
                          off_value=off_val, off_limit=limit, reject=bool(off_val < limit),
                          pre_repair_signed_value=pre[c]["v4"], pre_repair_verdict=pre[c]["verdict"],
                          on_detail=on, off_detail=off)
        print(f"{c}: on {on[PRIMARY[c]]:.4f} detect {on['passes']} | off {off_val:.4f} < {limit} "
              f"reject {off_val < limit} | pre-repair {pre[c]['v4']:.4f}")

    rec = dict(
        schema="V77_COMPONENT_DETECT_REJECT_REPAIRED_SUPPORT_V1",
        claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        question="do the frozen component statistics still detect and reject on worlds with repaired support?",
        instrument="v77_component_oracle_v4_signed (unchanged); thresholds as frozen, read from the statistics",
        ceiling_label="ORACLE_CEILING_UNDER_KNOWN_SUPPORT_AND_KNOWN_SIGN",
        worlds=worlds, results=results,
        summary=dict(detect=sum(r["detect"] for r in results.values()),
                     reject=sum(r["reject"] for r in results.values()), of=len(results)),
        command=f"python scripts/v77/run_v77_component_detect_reject_v2.py --worlds-dir {a.worlds_dir} --out {a.out}",
        source_commit=head, provenance_status="CLEAN_COMMITTED_HEAD__EXECUTORS_TRACKED_AND_UNMODIFIED",
        executor_sha256=digests, thresholds_changed=False, no_training_performed=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2, default=float) + "\n")
    print("summary:", rec["summary"])


if __name__ == "__main__":
    main()
