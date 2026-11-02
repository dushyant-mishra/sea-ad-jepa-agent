"""Static custody checks for append-only JEPA science/implementation progress.

A passing check proves metadata consistency only, not independent review,
physical source authentication, biological validity or training authority.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = Path("results/target_discovery/unified_qualification_v1/JEPA_CONTINUOUS_CHRONOLOGY_PROGRESS_V1.json")
CHRONOLOGY = Path("docs/agent/JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_20261102.md")
INDEX = Path("results/target_discovery/unified_qualification_v1/JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_20261102.json")
PROTOCOL = Path("docs/agent/JEPA_CONTINUOUS_CHRONOLOGY_AND_IMPLEMENTATION_CUSTODY_20261102.md")
ADDITIONAL = Path("docs/agent/JEPA_HISTORICAL_CHRONOLOGY_RECOVERY_ROUNDS_17_20_20261102.md")
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
TYPES = {"scientific_experiment","implementation","hostile_review","repair",
         "acceptance","rejection","source_custody","chronology_correction",
         "custody_process"}

def require(condition, message: str):
    if not condition:
        raise ValueError("JEPA_CONTINUOUS_CHRONOLOGY_REFUSAL: " + message)

def check(root: Path = ROOT):
    data = json.loads((root / LEDGER).read_text(encoding="utf-8"))
    index = json.loads((root / INDEX).read_text(encoding="utf-8"))
    chronology = (root / CHRONOLOGY).read_text(encoding="utf-8")
    protocol = (root / PROTOCOL).read_text(encoding="utf-8")
    additional = (root / ADDITIONAL).read_text(encoding="utf-8")
    require(data.get("schema") == "JEPA_CONTINUOUS_CHRONOLOGY_PROGRESS_V1", "schema")
    require(data.get("canonical_audit_pr") == 322 and
            data.get("active_handoff_pr") == 460 and
            data.get("historical_handoff_pr_323_is_superseded") is True,
            "PR322/460 custody")
    require(data.get("contract_path") == str(PROTOCOL), "protocol path")
    require(index.get("schema") == "JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_V1",
            "history index schema")
    require(len(index.get("source_evidence", [])) >= 27, "historical source coverage")
    sources = {x.get("id") for x in index.get("source_evidence", [])}
    require({"stage35c","stage69","stage70","stage75_f8","stage81a2r",
             "f1_replay","stage76_f9","stage76_f10","stage77_f11",
             "stage78_f12","stage79_f13","v2_real_graph_vs_no_graph",
             "v2_strict_shuffle","v3_stage25_baselines",
             "v3_stage31_residual_graph","stage81a3_complete_qualification_record"}.issubset(sources),
            "missing historical evidence")
    for token in ("Stage76", "Stage77", "Stage78", "Stage79", "Stage69",
                  "Stage70", "Stage75F", "41,238", "real F1"):
        require(token.casefold() in chronology.casefold(), "history omission " + token)
    for token in ("Stage81A3", "masked student", "Stage27C",
                  "UCDQ", "14 donor-recurring", "Perceiver"):
        require(token.casefold() in additional.casefold(), "additional chronology omission " + token)
    for token in ("PR #322", "PR #460", "implementation",
                  "independent review", "frozen", "update"):
        require(token.casefold() in protocol.casefold(), "continuity omission " + token)
    events = data.get("records")
    require(isinstance(events, list) and len(events) >= 3, "missing events")
    ids = []
    prior_date = ""
    required = ("event_id","date_utc","workstream","implementation_pr",
                "implementation_head","source_inputs","change_type",
                "what_already_existed","new_work_or_result",
                "negative_or_counterfactual_evidence","test_review_scope",
                "independent_review","authority_before","authority_after",
                "open_specific_deltas","historical_supersession","evidence_links")
    for event in events:
        require(type(event) is dict and all(k in event for k in required), "event fields")
        require(type(event["event_id"]) is str and event["event_id"].strip(), "event id")
        ids.append(event["event_id"])
        date = event["date_utc"]
        require(type(date) is str and len(date) >= 10 and date[:10] >= prior_date, "date ordering")
        prior_date = date[:10]
        require(event["change_type"] in TYPES, "unrecognized change type")
        for k in ("workstream","what_already_existed","new_work_or_result",
                  "negative_or_counterfactual_evidence","test_review_scope",
                  "independent_review","historical_supersession"):
            require(type(event[k]) is str and event[k].strip(), "missing " + k)
        require(event["authority_before"] == AUTH and event["authority_after"] == AUTH,
                "authority promotion requires a separate new protocol/version")
        require(type(event["source_inputs"]) is list and event["source_inputs"], "source inputs")
        require(type(event["open_specific_deltas"]) is list, "specific deltas type")
        require(type(event["evidence_links"]) is list and event["evidence_links"], "evidence links")
        require(event["implementation_pr"] is None or
                (type(event["implementation_pr"]) is int and event["implementation_pr"] > 0),
                "implementation PR")
        require(event["implementation_head"] is None or
                (type(event["implementation_head"]) is str and len(event["implementation_head"]) == 40),
                "implementation head")
        for source in event["source_inputs"]:
            require(type(source) is dict and type(source.get("path")) is str and
                    (root / source["path"]).is_file(), "source file identity/availability")
            require(type(source.get("role")) is str and bool(source["role"]), "source role")
    require(len(set(ids)) == len(ids), "duplicate events")
    return {"events": len(events), "historical_sources": len(sources), "authority": AUTH}

if __name__ == "__main__":
    result = check()
    print("JEPA_CONTINUOUS_CHRONOLOGY_CUSTODY_PASS__NO_SCIENCE_PROMOTION", result)
