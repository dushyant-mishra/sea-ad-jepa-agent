#!/usr/bin/env python3
"""Build nonlinear model-capacity authority V1 from narrow historical provenance."""
from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path

from sea_ad_jepa.v5.full104_census_receipt_v2 import sha256_file
from sea_ad_jepa.v5.masking_qualification_parameters_authority_v2 import MaskingQualificationParametersAuthorityV2
from sea_ad_jepa.v5.nonlinear_capacity_model_authority_v1 import NonlinearCapacityModelAuthorityV1

HISTORICAL_SCRIPT="analysis/v5_masking_successor_spike_20260917/scripts/outer5200_nonlinear_probe32.py"
HISTORICAL_SUMMARY="analysis/v5_masking_successor_spike_20260917/results/outer5200_nonlinear32_summary.csv"

EXPECTED_HISTORICAL_SCRIPT_SHA256="73c5125cb79555401836159d861f1775bce7e23879ab0dbada8350813d6ae89a"
EXPECTED_HISTORICAL_SUMMARY_SHA256="b43676f7d95bd8599ad7be47b2b121a6f02b4314d4507f537d4e59b7c68d01c4"


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--parameters-authority",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()

    pp=json.loads(args.parameters_authority.read_text(encoding="utf-8"))
    if pp.get("schema")!="V5_MASKING_QUALIFICATION_PARAMETERS_AUTHORITY_V2":
        raise SystemExit("current parameter authority V2 is required")
    names={f.name for f in fields(MaskingQualificationParametersAuthorityV2)}
    parameters=MaskingQualificationParametersAuthorityV2(**{name:pp[name] for name in names})
    parameters.validate()
    if pp.get("parameter_authority_sha256")!=parameters.canonical_digest():
        raise SystemExit("parameter authority digest mismatch")

    script=args.repo/HISTORICAL_SCRIPT
    summary=args.repo/HISTORICAL_SUMMARY
    if not script.is_file() or not summary.is_file():
        raise SystemExit("historical nonlinear provenance file is missing")
    script_sha=sha256_file(script)
    summary_sha=sha256_file(summary)
    if script_sha!=EXPECTED_HISTORICAL_SCRIPT_SHA256:
        raise SystemExit(
            f"historical nonlinear script byte drift: expected {EXPECTED_HISTORICAL_SCRIPT_SHA256}, observed {script_sha}"
        )
    if summary_sha!=EXPECTED_HISTORICAL_SUMMARY_SHA256:
        raise SystemExit(
            f"historical nonlinear summary byte drift: expected {EXPECTED_HISTORICAL_SUMMARY_SHA256}, observed {summary_sha}"
        )
    text=script.read_text(encoding="utf-8")
    required=("HistGradientBoostingRegressor","max_iter=50","max_leaf_nodes=15","l2_regularization=1.0","maxf=32")
    for fragment in required:
        if fragment not in text:
            raise SystemExit(f"historical nonlinear script no longer proves {fragment!r}")
    authority=NonlinearCapacityModelAuthorityV1(
        authority_id="JEPA_V5_FULL104_NONLINEAR_CAPACITY_MODEL_AUTHORITY_V1",
        primary_parameters_authority_sha256=parameters.canonical_digest(),
        historical_nonlinear_script_sha256=script_sha,
        historical_nonlinear_summary_sha256=summary_sha,
    )
    authority.bind_primary_parameters(parameters)
    payload={
        "schema":"V5_NONLINEAR_CAPACITY_MODEL_AUTHORITY_V1",
        **authority.__dict__,
        "authority_sha256":authority.canonical_digest(),
        "historical_role":"MODEL_CAPACITY_PROVENANCE_ONLY__NO_DATA_TARGET_BURDEN_FOLD_SEED_OR_ROW_CAP_AUTHORITY",
        "training_authorized":False,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(payload["authority_sha256"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
