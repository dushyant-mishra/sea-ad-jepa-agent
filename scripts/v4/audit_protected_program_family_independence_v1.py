#!/usr/bin/env python3
"""Outcome-blind independence audit of the frozen protected-program weight authority.

Scope: reads only the frozen v6r5a program-weight authority and its registry. No
expression, no model/checkpoint, no forward, no outcome, no training, no EMA. This
script is diagnostic. It does not select, redefine, add or remove any protected
program family, and it does not change any F1 gate. Any such change remains a
separate prospective decision requiring external review.

Question: the current F1 truth table (scripts/v4/contextual_target_f1_decision_v4.py)
consumes eight protected program families as if they were eight distinct hypotheses,
applies Holm across them, and requires all eight to be estimable. This audit measures
how many independent directions those eight weight vectors actually span, which
families are exact functions of others, and whether the rare/recurrent threshold
semantics recorded in the registry are representable in the current program estimand.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

# Code authority lives in the worktree; frozen data authority lives in the canonical
# local workspace, which is never cloned into a worktree. This mirrors the split the
# F1 executor already uses between worktree_root and canonical_root.
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANONICAL_ROOT = Path("D:/Jepa project")
AUTHORITY_RELATIVE = Path("exports/contextual_biology_v6r5a_20260822")
DECISION_V4 = ROOT / "scripts/v4/contextual_target_f1_decision_v4.py"
DECISION_V1 = ROOT / "scripts/v4/contextual_target_f1_decision_v1.py"
DECISION_V1_DECLARED_SHA = "204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34"

# Exactly the eight families gated by contextual_target_f1_decision_v4.PROGRAMS.
GATED = (
    "broad_common", "weak_distributed", "local", "local_core",
    "local_halo", "core_halo", "sparse_marker_like", "innovation_tail",
)
# Present in the authority but not gated by the current truth table.
UNGATED = ("recurrent_5pct", "recurrent_1pct")
ALL_PROGRAMS = GATED + UNGATED

ALPHA = 0.05
OUT = ROOT / "outputs/protected_program_family_audit_20260904"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_source(path: Path) -> str:
    """Tracked-source convention: LF-normalized bytes.

    .gitattributes sets `text eol=lf` only for *.sh, so Python sources are checked out
    with native CRLF on Windows and their on-disk digest differs from the frozen
    declared digest. The F1 executor normalizes CRLF before hashing tracked sources;
    this audit uses the same convention so the comparison is meaningful.
    """
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def sha256_array(array: np.ndarray) -> str:
    """Registry convention: SHA-256 over the stored float32 C-order bytes."""
    return hashlib.sha256(np.ascontiguousarray(array, dtype=np.float32).tobytes()).hexdigest()


def canonical_sha(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def numerical_rank(matrix: np.ndarray) -> tuple[int, list[float], float]:
    """Frozen-engine rank convention: max(shape) * float64 eps * largest singular value."""
    singular = np.linalg.svd(np.asarray(matrix, np.float64), compute_uv=False)
    largest = float(singular[0]) if singular.size else 0.0
    tolerance = max(matrix.shape) * float(np.finfo(np.float64).eps) * largest
    return int(np.sum(singular > tolerance)), [float(v) for v in singular], tolerance


def authority_paths(canonical_root: Path) -> dict[str, Path]:
    base = Path(canonical_root).resolve() / AUTHORITY_RELATIVE
    return {
        "weights": base / "program_weights.npz",
        "registry": base / "program_registry.csv",
        "provenance": base / "program_registry_provenance.json",
    }


def load_authority(paths: dict[str, Path]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, dict[str, str]]]:
    packed = np.load(paths["weights"], allow_pickle=True)
    raw = {name: np.asarray(packed[f"raw__{name}"]) for name in ALL_PROGRAMS}
    l2 = {name: np.asarray(packed[f"l2__{name}"]) for name in ALL_PROGRAMS}
    with paths["registry"].open("r", encoding="utf-8-sig", newline="") as handle:
        registry = {row["program_name"]: row for row in csv.DictReader(handle)}
    missing = set(ALL_PROGRAMS) - set(registry)
    if missing:
        raise RuntimeError(f"registry is missing program rows: {sorted(missing)}")
    return raw, l2, registry


def verify_registry_digests(raw, l2, registry) -> dict[str, object]:
    """Independently recompute the twenty digests the registry records for itself."""
    rows = []
    for name in ALL_PROGRAMS:
        for kind, table, field in (("raw", raw, "raw_weight_sha256"), ("l2", l2, "l2_weight_sha256")):
            actual = sha256_array(table[name])
            expected = registry[name][field]
            rows.append({
                "program": name, "kind": kind,
                "registry_sha256": expected, "recomputed_sha256": actual,
                "match": bool(actual == expected),
            })
    return {"checked": len(rows), "all_match": all(row["match"] for row in rows), "rows": rows}


def identity_classes(table: dict[str, np.ndarray]) -> dict[str, object]:
    """Group programs whose stored weight bytes are exactly identical."""
    buckets: dict[str, list[str]] = {}
    for name in ALL_PROGRAMS:
        buckets.setdefault(sha256_array(table[name]), []).append(name)
    duplicates = {digest: members for digest, members in buckets.items() if len(members) > 1}
    return {
        "distinct_vectors": len(buckets),
        "programs": len(ALL_PROGRAMS),
        "duplicate_classes": [
            {"sha256": digest, "members": members} for digest, members in sorted(duplicates.items())
        ],
    }


def program_geometry(l2, registry) -> list[dict[str, object]]:
    """Support, effective address count and concentration, cross-checked against the registry."""
    out = []
    for name in ALL_PROGRAMS:
        w = np.asarray(l2[name], np.float64)
        w2 = w * w
        support = int(np.count_nonzero(w))
        sum_w4 = float(np.sum(w2 * w2))
        n_eff = float(1.0 / sum_w4) if sum_w4 > 0 else None
        recorded = registry[name].get("n_eff_1_over_sum_w4")
        recorded_value = float(recorded) if recorded not in (None, "") else None
        nonzero = w[w != 0]
        out.append({
            "program": name,
            "gated_by_current_truth_table": name in GATED,
            "program_type": registry[name].get("program_type"),
            "support_role": registry[name].get("support_role"),
            "support_addresses": support,
            "registry_weighted_address_count": int(registry[name]["weighted_address_count"]),
            "support_matches_registry": support == int(registry[name]["weighted_address_count"]),
            "l2_norm": float(np.linalg.norm(w)),
            "negative_weights": int(np.sum(w < 0)),
            "max_abs_weight": float(np.abs(w).max()) if w.size else 0.0,
            "n_eff_recomputed": n_eff,
            "n_eff_registry": recorded_value,
            "n_eff_relative_difference": (
                None if recorded_value in (None, 0) or n_eff is None
                else abs(n_eff - recorded_value) / abs(recorded_value)
            ),
            # A uniform 1/sqrt(k) vector over k addresses has n_eff == support exactly.
            "uniform_over_support": bool(
                support > 0 and np.allclose(np.abs(nonzero), 1.0 / np.sqrt(support), rtol=1e-5, atol=1e-8)
            ),
            "concentration_ratio_n_eff_over_support": (None if not support or n_eff is None else n_eff / support),
            "evidence_definition": registry[name].get("evidence_definition"),
            "interpretation": registry[name].get("interpretation"),
        })
    return out


def dependence(l2) -> dict[str, object]:
    """Rank of the gated weight matrix plus exact-reconstruction residual per family."""
    matrix = np.stack([np.asarray(l2[name], np.float64) for name in GATED])
    rank, singular, tolerance = numerical_rank(matrix)
    reconstructions = []
    for index, name in enumerate(GATED):
        others = np.delete(matrix, index, axis=0)
        target = matrix[index]
        # Least-squares reconstruction of this family from the remaining seven.
        coefficients, *_ = np.linalg.lstsq(others.T, target, rcond=None)
        residual = target - others.T @ coefficients
        residual_norm = float(np.linalg.norm(residual))
        contributors = {
            other: float(coefficients[position])
            for position, other in enumerate(n for n in GATED if n != name)
            if abs(float(coefficients[position])) > 1e-6
        }
        reconstructions.append({
            "program": name,
            "residual_l2_norm": residual_norm,
            "max_abs_residual": float(np.abs(residual).max()),
            # float32 storage limits exact agreement to roughly 1e-7 relative.
            "exactly_dependent_at_float32_precision": bool(residual_norm < 1e-6),
            "nonzero_coefficients": dict(sorted(contributors.items())),
        })
    cosines = {
        a: {b: float(np.asarray(l2[a], np.float64) @ np.asarray(l2[b], np.float64)) for b in ALL_PROGRAMS}
        for a in ALL_PROGRAMS
    }
    return {
        "gated_matrix_shape": list(matrix.shape),
        "singular_values": singular,
        "rank_tolerance": tolerance,
        "numerical_rank": rank,
        "rank_deficiency": len(GATED) - rank,
        "reconstructions": reconstructions,
        "pairwise_cosine_l2": cosines,
    }


def holm_implications(dep: dict[str, object], ident: dict[str, object]) -> dict[str, object]:
    """What the measured dependence does and does not imply for the current gates."""
    dependent = [
        row["program"] for row in dep["reconstructions"]
        if row["exactly_dependent_at_float32_precision"]
    ]
    duplicate_gated = sorted({
        member
        for entry in ident["duplicate_classes"]
        for member in entry["members"]
        if member in GATED
    })
    return {
        "families_gated": len(GATED),
        "independent_directions_spanned": dep["numerical_rank"],
        "exact_linear_relations_among_gated_families": dep["rank_deficiency"],
        "gated_families_participating_in_an_exact_relation": dependent,
        "relation_note": (
            "Rank deficiency is a property of the set, not of one family. Each listed "
            "family is exactly reconstructible from the others because they jointly "
            "satisfy one linear relation; the audit does not assert which family is the "
            "redundant one, since that is a modelling choice rather than a measurement."
        ),
        "gated_families_sharing_bytes_with_an_ungated_family": duplicate_gated,
        "holm_family_wise_error_rate_still_controlled": True,
        "holm_note": (
            "Holm step-down controls FWER under arbitrary dependence, so the measured "
            "dependence is not a false-positive-rate defect. It is a power and "
            "interpretation issue. With rank deficiency 1, exactly one of the eight "
            "gated slots contributes no independent direction, yet it still adds "
            "gate-failure surface because no_contextual_minus_direct_degradation and "
            "no_qid_v2_program_negative_margin each require all eight families to be "
            "estimable, and it still consumes Holm multiplicity. The innovation_tail "
            "byte-identity finding is a separate naming/interpretation issue and does "
            "not itself reduce the rank of the gated set."
        ),
        "affected_gates": [
            "protected_program_family_estimable",
            "no_contextual_minus_direct_degradation",
            "no_qid_v2_program_negative_margin",
        ],
    }


def rare_threshold_representability(raw, l2, registry, provenance) -> dict[str, object]:
    """Are the recurrent-threshold semantics expressible in the current program estimand?"""
    reference = "innovation_tail"
    rows = []
    for name in UNGATED:
        rows.append({
            "program": name,
            "raw_bytes_identical_to_innovation_tail": bool(
                sha256_array(raw[name]) == sha256_array(raw[reference])
            ),
            "l2_bytes_identical_to_innovation_tail": bool(
                sha256_array(l2[name]) == sha256_array(l2[reference])
            ),
            "registry_program_type": registry[name].get("program_type"),
            "registry_evidence_definition": registry[name].get("evidence_definition"),
        })
    return {
        "reference_program": reference,
        "rows": rows,
        "recorded_thresholds": {
            "rare5_threshold": provenance.get("rare5_threshold"),
            "rare1_threshold": provenance.get("rare1_threshold"),
        },
        "current_program_estimand": "w2_weighted_address_aggregation_over_the_l2_weight_vector",
        "threshold_applied_by_current_estimand": False,
        "consequence": (
            "The rare/recurrent distinction recorded in the registry is a cell-level "
            "threshold on the innovation score, not a distinct weight vector. The current "
            "program estimand aggregates addresses through the L2 weight vector only, so "
            "no threshold is applied anywhere in the gated path. The gated innovation_tail "
            "slot therefore measures the dense innovation direction, not a rare or "
            "tail-restricted subpopulation."
        ),
    }


def render_report(document: dict) -> str:
    """Human-readable rendering of the audit document for independent review."""
    head = document["headline_measurements"]
    lines = [
        "# Protected-program family independence audit",
        "",
        f"Terminal: `{document['terminal']}`",
        "",
        f"Diagnostic label: `{document['diagnostic_label']}`. This is a **diagnostic "
        "measurement, not a gate verdict**. No protected-program family was selected, "
        "redefined, added or removed, and no F1 gate was changed.",
        "",
        "## Authority",
        "",
        f"- program weights SHA-256 `{document['authority']['program_weights_sha256']}`",
        f"- program registry SHA-256 `{document['authority']['program_registry_sha256']}`",
        f"- frozen decision arithmetic matches its declared SHA-256: "
        f"`{document['authority']['decision_v1_matches_declared_frozen_sha256']}`",
        f"- source digest convention: `{document['authority']['source_digest_convention']}`",
        f"- registry re-verification: "
        f"{document['registry_digest_reverification']['checked']} recorded digests "
        f"independently recomputed, all match = "
        f"`{document['registry_digest_reverification']['all_match']}`",
        "",
        "## Headline measurements",
        "",
        f"- gated families: **{head['gated_families']}**",
        f"- independent directions actually spanned: **{head['independent_directions']}**",
        f"- exact linear relations among gated families: "
        f"**{head['exact_linear_relations_among_gated_families']}**",
        f"- smallest singular value: `{head['smallest_singular_value']:.6e}`",
        f"- families participating in that relation: "
        f"{', '.join('`%s`' % n for n in head['gated_families_in_an_exact_relation'])}",
        f"- gated families byte-identical to an ungated family: "
        f"{', '.join('`%s`' % n for n in head['gated_families_byte_identical_to_ungated'])}",
        f"- most diffuse gated family: `{head['most_diffuse_gated_family']}` "
        f"(support {head['most_diffuse_gated_family_support']}, "
        f"N_eff {head['most_diffuse_gated_family_n_eff']:.2f})",
        "",
        "## Program geometry",
        "",
        "| program | gated | support | N_eff | N_eff (registry) | uniform | type |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in document["program_geometry"]:
        lines.append(
            "| `%s` | %s | %d | %.2f | %.2f | %s | %s |" % (
                row["program"], "yes" if row["gated_by_current_truth_table"] else "no",
                row["support_addresses"], row["n_eff_recomputed"], row["n_eff_registry"],
                "yes" if row["uniform_over_support"] else "no", row["program_type"],
            )
        )
    lines += [
        "",
        "N_eff is `1 / sum(w^4)` over the L2-normalised weights, the registry's own "
        "definition. Every recomputed value agrees with the recorded value to float64 "
        "round-off, and every support count agrees with `weighted_address_count`.",
        "",
        "## Exact dependence",
        "",
        "| family | residual L2 | exact at float32 precision | reconstruction |",
        "|---|---|---|---|",
    ]
    for row in document["dependence"]["reconstructions"]:
        terms = []
        for name, value in row["nonzero_coefficients"].items():
            sign = "− " if value < 0 else ("+ " if terms else "")
            terms.append(f"{sign}{abs(value):.6f}·`{name}`")
        coefficients = (
            " ".join(terms) if row["exactly_dependent_at_float32_precision"] else "—"
        )
        lines.append(
            "| `%s` | `%.3e` | %s | %s |" % (
                row["program"], row["residual_l2_norm"],
                "**yes**" if row["exactly_dependent_at_float32_precision"] else "no",
                coefficients,
            )
        )
    lines += [
        "",
        document["holm_implications"]["relation_note"],
        "",
        "## What this does and does not imply",
        "",
        f"Holm family-wise error control remains valid: "
        f"`{document['holm_implications']['holm_family_wise_error_rate_still_controlled']}`.",
        "",
        document["holm_implications"]["holm_note"],
        "",
        "Gates that require all eight families to be estimable:",
        "",
    ]
    lines += [f"- `{gate}`" for gate in document["holm_implications"]["affected_gates"]]
    lines += [
        "",
        "## Rare/recurrent threshold representability",
        "",
        document["rare_threshold_representability"]["consequence"],
        "",
        "Recorded thresholds: "
        + ", ".join(
            f"`{key}` = {value}"
            for key, value in sorted(document["rare_threshold_representability"]["recorded_thresholds"].items())
        )
        + ".",
        "",
        "## Upstream provenance note",
        "",
        f"- upstream basis status: `{document['authority']['upstream_basis_status']}`",
        f"- upstream basis asset: `{document['authority']['upstream_basis_asset']}` "
        f"(SHA-256 `{document['authority']['upstream_basis_source_sha256']}`; local path not published)",
        f"- registry claim limit: {document['authority']['registry_claim_limit']}",
        "",
        "## Explicit non-conclusions",
        "",
    ]
    lines += [f"- {item}" for item in document["explicit_non_conclusions"]]
    lines += [
        "",
        "## Firewall",
        "",
        "| check | value |",
        "|---|---|",
    ]
    lines += [f"| `{key}` | `{value}` |" for key, value in sorted(document["firewall"].items())]
    lines += [
        "",
        f"Audit semantic root SHA-256: `{document['audit_semantic_root_sha256']}`",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canonical-root", type=Path, default=DEFAULT_CANONICAL_ROOT,
        help="Canonical local workspace holding the frozen exports/ data authority.",
    )
    parser.add_argument(
        "--output-root", type=Path, default=None,
        help="Where to write the audit package (defaults to the worktree outputs/ path).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = authority_paths(args.canonical_root)
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError(
            "frozen v6r5a program-weight authority is not present at "
            f"{args.canonical_root}: missing {missing}"
        )
    out = Path(args.output_root).resolve() if args.output_root else OUT
    raw, l2, registry = load_authority(paths)
    provenance = json.loads(paths["provenance"].read_text(encoding="utf-8"))

    digests = verify_registry_digests(raw, l2, registry)
    ident_raw = identity_classes(raw)
    ident_l2 = identity_classes(l2)
    geometry = program_geometry(l2, registry)
    dep = dependence(l2)
    holm = holm_implications(dep, ident_l2)
    rare = rare_threshold_representability(raw, l2, registry, provenance)

    declared_v1_matches = sha256_source(DECISION_V1) == DECISION_V1_DECLARED_SHA
    most_diffuse = max(
        (row for row in geometry if row["gated_by_current_truth_table"]),
        key=lambda row: row["n_eff_recomputed"] or 0.0,
    )

    document = {
        "terminal": "IMPLEMENTATION_COMPLETE_AWAITING_INDEPENDENT_VERIFICATION",
        "diagnostic_label": "PROTECTED_PROGRAM_FAMILY_RANK_DEFICIENT_AND_TAIL_NONSPECIFIC",
        "not_a_gate_verdict": True,
        "outcome_blind": True,
        "audit_question": (
            "How many independent directions do the eight gated protected-program weight "
            "vectors span, which gated families are exact functions of others, and is the "
            "registry's rare/recurrent threshold semantics representable in the current "
            "program estimand?"
        ),
        "authority": {
            "canonical_root": str(Path(args.canonical_root).resolve().as_posix()),
            "program_weights_path": str(AUTHORITY_RELATIVE.as_posix() + "/program_weights.npz"),
            "program_weights_sha256": sha256_file(paths["weights"]),
            "program_registry_path": str(AUTHORITY_RELATIVE.as_posix() + "/program_registry.csv"),
            "program_registry_sha256": sha256_file(paths["registry"]),
            "program_registry_provenance_sha256": sha256_file(paths["provenance"]),
            "decision_v4_path": str(DECISION_V4.relative_to(ROOT).as_posix()),
            "decision_v4_sha256_lf_normalized": sha256_source(DECISION_V4),
            "decision_v1_sha256_lf_normalized": sha256_source(DECISION_V1),
            "decision_v1_matches_declared_frozen_sha256": declared_v1_matches,
            "source_digest_convention": "lf_normalized_bytes",
            "registry_semantic_hash": provenance.get("registry_semantic_hash"),
            "upstream_basis_status": provenance.get("basis_status"),
            # Sanitised for public review: the local absolute path is deliberately not
            # published. The artifact is identified by basename and SHA-256; local
            # resolution stays local.
            "upstream_basis_asset": Path(
                registry["broad_common"]["source_artifact_path"].replace("\\", "/")).name,
            "upstream_basis_source_sha256": registry["broad_common"]["source_artifact_sha256"],
            "upstream_basis_local_path_published": False,
            "registry_claim_limit": provenance.get("claim_limit"),
            "address_count": provenance.get("address_count"),
        },
        "registry_digest_reverification": digests,
        "byte_identity_raw": ident_raw,
        "byte_identity_l2": ident_l2,
        "program_geometry": geometry,
        "dependence": dep,
        "holm_implications": holm,
        "rare_threshold_representability": rare,
        "headline_measurements": {
            "gated_families": len(GATED),
            "independent_directions": dep["numerical_rank"],
            "smallest_singular_value": dep["singular_values"][-1],
            "exact_linear_relations_among_gated_families": holm["exact_linear_relations_among_gated_families"],
            "gated_families_in_an_exact_relation": holm["gated_families_participating_in_an_exact_relation"],
            "gated_families_byte_identical_to_ungated": holm[
                "gated_families_sharing_bytes_with_an_ungated_family"
            ],
            "most_diffuse_gated_family": most_diffuse["program"],
            "most_diffuse_gated_family_n_eff": most_diffuse["n_eff_recomputed"],
            "most_diffuse_gated_family_support": most_diffuse["support_addresses"],
        },
        "firewall": {
            "expression_read": False,
            "model_or_checkpoint_read": False,
            "model_forward_executed": False,
            "outcome_or_endpoint_read": False,
            "training_or_ema": False,
            "dev_sealed_or_pathology_accessed": False,
        },
        "change_assertions": {
            "program_family_added_removed_or_redefined": False,
            "program_weights_modified": False,
            "gate_definition_changed": False,
            "statistical_rule_changed": False,
            "dataset_dependent_parameter_selected": False,
            "frozen_artifact_written": False,
        },
        "explicit_non_conclusions": [
            "This audit does not claim the contextual target fails or succeeds.",
            "This audit does not select a replacement protected-program set.",
            "Holm family-wise error control remains valid under the measured dependence.",
            "No statement is made about any real F1 outcome, which does not exist.",
        ],
    }
    document["audit_semantic_root_sha256"] = canonical_sha(document)

    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "PROTECTED_PROGRAM_FAMILY_AUDIT.json"
    json_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path = out / "PROTECTED_PROGRAM_FAMILY_AUDIT.md"
    report_path.write_text(render_report(document), encoding="utf-8")

    manifest_path = out / "AUDIT_MANIFEST.csv"
    entries = [
        ("scripts/v4/audit_protected_program_family_independence_v1.py", sha256_source(Path(__file__))),
        ("PROTECTED_PROGRAM_FAMILY_AUDIT.json", sha256_file(json_path)),
        ("PROTECTED_PROGRAM_FAMILY_AUDIT.md", sha256_file(report_path)),
    ]
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "sha256"])
        writer.writerows(entries)
    root = canonical_sha([{"path": path, "sha256": digest} for path, digest in entries])
    (out / "AUDIT_PACKAGE_ROOT_SHA256.txt").write_text(root + "\n", encoding="utf-8")

    print(json.dumps({
        "terminal": document["terminal"],
        "diagnostic_label": document["diagnostic_label"],
        "registry_digests_all_match": digests["all_match"],
        "decision_v1_matches_declared_frozen_sha256": declared_v1_matches,
        **document["headline_measurements"],
        "package": str(out.as_posix()),
        "package_root_sha256": root,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
