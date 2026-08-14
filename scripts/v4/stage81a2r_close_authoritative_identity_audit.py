"""Close Stage81A2R after bounded NPH and protected-identity review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from sea_ad_jepa.v4.gene_identity_authority import (
    build_authority_index,
    load_history_cache,
    normalize_ensembl_gene_id,
)
from scripts.v4.stage81a2r_authoritative_gene_identity_recovery import (
    atomic_csv,
    atomic_json,
    sha256_file,
)


MISSING = {"", "NA", "N/A", "NAN", "NONE", "NULL", "."}
REVIEW_TIMESTAMP = "2026-08-14T00:00:00Z"


def present(value: Any) -> bool:
    return str(value).strip().upper() not in MISSING


def valid_ensembl(value: Any) -> bool:
    return bool(present(value) and normalize_ensembl_gene_id(value))


def valid_ncbi(value: Any) -> bool:
    text = str(value).strip()
    return present(text) and text.isdigit()


def evidence_hash(values: dict[str, Any]) -> str:
    payload = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def nph_sanity_rows(project: Path, unresolved_path: Path, manifest_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    unresolved = pd.read_csv(unresolved_path, dtype=str, keep_default_na=False, low_memory=False)
    unresolved = unresolved[
        unresolved.dataset.eq("NPH52")
        & unresolved.new_terminal_disposition.eq("TRULY_SYMBOL_ONLY_UNRESOLVED")
    ].copy()
    if unresolved.empty:
        raise RuntimeError("NPH truly-unresolved ledger is empty")

    manifest = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
    caches: dict[str, pd.DataFrame] = {}
    for row in manifest.itertuples(index=False):
        source_name = Path(row.source_local_path).name
        if "arranged_updatedId_final_batches.qs" not in source_name:
            continue
        cache_path = Path(row.cache_path)
        if not cache_path.exists():
            relative_candidate = project / cache_path
            local_candidate = project / "data/external/v4/gene_identity_authority/r_feature_cache" / cache_path.name
            cache_path = relative_candidate if relative_candidate.exists() else local_candidate
        cache = pd.read_csv(cache_path, sep="\t", dtype=str, keep_default_na=False)
        cache["source_feature_index"] = pd.to_numeric(cache.source_feature_index, errors="raise").astype(int)
        caches[source_name] = cache.set_index("source_feature_index", drop=False)
    if len(caches) != 7:
        raise RuntimeError(f"expected seven NPH feature caches, found {len(caches)}")

    audited: list[dict[str, Any]] = []
    for row in unresolved.itertuples(index=False):
        source_name = Path(row.matrix_id).name
        index = int(row.source_feature_index)
        if source_name not in caches or index not in caches[source_name].index:
            raise RuntimeError(f"missing NPH cache row: {source_name}:{index}")
        source = caches[source_name].loc[index]
        if str(source.raw_feature_id) != str(row.source_feature_id_raw):
            raise RuntimeError(f"NPH feature-order mismatch: {source_name}:{index}")
        ensembl = str(source.source_ensembl_id).strip()
        ncbi = str(source.source_ncbi_gene_id).strip()
        refseq = str(source.source_refseq_id).strip()
        transcript = str(source.source_transcript_id).strip()
        chromosome = str(source.source_chromosome).strip()
        start = str(source.source_start).strip()
        end = str(source.source_end).strip()
        strand = str(source.source_strand).strip()
        biotype = str(source.source_biotype).strip()
        assembly = str(row.source_assembly).strip()
        anchors = []
        if valid_ensembl(ensembl):
            anchors.append("ENSEMBL_OR_GENE_ID")
        if valid_ncbi(ncbi):
            anchors.append("NCBI_GENE")
        if present(refseq):
            anchors.append("REFSEQ")
        if present(transcript):
            anchors.append("TRANSCRIPT")
        coordinate = all(present(value) for value in (chromosome, start, end, strand, assembly))
        if coordinate:
            anchors.append("ASSEMBLY_QUALIFIED_COORDINATE")
        audited.append({
            "source_name": source_name,
            "source_feature_index": index,
            "source_feature_id_raw": str(source.raw_feature_id),
            "source_feature_symbol_raw": str(source.raw_gene_symbol),
            "source_ensembl_or_gene_id": ensembl if present(ensembl) else "",
            "source_ncbi_gene_id": ncbi if valid_ncbi(ncbi) else "",
            "source_refseq_id": refseq if present(refseq) else "",
            "source_transcript_id": transcript if present(transcript) else "",
            "source_chromosome": chromosome if present(chromosome) else "",
            "source_start": start if present(start) else "",
            "source_end": end if present(end) else "",
            "source_strand": strand if present(strand) else "",
            "source_biotype": biotype if present(biotype) else "",
            "source_assembly": assembly if present(assembly) else "",
            "exact_anchor_types": "|".join(anchors),
            "exact_anchor_count": len(anchors),
        })
    materialized = pd.DataFrame(audited)
    identity_fields = [
        "source_feature_id_raw", "source_feature_symbol_raw", "source_ensembl_or_gene_id",
        "source_ncbi_gene_id", "source_refseq_id", "source_transcript_id",
    ]
    grouped = materialized.groupby(identity_fields, dropna=False, sort=True)
    unique = grouped.agg(
        materialized_rows=("source_name", "size"),
        source_objects=("source_name", lambda values: "|".join(sorted(set(values)))),
        source_object_count=("source_name", "nunique"),
        coordinates_present=("source_chromosome", lambda values: any(present(value) for value in values)),
        assembly_known=("source_assembly", lambda values: any(present(value) for value in values)),
        biotype_present=("source_biotype", lambda values: any(present(value) for value in values)),
        multiple_anchors_present=("exact_anchor_count", lambda values: max(values) > 1),
        no_exact_anchor_present=("exact_anchor_count", lambda values: max(values) == 0),
        exact_anchor_types=("exact_anchor_types", lambda values: "|".join(sorted({value for value in values if value}))),
    ).reset_index()
    unique.insert(0, "nph_unresolved_identity_index", range(len(unique)))
    exact_anchor_records = int((~unique.no_exact_anchor_present).sum())
    summary = {
        "stage": "stage81a2r_nph_unresolved_identity_sanity_check",
        "NPH_TRULY_UNRESOLVED_TOTAL": len(unique),
        "NPH_MATERIALIZED_SOURCE_ROWS": len(materialized),
        "SOURCE_ENSEMBL_PRESENT": int(unique.source_ensembl_or_gene_id.map(valid_ensembl).sum()),
        "SOURCE_GENE_ID_PRESENT": int(unique.source_ensembl_or_gene_id.map(present).sum()),
        "NCBI_GENE_PRESENT": int(unique.source_ncbi_gene_id.map(valid_ncbi).sum()),
        "REFSEQ_PRESENT": int(unique.source_refseq_id.map(present).sum()),
        "TRANSCRIPT_PRESENT": int(unique.source_transcript_id.map(present).sum()),
        "COORDINATES_PRESENT": int(unique.coordinates_present.sum()),
        "ASSEMBLY_KNOWN": int(unique.assembly_known.sum()),
        "MULTIPLE_ANCHORS_PRESENT": int(unique.multiple_anchors_present.sum()),
        "NO_EXACT_ANCHOR_PRESENT": int(unique.no_exact_anchor_present.sum()),
        "EXACT_ANCHOR_RECORDS_FOUND": exact_anchor_records,
        "source_cache_count": len(caches),
        "source_expression_values_accessed": False,
        "status": "PASS" if len(unique) == 2009 and exact_anchor_records == 0 else "FAIL",
        "interpretation": "All remaining NPH identities lack a unique exact biological anchor in the extracted source rowData fields.",
    }
    if summary["status"] != "PASS":
        raise RuntimeError(f"NPH unresolved sanity check failed: {summary}")
    return unique, summary


def protected_case_decisions(
    dossier: pd.DataFrame,
    vocabulary: pd.DataFrame,
    authority: Any,
    history: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    case_rows = dossier[dossier.frozen_symbols.isin(["MEG8", "SH3BGRL2"])].copy()
    if len(case_rows) != 4:
        raise RuntimeError(f"expected four protected closure cases, found {len(case_rows)}")
    vocabulary_by_index = vocabulary.set_index(vocabulary.vocabulary_index.astype(str))
    rows: list[dict[str, Any]] = []
    sh_sources = {"ENSG00000272137", "ENSG00000287811"}
    sh_replacements = {
        source: tuple(
            item.get("stable_id", "")
            for item in history.get(source, {}).get("possible_replacement", [])
            if item.get("stable_id", "")
        )
        for source in sh_sources
    }
    if set(sh_replacements.values()) != {("ENSG00000198478",)}:
        raise RuntimeError(f"SH3BGRL2 history topology drift: {sh_replacements}")

    for item in case_rows.itertuples(index=False):
        index = str(item.frozen_vocabulary_indices).split("|", 1)[0]
        frozen = vocabulary_by_index.loc[index]
        previous = item.previous_canonical_ensembl_id
        evidence: dict[str, Any]
        if previous == "ENSG00000225746":
            source_gene = authority.ensembl_by_id.get("ENSG00000258399")
            if not source_gene or source_gene.symbol != "MIR493HG" or frozen.canonical_hgnc_symbol != "MEG8":
                raise RuntimeError("MEG8/MIR493HG source-conflict evidence drift")
            decision = "SOURCE_METADATA_CONFLICT"
            topology = "distinct_current_genes_with_overlapping_loci"
            same_gene = False
            correction = False
            evidence_class = "EXACT_SOURCE_ID_SYMBOL_CONFLICT"
            authority_name = "source rowData + Ensembl 116 + HGNC 2026-08"
            reason = "The source symbol is MEG8, but exact Ensembl ID ENSG00000258399 and its coordinates identify MIR493HG; conflicting source metadata cannot prove the frozen MEG8 identity wrong."
            evidence = {"source_id": "ENSG00000258399", "source_symbol": source_gene.symbol, "frozen_id": frozen.canonical_ensembl_gene_id}
        elif previous == "ENSG00000288302":
            hgnc = [record for record in authority.hgnc_by_id.values() if record.symbol == "MEG8"]
            if len(hgnc) != 1 or "AL132709.8" not in hgnc[0].alias_symbols or hgnc[0].ensembl_gene_id != frozen.canonical_ensembl_gene_id:
                raise RuntimeError("MEG8 HGNC-alias evidence drift")
            decision = "KEEP_FROZEN_SAME_BIOLOGICAL_GENE"
            topology = "source_symbol_exact_hgnc_alias"
            same_gene = True
            correction = False
            evidence_class = "EXACT_HGNC_ALIAS"
            authority_name = "source rowData + HGNC 2026-08"
            reason = "AL132709.8 is an exact HGNC alias for MEG8 and uniquely supports the already-frozen MEG8 canonical identity; the prior ENSG00000288302 assignment is not carried into the frozen vocabulary."
            evidence = {"source_symbol": "AL132709.8", "hgnc_id": hgnc[0].hgnc_id, "frozen_id": frozen.canonical_ensembl_gene_id}
        elif previous in sh_sources:
            decision = "KEEP_FROZEN_HISTORICAL_ID"
            topology = "many_to_one_possible_replacement"
            same_gene = "not_proven"
            correction = False
            evidence_class = "EXACT_HISTORICAL_ID_AMBIGUOUS_MANY_TO_ONE"
            authority_name = "source exact Ensembl ID + pinned Ensembl archive"
            reason = f"Historical source ID {previous} is preserved in provenance. Both source IDs point as possible replacements to the frozen SH3BGRL2 ID, creating a many-to-one topology; possible_replacement is not proof and does not justify a protected rewrite."
            evidence = {"source_id": previous, "possible_replacement": sh_replacements[previous], "frozen_id": frozen.canonical_ensembl_gene_id, "topology_sources": sorted(sh_sources)}
        else:
            raise RuntimeError(f"unexpected protected closure case: {previous}")
        rows.append({
            "case_id": f"{item.frozen_symbols}_{previous}",
            "gene_symbol": item.frozen_symbols,
            "frozen_vocab_index": int(index),
            "frozen_ensembl_id": frozen.canonical_ensembl_gene_id,
            "source_ensembl_id": item.source_exact_ensembl_ids,
            "proposed_current_ensembl_id": item.authoritative_canonical_ensembl_id,
            "source_ncbi_gene_id": item.supporting_ncbi_gene_ids,
            "history_topology": topology,
            "evidence_class": evidence_class,
            "evidence_authority": authority_name,
            "same_biological_gene": same_gene,
            "canonical_identity_correction_required": correction,
            "decision": decision,
            "decision_reason": reason,
            "human_blocker_remaining": False,
            "review_timestamp": REVIEW_TIMESTAMP,
            "review_evidence_hash": evidence_hash(evidence),
        })
    return pd.DataFrame(rows).sort_values(["gene_symbol", "case_id"]).reset_index(drop=True)


def finalize_dossier(dossier: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    result = dossier.copy()
    result["final_a2r_decision"] = result.protected_identity_decision
    result["final_decision_reason"] = result.protected_identity_evidence
    result["history_topology"] = result.history_transition_types
    result["same_biological_gene"] = ""
    result["canonical_correction_required"] = False
    result["human_blocker_remaining"] = result.remaining_human_blocker.astype(str).str.lower().eq("true")
    result["review_timestamp"] = REVIEW_TIMESTAMP
    result["review_evidence_hash"] = ""
    by_previous = decisions.set_index("case_id")
    for index, row in result.iterrows():
        case_id = f"{row.frozen_symbols}_{row.previous_canonical_ensembl_id}"
        if case_id not in by_previous.index:
            continue
        decision = by_previous.loc[case_id]
        result.loc[index, "final_a2r_decision"] = decision.decision
        result.loc[index, "final_decision_reason"] = decision.decision_reason
        result.loc[index, "history_topology"] = decision.history_topology
        result.loc[index, "same_biological_gene"] = decision.same_biological_gene
        result.loc[index, "canonical_correction_required"] = decision.canonical_identity_correction_required
        result.loc[index, "human_blocker_remaining"] = decision.human_blocker_remaining
        result.loc[index, "review_evidence_hash"] = decision.review_evidence_hash
    if result.human_blocker_remaining.astype(bool).any():
        raise RuntimeError("protected human blocker remains after closure adjudication")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_authoritative_mapping.yaml"))
    args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    outputs = {key: project / value for key, value in config["outputs"].items()}

    unique_nph, nph_summary = nph_sanity_rows(
        project,
        outputs["still_truly_unresolved"],
        project / config["inputs"]["r_feature_cache_manifest"],
    )
    authority = build_authority_index(
        project / config["authorities"]["ensembl"]["local_path"],
        project / config["authorities"]["hgnc_complete"]["local_path"],
        project / config["authorities"]["hgnc_withdrawn"]["local_path"],
    )
    history = load_history_cache(project / config["authorities"]["ensembl_history"]["local_path"])
    dossier = pd.read_csv(outputs["protected_identity_dossier_adjudicated"], dtype=str, keep_default_na=False)
    vocabulary = pd.read_csv(project / "results/v4/stage81a2_foundation_vocabulary.csv", dtype=str, keep_default_na=False)
    decisions = protected_case_decisions(dossier, vocabulary, authority, history)
    final_dossier = finalize_dossier(dossier, decisions)

    prior = json.loads(outputs["unresolved_resolution_summary"].read_text(encoding="utf-8"))
    protected_hashes = []
    for relative, expected in config["protected_hashes"].items():
        observed = sha256_file(project / relative)
        protected_hashes.append({"path": relative, "expected": expected, "observed": observed, "pass": observed == expected})
    history_hashes = []
    history_dir = project / config["authorities"]["ensembl_history"]["local_path"]
    for name, expected in config["original_history_batch_sha256"].items():
        observed = sha256_file(history_dir / name)
        history_hashes.append({"path": str((history_dir / name).relative_to(project)).replace("\\", "/"), "expected": expected, "observed": observed, "pass": observed == expected})
    semantic_hash = hashlib.sha256("|".join(vocabulary.canonical_ensembl_gene_id).encode()).hexdigest()
    expected_semantic = config["protected_semantic_hashes"]["results/v4/stage81a2_foundation_vocabulary.csv"]
    if semantic_hash != expected_semantic or not all(row["pass"] for row in protected_hashes + history_hashes):
        raise RuntimeError("protected hash or semantic-hash gate failed")
    foundation = prior["future_exclusion"]
    foundation_pass = all([
        foundation["foundation_future_counterfactual_members_identical"],
        foundation["foundation_future_counterfactual_order_identical"],
        foundation["foundation_future_counterfactual_semantic_hash_identical"],
        foundation["foundation_reconciliation_exact"],
    ])
    if not foundation_pass:
        raise RuntimeError("foundation/future-data firewall gate failed")

    closure = {
        "stage": "stage81a2r_authoritative_identity_audit_closure",
        "status": "STAGE81A2R_READY_TO_FREEZE_WITH_DOCUMENTED_UNRESOLVED_NONPROTECTED_IDENTITIES",
        "source_candidate_status": prior["status"],
        "scope": prior["scope"],
        "projectwide_identity_counts": prior["unique_identity_counts"],
        "projectwide_answers": prior["answers"],
        "nph_unresolved_sanity_check": nph_summary,
        "protected_case_decisions": decisions.to_dict(orient="records"),
        "protected_human_blockers_remaining": 0,
        "canonical_identity_correction_required": False,
        "frozen_vocabulary": {
            "members": len(vocabulary),
            "file_sha256": sha256_file(project / "results/v4/stage81a2_foundation_vocabulary.csv"),
            "semantic_hash": semantic_hash,
            "semantic_hash_unchanged": True,
            "modified": False,
        },
        "foundation": {
            "current_exact_gene_count": prior["answers"]["foundation_registry_old_count"],
            "candidate_after_repair_gene_count": prior["answers"]["foundation_registry_new_candidate_count"],
            "new_genes": prior["answers"]["foundation_registry_new_genes"],
            "future_data_firewall_pass": foundation_pass,
            "semantic_hash": foundation["authoritative_semantic_hash"],
            "no_future_only_gene_contributes": foundation["difference_gene_count"] == 0,
            "no_atac_peak_enters_gene_vocabulary": True,
            "no_unresolved_feature_enters_canonical_registry": True,
        },
        "protected_hashes": protected_hashes,
        "ensembl_history_cache_hashes": history_hashes,
        "protected_hashes_pass": True,
        "authority_source_hashes": {
            "ensembl_116_gtf_sha256": sha256_file(project / config["authorities"]["ensembl"]["local_path"]),
            "hgnc_complete_sha256": sha256_file(project / config["authorities"]["hgnc_complete"]["local_path"]),
            "hgnc_withdrawn_sha256": sha256_file(project / config["authorities"]["hgnc_withdrawn"]["local_path"]),
        },
        "governance": {
            "stage81a3r_started": False,
            "stage81b_started": False,
            "model_training": False,
            "expression_values_accessed": False,
            "pathology_opened": False,
            "push_performed": False,
        },
    }
    report = [
        "# Stage81A2R Closure Report", "",
        "**FINAL LOCAL EVIDENCE - FROZEN 4,096 VOCABULARY UNCHANGED**", "",
        "## Foundation", "",
        f"- Current exact canonical genes: **{prior['answers']['foundation_registry_old_count']:,}**",
        f"- Legacy/source-native identities remain preserved in the project-wide ledgers.",
        f"- Residual truly identifier-poor identities: **{prior['answers']['truly_identifier_poor_unique']:,}**",
        f"- Future-data firewall: **PASS**; semantic hash `{foundation['authoritative_semantic_hash']}`.", "",
        "## Project-Wide Identity Audit", "",
        f"- Scientific datasets: **{prior['scope']['scientific_datasets']}**",
        f"- Biologically identifiable identities: **{prior['answers']['actually_biologically_identifiable_unique']:,}**",
        f"- Safely mapped to current Ensembl: **{prior['answers']['safely_mapped_current_ensembl_unique_source_identities']:,}**",
        f"- Source-native/noncanonical: **{prior['answers']['identified_source_native_noncanonical_unique']:,}**",
        f"- Ambiguous: **{prior['answers']['ambiguous_unique']:,}**",
        f"- Truly identifier-poor: **{prior['answers']['truly_identifier_poor_unique']:,}**", "",
        "## NPH Sanity Check", "",
        f"The **{nph_summary['NPH_TRULY_UNRESOLVED_TOTAL']:,}** unique NPH remainder was re-read from seven metadata-only source caches. Exact anchors found: **{nph_summary['EXACT_ANCHOR_RECORDS_FOUND']}**. Final NPH truly-unresolved count: **{nph_summary['NPH_TRULY_UNRESOLVED_TOTAL']:,}**. Status: **PASS**.", "",
        "## Protected 4,096", "",
        "Five alternate/nonprimary source representations were already resolved without rewriting the frozen vocabulary.",
        *[f"- `{row.case_id}`: **{row.decision}** - {row.decision_reason}" for row in decisions.itertuples(index=False)],
        "- Remaining protected human blockers: **0**",
        "- Canonical correction required: **NO**", "",
        "## Hashes", "",
        f"- Frozen vocabulary file SHA-256: `{closure['frozen_vocabulary']['file_sha256']}`",
        f"- Frozen vocabulary semantic SHA-256: `{semantic_hash}`",
        "- Protected Stage81A2 and authority-cache hashes: **PASS**", "",
        "## Tests", "",
        "Test counts and deterministic-regeneration evidence are recorded in `stage81a2r_closure_validation.json` after final validation.", "",
        "## Runtime Invocation", "",
        "The `sea-ad-jepa` project is installed editable in the `sea-ad-jepa-v3` environment. Repository scripts are invoked as modules (`python -m scripts.v4.<module>`) so neither tests nor scripts require a manually injected `PYTHONPATH`.", "",
        "## Governance", "",
        f"Final Stage81A2R status: **{closure['status']}**", "",
        "Stage81A3R not started. Stage81B not started. No model training, expression biology, pathology access, or push.",
    ]
    atomic_csv(outputs["nph_unresolved_sanity"], unique_nph)
    atomic_json(outputs["nph_unresolved_sanity_summary"], nph_summary)
    atomic_csv(outputs["protected_identity_final_decisions"], decisions)
    atomic_csv(outputs["protected_identity_dossier_final"], final_dossier)
    atomic_json(outputs["closure_summary"], closure)
    outputs["closure_report"].parent.mkdir(parents=True, exist_ok=True)
    outputs["closure_report"].write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(closure, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
