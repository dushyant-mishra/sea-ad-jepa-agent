#!/usr/bin/env python3
"""SUPERSEDED — fail-closed tombstone for the 2026-09-17 partial freeze builder.

This script previously emitted a partial prospective freeze package containing a
placeholder support root, MaskingBurdenLadderAuthorityV1, and RunContractV2-era
source roles. Those semantics are superseded by the current 2026-09-18 builder
chain and must never be used to construct a FULL104 terminal package.

Historical bytes remain recoverable from Git history. The current working tree
keeps only this tombstone so accidental invocation cannot manufacture a competing
"freeze status" artifact.
"""
from __future__ import annotations

SUPERSEDED_BY = (
    "build_full104_target_evidence_budget_template_authority_v1_20260918.py; "
    "build_full104_burden_ladder_authority_v2_20260918.py; "
    "build_full104_masking_design_authority_v2_20260918.py; "
    "build_full104_masking_run_contract_v4_20260918.py"
)


def main() -> int:
    raise SystemExit(
        "SUPERSEDED_FAIL_CLOSED: build_full104_masking_freeze_status_20260917.py "
        "must not be used for current FULL104 authority. Use the 20260918 current "
        f"builder chain: {SUPERSEDED_BY}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
