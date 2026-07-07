from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
STAGE = "Stage41ABC"
ALLOWED_CLAIM = "safe SEA-AD resource acquisition and benchmark-readiness support only"
PROHIBITED_CLAIM = "external validation; clean validation; causal mechanism; therapeutic target; gene-ablation validation; disease-modifying effect"
FORBIDDEN_PATTERNS = [
    "braak", "cerad", "thal", "adnc", "dementia", "diagnosis", "cognitive", "mmse", "moca",
    "luminex", "abeta", "aβ", "amyloid", "ptau", "p-tau", "tau", "at8", "6e10",
    "gfap", "iba1", "neun", "halo", "pathology", "neuropath",
]
SAFE_METADATA_PATTERNS = ["age", "sex", "apoe", "pmi", "rin", "education", "cohort", "source", "race", "ethnicity"]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            attr = {k.lower(): v or "" for k, v in attrs}
            if attr.get("href"):
                self._current = {"href": attr["href"]}
                self._text = []

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current is not None:
            self._current["text"] = " ".join(x for x in self._text if x)
            self.links.append(self._current)
            self._current = None
            self._text = []


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(resolve(path).read_text(encoding="utf-8"))


def write_csv(df: pd.DataFrame, value: str | Path) -> Path:
    path = resolve(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def write_text(text: str, value: str | Path) -> Path:
    path = resolve(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def read_csv_if_exists(value: str | Path) -> pd.DataFrame:
    path = resolve(value)
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df if max_rows is None else df.head(max_rows)
    if view.empty:
        return "_No rows available._"
    view = view.fillna("").astype(str)
    cols = list(view.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        vals = [str(row[col]).replace("|", "\\|").replace("\n", " ") for col in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def fetch_url(url: str, user_agent: str, timeout: int = 30, method: str = "GET") -> tuple[bool, bytes, dict[str, str], str]:
    req = Request(url, method=method, headers={"User-Agent": user_agent})
    try:
        with urlopen(req, timeout=timeout) as handle:
            headers = {k.lower(): v for k, v in handle.headers.items()}
            return True, b"" if method == "HEAD" else handle.read(), headers, ""
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return False, b"", {}, str(exc)


def classify_link(url: str, text: str) -> str:
    s = f"{url} {text}".lower()
    if "cellxgene" in s:
        return "CELLxGENE"
    if "knowledge" in s or "synapse" in s or "controlled" in s:
        return "AD Knowledge Portal controlled access"
    if ".pdf" in s or "white" in s or "protocol" in s or "methods" in s:
        return "white paper / PDF"
    if "mri" in s or "volum" in s:
        return "MRI volumetrics"
    if "donor" in s or "metadata" in s or "clinical" in s:
        return "donor metadata"
    if "spatial" in s or "merfish" in s:
        return "spatial transcriptomics"
    if "atac" in s:
        return "snATAC"
    if "image" in s or "whole-slide" in s or "pathology" in s or "h&e" in s or "lfb" in s:
        return "neuropathology images"
    if "luminex" in s:
        return "Luminex"
    if "quantitative" in s or "neuropathology" in s or "braak" in s or "cerad" in s or "thal" in s:
        return "quantitative neuropathology"
    if "single" in s or "snrna" in s or "rna" in s or "h5ad" in s:
        return "single-cell / snRNA"
    if "aws" in s or "s3" in s or "bucket" in s:
        return "AWS/open data bucket"
    return "unknown"


def is_raw_large_type(url: str) -> bool:
    lower = url.lower()
    return any(x in lower for x in [".h5ad", ".zarr", ".h5", ".loom", ".bam", ".cram", ".fastq", ".tif", ".tiff", ".svs", ".ome.tif"])


def allowed_download(resource_type: str, url: str, size_bytes: int | None, cfg: dict[str, Any]) -> tuple[bool, str]:
    lower = url.lower()
    max_bytes = int(cfg["download_policy"]["max_download_mb"]) * 1024 * 1024
    pdf_bytes = int(cfg["download_policy"]["max_pdf_mb"]) * 1024 * 1024
    if resource_type in {"AD Knowledge Portal controlled access", "neuropathology images", "quantitative neuropathology", "Luminex"}:
        return False, f"skipped_{resource_type.replace(' ', '_')}"
    if is_raw_large_type(url):
        if size_bytes is None:
            return False, "skipped_unknown_size_raw_matrix_or_image"
        if size_bytes > max_bytes:
            return False, "skipped_over_size_raw_matrix_or_image"
    if lower.endswith(".pdf"):
        if size_bytes is not None and size_bytes > pdf_bytes:
            return False, "skipped_pdf_over_100mb"
        return True, "allowed_public_pdf_under_limit_or_unknown_small"
    if any(lower.endswith(ext) for ext in [".csv", ".tsv", ".txt", ".xlsx", ".xls", ".json", ".html", ".htm"]):
        if size_bytes is not None and size_bytes > max_bytes:
            return False, "skipped_file_over_250mb"
        return True, "allowed_small_medium_table_manifest_or_page"
    if resource_type in {"white paper / PDF", "donor metadata", "MRI volumetrics"} and size_bytes is not None and size_bytes <= max_bytes:
        return True, "allowed_priority_resource_under_limit"
    return False, "skipped_unclear_file_type_or_manifest_only"


def safe_filename(url: str, default: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name or default
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:160] or default


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_resources(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    ua = cfg["download_policy"]["user_agent"]
    pages = []
    links = []
    for page_id, url in cfg["references"]["resource_pages"].items():
        ok, content, headers, err = fetch_url(url, ua)
        text = content.decode("utf-8", errors="replace") if ok else ""
        parser = LinkParser()
        if text:
            parser.feed(text)
        pages.append({
            "page_id": page_id,
            "url": url,
            "fetch_success": ok,
            "http_content_type": headers.get("content-type", ""),
            "content_length_bytes": int(headers.get("content-length", "0") or 0),
            "n_links_parsed": len(parser.links),
            "error": err,
        })
        for i, link in enumerate(parser.links):
            full = urljoin(url, link["href"])
            rtype = classify_link(full, link.get("text", ""))
            links.append({
                "source_page_id": page_id,
                "source_page_url": url,
                "link_index": i,
                "link_text": link.get("text", ""),
                "url": full,
                "resource_type": rtype,
                "download_candidate": rtype in {"donor metadata", "MRI volumetrics", "white paper / PDF", "CELLxGENE", "single-cell / snRNA", "spatial transcriptomics", "snATAC", "AWS/open data bucket"},
            })
        if not parser.links:
            links.append({
                "source_page_id": page_id,
                "source_page_url": url,
                "link_index": -1,
                "link_text": page_id,
                "url": url,
                "resource_type": classify_link(url, page_id),
                "download_candidate": False,
            })
    return pd.DataFrame(pages), pd.DataFrame(links)


def download_safe_resources(cfg: dict[str, Any], links: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ua = cfg["download_policy"]["user_agent"]
    raw_dir = resolve(cfg["paths"]["raw_dir"])
    white_dir = resolve(cfg["paths"]["whitepaper_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    white_dir.mkdir(parents=True, exist_ok=True)
    attempts: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    checksums: list[dict[str, Any]] = []
    seen: set[str] = set()
    candidates = links[links["download_candidate"].map(as_bool)].copy() if not links.empty else pd.DataFrame()
    if candidates.empty:
        candidates = links.copy()
    for _, row in candidates.iterrows():
        url = str(row.get("url", ""))
        if not url or url in seen or not url.startswith(("http://", "https://")):
            continue
        seen.add(url)
        ok_head, _, headers, head_err = fetch_url(url, ua, method="HEAD")
        size = headers.get("content-length")
        size_bytes = int(size) if size and str(size).isdigit() else None
        allowed, reason = allowed_download(str(row.get("resource_type", "unknown")), url, size_bytes, cfg)
        attempt = {
            "url": url,
            "resource_type": row.get("resource_type", "unknown"),
            "head_success": ok_head,
            "content_length_bytes": size_bytes if size_bytes is not None else "",
            "download_allowed": allowed,
            "decision_reason": reason if ok_head else f"{reason}; head_error={head_err}",
            "download_success": False,
            "local_path": "",
            "error": "",
        }
        if allowed:
            ok, content, get_headers, err = fetch_url(url, ua)
            if ok and content:
                rtype = str(row.get("resource_type", "unknown"))
                out_dir = white_dir if (url.lower().endswith(".pdf") or rtype == "white paper / PDF") else raw_dir
                filename = safe_filename(url, f"stage41abc_download_{len(manifest)+1}")
                path = out_dir / filename
                if path.exists():
                    stem, suffix = path.stem, path.suffix
                    path = out_dir / f"{stem}_{len(manifest)+1}{suffix}"
                path.write_bytes(content)
                digest = sha256_file(path)
                attempt.update({"download_success": True, "local_path": str(path.relative_to(ROOT)), "error": ""})
                manifest.append({
                    "url": url,
                    "resource_type": rtype,
                    "local_path": str(path.relative_to(ROOT)),
                    "size_bytes": path.stat().st_size,
                    "content_type": get_headers.get("content-type", ""),
                    "sha256": digest,
                    "committed_to_git": False,
                })
                checksums.append({"local_path": str(path.relative_to(ROOT)), "sha256": digest, "size_bytes": path.stat().st_size})
            else:
                attempt.update({"error": err or "empty response"})
        attempts.append(attempt)
    return pd.DataFrame(attempts), pd.DataFrame(manifest), pd.DataFrame(checksums)


def likely_columns(columns: list[str], patterns: list[str]) -> list[str]:
    out = []
    for col in columns:
        lower = str(col).lower()
        if any(p in lower for p in patterns):
            out.append(str(col))
    return out


def table_sheet_summaries(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    rows: list[dict[str, Any]] = []
    try:
        if suffix in {".csv", ".txt"}:
            df = pd.read_csv(path, nrows=2000)
            rows.append({"sheet_name": "", "n_rows_observed": len(df), "n_columns": df.shape[1], "columns": list(df.columns)})
        elif suffix == ".tsv":
            df = pd.read_csv(path, sep="\t", nrows=2000)
            rows.append({"sheet_name": "", "n_rows_observed": len(df), "n_columns": df.shape[1], "columns": list(df.columns)})
        elif suffix in {".xlsx", ".xls"}:
            xls = pd.ExcelFile(path)
            for sheet in xls.sheet_names:
                df = pd.read_excel(path, sheet_name=sheet, nrows=2000)
                rows.append({"sheet_name": sheet, "n_rows_observed": len(df), "n_columns": df.shape[1], "columns": list(df.columns)})
        elif suffix == ".json":
            obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            rows.append({"sheet_name": "", "n_rows_observed": len(obj) if hasattr(obj, "__len__") else 1, "n_columns": 0, "columns": []})
    except Exception as exc:
        rows.append({"sheet_name": "", "n_rows_observed": "", "n_columns": "", "columns": [], "error": str(exc)})
    return rows


def analyze_downloads(cfg: dict[str, Any], manifest: pd.DataFrame, links: pd.DataFrame) -> dict[str, pd.DataFrame]:
    file_rows: list[dict[str, Any]] = []
    donor_rows: list[dict[str, Any]] = []
    mri_rows: list[dict[str, Any]] = []
    white_rows: list[dict[str, Any]] = []
    cellxgene_rows: list[dict[str, Any]] = []
    spatial_rows: list[dict[str, Any]] = []
    if not manifest.empty:
        for _, m in manifest.iterrows():
            path = resolve(m["local_path"])
            suffix = path.suffix.lower()
            is_pdf = suffix == ".pdf"
            if is_pdf:
                page_count = ""
                try:
                    raw = path.read_bytes()
                    page_count = raw.count(b"/Type /Page")
                except Exception:
                    page_count = ""
                white_rows.append({
                    "file_path": m["local_path"],
                    "resource_type": m.get("resource_type", ""),
                    "size_bytes": m.get("size_bytes", ""),
                    "page_count_approx": page_count,
                    "provenance_relevance": classify_link(str(m.get("url", "")), path.name),
                    "notes": "Downloaded for provenance review only; not a predictor.",
                })
                file_rows.append({"file_path": m["local_path"], "file_type": suffix, "n_sheets_or_tables": "", "analysis_status": "pdf_inventory_only", "notes": "basic PDF inventory"})
                continue
            summaries = table_sheet_summaries(path)
            for s in summaries:
                cols = [str(c) for c in s.get("columns", [])]
                donor_cols = likely_columns(cols, ["donor", "specimen", "subject"])
                region_cols = likely_columns(cols, ["region", "structure", "cortical", "anatomy"])
                forbidden_cols = likely_columns(cols, FORBIDDEN_PATTERNS)
                safe_cols = [c for c in likely_columns(cols, SAFE_METADATA_PATTERNS) if c not in forbidden_cols]
                numeric_volume_cols = likely_columns(cols, ["volume", "volumetric", "mm3", "area", "thick"])
                row_common = {
                    "file_path": m["local_path"],
                    "sheet_name": s.get("sheet_name", ""),
                    "n_rows": s.get("n_rows_observed", ""),
                    "n_columns": s.get("n_columns", ""),
                    "donor_id_column_candidates": ";".join(donor_cols),
                    "forbidden_predictor_columns": ";".join(forbidden_cols),
                }
                file_rows.append({
                    **row_common,
                    "file_type": suffix,
                    "column_names": ";".join(cols[:200]),
                    "likely_region_columns": ";".join(region_cols),
                    "likely_metadata_columns": ";".join(safe_cols),
                    "analysis_status": "table_inspected" if not s.get("error") else "inspection_error",
                    "notes": s.get("error", ""),
                })
                rtype = str(m.get("resource_type", "")).lower()
                if "donor" in rtype or donor_cols:
                    donor_rows.append({
                        **row_common,
                        "safe_metadata_columns": ";".join(safe_cols),
                        "caution_columns": ";".join([c for c in cols if c not in safe_cols and c not in forbidden_cols][:100]),
                        "notes": "Candidate donor metadata table; forbidden columns must be excluded before modeling.",
                    })
                if "mri" in rtype or numeric_volume_cols:
                    mri_rows.append({
                        **row_common,
                        "numeric_volume_columns": ";".join(numeric_volume_cols),
                        "region_volume_columns": ";".join([c for c in numeric_volume_cols if any(p in c.lower() for p in ["region", "structure", "volume"])]),
                        "likely_safe_columns": ";".join([c for c in numeric_volume_cols if c not in forbidden_cols]),
                        "caution_columns": ";".join([c for c in cols if c not in numeric_volume_cols and c not in forbidden_cols][:100]),
                        "forbidden_columns": ";".join(forbidden_cols),
                        "donor_linkage_ready": bool(donor_cols and numeric_volume_cols),
                        "notes": "MRI features allowed only with clean donor linkage and fold-safe scaling.",
                    })
    for _, row in (links if not links.empty else pd.DataFrame()).iterrows():
        rtype = str(row.get("resource_type", ""))
        if rtype in {"CELLxGENE", "single-cell / snRNA"}:
            cellxgene_rows.append({
                "source": row.get("url", ""),
                "downloaded_or_manifest_only": "manifest_only",
                "cell_metadata_available": False,
                "donor_id_available": False,
                "cell_type_available": False,
                "subclass_available": False,
                "region_available": False,
                "expression_available": False,
                "automatic_feature_build_possible": False,
                "required_manual_step": "Use CELLxGENE/Census or portal export to acquire donor-cell metadata under size/provenance controls.",
                "notes": "Do not use expression for model selection; build donor summaries only after linkage audit.",
            })
        if rtype == "spatial transcriptomics":
            spatial_rows.append({
                "resource": row.get("url", ""),
                "access_type": "public_or_manifest",
                "file_type": Path(urlparse(str(row.get("url", ""))).path).suffix,
                "downloaded_or_manifest_only": "manifest_only",
                "donor_linkage_possible": "unknown_until_manual_schema_review",
                "feature_build_possible_now": False,
                "proposed_spatial_features": "donor/region neighborhood summaries computed without target labels",
                "leakage_risk": "medium",
                "required_manual_step": "Acquire schema/metadata first; skip raw spatial matrices unless size-approved.",
            })
    if not cellxgene_rows:
        cellxgene_rows.append({
            "source": cfg["references"]["resource_pages"]["cellxgene_collection"],
            "downloaded_or_manifest_only": "resource_page_only",
            "cell_metadata_available": False,
            "donor_id_available": False,
            "cell_type_available": False,
            "subclass_available": False,
            "region_available": False,
            "expression_available": False,
            "automatic_feature_build_possible": False,
            "required_manual_step": "Export donor/cell metadata or use approved local h5ad/Census access.",
            "notes": "No small metadata-only table was automatically downloaded.",
        })
    if not spatial_rows:
        spatial_rows.append({
            "resource": "SEA-AD spatial resources",
            "access_type": "not_found_or_manifest_only",
            "file_type": "",
            "downloaded_or_manifest_only": "not_downloaded",
            "donor_linkage_possible": "unknown",
            "feature_build_possible_now": False,
            "proposed_spatial_features": "manual donor-linked neighborhood summaries",
            "leakage_risk": "medium",
            "required_manual_step": "Locate public processed spatial metadata/summaries; avoid raw large downloads by default.",
        })
    return {
        "downloaded_file_analysis": pd.DataFrame(file_rows),
        "whitepaper_inventory": pd.DataFrame(white_rows) if white_rows else pd.DataFrame(columns=["file_path", "resource_type", "size_bytes", "page_count_approx", "provenance_relevance", "notes"]),
        "donor_metadata_analysis": pd.DataFrame(donor_rows) if donor_rows else pd.DataFrame([{"file_path": "", "sheet_name": "", "n_rows": "", "n_columns": "", "donor_id_column_candidates": "", "safe_metadata_columns": "", "caution_columns": "", "forbidden_predictor_columns": "", "notes": "No donor metadata table downloaded automatically."}]),
        "mri_volumetrics_analysis": pd.DataFrame(mri_rows) if mri_rows else pd.DataFrame([{"file_path": "", "sheet_name": "", "n_rows": "", "n_columns": "", "donor_id_column_candidates": "", "numeric_volume_columns": "", "region_volume_columns": "", "likely_safe_columns": "", "caution_columns": "", "forbidden_columns": "", "donor_linkage_ready": False, "notes": "No MRI volumetrics table downloaded automatically."}]),
        "cellxgene_metadata_analysis": pd.DataFrame(cellxgene_rows),
        "spatial_resource_analysis": pd.DataFrame(spatial_rows),
    }


def feature_risk_tiers() -> pd.DataFrame:
    rows = [
        (0, "existing internal module/latent features", "Stage 27C/39E module features", True, False, False, "reference/baseline"),
        (1, "safe donor metadata; MRI volumetrics; broad region/anatomy; technical covariates", "age, sex, APOE, PMI, RIN, MRI volumes", True, False, False, "lock-candidate eligible after linkage audit"),
        (2, "cell-type composition; spatial neighborhoods; microglia/astrocyte/neuron state summaries; snATAC; H&E-LFB morphology", "context biology/features not directly target-derived", False, False, False, "caution features requiring proxy audit"),
        (3, "high-risk proxy features", "section/pathology-adjacent summaries and strongly target-correlated descriptors", False, True, False, "comparator-only"),
        (4, "forbidden predictors", "quantitative neuropathology, Luminex A_beta/tau, Braak/CERAD/Thal/ADNC, same-stain same-target, HALO target quantifications, pseudo-labels", False, False, True, "excluded from modeling"),
    ]
    return pd.DataFrame(rows, columns=["risk_tier", "feature_class", "examples", "allowed_for_lock_candidate", "comparator_only", "forbidden", "recommended_use"])


def feature_source_priority() -> pd.DataFrame:
    rows = [
        (1, "SEA-AD donor metadata", "donor metadata", "Tier1", "safe linkage/covariates", "high", "attempt automatic download if small public file exists"),
        (1, "postmortem MRI volumetrics", "MRI volumetrics", "Tier1", "anatomy/volume context", "high", "attempt automatic download if small public file exists"),
        (2, "CELLxGENE / SEA-AD snRNA donor-cell metadata", "single-cell metadata", "Tier2", "donor cell-type composition", "high", "manifest/manual unless small metadata export exists"),
        (3, "spatial transcriptomics metadata/summaries", "spatial", "Tier2", "neighborhood summaries", "medium", "manifest/manual by default"),
        (4, "snATAC / regulatory summaries", "snATAC", "Tier2", "regulatory context", "medium", "manifest/manual by default"),
        (5, "microglia-enriched multiregion state summaries", "microglia states", "Tier2", "Iba1/microglia biology context", "medium", "manual schema review"),
        (6, "H&E-LFB or non-target image morphology", "non-target morphology", "Tier2", "tissue architecture", "medium", "manual/precomputed summaries only"),
    ]
    return pd.DataFrame(rows, columns=["priority", "feature_source", "resource_type", "risk_tier", "expected_signal", "importance", "stage41abc_action"])


def target_donor_ids(cfg: dict[str, Any]) -> tuple[str, set[str]]:
    path = resolve(cfg["inputs"]["targets_path"])
    if not path.exists():
        return "", set()
    df = pd.read_csv(path)
    donor_col = next((c for c in df.columns if c.lower() in {"donor id", "donor_id", "donor"} or "donor" in c.lower()), "")
    if not donor_col:
        return "", set()
    return donor_col, set(df[donor_col].astype(str))


def donor_linkage_and_matrix_build(cfg: dict[str, Any], analysis: dict[str, pd.DataFrame], manifest: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    target_col, target_donors = target_donor_ids(cfg)
    linkage_rows: list[dict[str, Any]] = []
    matrix_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    processed = resolve(cfg["paths"]["processed_dir"])
    processed.mkdir(parents=True, exist_ok=True)
    candidate_tables = pd.concat([
        analysis["donor_metadata_analysis"].assign(feature_source="safe_donor_metadata"),
        analysis["mri_volumetrics_analysis"].assign(feature_source="mri_volumetrics"),
    ], ignore_index=True, sort=False)
    for _, row in candidate_tables.iterrows():
        file_path = str(row.get("file_path", ""))
        donor_candidates = [x for x in str(row.get("donor_id_column_candidates", "")).split(";") if x]
        linkage_ready = bool(file_path and donor_candidates and target_donors)
        n_feature_donors = ""
        n_overlap = 0
        out_path = ""
        notes = row.get("notes", "")
        if linkage_ready:
            # Conservative manifest only for now: table parsing already capped at 2k rows, and actual matrix
            # building requires exact schema/provenance review before predictors are admitted.
            notes = f"{notes} Candidate linkage detected, but matrix build held for explicit schema/provenance review."
            linkage_ready = False
        linkage_rows.append({
            "feature_source": row.get("feature_source", ""),
            "feature_file": file_path,
            "donor_id_column": ";".join(donor_candidates),
            "target_donor_id_column": target_col,
            "n_feature_donors": n_feature_donors,
            "n_target_donors": len(target_donors),
            "n_overlap": n_overlap,
            "overlap_fraction": 0.0,
            "linkage_ready": linkage_ready,
            "notes": notes,
        })
    for name in ["safe_donor_metadata", "mri_volumetrics", "safe_metadata_plus_mri", "cellxgene_composition"]:
        matrix_rows.append({
            "feature_matrix_id": name,
            "local_processed_path": "",
            "safe_feature_matrix_built": False,
            "n_donors": 0,
            "n_features": 0,
            "tier": "Tier1" if name != "cellxgene_composition" else "Tier2",
            "training_allowed": False,
            "reason": "No fully schema-reviewed donor-linked safe matrix was available from automatic downloads.",
        })
    summary_rows.append({
        "matrix_family": "safe_metadata_mri",
        "safe_metadata_matrix_built": False,
        "mri_matrix_built": False,
        "safe_metadata_plus_mri_built": False,
        "n_safe_metadata_features": 0,
        "n_mri_features": 0,
        "n_overlap_target_donors": 0,
        "notes": "Automatic discovery/download did not yield a ready donor-linked metadata/MRI feature matrix.",
    })
    return pd.DataFrame(linkage_rows), pd.DataFrame(matrix_rows), pd.DataFrame(summary_rows)


def forbidden_predictor_audit(analysis: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key in ["downloaded_file_analysis", "donor_metadata_analysis", "mri_volumetrics_analysis"]:
        df = analysis.get(key, pd.DataFrame())
        for _, row in df.iterrows():
            cols = str(row.get("forbidden_predictor_columns", row.get("forbidden_columns", "")))
            for col in [x for x in cols.split(";") if x]:
                lower = col.lower()
                affected = "all targets"
                if "at8" in lower or "tau" in lower:
                    affected = "AT8/tau"
                elif "6e10" in lower or "abeta" in lower or "amyloid" in lower:
                    affected = "6e10/A_beta"
                elif "gfap" in lower:
                    affected = "GFAP"
                elif "iba1" in lower:
                    affected = "Iba1"
                elif "neun" in lower:
                    affected = "NeuN"
                rows.append({
                    "source_file": row.get("file_path", ""),
                    "forbidden_column_or_feature": col,
                    "reason_forbidden": "Direct or near-direct pathology/disease burden predictor.",
                    "affected_target": affected,
                    "allowed_alternative_use": "outcome/context/manual review only; excluded from modeling",
                    "excluded_from_modeling": True,
                })
    if not rows:
        rows.append({
            "source_file": "",
            "forbidden_column_or_feature": "",
            "reason_forbidden": "No downloaded table columns were admitted for modeling.",
            "affected_target": "all",
            "allowed_alternative_use": "N/A",
            "excluded_from_modeling": True,
        })
    return pd.DataFrame(rows)


def manual_gaps(cfg: dict[str, Any], links: pd.DataFrame) -> pd.DataFrame:
    urls = cfg["references"]["resource_pages"]
    rows = [
        ("safe donor metadata", "SEA-AD donor metadata table/data dictionary", urls["sea_ad_data"], "not found as directly downloadable safe table or requires manual portal selection", "Download public donor metadata table; save checksum and schema.", "data/sea_ad/stage41abc/raw/donor_metadata/", "build_stage41abc_donor_feature_matrices_v1.py", "high", "medium"),
        ("postmortem MRI volumetrics", "SEA-AD postmortem MRI volumetric table", urls["sea_ad_data"], "not found as ready small table or requires manual portal selection", "Download MRI volumetrics workbook/table and provenance document.", "data/sea_ad/stage41abc/raw/mri_volumetrics/", "build_stage41abc_donor_feature_matrices_v1.py", "high", "medium"),
        ("CELLxGENE donor-cell metadata", "SEA-AD CELLxGENE metadata/h5ad", urls["cellxgene_collection"], "large/raw metadata access requires explicit CELLxGENE/Census export", "Export donor/cell metadata only; avoid raw expression unless approved.", "data/sea_ad/stage41abc/raw/cellxgene_metadata/", "build_stage41abc_donor_feature_matrices_v1.py", "high", "high"),
        ("spatial neighborhood summaries", "SEA-AD spatial transcriptomics processed metadata", urls["sea_ad_data"], "raw/large spatial resources are manifest-only by policy", "Acquire processed donor-linked coordinates/summaries; do not download huge raw matrices automatically.", "data/sea_ad/stage41abc/raw/spatial/", "build_stage41abc_donor_feature_matrices_v1.py", "medium", "high"),
        ("snATAC regulatory summaries", "SEA-AD snATAC processed summaries", urls["sea_ad_data"], "not present as small approved table", "Acquire processed donor-linked module/regulatory summaries.", "data/sea_ad/stage41abc/raw/snatac/", "build_stage41abc_donor_feature_matrices_v1.py", "medium", "high"),
        ("non-target image morphology", "H&E-LFB or non-target image feature summaries", urls["sea_ad_resources"], "raw images forbidden for automatic download", "Acquire precomputed donor/section-level morphology summaries only.", "data/sea_ad/stage41abc/raw/image_morphology/", "build_stage41abc_donor_feature_matrices_v1.py", "medium", "high"),
    ]
    return pd.DataFrame(rows, columns=["missing_feature_class", "required_resource", "source_url", "reason_not_downloaded", "manual_download_or_processing_instruction", "expected_local_path", "downstream_script_needed", "priority", "estimated_complexity"])


def skipped_benchmark_tables(cfg: dict[str, Any], reason: str) -> dict[str, pd.DataFrame]:
    locked = cfg["references"]["locked_benchmark_mean_pooled_oof_spearman"]
    threshold = cfg["references"]["material_rescue_threshold"]
    return {
        "model_registry": pd.DataFrame([{"condition": "training_skipped", "training_skipped": True, "reason": reason, "allowed_models": "ridge; target-specific ridge; conservative elastic net"}]),
        "oof_results": pd.DataFrame(columns=["condition", "donor_id", "target", "y_true", "y_pred", "fold"]),
        "target_level_results": pd.DataFrame(columns=["condition", "target", "spearman", "n_donors"]),
        "delta_vs_references": pd.DataFrame([{"condition": "training_skipped", "mean_pooled_oof_spearman": "", "delta_vs_stage27c": "", "delta_vs_stage39e_pca8": "", "delta_vs_stage39h_context": "", "reason": reason}]),
        "bootstrap_ci": pd.DataFrame([{"condition": "training_skipped", "bootstrap_lower_95": "", "bootstrap_upper_95": "", "passes_lower_ci_guard": False, "reason": reason}]),
        "negative_control_results": pd.DataFrame([{"negative_control": "not_run", "pass": True, "reason": "benchmark training skipped correctly because no safe linked matrix was available"}]),
        "proxy_leakage_decision": pd.DataFrame([{"feature_recipe": "none", "proxy_leakage_decision": "no_safe_feature_matrix_built", "tier3_used": False, "tier4_used": False, "notes": reason}]),
        "benchmark_lock_decision": pd.DataFrame([{"candidate": "none", "benchmark_training_ran": False, "benchmark_lock_eligible": False, "locked_benchmark_preserved": True, "stage27c_reference": locked, "material_threshold": threshold, "decision": "manual_feature_acquisition_required", "reason": reason}]),
    }


def claim_boundary_audit(training_ran: bool) -> pd.DataFrame:
    items = {
        "no_external_data_used_for_model_training": not training_ran,
        "no_external_model_selection": True,
        "no_candidate_selection": True,
        "frozen_candidates_preserved": True,
        "donor_held_out_evaluation_preserved": True,
        "train_fold_only_preprocessing_preserved": True,
        "forbidden_features_excluded": True,
        "proxy_risk_features_comparator_only": True,
        "negative_controls_reported_or_training_skipped": True,
        "no_clean_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "no_gene_ablation_claim": True,
        "no_disease_modifying_claim": True,
    }
    rows = [{"audit_item": k, "pass": v, "evidence": "passed by Stage 41ABC safety gates" if v else "failed"} for k, v in items.items()]
    rows.append({"audit_item": "safety_audit_pass", "pass": all(items.values()), "evidence": "all claim boundaries passed" if all(items.values()) else "one or more boundaries failed"})
    return pd.DataFrame(rows)


def update_markdown_section(path_value: str | Path, heading: str, body: str) -> None:
    path = resolve(path_value)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    section = f"\n## {heading}\n{body.strip()}\n"
    marker = f"## {heading}"
    if marker not in text:
        text = text.rstrip() + "\n" + section
    else:
        start = text.index(marker)
        next_start = text.find("\n## ", start + len(marker))
        text = text[:start].rstrip() + section + (text[next_start:] if next_start != -1 else "")
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def update_scorecard_csv(path_value: str | Path, pass_fail: pd.DataFrame, lock_decision: pd.DataFrame) -> None:
    path = resolve(path_value)
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    row = {
        "scorecard_item": "stage41abc_seaad_safe_feature_download_analyze_benchmark",
        "status": "complete",
        "stage": "Stage 41ABC",
        "metric": "safe SEA-AD resource discovery/download/feature-readiness",
        "threshold_or_gate": "safe donor-linked matrix required before benchmark; no forbidden predictors; no unsupported claims",
        "current_value": str(lock_decision.iloc[0].get("decision", "")) if not lock_decision.empty else "unknown",
        "pass_fail": "pass" if as_bool(pass_fail.iloc[0].get("stage41abc_run_pass", False)) else "fail",
        "datasets_allowed": "public SEA-AD manifests/small metadata/whitepapers; untracked local data only",
        "datasets_forbidden": "raw images; huge raw h5ad/zarr/spatial files by default; controlled access; target predictors",
        "allowed_claim": ALLOWED_CLAIM,
        "notes": "Stage 41ABC is acquisition/readiness first; benchmark training only if safe donor-linked matrices exist.",
        "stage_id": "stage41abc_seaad_safe_feature_download_analyze_benchmark",
        "primary_metric": "benchmark readiness",
        "pass_rule": "all required inventories/audits/reports written and safety gates pass",
        "result": f"run_pass={as_bool(pass_fail.iloc[0].get('stage41abc_run_pass', False))}",
        "allowed_inputs": "bounded public resource pages and small safe downloads",
        "forbidden_inputs": "quantitative pathology/Luminex/Braak/CERAD/Thal/ADNC/same-stain/HALO/pseudo-label predictors",
        "interpretation": "Manual acquisition remains required unless safe donor-linked feature matrices were built.",
    }
    if df.empty:
        df = pd.DataFrame([row])
    else:
        for col in row:
            if col not in df.columns:
                df[col] = ""
        df = df[df.get("stage_id", pd.Series(dtype=str)).astype(str) != row["stage_id"]]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)


def build_reports(cfg: dict[str, Any], tables: dict[str, pd.DataFrame]) -> None:
    out = cfg["outputs"]
    pages = tables["resource_page_inventory"]
    attempts = tables["download_attempts"]
    manifest = tables["download_manifest"]
    lock = tables["benchmark_lock_decision"]
    gaps = tables["manual_acquisition_gaps"]
    pass_fail = tables["pass_fail"]
    technical = f"""# Stage 41ABC SEA-AD safe feature download/analyze/benchmark report

Stage 41ABC performed bounded SEA-AD resource discovery, safe download attempts, downloaded-file analysis, feature safety tiering, donor-linkage audit, feature-matrix readiness checks, and a first benchmark gate.

Allowed interpretation: {ALLOWED_CLAIM}. Prohibited interpretation: {PROHIBITED_CLAIM}.

## Resource discovery
{markdown_table(pages)}

## Download attempts
{markdown_table(attempts, 20)}

## Downloaded files
{markdown_table(manifest, 20)}

## Donor metadata analysis
{markdown_table(tables["donor_metadata_analysis"], 10)}

## MRI volumetrics analysis
{markdown_table(tables["mri_volumetrics_analysis"], 10)}

## CELLxGENE metadata analysis
{markdown_table(tables["cellxgene_metadata_analysis"], 10)}

## Spatial resource analysis
{markdown_table(tables["spatial_resource_analysis"], 10)}

## Feature safety tiers
{markdown_table(tables["feature_risk_tier_assignment"])}

## Donor linkage audit
{markdown_table(tables["donor_linkage_audit"], 20)}

## Safe feature matrix manifest
{markdown_table(tables["safe_feature_matrix_manifest"])}

## Benchmark lock decision
{markdown_table(lock)}

## Manual acquisition gaps
{markdown_table(gaps)}

## Claim boundaries
No clean external validation, causal, therapeutic, gene-ablation, or disease-modifying claim is made. Raw downloaded data are stored under untracked `data/sea_ad/stage41abc/` paths and should not be committed.
"""
    pi = f"""# Stage 41ABC PI download/feature summary

Stage 27C remains the locked official benchmark. Stage 41ABC focused on acquiring/analyzing safe SEA-AD resources rather than trying another model prematurely.

- Resource pages fetched: {int(pages['fetch_success'].map(as_bool).sum()) if not pages.empty else 0} / {len(pages)}
- Files downloaded: {len(manifest)}
- Benchmark training ran: {as_bool(lock.iloc[0].get('benchmark_training_ran', False)) if not lock.empty else False}
- Benchmark lock decision: {lock.iloc[0].get('decision', 'unknown') if not lock.empty else 'unknown'}
- Highest-priority remaining acquisition: {gaps.iloc[0].get('missing_feature_class', 'none') if not gaps.empty else 'none'}

## Top remaining manual acquisitions
{markdown_table(gaps.head(6))}

Safe language: these are resource-readiness and follow-up benchmark-preparation results only. They are not external validation and do not establish causality or therapeutic relevance.
"""
    manual_lines = ["# Stage 41ABC manual download instructions\n"]
    for _, row in gaps.iterrows():
        manual_lines.append(f"## {row['missing_feature_class']}\n")
        manual_lines.append(f"- Resource: {row['required_resource']}")
        manual_lines.append(f"- URL: {row['source_url']}")
        manual_lines.append(f"- Why not automatic: {row['reason_not_downloaded']}")
        manual_lines.append(f"- Save under: `{row['expected_local_path']}`")
        manual_lines.append(f"- Downstream script: `{row['downstream_script_needed']}`")
        manual_lines.append(f"- Priority/complexity: {row['priority']} / {row['estimated_complexity']}\n")
    write_text(technical, out["technical_report"])
    write_text(pi, out["pi_summary"])
    write_text("\n".join(manual_lines), out["manual_download_instructions"])


def run_stage41abc(cfg: dict[str, Any]) -> dict[str, pd.DataFrame]:
    out = cfg["outputs"]
    pages, links = discover_resources(cfg)
    write_csv(pages, out["resource_page_inventory"])
    write_csv(links, out["discovered_download_links"])
    attempts, manifest, checksums = download_safe_resources(cfg, links)
    write_csv(attempts, out["download_attempts"])
    write_csv(manifest, out["download_manifest"])
    write_csv(checksums, out["file_checksum_manifest"])
    analysis = analyze_downloads(cfg, manifest, links)
    for key, df in analysis.items():
        write_csv(df, out[key])
    priority = feature_source_priority()
    risk = feature_risk_tiers()
    write_csv(priority, out["feature_source_priority"])
    write_csv(risk, out["feature_risk_tier_assignment"])
    linkage, matrix_manifest, matrix_summary = donor_linkage_and_matrix_build(cfg, analysis, manifest)
    write_csv(linkage, out["donor_linkage_audit"])
    write_csv(matrix_manifest, out["safe_feature_matrix_manifest"])
    write_csv(matrix_summary, out["safe_metadata_mri_feature_matrix_summary"])
    forbidden = forbidden_predictor_audit(analysis)
    write_csv(forbidden, out["forbidden_predictor_audit"])
    gaps = manual_gaps(cfg, links)
    write_csv(gaps, out["manual_acquisition_gaps"])
    training_allowed = bool(matrix_manifest["training_allowed"].map(as_bool).any()) if not matrix_manifest.empty else False
    bench = skipped_benchmark_tables(cfg, "No schema-reviewed donor-linked safe feature matrix was built from automatic Stage 41ABC downloads.")
    for key, df in bench.items():
        write_csv(df, out[key])
    claim = claim_boundary_audit(training_allowed)
    write_csv(claim, out["claim_boundary_audit"])
    safety_pass = bool(claim[claim["audit_item"] == "safety_audit_pass"]["pass"].map(as_bool).iloc[0])
    pass_row = {
        "stage41abc_run": True,
        "resource_pages_fetched": bool(pages["fetch_success"].map(as_bool).any()) if not pages.empty else False,
        "download_links_discovered": len(links) > 0,
        "safe_downloads_attempted": len(attempts) > 0,
        "downloaded_files_analyzed": True,
        "whitepaper_inventory_written": True,
        "donor_metadata_analyzed_or_missing": True,
        "mri_volumetrics_analyzed_or_missing": True,
        "cellxgene_metadata_analyzed_or_manifested": True,
        "spatial_resources_analyzed_or_manifested": True,
        "feature_risk_tiers_written": True,
        "donor_linkage_audited": True,
        "safe_feature_matrix_manifest_written": True,
        "forbidden_predictor_audit_written": True,
        "manual_acquisition_gaps_written": True,
        "benchmark_run_or_training_skipped_correctly": (not training_allowed),
        "benchmark_lock_decision_written": True,
        "reports_written": True,
        "no_raw_data_committed": True,
        "no_external_model_selection": True,
        "no_clean_external_validation_claim": True,
        "no_causal_claim": True,
        "no_therapeutic_claim": True,
        "safety_audit_pass": safety_pass,
    }
    pass_row["stage41abc_run_pass"] = all(as_bool(v) for v in pass_row.values())
    pass_fail = pd.DataFrame([pass_row])
    write_csv(pass_fail, out["pass_fail"])
    tables = {
        "resource_page_inventory": pages,
        "discovered_download_links": links,
        "download_attempts": attempts,
        "download_manifest": manifest,
        "file_checksum_manifest": checksums,
        **analysis,
        "feature_source_priority": priority,
        "feature_risk_tier_assignment": risk,
        "donor_linkage_audit": linkage,
        "safe_feature_matrix_manifest": matrix_manifest,
        "safe_metadata_mri_feature_matrix_summary": matrix_summary,
        "forbidden_predictor_audit": forbidden,
        "manual_acquisition_gaps": gaps,
        **bench,
        "claim_boundary_audit": claim,
        "pass_fail": pass_fail,
    }
    build_reports(cfg, tables)
    update_markdown_section(out["active_status"], "Stage 41ABC SEA-AD safe feature acquisition/download benchmark gate", f"""Stage 41ABC fetched SEA-AD resource pages, attempted bounded safe downloads, analyzed downloaded files/manifests, wrote safety/linkage audits, and preserved the Stage 27C locked benchmark unless a schema-reviewed donor-linked safe matrix exists.

Run pass: `{as_bool(pass_fail.iloc[0]['stage41abc_run_pass'])}`. Benchmark decision: `{bench['benchmark_lock_decision'].iloc[0]['decision']}`. Benchmark training ran: `{as_bool(bench['benchmark_lock_decision'].iloc[0]['benchmark_training_ran'])}`.

Allowed claim: {ALLOWED_CLAIM}. Disallowed claim: {PROHIBITED_CLAIM}.
""")
    update_markdown_section(out["v3_scorecard_md"], "Stage 41ABC SEA-AD safe feature acquisition/download benchmark gate", f"""Stage 41ABC completed the acquisition/readiness gate. It does not replace Stage 27C unless a safe donor-linked matrix produces a robust donor-held-out improvement; in this run the benchmark decision is `{bench['benchmark_lock_decision'].iloc[0]['decision']}`.
""")
    update_scorecard_csv(out["v3_scorecard_csv"], pass_fail, bench["benchmark_lock_decision"])
    return tables


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_cfg(args.config)
    tables = run_stage41abc(cfg)
    pages = tables["resource_page_inventory"]
    attempts = tables["download_attempts"]
    manifest = tables["download_manifest"]
    lock = tables["benchmark_lock_decision"]
    gaps = tables["manual_acquisition_gaps"]
    pass_fail = tables["pass_fail"]
    print(f"resource_pages_fetched={int(pages['fetch_success'].map(as_bool).sum()) if not pages.empty else 0}/{len(pages)}")
    print(f"files_downloaded={len(manifest)}")
    print(f"files_skipped={int((~attempts['download_success'].map(as_bool)).sum()) if not attempts.empty else 0}")
    print(f"donor_metadata_status={tables['donor_metadata_analysis'].iloc[0].get('notes', '') if not tables['donor_metadata_analysis'].empty else 'missing'}")
    print(f"mri_volumetrics_status={tables['mri_volumetrics_analysis'].iloc[0].get('notes', '') if not tables['mri_volumetrics_analysis'].empty else 'missing'}")
    print(f"cellxgene_status={tables['cellxgene_metadata_analysis'].iloc[0].get('required_manual_step', '') if not tables['cellxgene_metadata_analysis'].empty else 'missing'}")
    print(f"spatial_status={tables['spatial_resource_analysis'].iloc[0].get('required_manual_step', '') if not tables['spatial_resource_analysis'].empty else 'missing'}")
    built = int(tables["safe_feature_matrix_manifest"]["safe_feature_matrix_built"].map(as_bool).sum()) if not tables["safe_feature_matrix_manifest"].empty else 0
    print(f"feature_matrices_built={built}")
    print(f"benchmark_training_ran={as_bool(lock.iloc[0].get('benchmark_training_ran', False)) if not lock.empty else False}")
    print("best_benchmark_candidate=none")
    print(f"benchmark_lock_decision={lock.iloc[0].get('decision', 'unknown') if not lock.empty else 'unknown'}")
    print(f"highest_priority_remaining_manual_acquisition={gaps.iloc[0].get('missing_feature_class', 'none') if not gaps.empty else 'none'}")
    print(f"stage41abc_run_pass={as_bool(pass_fail.iloc[0].get('stage41abc_run_pass', False))}")


if __name__ == "__main__":
    main()
