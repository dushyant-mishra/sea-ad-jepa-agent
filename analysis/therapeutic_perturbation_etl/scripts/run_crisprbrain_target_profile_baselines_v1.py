#!/usr/bin/env python3
"""Run a DEVELOPMENT-only, source-hash-bound CRISPRbrain screen baseline.

This does not load FULL104, does not fit JEPA and does not confer biological
replication or external prospective confirmation. Source is one processed
screen; do not mix screens or label capture wells as donors.
"""
import argparse
import json
from pathlib import Path

from sea_ad_jepa.perturbation.benchmark_screen_profile_baselines_v1 import (
    load_verified_screen_gzip, score_retrospective_baselines,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-csv-gz", required=True)
    p.add_argument("--screen", required=True)
    p.add_argument("--expected-uncompressed-sha256", required=True)
    p.add_argument("--seed", default="GSE178317_RETROSPECTIVE_BASELINES_DEVELOPMENT_20260924")
    p.add_argument("--out-json", required=True)
    args = p.parse_args()
    if Path(args.out_json).exists():
        raise SystemExit("STOP: refuse to overwrite an existing benchmark receipt")
    profiles = load_verified_screen_gzip(
        args.source_csv_gz, screen=args.screen,
        expected_csv_sha256=args.expected_uncompressed_sha256,
    )
    out = score_retrospective_baselines(profiles, seed=args.seed)
    Path(args.out_json).write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: out[k] for k in ("screen", "targets", "targets_estimable", "exposure", "macro", "responsive_subset")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
