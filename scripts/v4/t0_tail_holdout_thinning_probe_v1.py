#!/usr/bin/env python3
"""Held-out tail coherence under the frozen depth intervention. Step 3.

Implements `configs/v4/t0_tail_holdout_thinning_contract_v1.json` exactly, as
frozen by the owner before execution in commit 03372f16.

Diagnostic only. `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` is unchanged,
`training_authorized: false`, and no tail rule, threshold, estimator, p-value
threshold or training gate is chosen from these results.

The design choice that makes this step worth running is that **the tail labels
are held fixed**. The frozen unthinned tail mask groups the cells at every
retention level, and only the measurement changes. Recomputing tail membership
after thinning would let the depth-sensitive SCORING estimator select the
validation groups again, reintroducing exactly the selection/measurement
entanglement the diagnostic exists to avoid. A consequence worth noticing: with
the grouping fixed, the SCORING counts never enter this step at all. Only the
COHERENCE_HOLDOUT panel does, and those genes played no part in defining the
grouping they are being asked to validate.

The intervention is the parent contract's, not a new one. The same retention
ladder, the same draws, the same `T0-TAIL-DEPTH-THINNING-V1` per-cell hash seed
derivation and the same binomial molecule-retention model, regenerated
deterministically over the full scalar panel so the library remainder stays
physically consistent with the thinned counts.

Every statistic comes from the frozen preflight and the frozen exact sign-flip
test, unmodified. The one derived function is `confirmation_holdout_vectors`
with a single substituted line, so the pre-normalisation L2 norms the contract
requires can be recorded without reimplementing the vector construction.
"""

from __future__ import annotations

import argparse
import csv as csvmod
import difflib
import hashlib
import inspect
import io
import json
import struct
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

STOP = "STOP_T0_TAIL_HOLDOUT_THINNING_REFUSED"
CONTRACT = "configs/v4/t0_tail_holdout_thinning_contract_v1.json"
PARENT_CONTRACT = "configs/v4/t0_tail_depth_thinning_contract_v1.json"
REPORT = "T0_TAIL_HOLDOUT_THINNING_PROBE.json"
LEVEL_CSV = "T0_TAIL_HOLDOUT_THINNING_LEVELS.csv"
DONOR_CSV = "T0_TAIL_HOLDOUT_THINNING_DONORS.csv"

# The parent contract's namespace, reused rather than replaced.
PARENT_NAMESPACE = b"T0-TAIL-DEPTH-THINNING-V1"

_PRENORM_ORIGINAL = "        norm=float(np.linalg.norm(V[j,mask]));"
_PRENORM_REPAIRED = ("        norm=float(np.linalg.norm(V[j,mask]));"
                     " _prenorms.append(norm)")


def _fail(message: str) -> None:
    raise RuntimeError("%s: %s" % (STOP, message))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cell_seed(draw: int, level: float, donor: str, stable_key: str) -> int:
    """The parent contract's per-cell seed derivation, unchanged."""
    level_text = repr(float(level)).encode()
    donor_bytes = str(donor).encode()
    key_bytes = str(stable_key).encode()
    digest = hashlib.sha256(
        PARENT_NAMESPACE + b"\x00" + struct.pack(">I", draw)
        + struct.pack(">H", len(level_text)) + level_text
        + struct.pack(">H", len(donor_bytes)) + donor_bytes
        + struct.pack(">H", len(key_bytes)) + key_bytes).digest()
    return int.from_bytes(digest[:8], "little", signed=False)


def instrumented_holdout_vectors(preflight):
    """The frozen vector builder, with the pre-normalisation norms recorded.

    Derived by substituting one line of its own source rather than reimplemented,
    so the vector construction, the zeroing of non-decision features and the
    normalisation are the frozen ones. The contract requires the unnormalised L2
    norm per donor, which the frozen function discards when it normalises in
    place.
    """
    source = inspect.getsource(preflight.confirmation_holdout_vectors)
    if source.count(_PRENORM_ORIGINAL) != 1:
        _fail("expected exactly one normalisation line to instrument, found %d"
              % source.count(_PRENORM_ORIGINAL))
    derived = source.replace(_PRENORM_ORIGINAL, _PRENORM_REPAIRED, 1)

    added = [line for line in difflib.unified_diff(
        source.splitlines(), derived.splitlines(), lineterm="", n=0)
        if line.startswith("+") and not line.startswith("+++")]
    removed = [line for line in difflib.unified_diff(
        source.splitlines(), derived.splitlines(), lineterm="", n=0)
        if line.startswith("-") and not line.startswith("---")]
    if len(added) != 1 or len(removed) != 1:
        _fail("instrumentation changed %d/%d lines, expected one" %
              (len(added), len(removed)))

    prenorms: list[float] = []
    namespace = dict(preflight.__dict__)
    namespace["_prenorms"] = prenorms
    exec(compile(derived, "<holdout-thinning:confirmation_holdout_vectors>",
                 "exec"), namespace)
    return namespace["confirmation_holdout_vectors"], prenorms, {
        "changed_lines": 1,
        "added": added[0][1:].strip(),
        "removed": removed[0][1:].strip(),
    }


def thin_full_panel(matrix, donors, indices, keys, library: np.ndarray,
                    level: float, draw: int):
    """The parent contract's intervention, over the whole scalar panel.

    Rows are emitted grouped by donor and sorted by stable key, which is the
    order the frozen builders derive internally, so their own sorting is the
    identity on what they are handed.
    """
    csr = matrix.tocsr() if sp.issparse(matrix) else sp.csr_matrix(matrix)
    rows = []
    libraries: list[float] = []
    unchanged = True
    for donor in donors:
        donor_keys = keys[donor]
        for local, row_index in enumerate(indices[donor]):
            row = csr[row_index]
            counts = row.data.astype(np.int64)
            original_library = float(library[row_index])
            remainder = max(0.0, original_library - float(counts.sum()))
            if level >= 1.0:
                rows.append(row)
                libraries.append(original_library)
                continue
            unchanged = False
            generator = np.random.default_rng(
                _cell_seed(draw, level, donor, donor_keys[local]))
            thinned = generator.binomial(counts, level)
            if np.any(thinned > counts):
                _fail("thinning increased a count for donor %s" % donor)
            thinned_remainder = float(
                generator.binomial(int(round(remainder)), level))
            keep = thinned > 0
            rows.append(sp.csr_matrix(
                (thinned[keep].astype(np.float64), row.indices[keep],
                 np.array([0, int(keep.sum())])), shape=row.shape))
            thinned_library = float(thinned.sum()) + thinned_remainder
            if thinned_library > original_library + 1e-9:
                _fail("thinning increased the library for donor %s" % donor)
            if thinned_library <= 0:
                _fail("thinning emptied the library for donor %s" % donor)
            libraries.append(thinned_library)
    return sp.vstack(rows, format="csr"), np.asarray(libraries,
                                                     dtype=np.float64), unchanged


def coherence_of(*, builder, prenorms, support_mod, loo_mod, holdout, donor_id,
                 stable_key, library, masks, scale, decision_mask):
    prenorms.clear()
    donors, vectors, tail_counts, rest_counts = builder(
        holdout_raw_counts=holdout, donor_id=donor_id, stable_key=stable_key,
        source_library=library, tail_masks_by_donor=masks, scale=scale,
        decision_mask=decision_mask)
    support = support_mod.adjudicate_tail_support_coherence(
        vectors, tail_counts, rest_counts)
    record: dict[str, Any] = {
        "support_ok": bool(support["support_ok"]),
        "coherence_ok": bool(support["coherence_ok"]),
        "decision_donors": int(support["decision_donors"]),
        "donors": [str(d) for d in donors],
        "tail_counts": [int(c) for c in tail_counts],
        "rest_counts": [int(c) for c in rest_counts],
        "prenormalisation_l2_norms": [float(x) for x in prenorms],
    }
    coherence = support.get("coherence")
    if coherence:
        record["coherence"] = {k: (float(v) if isinstance(v, float) else int(v))
                               for k, v in coherence.items()}
        usable = np.asarray([np.linalg.norm(v) > 0 for v in vectors])
        if int(usable.sum()) >= 3:
            loo = loo_mod.loo_coherence(vectors[usable])
            record["loo_mean_cosine"] = float(loo["loo_mean_cosine"])
            record["loo_median_cosine"] = float(loo["loo_median_cosine"])
            record["loo_positive_fraction"] = float(loo["loo_positive_fraction"])
    return record, np.asarray(vectors, dtype=np.float64)


def run(*, confirmation_pkg: Path, discovery_pkg: Path, tail_dir: Path,
        membership: Path, feature_split: Path, outdir: Path,
        log=print) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    contract_bytes = (root / CONTRACT).read_bytes()
    parent_bytes = (root / PARENT_CONTRACT).read_bytes()
    contract = json.loads(contract_bytes.decode("utf-8"))
    parent = json.loads(parent_bytes.decode("utf-8"))
    if contract.get("status") != "FROZEN_BEFORE_EXECUTION":
        _fail("the holdout thinning contract is not frozen")

    # PARENT_INTERVENTION_IDENTITY_EXACT
    intervention = contract["measurement_intervention"]
    if intervention["retention_levels"] != parent["retention_levels"]:
        _fail("retention levels differ from the parent thinning contract")
    if intervention["draws_per_level"] != parent["draws_per_level"]:
        _fail("draws per level differ from the parent thinning contract")
    if parent["seed_derivation"]["namespace"] != PARENT_NAMESPACE.decode():
        _fail("the parent seed namespace is %r, not %r"
              % (parent["seed_derivation"]["namespace"],
                 PARENT_NAMESPACE.decode()))
    levels = intervention["retention_levels"]
    draws = int(intervention["draws_per_level"])
    log("parent intervention identity verified: levels %s, draws %d"
        % (levels, draws))

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
    frozen_coherence = frozen_preflight["support"]["coherence"]
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
    feature_mod = stage2a._frozen("t0_feature_authority_v1")

    feature = feature_mod.load_feature_authority(str(feature_split))
    roles = feature.feature_role.to_numpy()
    address_ids = feature.molecular_address_id.astype(str).to_numpy()
    scoring_pos = np.flatnonzero(roles == "SCORING")
    holdout_pos = np.flatnonzero(roles == "COHERENCE_HOLDOUT")

    # SCORING_FEATURE_EXCLUSION
    if set(scoring_pos.tolist()) & set(holdout_pos.tolist()):
        _fail("SCORING and COHERENCE_HOLDOUT positions overlap")
    log("%d SCORING excluded, %d COHERENCE_HOLDOUT validation features"
        % (len(scoring_pos), len(holdout_pos)))

    # The frozen discovery-fit scale and decision mask, never refit.
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
    log("holdout decision features %d reproduce the frozen authority" % features)

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

    order = np.concatenate([indices[d] for d in donors])
    donor_id_ordered = np.asarray(
        [str(x) for x in np.asarray(conf["donor_id"])[order]])
    stable_key_ordered = np.asarray(conf["stable_key"])[order]
    library_all = np.asarray(conf["source_library"], dtype=np.float64)
    label_signature = _sha256_bytes(b"".join(
        np.asarray(frozen_masks[d], dtype=np.bool_).tobytes()
        for d in donors))
    cell_signature = _sha256_bytes(
        "|".join(str(k) for k in stable_key_ordered).encode("utf-8"))

    builder, prenorms, instrumentation = instrumented_holdout_vectors(preflight)
    log("holdout vector builder instrumented by one substituted line")

    # --- baseline, unthinned ------------------------------------------------
    conf_csr = conf["matrix"].tocsr() if sp.issparse(conf["matrix"]) \
        else sp.csr_matrix(conf["matrix"])
    baseline_holdout = conf_csr[order][:, holdout_pos]
    baseline, baseline_vectors = coherence_of(
        builder=builder, prenorms=prenorms, support_mod=support_mod,
        loo_mod=loo_mod, holdout=baseline_holdout,
        donor_id=donor_id_ordered, stable_key=stable_key_ordered,
        library=library_all[order], masks=frozen_masks, scale=scale,
        decision_mask=decision_mask)
    baseline["retention"] = None
    baseline["draw"] = None
    baseline["label"] = "BASELINE_UNTHINNED"

    # LEVEL_1_COHERENCE_EXACT, against the committed object
    observed = baseline.get("coherence") or {}
    for field, committed in frozen_coherence.items():
        if field not in observed:
            _fail("baseline coherence is missing %r" % field)
        if isinstance(committed, float):
            if float(observed[field]) != float(committed):
                _fail("baseline %s %r does not reproduce the committed %r"
                      % (field, observed[field], committed))
        elif int(observed[field]) != int(committed):
            _fail("baseline %s %r does not reproduce the committed %r"
                  % (field, observed[field], committed))
    log("baseline reproduces the committed frozen coherence object exactly")

    level_rows: list[dict[str, Any]] = [baseline]
    donor_rows: list[dict[str, Any]] = []
    for j, donor in enumerate(baseline["donors"]):
        donor_rows.append({
            "retention": "", "draw": "", "donor_id": donor,
            "tail_cells": baseline["tail_counts"][j],
            "rest_cells": baseline["rest_counts"][j],
            "prenormalisation_l2_norm": baseline["prenormalisation_l2_norms"][j],
            "cosine_to_unthinned": 1.0,
        })

    for level in levels:
        for draw in range(draws):
            thinned, libraries, unchanged = thin_full_panel(
                conf["matrix"], donors, indices, keys, library_all,
                float(level), draw)

            # LEVEL_1_COUNTS_AND_LIBRARY_EXACT
            if float(level) >= 1.0:
                if not unchanged:
                    _fail("retention 1.0 modified counts")
                if not np.array_equal(libraries, library_all[order]):
                    _fail("retention 1.0 modified source_library")
                delta = (thinned - baseline_holdout_full(conf_csr, order))
                if delta.nnz:
                    _fail("retention 1.0 modified the scalar counts")

            record, vectors = coherence_of(
                builder=builder, prenorms=prenorms, support_mod=support_mod,
                loo_mod=loo_mod, holdout=thinned[:, holdout_pos],
                donor_id=donor_id_ordered, stable_key=stable_key_ordered,
                library=libraries, masks=frozen_masks, scale=scale,
                decision_mask=decision_mask)
            record["retention"] = level
            record["draw"] = draw
            record["label"] = "THINNED"

            # DONOR_CELL_AND_LABEL_IDENTITY_FIXED
            if record["donors"] != baseline["donors"]:
                _fail("the donor set changed at retention %s" % level)
            if record["tail_counts"] != baseline["tail_counts"] or \
                    record["rest_counts"] != baseline["rest_counts"]:
                _fail("support counts changed at retention %s, but the "
                      "grouping is fixed and they cannot" % level)

            cosines = []
            for j in range(len(vectors)):
                a = baseline_vectors[j]
                b = vectors[j]
                na = float(np.linalg.norm(a))
                nb = float(np.linalg.norm(b))
                cosines.append(float(a @ b / (na * nb))
                               if na > 0 and nb > 0 else None)
            record["donor_cosine_to_unthinned"] = cosines
            usable = [c for c in cosines if c is not None]
            record["mean_donor_cosine_to_unthinned"] = \
                float(np.mean(usable)) if usable else None
            record["min_donor_cosine_to_unthinned"] = \
                float(np.min(usable)) if usable else None

            # LEVEL_1_HOLDOUT_VECTOR_EXACT
            if float(level) >= 1.0:
                if not np.array_equal(vectors, baseline_vectors):
                    _fail("retention 1.0 did not reproduce the unthinned "
                          "holdout vectors exactly")
                if record["prenormalisation_l2_norms"] != \
                        baseline["prenormalisation_l2_norms"]:
                    _fail("retention 1.0 did not reproduce the unthinned "
                          "pre-normalisation norms exactly")

            level_rows.append(record)
            for j, donor in enumerate(record["donors"]):
                donor_rows.append({
                    "retention": level, "draw": draw, "donor_id": donor,
                    "tail_cells": record["tail_counts"][j],
                    "rest_cells": record["rest_counts"][j],
                    "prenormalisation_l2_norm":
                        record["prenormalisation_l2_norms"][j],
                    "cosine_to_unthinned": cosines[j],
                })

            coherence = record.get("coherence") or {}
            log("  retention %-5s draw %d  support %-5s coh %-5s  cos %s  "
                "p %s  dir cos %.4f"
                % (level, draw, record["support_ok"], record["coherence_ok"],
                   ("%.6f" % coherence["mean_pairwise_cosine"])
                   if coherence else "n/a",
                   ("%.3e" % coherence["p_upper_exact"]) if coherence else "n/a",
                   record["mean_donor_cosine_to_unthinned"] or float("nan")))

    log("control level reproduced counts, library, vectors, norms and coherence")

    outdir.mkdir(parents=True, exist_ok=True)
    level_path = outdir / LEVEL_CSV
    with io.open(level_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(["label", "retention", "draw", "support_ok",
                         "coherence_ok", "decision_donors",
                         "mean_pairwise_cosine", "p_upper_exact",
                         "sign_configurations", "null_min", "null_max",
                         "loo_mean_cosine", "loo_positive_fraction",
                         "mean_donor_cosine_to_unthinned",
                         "min_donor_cosine_to_unthinned"])
        for row in level_rows:
            coherence = row.get("coherence") or {}
            writer.writerow([
                row["label"],
                "" if row["retention"] is None else row["retention"],
                "" if row["draw"] is None else row["draw"],
                row["support_ok"], row["coherence_ok"], row["decision_donors"],
                repr(float(coherence["mean_pairwise_cosine"])) if coherence else "",
                repr(float(coherence["p_upper_exact"])) if coherence else "",
                coherence.get("sign_configurations", ""),
                repr(float(coherence["null_min"])) if coherence else "",
                repr(float(coherence["null_max"])) if coherence else "",
                repr(float(row["loo_mean_cosine"]))
                if "loo_mean_cosine" in row else "",
                repr(float(row["loo_positive_fraction"]))
                if "loo_positive_fraction" in row else "",
                repr(float(row["mean_donor_cosine_to_unthinned"]))
                if row.get("mean_donor_cosine_to_unthinned") is not None else "",
                repr(float(row["min_donor_cosine_to_unthinned"]))
                if row.get("min_donor_cosine_to_unthinned") is not None else "",
            ])

    donor_path = outdir / DONOR_CSV
    with io.open(donor_path, "w", encoding="utf-8", newline="") as handle:
        writer = csvmod.writer(handle, lineterminator="\n")
        writer.writerow(["retention", "draw", "donor_id", "tail_cells",
                         "rest_cells", "prenormalisation_l2_norm",
                         "cosine_to_unthinned"])
        for row in donor_rows:
            cosine = row["cosine_to_unthinned"]
            writer.writerow([row["retention"], row["draw"], row["donor_id"],
                             row["tail_cells"], row["rest_cells"],
                             repr(float(row["prenormalisation_l2_norm"])),
                             repr(float(cosine)) if cosine is not None else ""])

    report = {
        "schema": "JEPA_T0_TAIL_HOLDOUT_THINNING_PROBE_V1",
        "step": "3 of the QC methodology investigation",
        "implements_contract": CONTRACT,
        "contract_sha256": _sha256_bytes(contract_bytes),
        "parent_thinning_contract": PARENT_CONTRACT,
        "parent_contract_sha256": _sha256_bytes(parent_bytes),
        "diagnostic_only": True,
        "frozen_tail_terminal": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "training_authorized": False,
        "t0_v20_modified": False,
        "frozen_target_modified": False,
        "frozen_tail_threshold_modified": False,
        "frozen_tail_mask_modified": False,
        "qc_alpha_modified": False,
        "coherence_rule_modified": False,
        "holdout_scale_refit": False,
        "tail_labels_recomputed_after_thinning": False,
        "scoring_features_entering_validation": 0,
        "remediation_designed_or_tested": False,
        "matched_qc_analysis_designed": False,
        "pathology_blind": True,
        "reads_at8": False,
        "baseline_reproduces_committed_coherence": True,
        "control_level_exact": True,
        "holdout_vector_builder_instrumentation": instrumentation,
        "scoring_addresses_excluded": int(len(scoring_pos)),
        "holdout_addresses": int(len(holdout_pos)),
        "holdout_decision_features": features,
        "committed_coherence": frozen_coherence,
        "interpretation_limits": contract["interpretation_limits"],
        "per_level": level_rows,
        "machine_readable": {"level_csv": level_path.name,
                             "donor_csv": donor_path.name},
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
            "membership_sha256": _sha256_bytes(Path(membership).read_bytes()),
            "holdout_address_ids_sha256":
                _sha256_bytes("|".join(address_ids[holdout_pos]
                                       ).encode("utf-8")),
            "holdout_decision_mask_sha256":
                _sha256_bytes(np.asarray(decision_mask,
                                         dtype=np.bool_).tobytes()),
            "holdout_scale_sha256":
                _sha256_bytes(np.asarray(scale, dtype=np.float64).tobytes()),
            "donor_set": [str(d) for d in donors],
            "frozen_tail_label_signature_sha256": label_signature,
            "confirmation_cell_signature_sha256": cell_signature,
            "seed_namespace": PARENT_NAMESPACE.decode(),
        },
        "numeric_environment": numeric_environment.numeric_environment(),
    }
    out = outdir / REPORT
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                default=str) + "\n")
    log("wrote %s, %s, %s" % (out.name, level_path.name, donor_path.name))
    return report


def baseline_holdout_full(conf_csr, order):
    """The unthinned panel in the probe's row order, for the level-1.0 check."""
    return conf_csr[order]


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
    print("%-20s %5s %8s %8s %13s %11s %9s %9s"
          % ("label", "ret", "support", "coher", "mean cosine", "exact p",
             "dir cos", "min cos"))
    for row in report["per_level"]:
        coherence = row.get("coherence") or {}
        print("%-20s %5s %8s %8s %13s %11s %9s %9s"
              % (row["label"],
                 "-" if row["retention"] is None else row["retention"],
                 row["support_ok"], row["coherence_ok"],
                 ("%.6f" % coherence["mean_pairwise_cosine"])
                 if coherence else "n/a",
                 ("%.3e" % coherence["p_upper_exact"]) if coherence else "n/a",
                 ("%.4f" % row["mean_donor_cosine_to_unthinned"])
                 if row.get("mean_donor_cosine_to_unthinned") is not None
                 else "-",
                 ("%.4f" % row["min_donor_cosine_to_unthinned"])
                 if row.get("min_donor_cosine_to_unthinned") is not None
                 else "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
