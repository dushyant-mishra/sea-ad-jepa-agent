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
LATER = Path("docs/agent/JEPA_HISTORICAL_CHRONOLOGY_RECOVERY_ROUNDS_21_24_20261102.md")
NEWER = Path("docs/agent/JEPA_HISTORICAL_CHRONOLOGY_RECOVERY_ROUNDS_25_29_20261102.md")
AUTH = "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
TYPES = {"scientific_experiment","implementation","hostile_review","repair",
         "acceptance","rejection","source_custody","chronology_correction",
         "custody_process",
          "independently_reproduced_implementation_defect_and_nontraining_repair",
          "confirmed_no_training_ci_collection_safety_gap_scoped_author_green_repair",
          "independent_legacy_automatic_ci_step_eligibility_safety_repair"}

def require(condition, message: str):
    if not condition:
        raise ValueError("JEPA_CONTINUOUS_CHRONOLOGY_REFUSAL: " + message)

def check(root: Path = ROOT):
    data = json.loads((root / LEDGER).read_text(encoding="utf-8"))
    index = json.loads((root / INDEX).read_text(encoding="utf-8"))
    chronology = (root / CHRONOLOGY).read_text(encoding="utf-8")
    protocol = (root / PROTOCOL).read_text(encoding="utf-8")
    additional = (root / ADDITIONAL).read_text(encoding="utf-8")
    later = (root / LATER).read_text(encoding="utf-8")
    require(data.get("schema") == "JEPA_CONTINUOUS_CHRONOLOGY_PROGRESS_V1", "schema")
    require(data.get("canonical_audit_pr") == 322 and
            data.get("active_handoff_pr") == 460 and
            data.get("historical_handoff_pr_323_is_superseded") is True,
            "PR322/460 custody")
    require(data.get("contract_path") == str(PROTOCOL), "protocol path")
    require(index.get("schema") == "JEPA_HISTORICAL_CHRONOLOGY_SOURCE_RECOVERY_V1",
            "history index schema")
    require(len(index.get("source_evidence", [])) >= 41, "historical source coverage")
    sources = {x.get("id") for x in index.get("source_evidence", [])}
    require({"stage35c","stage69","stage70","stage75_f8","stage81a2r",
             "f1_replay","stage76_f9","stage76_f10","stage77_f11",
             "stage78_f12","stage79_f13","v2_real_graph_vs_no_graph",
             "v2_strict_shuffle","v3_stage25_baselines",
             "v3_stage31_residual_graph","stage81a3_complete_qualification_record",
             "stage81a3r_historical_freeze1","stage81a3r_freeze1_machine_contract",
             "td19_depth_pseudostate_negative_control","stage73r_graph_prior_controls",
             "v5_within_operator_x4_redteam"}.issubset(sources),
            "missing historical evidence")
    for token in ("Stage76", "Stage77", "Stage78", "Stage79", "Stage69",
                  "Stage70", "Stage75F", "41,238", "real F1"):
        require(token.casefold() in chronology.casefold(), "history omission " + token)
    for token in ("Stage81A3", "masked student", "Stage27C",
                  "UCDQ", "14 donor-recurring", "Perceiver"):
        require(token.casefold() in additional.casefold(), "additional chronology omission " + token)
    for token in ("Stage81A3R", "Freeze1", "d_global=224", "TD19",
                  "depth-only", "Stage73R", "x4_within"):
        require(token.casefold() in later.casefold(), "later chronology omission " + token)
    # Rounds 25-29: additional already-executed external/atlas/GRN history.
    newer_path = NEWER
    newer = (root / newer_path).read_text(encoding="utf-8")
    require(index.get("additional_recovery_rounds_25_29_path") == str(newer_path),
            "newer source-index pointer")
    new_ids = {"v21_morabito_frozen_encoder_external_projection",
               "v21_grubman_six_group_zero_shot",
               "v22_rexach_olah_cellxgene_alignment",
               "discovery_atlas_targeted_45_gene_manifold_qc",
               "stage72b_morabito_541_pseudobulk_coactivity_edges",
               "stage74_directed_perturbation_hypothesis_audit"}
    require(new_ids.issubset(sources), "missing round25-29 primary sources")
    for token in ("Round 25", "Round 26", "Round 27", "Round 28", "Round 29",
                  "0.2237", "0.6234", "45/45", "541", "39/41", "NO_NEW"):
        require(token.casefold() in newer.casefold(), "newer chronology omission " + token)
    extra = index.get("milestones", {})
    require(extra.get("round29_source_index_reachability", {}).get("missing_git_blob_count") == 0,
            "source blob unavailable assertion")
    require(extra.get("round25_early_external_cohort_tests", {}).get("current_clean_benchmark_authority") is False,
            "old external cohort silently promoted")
    require(extra.get("round28_morabito_regulatory_ancestry", {}).get("validated_regulation") is False,
            "stage72 coactivity silently promoted")
    require(index.get("milestones", {}).get("historical_stage81a3r_freeze1", {}).get("declared") is True,
            "historical Freeze1 declaration missing")
    require(index["milestones"]["historical_stage81a3r_freeze1"].get("current_representation_winner") is False,
            "historical Freeze1 must not promote current dimension")
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
        # A duplicate appended after newer events must be classified as a
        # duplicate, not hidden behind the later date-order check.
        require(event["event_id"] not in ids, "duplicate events")
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
