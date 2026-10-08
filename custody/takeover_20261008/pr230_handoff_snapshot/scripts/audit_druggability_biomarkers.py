from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests


TARGETS = ["TLR2", "APP", "APOE"]


FALLBACKS: dict[str, dict[str, Any]] = {
    "TLR2": {
        "uniprot_id": "O60603",
        "protein_name": "Toll-like receptor 2",
        "subcellular_location": "Cell membrane; single-pass type I membrane protein.",
        "is_membrane": True,
        "is_secreted": False,
        "fallback_strategy": "Surface immunomodulatory target; prioritize antibody, biologic, or antagonist repurposing review.",
        "caution": "Innate immune receptor with infection and inflammatory-pleiotropy risk.",
    },
    "APP": {
        "uniprot_id": "P05067",
        "protein_name": "Amyloid-beta precursor protein",
        "subcellular_location": "Cell membrane; secreted soluble APP and amyloid-beta peptides after proteolytic processing.",
        "is_membrane": True,
        "is_secreted": True,
        "fallback_strategy": "Diagnostic biomarker and high-risk therapeutic pathway target.",
        "caution": "Broad neuronal biology; direct APP targeting must be separated from secretase-pathway effects.",
    },
    "APOE": {
        "uniprot_id": "P02649",
        "protein_name": "Apolipoprotein E",
        "subcellular_location": "Secreted; extracellular/lipoprotein particle associated.",
        "is_membrane": False,
        "is_secreted": True,
        "fallback_strategy": "Diagnostic biomarker and lipid-transport pathway target.",
        "caution": "Isoform- and context-dependent AD biology; direct pharmacology is harder than pathway modulation.",
    },
}


def request_json(
    url: str,
    params: dict[str, Any] | None = None,
    *,
    timeout: int = 25,
    retries: int = 3,
    sleep_seconds: float = 1.5,
) -> dict[str, Any] | None:
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers={"Accept": "application/json", "User-Agent": "sea-ad-jepa-druggability-audit/1.0"},
                timeout=timeout,
            )
            if response.status_code in {429, 500, 502, 503, 504} and attempt < retries:
                time.sleep(sleep_seconds * attempt)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt == retries:
                return None
            time.sleep(sleep_seconds * attempt)
    return None


def text_blob(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return str(value)


def parse_uniprot_location(record: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    protein_name = fallback["protein_name"]
    protein_description = record.get("proteinDescription") or {}
    recommended_name = protein_description.get("recommendedName") or {}
    full_name = recommended_name.get("fullName") or {}
    if full_name.get("value"):
        protein_name = full_name["value"]

    location_parts: list[str] = []
    for comment in record.get("comments", []):
        if comment.get("commentType") != "SUBCELLULAR LOCATION":
            continue
        for sublocation in comment.get("subcellularLocations", []):
            location = sublocation.get("location") or {}
            value = location.get("value")
            if value:
                location_parts.append(value)
        for text in comment.get("texts", []):
            if text.get("value"):
                location_parts.append(text["value"])

    if not location_parts:
        for comment in record.get("comments", []):
            blob = text_blob(comment)
            if "membrane" in blob.lower() or "secret" in blob.lower() or "extracellular" in blob.lower():
                location_parts.append(blob)

    subcellular_location = "; ".join(dict.fromkeys(location_parts)) or fallback["subcellular_location"]
    lower_location = subcellular_location.lower()

    return {
        "UniProt_ID": record.get("primaryAccession") or fallback["uniprot_id"],
        "Protein_Name": protein_name,
        "Subcellular_Location": subcellular_location,
        "Is_Membrane": bool(fallback["is_membrane"] or "membrane" in lower_location),
        "Is_Secreted": bool(
            fallback["is_secreted"]
            or "secreted" in lower_location
            or "extracellular" in lower_location
            or "lipoprotein" in lower_location
        ),
    }


def fetch_uniprot_annotation(gene: str) -> dict[str, Any]:
    fallback = FALLBACKS[gene]
    data = request_json(
        "https://rest.uniprot.org/uniprotkb/search",
        {
            "query": f"gene_exact:{gene} AND organism_id:9606 AND reviewed:true",
            "format": "json",
            "size": 1,
            "fields": "accession,protein_name,cc_subcellular_location",
        },
    )
    if not data or not data.get("results"):
        return {
            "UniProt_ID": fallback["uniprot_id"],
            "Protein_Name": fallback["protein_name"],
            "Subcellular_Location": fallback["subcellular_location"],
            "Is_Membrane": fallback["is_membrane"],
            "Is_Secreted": fallback["is_secreted"],
        }
    return parse_uniprot_location(data["results"][0], fallback)


def component_symbols(target: dict[str, Any]) -> set[str]:
    symbols: set[str] = set()
    for component in target.get("target_components", []) or []:
        for synonym in component.get("target_component_synonyms", []) or []:
            if synonym.get("syn_type") in {"GENE_SYMBOL", "GENE NAME", "UNIPROT"} and synonym.get("component_synonym"):
                symbols.add(str(synonym["component_synonym"]).upper())
    return symbols


def choose_chembl_target(gene: str, targets: list[dict[str, Any]]) -> dict[str, Any] | None:
    human_targets = [t for t in targets if t.get("organism") == "Homo sapiens"]
    single_protein = [t for t in human_targets if t.get("target_type") in {"SINGLE PROTEIN", "PROTEIN COMPLEX"}]

    for target in single_protein + human_targets:
        if gene.upper() in component_symbols(target):
            return target

    for target in single_protein + human_targets:
        joined = " ".join(
            str(target.get(k, "")) for k in ["pref_name", "target_chembl_id", "target_type", "organism"]
        ).upper()
        if gene.upper() in joined:
            return target
    return None


def fetch_all_pages(url: str, params: dict[str, Any], key: str, limit_pages: int = 20) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    next_url: str | None = url
    next_params: dict[str, Any] | None = params.copy()
    pages = 0
    while next_url and pages < limit_pages:
        data = request_json(next_url, next_params)
        if not data:
            break
        rows.extend(data.get(key, []))
        next_path = (data.get("page_meta") or {}).get("next")
        if next_path:
            next_url = "https://www.ebi.ac.uk" + next_path if next_path.startswith("/") else next_path
            next_params = None
        else:
            next_url = None
        pages += 1
    return rows


def is_active_activity(activity: dict[str, Any]) -> bool:
    pchembl = activity.get("pchembl_value")
    if pchembl not in {None, ""}:
        try:
            return float(pchembl) >= 5.0
        except (TypeError, ValueError):
            pass

    standard_value = activity.get("standard_value")
    units = str(activity.get("standard_units") or "").lower()
    relation = str(activity.get("standard_relation") or "")
    try:
        value = float(standard_value)
    except (TypeError, ValueError):
        return False
    if units in {"nm", "nanomolar"} and relation in {"=", "<", "<="}:
        return value <= 10_000.0
    return False


def parse_molecule_phase(molecule: dict[str, Any], fallback_name: str) -> tuple[float, str]:
    phase = molecule.get("max_phase")
    try:
        max_phase = float(phase or 0.0)
    except (TypeError, ValueError):
        max_phase = 0.0
    return max_phase, str(molecule.get("pref_name") or fallback_name)


def fetch_molecule_phases_batch(molecule_chembl_ids: list[str], chunk_size: int = 100) -> dict[str, tuple[float, str]]:
    phases: dict[str, tuple[float, str]] = {}
    for start in range(0, len(molecule_chembl_ids), chunk_size):
        chunk = molecule_chembl_ids[start : start + chunk_size]
        data = request_json(
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json",
            {"molecule_chembl_id__in": ",".join(chunk), "limit": len(chunk)},
        )
        if not data:
            continue
        for molecule in data.get("molecules", []):
            molecule_id = molecule.get("molecule_chembl_id")
            if molecule_id:
                phases[str(molecule_id)] = parse_molecule_phase(molecule, str(molecule_id))
    return phases


def fetch_chembl_summary(gene: str, max_molecule_phase_queries: int) -> dict[str, Any]:
    search = request_json("https://www.ebi.ac.uk/chembl/api/data/target/search.json", {"q": gene, "limit": 20})
    target = choose_chembl_target(gene, search.get("targets", []) if search else [])
    if not target:
        return {
            "ChEMBL_Target_ID": "",
            "Known_Compounds_Count": 0,
            "Max_Clinical_Trial_Phase": 0.0,
            "Clinical_Molecules": "",
        }

    target_id = target["target_chembl_id"]
    activities = fetch_all_pages(
        "https://www.ebi.ac.uk/chembl/api/data/activity.json",
        {
            "target_chembl_id": target_id,
            "standard_type__in": "IC50,Ki,Kd,EC50,Potency",
            "limit": 1000,
        },
        "activities",
        limit_pages=25,
    )

    active_molecules = sorted(
        {
            str(activity.get("molecule_chembl_id"))
            for activity in activities
            if activity.get("molecule_chembl_id") and is_active_activity(activity)
        }
    )

    phase_sample = active_molecules[:max_molecule_phase_queries]
    phase_lookup = fetch_molecule_phases_batch(phase_sample)

    max_phase = 0.0
    clinical_names: list[str] = []
    for molecule_id in phase_sample:
        phase, name = phase_lookup.get(molecule_id, (0.0, molecule_id))
        if phase > max_phase:
            max_phase = phase
        if phase >= 1:
            clinical_names.append(f"{name} (phase {phase:g})")

    return {
        "ChEMBL_Target_ID": target_id,
        "Known_Compounds_Count": len(active_molecules),
        "Max_Clinical_Trial_Phase": max_phase,
        "Clinical_Molecules": "; ".join(clinical_names[:10]),
    }


def choose_strategy(row: dict[str, Any]) -> str:
    strategies: list[str] = []
    if row["Is_Membrane"] and float(row["Max_Clinical_Trial_Phase"]) > 0:
        strategies.append("Repurpose Existing Drug / Monoclonal Target")
    elif row["Is_Membrane"]:
        strategies.append("Surface / Monoclonal Target")
    if row["Is_Secreted"]:
        strategies.append("Diagnostic Biomarker Target")
    if not row["Is_Membrane"] and not row["Is_Secreted"] and int(row["Known_Compounds_Count"]) == 0:
        strategies.append("Difficult Small Molecule Target")
    return " + ".join(strategies) if strategies else FALLBACKS[row["Target_Gene"]]["fallback_strategy"]


def audit_target(gene: str, max_molecule_phase_queries: int) -> dict[str, Any]:
    localization = fetch_uniprot_annotation(gene)
    chembl = fetch_chembl_summary(gene, max_molecule_phase_queries)
    row: dict[str, Any] = {
        "Target_Gene": gene,
        **localization,
        **chembl,
        "Caution": FALLBACKS[gene]["caution"],
    }
    row["Translational_Strategy"] = choose_strategy(row)
    return row


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit artifact-cleared SEA-AD Graph-JEPA targets for localization, biomarker potential, and ChEMBL druggability."
    )
    parser.add_argument("--out", default="results/tables/v2_2_druggability_summary.csv")
    parser.add_argument("--targets", nargs="+", default=TARGETS)
    parser.add_argument("--max-molecule-phase-queries", type=int, default=2000)
    args = parser.parse_args()

    unknown = [target for target in args.targets if target not in FALLBACKS]
    if unknown:
        raise ValueError(f"No fallback annotation is defined for: {unknown}")

    rows = [audit_target(target, args.max_molecule_phase_queries) for target in args.targets]
    df = pd.DataFrame(rows)

    ordered_columns = [
        "Target_Gene",
        "UniProt_ID",
        "Protein_Name",
        "Subcellular_Location",
        "Is_Membrane",
        "Is_Secreted",
        "ChEMBL_Target_ID",
        "Known_Compounds_Count",
        "Max_Clinical_Trial_Phase",
        "Clinical_Molecules",
        "Translational_Strategy",
        "Caution",
    ]
    df = df[ordered_columns]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(df.to_string(index=False))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
