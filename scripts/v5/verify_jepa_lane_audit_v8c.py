"""Static V8c append-only delta guard; no remote issuer or science authority."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DELTA = "results/target_discovery/unified_qualification_v1/JEPA_POST_V8B_DELTA_V8C_20261027.json"
NARRATIVE = "docs/agent/JEPA_POST_V8B_DELTA_V8C_20261027.md"
AUTHORITY = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
EXPECTED_HEADS = {
    457: "53ff7adc7eb01c84edb7abe623d67dfb848f408d",
    458: "3b08081d7fb3fa99cf1459b13cbe47d5b0962547",
    459: "57e707149b46ca011eee096f01dc08b64aeb8f9f",
    460: "3bf155717472c5eb6f2b91339bf45c5e4c45c732",
    461: "495350d477a0b7ba65c13dcab5032d443f939cd5",
    462: "67d2336155624a8657d2ef3320c9bfff175951ee",
}
EXPECTED_CI = {
    457: {40532275239, 40532274784},
    458: {40516953772, 40516953763},
    459: {40518058012},
    460: {40531398424, 40531398538},
    461: {40519155593, 40519155528},
    462: {40530824776, 40530825628, 40531130624},
}
CLASS_TAG = {
    457: "PUBLIC_REFERENCE_CONTEXT_ONLY",
    458: "13_HOSTILE_RED",
    459: "INDEPENDENT_X1_S1_S2_RED",
    460: "POINTER_REQUIRES_V8C_REFRESH",
    461: "8_NEW_HOSTILE_RED",
    462: "INDEPENDENT_TASK4_X1_SHORT_WRITE_RED",
}
REQUIRED_OLDER = (
    "docs/agent/JEPA_POST_V8A_DELTA_V8B_20261027.md",
    "results/target_discovery/unified_qualification_v1/JEPA_POST_V8A_DELTA_V8B_20261027.json",
    "results/target_discovery/unified_qualification_v1/JEPA_TAKEOVER_SUPPLEMENT_V8B_20261027.json",
    "results/target_discovery/unified_qualification_v1/JEPA_COMPLETE_TAKEOVER_FILE_INDEX_V8A_20261027.json",
)


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def validate(data, root):
    require(type(data) is dict and data.get("schema") == "JEPA_POST_V8B_DELTA_V8C_20261027", "V8c schema mismatch")
    require(data.get("authority") == AUTHORITY and data.get("no_qualification_promotion") is True,
            "science authorization promoted")
    require(data.get("append_only") is True, "append-only invariant missing")
    require(data.get("prior_audit_head") == "c07659ccce04bec18a43cc4a371ec0bf277c9255",
            "old V8b audit exact SHA rewritten")
    require(data.get("prior_active_successor_head") == EXPECTED_HEADS[460],
            "prior successor SHA rewritten")
    require(data.get("prior_files") == list(REQUIRED_OLDER), "historical prior source list changed")
    for name in REQUIRED_OLDER:
        require((root / name).is_file(), "missing older audit source " + name)
    require((root / NARRATIVE).is_file(), "missing V8c narrative")
    doc = (root / NARRATIVE).read_text(encoding="utf-8")
    for tag in ("X1-S1", "X1-S2", "#461", "#462", "T2-D", "NON", "X3", AUTHORITY):
        require(tag in doc, "V8c narrative missing guard: " + tag)
    rows = data.get("current")
    require(type(rows) is list and len(rows) == len(EXPECTED_HEADS), "V8c exact roster changed")
    require(all(type(x) is dict and type(x.get("pr")) is int for x in rows),
            "bad V8c PR row")
    require(len({x["pr"] for x in rows}) == len(rows), "duplicate V8c PR")
    require({x["pr"]: x.get("head") for x in rows} == EXPECTED_HEADS, "V8c exact heads changed")
    for row in rows:
        pr = row["pr"]
        require(re.fullmatch(r"[0-9a-f]{40}", row["head"]) is not None, "invalid SHA")
        require(CLASS_TAG[pr] in row.get("classification", ""), "review boundary promoted: " + str(pr))
        ci = row.get("ci")
        require(type(ci) is list and {x.get("run_id") for x in ci} == EXPECTED_CI[pr],
                "CI exact-run lineage altered: " + str(pr))
        require(all(type(x.get("result")) is str and x["result"] for x in ci), "missing CI result")
        require(type(row.get("action")) is str and row["action"], "missing current action")
    by = {x["pr"]: x for x in rows}
    require(by[462]["ci"][0].get("exact_head") == "e3b0c92c37336dfe16c459d85832f062c8cb2a48",
            "Linux focused reviewer commit misbound")
    require(by[462]["ci"][1].get("exact_head") == "e3b0c92c37336dfe16c459d85832f062c8cb2a48",
            "Linux full reviewer commit misbound")
    require(by[462]["ci"][2].get("exact_head") == EXPECTED_HEADS[462],
            "Windows reviewer commit misbound")
    evidence = data.get("evidence_boundaries", {})
    require(all(type(evidence.get(x)) is str for x in
                ("unified_task1", "task4", "ps_task1_2", "e2g", "training")),
            "missing evidence boundaries")
    require("not automatically" in evidence["unified_task1"], "lawful historical identities falsely invalidated")
    require("not an authenticated scan" in evidence["ps_task1_2"], "T2-D forgery promoted")
    require("no TF causal" in evidence["e2g"], "E2G biological claim promoted")
    require("TRAINING_OFF" in evidence["training"], "real training authorization promoted")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    validate(json.loads((args.repo_root / DELTA).read_text(encoding="utf-8")), args.repo_root)
    print("JEPA_V8C_DELTA_PASS__NEW_RED_PRESERVED__NO_AUTHORITY_ISSUED")


if __name__ == "__main__":
    main()
