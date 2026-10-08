#!/usr/bin/env python3
"""Apply the human SCP2167 provenance adjudication over frozen UCDQ evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


CONTRACT_HASHES = {
    "configs/v4/stage81a3_uniform_context_data_qualification.yaml": "b66c420f01741b5a044d2309ffdde0c8e20aceb1952400aff4f23bb559f48723",
    "results/v4/stage81a3_uniform_context_data_qualification_contract.json": "812678ba4f4f08523b91e18e1207e90f965a6b3873a10d4691d30e99f7460340",
}
ORIGINAL_OUTPUT_HASHES = {
    "results/v4/stage81a3_uniform_context_data_qualification.json": "dc976d3d51633b4693e2efae51189925a288b26aad2d3f7927ff6a95fa116a99",
    "results/v4/stage81a3_context_identifiability_decision.json": "165e733babee7b6a05bbd26c45c95f95db910d0ab6be933a8a128dfe6a07a0a9",
    "results/v4/stage81a3_context_dataset_role_matrix.csv": "234052599547f47230e2ab5857644dec9168f58a93aa1c94e239af2a610f4f54",
}
PUBLICATION = {
    "publication_title": "Slide-tags enables single-nucleus barcoding for multimodal spatial genomics.",
    "publication_doi": "10.1038/s41586-023-06837-4",
    "publication_pmid": "38093010",
    "publication_pmcid": "PMC10764288",
    "evidence_location": "Russell AJ et al., Nature 2024;625:101-109, human-cortex section and Data Availability statement",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def load_ucdq_module(project: Path):
    path = project / "scripts/v4/stage81a3_uniform_context_data_qualification.py"
    spec = importlib.util.spec_from_file_location("stage81a3_ucdq", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def verify_immutable_inputs(project: Path) -> dict[str, dict[str, Any]]:
    checks = {}
    for relative, expected in {**CONTRACT_HASHES, **ORIGINAL_OUTPUT_HASHES}.items():
        observed = sha256(project / relative)
        checks[relative] = {"expected_sha256": expected, "observed_sha256": observed, "pass": observed == expected}
    if not all(item["pass"] for item in checks.values()):
        raise RuntimeError("Frozen contract or original UCDQ history has changed; adjudication stopped")
    return checks


def adjudicate(project: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    immutable = verify_immutable_inputs(project)
    cfg = yaml.safe_load((project / "configs/v4/stage81a3_uniform_context_data_qualification.yaml").read_text(encoding="utf-8"))
    ucdq = load_ucdq_module(project)
    original_rows = pd.read_csv(project / "results/v4/stage81a3_context_dataset_role_matrix.csv").to_dict("records")
    scp_rows = [row for row in original_rows if row["dataset_id"] == "SCP2167"]
    if len(scp_rows) != 1:
        raise RuntimeError(f"Expected exactly one SCP2167 row, found {len(scp_rows)}")
    prior = scp_rows[0]
    expected = {
        "source_feature_count": 36601,
        "frozen4096_supported": 4096,
        "measurement_semantics": "RAW_UMI_COUNT",
        "spatial_entity_type": "NUCLEUS",
        "coordinate_class": "PHYSICAL_XY_UNKNOWN_UNITS",
        "pairing_class": "SAME_ENTITY_EXACT",
        "n_exact_matches": 4065,
    }
    for key, value in expected.items():
        observed = prior[key]
        if isinstance(value, int):
            observed = int(observed)
        if observed != value:
            raise RuntimeError(f"SCP2167 frozen evidence drift for {key}: {observed!r} != {value!r}")
    if abs(float(prior["frozen4096_support_fraction"]) - 1.0) > 1e-12:
        raise RuntimeError("SCP2167 frozen support fraction drift")
    if abs(float(prior["pairing_fraction"]) - 4065 / 4067) > 1e-12:
        raise RuntimeError("SCP2167 pairing fraction drift")

    role_input = {
        "spatial_entity_type": prior["spatial_entity_type"],
        "measurement_semantics": prior["measurement_semantics"],
        "pairing_class": prior["pairing_class"],
        "physical_geometry": bool(prior["physical_geometry"]),
        "frozen4096_supported": int(prior["frozen4096_supported"]),
        "frozen4096_support_fraction": float(prior["frozen4096_support_fraction"]),
        "source_feature_count": int(prior["source_feature_count"]),
        "pathology_blind_provenance": "NEUROTYPICAL_DECLARED",
        "exact_donors": int(prior["exact_donors"]),
        "forced_role": "",
    }
    adjudicated_role, role_reason = ucdq.role_for(role_input, cfg)
    if adjudicated_role != "CORE_SAME_ENTITY_BROAD_CONTEXT":
        raise RuntimeError(f"Unchanged frozen role gate produced unexpected role: {adjudicated_role}: {role_reason}")

    adjudicated_rows = []
    for row in original_rows:
        updated = dict(row)
        if row["dataset_id"] == "SCP2167":
            updated.update({
                "pathology_blind_provenance": "NEUROTYPICAL_DECLARED",
                "qualification_role": adjudicated_role,
                "a3_core_eligible": True,
                "quarantine_required": False,
                "reason": role_reason,
            })
        adjudicated_rows.append(updated)

    decisions = ucdq.identifiability(adjudicated_rows, cfg)
    expected_decisions = {
        "BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE": "YES",
        "CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE": "YES",
        "CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE": "YES",
    }
    if decisions != expected_decisions:
        raise RuntimeError(f"Frozen identifiability logic produced {decisions}, expected {expected_decisions}")

    eligible_high_plex = [
        row for row in adjudicated_rows
        if row["dataset_id"] == "doi:10.5061/dryad.x3ffbg7mw"
        and row["brain_region"] == "STG"
        and row["qualification_role"] == "CORE_CELL_RESOLVED_HIGH_PLEX_CONTEXT"
    ]
    if len(eligible_high_plex) != 5 or len({row["source_donor_id"] for row in eligible_high_plex}) != 2:
        raise RuntimeError("Fang STG replication evidence drift")
    if any(row["brain_region"] == "MTG" and row["qualification_role"].startswith("CORE_") for row in adjudicated_rows if row["dataset_id"] == "doi:10.5061/dryad.x3ffbg7mw"):
        raise RuntimeError("Quarantined Fang MTG evidence entered the core decision")

    addendum = {
        "stage": "STAGE81A3-UCDQ-HPA",
        "dataset_id": "SCP2167",
        "prior_provenance_class": prior["pathology_blind_provenance"],
        "adjudicated_provenance_class": "NEUROTYPICAL_DECLARED",
        "prior_role": prior["qualification_role"],
        "adjudicated_role": adjudicated_role,
        **PUBLICATION,
        "evidence_summary": "The primary peer-reviewed publication explicitly identifies the human prefrontal-cortex donor used for the reported Slide-tags experiment as neurotypical and identifies SCP2167 as the human-brain data deposition.",
        "pathology_values_used": False,
        "contract_changed": False,
        "thresholds_changed": False,
        "original_governance_incident_preserved": True,
        "human_adjudication": True,
        "unchanged_non_provenance_evidence": expected | {
            "frozen4096_support_fraction": float(prior["frozen4096_support_fraction"]),
            "direct_measurement": bool(prior["direct_measurement"]),
            "physical_geometry": bool(prior["physical_geometry"]),
            "n_spatial_entities": 4067,
            "pairing_fraction": float(prior["pairing_fraction"]),
            "duplicated_pairing_identifiers": 0,
        },
        "role_reason": role_reason,
        "immutable_input_hashes": immutable,
    }
    decision_addendum = {
        "stage": "STAGE81A3-UCDQ-HPA",
        "original_automated_result": {
            "final_classification": "REAL CONTEXT QUALIFICATION NOT IDENTIFIABLE",
            "reason": "SCP2167 publication provenance had not yet been human-adjudicated.",
            "governance_compliant_completion": False,
        },
        "human_provenance_adjudication_complete": True,
        "scp2167_adjudicated_role": adjudicated_role,
        **decisions,
        "final_classification": "REAL CONTEXT VALUE + CROSS-DONOR + CROSS-TECHNOLOGY QUALIFICATION IDENTIFIABLE",
        "broad_anchor": {"dataset_id": "SCP2167", "technology": "Slide-tags", "exact_donors": 1, "n_exact_paired_nuclei": 4065},
        "independent_high_plex_replication": {"dataset_id": "doi:10.5061/dryad.x3ffbg7mw", "region": "STG", "technology": "MERFISH", "experiments": 5, "exact_donors": 2, "frozen4096_supported": 954},
        "excluded_from_core_decision": {"fang_mtg_experiments": 5, "reason": "SURGICAL_TISSUE_PROVENANCE_REVIEW"},
        "context_benefit_demonstrated": False,
        "experiment_run": False,
        "context_model_training_started": False,
        "pathology_used_for_adjudication": False,
        "contract_changed": False,
        "thresholds_changed": False,
        "original_governance_incident_preserved": True,
    }
    return addendum, decision_addendum


def build_doc(addendum: dict[str, Any], decision: dict[str, Any]) -> str:
    return f"""# Stage81A3 SCP2167 Human Provenance Adjudication

## Chronology

The original automated UCDQ classified SCP2167 provenance as `UNKNOWN`, retained the dataset as `QUARANTINED_PENDING_GOVERNANCE`, and concluded `REAL CONTEXT QUALIFICATION NOT IDENTIFIABLE`. That result remains preserved. The original governance-compliant completion also remains `NO` because a generic `disease=normal` value was incidentally displayed before the audited reader ran. It was not used in qualification.

## Human publication adjudication

The human reviewer examined Russell AJ et al., *{addendum['publication_title']}* Nature 2024;625:101-109 (DOI `{addendum['publication_doi']}`, PMID `{addendum['publication_pmid']}`, PMCID `{addendum['publication_pmcid']}`). The primary publication describes the human prefrontal-cortex donor as neurotypical and identifies SCP2167 as the human-brain deposition.

This publication evidence changes SCP2167 provenance from `UNKNOWN` to `NEUROTYPICAL_DECLARED`. It does not use the incidental terminal value, modify the UCDQ contract, change a threshold, or relax an eligibility rule.

## Unchanged role-gate result

All previously computed non-provenance conditions remain unchanged: 36,601 source features, 4,096 frozen genes, raw UMI counts, nucleus entity type, physical XY coordinates with unknown units, 4,065/4,067 exact spatial matches, and no duplicated pairing identifiers. Applying the frozen gate changes the role from `QUARANTINED_PENDING_GOVERNANCE` to **`{addendum['adjudicated_role']}`**.

## Post-adjudication identifiability

- **BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE: {decision['BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE']}**
- **CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE: {decision['CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE']}**
- **CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE: {decision['CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE']}**

The broad anchor is one-donor Slide-tags SCP2167. Independent measured-subset replication is supplied by five eligible Fang STG MERFISH experiments across two donors. The five Fang MTG experiments remain quarantined and are excluded from the decision.

Final post-adjudication classification: **REAL CONTEXT VALUE + CROSS-DONOR + CROSS-TECHNOLOGY QUALIFICATION IDENTIFIABLE**.

Identifiable does not mean demonstrated. No context-benefit experiment, neighbor graph, masking, model training, optimizer update, or architecture change occurred.

ORIGINAL UCDQ GOVERNANCE-COMPLIANT COMPLETION: NO
UCDQ QUALIFICATION COMPUTATION COMPLETE: YES
HUMAN PROVENANCE ADJUDICATION COMPLETE: YES
CONTEXT BENEFIT DEMONSTRATED: NO
CONTEXT EXPERIMENT RUN: NO
STAGE81A3 FROZEN: NO
READY FOR STAGE81B: NO
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    args = parser.parse_args()
    project = Path(args.project_dir).resolve()
    addendum, decision = adjudicate(project)
    atomic_json(project / "results/v4/stage81a3_context_human_provenance_adjudication.json", addendum)
    atomic_json(project / "results/v4/stage81a3_context_identifiability_after_human_adjudication.json", decision)
    atomic_text(project / "docs/v4/STAGE81A3_CONTEXT_HUMAN_PROVENANCE_ADJUDICATION.md", build_doc(addendum, decision))
    print("UCDQ CONTRACT UNCHANGED: YES")
    print("ORIGINAL UCDQ GOVERNANCE-COMPLIANT COMPLETION: NO")
    print("UCDQ QUALIFICATION COMPUTATION COMPLETE: YES")
    print("HUMAN PROVENANCE ADJUDICATION COMPLETE: YES")
    print("SCP2167 PROVENANCE: NEUROTYPICAL_DECLARED")
    print(f"SCP2167 QUALIFICATION ROLE: {addendum['adjudicated_role']}")
    for key in ("BOUNDED_REAL_CONTEXT_VALUE_IDENTIFIABLE", "CROSS_DONOR_CONTEXT_VALUE_IDENTIFIABLE", "CROSS_TECHNOLOGY_CONTEXT_REPLICATION_IDENTIFIABLE"):
        print(f"{key}: {decision[key]}")
    print("CONTEXT BENEFIT DEMONSTRATED: NO")
    print("CONTEXT EXPERIMENT RUN: NO")
    print("CONTEXT MODEL TRAINING STARTED: NO")
    print("PATHOLOGY USED FOR ADJUDICATION: NO")
    print("REAL DEV RNA ACCESSED: NO")
    print("REAL SEALED RNA ACCESSED: NO")
    print("STAGE81A3 FROZEN: NO")
    print("READY FOR STAGE81B: NO")
    print("NOTHING STAGED COMMITTED OR PUSHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
