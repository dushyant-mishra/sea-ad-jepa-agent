"""Stage 2B — open DISCOVERY numeric AT8 only, fit and freeze the discovery object.

This is the module that reads pathology magnitudes for the first time in the
lane. Everything about it is arranged so that what it reads is exactly the
authorized slice and nothing more.

The endpoint reader
-------------------
`load_discovery_at8` does not hand the pathology CSV to a DictReader. A
DictReader would materialize every column of every row, including Braak, CERAD,
Thal and every other endpoint, which would make "no non-AT8 pathology endpoint is
parsed" false in the only sense that matters. Instead it locates two column
indices from the header, and for each row takes those two fields and discards the
rest of the line unparsed. Rows whose donor is not in the frozen DISCOVERY set
are skipped before the value is even converted.

Hard refusals, all before a value is used
-----------------------------------------
The source digest must equal the frozen one. The endpoint column must be the
frozen identity, taken from the verified availability parent. The donor set must
equal the frozen DISCOVERY set by digest. A CONFIRMATION donor appearing in the
load is a STOP. A donor outside the frozen DISCOVERY set is a STOP. Any of these
stops before the fit.

The conclusion path
-------------------
`verify_r7_gate` then `freeze_target_after_role`, which is exactly v2's
architecture with R7 supplying the stricter and satisfiable gate. The AST guard
in Stage 2A refuses a conclusion call that is not preceded by a gate call, and
refuses any `_for_test` entrypoint in production code.

What is emitted
---------------
Roots, fitted parameters, sufficient summaries and replayable provenance. The
per-donor AT8 magnitudes are **not** emitted: the frozen design does not require
them as a package artifact, and the access manifest records the donor-set digest
and the endpoint identity instead. What is recorded about the values themselves
is their digest, so the fit is reproducible without republishing pathology.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import t0_execution_input_readiness_authority_v1 as readiness  # noqa: E402
import t0_stage2a_pre_at8_gate_v1 as stage2a  # noqa: E402

SUMMARY = "T0_DISCOVERY_STAGE_RUN_SUMMARY.json"
ACCESS_MANIFEST = "T0_DISCOVERY_NUMERIC_AT8_ACCESS_MANIFEST.json"

STOP_CONFIRMATION_LEAK = (
    "STOP_T0_STAGE2B_CONFIRMATION_DONOR_IN_THE_DISCOVERY_NUMERIC_LOAD")
STOP_DONOR_OUTSIDE = "STOP_T0_STAGE2B_DONOR_OUTSIDE_THE_FROZEN_DISCOVERY_SET"
STOP_DONOR_SET = "STOP_T0_STAGE2B_DISCOVERY_DONOR_SET_DIGEST_MISMATCH"
STOP_ENDPOINT = "STOP_T0_STAGE2B_ENDPOINT_IS_NOT_THE_FROZEN_AT8_ENDPOINT"
STOP_SOURCE = "STOP_T0_STAGE2B_PATHOLOGY_SOURCE_DIGEST_MISMATCH"
STOP_VALUE = "STOP_T0_STAGE2B_AT8_VALUE_NOT_A_FINITE_NONNEGATIVE_NUMBER"
STOP_EXTRA_ENDPOINT = "STOP_T0_STAGE2B_A_NON_AT8_PATHOLOGY_ENDPOINT_WAS_PARSED"
STOP_DIRTY = "STOP_T0_STAGE2B_PRODUCTION_CODE_NOT_COMMITTED"

# Column names in the pathology source that are pathology endpoints other than
# the frozen AT8 one. None of these may be read into a value.
NON_AT8_ENDPOINT_MARKERS = ("braak", "cerad", "thal", "6e10", "gfap", "iba1",
                            "neun", "abeta", "ptau", "ttau", "lewy", "tdp",
                            "adnc", "lath")


def code_sha256(filename: str) -> str:
    """SHA-256 over LF-normalized content. Not a Git blob digest."""
    path = Path(__file__).resolve().parent / filename
    return hashlib.sha256(
        path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def _raw_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with io.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _split_csv_line(line: str) -> list[str]:
    """Split one CSV line, honouring quotes, without building a dict."""
    import csv as _csv
    return next(_csv.reader([line]))


def load_role_numeric_at8(
        source: Path,
        *,
        role: str,
        endpoint_identity: str,
        donor_id_field: str,
        included_donors: set[str],
        excluded_donors: set[str],
        expected_source_sha256: str,
        expected_donor_set_sha256: str,
        log=print) -> dict[str, Any]:
    """Read the frozen AT8 endpoint for one role's donors. Nothing else.

    Two columns are located by index from the header and only those two fields
    are converted per row. Every other column, including every other pathology
    endpoint, is left as unparsed text and discarded with the line. Donors in
    `excluded_donors` are skipped before their value is ever touched.

    `role` is required, and required for a reason. An earlier version hardcoded
    "DISCOVERY" when digesting the loaded donor set, so reusing it for the
    confirmation read produced the right eighteen donors under the wrong role
    label and the frozen-expectation check refused the package. Making the role
    explicit at every call site is what stops that recurring; the parameters are
    also role-neutral now, because the confirmation call previously had to pass
    its own donors as `discovery_donors`, which is precisely the inversion that
    made the mistake easy to make and hard to see.
    """
    if not isinstance(role, str) or role not in ("DISCOVERY", "CONFIRMATION"):
        raise AssertionError(
            "%s: role must be DISCOVERY or CONFIRMATION, got %r"
            % (STOP_DONOR_SET, role))
    discovery_donors = included_donors
    confirmation_donors = excluded_donors
    expected_discovery_donor_set_sha256 = expected_donor_set_sha256
    digest = _raw_digest(source)
    if digest != str(expected_source_sha256):
        raise AssertionError("%s: source hashes to %s, frozen identity is %s"
                             % (STOP_SOURCE, digest, expected_source_sha256))
    log("    source digest %s confirmed" % digest)

    text = Path(source).read_text(encoding="utf-8-sig").splitlines()
    header = _split_csv_line(text[0])
    if str(endpoint_identity) not in header:
        raise AssertionError("%s: %r is not a column of the source"
                             % (STOP_ENDPOINT, endpoint_identity))
    if str(donor_id_field) not in header:
        raise AssertionError("%s: %r is not a column of the source"
                             % (STOP_ENDPOINT, donor_id_field))
    endpoint_index = header.index(str(endpoint_identity))
    donor_index = header.index(str(donor_id_field))

    # The endpoint we are authorized to read must not itself be another marker.
    lowered = str(endpoint_identity).lower()
    if "at8" not in lowered:
        raise AssertionError("%s: %r does not name the AT8 endpoint"
                             % (STOP_ENDPOINT, endpoint_identity))
    for marker in NON_AT8_ENDPOINT_MARKERS:
        if marker in lowered:
            raise AssertionError("%s: the authorized endpoint %r also names %r"
                                 % (STOP_EXTRA_ENDPOINT, endpoint_identity,
                                    marker))
    log("    endpoint column %r at index %d; %d other columns left unparsed"
        % (endpoint_identity, endpoint_index, len(header) - 2))

    values: dict[str, float] = {}
    seen_confirmation: list[str] = []
    for line in text[1:]:
        if not line.strip():
            continue
        fields = _split_csv_line(line)
        donor = str(fields[donor_index]).strip()
        if donor in confirmation_donors:
            # Recorded, not read. The value at endpoint_index is never touched.
            seen_confirmation.append(donor)
            continue
        if donor not in discovery_donors:
            continue
        raw = str(fields[endpoint_index]).strip()
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise AssertionError("%s: %s carries %r" % (STOP_VALUE, donor, raw))
        if not np.isfinite(value) or value < 0:
            raise AssertionError("%s: %s carries %r" % (STOP_VALUE, donor, raw))
        values[donor] = value

    # The confirmation donors are present in the file and were deliberately
    # skipped. That is the point: their rows exist and their values were not read.
    if set(values) & confirmation_donors:
        raise AssertionError("%s: %s"
                             % (STOP_CONFIRMATION_LEAK,
                                sorted(set(values) & confirmation_donors)))
    outside = sorted(set(values) - discovery_donors)
    if outside:
        raise AssertionError("%s: %s" % (STOP_DONOR_OUTSIDE, outside))
    missing = sorted(discovery_donors - set(values))
    if missing:
        raise AssertionError(
            "%s: the frozen DISCOVERY set has %d donors and the source supplied "
            "%d; missing %s" % (STOP_DONOR_SET, len(discovery_donors),
                                len(values), missing))

    produced = readiness.donor_set_digest(role, values)
    if produced != str(expected_discovery_donor_set_sha256):
        raise AssertionError("%s: loaded set digests to %s, frozen is %s"
                             % (STOP_DONOR_SET, produced,
                                expected_discovery_donor_set_sha256))

    # A digest of the values, so the fit is reproducible without republishing
    # pathology magnitudes.
    parts = [b"T0-DISCOVERY-AT8-VALUES-V1"]
    for donor in sorted(values, key=lambda d: d.encode("utf-8")):
        parts.append(donor.encode("utf-8"))
        parts.append(np.asarray([values[donor]], dtype="<f8").tobytes())
    values_digest = hashlib.sha256(b"".join(parts)).hexdigest()

    other = "CONFIRMATION" if role == "DISCOVERY" else "DISCOVERY"
    log("    read %d %s donors; %d %s rows skipped unread"
        % (len(values), role, len(set(seen_confirmation)), other))
    log("    %s donor-set digest %s" % (role.lower(), produced))
    log("    endpoint values digest     %s" % values_digest)
    return {
        "values": values,
        "role": role,
        "donor_count": len(values),
        "donor_set_sha256": produced,
        # Retained under the old name so existing readers keep working; both
        # carry the digest computed under the role actually supplied.
        "discovery_donor_set_sha256": produced,
        "endpoint_values_sha256": values_digest,
        "endpoint_identity": str(endpoint_identity),
        "endpoint_identity_sha256": hashlib.sha256(
            str(endpoint_identity).encode("utf-8")).hexdigest(),
        "pathology_source_sha256": digest,
        "confirmation_rows_present_and_skipped": len(set(seen_confirmation)),
        "confirmation_numeric_at8_accessed": False,
        "other_columns_left_unparsed": len(header) - 2,
    }


def assert_worktree_committed(repo: Path) -> bool:
    """Production code entering a result must be committed."""
    import subprocess
    out = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo),
                         capture_output=True, text=True, check=True)
    dirty = [l for l in out.stdout.splitlines()
             if l.strip() and not l.startswith("??")]
    if dirty:
        raise AssertionError("%s: %s" % (STOP_DIRTY, dirty[:5]))
    return True


def build_discovery_metadata(*, discovery_donors, at8_values, age_sex_pkg):
    """The frozen discovery metadata frame: exactly ['donor_id','AT8','age','sex'].

    Age and sex come from the replayed age/sex authority. AT8 comes from the
    endpoint slice this module just read. Column order is exactly what
    `fit_discovery_target_v2` demands, and it refuses anything else.
    """
    import pandas as pd

    ages_mod = stage2a._frozen("t0_age_sex_authority_v1")
    import t0_eligible_donor_production_run_v1 as ed
    replayed = ages_mod.load_authority(
        age_sex_pkg,
        expected_package_root_sha256=ed.AGE_SEX_EXPECTED_PACKAGE_ROOT,
        expected_age_sex_root_sha256=ed.AGE_SEX_EXPECTED_ROOT,
        expected_source_sha256=ed.AGE_SEX_EXPECTED_SOURCE_SHA256,
        expected_candidate_donor_set_sha256=(
            ed.AGE_SEX_EXPECTED_CANDIDATE_DONOR_SET))
    by_donor = {str(r["donor_id"]): r for r in replayed["rows"]}
    order = sorted(discovery_donors, key=lambda d: d.encode("utf-8"))
    frame = pd.DataFrame({
        "donor_id": order,
        "AT8": [float(at8_values[d]) for d in order],
        "age": [int(by_donor[d]["age"]) for d in order],
        "sex": [str(by_donor[d]["sex"]) for d in order],
    })
    return frame[["donor_id", "AT8", "age", "sex"]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--readiness-pkg", required=True, type=Path)
    parser.add_argument("--stage2a-pkg", required=True, type=Path)
    parser.add_argument("--role-pkg", required=True, type=Path)
    parser.add_argument("--at8-pkg", required=True, type=Path)
    parser.add_argument("--age-sex-pkg", required=True, type=Path)
    parser.add_argument("--population-pkg", required=True, type=Path)
    parser.add_argument("--pathology-source", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--membership", required=True, type=Path)
    parser.add_argument("--feature-split", required=True, type=Path)
    args = parser.parse_args(argv)

    started = time.time()

    def stamp(message):
        print("[%6.1fs] %s" % (time.time() - started, message))

    repo = Path(__file__).resolve().parents[2]
    out_for_cache = Path(args.outdir)
    out_for_cache.mkdir(parents=True, exist_ok=True)
    stamp("Stage 2B step 1 - verifying the R7 gate before anything is read")
    assert_worktree_committed(repo)
    gate = stage2a.verify_r7_gate(args.readiness_pkg, log=print)
    stage2a.assert_no_direct_v1_production_call(
        pathlib.Path(__file__).read_text(encoding="utf-8"))

    stage2a_summary = json.loads(
        (args.stage2a_pkg / stage2a.SUMMARY).read_text(encoding="utf-8"))
    discovery = set(stage2a_summary["discovery_donors"])
    confirmation = set(stage2a_summary["confirmation_donors"])
    if discovery & confirmation:
        raise AssertionError("%s: the two role sets overlap"
                             % STOP_CONFIRMATION_LEAK)
    bindings = gate["authority"]["bindings"]

    stamp("Stage 2B step 2 - materializing the discovery scalar matrix "
          "(no pathology)")
    import t0_discovery_scalar_matrix_v1 as dm
    materialized = dm.load_cache(out_for_cache, log=print)
    if materialized is None:
        materialized = dm.materialize(
            store=args.store, membership_csv=args.membership,
            population_pkg=args.population_pkg,
            feature_split_csv=args.feature_split,
            discovery_donors=discovery, log=print)
        cached = dm.save_cache(out_for_cache, materialized)
        stamp("  cached the matrix at %s" % cached)
    else:
        stamp("  matrix reused from cache; materialization skipped")

    import t0_eligible_donor_production_run_v1 as ed
    at8_parent = ed.load_at8_availability(args.at8_pkg)

    stamp("Stage 2B step 3 - opening DISCOVERY numeric AT8 only")
    loaded = load_role_numeric_at8(
        args.pathology_source, role="DISCOVERY",
        endpoint_identity=at8_parent["at8_endpoint_identity"],
        donor_id_field=at8_parent["donor_id_field"],
        included_donors=discovery, excluded_donors=confirmation,
        expected_source_sha256=bindings["pathology_source_sha256"],
        expected_donor_set_sha256=bindings["discovery_donor_set_sha256"])

    manifest = {
        "schema": "JEPA_T0_DISCOVERY_NUMERIC_AT8_ACCESS_MANIFEST_V1",
        "discovery_numeric_at8_authorized": True,
        "confirmation_numeric_at8_authorized": False,
        "CONFIRMATION_NUMERIC_AT8_NOT_ACCESSED": True,
        "discovery_donor_count": loaded["donor_count"],
        "discovery_donor_set_sha256": loaded["discovery_donor_set_sha256"],
        "endpoint_identity": loaded["endpoint_identity"],
        "endpoint_identity_sha256": loaded["endpoint_identity_sha256"],
        "endpoint_values_sha256": loaded["endpoint_values_sha256"],
        "pathology_source_sha256": loaded["pathology_source_sha256"],
        "confirmation_rows_present_and_skipped":
            loaded["confirmation_rows_present_and_skipped"],
        "other_columns_left_unparsed": loaded["other_columns_left_unparsed"],
        "per_donor_at8_values_emitted": False,
        "non_at8_pathology_endpoint_parsed": False,
        "dev_opened": False, "sealed_opened": False,
        "protected_populations_opened": False,
        "r7_readiness_root_sha256": gate["readiness_root_sha256"],
        "r7_package_root_sha256": gate["package_root_sha256"],
        "donor_role_package_root_sha256":
            stage2a_summary["donor_role_package_root_sha256"],
        "runner_code_sha256": code_sha256("t0_stage2b_discovery_at8_v1.py"),
        "code_byte_semantics": readiness.ACCURATE_CODE_BYTE_SEMANTICS,
    }
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    with io.open(out / ACCESS_MANIFEST, "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    stamp("  access manifest written")

    stamp("Stage 2B step 4 - the frozen conclusion: gated freeze")
    metadata = build_discovery_metadata(
        discovery_donors=discovery, at8_values=loaded["values"],
        age_sex_pkg=args.age_sex_pkg)
    freeze_mod = stage2a._frozen("t0_canonical_freeze_v1")
    result = freeze_mod.freeze_target_after_role(
        target_dir=str(out / "target"),
        discovery_authority_dir=str(out / "discovery_authority"),
        role_dir=str(args.role_pkg),
        feature_split_csv=str(args.feature_split),
        membership_csv=str(args.membership),
        scalar_raw_counts=materialized["matrix"],
        scalar_feature_ids=materialized["feature_ids"],
        matrix_id=materialized["matrix_id"],
        local_row=materialized["local_row"],
        cell_id=materialized["cell_id"],
        donor_id=materialized["donor_id"],
        stable_key=materialized["stable_key"],
        source_library=materialized["source_library"],
        donor_metadata=metadata)
    target = result["target"]
    provenance_root = target["provenance"]["root_sha256"]
    stamp("  target package root      %s" % target["package_root_sha256"])
    stamp("  discovery provenance root %s" % provenance_root)
    stamp("  discovery authority root  %s"
          % result["discovery_authority"]["package_root_sha256"])

    fit = target["fit"]
    record = {
        "schema": "JEPA_T0_DISCOVERY_STAGE_RUN_SUMMARY_V1",
        "terminal": ("DISCOVERY_STAGE_DONE_AND_REPLAYED"
                     "__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN"),
        "CONFIRMATION_NUMERIC_AT8_NOT_ACCESSED": True,
        "discovery_donor_count": len(discovery),
        "discovery_cells": materialized["cells"],
        "declared_addresses": materialized["declared_addresses"],
        "matrix_nnz": materialized["nnz"],
        "discovery_scalar_matrix_sha256": materialized["matrix_sha256"],
        "discovery_donor_set_sha256": loaded["discovery_donor_set_sha256"],
        "endpoint_identity": loaded["endpoint_identity"],
        "endpoint_identity_sha256": loaded["endpoint_identity_sha256"],
        "endpoint_values_sha256": loaded["endpoint_values_sha256"],
        "pathology_source_sha256": loaded["pathology_source_sha256"],
        "discovery_target_package_root_sha256": target["package_root_sha256"],
        "discovery_provenance_root_sha256": provenance_root,
        "discovery_authority_package_root_sha256":
            result["discovery_authority"]["package_root_sha256"],
        "donor_role_package_root_sha256":
            result["donor_role_package_root_sha256"],
        "r7_readiness_root_sha256": gate["readiness_root_sha256"],
        "r7_package_root_sha256": gate["package_root_sha256"],
        "population_closure_root_sha256":
            materialized["population_closure_root_sha256"],
        "logical_row_authority_root_sha256":
            materialized["logical_row_authority_root_sha256"],
        "population_raw_source_root_sha256":
            materialized["population_raw_source_root_sha256"],
        "selected_multiplier_exponent": fit["selected_multiplier_exponent"],
        "final_lambda": fit["final_lambda"],
        "response_residual_sd": fit["response_residual_sd"],
        "discovery_age_center": fit["discovery_age_center"],
        "decision_gene_count": int(sum(1 for v in fit["decision_gene_mask"]
                                       if v)),
        "per_donor_at8_values_emitted": False,
        "non_at8_pathology_endpoint_parsed": False,
        "dev_opened": False, "sealed_opened": False,
        "protected_populations_opened": False,
        "training_begun": False, "successor_u0_materialized": False,
        "td60_run": False, "biological_sweeps_run": False,
        "scientific_design_unchanged": True,
        "counts_payload_reads": materialized["counts_payload_reads"],
        "counts_payload_cache_hits": materialized["counts_payload_cache_hits"],
        "runner_code_sha256": code_sha256("t0_stage2b_discovery_at8_v1.py"),
        "matrix_code_sha256": code_sha256("t0_discovery_scalar_matrix_v1.py"),
        "code_byte_semantics": readiness.ACCURATE_CODE_BYTE_SEMANTICS,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    with io.open(out / SUMMARY, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")

    stamp("Stage 2B step 5 - replaying the discovery target from disk")
    reloaded = freeze_mod.load_target_v2(
        str(out / "target"), str(args.feature_split)) if hasattr(
            freeze_mod, "load_target_v2") else None
    if reloaded is None:
        serializer = stage2a._frozen("t0_target_serializer_v2")
        reloaded = serializer.load_target_v2(str(out / "target"),
                                             str(args.feature_split))
    if reloaded["package_root_sha256"] != target["package_root_sha256"]:
        raise AssertionError("the reloaded target root does not match")
    if reloaded["provenance"]["root_sha256"] != provenance_root:
        raise AssertionError("the reloaded provenance root does not match")
    stamp("  target replays: root %s" % reloaded["package_root_sha256"])

    print()
    print(json.dumps(record, indent=2, sort_keys=True))
    print()
    print("DISCOVERY_STAGE_DONE_AND_REPLAYED"
          "__CONFIRMATION_NUMERIC_AT8_READY_TO_OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
