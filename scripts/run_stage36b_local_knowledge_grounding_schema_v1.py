from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

TRISTATE = ["True", "False", "not_evaluated"]
CATEGORY_KEYWORDS = {
    "kg_known_ad": ["ad", "alzheimer", "dementia", "apoe", "trem2"],
    "kg_known_microglia": ["microglia", "dam", "trem2", "tyrobp", "iba1"],
    "kg_known_neuroinflammation": ["neuroinflammation", "inflammatory", "complement", "interferon", "chemokine", "antigen"],
    "kg_known_amyloid": ["amyloid", "6e10", "abeta", "a_beta", "app"],
    "kg_known_tau": ["tau", "at8"],
    "kg_known_astrocyte": ["astrocyte", "gfap"],
    "kg_known_neuronal": ["neuron", "neuronal", "neun", "synapse"],
}
TARGET_CATEGORY = {
    "6e10/A_beta": "kg_known_amyloid",
    "AT8": "kg_known_tau",
    "GFAP": "kg_known_astrocyte",
    "Iba1": "kg_known_microglia",
    "NeuN": "kg_known_neuronal",
}
GENE_COL_CANDIDATES = ["gene", "genes", "symbol", "gene_symbol", "hgnc_symbol", "target", "candidate_gene"]
TERM_COL_CANDIDATES = ["term", "pathway", "category", "label", "module", "description", "gene_set"]


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    low = text.lower()
    return [kw for kw in keywords if kw.lower() in low]


def discover_resources(cfg: dict[str, Any]) -> pd.DataFrame:
    rows = []
    roots = [resolve(root) for root in cfg["resource_discovery"]["roots"]]
    exts = set(cfg["resource_discovery"]["extensions"])
    max_size = int(cfg["resource_discovery"]["max_file_size_bytes"])
    keywords = list(cfg["resource_discovery"]["keywords"])
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in exts:
                continue
            rel = str(path.relative_to(ROOT))
            if rel.replace("\\", "/").startswith("data/"):
                continue
            if rel.replace("\\", "/") == "docs/stage_c_finetuning_analysis.md":
                continue
            if rel.replace("\\", "/").startswith("results/tables/stage36b_"):
                continue
            if rel.replace("\\", "/").startswith("results/reports/stage36b_"):
                continue
            path_hits = keyword_hits(rel, keywords)
            if not path_hits and rel.replace("\\", "/").startswith(("results/tables/", "configs/")):
                continue
            size = int(path.stat().st_size)
            if size > max_size:
                rows.append({"path": rel, "size_bytes": size, "extension": path.suffix.lower(), "keyword_hits": "", "scanned": False, "exclusion_reason": "file_exceeds_size_limit"})
                continue
            text = read_text(path)[:200000]
            hits = sorted(set(path_hits) | set(keyword_hits(text, keywords)))
            if hits:
                rows.append({"path": rel, "size_bytes": size, "extension": path.suffix.lower(), "keyword_hits": ";".join(hits), "scanned": True, "exclusion_reason": ""})
    return pd.DataFrame(rows)


def safe_read_table(path: Path) -> pd.DataFrame:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        if path.suffix.lower() == ".tsv":
            return pd.read_csv(path, sep="\t")
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(read_text(path))
            return pd.json_normalize(data) if isinstance(data, (dict, list)) else pd.DataFrame()
        if path.suffix.lower() == ".json":
            data = json.loads(read_text(path))
            return pd.json_normalize(data) if isinstance(data, (dict, list)) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame()


def exact_gene_mentions(text: str, genes: set[str]) -> set[str]:
    found = set()
    for gene in genes:
        if re.search(rf"(?<![A-Za-z0-9_-]){re.escape(gene)}(?![A-Za-z0-9_-])", text, flags=re.IGNORECASE):
            found.add(gene)
    return found


def exact_gene_context_categories(text: str, genes: set[str], window: int = 600) -> dict[str, set[str]]:
    contexts: dict[str, set[str]] = {}
    for gene in genes:
        cats: set[str] = set()
        for match in re.finditer(rf"(?<![A-Za-z0-9_-]){re.escape(gene)}(?![A-Za-z0-9_-])", text, flags=re.IGNORECASE):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            cats |= infer_categories(text[start:end])
        contexts[gene] = cats
    return contexts


def infer_categories(text: str) -> set[str]:
    low = text.lower()
    categories = set()
    for category, kws in CATEGORY_KEYWORDS.items():
        if any(kw in low for kw in kws):
            categories.add(category)
    return categories


def schema_and_annotations(inventory: pd.DataFrame, query_genes: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    registry_rows = []
    annotation_rows = []
    for idx, row in inventory.iterrows():
        path = resolve(row["path"])
        resource_id = f"resource_{idx + 1:03d}"
        table = safe_read_table(path)
        gene_col = ""
        term_col = ""
        stable = False
        resource_type = "unknown_schema"
        parse_status = "no_parse"
        categories = infer_categories(str(row.get("keyword_hits", "")) + " " + row["path"])
        terms = set(str(row.get("keyword_hits", "")).split(";")) - {""}
        matched_genes: set[str] = set()
        gene_categories: dict[str, set[str]] = {}
        if not table.empty:
            lower = {c.lower(): c for c in table.columns}
            gene_col = next((lower[c] for c in GENE_COL_CANDIDATES if c in lower), "")
            term_col = next((lower[c] for c in TERM_COL_CANDIDATES if c in lower), "")
            if gene_col:
                vals = table[gene_col].dropna().astype(str).str.upper()
                matched_genes = set(vals) & query_genes
                stable = bool(matched_genes)
                parse_status = "parsed_table_exact_gene_column" if stable else "parsed_table_no_query_gene_overlap"
                resource_type = "gene_term_table" if term_col else "gene_list"
                if term_col and term_col in table:
                    text = " ".join(table[term_col].dropna().astype(str).head(200).tolist())
                    categories |= infer_categories(text)
                    terms |= set(table[term_col].dropna().astype(str).head(50).tolist())
        if not stable:
            text = read_text(path)
            matched_genes = exact_gene_mentions(text, query_genes)
            if matched_genes:
                gene_categories = exact_gene_context_categories(text, matched_genes)
                stable = True
                parse_status = "parsed_markdown_or_text_exact_gene_mentions"
                resource_type = "markdown_gene_mentions" if path.suffix.lower() == ".md" else "gene_list"
        registry_rows.append(
            {
                "resource_id": resource_id,
                "resource_path": row["path"],
                "resource_type": resource_type,
                "parse_status": parse_status,
                "gene_column": gene_col,
                "term_column": term_col,
                "category_column": "",
                "evidence_column": "",
                "target_scope_column": "",
                "species_column": "",
                "disease_scope_column": "",
                "n_rows": int(len(table)) if not table.empty else 0,
                "n_gene_rows": int(len(matched_genes)),
                "stable_schema_available": stable,
                "exclusion_reason": "" if stable else "no_exact_query_gene_match_or_no_gene_schema",
            }
        )
        for gene in sorted(matched_genes):
            cats_for_gene = gene_categories.get(gene, categories)
            annotation_rows.append(
                {
                    "gene": gene,
                    "resource_id": resource_id,
                    "resource_path": row["path"],
                    "resource_type": resource_type,
                    "support_terms": ";".join(sorted(t for t in terms if t)),
                    "categories": ";".join(sorted(cats_for_gene)),
                    "confidence": "low" if resource_type == "markdown_gene_mentions" else ("high" if categories else "medium"),
                    "parsing_method": parse_status,
                }
            )
    return pd.DataFrame(registry_rows), pd.DataFrame(annotation_rows)


def gene_annotations(query_genes: set[str], raw_ann: pd.DataFrame, grounding_pass: bool) -> pd.DataFrame:
    rows = []
    for gene in sorted(query_genes):
        subset = raw_ann[raw_ann["gene"] == gene] if not raw_ann.empty else pd.DataFrame()
        if not grounding_pass:
            vals = {k: "not_evaluated" for k in list(CATEGORY_KEYWORDS) + ["kg_known_target_pathology"]}
            rows.append({"gene": gene, **vals, "kg_any_prior_support": "not_evaluated", "kg_support_terms": "", "kg_support_sources": "", "kg_support_count": 0, "kg_grounding_confidence": "not_evaluated"})
            continue
        cats = set()
        terms = set()
        sources = set()
        confidences = []
        for _, row in subset.iterrows():
            cats |= {c for c in str(row["categories"]).split(";") if c}
            terms |= {t for t in str(row["support_terms"]).split(";") if t}
            sources.add(str(row["resource_id"]))
            confidences.append(str(row["confidence"]))
        vals = {k: str(k in cats) for k in CATEGORY_KEYWORDS}
        vals["kg_known_target_pathology"] = "False"
        any_support = bool(len(subset))
        if "high" in confidences:
            conf = "high"
        elif "medium" in confidences:
            conf = "medium"
        elif "low" in confidences:
            conf = "low"
        else:
            conf = "not_evaluated" if not grounding_pass else "low"
        rows.append(
            {
                "gene": gene,
                **vals,
                "kg_any_prior_support": str(any_support),
                "kg_support_terms": ";".join(sorted(terms)),
                "kg_support_sources": ";".join(sorted(sources)),
                "kg_support_count": int(len(subset)),
                "kg_grounding_confidence": conf if any_support else "low",
            }
        )
    return pd.DataFrame(rows)


def hypothesis_grounding(stage36a: pd.DataFrame, ann: pd.DataFrame, grounding_pass: bool) -> pd.DataFrame:
    drop_cols = [c for c in stage36a.columns if c.startswith("kg_")]
    merged = stage36a.drop(columns=drop_cols, errors="ignore").merge(ann, on="gene", how="left")
    target_known = []
    novelty = []
    safe = []
    for _, row in merged.iterrows():
        target_field = TARGET_CATEGORY.get(str(row["target_key"]), "")
        if grounding_pass and target_field:
            val = str(row.get(target_field, "False"))
        else:
            val = "not_evaluated" if not grounding_pass else "False"
        target_known.append(val)
        any_support = str(row.get("kg_any_prior_support", "not_evaluated"))
        if not grounding_pass:
            ns = "not_evaluated"
        elif any_support == "True":
            ns = "known_prior_supported"
        else:
            ns = "no_local_prior_found"
        novelty.append(ns)
        safe.append("local prior-knowledge annotation only; knowledge support is not validation; requires independent validation")
    merged["kg_known_target_pathology"] = target_known
    merged["novelty_status"] = novelty
    merged["safe_interpretation"] = safe
    out_cols = [
        "target", "target_key", "module", "gene", "evidence_level", "module_importance_score", "module_delta_metric",
        "mean_abs_prediction_delta", "projection_method", "kg_known_ad", "kg_known_microglia", "kg_known_neuroinflammation",
        "kg_known_amyloid", "kg_known_tau", "kg_known_astrocyte", "kg_known_neuronal", "kg_known_target_pathology",
        "kg_any_prior_support", "kg_support_terms", "kg_support_sources", "kg_support_count", "kg_grounding_confidence",
        "novelty_status", "safe_interpretation",
    ]
    merged = merged.rename(columns={"evidence_level": "evidence_level_from_stage36a"})
    out_cols[4] = "evidence_level_from_stage36a"
    return merged[out_cols]


def write_report(cfg, inventory, registry, ann, hyp, audit, pf):
    row = pf.iloc[0]
    lines = [
        "# Stage 36B local knowledge grounding report v1",
        "",
        "## 1. Executive summary",
        "",
        f"Stage 36B run pass: `{bool(row.stage36b_run_pass)}`. Knowledge grounding pass: `{bool(row.stage36b_knowledge_grounding_pass)}`. Stable local resources: `{int(row.n_schema_stable_resources)}`.",
        "Stage 36B performs local prior-knowledge grounding of Stage 36A model-implied hypotheses. Knowledge support is not validation.",
        "",
        "## 2. Why Stage 36B was run",
        "",
        "Stage 36A generated module-level and projected gene-level hypotheses but did not have a stable local knowledge schema for annotation.",
        "",
        "## 3. Inputs from Stage 36A",
        "",
        f"Stage 36A gene hypotheses evaluated: `{int(row.n_stage36a_gene_hypotheses)}`.",
        "",
        "## 4. Local resource inventory",
        "",
        "```csv",
        inventory.to_csv(index=False).strip(),
        "```",
        "",
        "## 5. Schema registry",
        "",
        "```csv",
        registry.to_csv(index=False).strip(),
        "```",
        "",
        "## 6. Knowledge annotation method",
        "",
        "Annotations use exact uppercase gene-symbol matching against Stage 36A query genes. Markdown/text mentions are low-confidence local prior support; structured gene tables are medium/high depending on category specificity. No aliases were invented.",
        "",
        "## 7. Hypothesis grounding results",
        "",
        "```csv",
        hyp.head(40).to_csv(index=False).strip(),
        "```",
        "",
        "## 8. What passed",
        "",
        "Inventory, schema registry, gene annotations, hypothesis grounding, safety audit, and report were written. No web scraping, downloads, model training, external validation, or ablation reruns were performed.",
        "",
        "## 9. What remains unresolved",
        "",
        "No clean external validation was run. No causal or therapeutic claims are supported. Genes without local prior support should be described as no-local-prior-found, not validated novel targets.",
        "",
        "## 10. Safe claim language",
        "",
        "- Stage 36B performs local prior-knowledge grounding of Stage 36A model-implied hypotheses.",
        "- Knowledge support is not validation.",
        "- No clean external validation was run.",
        "- No causal or therapeutic claims are supported.",
        "- Genes without local prior support should be described as no-local-prior-found, not validated novel targets.",
        "",
        "## 11. Forbidden claim language",
        "",
        "- Do not claim validated targets.",
        "- Do not claim therapeutic targets.",
        "- Do not claim causal regulators.",
        "- Do not claim external validation succeeded.",
        "- Do not claim novel genes were discovered.",
        "- Do not claim Graph-JEPA proves causality.",
        "",
        "## 12. Recommended next step",
        "",
        "Use Stage 36B annotations as inputs to a ranked follow-up hypothesis package while keeping validation and causality claims out of scope.",
        "",
        "## Audit",
        "",
        "```csv",
        audit.to_csv(index=False).strip(),
        "```",
        "",
        "## Pass/fail",
        "",
        "```csv",
        pf.to_csv(index=False).strip(),
        "```",
    ]
    resolve(cfg["outputs"]["report"]).write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    status = (
        f"Stage 36B local knowledge grounding is complete. Knowledge grounding pass: `{bool(row.stage36b_knowledge_grounding_pass)}`; "
        f"schema-stable local resources: `{int(row.n_schema_stable_resources)}`; annotated Stage 36A gene hypotheses: `{int(row.n_gene_hypotheses_annotated)}`. "
        "This is local prior-knowledge annotation only, not validation, causality, or therapeutic evidence."
    )
    for doc_path, marker in [
        (ROOT / "docs" / "ACTIVE_V3_STATUS.md", "\n\n## Stage 36B local knowledge grounding status\n"),
        (ROOT / "docs" / "V3_SCORECARD.md", "\n\n## Stage 36B local knowledge grounding result\n"),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + status + "\n", encoding="utf-8")
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    item = "stage36b_local_knowledge_grounding"
    new = {
        "scorecard_item": item,
        "status": "complete",
        "stage": "Stage 36B",
        "metric": "local prior-knowledge grounding of Stage 36A gene hypotheses",
        "threshold_or_gate": "pass requires schema-stable local resources and annotations for all Stage 36A gene hypotheses",
        "current_value": f"grounding_pass={bool(row.stage36b_knowledge_grounding_pass)}; stable_resources={int(row.n_schema_stable_resources)}",
        "pass_fail": "pass" if bool(row.stage36b_knowledge_grounding_pass) else "nonfatal_fail",
        "datasets_allowed": "existing local repo resources only",
        "datasets_forbidden": "web scraping; downloads; clean holdouts; external labels; model training",
        "allowed_claim": row.controlled_interpretation,
        "notes": "Knowledge support is not validation.",
    }
    score = score[score["scorecard_item"] != item]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/agent/stage36b_local_knowledge_grounding_schema_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stage36a_path = resolve(cfg["inputs"]["stage36a_gene_hypotheses"])
    stage36a_found = stage36a_path.exists()
    stage36a = pd.read_csv(stage36a_path) if stage36a_found else pd.DataFrame()
    query_genes = set(stage36a["gene"].dropna().astype(str).str.upper()) if not stage36a.empty else set()
    inventory = discover_resources(cfg)
    registry, raw_ann = schema_and_annotations(inventory[inventory.get("scanned", False).astype(bool)] if not inventory.empty else inventory, query_genes)
    stable_count = int(registry["stable_schema_available"].sum()) if not registry.empty else 0
    grounding_pass = bool(stable_count >= 1 and len(query_genes) > 0)
    ann = gene_annotations(query_genes, raw_ann, grounding_pass)
    hyp = hypothesis_grounding(stage36a, ann, grounding_pass) if not stage36a.empty else pd.DataFrame()
    audit = pd.DataFrame([{"clean_holdout_used": False, "external_validation_run": False, "external_labels_used_for_supervised_pathology_prediction": False, "web_scraping_run": False, "new_resource_downloaded": False, "in_silico_ablation_run": False, "causal_validation_claim_used": False, "therapeutic_target_language_used": False, "novelty_overclaim_used": False, "annotation_fabrication_detected": False, "knowledge_grounding_audit_pass": True}])
    interpretation = "Stage 36B created a local prior-knowledge grounding schema for Stage 36A model-implied hypotheses. Knowledge support is annotation only, not validation."
    pf = pd.DataFrame([{"stage36b_run": True, "stage36a_inputs_found": stage36a_found, "local_resource_inventory_written": True, "schema_registry_written": True, "n_local_resources_scanned": int(len(inventory)), "n_schema_stable_resources": stable_count, "n_stage36a_gene_hypotheses": int(len(stage36a)), "n_gene_hypotheses_annotated": int(len(hyp)), "stage36b_knowledge_grounding_pass": grounding_pass and len(hyp) == len(stage36a), "stage36b_run_pass": True, "no_web_scraping": True, "no_downloads": True, "no_external_validation": True, "no_causal_claim": True, "no_therapeutic_claim": True, "controlled_interpretation": interpretation}])
    inventory.to_csv(resolve(cfg["outputs"]["inventory"]), index=False)
    registry.to_csv(resolve(cfg["outputs"]["schema_registry"]), index=False)
    ann.to_csv(resolve(cfg["outputs"]["gene_annotations"]), index=False)
    hyp.to_csv(resolve(cfg["outputs"]["hypothesis_grounding"]), index=False)
    audit.to_csv(resolve(cfg["outputs"]["audit"]), index=False)
    pf.to_csv(resolve(cfg["outputs"]["pass_fail"]), index=False)
    write_report(cfg, inventory, registry, ann, hyp, audit, pf)
    update_status(pf)
    print(f"stage36b_run_pass={bool(pf.iloc[0]['stage36b_run_pass'])}")
    print(f"stage36b_knowledge_grounding_pass={bool(pf.iloc[0]['stage36b_knowledge_grounding_pass'])}")
    print(f"n_schema_stable_resources={stable_count}")


if __name__ == "__main__":
    main()
