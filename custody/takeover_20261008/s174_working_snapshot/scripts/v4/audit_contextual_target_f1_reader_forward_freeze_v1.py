#!/usr/bin/env python3
"""Fail-fast pre-result authority audit for the F1 reader/forward freeze.

This script intentionally opens no expression arrays and imports no model code.
It records the exact point at which the controlling freeze cannot proceed without
inventing a nuisance-column construction rule.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/contextual_teacher_target_v1_f1_reader_forward_authority_freeze_20260902"
STOP = "STOP_F1_NUISANCE_AUTHORITY_UNRESOLVED"

FILES = {
    "legal_boolean_zip": (ROOT / "outputs/CONTEXTUAL_TEACHER_TARGET_V1_F1_LEGAL_BOOLEAN_REPAIR_REVIEW_20260902.zip", "805893791d8290186ee948f10429681c0fb3af6880d5fc2ad7001214bcb2f3e4"),
    "legal_boolean_manifest": (ROOT / "outputs/contextual_teacher_target_v1_f1_legal_boolean_repair_20260902/F1_LEGAL_BOOLEAN_REPAIR_MANIFEST.csv", "e95aac28c3dacaeba94b202a2be53b46e94c848dd7fbb433b9d99b58efa94976"),
    "decision_truth_table": (ROOT / "outputs/contextual_teacher_target_v1_f1_decision_truth_table_repair_20260902/F1_FINAL_DECISION_TRUTH_TABLE_V2.json", "76d420a0aa71f9b062b7394453f1f33282f7c78a956fc950fceb7ead682dcf5e"),
    "decision_v4": (ROOT / "scripts/v4/contextual_target_f1_decision_v4.py", "5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913"),
    "integration_v4": (ROOT / "scripts/v4/contextual_target_f1_decision_integration_v4.py", "5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a"),
    "population_component_v2": (ROOT / "scripts/v4/contextual_target_f1_querydesign_decision_v2.py", "ac8157105b66ccd1617efb3740768a91711b429e5288afc34fb9a54adedcc462"),
    "assignments": (ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv", "12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617"),
    "observation_states": (ROOT / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz", "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"),
    "primary_null_map": (ROOT / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv", "aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6"),
    "f0_constructor": (ROOT / "src/sea_ad_jepa/v4/contextual_query_local.py", "6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa"),
    "f0_slow_reference": (ROOT / "scripts/v4/contextual_target_v1_f0_slow_reference.py", "80cd7aca623452355ba1a5b67fff77280e25cd9c83465c7fdb8222c8c97090b6"),
    "encoder": (ROOT / "src/sea_ad_jepa/v4/ipb_jepa.py", "732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a"),
    "tokenizer": (ROOT / "src/sea_ad_jepa/v4/gene_tokenizer.py", "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4"),
    "u0_checkpoint": (ROOT / "exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt", "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4"),
    "reader_split": (ROOT / "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv", "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"),
    "full104_row_lineage": (ROOT / "outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ROW_LINEAGE.csv", "a6065751667b35a38c5990107c6b3f0177e262f7d145addb24bea24206eeb61b"),
    "evidence_mask_contract": (ROOT / "outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_EVIDENCE_MASK_CONTRACT.md", "d1eefdab177501a00370d71521ae86932e60540fb9f769dfe2b56c7994ca5c5a"),
}

SEMANTIC = {
    "cell_weight_semantic_root": "018d80428c25a0060168a942ca03dc9e814783463cc077e3661008ba5f7b5eeb",
    "namespace_semantic_root": "595fd8bc860b13ce9ec2a957b0f3d92f850effcb51ae6e2f06b8c5d25d7bd53f",
    "f0_output_root": "e45dd8d885c4f6918bcaf0b24bde971c08c16322b27555e112693f46e42ddb4b",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def dump(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    checked = []
    for name, (path, expected) in FILES.items():
        actual = sha(path) if path.is_file() else None
        checked.append({"authority": name, "path": rel(path), "expected_sha256": expected, "actual_sha256": actual, "pass": actual == expected})
    if not all(x["pass"] for x in checked):
        raise RuntimeError("STOP_F1_READER_FORWARD_FREEZE_AUTHORITY_MISMATCH")

    assignment_audit = json.loads((ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENT_AUDIT.json").read_text(encoding="utf-8"))
    namespace_audit = json.loads((ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_ADDRESS_NAMESPACE_AUDIT.json").read_text(encoding="utf-8"))
    f0_root = (ROOT / "outputs/contextual_teacher_target_v1_f0_implementation_20260901/CONTEXTUAL_TARGET_V1_F0_OUTPUT_MANIFEST_ROOT_SHA256.txt").read_text(encoding="utf-8").strip()
    if assignment_audit["cell_weight_authority_sha256"] != SEMANTIC["cell_weight_semantic_root"] or namespace_audit["ordered_namespace_semantic_sha256"] != SEMANTIC["namespace_semantic_root"] or f0_root != SEMANTIC["f0_output_root"]:
        raise RuntimeError("STOP_F1_READER_FORWARD_FREEZE_AUTHORITY_MISMATCH")

    with FILES["assignments"][0].open("r", encoding="utf-8-sig", newline="") as f:
        assignments = list(csv.DictReader(f))
    pairs = {(r["canonical_cell_id"], int(r["selected_query_address"])) for r in assignments}
    if len(assignments) != 44_496 or len(pairs) != 43_108:
        raise RuntimeError("STOP_F1_FORWARD_COUNT_MISMATCH")

    evidence = FILES["evidence_mask_contract"][0].read_text(encoding="utf-8")
    required_evidence_clauses = [
        "c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f",
        "state[r,j]=MEASURED_SCALAR and j!=q",
        "floor(p*|E|/100)",
        "20 subset 40 subset 60 subset 80 subset 100",
        "At 100%, all of `E` is selected",
        "query scalar is withheld at every level",
    ]
    if not all(x in evidence for x in required_evidence_clauses):
        raise RuntimeError("STOP_F1_EVIDENCE_MASK_AUTHORITY_UNRESOLVED")

    evidence_doc = {
        "status": "RESOLVED_PROSPECTIVE_PRE_RESULT",
        "path": rel(FILES["evidence_mask_contract"][0]),
        "sha256": FILES["evidence_mask_contract"][1],
        "levels_percent": [20, 40, 60, 80, 100],
        "primary_level_percent": 60,
        "seed_sha256": "c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f",
        "mask_scope": "query-level because q is removed before ranking",
        "nested": True,
        "one_hundred_percent": "all and only MEASURED_SCALAR addresses except q",
        "measured_zero_retained": True,
        "independent_reconstruction": "filter state code MEASURED_SCALAR excluding q; SHA256(seed|canonical-row-locator|decimal-q|decimal-j); sort digest bytes then integer address; take floor(p*|E|/100)",
    }
    dump(OUT / "F1_EVIDENCE_MASK_AUTHORITY.json", evidence_doc)

    forward_audit = {
        "status": "COUNT_RECOMPUTED_METADATA_ONLY_NOT_FROZEN_DUE_TO_NUISANCE_STOP",
        "assignment_rows": len(assignments),
        "unique_cell_query_pairs": len(pairs),
        "computational_dedup_opportunities": len(assignments) - len(pairs),
        "forwards_per_unique_cell_query": 11,
        "future_expensive_forward_identities": len(pairs) * 11,
        "model_forward_executed": False,
        "candidate_outcome_computed": False,
    }
    dump(OUT / "F1_FUTURE_FORWARD_AUDIT.json", forward_audit)

    searched = [
        ROOT / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_DECISION_LOGIC_PROPOSAL.md",
        ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_adjudicator_repair_20260902/F1_DECISION_ENGINE_INTEGRATION_CONTRACT.md",
        ROOT / "scripts/v4/contextual_target_f1_decision_integration_v4.py",
        ROOT / "outputs/contextual_teacher_target_v1_f1_decision_truth_table_repair_20260902/F1_DECISION_LOGIC_PROPOSAL_FROZEN_COPY.md",
    ]
    nuisance = {
        "status": STOP,
        "searched_authorities": [{"path": rel(p), "sha256": sha(p)} for p in searched],
        "what_is_frozen": {
            "semantic_categories": ["source_indicators", "operator_mixture_fractions", "recipient_physical_support", "recipient_depth", "correct_minus_null_visible_depth", "correct_minus_null_measured_zero_rate"],
            "downstream_rule": "center columns; lexicographic rank selection; frozen numerical rank tolerance; HC3; t df n-rank; cross-source replication",
        },
        "missing_conclusion_bearing_authority": [
            "denominator and aggregation hierarchy for operator_mixture_fractions",
            "address set, denominator, and cell/donor aggregation for recipient_physical_support",
            "whether recipient_depth is library size, nonzero count, sum normalized values, or another transform; its aggregation and scaling",
            "whether correct_minus_null_visible_depth uses counts, normalized-value sums, nonzero breadth, or another depth definition; its evidence level and aggregation",
            "denominator, evidence level, weighting, and aggregation for correct_minus_null_measured_zero_rate",
            "exact categorical reference coding, output column order, dtype, and any standardization",
        ],
        "why_no_derivation_was_made": "The frozen sources name categories but provide no executable or mathematical column-construction formula. Several lawful formulas are not equivalent. Selecting one now would invent a result-bearing nuisance authority after the query design was frozen.",
        "required_resolution": "Prospectively authorize exact formulas and byte-level serialization for all six categories without inspecting candidate model outcomes.",
        "expression_opened": False,
        "model_forward_executed": False,
        "candidate_outcome_inspected": False,
        "training_or_ema": False,
    }
    dump(OUT / "F1_NUISANCE_AUTHORITY.json", nuisance)

    authority = {
        "terminal_status": STOP,
        "file_authorities": checked,
        "semantic_authorities": SEMANTIC,
        "evidence_mask_authority_resolved": True,
        "reader_freeze_completed": False,
        "forward_identity_freeze_completed": False,
        "nuisance_authority_frozen": False,
        "fail_fast_reason": "exact nuisance construction is absent from prior frozen authority",
        "no_expression_or_model_outcomes_accessed": True,
        "assignments_randomization_null_truth_table_unchanged": True,
    }
    dump(OUT / "F1_READER_FORWARD_FREEZE_AUTHORITY.json", authority)

    snapshot = OUT / "source_snapshot"
    snapshot.mkdir(exist_ok=True)
    shutil.copy2(Path(__file__), snapshot / Path(__file__).name)
    source_rows = [{"path": rel(Path(__file__)), "sha256": sha(Path(__file__))}]
    with (OUT / "F1_READER_FORWARD_SOURCE_MANIFEST.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "sha256"], lineterminator="\n"); w.writeheader(); w.writerows(source_rows)

    handoff = f"""# F1 reader/forward/nuisance freeze — external review handoff\n\nTerminal: `{STOP}`.\n\nAll supplied file authorities and three semantic roots matched. The prospective evidence-mask authority is present and exact. Metadata-only recomputation confirms 44,496 assignments, 43,108 unique `(cell,q)` pairs, 1,388 compute-only dedup opportunities, and 474,188 planned forward identities.\n\nThe run stopped before reader implementation/parity and before forward-identity publication because prior frozen authority does not define the six nuisance columns mathematically or executably. Only category names and the downstream HC3/rank procedure exist. Choosing among non-equivalent depth/support/aggregation definitions now would violate the instruction not to invent nuisance authority.\n\nNo expression, checkpoint tensors, candidate outcome, model forward, training, or EMA was accessed. The assignment file, CSPRNG authority, null map, namespace, truth table, and decision code were not modified.\n\nRequired next authority: an outcome-blind prospective formula/serialization contract for every nuisance category listed in `F1_NUISANCE_AUTHORITY.json`.\n"""
    (OUT / "F1_READER_FORWARD_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff, encoding="utf-8")

    entries = []
    for p in sorted(x for x in OUT.rglob("*") if x.is_file() and x.name != "F1_READER_FORWARD_MANIFEST.csv"):
        entries.append({"path": str(p.relative_to(OUT)).replace("\\", "/"), "bytes": p.stat().st_size, "sha256": sha(p)})
    with (OUT / "F1_READER_FORWARD_MANIFEST.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256"], lineterminator="\n"); w.writeheader(); w.writerows(entries)
    print(json.dumps({"terminal_status": STOP, "output": rel(OUT), "manifest_sha256": sha(OUT / "F1_READER_FORWARD_MANIFEST.csv"), "unique_cell_q": len(pairs), "future_forwards": len(pairs) * 11}))


if __name__ == "__main__":
    main()
