"""Stage 3 — tail freeze, confirmation numeric AT8, and the frozen adjudication.

Runs the frozen T0 V20 procedure exactly as registered. Nothing here widens the
ridge grid, refits discovery, or alters the endpoint, nuisance design,
thresholds, donor roles, discovery object or adjudication rule.

Order, and why
--------------
1. Re-verify the R7 gate and every frozen root, before anything is read.
2. Reload the cached discovery matrix. It is digest-checked on reload, so this
   is a reuse of the exact matrix the discovery object was fitted from, not a
   re-materialization that might differ.
3. Re-read **discovery** AT8. Already opened under Stage 2; needed again to
   rebuild `discovery_metadata`, which the tail freeze and the pretarget
   authority both consume. This is not a refit: the adjudicator itself calls
   `verify_target_v2_against_raw`, which recomputes the discovery fit and
   requires it to reproduce the frozen object exactly.
4. Freeze the tail authority through the R7 gate, then the frozen conclusion
   function — the same architecture the canonical v2 wrapper uses.
5. Materialize the **confirmation** scalar matrix. Pathology-blind.
6. Build the pretarget execution authority with derived readiness.
7. **Open confirmation numeric AT8**, the last gate this stage opens.
8. Build the preadjudication execution authority with derived readiness.
9. Adjudicate through the R8-repaired path.
10. Replay every emitted package.

The adjudicator is reached by exec'ing `_adjudicate_from_raw_v2` **verbatim**
into a namespace whose two verifier names resolve to the R8-repaired versions.
No source substitution, no monkeypatching of the frozen module, and
`allow_synthetic_test_fixture` is passed False so the production condition is
enforced rather than bypassed.

A null or negative biological result is a valid outcome and is packaged exactly
as it comes out. A provenance, replay, donor-set, endpoint, readiness or gate
violation is a STOP.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_discovery_scalar_matrix_v1 as dm  # noqa: E402
import t0_eligible_donor_production_run_v1 as ed  # noqa: E402
import t0_execution_input_authority_v2 as v2  # noqa: E402
import t0_execution_input_readiness_authority_v1 as readiness  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402
import t0_stage2b_discovery_at8_v1 as stage2b  # noqa: E402

SUMMARY = "T0_STAGE3_CONFIRMATION_RUN_SUMMARY.json"
ACCESS_MANIFEST = "T0_CONFIRMATION_NUMERIC_AT8_ACCESS_MANIFEST.json"
DECISION_FILE = "T0_V20_ADJUDICATION_DECISION.json"

STOP_ROOT_MOVED = "STOP_T0_STAGE3_A_FROZEN_ROOT_MOVED"
STOP_DISCOVERY_LEAK = "STOP_T0_STAGE3_DISCOVERY_DONOR_IN_THE_CONFIRMATION_LOAD"
STOP_DONOR_SET = "STOP_T0_STAGE3_CONFIRMATION_DONOR_SET_DIGEST_MISMATCH"
STOP_IMMUNE = "STOP_T0_STAGE3_IMMUNE_FRACTION_NOT_AVAILABLE_FOR_A_DONOR"
STOP_REFIT = "STOP_T0_STAGE3_DISCOVERY_OBJECT_DID_NOT_REPRODUCE"

FROZEN_ROOTS = {
    "r7_package_root_sha256":
        "a7e25e515f8e9cb4ec43e1e3bf09798adca6a573059d4b7ca0b61483c5c96c09",
    "r7_readiness_root_sha256":
        "a75581dfc5e7ea88609a9ef62f54765b9a495a7dbdc5c09152ba7fb76d1488ae",
    "discovery_target_package_root_sha256":
        "b29429021b551f3b26dadbc5ee20f57cec4e84cccc483943b73602f5bcfad8fe",
    "discovery_provenance_root_sha256":
        "15d13dd3e733e0ea90b199cf981b03ccd94bc67fbd19660ef88861e3ae1a37c2",
    "discovery_authority_package_root_sha256":
        "9806de382c75f7a7a12bb952631ed0b6c9b458250e8161a876b470c48898f6f7",
    "discovery_scalar_matrix_sha256":
        "456377fb5bd37a57aadf03a7a641bafc8d3b6e556b85dc9cfa827dccf02dd2b7",
    "donor_role_package_root_sha256":
        "db8680e6cef3e0d26ee117a2acbd10ba1f681a53401008128a9bb7a2e6c478e0",
    "target_family_package_root_sha256":
        "1a531e114ffa80dc00ef39881a101a495cc731c9e0aa688ba575a85e2fe5bacb",
    "technical_registry_package_root_sha256":
        "420b95981652853d888be23abb0b73468891d508693064b35b4e339c96ba33bc",
}


def code_sha256(filename: str) -> str:
    path = Path(__file__).resolve().parent / filename
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def _immune_fraction(pkg: Path) -> dict[str, float]:
    """IMMUNE_FRACTION per donor, from the frozen immune-fraction authority."""
    with io.open(pkg / "T0_IMMUNE_FRACTION_REGISTRY.csv", "r",
                 encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    out = {}
    for row in rows:
        total = int(row["total_op31_n_donor"])
        if total <= 0:
            raise AssertionError("%s: %s has total_op31_n_donor %d"
                                 % (STOP_IMMUNE, row["donor_id"], total))
        out[str(row["donor_id"])] = int(row["immune_n_donor"]) / total
    return out


def _adjudicator_through_r8():
    """`_adjudicate_from_raw_v2`, verbatim, resolving the repaired verifiers.

    The frozen adjudicator imports the two verifier names at module level, so
    exec'ing its source into a namespace where those names are bound to the
    repaired versions is enough. Nothing is substituted in the adjudicator's own
    source and nothing on the frozen module is rebound.
    """
    import inspect

    frozen = stage2a._frozen("t0_adjudicator_v2")
    source = inspect.getsource(frozen._adjudicate_from_raw_v2)
    namespace = dict(frozen.__dict__)
    namespace["verify_pretarget_execution_authority"] = (
        v2.verify_pretarget_execution_authority)
    namespace["verify_preadjudication_execution_authority"] = (
        v2.verify_preadjudication_execution_authority)
    exec(compile(source, "<r8-routed:_adjudicate_from_raw_v2>", "exec"),
         namespace)
    return namespace["_adjudicate_from_raw_v2"]


def run(*, outdir: Path, readiness_pkg: Path, stage2a_pkg: Path,
        discovery_pkg: Path, role_pkg: Path, at8_pkg: Path, age_sex_pkg: Path,
        immune_pkg: Path, family_pkg: Path, technical_pkg: Path,
        tc_pkg: Path,
        stage3_prep_pkg: Path, population_pkg: Path, pathology_source: Path,
        store: Path, membership: Path, feature_split: Path,
        log=print) -> dict[str, Any]:
    started = time.time()

    def stamp(message: str) -> None:
        log("[%6.1fs] %s" % (time.time() - started, message))

    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    # --- 1. gate and frozen roots -------------------------------------------
    stamp("1/10 verifying the R7 gate and every frozen root")
    stage2b.assert_worktree_committed(Path(__file__).resolve().parents[2])
    gate = stage2a.verify_r7_gate(readiness_pkg, log=lambda m: None)
    bindings = gate["authority"]["bindings"]
    s2a = json.loads((stage2a_pkg / stage2a.SUMMARY).read_text(encoding="utf-8"))
    s2b = json.loads((discovery_pkg / "T0_DISCOVERY_STAGE_RUN_SUMMARY.json"
                      ).read_text(encoding="utf-8"))
    s3p = json.loads((stage3_prep_pkg / "T0_STAGE3_PREP_SUMMARY.json"
                      ).read_text(encoding="utf-8"))
    observed = {
        "r7_package_root_sha256": gate["package_root_sha256"],
        "r7_readiness_root_sha256": gate["readiness_root_sha256"],
        "discovery_target_package_root_sha256":
            s2b["discovery_target_package_root_sha256"],
        "discovery_provenance_root_sha256":
            s2b["discovery_provenance_root_sha256"],
        "discovery_authority_package_root_sha256":
            s2b["discovery_authority_package_root_sha256"],
        "discovery_scalar_matrix_sha256":
            s2b["discovery_scalar_matrix_sha256"],
        "donor_role_package_root_sha256":
            s2a["donor_role_package_root_sha256"],
        "target_family_package_root_sha256":
            s3p["target_family_package_root_sha256"],
        "technical_registry_package_root_sha256":
            s3p["technical_registry_package_root_sha256"],
    }
    for field, expected in FROZEN_ROOTS.items():
        if observed[field] != expected:
            raise AssertionError("%s: %s is %s, frozen %s"
                                 % (STOP_ROOT_MOVED, field, observed[field],
                                    expected))
    stamp("    all %d frozen roots unchanged" % len(FROZEN_ROOTS))

    discovery_donors = set(s2a["discovery_donors"])
    confirmation_donors = set(s2a["confirmation_donors"])

    # --- 2. the cached discovery matrix -------------------------------------
    stamp("2/10 reloading the cached discovery matrix, digest-checked")
    disc = dm.load_cache(
        discovery_pkg,
        expected_matrix_sha256=FROZEN_ROOTS["discovery_scalar_matrix_sha256"],
        log=log)
    if disc is None:
        raise AssertionError("the discovery matrix cache is absent; Stage 3 "
                             "must reuse the exact matrix the object was fitted "
                             "from rather than re-materialize it")

    # --- 3. discovery metadata ----------------------------------------------
    stamp("3/10 rebuilding discovery metadata (discovery AT8 already open)")
    at8_parent = ed.load_at8_availability(at8_pkg)
    disc_at8 = stage2b.load_discovery_at8(
        pathology_source,
        endpoint_identity=at8_parent["at8_endpoint_identity"],
        donor_id_field=at8_parent["donor_id_field"],
        discovery_donors=discovery_donors,
        confirmation_donors=confirmation_donors,
        expected_source_sha256=bindings["pathology_source_sha256"],
        expected_discovery_donor_set_sha256=bindings[
            "discovery_donor_set_sha256"],
        log=lambda m: None)
    if disc_at8["endpoint_values_sha256"] != s2b["endpoint_values_sha256"]:
        raise AssertionError(
            "%s: the discovery endpoint values digest changed since Stage 2"
            % STOP_ROOT_MOVED)
    stamp("    discovery endpoint values reproduce: %s"
          % disc_at8["endpoint_values_sha256"])
    disc_meta = stage2b.build_discovery_metadata(
        discovery_donors=discovery_donors, at8_values=disc_at8["values"],
        age_sex_pkg=age_sex_pkg)

    # --- 4. tail authority ---------------------------------------------------
    stamp("4/10 freezing the tail authority through the R7 gate")
    freeze_mod = stage2a._frozen("t0_canonical_freeze_v1")
    tail_dir = out / "tail"
    tail_result = freeze_mod.freeze_tail_after_discovery_authority(
        tail_dir=str(tail_dir),
        discovery_authority_dir=str(discovery_pkg / "discovery_authority"),
        target_dir=str(discovery_pkg / "target"),
        role_dir=str(role_pkg), feature_split_csv=str(feature_split),
        membership_csv=str(membership),
        scalar_raw_counts=disc["matrix"],
        scalar_feature_ids=disc["feature_ids"],
        matrix_id=disc["matrix_id"], local_row=disc["local_row"],
        cell_id=disc["cell_id"], donor_id=disc["donor_id"],
        stable_key=disc["stable_key"], source_library=disc["source_library"],
        donor_metadata=disc_meta)
    tail_root = tail_result["tail"]["package_root_sha256"] if isinstance(
        tail_result.get("tail"), dict) else tail_result["package_root_sha256"]
    stamp("    tail authority root %s" % tail_root)

    # --- 5. confirmation matrix, pathology-blind -----------------------------
    stamp("5/10 materializing the confirmation scalar matrix (no pathology)")
    conf = dm.load_cache(out, log=log)
    if conf is None:
        conf = dm.materialize(
            store=store, membership_csv=membership,
            population_pkg=population_pkg, feature_split_csv=feature_split,
            discovery_donors=confirmation_donors,
            expected_cells=7037, log=log)
        dm.save_cache(out, conf)
        stamp("    cached the confirmation matrix")

    # --- 6. pretarget authority, readiness derived ---------------------------
    stamp("6/10 building the pretarget execution authority, readiness derived")
    r7_obj = gate["authority"]
    derived = readiness.derive_readiness(r7_obj)
    v2.record_readiness_derivation(
        value=bool(derived), derivation=readiness.READINESS_DERIVATION,
        evidence={"r7_readiness_root_sha256": gate["readiness_root_sha256"],
                  "r7_package_root_sha256": gate["package_root_sha256"]})
    stamp("    readiness derived from R7: %s" % derived)

    role_meta = pd.DataFrame({
        "donor_id": sorted(discovery_donors | confirmation_donors,
                           key=lambda d: d.encode("utf-8")),
    })
    ages_mod = stage2a._frozen("t0_age_sex_authority_v1")
    replayed_ages = ages_mod.load_authority(
        age_sex_pkg,
        expected_package_root_sha256=ed.AGE_SEX_EXPECTED_PACKAGE_ROOT,
        expected_age_sex_root_sha256=ed.AGE_SEX_EXPECTED_ROOT,
        expected_source_sha256=ed.AGE_SEX_EXPECTED_SOURCE_SHA256,
        expected_candidate_donor_set_sha256=(
            ed.AGE_SEX_EXPECTED_CANDIDATE_DONOR_SET))
    by_donor = {str(r["donor_id"]): r for r in replayed_ages["rows"]}
    complete = ed.load_technical_completeness(tc_pkg)
    role_meta["AT8_available"] = [bool(at8_parent["flags"][d])
                                  for d in role_meta.donor_id]
    role_meta["age"] = [int(by_donor[d]["age"]) for d in role_meta.donor_id]
    role_meta["sex"] = [str(by_donor[d]["sex"]) for d in role_meta.donor_id]
    role_meta["technical_complete"] = [bool(complete["flags"][d])
                                       for d in role_meta.donor_id]
    role_meta = role_meta[["donor_id", "AT8_available", "age", "sex",
                           "technical_complete"]]

    external_hashes = {
        "pathology_source_sha256": bindings["pathology_source_sha256"],
        "population_raw_source_root_sha256":
            bindings["b2_population_raw_source_root_sha256"],
        "b1_feature_authority_root_sha256":
            "538b73b8414f47c70507cb0c8b46a6d4787e019c49056e07d6b0238382cf99b8",
    }
    pretarget_dir = out / "pretarget_execution_input"
    pre = v2.build_pretarget_execution_authority(
        str(pretarget_dir), role_dir=str(role_pkg), role_metadata=role_meta,
        discovery_scalar_raw_counts=disc["matrix"],
        scalar_feature_ids=disc["feature_ids"],
        discovery_matrix_id=disc["matrix_id"],
        discovery_local_row=disc["local_row"],
        discovery_cell_id=disc["cell_id"],
        discovery_donor_id=disc["donor_id"],
        discovery_stable_key=disc["stable_key"],
        discovery_source_library=disc["source_library"],
        discovery_metadata=disc_meta,
        feature_split_csv=str(feature_split), membership_csv=str(membership),
        external_source_authority_hashes=external_hashes)
    stamp("    pretarget root %s, readiness %s"
          % (pre["package_root_sha256"],
             pre["authority"]["real_execution_ready"]))

    # --- 7. CONFIRMATION NUMERIC AT8 -----------------------------------------
    stamp("7/10 OPENING CONFIRMATION NUMERIC AT8")
    conf_at8 = stage2b.load_discovery_at8(
        pathology_source,
        endpoint_identity=at8_parent["at8_endpoint_identity"],
        donor_id_field=at8_parent["donor_id_field"],
        discovery_donors=confirmation_donors,
        confirmation_donors=discovery_donors,   # the roles swap here
        expected_source_sha256=bindings["pathology_source_sha256"],
        expected_discovery_donor_set_sha256=bindings[
            "confirmation_donor_set_sha256"],
        log=log)
    if set(conf_at8["values"]) & discovery_donors:
        raise AssertionError("%s: %s" % (STOP_DISCOVERY_LEAK,
                                         sorted(set(conf_at8["values"])
                                                & discovery_donors)))
    stamp("    read %d CONFIRMATION donors; %d DISCOVERY rows skipped"
          % (conf_at8["donor_count"],
             conf_at8["confirmation_rows_present_and_skipped"]))

    immune = _immune_fraction(immune_pkg)
    order = sorted(confirmation_donors, key=lambda d: d.encode("utf-8"))
    missing = [d for d in order if d not in immune]
    if missing:
        raise AssertionError("%s: %s" % (STOP_IMMUNE, missing))
    conf_meta = pd.DataFrame({
        "donor_id": order,
        "AT8": [float(conf_at8["values"][d]) for d in order],
        "age": [int(by_donor[d]["age"]) for d in order],
        "sex": [str(by_donor[d]["sex"]) for d in order],
        "IMMUNE_FRACTION": [float(immune[d]) for d in order],
    })[["donor_id", "AT8", "age", "sex", "IMMUNE_FRACTION"]]

    access = {
        "schema": "JEPA_T0_CONFIRMATION_NUMERIC_AT8_ACCESS_MANIFEST_V1",
        "confirmation_numeric_at8_opened": True,
        "confirmation_donor_count": conf_at8["donor_count"],
        "confirmation_donor_set_sha256":
            conf_at8["discovery_donor_set_sha256"],
        "endpoint_identity": conf_at8["endpoint_identity"],
        "endpoint_identity_sha256": conf_at8["endpoint_identity_sha256"],
        "endpoint_values_sha256": conf_at8["endpoint_values_sha256"],
        "pathology_source_sha256": conf_at8["pathology_source_sha256"],
        "discovery_rows_present_and_skipped":
            conf_at8["confirmation_rows_present_and_skipped"],
        "other_columns_left_unparsed": conf_at8["other_columns_left_unparsed"],
        "per_donor_at8_values_emitted": False,
        "non_at8_pathology_endpoint_parsed": False,
        "dev_opened": False, "sealed_opened": False,
        "protected_populations_opened": False,
    }
    with io.open(out / ACCESS_MANIFEST, "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(json.dumps(access, indent=2, sort_keys=True) + "\n")

    # --- 8. preadjudication authority ---------------------------------------
    stamp("8/10 building the preadjudication execution authority")
    preadj_dir = out / "preadjudication_execution_input"
    adj_auth = v2.build_preadjudication_execution_authority(
        str(preadj_dir), pretarget_authority_dir=str(pretarget_dir),
        role_dir=str(role_pkg),
        target_root_sha256=FROZEN_ROOTS["discovery_target_package_root_sha256"],
        tail_root_sha256=tail_root,
        discovery_authority_root_sha256=FROZEN_ROOTS[
            "discovery_authority_package_root_sha256"],
        technical_registry_dir=str(technical_pkg),
        family_registry_dir=str(family_pkg),
        confirmation_scalar_raw_counts=conf["matrix"],
        scalar_feature_ids=conf["feature_ids"],
        confirmation_matrix_id=conf["matrix_id"],
        confirmation_local_row=conf["local_row"],
        confirmation_cell_id=conf["cell_id"],
        confirmation_donor_id=conf["donor_id"],
        confirmation_stable_key=conf["stable_key"],
        confirmation_source_library=conf["source_library"],
        confirmation_metadata=conf_meta,
        feature_split_csv=str(feature_split), membership_csv=str(membership),
        external_source_authority_hashes=external_hashes)
    stamp("    preadjudication root %s, readiness %s"
          % (adj_auth["package_root_sha256"],
             adj_auth["authority"]["real_execution_ready"]))

    # --- 9. adjudicate -------------------------------------------------------
    stamp("9/10 adjudicating through the R8-repaired path")
    adjudicate = _adjudicator_through_r8()
    decision = adjudicate(
        allow_synthetic_test_fixture=False,
        pretarget_authority_dir=str(pretarget_dir),
        preadjudication_authority_dir=str(preadj_dir),
        role_metadata=role_meta,
        rare5_status_authority_file=str(
            stage3_prep_pkg / "T0_RARE5_DECISION_CAPABILITY_STATUS.json"),
        target_dir=str(discovery_pkg / "target"), tail_dir=str(tail_dir),
        role_dir=str(role_pkg),
        discovery_authority_dir=str(discovery_pkg / "discovery_authority"),
        technical_registry_dir=str(technical_pkg),
        family_registry_dir=str(family_pkg),
        discovery_scalar_raw_counts=disc["matrix"],
        scalar_feature_ids=disc["feature_ids"],
        discovery_matrix_id=disc["matrix_id"],
        discovery_local_row=disc["local_row"],
        discovery_cell_id=disc["cell_id"],
        discovery_donor_id=disc["donor_id"],
        discovery_stable_key=disc["stable_key"],
        discovery_source_library=disc["source_library"],
        discovery_metadata=disc_meta,
        confirmation_scalar_raw_counts=conf["matrix"],
        confirmation_matrix_id=conf["matrix_id"],
        confirmation_local_row=conf["local_row"],
        confirmation_cell_id=conf["cell_id"],
        confirmation_donor_id=conf["donor_id"],
        confirmation_stable_key=conf["stable_key"],
        confirmation_source_library=conf["source_library"],
        confirmation_metadata=conf_meta,
        feature_split_csv=str(feature_split), membership_csv=str(membership))
    stamp("    adjudication returned")

    serialisable = json.loads(json.dumps(decision, default=str))
    with io.open(out / DECISION_FILE, "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(json.dumps(serialisable, indent=2, sort_keys=True) + "\n")

    # --- 10. replay ----------------------------------------------------------
    stamp("10/10 replaying the emitted packages from disk")
    tail_mod = stage2a._frozen("t0_tail_authority_v1")
    tail_reloaded = tail_mod.load_tail_authority(
        str(tail_dir), FROZEN_ROOTS["discovery_target_package_root_sha256"])
    pre_reloaded = v2.load_pretarget_execution_authority(str(pretarget_dir))
    adj_reloaded = v2.load_preadjudication_execution_authority(str(preadj_dir))
    for label, reloaded, built in (
            ("pretarget", pre_reloaded, pre),
            ("preadjudication", adj_reloaded, adj_auth)):
        if reloaded["package_root_sha256"] != built["package_root_sha256"]:
            raise AssertionError("%s root does not replay" % label)
        if not v2.adjudicator_gate_satisfied(reloaded["authority"]):
            raise AssertionError("%s does not satisfy the adjudicator gate"
                                 % label)
        stamp("    %-16s replays, gate satisfied" % label)
    stamp("    tail authority replays: %s"
          % tail_reloaded["package_root_sha256"])

    record = {
        "schema": "JEPA_T0_STAGE3_CONFIRMATION_RUN_SUMMARY_V1",
        "terminal": ("PASS_T0_V20_STAGE3_CONFIRMATION_AND_ADJUDICATION"
                     "_REPLAYED"),
        "frozen_roots_unchanged": observed,
        "tail_package_root_sha256": tail_root,
        "pretarget_execution_input_package_root_sha256":
            pre["package_root_sha256"],
        "preadjudication_execution_input_package_root_sha256":
            adj_auth["package_root_sha256"],
        "readiness_derived": bool(derived),
        "readiness_derivation": readiness.READINESS_DERIVATION,
        "confirmation_donor_count": conf_at8["donor_count"],
        "confirmation_cells": conf["cells"],
        "confirmation_matrix_nnz": conf["nnz"],
        "confirmation_matrix_sha256": conf["matrix_sha256"],
        "confirmation_donor_set_sha256":
            conf_at8["discovery_donor_set_sha256"],
        "confirmation_endpoint_values_sha256":
            conf_at8["endpoint_values_sha256"],
        "discovery_endpoint_values_sha256":
            disc_at8["endpoint_values_sha256"],
        "decision": serialisable,
        "ridge_grid_widened": False,
        "discovery_refit": False,
        "endpoint_altered": False,
        "nuisance_design_altered": False,
        "thresholds_altered": False,
        "donor_roles_altered": False,
        "adjudication_rule_altered": False,
        "dev_opened": False, "sealed_opened": False,
        "protected_populations_opened": False, "training_begun": False,
        "successor_u0_materialized": False, "td60_run": False,
        "biological_sweeps_run": False,
        "cv_boundary_caveat": (
            "The discovery LOODO selected ridge exponent 2.0, the frozen grid "
            "maximum. Minor as grid mis-specification because the CV curve is "
            "asymptoting, major as interpretation because discovery preferred "
            "near-total shrinkage. Recorded before confirmation and not used to "
            "change this run."),
        "runner_code_sha256": code_sha256("t0_stage3_confirmation_v1.py"),
        "code_byte_semantics": readiness.ACCURATE_CODE_BYTE_SEMANTICS,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    with io.open(out / SUMMARY, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    v2.clear_readiness_derivation()
    return record


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("outdir", "readiness-pkg", "stage2a-pkg", "discovery-pkg",
                 "role-pkg", "at8-pkg", "age-sex-pkg", "immune-pkg",
                 "family-pkg", "technical-pkg", "tc-pkg", "stage3-prep-pkg",
                 "population-pkg", "pathology-source", "store", "membership",
                 "feature-split"):
        p.add_argument("--%s" % name, required=True, type=Path)
    a = p.parse_args(argv)
    record = run(outdir=a.outdir, readiness_pkg=a.readiness_pkg,
                 stage2a_pkg=a.stage2a_pkg, discovery_pkg=a.discovery_pkg,
                 role_pkg=a.role_pkg, at8_pkg=a.at8_pkg,
                 age_sex_pkg=a.age_sex_pkg, immune_pkg=a.immune_pkg,
                 family_pkg=a.family_pkg, technical_pkg=a.technical_pkg,
                 tc_pkg=a.tc_pkg,
                 stage3_prep_pkg=a.stage3_prep_pkg,
                 population_pkg=a.population_pkg,
                 pathology_source=a.pathology_source, store=a.store,
                 membership=a.membership, feature_split=a.feature_split)
    print()
    print(json.dumps({k: v for k, v in record.items() if k != "decision"},
                     indent=2, sort_keys=True))
    print()
    print(record["terminal"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
