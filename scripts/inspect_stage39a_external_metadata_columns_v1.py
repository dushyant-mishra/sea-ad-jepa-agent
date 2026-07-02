from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def unique_join(values: list[Any], sep: str = ";") -> str:
    seen: list[str] = []
    for value in values:
        text = clean_text(value)
        if not text or text.lower() == "nan":
            continue
        if text not in seen:
            seen.append(text)
    return sep.join(seen)


def contains_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def term_hits(text: str, terms: list[str]) -> str:
    lower = text.lower()
    return unique_join([term for term in terms if term.lower() in lower])


def read_table_preview(path: Path, nrows: int = 200) -> tuple[pd.DataFrame, str]:
    suffixes = "".join(path.suffixes).lower()
    try:
        if suffixes.endswith(".csv.gz") or suffixes.endswith(".csv"):
            return pd.read_csv(path, nrows=nrows), "csv"
        if suffixes.endswith(".tsv.gz") or suffixes.endswith(".tsv"):
            return pd.read_csv(path, sep="\t", nrows=nrows), "tsv"
        if suffixes.endswith(".txt.gz") or suffixes.endswith(".txt"):
            # GEO series-matrix files are text metadata, not expression tables for this stage.
            opener = gzip.open if suffixes.endswith(".gz") else open
            rows: list[dict[str, str]] = []
            with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.startswith("!Sample_") or line.startswith("!Series_"):
                        key, *vals = line.rstrip("\n").split("\t")
                        rows.append({"geo_key": key.lstrip("!"), "n_values": str(len(vals)), "example_values": unique_join(vals[:5])})
                    if len(rows) >= nrows:
                        break
            return pd.DataFrame(rows), "geo_series_matrix"
        return pd.DataFrame(), "unsupported_preview"
    except Exception as exc:  # noqa: BLE001
        return pd.DataFrame([{"load_error": str(exc)}]), "load_failed"


def inspect_h5_10x(path: Path) -> dict[str, Any]:
    out = {
        "h5_inspected": False,
        "h5_barcodes_found": False,
        "h5_features_found": False,
        "h5_n_barcodes": 0,
        "h5_n_features": 0,
        "h5_error": "",
    }
    try:
        import h5py  # type: ignore
    except Exception as exc:  # noqa: BLE001
        out["h5_error"] = f"h5py_unavailable:{exc}"
        return out
    try:
        with h5py.File(path, "r") as handle:
            out["h5_inspected"] = True
            matrix = handle.get("matrix")
            if matrix is not None:
                if "barcodes" in matrix:
                    out["h5_barcodes_found"] = True
                    out["h5_n_barcodes"] = len(matrix["barcodes"])
                features = matrix.get("features")
                if features is not None:
                    if "name" in features:
                        out["h5_features_found"] = True
                        out["h5_n_features"] = len(features["name"])
                    elif "id" in features:
                        out["h5_features_found"] = True
                        out["h5_n_features"] = len(features["id"])
    except Exception as exc:  # noqa: BLE001
        out["h5_error"] = str(exc)
    return out


def read_10x_barcodes(path: Path, max_barcodes: int | None = None) -> list[str]:
    try:
        import h5py  # type: ignore
    except Exception:
        return []
    try:
        with h5py.File(path, "r") as handle:
            ds = handle["matrix"]["barcodes"]
            if max_barcodes is None:
                vals = ds[:]
            else:
                vals = ds[:max_barcodes]
            return [v.decode("utf-8") if isinstance(v, bytes) else str(v) for v in vals]
    except Exception:
        return []


def infer_dataset_files(inventory: pd.DataFrame, dataset_ids: list[str]) -> pd.DataFrame:
    if inventory.empty:
        return pd.DataFrame()
    return inventory[inventory["dataset_id"].astype(str).str.lower().isin([d.lower() for d in dataset_ids])].copy()


def inspect_file_metadata(row: pd.Series, terms: dict[str, list[str]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = resolve(str(row["file_path"]))
    preview, preview_type = read_table_preview(path)
    h5_info = inspect_h5_10x(path) if path.suffix.lower() == ".h5" else {}
    cols = list(preview.columns) if not preview.empty else []
    if preview_type == "geo_series_matrix" and "geo_key" in preview.columns:
        cols = preview["geo_key"].astype(str).tolist()
    inventory_row = {
        "dataset_id": row.get("dataset_id", ""),
        "file_path": str(path.relative_to(ROOT)) if path.exists() else str(path),
        "file_name": path.name,
        "inferred_file_type_stage38a": row.get("inferred_file_type", ""),
        "preview_type": preview_type,
        "file_exists": path.exists(),
        "n_preview_rows": len(preview),
        "n_preview_columns": len(cols),
        "preview_columns": unique_join(cols[:50]),
        "h5_inspected": h5_info.get("h5_inspected", False),
        "h5_barcodes_found": h5_info.get("h5_barcodes_found", False),
        "h5_features_found": h5_info.get("h5_features_found", False),
        "h5_n_barcodes": h5_info.get("h5_n_barcodes", 0),
        "h5_n_features": h5_info.get("h5_n_features", 0),
        "h5_error": h5_info.get("h5_error", ""),
    }
    candidates: list[dict[str, Any]] = []
    for col in cols:
        col_text = clean_text(col)
        roles = [role for role, role_terms in terms.items() if contains_any(col_text, role_terms)]
        if roles:
            examples = ""
            if col_text in preview.columns:
                examples = unique_join(preview[col_text].dropna().astype(str).head(8).tolist())
            elif preview_type == "geo_series_matrix" and "geo_key" in preview.columns:
                hit = preview[preview["geo_key"].astype(str) == col_text]
                if not hit.empty and "example_values" in hit.columns:
                    examples = clean_text(hit.iloc[0]["example_values"])
            candidates.append(
                {
                    "dataset_id": row.get("dataset_id", ""),
                    "file_path": inventory_row["file_path"],
                    "column_name": col_text,
                    "candidate_roles": unique_join(roles),
                    "matched_terms": unique_join([term_hits(col_text, terms[role]) for role in roles]),
                    "example_values": examples,
                    "n_unique_preview_values": int(preview[col_text].nunique()) if col_text in preview.columns else "",
                }
            )
    return inventory_row, candidates


def choose_column(df: pd.DataFrame, role_terms: list[str]) -> str:
    if df.empty:
        return ""
    scored: list[tuple[int, str]] = []
    for col in df.columns:
        lower = col.lower()
        score = sum(1 for term in role_terms if term.lower() in lower)
        if score:
            scored.append((score, col))
    if not scored:
        return ""
    return sorted(scored, key=lambda x: (-x[0], len(x[1])))[0][1]


def find_metadata_file(file_rows: pd.DataFrame) -> str:
    if file_rows.empty:
        return ""
    metadata = file_rows[file_rows.get("usable_for_metadata", pd.Series(dtype=bool)).map(as_bool)]
    if not metadata.empty:
        return clean_text(metadata.iloc[0]["file_path"])
    for _, row in file_rows.iterrows():
        name = clean_text(row.get("file_name", "")).lower()
        if "meta" in name or "covariate" in name:
            return clean_text(row.get("file_path", ""))
    return ""


def find_expression_file(file_rows: pd.DataFrame) -> str:
    if file_rows.empty:
        return ""
    expr = file_rows[file_rows.get("usable_for_expression", pd.Series(dtype=bool)).map(as_bool)]
    if not expr.empty:
        # Prefer processed/count matrix over GEO series matrix when possible.
        rows = expr.copy()
        rows["rank"] = rows["file_name"].astype(str).str.contains("series_matrix", case=False).map(lambda x: 1 if x else 0)
        rows = rows.sort_values(["rank", "file_size_bytes"], ascending=[True, False])
        return clean_text(rows.iloc[0]["file_path"])
    return ""
