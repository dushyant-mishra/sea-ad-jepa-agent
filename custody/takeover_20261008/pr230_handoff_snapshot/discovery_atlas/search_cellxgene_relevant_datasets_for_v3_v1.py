"""Search CELLxGENE Census metadata for Graph-JEPA v3-relevant datasets.

Stage 26C is a metadata discovery/schema audit only. It inspects Census
dataset and obs metadata, ranks candidate public datasets for possible v3
integration roles, and never downloads expression matrices or H5AD payloads.
"""

from __future__ import annotations

import importlib
import traceback
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

CANDIDATES_OUT = TABLE_DIR / "v3_cellxgene_relevant_dataset_candidates_v1.csv"
ROLES_OUT = TABLE_DIR / "v3_cellxgene_dataset_role_assignment_v1.csv"
REPORT_OUT = REPORT_DIR / "v3_cellxgene_relevant_dataset_search_v1.md"

TISSUE_TERMS = [
    "brain",
    "cerebral cortex",
    "prefrontal cortex",
    "frontal cortex",
    "temporal cortex",
    "entorhinal cortex",
    "hippocampus",
    "central nervous system",
]

CELL_TYPE_TERMS = [
    "microglial cell",
    "central nervous system macrophage",
    "macrophage",
    "monocyte",
    "astrocyte",
    "neuron",
    "oligodendrocyte",
    "oligodendrocyte precursor cell",
    "endothelial cell",
    "pericyte",
]

DISEASE_TERMS = [
    "Alzheimer disease",
    "dementia",
    "normal",
    "control",
    "Parkinson disease",
    "multiple sclerosis",
    "neurodegenerative disease",
]

QUERY_DISEASE_TERMS = [
    "Alzheimer disease",
    "dementia",
    "Parkinson disease",
    "multiple sclerosis",
    "neurodegenerative disease",
]

MICROGLIA_TERMS = {"microglial cell", "central nervous system macrophage"}
NEURO_SUPPORT_TERMS = {
    "astrocyte",
    "neuron",
    "oligodendrocyte",
    "oligodendrocyte precursor cell",
}
PERIPHERAL_TERMS = {"macrophage", "monocyte"}
ALREADY_USED_MARKERS = {
    "GSE174367",
    "GSE138852",
    "SEA-AD",
    "Seattle Alzheimer",
    "Rexach",
    "Cross-dementia human brain",
    "Olah",
    "Leng",
    "Grubman",
    "selectively vulnerable neurons",
}
ALREADY_USED_COLLECTION_IDS = {
    # Primary discovery/training atlas; never a clean external holdout.
    "1ca90a2d-2943-483d-b678-b809bf464c30",
    # Leng/Grubman/GSE138852 historical smoke-test/plausibility collection.
    "180bff9c-c8a5-4539-b13b-ddbc00d643e6",
    # Rexach cross-dementia was adapted in v2.2 alignment context.
    "c53573b2-eff4-4c5e-9ad0-b24d422dfd9b",
}

CANDIDATE_COLUMNS = [
    "dataset_id",
    "collection_id",
    "collection_name",
    "dataset_title",
    "organism",
    "dataset_total_cell_count",
    "matched_cell_count",
    "n_donors_or_samples",
    "n_microglia_or_cns_macrophage_cells",
    "tissue_terms",
    "disease_terms",
    "cell_type_terms",
    "has_ad_or_dementia",
    "has_control_or_normal",
    "has_brain_or_cns",
    "has_microglia_or_cns_macrophage",
    "has_donor_metadata",
    "dataset_h5ad_path",
    "relevance_score",
    "recommended_role",
    "download_recommendation",
    "notes",
]

ROLE_COLUMNS = [
    "dataset_id",
    "collection_name",
    "dataset_title",
    "organism",
    "recommended_role",
    "allowed_for_training",
    "allowed_for_pretraining",
    "allowed_for_auxiliary_supervision",
    "reserved_for_external_holdout",
    "allowed_for_model_selection",
    "risk_if_used_for_training",
    "rationale",
    "notes",
]


def norm(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def lower_set(values: Iterable[object]) -> set[str]:
    return {norm(v).lower() for v in values if norm(v)}


def joined(values: Iterable[object]) -> str:
    cleaned = sorted({norm(v) for v in values if norm(v)})
    return "; ".join(cleaned)


def contains_any(text: str, markers: Iterable[str]) -> bool:
    text_upper = text.upper()
    return any(marker.upper() in text_upper for marker in markers)


def get_first(row: pd.Series, columns: Iterable[str], default: object = "") -> object:
    for col in columns:
        if col in row.index and not pd.isna(row[col]):
            return row[col]
    return default


def sql_list(values: Iterable[str]) -> str:
    escaped = [v.replace("'", "\\'") for v in values]
    return "[" + ", ".join(f"'{v}'" for v in escaped) + "]"


def write_outputs(candidates: pd.DataFrame, roles: pd.DataFrame, report: str) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    candidates.reindex(columns=CANDIDATE_COLUMNS).to_csv(CANDIDATES_OUT, index=False)
    roles.reindex(columns=ROLE_COLUMNS).to_csv(ROLES_OUT, index=False)
    REPORT_OUT.write_text(report, encoding="utf-8")


def write_unavailable_outputs(reason: str, details: str = "") -> None:
    note = reason if not details else f"{reason}: {details}"
    candidates = pd.DataFrame(
        [
            {
                "dataset_id": "cellxgene_census_unavailable",
                "collection_id": "",
                "collection_name": "CELLxGENE Census unavailable",
                "dataset_title": "CELLxGENE Census metadata search not completed",
                "organism": "unknown",
                "dataset_total_cell_count": 0,
                "matched_cell_count": 0,
                "n_donors_or_samples": 0,
                "n_microglia_or_cns_macrophage_cells": 0,
                "tissue_terms": "",
                "disease_terms": "",
                "cell_type_terms": "",
                "has_ad_or_dementia": False,
                "has_control_or_normal": False,
                "has_brain_or_cns": False,
                "has_microglia_or_cns_macrophage": False,
                "has_donor_metadata": False,
                "dataset_h5ad_path": "",
                "relevance_score": -10,
                "recommended_role": "do_not_use_until_reviewed",
                "download_recommendation": "install/repair cellxgene-census and rerun metadata search; do not download matrices yet",
                "notes": note,
            }
        ]
    )
    roles = pd.DataFrame(
        [
            {
                "dataset_id": "cellxgene_census_unavailable",
                "collection_name": "CELLxGENE Census unavailable",
                "dataset_title": "CELLxGENE Census metadata search not completed",
                "organism": "unknown",
                "recommended_role": "do_not_use_until_reviewed",
                "allowed_for_training": False,
                "allowed_for_pretraining": False,
                "allowed_for_auxiliary_supervision": False,
                "reserved_for_external_holdout": False,
                "allowed_for_model_selection": False,
                "risk_if_used_for_training": "No Census metadata audit was completed.",
                "rationale": note,
                "notes": "This placeholder row prevents silent failure and preserves auditability.",
            }
        ]
    )
    report = "\n".join(
        [
            "# v3 CELLxGENE relevant dataset search v1",
            "",
            "## 1. Executive summary",
            "",
            f"CELLxGENE Census metadata search was not completed: {note}",
            "No v3 training, graph neural model, external validation, model selection, or evidence-level change was run.",
            "",
            "## 2. Search method",
            "",
            "The script attempted to import/open `cellxgene-census`. Because this failed, no CELLxGENE metadata query was performed.",
            "",
            "## 3. Best human AD/dementia brain candidates",
            "",
            "Unavailable until the Census metadata search succeeds.",
            "",
            "## 4. Best human normal brain/microglia pretraining candidates",
            "",
            "Unavailable until the Census metadata search succeeds.",
            "",
            "## 5. Mouse auxiliary candidates",
            "",
            "Unavailable until the Census metadata search succeeds.",
            "",
            "## 6. Peripheral immune candidates",
            "",
            "Unavailable until the Census metadata search succeeds.",
            "",
            "## 7. Datasets to avoid or review",
            "",
            "All CELLxGENE datasets should remain unreviewed until metadata discovery is rerun successfully.",
            "",
            "## 8. Recommended downloads",
            "",
            "Do not download H5AD/expression matrices yet. First restore Census metadata access and rerun this audit.",
            "",
            "## 9. Recommended integration plan",
            "",
            "Repeat Stage 26C metadata search, then freeze dataset roles before any download/integration.",
            "",
            "## 10. Role-freezing rules",
            "",
            "No dataset may be used for model selection. Clean holdout candidates must remain untouched by training unless explicitly reclassified.",
        ]
    )
    write_outputs(candidates, roles, report)


def open_census(cellxgene_census):
    attempts = ["stable", "latest", None]
    errors: list[str] = []
    for version in attempts:
        try:
            if version is None:
                return cellxgene_census.open_soma(), "default"
            return cellxgene_census.open_soma(census_version=version), str(version)
        except Exception as exc:  # pragma: no cover - depends on remote Census state.
            errors.append(f"{version or 'default'}: {exc}")
    raise RuntimeError("; ".join(errors))


def read_soma_dataframe(soma_df, value_filter: str | None = None, column_names: list[str] | None = None) -> pd.DataFrame:
    kwargs = {}
    if value_filter:
        kwargs["value_filter"] = value_filter
    if column_names:
        kwargs["column_names"] = column_names
    return soma_df.read(**kwargs).concat().to_pandas()


def read_dataset_metadata(census) -> pd.DataFrame:
    datasets = read_soma_dataframe(census["census_info"]["datasets"])
    if "dataset_id" not in datasets.columns:
        raise RuntimeError("CELLxGENE datasets metadata did not include dataset_id.")
    return datasets


def read_relevant_obs(census, organism_key: str) -> tuple[pd.DataFrame, str]:
    obs = census["census_data"][organism_key].obs
    columns = [
        "soma_joinid",
        "dataset_id",
        "donor_id",
        "assay",
        "disease",
        "tissue",
        "tissue_general",
        "cell_type",
        "sex",
        "development_stage",
        "suspension_type",
    ]
    filters = [
        f"tissue in {sql_list(TISSUE_TERMS)}",
        f"tissue_general in {sql_list(TISSUE_TERMS)}",
        f"cell_type in {sql_list(['microglial cell', 'central nervous system macrophage', 'macrophage', 'monocyte'])}",
        f"disease in {sql_list(QUERY_DISEASE_TERMS)}",
    ]
    value_filter = "(" + " or ".join(filters) + ")"
    try:
        df = read_soma_dataframe(obs, value_filter=value_filter, column_names=columns)
        return df.drop_duplicates(subset=["soma_joinid"], keep="first"), value_filter
    except Exception:
        # Some Census releases have stricter filter parsing. Fall back to exact
        # column filters rather than reading all obs metadata.
        frames = []
        for filt in filters:
            try:
                frames.append(read_soma_dataframe(obs, value_filter=filt, column_names=columns))
            except Exception:
                continue
        if not frames:
            raise
        df = pd.concat(frames, ignore_index=True)
        return df.drop_duplicates(subset=["soma_joinid"], keep="first"), "fallback exact-column filters"


def enrich_dataset_row(dataset_row: pd.Series, obs_rows: pd.DataFrame, organism: str) -> dict[str, object]:
    text_blob = " ".join(
        [
            norm(get_first(dataset_row, ["collection_name"])),
            norm(get_first(dataset_row, ["dataset_title", "title", "dataset_label"])),
            norm(get_first(dataset_row, ["dataset_id"])),
        ]
    )
    tissue_values = []
    for col in ["tissue", "tissue_general"]:
        if col in obs_rows.columns:
            tissue_values.extend(obs_rows[col].dropna().tolist())
    disease_values = obs_rows["disease"].dropna().tolist() if "disease" in obs_rows.columns else []
    cell_values = obs_rows["cell_type"].dropna().tolist() if "cell_type" in obs_rows.columns else []
    donor_values = obs_rows["donor_id"].dropna().tolist() if "donor_id" in obs_rows.columns else []

    tissue_lower = lower_set(tissue_values)
    disease_lower = lower_set(disease_values)
    cell_lower = lower_set(cell_values)

    has_brain = any(term in tissue_lower for term in TISSUE_TERMS)
    has_ad = any(term in disease_lower for term in ["alzheimer disease", "dementia"])
    has_control = any(term in disease_lower for term in ["normal", "control"])
    has_microglia = bool(MICROGLIA_TERMS & cell_lower)
    has_neuro_support = bool(NEURO_SUPPORT_TERMS & cell_lower)
    has_peripheral = bool(PERIPHERAL_TERMS & cell_lower) and not has_brain
    has_donor = len({norm(v) for v in donor_values if norm(v)}) > 0
    is_human = organism == "Homo sapiens"
    is_mouse = organism == "Mus musculus"
    collection_id = norm(get_first(dataset_row, ["collection_id"]))
    already_used = collection_id in ALREADY_USED_COLLECTION_IDS or contains_any(text_blob, ALREADY_USED_MARKERS)
    provenance_unclear = not norm(get_first(dataset_row, ["collection_name"])) or not norm(
        get_first(dataset_row, ["dataset_title", "title", "dataset_label"])
    )

    total_cells = int(get_first(dataset_row, ["dataset_total_cell_count", "cell_count"], 0) or 0)
    matched_cells = int(len(obs_rows))
    microglia_cells = int(obs_rows["cell_type"].isin(MICROGLIA_TERMS).sum()) if "cell_type" in obs_rows.columns else 0
    h5ad_path = norm(get_first(dataset_row, ["dataset_h5ad_path", "h5ad_path", "dataset_asset_h5ad_uri", "asset_h5ad_uri"]))

    score = 0
    if is_human and has_brain:
        score += 5
    if has_ad:
        score += 5
    if has_microglia:
        score += 4
    if has_donor:
        score += 3
    if has_ad or has_control:
        score += 3
    if has_neuro_support:
        score += 2
    if h5ad_path:
        score += 2
    if total_cells >= 10_000 or matched_cells >= 5_000:
        score += 2
    if is_mouse:
        score -= 5
    if has_peripheral:
        score -= 4
    if already_used:
        score -= 5
    if provenance_unclear:
        score -= 5

    role = recommend_role(
        is_human=is_human,
        is_mouse=is_mouse,
        has_brain=has_brain,
        has_ad=has_ad,
        has_microglia=has_microglia,
        has_peripheral=has_peripheral,
        already_used=already_used,
        provenance_unclear=provenance_unclear,
        score=score,
    )
    recommendation = download_recommendation(role, h5ad_path)

    notes = []
    if is_mouse:
        notes.append("mouse dataset; any human integration requires ortholog mapping")
    if has_peripheral:
        notes.append("peripheral immune signal is not direct brain microglia validation")
    if already_used:
        notes.append("resembles already-used v1/v2 provenance; plausibility only")
    if provenance_unclear:
        notes.append("collection/title provenance incomplete")
    if role == "clean_external_holdout_candidate":
        notes.append("keep untouched by training/model selection unless explicitly reclassified")

    return {
        "dataset_id": norm(dataset_row["dataset_id"]),
        "collection_id": collection_id,
        "collection_name": norm(get_first(dataset_row, ["collection_name"])),
        "dataset_title": norm(get_first(dataset_row, ["dataset_title", "title", "dataset_label"])),
        "organism": organism,
        "dataset_total_cell_count": total_cells,
        "matched_cell_count": matched_cells,
        "n_donors_or_samples": len({norm(v) for v in donor_values if norm(v)}),
        "n_microglia_or_cns_macrophage_cells": microglia_cells,
        "tissue_terms": joined(v for v in tissue_values if norm(v).lower() in {t.lower() for t in TISSUE_TERMS}),
        "disease_terms": joined(v for v in disease_values if norm(v).lower() in {t.lower() for t in DISEASE_TERMS}),
        "cell_type_terms": joined(v for v in cell_values if norm(v).lower() in {t.lower() for t in CELL_TYPE_TERMS}),
        "has_ad_or_dementia": has_ad,
        "has_control_or_normal": has_control,
        "has_brain_or_cns": has_brain,
        "has_microglia_or_cns_macrophage": has_microglia,
        "has_donor_metadata": has_donor,
        "dataset_h5ad_path": h5ad_path,
        "relevance_score": score,
        "recommended_role": role,
        "download_recommendation": recommendation,
        "notes": "; ".join(notes) if notes else "metadata candidate from CELLxGENE Census",
    }


def recommend_role(
    *,
    is_human: bool,
    is_mouse: bool,
    has_brain: bool,
    has_ad: bool,
    has_microglia: bool,
    has_peripheral: bool,
    already_used: bool,
    provenance_unclear: bool,
    score: int,
) -> str:
    if provenance_unclear or score < 0:
        return "do_not_use_until_reviewed"
    if already_used:
        return "already_used_plausibility_only"
    if is_mouse:
        return "mouse_auxiliary_only"
    if has_peripheral and not has_brain:
        return "peripheral_immune_plausibility"
    if is_human and has_brain and has_ad and has_microglia:
        return "clean_external_holdout_candidate"
    if is_human and has_brain and has_microglia:
        return "self_supervised_pretraining_candidate"
    if is_human and has_brain:
        return "external_projection_stress_test"
    if is_human and has_microglia:
        return "auxiliary_microglia_training_candidate"
    return "do_not_use_until_reviewed"


def download_recommendation(role: str, h5ad_path: str) -> str:
    if role == "clean_external_holdout_candidate":
        return "metadata/schema first; defer H5AD until v3 architecture/training is frozen"
    if role in {"self_supervised_pretraining_candidate", "auxiliary_microglia_training_candidate", "mouse_auxiliary_only"}:
        return "consider targeted H5AD download after role approval and schema review" if h5ad_path else "locate processed H5AD before integration"
    if role == "peripheral_immune_plausibility":
        return "metadata/schema only unless explicitly needed for peripheral plausibility"
    if role == "already_used_plausibility_only":
        return "avoid clean-validation use; download only for historical plausibility checks"
    return "do not download until reviewed"


def make_role_rows(candidates: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in candidates.to_dict("records"):
        role = row["recommended_role"]
        allowed_training = role in {"self_supervised_pretraining_candidate", "auxiliary_microglia_training_candidate", "mouse_auxiliary_only"}
        allowed_pretraining = role in {"self_supervised_pretraining_candidate", "mouse_auxiliary_only"}
        allowed_aux = role in {"auxiliary_microglia_training_candidate", "mouse_auxiliary_only", "peripheral_immune_plausibility"}
        holdout = role == "clean_external_holdout_candidate"
        risks = []
        if holdout:
            risks.append("training would contaminate an external holdout")
        if role == "mouse_auxiliary_only":
            risks.append("mouse data cannot provide human external validation")
        if role == "peripheral_immune_plausibility":
            risks.append("peripheral immune data cannot validate brain microglia directly")
        if role == "already_used_plausibility_only":
            risks.append("already-used provenance prevents clean external validation")
        if role == "do_not_use_until_reviewed":
            risks.append("metadata/provenance insufficient for integration")
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "collection_name": row["collection_name"],
                "dataset_title": row["dataset_title"],
                "organism": row["organism"],
                "recommended_role": role,
                "allowed_for_training": bool(allowed_training),
                "allowed_for_pretraining": bool(allowed_pretraining),
                "allowed_for_auxiliary_supervision": bool(allowed_aux),
                "reserved_for_external_holdout": bool(holdout),
                "allowed_for_model_selection": False,
                "risk_if_used_for_training": "; ".join(risks) if risks else "standard leakage/QC risk; freeze role before use",
                "rationale": row["notes"],
                "notes": "No CELLxGENE dataset is allowed for model selection in this audit.",
            }
        )
    return pd.DataFrame(rows)


def bullet_table(df: pd.DataFrame, columns: list[str], limit: int = 10) -> list[str]:
    lines = []
    for row in df.head(limit).to_dict("records"):
        fields = [f"{col}={row.get(col, '')}" for col in columns]
        lines.append("- " + "; ".join(fields))
    return lines or ["- None identified from metadata query."]


def build_report(candidates: pd.DataFrame, roles: pd.DataFrame, census_version: str, query_notes: list[str], n_datasets_scanned: int) -> str:
    ranked = candidates.sort_values(["relevance_score", "matched_cell_count"], ascending=[False, False])
    human_ad = ranked[
        (ranked["organism"] == "Homo sapiens")
        & (ranked["has_ad_or_dementia"])
        & (ranked["has_brain_or_cns"])
    ]
    human_normal = ranked[
        (ranked["organism"] == "Homo sapiens")
        & (ranked["has_brain_or_cns"])
        & (~ranked["has_ad_or_dementia"])
    ]
    mouse = ranked[ranked["organism"] == "Mus musculus"]
    peripheral = ranked[ranked["recommended_role"] == "peripheral_immune_plausibility"]
    review = ranked[ranked["recommended_role"].isin(["do_not_use_until_reviewed", "already_used_plausibility_only"])]

    lines = [
        "# v3 CELLxGENE relevant dataset search v1",
        "",
        "## 1. Executive summary",
        "",
        f"Stage 26C searched CELLxGENE Census metadata using Census release `{census_version}`.",
        f"Dataset metadata rows scanned: {n_datasets_scanned}. Candidate dataset rows emitted: {len(candidates)}.",
        "No expression matrices/H5AD payloads were downloaded. No v3 training, graph neural model, external validation, model selection, evidence-level change, or manuscript prose was run.",
        "",
        "## 2. Search method",
        "",
        "The script loaded `census['census_info']['datasets']` and queried human and mouse obs metadata for brain/CNS tissues, microglia/CNS macrophage or immune cell labels, and neurodegenerative disease labels.",
        "Broad `normal`/`control` disease-only queries were not used as standalone filters to avoid pulling unrelated whole-Census normal/control metadata; control/normal labels are reported when present among matched brain/cell-type/disease records.",
        *[f"- {note}" for note in query_notes],
        "",
        "## 3. Best human AD/dementia brain candidates",
        "",
        *bullet_table(
            human_ad,
            [
                "collection_name",
                "dataset_title",
                "matched_cell_count",
                "n_microglia_or_cns_macrophage_cells",
                "relevance_score",
                "recommended_role",
            ],
            limit=12,
        ),
        "",
        "## 4. Best human normal brain/microglia pretraining candidates",
        "",
        *bullet_table(
            human_normal,
            [
                "collection_name",
                "dataset_title",
                "matched_cell_count",
                "n_microglia_or_cns_macrophage_cells",
                "relevance_score",
                "recommended_role",
            ],
            limit=12,
        ),
        "",
        "## 5. Mouse auxiliary candidates",
        "",
        *bullet_table(mouse, ["collection_name", "dataset_title", "matched_cell_count", "relevance_score", "recommended_role"], limit=12),
        "",
        "## 6. Peripheral immune candidates",
        "",
        *bullet_table(peripheral, ["collection_name", "dataset_title", "matched_cell_count", "relevance_score", "recommended_role"], limit=12),
        "",
        "## 7. Datasets to avoid or review",
        "",
        *bullet_table(review, ["collection_name", "dataset_title", "relevance_score", "recommended_role", "notes"], limit=12),
        "",
        "## 8. Recommended downloads",
        "",
        "Metadata/schema should remain the first download step. H5AD download should be limited to top-ranked candidates after role approval. Clean holdout candidates should stay untouched until v3 architecture/training decisions are frozen.",
        "",
        "## 9. Recommended integration plan",
        "",
        "- Preserve clean human AD/dementia brain candidates as external holdouts unless intentionally reclassified.",
        "- Use mouse datasets only as auxiliary/pretraining resources with ortholog mapping, never as human validation.",
        "- Use peripheral immune datasets only for plausibility/auxiliary context, not direct brain microglia validation.",
        "- Keep already-used or provenance-unclear datasets out of clean validation.",
        "",
        "## 10. Role-freezing rules",
        "",
        "No CELLxGENE dataset found in this audit is allowed for model selection. Training/pretraining permissions are role-specific and must be frozen before any matrix download or integration.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        cellxgene_census = importlib.import_module("cellxgene_census")
    except ImportError as exc:
        write_unavailable_outputs("cellxgene-census package missing", str(exc))
        print(f"Wrote unavailable CELLxGENE audit outputs because cellxgene-census is missing: {exc}")
        return

    try:
        census, census_version = open_census(cellxgene_census)
        with census:
            datasets = read_dataset_metadata(census)
            dataset_by_id = datasets.set_index("dataset_id", drop=False)

            obs_frames = []
            query_notes = []
            for organism_key, organism_label in [("homo_sapiens", "Homo sapiens"), ("mus_musculus", "Mus musculus")]:
                obs_df, obs_filter = read_relevant_obs(census, organism_key)
                obs_df = obs_df.copy()
                obs_df["organism"] = organism_label
                obs_frames.append(obs_df)
                query_notes.append(f"{organism_label}: {len(obs_df)} matched obs rows using `{obs_filter}`")

            all_obs = pd.concat(obs_frames, ignore_index=True)
            rows = []
            for (dataset_id, organism), group in all_obs.groupby(["dataset_id", "organism"], dropna=False):
                if dataset_id not in dataset_by_id.index:
                    continue
                rows.append(enrich_dataset_row(dataset_by_id.loc[dataset_id], group, organism))

            if not rows:
                write_unavailable_outputs("CELLxGENE metadata query returned no candidate rows", "; ".join(query_notes))
                print("Wrote unavailable CELLxGENE audit outputs because no candidate rows were found.")
                return

            candidates = pd.DataFrame(rows).sort_values(["relevance_score", "matched_cell_count"], ascending=[False, False])
            roles = make_role_rows(candidates)
            report = build_report(candidates, roles, census_version, query_notes, len(datasets))
            write_outputs(candidates, roles, report)
    except Exception as exc:
        write_unavailable_outputs(
            "cellxgene-census metadata search failed",
            f"{exc}\n{traceback.format_exc(limit=5)}",
        )
        print(f"Wrote unavailable CELLxGENE audit outputs because metadata search failed: {exc}")
        return

    print(f"Wrote {CANDIDATES_OUT}")
    print(f"Wrote {ROLES_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
