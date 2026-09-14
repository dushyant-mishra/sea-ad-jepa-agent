from __future__ import annotations

import argparse
import json
from pathlib import Path

from sea_ad_jepa.v5.environment_preflight_v1 import (
    collect_environment_preflight_v1,
    seal_environment_preflight_receipt_v1,
    validate_environment_preflight_v1,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and seal the V5 environment preflight receipt.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--junit", required=True)
    parser.add_argument("--critical-manifest", required=True)
    parser.add_argument("--authority-path", action="append", dest="authority_paths", required=True)
    parser.add_argument("--environment-name", default="sea-ad-jepa-v3")
    parser.add_argument("--cuda-required", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    receipt = collect_environment_preflight_v1(
        root=Path(args.root),
        expected_head=args.expected_head,
        junit_path=Path(args.junit),
        critical_manifest_path=Path(args.critical_manifest),
        authority_paths=args.authority_paths,
        cuda_required=args.cuda_required,
        environment_name=args.environment_name,
    )
    envelope = seal_environment_preflight_receipt_v1(receipt)
    validate_environment_preflight_v1(envelope)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print("PASS_V5_ENVIRONMENT_PREFLIGHT_V1")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
