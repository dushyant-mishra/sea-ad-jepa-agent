from __future__ import annotations

import pandas as pd


FORBIDDEN_COVARIATE_TERMS = [
    "braak",
    "thal",
    "cerad",
    "patholog",
    "6e10",
    "abeta",
    "amyloid",
    "at8",
    "ptau",
    "ttau",
    "gfap",
    "iba1",
    "neun",
    "diagnosis",
    "dementia",
    "cognitive status",
    "ad neuropathological",
]


def audit_covariate_columns(covariate_columns: list[str]) -> pd.DataFrame:
    rows = []
    for col in covariate_columns:
        lower = col.lower()
        hits = [term for term in FORBIDDEN_COVARIATE_TERMS if term in lower]
        rows.append(
            {
                "covariate_column": col,
                "forbidden_term_hits": ";".join(hits),
                "leakage_risk": bool(hits),
                "allowed_for_stage39c": not bool(hits),
            }
        )
    return pd.DataFrame(rows)


def audit_oof_predictions(oof: pd.DataFrame) -> pd.DataFrame:
    if oof.empty:
        return pd.DataFrame(
            [
                {
                    "audit_item": "oof_predictions_present",
                    "pass": False,
                    "evidence": "OOF prediction table is empty",
                }
            ]
        )
    duplicate_rows = int(oof.duplicated(["condition", "target", "donor_id"]).sum())
    leakage_flag = bool(oof.get("heldout_donor_leakage_detected", pd.Series(False, index=oof.index)).astype(bool).any())
    clean_holdout_flag = bool(oof.get("clean_holdout_used", pd.Series(False, index=oof.index)).astype(bool).any())
    return pd.DataFrame(
        [
            {"audit_item": "no_duplicate_condition_target_donor_rows", "pass": duplicate_rows == 0, "evidence": f"duplicate_rows={duplicate_rows}"},
            {"audit_item": "heldout_donor_leakage_not_detected", "pass": not leakage_flag, "evidence": f"heldout_donor_leakage_detected={leakage_flag}"},
            {"audit_item": "clean_holdout_not_used", "pass": not clean_holdout_flag, "evidence": f"clean_holdout_used={clean_holdout_flag}"},
        ]
    )
