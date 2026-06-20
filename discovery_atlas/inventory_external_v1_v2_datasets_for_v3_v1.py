"""Inventory external v1/v2 dataset artifacts and freeze v3 roles.

This Stage 26A script is provenance-only. It does not train v3, run graph
neural models, run external validation, change evidence levels, create biology
cards, or write manuscript prose.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

INVENTORY_OUT = TABLE_DIR / "v3_external_dataset_inventory_v1.csv"
ROLES_OUT = TABLE_DIR / "v3_external_dataset_role_assignment_v1.csv"
REPORT_OUT = REPORT_DIR / "v3_external_dataset_role_assignment_v1.md"

GENE_UNIVERSE = TABLE_DIR / "ablation_edge_sets" / "no_graph_identity_edges_v1.csv"

SEARCH_PATTERNS = [
    "gse174367",
    "abeta",
    "aβ",
    "external",
    "trajectory",
    "cell-state",
    "cell_state",
    "perturb",
    "validation",
    "v2_1",
    "v2_2",
    "geo",
    "gse",
    "cellxgene",
    "grubman",
    "gse138852",
]

KNOWN_CANDIDATES = [
    "results/tables/v2_1_gse174367_cell_trajectory_scores.csv",
    "results/tables/v2_2_abeta_responsive_microglia_cell_scores_summary.csv",
    "docs/stage_c_finetuning_analysis.md",
]

PATH_EXCLUDE_HINTS = [
    ".git/",
    ".codex/",
    "__pycache__",
    ".pytest_cache",
    "results/tables/multitarget_causal/",
]

FOCUSED_INCLUDE_HINTS = [
    "gse174367",
    "gse138852",
    "grubman",
    "geo",
    "external",
    "open_validation",
    "cellxgene",
    "perturb",
    "v2_1",
    "v2_2",
    "abeta_responsive",
    "abeta_mil",
    "stage_c",
    "trajectory",
]


@dataclass
class DatasetArtifact:
    dataset_id: str
    dataset_name: str
    source: str
    path: str


def read_gene_universe() -> set[str]:
    if not GENE_UNIVERSE.exists():
        return set()
    df = pd.read_csv(GENE_UNIVERSE)
    candidates = []
    for col in df.columns:
        if col.lower() in {"gene", "source", "target"}:
            candidates.extend(df[col].dropna().astype(str).tolist())
    return {gene.upper() for gene in candidates}


def matched_files() -> list[Path]:
    paths: set[Path] = set()
    lowered_patterns = [p.lower() for p in SEARCH_PATTERNS]
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        rel_lower = rel.lower()
        if any(hint in rel_lower for hint in PATH_EXCLUDE_HINTS):
            continue
        if any(pattern in rel_lower for pattern in lowered_patterns) and any(
            hint in rel_lower for hint in FOCUSED_INCLUDE_HINTS
        ):
            if path.suffix.lower() in {".csv", ".tsv", ".txt", ".md", ".svg", ".ps1", ".py"}:
                paths.add(path)
    for candidate in KNOWN_CANDIDATES:
        paths.add(ROOT / candidate)
    return sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix().lower())


def infer_dataset_id(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix().lower()
    if "gse174367" in rel:
        return "gse174367_morabito"
    if "gse138852" in rel or "grubman" in rel:
        return "gse138852_grubman"
    if "abeta_responsive_microglia" in rel or "abeta_mil" in rel:
        return "v2_2_abeta_responsive_microglia"
    if "cellxgene" in rel:
        return "cellxgene_normal_microglia"
    if "perturbseq" in rel or "perturbation" in rel or "crispr" in rel:
        return "perturbation_related"
    if "external_gene_masks" in rel:
        return "external_gene_masks"
    if "external" in rel:
        return "external_validation_related"
    if "v2_1" in rel:
        return "v2_1_external_or_projection_artifacts"
    if "v2_2" in rel:
        return "v2_2_external_or_projection_artifacts"
    if "stage_c" in rel:
        return "stage_c_finetuning_artifacts"
    return re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_")[:64]


def dataset_name_source(dataset_id: str) -> tuple[str, str]:
    mapping = {
        "gse174367_morabito": ("GSE174367 Morabito external AD microglia/projection artifacts", "GEO / GSE174367"),
        "gse138852_grubman": ("GSE138852/Grubman external AD microglia zero-shot artifacts", "GEO / GSE138852"),
        "v2_2_abeta_responsive_microglia": ("v2.2 Aβ-responsive microglia derived artifacts", "SEA-AD derived / internal v2.2 analysis"),
        "cellxgene_normal_microglia": ("cellxgene normal microglia anchor artifacts", "cellxgene external normal microglia"),
        "perturbation_related": ("Perturb-seq / perturbation benchmark artifacts", "external perturbation references or synthetic placeholders"),
        "external_gene_masks": ("External gene masks and overlap artifacts", "external gene universe overlap"),
        "external_validation_related": ("External validation planning/projection artifacts", "mixed external validation artifacts"),
        "v2_1_external_or_projection_artifacts": ("v2.1 external/projection artifacts", "mixed v2.1 artifacts"),
        "v2_2_external_or_projection_artifacts": ("v2.2 external/projection artifacts", "mixed v2.2 artifacts"),
        "stage_c_finetuning_artifacts": ("Stage C fine-tuning documentation/artifacts", "internal SEA-AD model-development artifacts"),
    }
    return mapping.get(dataset_id, (dataset_id.replace("_", " ").title(), "repository artifact"))


def sniff_table(path: Path) -> tuple[int | None, int | None, list[str]]:
    if not path.exists() or path.suffix.lower() not in {".csv", ".tsv", ".txt"}:
        return None, None, []
    sep = "\t" if path.suffix.lower() == ".tsv" else ","
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle, delimiter=sep)
            header = next(reader, [])
            n_rows = sum(1 for _ in reader)
        return n_rows, len(header), header
    except Exception:
        return None, None, []


def summarize_artifact(path: Path, gene_universe: set[str]) -> dict[str, object]:
    rel = path.relative_to(ROOT).as_posix()
    exists = path.exists()
    n_rows, n_cols, cols = sniff_table(path)
    col_text = " ".join(cols).lower()
    path_text = rel.lower()
    col_upper = {c.upper() for c in cols}
    overlap = len(gene_universe & col_upper) if gene_universe and cols else 0
    has_gene_expression = overlap >= 20 or "gene" in col_text or "expression" in path_text or "pseudobulk" in path_text
    has_cell_level_data = "cell" in path_text or "cell" in col_text or "barcode" in col_text
    has_donor_level_data = "donor" in path_text or "donor" in col_text or "Donor ID" in cols
    has_pathology_targets = any(token in col_text or token in path_text for token in ["at8", "6e10", "abeta", "aβ", "gfap", "iba1", "neun", "pathology"])
    has_cell_state_labels = any(token in col_text or token in path_text for token in ["cell_state", "cell-state", "cluster", "state", "label"])
    has_trajectory_scores = "trajectory" in path_text or "trajectory" in col_text
    has_perturbation_labels = any(token in path_text or token in col_text for token in ["perturb", "crispr", "knockout", "intervention"])
    notes = []
    if not exists:
        notes.append("Known candidate path missing.")
    if path.suffix.lower() in {".md", ".py", ".ps1"}:
        notes.append("Documentation or script artifact; role assignment reflects provenance/use, not direct training data.")
    if overlap:
        notes.append(f"{overlap} column/header names overlap 2,957-gene universe.")
    return {
        "path": rel,
        "exists": exists,
        "n_rows": "" if n_rows is None else n_rows,
        "n_columns": "" if n_cols is None else n_cols,
        "has_gene_expression": has_gene_expression,
        "has_cell_level_data": has_cell_level_data,
        "has_donor_level_data": has_donor_level_data,
        "has_pathology_targets": has_pathology_targets,
        "has_cell_state_labels": has_cell_state_labels,
        "has_trajectory_scores": has_trajectory_scores,
        "has_perturbation_labels": has_perturbation_labels,
        "overlap_with_2957_gene_universe": overlap,
        "notes": " ".join(notes),
    }


def build_inventory() -> pd.DataFrame:
    gene_universe = read_gene_universe()
    rows = []
    for path in matched_files():
        dataset_id = infer_dataset_id(path)
        dataset_name, source = dataset_name_source(dataset_id)
        summary = summarize_artifact(path, gene_universe)
        rows.append(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "source": source,
                **summary,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["dataset_id", "path"]).reset_index(drop=True)


def bool_any(group: pd.DataFrame, col: str) -> bool:
    return group[col].astype(str).str.lower().isin(["true", "1", "yes"]).any()


def assign_role(dataset_id: str, group: pd.DataFrame) -> dict[str, object]:
    has_pathology = bool_any(group, "has_pathology_targets")
    has_cell_state = bool_any(group, "has_cell_state_labels")
    has_trajectory = bool_any(group, "has_trajectory_scores")
    has_perturb = bool_any(group, "has_perturbation_labels")
    has_expression = bool_any(group, "has_gene_expression")
    provenance_unclear = dataset_id in {
        "external_validation_related",
        "v2_1_external_or_projection_artifacts",
        "v2_2_external_or_projection_artifacts",
        "stage_c_finetuning_artifacts",
    }

    if "gse174367" in dataset_id:
        role = "biological_plausibility_check"
        rationale = "Already used/generated in v2 external projection/trajectory artifacts; not untouched for v3 external validation."
        training = False
        pretraining = False
        aux = False
        validation = False
        selection = False
        final_reporting = True
        risk = "High if used for training: would contaminate a previously used external plausibility/projection reference."
    elif "gse138852" in dataset_id:
        role = "biological_plausibility_check"
        rationale = "Already used in zero-shot/projection artifacts; useful as plausibility context, not untouched validation."
        training = False
        pretraining = False
        aux = False
        validation = False
        selection = False
        final_reporting = True
        risk = "High if reused for model selection after prior external projection analyses."
    elif dataset_id == "cellxgene_normal_microglia":
        role = "self_supervised_pretraining"
        rationale = "Normal microglia expression anchors may support self-supervised representation pretraining; no SEA-AD-like pathology targets."
        training = True
        pretraining = True
        aux = False
        validation = False
        selection = False
        final_reporting = True
        risk = "Moderate: using it for pretraining precludes calling it untouched validation."
    elif dataset_id == "v2_2_abeta_responsive_microglia":
        role = "auxiliary_supervised_training"
        rationale = "Aβ-responsive cell/axis labels can supervise auxiliary biological heads, but are not main donor-level pathology targets."
        training = True
        pretraining = False
        aux = True
        validation = False
        selection = False
        final_reporting = True
        risk = "High if later treated as independent validation because it would influence auxiliary training."
    elif dataset_id == "perturbation_related":
        role = "future_perturbation_calibration"
        rationale = "Perturbation artifacts are relevant to future calibration, not current pathology prediction validation."
        training = False
        pretraining = False
        aux = False
        validation = False
        selection = False
        final_reporting = True
        risk = "Moderate if synthetic or previously inspected perturbation references are mixed with final validation claims."
    elif dataset_id == "external_gene_masks":
        role = "biological_plausibility_check"
        rationale = "Gene masks are overlap/provenance aids, not direct outcome datasets."
        training = False
        pretraining = False
        aux = False
        validation = False
        selection = False
        final_reporting = True
        risk = "Low for reporting overlap; high if used post hoc to select targets after results."
    elif provenance_unclear:
        role = "do_not_use_until_reviewed"
        rationale = "Provenance or role is unclear/mixed; freeze out of training and validation until reviewed."
        training = False
        pretraining = False
        aux = False
        validation = False
        selection = False
        final_reporting = False
        risk = "Unknown; do not use for v3 decisions until reviewed."
    elif has_perturb:
        role = "future_perturbation_calibration"
        rationale = "Perturbation labels suggest future calibration, not current internal pathology benchmark."
        training = False
        pretraining = False
        aux = False
        validation = False
        selection = False
        final_reporting = True
        risk = "Moderate if used to tune v3 then claimed as validation."
    elif has_cell_state or has_trajectory:
        role = "auxiliary_supervised_training"
        rationale = "Cell-state/trajectory labels may support auxiliary biological heads but should not be main pathology-head labels."
        training = True
        pretraining = False
        aux = True
        validation = False
        selection = False
        final_reporting = True
        risk = "High if used for auxiliary training and later described as untouched validation."
    elif has_expression and not has_pathology:
        role = "self_supervised_pretraining"
        rationale = "Expression data without compatible donor-level pathology targets may support self-supervised pretraining only."
        training = True
        pretraining = True
        aux = False
        validation = False
        selection = False
        final_reporting = True
        risk = "Moderate: pretraining use prevents untouched-validation use."
    else:
        role = "do_not_use_until_reviewed"
        rationale = "No clear v3-safe use inferred from file names/columns."
        training = False
        pretraining = False
        aux = False
        validation = False
        selection = False
        final_reporting = False
        risk = "Unknown until reviewed."

    if validation:
        training = False
        selection = False

    return {
        "dataset_id": dataset_id,
        "recommended_role": role,
        "allowed_for_training": training,
        "allowed_for_pretraining": pretraining,
        "allowed_for_auxiliary_supervision": aux,
        "reserved_for_external_validation": validation,
        "allowed_for_model_selection": selection,
        "allowed_for_final_reporting": final_reporting,
        "risk_if_used_for_training": risk,
        "rationale": rationale,
        "notes": (
            f"Artifacts={len(group)}; has_pathology_targets={has_pathology}; "
            f"has_cell_state_labels={has_cell_state}; has_trajectory_scores={has_trajectory}; "
            f"has_perturbation_labels={has_perturb}."
        ),
    }


def build_roles(inventory: pd.DataFrame) -> pd.DataFrame:
    rows = [assign_role(dataset_id, group) for dataset_id, group in inventory.groupby("dataset_id", sort=True)]
    return pd.DataFrame(rows).sort_values("dataset_id").reset_index(drop=True)


def write_report(inventory: pd.DataFrame, roles: pd.DataFrame) -> None:
    found_lines = []
    for row in roles.itertuples():
        group = inventory[inventory["dataset_id"] == row.dataset_id]
        found_lines.append(
            f"- `{row.dataset_id}`: {group['dataset_name'].iloc[0]} ({group['source'].iloc[0]}); artifacts={len(group)}"
        )
    role_lines = [
        f"- `{row.dataset_id}` -> `{row.recommended_role}`; training={row.allowed_for_training}; validation_holdout={row.reserved_for_external_validation}. {row.rationale}"
        for row in roles.itertuples()
    ]
    contents_lines = []
    for dataset_id, group in inventory.groupby("dataset_id", sort=True):
        contents_lines.append(
            f"- `{dataset_id}`: rows_total_known={pd.to_numeric(group['n_rows'], errors='coerce').sum(skipna=True):.0f}; "
            f"gene_expression={bool_any(group, 'has_gene_expression')}; donor_level={bool_any(group, 'has_donor_level_data')}; "
            f"cell_level={bool_any(group, 'has_cell_level_data')}; pathology_targets={bool_any(group, 'has_pathology_targets')}; "
            f"cell_state={bool_any(group, 'has_cell_state_labels')}; trajectory={bool_any(group, 'has_trajectory_scores')}; perturbation={bool_any(group, 'has_perturbation_labels')}"
        )
    pretraining = roles[roles["allowed_for_pretraining"]]["dataset_id"].tolist()
    aux = roles[roles["allowed_for_auxiliary_supervision"]]["dataset_id"].tolist()
    validation = roles[roles["reserved_for_external_validation"]]["dataset_id"].tolist()
    reviewed = roles[roles["recommended_role"] == "do_not_use_until_reviewed"]["dataset_id"].tolist()

    REPORT_OUT.write_text(
        "\n".join(
            [
                "# v3 external dataset role assignment v1",
                "",
                "## 1. Executive summary",
                "",
                "Stage 26A inventories external or non-SEA-AD-like v1/v2 artifacts before v3 training and freezes conservative dataset roles. Any dataset used for training, tuning, model selection, or architecture decisions cannot later be claimed as untouched external validation.",
                "",
                f"Datasets/artifact groups found: `{roles['dataset_id'].nunique()}`. No dataset is currently reserved as untouched external validation because the discovered external artifacts have already been used/generated in v1/v2 analyses or have mixed/unclear provenance.",
                "",
                "No v3 training, graph neural model, external validation, evidence-level change, candidate biology card, or manuscript prose was run.",
                "",
                "## 2. External datasets found",
                "",
                *found_lines,
                "",
                "## 3. What each dataset contains",
                "",
                *contents_lines,
                "",
                "## 4. Recommended role for each dataset",
                "",
                *role_lines,
                "",
                "## 5. Training-safe uses",
                "",
                f"- Self-supervised pretraining candidates: {', '.join(pretraining) if pretraining else 'none'}",
                f"- Auxiliary supervision candidates: {', '.join(aux) if aux else 'none'}",
                "- Main donor-level pathology prediction head: use SEA-AD locked donor folds only unless a future dataset has compatible donor-level pathology targets and is explicitly approved.",
                "",
                "## 6. Validation-safe uses",
                "",
                f"- Reserved untouched external validation datasets: {', '.join(validation) if validation else 'none currently identified'}",
                "- GSE174367/GSE138852-derived artifacts should be treated as biological plausibility or prior external-projection context, not untouched v3 validation holdouts.",
                "",
                "## 7. Risks of overfitting/generalization leakage",
                "",
                "- A dataset used for pretraining or auxiliary supervision is no longer untouched validation.",
                "- A dataset used for model selection, threshold choices, architecture choices, or candidate filtering cannot later support final external-validation claims.",
                "- Provenance-unclear artifacts are frozen as do-not-use until reviewed.",
                "",
                "## 8. Recommended v3 training strategy",
                "",
                "- Use SEA-AD locked donor folds for the main pathology benchmark.",
                "- Use external expression/cell-state datasets only for self-supervised pretraining or auxiliary biological heads unless compatible pathology labels are proven.",
                "- Keep role flags frozen in the CSV before any v3 training begins.",
                "",
                "## 9. Recommended untouched validation strategy",
                "",
                "- Keep at least one future external dataset untouched if a final external generalization claim is desired.",
                "- Do not use external validation data during model selection.",
                f"- Do-not-use-until-reviewed groups: {', '.join(reviewed) if reviewed else 'none'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory()
    if inventory.empty:
        raise RuntimeError("No external/non-SEA-AD-like artifacts found")
    roles = build_roles(inventory)
    inventory.to_csv(INVENTORY_OUT, index=False)
    roles.to_csv(ROLES_OUT, index=False)
    write_report(inventory, roles)
    print(f"Wrote {INVENTORY_OUT}")
    print(f"Wrote {ROLES_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
