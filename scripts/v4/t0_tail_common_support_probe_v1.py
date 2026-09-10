#!/usr/bin/env python3
"""Within-donor common support: does the confound fall, and does biology stay?

Step 4, implementing `configs/v4/t0_tail_common_support_contract_v1.json`,
frozen before this module was written.

Diagnostic only. `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is unchanged,
`training_authorized: false`, and no successor estimator, QC gate, threshold or
training authority is chosen from these results.

Step 3 preserved the tail/rest depth difference by construction, because
thinning scales both groups together. This step removes it: within each donor,
keep only cells whose Q_DEPTH and Q_DETECT both lie in the overlap of the tail
and rest ranges, discard the rest, and then ask two frozen questions of what is
left.

    HOLDOUT_COHERENCE  do the donors still share a held-out direction among
                       technically comparable cells?
    QC_ASSOCIATION     does the association that produced the veto still fire
                       among those same cells?

The second is the validity check and the reason the contract requires both.
Common support equalises the range the two groups occupy; it does not by itself
equalise their distributions inside that range. Recomputing the frozen QC
statistic on the restricted set is the only evidence about whether the contrast
actually fell, and without it a surviving coherence could be reported as
confound-free while the confound was still present.

Nothing frozen is modified or reimplemented. The frozen per-donor QC contrast,
the frozen randomization veto, the frozen discovery-fit holdout scale, the
frozen holdout vector builder, the frozen support minima and the frozen exact
sign-flip test all run unchanged. Labels are the frozen mask throughout and are
never recomputed.

Pathology-blind: no AT8 value is read.
"""

from __future__ import annotations

import argparse
import csv as csvmod
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t0_discovery_scalar_matrix_v1 as dm  # noqa: E402
import t0_numeric_environment_v1 as numeric_environment  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402

STOP = "STOP_T0_TAIL_COMMON_SUPPORT_REFUSED"
CONTRACT = "configs/v4/t0_tail_common_support_contract_v1.json"
REPORT = "T0_TAIL_COMMON_SUPPORT_PROBE.json"
DONOR_CSV = "T0_TAIL_COMMON_SUPPORT_DONORS.csv"

METRIC_NAMES = ("Q_DEPTH", "Q_DETECT")
UNRESTRICTED = "UNRESTRICTED"
RESTRICTED = "COMMON_SUPPORT"


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def common_support_mask(qc: np.ndarray, tail: np.ndarray) -> tuple[np.ndarray,
                                                                   dict]:
    """The contract's rule: the box where the two groups' ranges overlap.

    Parameter-free by construction. There is no tolerance or caliper to choose,
    so nothing here can be tuned toward an outcome.
    """
    values = np.asarray(qc, dtype=np.float64)
    mask = np.asarray(tail, dtype=bool)
    if mask.sum() == 0 or (~mask).sum() == 0:
        _fail("a donor must have both tail and rest cells")
    low = np.maximum(values[mask].min(axis=0), values[~mask].min(axis=0))
    high = np.minimum(values[mask].max(axis=0), values[~mask].max(axis=0))
    inside = np.all((values >= low) & (values <= high), axis=1)
    box = {"low": [float(x) for x in low], "high": [float(x) for x in high]}
    return inside, box


def qc_contrast(qc: np.ndarray, tail: np.ndarray, frozen_qc) -> list[float]:
    """The frozen per-donor standardized contrast, unchanged."""
    return [float(x) for x in frozen_qc._donor_delta(qc, tail)]


def run(*, confirmation_pkg: Path, discovery_pkg: Path, tail_dir: Path,
        membership: Path, feature_split: Path, outdir: Path,
        log=print) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    contract_bytes = (root / CONTRACT).read_bytes()
    contract = json.loads(contract_bytes.decode("utf-8"))
    if contract.get("status") != "FROZEN_BEFORE_EXECUTION":
        _fail("the common-support contract is not frozen")

    conf_summary = json.loads(
        (confirmation_pkg / "T0_STAGE3_CONFIRMATION_RUN_SUMMARY.json"
         ).read_text(encoding="utf-8"))
    decision = json.loads(
        (confirmation_pkg / "T0_V20_ADJUDICATION_DECISION.json"
         ).read_text(encoding="utf-8"))
    if decision.get("tail_terminal") != "RARE_TAIL_UNDERDETERMINED_MEASUREMENT":
        _fail("expected the QC-vetoed tail terminal, found %r"
              % decision.get("tail_terminal"))
    frozen_preflight = decision["tail_preflight"]
    committed_coherence = frozen_preflight["support"]["coherence"]
    committed_qc = frozen_preflight["qc"]
    disc_summary = json.loads(
        (discovery_pkg / "T0_DISCOVERY_STAGE_RUN_SUMMARY.json"
         ).read_text(encoding="utf-8"))

    conf = dm.load_cache(
        confirmation_pkg,
        expected_matrix_sha256=conf_summary["confirmation_matrix_sha256"],
        log=lambda m: None)
    disc = dm.load_cache(
        discovery_pkg,
        expected_matrix_sha256=disc_summary["discovery_scalar_matrix_sha256"],
        log=lambda m: None)
    if conf is None or disc is None:
        _fail("both digest-verified matrix caches are required")

    raw = stage2a._frozen("t0_confirmation_raw_v1")
    preflight = stage2a._frozen("t0_tail_preflight_raw_v1")
    support_mod = stage2a._frozen("t0_tail_support_coherence_v1")
    loo_mod = stage2a._frozen("t0_coherence_statistic_v1")
    frozen_qc = stage2a._frozen("t0_tail_qc_randomization_v1")
    feature_mod = stage2a._frozen("t0_feature_authority_v1")

    feature = feature_mod.load_feature_authority(str(feature_split))
    roles = feature.feature_role.to_numpy()
    address_ids = feature.molecular_address_id.astype(str).to_numpy()
    scoring_pos = np.flatnonzero(roles == "SCORING")
    holdout_pos = np.flatnonzero(roles == "COHERENCE_HOLDOUT")
    if set(scoring_pos.tolist()) & set(holdout_pos.tolist()):
        _fail("SCORING and COHERENCE_HOLDOUT positions overlap")

    disc_csr = disc["matrix"].tocsr() if sp.issparse(disc["matrix"]) \
        else sp.csr_matrix(disc["matrix"])
    scale, decision_mask = preflight.discovery_holdout_scale(
        holdout_raw_counts=disc_csr[:, holdout_pos],
        donor_id=disc["donor_id"], stable_key=disc["stable_key"],
        source_library=disc["source_library"])
    features = int(decision_mask.sum())
    if features != int(frozen_preflight["holdout_decision_features"]):
        _fail("holdout decision features %d do not reproduce the committed %d"
              % (features, frozen_preflight["holdout_decision_features"]))
    log("frozen holdout scale reproduces %d decision features" % features)

    summaries = raw.confirmation_summaries_from_raw(
        target_dir=str(discovery_pkg / "target"), tail_dir=str(tail_dir),
        scalar_raw_counts=conf["matrix"],
        scalar_feature_ids=conf["feature_ids"],
        matrix_id=conf["matrix_id"], local_row=conf["local_row"],
        cell_id=conf["cell_id"], donor_id=conf["donor_id"],
        stable_key=conf["stable_key"],
        source_library=conf["source_library"],
        feature_split_csv=str(feature_split), membership_csv=str(membership))

    frozen_masks = summaries["tail_masks_by_donor"]
    donors = [d for d in summaries["donor_table"]["donor_id"].tolist()
              if d in frozen_masks]
    indices = summaries["cell_indices_by_donor"]
    keys = summaries["stable_keys_by_donor"]
    qc_by_donor = summaries["qc_by_donor"]

    conf_csr = conf["matrix"].tocsr() if sp.issparse(conf["matrix"]) \
        else sp.csr_matrix(conf["matrix"])
    library = np.asarray(conf["source_library"], dtype=np.float64)
    donor_ids_raw = np.asarray([str(x) for x in conf["donor_id"]])
    keys_raw = np.asarray(conf["stable_key"])

    def assemble(keep_by_donor):
        """Rows, arrays and masks for a per-donor keep selection."""
        rows, ids, stable, libs, masks, qcs, key_lists = [], [], [], {}, {}, {}, {}
        for donor in donors:
            ix = np.asarray(indices[donor])
            keep = np.asarray(keep_by_donor[donor], dtype=bool)
            selected = ix[keep]
            if selected.size == 0:
                _fail("donor %s retained no cells" % donor)
            # RESTRICTION_ONLY_REMOVES / LABELS_NEVER_RECOMPUTED
            if not np.all(np.isin(selected, ix)):
                _fail("donor %s gained a cell" % donor)
            rows.append(conf_csr[selected])
            ids.append(donor_ids_raw[selected])
            stable.append(keys_raw[selected])
            libs[donor] = library[selected]
            masks[donor] = np.asarray(frozen_masks[donor], dtype=bool)[keep]
            qcs[donor] = np.asarray(qc_by_donor[donor],
                                    dtype=np.float64)[keep]
            key_lists[donor] = np.asarray(keys[donor])[keep]
            if not np.all(donor_ids_raw[selected] == str(donor)):
                _fail("a retained cell changed donor for %s" % donor)
        return (sp.vstack(rows, format="csr"), np.concatenate(ids),
                np.concatenate(stable),
                np.concatenate([libs[d] for d in donors]), masks, qcs,
                key_lists)

    def evaluate(label, keep_by_donor):
        matrix, ids, stable, libs, masks, qcs, key_lists = assemble(
            keep_by_donor)
        donor_list, vectors, tail_counts, rest_counts = \
            preflight.confirmation_holdout_vectors(
                holdout_raw_counts=matrix[:, holdout_pos], donor_id=ids,
                stable_key=stable, source_library=libs,
                tail_masks_by_donor=masks, scale=scale,
                decision_mask=decision_mask)
        support = support_mod.adjudicate_tail_support_coherence(
            vectors, tail_counts, rest_counts)
        veto = frozen_qc.tail_qc_veto_test(
            [qcs[d] for d in donor_list], [masks[d] for d in donor_list],
            [key_lists[d] for d in donor_list], list(donor_list))
        contrasts = {d: qc_contrast(qcs[d], masks[d], frozen_qc)
                     for d in donor_list}
        record: dict[str, Any] = {
            "label": label,
            "donors": [str(d) for d in donor_list],
            "tail_counts": [int(c) for c in tail_counts],
            "rest_counts": [int(c) for c in rest_counts],
            "support_ok": bool(support["support_ok"]),
            "coherence_ok": bool(support["coherence_ok"]),
            "decision_donors": int(support["decision_donors"]),
            "qc_veto": {k: (float(v) if isinstance(v, float)
                            else (bool(v) if isinstance(v, bool) else int(v)))
                        for k, v in veto.items()},
            "per_donor_qc_contrast": {str(d): contrasts[d] for d in donor_list},
        }
        coherence = support.get("coherence")
        if coherence:
            record["coherence"] = {
                k: (float(v) if isinstance(v, float) else int(v))
                for k, v in coherence.items()}
            usable = np.asarray([np.linalg.norm(v) > 0 for v in vectors])
            if int(usable.sum()) >= 3:
                loo = loo_mod.loo_coherence(vectors[usable])
                record["loo_mean_cosine"] = float(loo["loo_mean_cosine"])
                record["loo_positive_fraction"] = float(
                    loo["loo_positive_fraction"])
        return record, np.asarray(vectors, dtype=np.float64)

    # --- unrestricted control ------------------------------------------------
    everything = {d: np.ones(len(indices[d]), dtype=bool) for d in donors}
    control, control_vectors = evaluate(UNRESTRICTED, everything)

    for field, value in committed_coherence.items():
        observed = (control.get("coherence") or {}).get(field)
        if observed is None:
            _fail("control coherence is missing %r" % field)
        if isinstance(value, float):
            if float(observed) != float(value):
                _fail("control coherence %s %r does not reproduce %r"
                      % (field, observed, value))
        elif int(observed) != int(value):
            _fail("control coherence %s %r does not reproduce %r"
                  % (field, observed, value))
    for field in ("max_mean_abs_standardized_qc_contrast", "p_upper",
                  "replicates", "donors", "decision_qc_metrics"):
        observed = control["qc_veto"][field]
        value = committed_qc[field]
        if isinstance(value, float):
            if float(observed) != float(value):
                _fail("control QC %s %r does not reproduce %r"
                      % (field, observed, value))
        elif int(observed) != int(value):
            _fail("control QC %s %r does not reproduce %r"
                  % (field, observed, value))
    if control["qc_veto"]["veto"] is not True:
        _fail("the control QC veto did not reproduce")
    log("unrestricted control reproduces the committed coherence and QC veto")

    # --- common-support restriction -----------------------------------------
    keep_by_donor = {}
    boxes = {}
    for donor in donors:
        inside, box = common_support_mask(qc_by_donor[donor],
                                          frozen_masks[donor])
        keep_by_donor[donor] = inside
        boxes[donor] = box
    restricted, restricted_vectors = evaluate(RESTRICTED, keep_by_donor)

    cosines = []
    for j in range(len(restricted_vectors)):
        a = control_vectors[j]
        b = restricted_vectors[j]
        na = float(np.linalg.norm(a))
        nb = float(np.linalg.norm(b))
        cosines.append(float(a @ b / (na * nb)) if na > 0 and nb > 0 else None)
    restricted["donor_cosine_to_unrestricted"] = cosines
    usable = [c for c in cosines if c is not None]
    restricted["mean_donor_cosine_to_unrestricted"] = \
        float(np.mean(usable)) if usable else None

    # --- which declared outcome occurred ------------------------------------
    still_fires = bool(restricted["qc_veto"]["veto"])
    coherent = bool(restricted["coherence_ok"])
    capable = bool(restricted["support_ok"])
    if not capable:
        outcome = "NOT_DECISION_CAPABLE_AFTER_RESTRICTION"
    elif still_fires:
        outcome = "QC_ASSOCIATION_STILL_FIRES__RESTRICTION_INSUFFICIENT"
    elif coherent:
        outcome = "CONFOUND_NOT_DETECTABLE_AND_HOLDOUT_COHERENCE_SURVIVES"
    else:
        outcome = "CONFOUND_NOT_DETECTABLE_AND_HOLDOUT_COHERENCE_COLLAPSES"
    log("declared outcome: %s" % outcome)

    donor_rows = []
    for j, donor in enumerate(restricted["donors"]):
        before = control["per_donor_qc_contrast"][donor]
        after = restricted["per_donor_qc_contrast"][donor]
        donor_rows.append({
            "donor_id": donor,
            "tail_before": control["tail_counts"][j],
            "rest_before": control["rest_counts"][j],
            "tail_after": restricted["tail_counts"][j],
            "rest_after": restricted["rest_counts"][j],
            "q_depth_low": boxes[donor]["low"][0],
            "q_depth_high": boxes[donor]["high"][0],
            "q_detect_low": boxes[donor]["low"][1],
            "q_detect_high": boxes[donor]["high"][1],
            "q_depth_contrast_before": before[0],
            "q_depth_contrast_after": after[0],
            "q_detect_contrast_before": before[1],
            "q_detect_contrast_after": after[1],
            "holdout_cosine_to_unrestricted": cosines[j],
        })

    outdir.mkdir(parents=True, exist_ok=True)
    donor_path = outdir / DONOR_CSV
    columns = list(donor_rows[0].keys())
    with io.open(donor_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        for row in donor_rows:
            writer.writerow([repr(float(row[c]))
                             if isinstance(row[c], float) else row[c]
                             for c in columns])

    report = {
        "schema": "JEPA_T0_TAIL_COMMON_SUPPORT_PROBE_V1",
        "step": "4 of the QC methodology investigation",
        "implements_contract": CONTRACT,
        "contract_sha256": _sha256_bytes(contract_bytes),
        "declared_outcome": outcome,
        "diagnostic_only": True,
        "frozen_tail_terminal": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "training_authorized": False,
        "t0_v20_modified": False,
        "frozen_target_modified": False,
        "frozen_tail_mask_modified": False,
        "tail_labels_recomputed": False,
        "qc_alpha_modified": False,
        "coherence_alpha_modified": False,
        "support_minima_modified": False,
        "holdout_scale_refit": False,
        "thinning_applied": False,
        "scoring_features_entering_validation": 0,
        "successor_estimator_designed": False,
        "pathology_blind": True,
        "reads_at8": False,
        "control_reproduces_committed_coherence_and_veto": True,
        "restriction_rule": "PER_DONOR_COMMON_SUPPORT",
        "restriction_parameter_free": True,
        "frozen_support_minima": {
            "MIN_TAIL_CELLS": int(support_mod.MIN_TAIL_CELLS),
            "MIN_REST_CELLS": int(support_mod.MIN_REST_CELLS),
            "MIN_DECISION_DONORS": int(support_mod.MIN_DECISION_DONORS),
        },
        "holdout_decision_features": features,
        "committed_coherence": committed_coherence,
        "committed_qc": committed_qc,
        "interpretation_limits": contract["interpretation_limits"],
        "unrestricted": control,
        "restricted": restricted,
        "per_donor_common_support_box": boxes,
        "machine_readable": {"donor_csv": donor_path.name},
        "provenance": {
            "confirmation_matrix_sha256":
                conf_summary["confirmation_matrix_sha256"],
            "discovery_matrix_sha256":
                disc_summary["discovery_scalar_matrix_sha256"],
            "target_package_root_sha256":
                summaries["target_package_root_sha256"],
            "tail_package_root_sha256": summaries["tail_package_root_sha256"],
            "tail_threshold": float(summaries["threshold"]),
            "feature_role_authority_sha256":
                _sha256_bytes(Path(feature_split).read_bytes()),
            "holdout_address_ids_sha256":
                _sha256_bytes("|".join(address_ids[holdout_pos]
                                       ).encode("utf-8")),
            "holdout_decision_mask_sha256":
                _sha256_bytes(np.asarray(decision_mask,
                                         dtype=np.bool_).tobytes()),
            "donor_set": [str(d) for d in donors],
        },
        "numeric_environment": numeric_environment.numeric_environment(),
    }
    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                default=str) + "\n")
    log("wrote %s, %s" % (out.name, donor_path.name))
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("confirmation-pkg", "discovery-pkg", "tail-dir", "membership",
                 "feature-split", "outdir"):
        p.add_argument("--%s" % name, required=True, type=Path)
    a = p.parse_args(argv)
    report = run(confirmation_pkg=a.confirmation_pkg,
                 discovery_pkg=a.discovery_pkg, tail_dir=a.tail_dir,
                 membership=a.membership, feature_split=a.feature_split,
                 outdir=a.outdir)
    print()
    for key in ("unrestricted", "restricted"):
        row = report[key]
        coherence = row.get("coherence") or {}
        veto = row["qc_veto"]
        print("%-15s cells %5d/%5d  support %-5s coh %-5s  cosine %s p %s"
              % (row["label"], sum(row["tail_counts"]),
                 sum(row["rest_counts"]), row["support_ok"],
                 row["coherence_ok"],
                 ("%.6f" % coherence["mean_pairwise_cosine"])
                 if coherence else "n/a",
                 ("%.3e" % coherence["p_upper_exact"]) if coherence else "n/a"))
        print("%-15s QC max contrast %.6f  p_upper %.4f  veto %s"
              % ("", veto["max_mean_abs_standardized_qc_contrast"],
                 veto["p_upper"], veto["veto"]))
    print()
    print("declared outcome: %s" % report["declared_outcome"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
