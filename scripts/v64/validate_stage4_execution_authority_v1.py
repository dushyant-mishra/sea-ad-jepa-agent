#!/usr/bin/env python3
"""Outcome-blind Stage-4 authority validator.

This validator checks custody, frozen-rule identity and governance only.
It contains no RNA×ATAC multiplication/correlation code and cannot authorize Stage 4.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

CONTRACT_PATH = "results/v64/V66_STAGE4_EXECUTION_AUTHORITY_CONTRACT_V3.json"

FORBIDDEN_MANIFEST_KEYS = {
    "correspondence_result",
    "delta",
    "delta_gene_balanced",
    "linked_minus_control",
    "p_value",
    "lcb95",
    "LCB95",
}


class Stop(RuntimeError):
    pass


def sha256_file(path: str | os.PathLike[str]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _require(condition, message):
    if not condition:
        raise Stop(message)


def _walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v)


def validate_manifest_structural(manifest: dict, contract: dict) -> list[str]:
    """Validate frozen declarations without touching any scientific value."""
    errors = []

    def check(cond, msg):
        if not cond:
            errors.append(msg)

    check(manifest.get("schema") == "V66_STAGE4_AUTHORITY_INPUT_MANIFEST_V1",\n          "BAD_SCHEMA")\n    check(set(manifest) == {"schema","correspondence_opened","stage4_authorized","training","multimodal_training","Morabito","TD60","phase_b_aggregate_binding","qualifying_donors","metacells","microglia_covered","genes","intervals","pairs","t5_rows","t3_nnz","t4_nnz","pairs_meeting_minimum_donors","availability_state_vocabulary","statistical_rules","missingness_rules","requested_actions","files"}, "TOP_LEVEL_SCHEMA_DRIFT")
    check(manifest.get("correspondence_opened") is False,
          "CORRESPONDENCE_MUST_BE_UNOPENED")
    check(manifest.get("stage4_authorized") is False,
          "STAGE4_MUST_REMAIN_UNAUTHORIZED")
    check(manifest.get("training") == "OFF", "TRAINING_MUST_BE_OFF")
    check(manifest.get("multimodal_training") == "OFF",
          "MULTIMODAL_TRAINING_MUST_BE_OFF")
    check(manifest.get("Morabito") == "PROTECTED", "MORABITO_MUST_BE_PROTECTED")
    check(manifest.get("TD60") == "BLOCKED", "TD60_MUST_BE_BLOCKED")

    keys = set(_walk_keys(manifest))
    bad = sorted(keys & FORBIDDEN_MANIFEST_KEYS)
    if bad:
        errors.append("OUTCOME_OR_AUTHORIZATION_FIELD_PRESENT:" + ",".join(bad))

    frozen = contract["frozen_statistical_rules"]
    got = manifest.get("statistical_rules", {})
    for key in (
        "primary_weighting",
        "mandatory_companion",
        "sensitivity_weighting",
        "bootstrap_unit",
        "bootstrap_replicates",
        "bootstrap_seed",
        "randomized_null_denominator",
        "forced_identical_pairs_excluded_from_calibration",
        "r1", "r2", "r3", "r3_required_label",
        "primary_correlation",
        "primary_distance",
        "nuisance_basis_terms",
        "ridge_alpha",
        "cross_fitting_unit",
        "minimum_microglia_per_donor",
        "minimum_metacells_per_donor",
        "minimum_donors_per_edge",
        "metacell_target_size",
        "metacell_hvg",
        "metacell_pc",
        "metacell_n_init",
        "metacell_seed",
    ):
        check(got.get(key) == frozen[key], "RULE_DRIFT:" + key)

    check(manifest.get("availability_state_vocabulary")
          == contract["frozen_state_vocabulary"],
          "STATE_VOCABULARY_DRIFT")

    missing = contract["missingness_rules"]
    got_missing = manifest.get("missingness_rules", {})
    for key, value in missing.items():
        check(got_missing.get(key) == value, "MISSINGNESS_RULE_DRIFT:" + key)

    check(manifest.get("phase_b_aggregate_binding")
          == contract["accepted_execution_parent"]["phase_b_aggregate_binding"],
          "AGGREGATE_BINDING_DRIFT")
    check(manifest.get("qualifying_donors")
          == contract["accepted_execution_parent"]["qualifying_donors"],
          "QUALIFYING_DONOR_COUNT_DRIFT")
    check(manifest.get("metacells")
          == contract["accepted_execution_parent"]["metacells"],
          "METACELL_COUNT_DRIFT")
    check(manifest.get("t5_rows")
          == contract["accepted_execution_parent"]["t5_rows"],
          "T5_ROW_COUNT_DRIFT")
    for key, token in (
        ("microglia_covered", "MICROGLIA_COUNT_DRIFT"),
        ("genes", "GENE_COUNT_DRIFT"),
        ("intervals", "INTERVAL_COUNT_DRIFT"),
        ("pairs", "PAIR_COUNT_DRIFT"),
        ("t3_nnz", "T3_NNZ_DRIFT"),
        ("t4_nnz", "T4_NNZ_DRIFT"),
        ("pairs_meeting_minimum_donors", "MIN_DONOR_PAIR_COUNT_DRIFT"),
    ):
        check(manifest.get(key) == contract["accepted_execution_parent"][key], token)

    prohibited_actions = set(manifest.get("requested_actions", []))
    if prohibited_actions:
        errors.append("REQUESTED_ACTIONS_MUST_BE_EMPTY_BEFORE_AUTHORIZATION")

    return errors


def validate_file_bindings(manifest: dict, contract: dict) -> list[str]:
    errors = []
    files = manifest.get("files", {})

    def bind(label, expected):
        item = files.get(label)
        if not item:
            errors.append("MISSING_FILE_BINDING:" + label)
            return
        path = item.get("path")
        if not path or not os.path.isfile(path):
            errors.append("FILE_NOT_FOUND:" + label)
            return
        got = sha256_file(path)
        if got != expected:
            errors.append(f"DIGEST_MISMATCH:{label}:{got}:{expected}")

    for label, expected in contract["frozen_authority_digests"].items():
        bind(label, expected)
    for filename, expected in contract["substrate_shards_sha256"].items():
        bind(filename, expected)

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    contract = load_json(CONTRACT_PATH)
    manifest = load_json(args.manifest)

    errors = validate_manifest_structural(manifest, contract)
    errors.extend(validate_file_bindings(manifest, contract))

    verdict = ("READY_FOR_INDEPENDENT_AUDIT__STAGE4_STILL_NOT_AUTHORIZED"
               if not errors else "FAIL_CLOSED")

    receipt = {
        "schema": "V66_STAGE4_EXECUTION_AUTHORITY_VALIDATION_RECEIPT_V1",
        "contract_path": CONTRACT_PATH,
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "manifest_path": args.manifest,
        "manifest_sha256": sha256_file(args.manifest),
        "verdict": verdict,
        "errors": errors,
        "correspondence_opened": False,
        "stage4_authorized": False,
        "training": "OFF",
        "Morabito": "PROTECTED",
        "TD60": "BLOCKED",
        "explicit_non_authority": (
            "A PASS means only that custody and frozen-rule declarations are "
            "ready for independent audit. A separate successor authorization "
            "artifact is required before any Stage-4 biological computation."
        ),
    }

    out = Path(args.out)
    if out.exists():
        raise Stop("STOP_OUTPUT_EXISTS")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(verdict)
    if errors:
        for e in errors:
            print(e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
