#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from sea_ad_jepa.v5.critical_test_execution_guard_v1 import validate_junit_critical_tests

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--junit", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out")
    args=ap.parse_args()
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if manifest.get("schema")!="JEPA_V5_CRITICAL_TEST_EXECUTION_MANIFEST_V1":
        raise SystemExit("STOP_CRITICAL_TEST_MANIFEST_SCHEMA")
    report=validate_junit_critical_tests(
        args.junit, expected_test_ids=manifest.get("expected_test_ids", [])
    )
    obj={**report.__dict__, "training_authorized":False, "execution_authorized":False}
    if args.out:
        Path(args.out).write_text(
            json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8"
        )
    print(json.dumps(obj,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
