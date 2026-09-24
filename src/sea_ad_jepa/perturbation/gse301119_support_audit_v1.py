"""Independent GSE301119 GUIDE×DONOR SUPPORT census, metadata only.

This CPU audit reads ONLY the SHA-bound lightweight metadata CSVs committed
with PR #77 raw-pseudobulk receipts, NOT heavyweight RNA or protected FULL104
outcomes. It makes NO differential-expression, guide-effect significance,
donor-population uncertainty, JEPA-prediction or therapeutic claim.

The SHA pins are from the reviewed producer SHA256SUMS_PERTURBATION_ETL.txt,
not from a caller-created local replacement. Changing source bytes requires
a deliberate new authority/version, not a caller-provided expected digest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

EXPECTED_CSV = {
    "CRISPRa": (
        "e13c3bb2741824139d5adb91b22ad725956078ede98f59cf74a5c1abe96e3397",
        2098, 23584, 1906, 192,
    ),
    "CRISPRi": (
        "ce96daa64413a238173b485a91037df02824e85bc071e715292aa800dee7abe8",
        2137, 28466, 1949, 188,
    ),
}
EXPECTED_COLUMNS = (
    "guide_donor", "guide_identity", "donor", "Gene_Targeted",
    "crispr", "n_cells", "total_counts",
)
DONORS = frozenset({"D1", "D2"})


class SupportCensusError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def census(path: Path, *, modality: str, test_fixture: bool = False) -> dict:
    if modality not in EXPECTED_CSV:
        raise SupportCensusError("unknown CRISPR modality")
    expected_hash, exp_rows, exp_cells, exp_perturbed, exp_nt = EXPECTED_CSV[modality]
    if not path.is_file():
        raise SupportCensusError(f"missing committed metadata file: {path}")
    observed_hash = sha256_file(path)
    if not test_fixture and observed_hash != expected_hash:
        raise SupportCensusError(
            f"committed {modality} metadata SHA differs from frozen producer evidence"
        )
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise SupportCensusError("raw pseudobulk metadata column schema/order drift")
        rows = list(reader)
    if not rows:
        raise SupportCensusError("empty metadata")
    if not test_fixture and len(rows) != exp_rows:
        raise SupportCensusError("raw pseudobulk guide×donor row census drift")
    seen: set[tuple[str, str]] = set()
    identity: dict[str, tuple[str, str]] = {}
    guide_by_target: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"D1": set(), "D2": set()}
    )
    cells_by_target: dict[str, dict[str, int]] = defaultdict(
        lambda: {"D1": 0, "D2": 0}
    )
    control_guides: dict[str, set[str]] = {"D1": set(), "D2": set()}
    control_cells = {"D1": 0, "D2": 0}
    roles = {"Perturbed": 0, "NT": 0}
    all_cells = 0
    for index, row in enumerate(rows):
        if None in row or any(v is None for v in row.values()):
            raise SupportCensusError(f"malformed CSV row {index}")
        g = row["guide_identity"]
        d = row["donor"]
        t = row["Gene_Targeted"]
        role = row["crispr"]
        if not g or d not in DONORS or not t or role not in roles:
            raise SupportCensusError("unrecognized donor, guide, target or role")
        if row["guide_donor"] != f"{g}||{d}":
            raise SupportCensusError("guide×donor composite identity drift")
        if (g, d) in seen:
            raise SupportCensusError("duplicated guide×donor row")
        seen.add((g, d))
        if role == "NT" and t != "NT":
            raise SupportCensusError("non-targeting guide has a targeted-gene annotation")
        if role == "Perturbed" and t == "NT":
            raise SupportCensusError("perturbed guide has non-targeting target identity")
        if g in identity and identity[g] != (t, role):
            raise SupportCensusError("guide target/role changed across biological donors")
        identity[g] = (t, role)
        try:
            n_cells = int(row["n_cells"])
            n_counts = int(row["total_counts"])
        except ValueError as exc:
            raise SupportCensusError("invalid raw integer cell/UMI count") from exc
        if n_cells < 1 or n_counts < 1:
            raise SupportCensusError("zero/negative cell count or source UMI total")
        if str(n_cells) != row["n_cells"] or str(n_counts) != row["total_counts"]:
            raise SupportCensusError("noncanonical raw integer count")
        all_cells += n_cells
        roles[role] += 1
        if role == "NT":
            control_guides[d].add(g)
            control_cells[d] += n_cells
        else:
            guide_by_target[t][d].add(g)
            cells_by_target[t][d] += n_cells

    if not test_fixture:
        if (all_cells, roles["Perturbed"], roles["NT"]) != (
            exp_cells, exp_perturbed, exp_nt
        ):
            raise SupportCensusError("committed total cells/roles changed")
        if len(guide_by_target) != 206:
            raise SupportCensusError("expected 206 physically characterized perturbation targets")

    targets = []
    for t in sorted(guide_by_target):
        guides = guide_by_target[t]
        both = guides["D1"] & guides["D2"]
        targets.append({
            "target": t,
            "guides_D1": len(guides["D1"]),
            "guides_D2": len(guides["D2"]),
            "same_guide_in_both_donors": len(both),
            "cells_D1": cells_by_target[t]["D1"],
            "cells_D2": cells_by_target[t]["D2"],
            "support_status": (
                "NO_BOTH_DONOR_COVERAGE"
                if min(len(guides["D1"]), len(guides["D2"])) == 0 else
                "SINGLE_GUIDE_IN_AT_LEAST_ONE_DONOR_NO_WITHIN_DONOR_GUIDE_VARIANCE"
                if min(len(guides["D1"]), len(guides["D2"])) == 1 else
                "TWO_GUIDES_MIN_PER_DONOR"
                if min(len(guides["D1"]), len(guides["D2"])) == 2 else
                "AT_LEAST_THREE_GUIDES_EACH_DONOR"
            ),
        })
    result = {
        "schema": "GSE301119_GUIDE_DONOR_SUPPORT_AUDIT_V1",
        "evidence_role": ("SYNTHETIC_TEST_ONLY__NO_PHYSICAL_AUTHORITY" if test_fixture else "PHYSICAL_PRODUCER_METADATA_ONLY__NO_EXPRESSION_OR_DE_ANALYSIS"),
        "modality": modality,
        "input_sha256": observed_hash,
        "input_role": "PR77_SHA_BOUND_RAW_PSEUDOBULK_GUIDE_DONOR_METADATA",
        "guide_donor_rows": len(rows),
        "cells_total": all_cells,
        "role_rows": roles,
        "perturbed_targets": len(targets),
        "both_donor_targets": sum(
            t["guides_D1"] >= 1 and t["guides_D2"] >= 1 for t in targets
        ),
        "at_least_two_guides_per_donor": sum(
            t["guides_D1"] >= 2 and t["guides_D2"] >= 2 for t in targets
        ),
        "at_least_three_guides_per_donor": sum(
            t["guides_D1"] >= 3 and t["guides_D2"] >= 3 for t in targets
        ),
        "nt_controls": {
            d: {"guides": len(control_guides[d]), "cells": control_cells[d]}
            for d in sorted(DONORS)
        },
        "targets": targets,
        "statistical_claim": "DESCRIPTIVE_REPLICATION_SUPPORT_ONLY__N_BIOLOGICAL_DONORS_2",
        "de_results_executed": False,
        "physical_counts_reaggregated_here": False,
        "jepa_training_authorized": False,
    }
    if not test_fixture:
        result["report_sha256"] = hashlib.sha256(json.dumps(
            result, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")).hexdigest()
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit("output exists: immutable evidence may not be overwritten")
    data = {
        "schema": "GSE301119_GUIDE_DONOR_SUPPORT_AUDIT_COMBINED_V1",
        "modalities": {
            mod: census(
                args.evidence_dir / f"{mod}_guide_donor_meta.csv",
                modality=mod,
            ) for mod in ("CRISPRa", "CRISPRi")
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
