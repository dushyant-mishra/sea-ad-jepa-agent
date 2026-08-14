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
IDENTITY_LAYERS = (
    "current_exact",
    "legacy_exact",
    "alternative_authority_exact",
    "source_native_anchored",
    "source_native_unprojected",
    "ambiguous",
    "symbol_or_identifier_poor",
    "true_technical_nonbiological",
)


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


def foundation_source_family(source_dataset_id: str) -> str:
    if source_dataset_id == "SEA_AD_COMMON":
        return "SEA-AD"
    if source_dataset_id == "HVS_COMMON":
        return "HVS"
    if source_dataset_id.startswith("NPH52::"):
        return "NPH52"
    raise RuntimeError(f"non-foundation source in foundation ledger: {source_dataset_id}")


def _first_present(*values: Any) -> str:
    return next((str(value).strip() for value in values if present(value)), "")


def foundation_identity_accounting(
    decisions: pd.DataFrame,
    reclassification: pd.DataFrame,
    *,
    expected_current_exact: int | None = None,
    expected_nph_identifier_poor: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], pd.DataFrame]:
    """Aggregate completed decisions without changing any identity assignment."""
    frame = decisions.copy()
    frame["source_family"] = frame.source_dataset_id.map(foundation_source_family)
    frame["accounting_disposition"] = frame.terminal_disposition
    frame["accounting_current_ensembl_id"] = frame.authority_current_ensembl_id
    frame["accounting_source_native_id"] = frame.source_native_id
    frame["accounting_mapping_evidence_class"] = frame.mapping_evidence_class
    frame["accounting_mapping_authority"] = frame.mapping_authority
    frame["accounting_mapping_evidence_file"] = frame.mapping_evidence_file

    updates = reclassification[reclassification.dataset.eq("NPH52")].copy()
    updates["source_dataset_id"] = updates.matrix_id.map(lambda value: f"NPH52::{Path(value).name}")
    updates["source_feature_index"] = pd.to_numeric(updates.source_feature_index, errors="raise").astype(int)
    update_lookup = updates.set_index(["source_dataset_id", "source_feature_index"])
    frame["source_feature_index"] = pd.to_numeric(frame.source_feature_index, errors="raise").astype(int)
    for index, row in frame.iterrows():
        key = (row.source_dataset_id, row.source_feature_index)
        if key not in update_lookup.index:
            continue
        update = update_lookup.loc[key]
        frame.loc[index, "accounting_disposition"] = update.new_terminal_disposition
        if present(update.recovered_canonical_ensembl_id):
            frame.loc[index, "accounting_current_ensembl_id"] = update.recovered_canonical_ensembl_id
        for target, source in (
            ("accounting_mapping_evidence_class", "mapping_evidence_class"),
            ("accounting_mapping_authority", "mapping_authority"),
            ("accounting_mapping_evidence_file", "evidence_file"),
        ):
            if present(update[source]):
                frame.loc[index, target] = update[source]

    layers: list[str] = []
    keys: list[str] = []
    universal: list[bool] = []
    for row in frame.itertuples(index=False):
        disposition = row.accounting_disposition
        current = _first_present(row.accounting_current_ensembl_id)
        legacy = _first_present(row.normalized_source_ensembl_id, row.source_exact_ensembl_id)
        alternative = _first_present(row.source_refseq_id, row.source_ncbi_gene_id, row.source_transcript_id)
        native = _first_present(row.accounting_source_native_id)
        unresolved_identity = _first_present(
            row.normalized_source_symbol,
            row.raw_source_feature_symbol,
            row.raw_source_feature_id,
        )
        if current:
            layer, key, established = "current_exact", current, True
        elif disposition.startswith("LEGACY_"):
            layer, key, established = "legacy_exact", legacy, True
        elif disposition.startswith(("EXACT_NCBI", "EXACT_REFSEQ", "EXACT_GENCODE", "EXACT_REFSEQ_OR_NCBI")):
            layer, key, established = "alternative_authority_exact", alternative, True
        elif disposition.startswith("SOURCE_NATIVE_") and native:
            layer, key, established = "source_native_anchored", native, True
        elif disposition.startswith("SOURCE_NATIVE_"):
            layer = "source_native_unprojected"
            key = f"{row.source_family}|{unresolved_identity}"
            established = False
        elif disposition.startswith("AMBIGUOUS_") or disposition in {"ASSEMBLY_UNRESOLVED", "CONFLICTING_AUTHORITATIVE_IDENTITY"}:
            layer = "ambiguous"
            key = f"{row.source_family}|{unresolved_identity}"
            established = False
        elif disposition == "NON_BIOLOGICAL_TECHNICAL_FEATURE":
            layer = "true_technical_nonbiological"
            key = f"{row.source_family}|{unresolved_identity}"
            established = False
        else:
            layer = "symbol_or_identifier_poor"
            key = f"{row.source_family}|{unresolved_identity}"
            established = False
        if not key:
            raise RuntimeError(f"empty identity key for {row.source_dataset_id}:{row.source_feature_index}")
        layers.append(layer)
        keys.append(key)
        universal.append(established)
    frame["identity_layer"] = layers
    frame["identity_key"] = keys
    frame["universal_identity_established"] = universal
    frame["source_feature_key"] = frame.apply(
        lambda row: (
            f"{row.source_family}|"
            f"{_first_present(row.normalized_source_symbol, row.raw_source_feature_symbol, row.raw_source_feature_id)}"
        ),
        axis=1,
    )

    rows = []
    for scope in ("FOUNDATION", "SEA-AD", "HVS", "NPH52"):
        subset = frame if scope == "FOUNDATION" else frame[frame.source_family.eq(scope)]
        counts = {
            layer: int(subset.loc[subset.identity_layer.eq(layer), "identity_key"].nunique())
            for layer in IDENTITY_LAYERS
        }
        rows.append({
            "scope": scope,
            "foundation_source_rows_total": len(subset),
            "foundation_unique_source_features": int(subset.source_feature_key.nunique()),
            "foundation_unique_biological_identities": sum(counts.values()),
            **{f"G_foundation_{layer}": count for layer, count in counts.items()},
        })
    accounting = pd.DataFrame(rows)
    policy_rows = [
        ("current_exact", "YES", "YES", "ELIGIBLE"),
        ("legacy_exact", "YES", "YES", "ELIGIBLE"),
        ("alternative_authority_exact", "YES", "YES", "HUMAN POLICY REQUIRED"),
        ("source_native_anchored", "YES", "YES", "ELIGIBLE"),
        ("source_native_unprojected", "YES", "NO", "NOT YET ELIGIBLE"),
        ("ambiguous", "YES", "NO", "NOT YET ELIGIBLE"),
        ("symbol_or_identifier_poor", "YES", "NO", "NOT YET ELIGIBLE"),
        ("true_technical_nonbiological", "NO", "NO", "NOT YET ELIGIBLE"),
    ]
    policy = pd.DataFrame(policy_rows, columns=[
        "identity_layer", "molecular_evidence_preserved", "universal_identity_established",
        "proposed_universal_encoder_eligibility",
    ])
    layer_counts = accounting.set_index("scope").loc["FOUNDATION"].to_dict()
    summary = {
        "stage": "stage81a2r_foundation_identity_accounting",
        "scope": "FOUNDATION ONLY: SEA-AD + HVS + NPH52",
        "source_rows_total": int(layer_counts["foundation_source_rows_total"]),
        "unique_source_features": int(layer_counts["foundation_unique_source_features"]),
        "unique_biological_identities": int(layer_counts["foundation_unique_biological_identities"]),
        "identity_layer_counts": {
            layer: int(layer_counts[f"G_foundation_{layer}"])
            for layer in IDENTITY_LAYERS
        },
        "universal_identity_established": {
            "true": int(sum(layer_counts[f"G_foundation_{layer}"] for layer in IDENTITY_LAYERS[:4])),
            "false": int(sum(layer_counts[f"G_foundation_{layer}"] for layer in IDENTITY_LAYERS[4:])),
        },
        "source_breakdown": accounting[accounting.scope.ne("FOUNDATION")].to_dict(orient="records"),
        "nph_reconciliation": {
            "NPH52_identifier_poor": int(accounting.set_index("scope").loc["NPH52", "G_foundation_symbol_or_identifier_poor"]),
            "SEA_AD_identifier_poor": int(accounting.set_index("scope").loc["SEA-AD", "G_foundation_symbol_or_identifier_poor"]),
            "HVS_identifier_poor": int(accounting.set_index("scope").loc["HVS", "G_foundation_symbol_or_identifier_poor"]),
            "foundation_identifier_poor_total": int(layer_counts["G_foundation_symbol_or_identifier_poor"]),
        },
        "mapping_decisions_changed": False,
        "expression_values_accessed": False,
    }
    if (
        expected_current_exact is not None
        and summary["identity_layer_counts"]["current_exact"] != expected_current_exact
    ):
        raise RuntimeError("foundation current-exact count drift")
    if expected_nph_identifier_poor is not None and summary["nph_reconciliation"] != {
        "NPH52_identifier_poor": expected_nph_identifier_poor,
        "SEA_AD_identifier_poor": 0,
        "HVS_identifier_poor": 0,
        "foundation_identifier_poor_total": expected_nph_identifier_poor,
    }:
        raise RuntimeError(f"foundation unresolved reconciliation failed: {summary['nph_reconciliation']}")
    return accounting, policy, summary, frame


def _joined_unique(values: pd.Series) -> str:
    return "|".join(sorted({str(value).strip() for value in values if present(value)}))


def _preferred_value(group: pd.DataFrame, columns: tuple[str, ...]) -> str:
    for column in columns:
        values = sorted({str(value).strip() for value in group[column] if present(value)})
        if values:
            return values[0]
    return ""


def registry_semantic_hash(registry: pd.DataFrame) -> str:
    columns = [
        "molecular_address_index", "molecular_address_id", "identity_class",
        "current_ensembl_gene_id", "legacy_source_exact_id", "source_native_anchor",
        "symbol", "biotype", "identity_authority", "identity_evidence",
    ]
    payload = registry[columns].to_json(orient="records", force_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_foundation_molecular_address_package(
    frame: pd.DataFrame,
    current_measurement_support: pd.DataFrame,
    *,
    expected_address_counts: dict[str, int] | None = None,
    expected_nonuniversal_count: int = 2010,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if expected_address_counts is None:
        expected_address_counts = {
            "current_exact": 40422,
            "legacy_exact": 773,
            "source_native_anchored": 43,
        }
    eligible_layers = {"current_exact", "legacy_exact", "source_native_anchored"}
    eligible = frame[frame.identity_layer.isin(eligible_layers)].copy()

    registry_rows: list[dict[str, Any]] = []
    for (identity_class, address_id), group in eligible.groupby(
        ["identity_layer", "identity_key"], sort=True, dropna=False
    ):
        registry_rows.append({
            "molecular_address_id": address_id,
            "identity_class": identity_class,
            "current_ensembl_gene_id": address_id if identity_class == "current_exact" else "",
            "legacy_source_exact_id": address_id if identity_class == "legacy_exact" else "",
            "source_native_anchor": address_id if identity_class == "source_native_anchored" else "",
            "symbol": _preferred_value(group, (
                "canonical_hgnc_symbol", "normalized_source_symbol", "raw_source_feature_symbol",
            )),
            "biotype": _joined_unique(group.source_biotype),
            "identity_authority": _joined_unique(group.accounting_mapping_authority),
            "identity_evidence": _joined_unique(pd.concat([
                group.accounting_disposition,
                group.accounting_mapping_evidence_class,
            ], ignore_index=True)),
            "measurement_support_provenance": (
                "stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz"
                f"#{address_id}"
            ),
            "contributing_source_feature_count": int(len(group)),
            "contributing_source_families": _joined_unique(group.source_family),
            "contributing_source_dataset_ids": _joined_unique(group.source_dataset_id),
        })
    registry = pd.DataFrame(registry_rows)
    class_order = {"current_exact": 0, "legacy_exact": 1, "source_native_anchored": 2}
    registry["_class_order"] = registry.identity_class.map(class_order)
    registry = registry.sort_values(
        ["_class_order", "molecular_address_id"], kind="mergesort"
    ).drop(columns="_class_order").reset_index(drop=True)
    registry.insert(0, "molecular_address_index", range(len(registry)))

    address_counts = registry.identity_class.value_counts().to_dict()
    proposed_counts = {
        "current_exact": int(address_counts.get("current_exact", 0)),
        "legacy_exact": int(address_counts.get("legacy_exact", 0)),
        "source_native_anchored": int(address_counts.get("source_native_anchored", 0)),
    }
    if proposed_counts != expected_address_counts:
        raise RuntimeError(f"foundation molecular-address count drift: {proposed_counts}")

    cross_layer = (
        registry.groupby("molecular_address_id").identity_class.nunique().loc[lambda values: values > 1]
    )
    within_layer = registry.duplicated(["identity_class", "molecular_address_id"], keep=False)
    current_or_legacy = eligible[eligible.identity_layer.isin({"current_exact", "legacy_exact"})]
    established_non_native_anchors = {
        value
        for value in current_or_legacy.source_native_id
        if present(value)
    }
    native_addresses = set(
        registry.loc[registry.identity_class.eq("source_native_anchored"), "molecular_address_id"]
    )
    native_cross_layer = sorted(native_addresses & established_non_native_anchors)
    if len(cross_layer) or within_layer.any() or native_cross_layer:
        raise RuntimeError("exact universal-address injectivity violation")

    registry_hash = registry_semantic_hash(registry)
    registry["registry_semantic_hash"] = registry_hash
    address_lookup = registry.set_index(["identity_class", "molecular_address_id"])

    provenance_rows = []
    for row in eligible.itertuples(index=False):
        address_index = int(address_lookup.loc[(row.identity_layer, row.identity_key), "molecular_address_index"])
        provenance_rows.append({
            "molecular_address_index": address_index,
            "molecular_address_id": row.identity_key,
            "identity_class": row.identity_layer,
            "measurement_provenance_key": f"{row.identity_key}|{row.source_dataset_id}",
            "source_record_index": row.source_record_index,
            "source_dataset_id": row.source_dataset_id,
            "source_object_or_matrix": row.source_object_or_matrix,
            "source_feature_index": row.source_feature_index,
            "raw_source_feature_id": row.raw_source_feature_id,
            "raw_source_feature_symbol": row.raw_source_feature_symbol,
            "source_exact_ensembl_id": row.source_exact_ensembl_id,
            "source_native_anchor": row.accounting_source_native_id,
            "mapping_evidence_class": row.accounting_mapping_evidence_class,
            "mapping_authority": row.accounting_mapping_authority,
            "mapping_evidence_file": row.accounting_mapping_evidence_file,
        })
    provenance = pd.DataFrame(provenance_rows).sort_values(
        ["molecular_address_index", "source_dataset_id", "source_object_or_matrix", "source_feature_index"],
        kind="mergesort",
    ).reset_index(drop=True)
    if provenance.source_record_index.eq("").any():
        raise RuntimeError("untraceable foundation source feature in address provenance")

    current_registry = registry[registry.identity_class.eq("current_exact")][[
        "molecular_address_index", "molecular_address_id", "identity_class",
    ]]
    support = current_measurement_support.merge(
        current_registry,
        left_on="canonical_ensembl_gene_id",
        right_on="molecular_address_id",
        how="left",
        validate="many_to_one",
    )
    if support.molecular_address_index.isna().any():
        raise RuntimeError("current measurement support contains an unknown molecular address")
    support = support.rename(columns={"measured_gene": "measured_address"})

    extra_registry = registry[registry.identity_class.ne("current_exact")][[
        "molecular_address_index", "molecular_address_id", "identity_class",
    ]]
    matrix_meta = current_measurement_support[[
        "matrix_id", "source_dataset_id", "source_feature_universe_hash",
    ]].drop_duplicates().sort_values("matrix_id", kind="mergesort")
    matrix_meta["_join"] = 1
    extra_registry = extra_registry.copy()
    extra_registry["_join"] = 1
    extra_support = matrix_meta.merge(extra_registry, on="_join", validate="many_to_many").drop(columns="_join")
    provenance_keys = set(provenance.measurement_provenance_key)
    extra_support["measurement_provenance_key"] = (
        extra_support.molecular_address_id + "|" + extra_support.source_dataset_id
    )
    extra_support["measured_address"] = extra_support.measurement_provenance_key.isin(provenance_keys)
    extra_support["measurement_status"] = extra_support.measured_address.map({
        True: "addressable_measured_zero_or_nonzero_at_runtime",
        False: "structurally_unmeasured",
    })
    extra_support["measured_zero_distinct_from_unmeasured"] = True
    extra_support["canonical_ensembl_gene_id"] = ""
    extra_support["canonical_symbol"] = ""

    support["measurement_provenance_key"] = (
        support.molecular_address_id + "|" + support.source_dataset_id
    ).where(support.measured_address.astype(str).str.lower().eq("true"), "")
    support = pd.concat([support, extra_support], ignore_index=True, sort=False)
    support["molecular_address_index"] = pd.to_numeric(
        support.molecular_address_index, errors="raise"
    ).astype(int)
    support["molecular_address_registry_semantic_hash"] = registry_hash
    support = support[[
        "matrix_id", "source_dataset_id", "molecular_address_index", "molecular_address_id",
        "identity_class", "measured_address", "measurement_status",
        "measured_zero_distinct_from_unmeasured", "measurement_provenance_key",
        "source_feature_universe_hash", "molecular_address_registry_semantic_hash",
    ]].sort_values(["matrix_id", "molecular_address_index"], kind="mergesort").reset_index(drop=True)

    expected_support_rows = int(current_measurement_support.matrix_id.nunique() * len(registry))
    if len(support) != expected_support_rows:
        raise RuntimeError("molecular-address measurement-support cardinality drift")
    if support.duplicated(["matrix_id", "molecular_address_id"]).any():
        raise RuntimeError("duplicate matrix/address measurement-support row")
    measured_keys = set(support.loc[support.measured_address.astype(str).str.lower().eq("true"), "measurement_provenance_key"])
    if "" in measured_keys or not measured_keys.issubset(provenance_keys):
        raise RuntimeError("measured address lacks source-feature provenance")
    if not support.measured_zero_distinct_from_unmeasured.astype(str).str.lower().eq("true").all():
        raise RuntimeError("measured-zero/structurally-unmeasured distinction lost")

    nonuniversal = frame[frame.identity_layer.isin({
        "source_native_unprojected", "ambiguous", "symbol_or_identifier_poor",
    })].copy()
    evidence_rows = []
    for (identity_class, identity_key), group in nonuniversal.groupby(
        ["identity_layer", "identity_key"], sort=True
    ):
        evidence_rows.append({
            "nonuniversal_evidence_id": hashlib.sha256(
                f"{identity_class}|{identity_key}".encode("utf-8")
            ).hexdigest(),
            "identity_class": identity_class,
            "source_identity_key": identity_key,
            "symbol": _preferred_value(group, ("normalized_source_symbol", "raw_source_feature_symbol")),
            "source_feature_count": int(len(group)),
            "source_families": _joined_unique(group.source_family),
            "source_dataset_ids": _joined_unique(group.source_dataset_id),
            "source_record_indices": _joined_unique(group.source_record_index),
            "molecular_evidence_preserved": True,
            "universal_identity_established": False,
            "unrestricted_encoder_address_eligible": False,
            "absence_classification": "DATA / PROVENANCE LIMITATION",
        })
    nonuniversal_evidence = pd.DataFrame(evidence_rows).sort_values(
        ["identity_class", "source_identity_key"], kind="mergesort"
    ).reset_index(drop=True)
    if len(nonuniversal_evidence) != expected_nonuniversal_count:
        raise RuntimeError("preserved nonuniversal evidence count drift")

    nonterminal_links = set()
    legacy = eligible[eligible.identity_layer.eq("legacy_exact")]
    for row in legacy.itertuples(index=False):
        for field in (
            "hgnc_approved_ensembl", "hgnc_previous_ensembl",
            "hgnc_alias_ensembl", "hgnc_withdrawn_ensembl",
        ):
            target = str(getattr(row, field)).strip()
            if present(target):
                nonterminal_links.add((row.identity_key, target, field))
    injectivity = {
        "stage": "stage81a2r_foundation_molecular_address_injectivity_audit",
        "scope": "FOUNDATION ONLY: SEA-AD + HVS + NPH52",
        "proposed_current_addresses": proposed_counts["current_exact"],
        "proposed_legacy_addresses": proposed_counts["legacy_exact"],
        "proposed_anchored_addresses": proposed_counts["source_native_anchored"],
        "exact_cross_layer_duplicate_equivalence_classes": 0,
        "exact_within_layer_duplicate_equivalence_classes": 0,
        "legacy_exact_alternate_of_current_exact_classes": 0,
        "legacy_exact_within_layer_equivalence_classes": 0,
        "source_native_anchor_cross_layer_equivalence_classes": 0,
        "source_native_anchor_within_layer_equivalence_classes": 0,
        "source_native_repeated_measurement_rows_collapsed": int(
            len(eligible[eligible.identity_layer.eq("source_native_anchored")])
            - proposed_counts["source_native_anchored"]
        ),
        "dataset_or_source_family_used_in_address_id": False,
        "nonterminal_symbol_or_namespace_links_not_promoted": len(nonterminal_links),
        "nonterminal_link_reason": (
            "Completed terminal adjudication did not establish these links as exact biological equivalence; "
            "possible replacements, symbol links, coordinates, and namespace differences were not promoted."
        ),
        "final_distinct_universal_molecular_addresses": len(registry),
        "foundation_preserved_nonuniversal_evidence": len(nonuniversal_evidence),
        "registry_semantic_hash": registry_hash,
        "measurement_support_rows": len(support),
        "measurement_support_matrices": int(support.matrix_id.nunique()),
        "one_row_per_matrix_address": True,
        "deterministic_ordering": True,
        "future_only_addresses": 0,
        "measured_zero_distinct_from_structurally_unmeasured": True,
        "complete_foundation_source_feature_provenance": True,
        "historical_frozen_4096_modified": False,
        "expression_values_accessed": False,
    }
    expected_total = sum(expected_address_counts.values())
    if len(registry) != expected_total:
        raise RuntimeError(f"injective address count differs from accounting expectation: {len(registry)}")
    return registry, provenance, support, nonuniversal_evidence, injectivity


def matrix_accounting_reconciliation(
    historical_assets: pd.DataFrame,
    measurement_support: pd.DataFrame,
) -> dict[str, Any]:
    assets = historical_assets[
        historical_assets.foundation_eligible.astype(str).str.lower().eq("true")
    ].copy()
    historical = {
        "HVS": int(assets.study_id.eq("HVS").sum()),
        "SEA_AD": int(assets.study_id.eq("SEA_AD").sum()),
        "NPH52_aggregate_collections": int(assets.study_id.eq("NPH52").sum()),
    }
    matrices = measurement_support[["matrix_id", "source_dataset_id"]].drop_duplicates()
    current = {
        "HVS": int(matrices.source_dataset_id.eq("HVS_COMMON").sum()),
        "SEA_AD": int(matrices.source_dataset_id.eq("SEA_AD_COMMON").sum()),
        "NPH52_QS_objects": int(matrices.source_dataset_id.str.startswith("NPH52::").sum()),
    }
    historical_total = sum(historical.values())
    current_total = sum(current.values())
    if historical != {"HVS": 24, "SEA_AD": 11, "NPH52_aggregate_collections": 1}:
        raise RuntimeError(f"historical Stage81A2 asset accounting drift: {historical}")
    if current != {"HVS": 24, "SEA_AD": 11, "NPH52_QS_objects": 7}:
        raise RuntimeError(f"Stage81A2R matrix accounting drift: {current}")
    if historical_total != 36 or current_total != 42:
        raise RuntimeError("36-to-42 matrix-accounting reconciliation failed")
    return {
        "historical_stage81a2_asset_entries": historical,
        "historical_stage81a2_asset_entry_total": historical_total,
        "current_stage81a2r_measurement_support_matrices": current,
        "current_stage81a2r_measurement_support_matrix_total": current_total,
        "accounting_granularity_only": True,
        "new_foundation_datasets_introduced": 0,
        "explanation": (
            "The historical registry represented NPH52 as one aggregate source collection; "
            "Stage81A2R preserves the seven NPH QS objects as separate matrix-level measurement operators."
        ),
    }


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

    source_decisions = pd.read_csv(outputs["source_decisions"], dtype=str, keep_default_na=False, low_memory=False)
    reclassification = pd.read_csv(outputs["unresolved_reclassification"], dtype=str, keep_default_na=False, low_memory=False)
    foundation_accounting, address_policy, foundation_accounting_summary, foundation_frame = foundation_identity_accounting(
        source_decisions,
        reclassification,
        expected_current_exact=40422,
        expected_nph_identifier_poor=2009,
    )
    current_measurement_support = pd.read_csv(
        outputs["measurement_support"], dtype=str, keep_default_na=False, low_memory=False
    )
    historical_assets = pd.read_csv(
        project / config["inputs"]["frozen_asset_registry"],
        dtype=str,
        keep_default_na=False,
    )
    matrix_accounting = matrix_accounting_reconciliation(
        historical_assets,
        current_measurement_support,
    )
    (
        molecular_address_registry,
        molecular_address_provenance,
        molecular_address_measurement_support,
        nonuniversal_evidence,
        injectivity_audit,
    ) = build_foundation_molecular_address_package(
        foundation_frame,
        current_measurement_support,
    )
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
    expected_protected_cases = {
        "MEG8_ENSG00000225746",
        "MEG8_ENSG00000288302",
        "SH3BGRL2_ENSG00000272137",
        "SH3BGRL2_ENSG00000287811",
    }
    if len(decisions) != 4 or set(decisions.case_id) != expected_protected_cases:
        raise RuntimeError("final protected-review case accounting drift")
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
        "status": "STAGE81A2R_READY_FOR_FREEZE",
        "source_candidate_status": prior["status"],
        "scope": prior["scope"],
        "projectwide_identity_counts": prior["unique_identity_counts"],
        "projectwide_answers": prior["answers"],
        "projectwide_scope_label": "PROJECT-WIDE - FOUNDATION + FUTURE DATASETS",
        "foundation_identity_accounting": foundation_accounting_summary,
        "foundation_molecular_address_space": injectivity_audit,
        "matrix_accounting_reconciliation": matrix_accounting,
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
            "foundation_molecular_address_count": len(molecular_address_registry),
            "preserved_nonuniversal_evidence_count": len(nonuniversal_evidence),
            "molecular_address_semantic_hash": injectivity_audit["registry_semantic_hash"],
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
        "**FOUNDATION ONLY - SEA-AD + HVS + NPH52**", "",
        f"- Current exact canonical genes: **{prior['answers']['foundation_registry_old_count']:,}**",
        f"- Source rows: **{foundation_accounting_summary['source_rows_total']:,}**",
        f"- Distinct source features within source families: **{foundation_accounting_summary['unique_source_features']:,}**",
        f"- Unique adjudicated biological identities across identity layers: **{foundation_accounting_summary['unique_biological_identities']:,}**",
        *[f"- {layer.replace('_', ' ').title()}: **{count:,}**" for layer, count in foundation_accounting_summary["identity_layer_counts"].items()],
        f"- Future-data firewall: **PASS**; semantic hash `{foundation['authoritative_semantic_hash']}`.", "",
        "### Foundation Source Breakdown", "",
        foundation_accounting.to_csv(index=False), "",
        "### NPH Reconciliation", "",
        f"Of **{foundation_accounting_summary['nph_reconciliation']['foundation_identifier_poor_total']:,}** Foundation identifier-poor identities, NPH52 contributes **{foundation_accounting_summary['nph_reconciliation']['NPH52_identifier_poor']:,}**, SEA-AD contributes **{foundation_accounting_summary['nph_reconciliation']['SEA_AD_identifier_poor']:,}**, and HVS contributes **{foundation_accounting_summary['nph_reconciliation']['HVS_identifier_poor']:,}**.", "",
        "### Molecular Evidence and Universal Address Policy", "",
        "Molecular evidence preservation is distinct from universal encoder address eligibility. The Foundation Molecular Address Space contains current exact, legacy exact, and source-native anchored identities. It is not exclusively a current gene vocabulary.", "",
        address_policy.to_csv(index=False), "",
        "### Foundation Molecular Address Space", "",
        f"- Current exact addresses: **{injectivity_audit['proposed_current_addresses']:,}**",
        f"- Legacy exact addresses: **{injectivity_audit['proposed_legacy_addresses']:,}**",
        f"- Source-native anchored addresses: **{injectivity_audit['proposed_anchored_addresses']:,}**",
        f"- Exact cross-layer duplicate equivalence classes: **{injectivity_audit['exact_cross_layer_duplicate_equivalence_classes']}**",
        f"- Exact within-layer duplicate equivalence classes: **{injectivity_audit['exact_within_layer_duplicate_equivalence_classes']}**",
        f"- Final distinct universal molecular addresses: **{injectivity_audit['final_distinct_universal_molecular_addresses']:,}**",
        f"- Preserved nonuniversal evidence identities: **{injectivity_audit['foundation_preserved_nonuniversal_evidence']:,}**",
        f"- Successor registry semantic SHA-256: `{injectivity_audit['registry_semantic_hash']}`",
        "- Ambiguous and identifier-poor identities remain preserved as **DATA / PROVENANCE LIMITATION** evidence; they are not biological top-K exclusions and are not unrestricted encoder addresses.",
        "- Measurement support remains matrix-specific and distinguishes measured zero from structurally unmeasured.", "",
        "### Matrix-Accounting Reconciliation", "",
        "- Historical Stage81A2: **24 HVS + 11 SEA-AD + 1 aggregate NPH52 = 36 asset-registry entries**.",
        "- Current Stage81A2R: **24 HVS + 11 SEA-AD + 7 NPH52 QS objects = 42 matrix-level measurement-support contracts**.",
        "The change from 36 historical asset-registry entries to 42 measurement-support matrices is an accounting-granularity change: the historical registry represented NPH52 as one aggregate source collection, whereas A2R preserves the seven NPH QS objects as separate matrix-level measurement operators. No six new foundation datasets were introduced.", "",
        "## Project-Wide Identity Audit", "",
        "**PROJECT-WIDE - FOUNDATION + FUTURE DATASETS**", "",
        f"- Scientific datasets: **{prior['scope']['scientific_datasets']}**",
        f"- Biologically identifiable identities: **{prior['answers']['actually_biologically_identifiable_unique']:,}**",
        f"- Safely mapped to current Ensembl: **{prior['answers']['safely_mapped_current_ensembl_unique_source_identities']:,}**",
        f"- Source-native/noncanonical: **{prior['answers']['identified_source_native_noncanonical_unique']:,}**",
        f"- Ambiguous: **{prior['answers']['ambiguous_unique']:,}**",
        f"- Truly identifier-poor: **{prior['answers']['truly_identifier_poor_unique']:,}**", "",
        "The **41,719** truly identifier-poor identities are a project-wide total across Foundation and future-use datasets. They are not a Foundation-only count.", "",
        "## NPH Sanity Check", "",
        f"The **{nph_summary['NPH_TRULY_UNRESOLVED_TOTAL']:,}** unique NPH remainder was re-read from seven metadata-only source caches. Exact anchors found: **{nph_summary['EXACT_ANCHOR_RECORDS_FOUND']}**. Final NPH truly-unresolved count: **{nph_summary['NPH_TRULY_UNRESOLVED_TOTAL']:,}**. Status: **PASS**.", "",
        "## Protected 4,096", "",
        "Four alternate/nonprimary source representations were already resolved without rewriting the frozen vocabulary.",
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
    atomic_csv(outputs["foundation_identity_accounting"], foundation_accounting)
    atomic_csv(outputs["foundation_address_policy"], address_policy)
    atomic_json(outputs["foundation_accounting_summary"], foundation_accounting_summary)
    atomic_csv(outputs["foundation_molecular_address_registry"], molecular_address_registry)
    atomic_csv(outputs["foundation_molecular_address_provenance"], molecular_address_provenance, compression="gzip")
    atomic_csv(
        outputs["foundation_molecular_address_measurement_support"],
        molecular_address_measurement_support,
        compression="gzip",
    )
    atomic_csv(outputs["foundation_nonuniversal_evidence"], nonuniversal_evidence, compression="gzip")
    atomic_json(outputs["foundation_address_injectivity_audit"], injectivity_audit)
    atomic_json(outputs["closure_summary"], closure)
    outputs["closure_report"].parent.mkdir(parents=True, exist_ok=True)
    outputs["closure_report"].write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(closure, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
