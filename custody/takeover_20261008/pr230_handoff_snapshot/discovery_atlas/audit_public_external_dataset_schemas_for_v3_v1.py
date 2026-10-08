"""Audit public external dataset schemas for Graph-JEPA v3 integration.

Stage 26B is a schema/metadata audit only. It downloads small GEO
series-matrix metadata files when available, records supplementary file
listings, and never downloads SRA/FASTQ/BAM/raw sequencing payloads.
"""

from __future__ import annotations

import gzip
import html.parser
import re
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import h5py
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "data" / "external" / "public_schema_audit"
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

SCHEMA_OUT = TABLE_DIR / "v3_public_external_dataset_schema_inventory_v1.csv"
MAP_OUT = TABLE_DIR / "v3_public_external_dataset_integration_map_v1.csv"
REPORT_OUT = REPORT_DIR / "v3_public_external_dataset_schema_audit_v1.md"

GENE_UNIVERSE = TABLE_DIR / "ablation_edge_sets" / "no_graph_identity_edges_v1.csv"
MAX_METADATA_DOWNLOAD_MB = 80
HTTP_TIMEOUT = 30


@dataclass(frozen=True)
class CandidateDataset:
    dataset_id: str
    geo_accession: str
    dataset_name: str
    organism: str
    assay_type: str
    expected_role: str
    expected_file_type: str
    frozen_context: str


DATASETS = [
    CandidateDataset(
        "gse157827",
        "GSE157827",
        "Candidate public external brain snRNA/scRNA dataset",
        "Homo sapiens",
        "single-cell/nucleus RNA-seq",
        "candidate untouched external stress-test/holdout unless reclassified",
        "series matrix metadata; supplementary MTX/H5/TSV possible",
        "Remain external holdout candidate unless explicitly used for training later.",
    ),
    CandidateDataset(
        "gse147528",
        "GSE147528",
        "Candidate public external brain snRNA/scRNA dataset",
        "Homo sapiens",
        "single-cell/nucleus RNA-seq",
        "candidate untouched external stress-test/holdout unless reclassified",
        "series matrix metadata; supplementary MTX/H5/TSV possible",
        "Remain external holdout candidate unless explicitly used for training later.",
    ),
    CandidateDataset(
        "gse203206",
        "GSE203206",
        "Candidate public bulk donor/sample-level external stress test",
        "Homo sapiens",
        "bulk RNA-seq / expression profiling",
        "bulk donor/sample-level external stress test",
        "series matrix metadata; CSV/TSV counts possible",
        "Bulk sample-level, not cell-level.",
    ),
    CandidateDataset(
        "gse98969",
        "GSE98969",
        "Mouse DAM/microglia auxiliary pretraining candidate",
        "Mus musculus",
        "single-cell RNA-seq / microglia signatures",
        "mouse DAM/microglia auxiliary pretraining candidate",
        "series matrix metadata; supplementary TSV/MTX possible",
        "Mouse; any integration requires mouse-to-human ortholog mapping.",
    ),
    CandidateDataset(
        "gse127893",
        "GSE127893",
        "Mouse/public subseries review candidate",
        "Mus musculus",
        "mixed/subseries RNA-seq",
        "review subseries before any download",
        "series matrix metadata/subseries metadata only",
        "Mouse; inspect subseries metadata before any raw/SRA download.",
    ),
    CandidateDataset(
        "gse181279",
        "GSE181279",
        "Peripheral immune plausibility/auxiliary candidate",
        "Homo sapiens",
        "peripheral blood immune single-cell/bulk profiling",
        "peripheral immune plausibility/auxiliary only",
        "series matrix metadata; supplementary MTX/H5/TSV possible",
        "Peripheral blood; not direct brain microglia validation.",
    ),
    CandidateDataset(
        "gse174367",
        "GSE174367",
        "Already-used Morabito external AD microglia context",
        "Homo sapiens",
        "single-cell/nucleus RNA-seq",
        "plausibility/projection only",
        "series matrix metadata; existing local projection artifacts",
        "Already used in v1/v2 context, not clean validation.",
    ),
    CandidateDataset(
        "gse138852",
        "GSE138852",
        "Already-used Grubman external AD microglia context",
        "Homo sapiens",
        "single-cell/nucleus RNA-seq",
        "plausibility/projection only",
        "series matrix metadata; existing local projection artifacts",
        "Already used in v1/v2 context, not clean validation.",
    ),
]


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href and not href.startswith("?") and href not in {"../", "/"}:
            self.links.append(href)


def series_prefix(accession: str) -> str:
    return f"{accession[:-3]}nnn"


def geo_base(accession: str) -> str:
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{series_prefix(accession)}/{accession}"


def url_exists_and_size(url: str) -> tuple[bool, int | None, str]:
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            size = response.headers.get("Content-Length")
            return True, int(size) if size else None, ""
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"


def download_small(url: str, dest: Path, max_mb: int = MAX_METADATA_DOWNLOAD_MB) -> tuple[str, float | None, str]:
    exists, size, err = url_exists_and_size(url)
    if not exists:
        return "not_available", None, err
    size_mb = (size or 0) / 1_000_000
    if size is not None and size_mb > max_mb:
        return "not_downloaded_large_file", size_mb, f"HEAD size {size_mb:.1f} MB exceeds {max_mb} MB limit"
    if dest.exists():
        return "already_downloaded", dest.stat().st_size / 1_000_000, ""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as response, dest.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        return "downloaded", dest.stat().st_size / 1_000_000, ""
    except Exception as exc:
        return "download_failed", size_mb if size is not None else None, f"{type(exc).__name__}: {exc}"


def fetch_supplementary_listing(accession: str) -> tuple[list[str], str]:
    url = f"{geo_base(accession)}/suppl/"
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as response:
            text = response.read().decode("utf-8", errors="replace")
        parser = LinkParser()
        parser.feed(text)
        return sorted(set(parser.links)), ""
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def parse_series_matrix(path: Path) -> dict[str, object]:
    metadata_rows: dict[str, list[str]] = {}
    n_samples = 0
    if not path.exists():
        return {}
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith("!series_matrix_table_begin"):
                break
            if not line.startswith("!Sample_"):
                continue
            parts = line.split("\t")
            key = parts[0].lstrip("!")
            values = [p.strip().strip('"') for p in parts[1:]]
            metadata_rows[key] = values
            n_samples = max(n_samples, len(values))
    keys = list(metadata_rows.keys())
    preview_values = []
    for key in keys[:30]:
        vals = metadata_rows[key][:3]
        preview_values.append(f"{key}={' | '.join(vals)}")
    return {
        "n_rows": len(keys),
        "n_columns": n_samples,
        "metadata_columns_preview": "; ".join(keys[:40]),
        "column_names_preview": "",
        "sample_values_preview": "; ".join(preview_values)[:2000],
        "all_text": " ".join(keys + [v for vals in metadata_rows.values() for v in vals[:10]]).lower(),
    }


def inspect_h5(path: Path) -> dict[str, object]:
    groups: list[str] = []
    shapes: list[str] = []
    try:
        with h5py.File(path, "r") as handle:
            def visitor(name: str, obj) -> None:
                if len(groups) < 80:
                    groups.append(name)
                shape = getattr(obj, "shape", None)
                if shape is not None and len(shapes) < 40:
                    shapes.append(f"{name}:{shape}")
            handle.visititems(visitor)
    except Exception as exc:
        return {"notes": f"H5 inspect failed: {type(exc).__name__}: {exc}"}
    return {
        "n_rows": "",
        "n_columns": "",
        "matrix_shape": "; ".join(shapes[:20]),
        "column_names_preview": "; ".join(groups[:40]),
        "metadata_columns_preview": "",
        "all_text": " ".join(groups + shapes).lower(),
    }


def inspect_table_header(path: Path) -> dict[str, object]:
    sep = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    try:
        df = pd.read_csv(path, sep=sep, nrows=5, low_memory=False)
        n_rows = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace")) - 1
        cols = [str(c) for c in df.columns]
        text = " ".join(cols + df.astype(str).head(3).values.flatten().tolist()).lower()
        return {
            "n_rows": max(n_rows, 0),
            "n_columns": len(cols),
            "matrix_shape": "",
            "column_names_preview": "; ".join(cols[:50]),
            "metadata_columns_preview": "",
            "all_text": text,
        }
    except Exception as exc:
        return {"notes": f"table inspect failed: {type(exc).__name__}: {exc}"}


def candidate_fields(text: str, candidates: list[str]) -> str:
    found = [token for token in candidates if token.lower() in text]
    return "; ".join(found)


def classify_candidates(text: str) -> dict[str, str]:
    return {
        "sample_id_column_candidates": candidate_fields(text, ["geo_accession", "sample", "sample_id", "title", "barcode", "cell"]),
        "donor_id_column_candidates": candidate_fields(text, ["donor", "subject", "individual", "patient", "specimen"]),
        "diagnosis_column_candidates": candidate_fields(text, ["diagnosis", "disease", "condition", "control", "ad", "alzheim"]),
        "cell_type_column_candidates": candidate_fields(text, ["cell type", "cell_type", "cluster", "microglia", "pvm", "myeloid", "immune"]),
        "region_column_candidates": candidate_fields(text, ["region", "brain", "cortex", "hippocampus", "entorhinal", "prefrontal", "mtg"]),
        "sex_column_candidates": candidate_fields(text, ["sex", "gender", "male", "female"]),
        "age_column_candidates": candidate_fields(text, ["age", "development", "months", "years"]),
        "batch_column_candidates": candidate_fields(text, ["batch", "platform", "library", "run", "lane", "chemistry"]),
        "gene_id_column_candidates": candidate_fields(text, ["gene_id", "ensembl", "entrez", "feature id", "features.tsv"]),
        "gene_symbol_column_candidates": candidate_fields(text, ["gene", "symbol", "gene_symbol", "hgnc", "features.tsv"]),
        "pathology_or_stage_column_candidates": candidate_fields(text, ["braak", "cerad", "plaque", "tangle", "amyloid", "abeta", "aβ", "pathology", "stage"]),
    }


def infer_file_type(file_name: str, matrix: bool = False) -> str:
    lower = file_name.lower()
    if "series_matrix" in lower:
        return "series matrix metadata"
    if lower.endswith((".h5", ".h5ad", ".hdf5")):
        return "H5"
    if lower.endswith((".mtx", ".mtx.gz")) or matrix:
        return "MTX/TSV"
    if lower.endswith((".csv", ".csv.gz", ".tsv", ".tsv.gz", ".txt", ".txt.gz")):
        return "CSV/TSV counts or metadata"
    if lower.endswith((".soft", ".soft.gz", ".xml", ".xml.gz")):
        return "SOFT/MINiML metadata"
    if lower.endswith((".sra", ".fastq", ".fastq.gz", ".bam")):
        return "raw sequencing file"
    return "supplementary listing entry"


def accession_local_dir(accession: str) -> Path:
    return SCHEMA_DIR / accession


def series_matrix_url(accession: str) -> str:
    return f"{geo_base(accession)}/matrix/{accession}_series_matrix.txt.gz"


def add_inventory_row(
    rows: list[dict[str, object]],
    dataset: CandidateDataset,
    file_name: str,
    file_type: str,
    download_status: str,
    local_path: Path | None,
    file_size_mb: float | None,
    inspect: dict[str, object] | None = None,
    notes: str = "",
) -> None:
    inspect = inspect or {}
    text = str(inspect.get("all_text", "")).lower()
    field_hits = classify_candidates(text)
    rows.append(
        {
            "dataset_id": dataset.dataset_id,
            "geo_accession": dataset.geo_accession,
            "dataset_name": dataset.dataset_name,
            "organism": dataset.organism,
            "assay_type": dataset.assay_type,
            "expected_role": dataset.expected_role,
            "file_name": file_name,
            "file_type": file_type,
            "download_status": download_status,
            "local_path": "" if local_path is None else local_path.relative_to(ROOT).as_posix(),
            "file_size_mb": "" if file_size_mb is None else round(float(file_size_mb), 4),
            "n_rows": inspect.get("n_rows", ""),
            "n_columns": inspect.get("n_columns", ""),
            "matrix_shape": inspect.get("matrix_shape", ""),
            "column_names_preview": inspect.get("column_names_preview", ""),
            "metadata_columns_preview": inspect.get("metadata_columns_preview", ""),
            **field_hits,
            "notes": " ".join(
                part
                for part in [
                    notes,
                    str(inspect.get("sample_values_preview", ""))[:800],
                    str(inspect.get("notes", "")),
                    dataset.frozen_context,
                ]
                if part
            ),
        }
    )


def build_schema_inventory() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for dataset in DATASETS:
        local_dir = accession_local_dir(dataset.geo_accession)
        local_dir.mkdir(parents=True, exist_ok=True)
        url = series_matrix_url(dataset.geo_accession)
        local_series = local_dir / f"{dataset.geo_accession}_series_matrix.txt.gz"
        status, size_mb, message = download_small(url, local_series)
        inspect: dict[str, object] = {}
        if status in {"downloaded", "already_downloaded"}:
            inspect = parse_series_matrix(local_series)
        add_inventory_row(
            rows,
            dataset,
            file_name=local_series.name,
            file_type="SOFT/MINiML/series matrix metadata",
            download_status=status,
            local_path=local_series if local_series.exists() else None,
            file_size_mb=size_mb,
            inspect=inspect,
            notes=message,
        )

        links, listing_error = fetch_supplementary_listing(dataset.geo_accession)
        if not links:
            add_inventory_row(
                rows,
                dataset,
                file_name="supplementary_listing",
                file_type="supplementary listing",
                download_status="listing_unavailable",
                local_path=None,
                file_size_mb=None,
                inspect={},
                notes=listing_error,
            )
        for link in links[:80]:
            if link.endswith("/"):
                continue
            lower = link.lower()
            file_type = infer_file_type(link)
            if any(lower.endswith(ext) for ext in [".sra", ".fastq", ".fastq.gz", ".bam"]):
                status = "not_downloaded_raw_sequencing"
            else:
                status = "not_downloaded_large_file"
            add_inventory_row(
                rows,
                dataset,
                file_name=link,
                file_type=file_type,
                download_status=status,
                local_path=None,
                file_size_mb=None,
                inspect={},
                notes=f"Supplementary file listed at {geo_base(dataset.geo_accession)}/suppl/{link}; header not downloaded in schema-only stage.",
            )
    return pd.DataFrame(rows)


def bool_hit(series: pd.Series) -> bool:
    return series.astype(str).str.len().gt(0).any()


def build_integration_map(schema: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dataset in DATASETS:
        group = schema[schema["geo_accession"] == dataset.geo_accession]
        text = " ".join(group.astype(str).values.flatten()).lower()
        has_gene = bool_hit(group["gene_symbol_column_candidates"]) or bool_hit(group["gene_id_column_candidates"]) or "features.tsv" in text
        has_sample = bool_hit(group["sample_id_column_candidates"])
        has_donor = bool_hit(group["donor_id_column_candidates"])
        has_cell = bool_hit(group["cell_type_column_candidates"]) or "barcodes" in text or "single" in dataset.assay_type.lower()
        has_pathology = bool_hit(group["pathology_or_stage_column_candidates"]) or "pathology" in text
        is_mouse = "mus musculus" in dataset.organism.lower()

        if dataset.geo_accession in {"GSE157827", "GSE147528"}:
            role = "external_projection_holdout_candidate"
            level = "cell_level"
            branch = "external projection/stress-test branch"
            training = False
            pretraining = False
            aux = False
            holdout = True
            model_selection = False
            risks = "Must remain untouched by training/model selection if used as external holdout."
        elif dataset.geo_accession == "GSE203206":
            role = "bulk_external_stress_test"
            level = "bulk_sample_level"
            branch = "bulk sample-level stress-test branch"
            training = False
            pretraining = False
            aux = False
            holdout = True
            model_selection = False
            risks = "Bulk sample-level data cannot validate cell-level microglia/PVM extraction directly."
        elif dataset.geo_accession == "GSE98969":
            role = "self_supervised_pretraining_candidate"
            level = "cell_level"
            branch = "auxiliary microglia/DAM representation branch"
            training = True
            pretraining = True
            aux = False
            holdout = False
            model_selection = False
            risks = "Mouse-to-human ortholog mapping required; pretraining use forfeits holdout status."
        elif dataset.geo_accession == "GSE127893":
            role = "subseries_review_required"
            level = "unknown"
            branch = "none until subseries reviewed"
            training = False
            pretraining = False
            aux = False
            holdout = False
            model_selection = False
            risks = "Do not download raw/SRA or use before subseries-level review; mouse ortholog mapping likely required."
        elif dataset.geo_accession == "GSE181279":
            role = "peripheral_immune_plausibility"
            level = "cell_level" if has_cell else "bulk_sample_level"
            branch = "peripheral immune plausibility branch"
            training = False
            pretraining = False
            aux = True
            holdout = False
            model_selection = False
            risks = "Peripheral blood is not direct brain microglia validation."
        elif dataset.geo_accession in {"GSE174367", "GSE138852"}:
            role = "plausibility_projection_only"
            level = "cell_level"
            branch = "external plausibility/projection reporting only"
            training = False
            pretraining = False
            aux = False
            holdout = False
            model_selection = False
            risks = "Already used in v1/v2 context; not clean validation."
        else:
            role = "do_not_use_until_reviewed"
            level = "unknown"
            branch = "none"
            training = False
            pretraining = False
            aux = False
            holdout = False
            model_selection = False
            risks = "Unknown."

        preprocessing = []
        if has_gene:
            preprocessing.append("map gene identifiers/symbols to 2,957-gene universe")
        if is_mouse:
            preprocessing.append("mouse-to-human ortholog mapping")
        if has_cell:
            preprocessing.append("cell-level QC and microglia/PVM extraction if labels support it")
        if has_donor:
            preprocessing.append("donor/sample harmonization")
        if has_sample and not has_donor:
            preprocessing.append("sample-level harmonization; donor mapping may be unavailable")
        if has_pathology:
            preprocessing.append("audit pathology/stage fields for compatibility; do not use for model selection if holdout")
        rows.append(
            {
                "dataset_id": dataset.dataset_id,
                "geo_accession": dataset.geo_accession,
                "recommended_integration_role": role,
                "integration_level": level,
                "compatible_v3_branch": branch,
                "can_make_donor_pseudobulk": bool(has_donor and has_gene and has_cell),
                "can_extract_microglia_or_pvm": bool(has_cell and ("microglia" in text or "myeloid" in text or dataset.geo_accession in {"GSE174367", "GSE138852", "GSE98969"})),
                "can_map_to_2957_gene_universe": bool(has_gene),
                "compatible_with_main_pathology_targets": bool(has_pathology and not is_mouse and dataset.geo_accession not in {"GSE181279", "GSE174367", "GSE138852"}),
                "compatible_with_auxiliary_labels": bool(has_cell or "dam" in text or dataset.geo_accession in {"GSE98969", "GSE181279"}),
                "allowed_for_training": training,
                "allowed_for_pretraining": pretraining,
                "allowed_for_auxiliary_supervision": aux,
                "reserved_for_external_holdout": holdout,
                "allowed_for_model_selection": model_selection,
                "main_risks": risks,
                "required_preprocessing": "; ".join(preprocessing) if preprocessing else "metadata review required",
                "notes": dataset.frozen_context,
            }
        )
    return pd.DataFrame(rows)


def write_report(schema: pd.DataFrame, imap: pd.DataFrame) -> None:
    summary_lines = []
    for row in imap.itertuples():
        files = schema[schema["geo_accession"] == row.geo_accession]
        downloaded = files[files["download_status"].isin(["downloaded", "already_downloaded"])]["file_name"].tolist()
        summary_lines.append(
            f"- `{row.geo_accession}` (`{row.dataset_id}`): role=`{row.recommended_integration_role}`, level=`{row.integration_level}`, downloaded={downloaded if downloaded else 'none'}, holdout={row.reserved_for_external_holdout}"
        )

    metadata_lines = []
    for accession, group in schema.groupby("geo_accession", sort=True):
        candidates = {
            "sample": sorted(set(x for x in group["sample_id_column_candidates"].dropna().astype(str) if x)),
            "donor": sorted(set(x for x in group["donor_id_column_candidates"].dropna().astype(str) if x)),
            "diagnosis": sorted(set(x for x in group["diagnosis_column_candidates"].dropna().astype(str) if x)),
            "cell_type": sorted(set(x for x in group["cell_type_column_candidates"].dropna().astype(str) if x)),
            "gene": sorted(set(x for x in group["gene_symbol_column_candidates"].dropna().astype(str) if x)),
        }
        metadata_lines.append(f"- `{accession}`: {candidates}")

    pseudobulk = imap[imap["can_make_donor_pseudobulk"]]["geo_accession"].tolist()
    microglia = imap[imap["can_extract_microglia_or_pvm"]]["geo_accession"].tolist()
    holdouts = imap[imap["reserved_for_external_holdout"]]["geo_accession"].tolist()
    pretraining = imap[imap["allowed_for_pretraining"]]["geo_accession"].tolist()
    aux = imap[imap["allowed_for_auxiliary_supervision"]]["geo_accession"].tolist()
    review = imap[imap["recommended_integration_role"].isin(["subseries_review_required", "do_not_use_until_reviewed"])]["geo_accession"].tolist()

    REPORT_OUT.write_text(
        "\n".join(
            [
                "# v3 public external dataset schema audit v1",
                "",
                "## 1. Executive summary",
                "",
                "Stage 26B inspected small GEO series-matrix metadata and supplementary file listings for candidate public datasets. No SRA, FASTQ, BAM, or large raw sequencing payloads were downloaded. This is not external validation and does not alter evidence levels.",
                "",
                "## 2. Dataset-by-dataset schema summary",
                "",
                *summary_lines,
                "",
                "## 3. Metadata columns found",
                "",
                *metadata_lines,
                "",
                "## 4. Gene identifier compatibility",
                "",
                "Gene identifier compatibility is inferred from downloaded metadata and supplementary filenames only. Full count matrices may still require features.tsv/H5 inspection in a future approved integration stage.",
                "",
                "## 5. Donor/sample/cell mapping compatibility",
                "",
                "Series-matrix metadata commonly exposes sample-level fields. Donor-level harmonization must be audited before any dataset is used for training or final reporting.",
                "",
                "## 6. Which datasets can support pseudobulk construction",
                "",
                f"Candidates: {', '.join(pseudobulk) if pseudobulk else 'none confirmed from schema metadata alone'}",
                "",
                "## 7. Which datasets can support microglia/PVM extraction",
                "",
                f"Candidates: {', '.join(microglia) if microglia else 'none confirmed'}",
                "",
                "## 8. Which datasets can support external projection/stress testing",
                "",
                f"Holdout/stress-test candidates: {', '.join(holdouts) if holdouts else 'none'}",
                "GSE157827 and GSE147528 remain external holdout candidates unless explicitly reclassified. GSE203206 is a bulk sample-level stress-test candidate.",
                "",
                "## 9. Which datasets can support pretraining or auxiliary supervision",
                "",
                f"Pretraining candidates: {', '.join(pretraining) if pretraining else 'none'}",
                f"Auxiliary supervision/plausibility candidates: {', '.join(aux) if aux else 'none'}",
                "",
                "## 10. Which datasets should not be used until reviewed",
                "",
                f"Review-required candidates: {', '.join(review) if review else 'none'}",
                "GSE127893 must undergo subseries review before any raw/SRA or large supplemental download.",
                "",
                "## 11. Recommended next integration stage",
                "",
                "- For holdout candidates, freeze them out of training and model selection.",
                "- For any approved integration dataset, download processed matrices only, inspect features/barcodes/matrix dimensions, and map genes to the 2,957-gene universe.",
                "- For mouse datasets, add mouse-to-human ortholog mapping before use.",
                "- For GSE174367/GSE138852, keep use limited to plausibility/projection context because they were already used in v1/v2.",
                "",
                "No v3 training, graph neural model, model selection, evidence change, or external validation was run.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    schema = build_schema_inventory()
    imap = build_integration_map(schema)
    schema.to_csv(SCHEMA_OUT, index=False)
    imap.to_csv(MAP_OUT, index=False)
    write_report(schema, imap)
    print(f"Wrote {SCHEMA_OUT}")
    print(f"Wrote {MAP_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
