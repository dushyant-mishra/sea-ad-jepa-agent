#!/usr/bin/env python3
"""Read-only, fail-closed audit of PR121 readiness claims against committed receipts.

The V2 registry and every historical receipt are immutable evidence. This tool
DOES NOT rewrite either and DOES NOT assert scientific independence. It checks
only newly evidenced completion against stale readiness claims. Passing tests
on fixtures does not mean the committed V2 registry passes.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "evidence/CURATOR_ASSERTION_REGISTRY_V2.json"
RECEIPTS = {
    "GSE301119": "evidence/gse301119_independent_repro/GSE301119_INDEPENDENT_REPRODUCTION_RECEIPT_V1.json",
    "GSE254205": "evidence/gse254205_independent_repro/GSE254205_BULK_INDEPENDENT_REPRODUCTION_V1.json",
    "GSE311359": "evidence/gse311359_v2_idkeyed/GSE311359_ID_KEYED_RECEIPT_V2.json",
    "GSE178317": "evidence/gse178317_engagement_repro/GSE178317_ENGAGEMENT_INDEPENDENT_RECEIPT_V1.json",
}


def load(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"MISSING_EVIDENCE: {path}")
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError(f"NOT_AN_OBJECT: {path}")
    return obj


def check(registry: dict, evidence: dict[str, dict]) -> list[str]:
    errors = []
    assertions = registry.get("assertions", {})
    if not isinstance(assertions, dict):
        return ["INVALID_ASSERTION_REGISTRY"]
    if set(RECEIPTS) - assertions.keys():
        errors.append("MISSING_REQUIRED_STUDY_ASSERTION")
    if set(RECEIPTS) - evidence.keys():
        errors.append("MISSING_REQUIRED_RECEIPT")
    if errors:
        return errors
    a = assertions
    g = evidence["GSE301119"]
    modalities = g.get("modalities", {})
    if not isinstance(modalities, dict) or set(modalities) != {"CRISPRi", "CRISPRa"}:
        errors.append("GSE301119_RECEIPT_MODALITIES_MISSING")
    else:
        for name in ("CRISPRi", "CRISPRa"):
            m = modalities[name]
            if (m.get("verdict") != "AGREE"
                or m.get("target_order_matches") is not True
                or m.get("feature_order_matches") is not True
                or any(v != 0 for v in m.get("per_donor_support_mask_mismatches", {}).values())
                or set(m.get("per_donor_support_mask_mismatches", {})) != {"D1", "D2"}
                or m.get("cross_donor_mean_mask_mismatches") != 0
                or not (m.get("per_donor_max_abs_delta", {}).get("D1", float("inf")) <= 1e-9)
                or not (m.get("per_donor_max_abs_delta", {}).get("D2", float("inf")) <= 1e-9)):
                errors.append(f"GSE301119_UNQUALIFIED_RECEIPT_{name}")
    if g.get("synthetic_sign_checks", {}).get("planted_fixture_ok") is not True or g.get("synthetic_sign_checks", {}).get("swapped_numerator_denominator_negates_ok") is not True:
        errors.append("GSE301119_SIGN_CONTROLS_NOT_DEMONSTRATED")
    if not any(x.startswith("GSE301119_") for x in errors):
        if a["GSE301119"].get("independent_reproduction") != "IMPLEMENTATION_REPRODUCED":
            errors.append("GSE301119_STATUS_MUST_BE_IMPLEMENTATION_REPRODUCED_NOT_INDEPENDENT")
    b = evidence["GSE254205"]
    rows = b.get("rows_where_round_to_stored_decimals_matches_exactly", {})
    if (b.get("verdict") != "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION"
        or b.get("rounding_fully_explains_every_delta") is not True
        or set(rows) != {"AB_vs_NT", "AB_GNE_vs_AB", "AB_GNE_vs_NT"}
        or any(rows[k] != 36117 for k in rows)
        or b.get("declared_tolerance_met_at_full_precision") is not False):
        errors.append("GSE254205_RECEIPT_NOT_STORED_PRECISION_REPRODUCED")
    elif a["GSE254205"].get("independent_reproduction") != "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION":
        errors.append("GSE254205_STATUS_STALE_OR_OVERCLAIMED")
    q = evidence["GSE311359"]
    if (q.get("schema") != "GSE311359_ID_KEYED_EFFECTS_V2"
        or q.get("phantom_units_detected") != 0
        or q.get("unique_guide_feature_ids") != 381
        or set(q.get("bin1_cis_elements_kept_separate", [])) != {"BIN1_enh_1", "BIN1_enh_2", "BIN1_enh_2_AS"}):
        errors.append("GSE311359_RECEIPT_NOT_ID_KEYED_QUALIFIED")
    else:
        s = a["GSE311359"]
        if s.get("etl_status") != "PASS_DEVELOPMENT_ETL_ID_KEYED":
            errors.append("GSE311359_V2_REBUILD_STATUS_STALE")
        if s.get("biological_estimability") != "SEQUENCE_IDENTITY_UNPROVEN_CIS_CAUSALITY_UNPROVEN":
            errors.append("GSE311359_BIOLOGICAL_SCOPE_STATUS_STALE")
        if s.get("independent_reproduction") not in {"NOT_DONE", "ID_KEYED_V1_NONBIN1_PARITY_ONLY"}:
            errors.append("GSE311359_INDEPENDENCE_OVERCLAIMED_OR_STALE")
    h = evidence["GSE178317"]
    if (h.get("verdict") != "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION"
        or h.get("rounding_explains_every_delta") is not True
        or h.get("targets_compared") != 39
        or h.get("rows_exact_on_round") != 39):
        errors.append("GSE178317_RECEIPT_NOT_STORED_PRECISION_REPRODUCED")
    elif a["GSE178317"].get("independent_reproduction") != "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION":
        errors.append("GSE178317_STATUS_STALE_OR_OVERCLAIMED")
    # Unrelated scientific STOPs and exposure controls MUST survive a registry revision.
    if a["GSE335887"].get("outcome_exposure") != "UNOPENED_RESERVED":
        errors.append("GSE335887_PROTECTED_EXPOSURE_PROMOTED")
    if a["GSE175721"].get("etl_status") != "STOP_AUTHOR_SOURCE_MISSING":
        errors.append("GSE175721_AUTHOR_SOURCE_STOP_REMOVED")
    if a["GSE254205"].get("outcome_exposure") != "INSPECTED_DEVELOPMENT_BULK_THREE_CONTRASTS_ONLY":
        errors.append("GSE254205_BULK_EXPOSURE_PROMOTED")
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--registry", type=Path)
    args = ap.parse_args(argv)
    try:
        registry = load(args.registry or args.root / REGISTRY)
        evidence = {study: load(args.root / rel) for study, rel in RECEIPTS.items()}
        errors = check(registry, evidence)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL_EVIDENCE_READ {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print("FAIL " + error)
        return 1
    print("PASS_RECEIPT_READINESS_CONSISTENCY (scope: metadata status only; NO scientific authority)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
