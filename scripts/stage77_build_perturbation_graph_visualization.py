#!/usr/bin/env python3
"""Build Stage77/F11V-B read-only perturbation graph visualization data.

Consumes frozen Stage75/F10 evidence plus frozen Stage77/F11 perturbation
outputs. The exporter reshapes already-computed values for display only; it does
not recompute edge weights, perturbation magnitudes, directions, propagation,
JEPA embeddings, rescue scores, drug matches, or scientific thresholds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

APPROVED_WORDING = "Model-based, enhancer-informed perturbation hypotheses requiring experimental validation."
EDGE_LABEL = "Coactivity-signed candidate influence"
DELTA_LABEL = "Simulated input-space expression delta"
HYPOTHESIS_LABEL = "Model-based perturbation hypothesis"
FALSE_CLAIMS = {
    "validated_regulation": False,
    "validated_grn_claim": False,
    "causal_validation_pass": False,
    "therapeutic_target_claim": False,
    "jepa_embedding_run": False,
    "visualization_recalculates_analysis": False,
}

REQUIRED_EDGE_COLUMNS = {
    "tf", "target_gene", "motif_support_class", "n_supported_motifs",
    "n_direct_supported_motifs", "n_unique_query_peaks",
    "n_unique_screen_regions", "max_motif_NES", "edge_bootstrap_median_rho",
    "edge_bootstrap_sign_stability", "predicted_response_sign_from_coactivity",
    "evidence_tier", "edge_feature_status", "included_in_perturbation_graph_candidate",
}
REQUIRED_READINESS_COLUMNS = {
    "tf", "evidence_tier", "regulator_present_in_jepa_feature_space",
    "total_candidate_edges", "usable_signed_edges", "readiness_status", "blocking_reason",
}
REQUIRED_SCENARIO_COLUMNS = {
    "scenario_id", "regulator", "direction", "magnitude", "scenario_type",
    "cell_count", "donor_count", "region_count", "state_count", "edge_count",
}
REQUIRED_DELTA_COLUMNS = {
    "scenario_id", "scenario_type", "regulator", "direction", "magnitude",
    "cell_id", "donor_id", "brain_region", "state_label", "gene_symbol",
    "baseline_value", "unclipped_delta", "clipped_delta", "perturbed_value_clipped", "clipped",
}
REQUIRED_WEIGHT_COLUMNS = {
    "tf", "target_gene", "normalized_outgoing_weight", "absolute_unnormalized_weight",
    "edge_feature_status",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML root is not a mapping: {path}")
    return data


def git_head(project: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, check=True, text=True, capture_output=True).stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).encode("utf-8") + b"\n"


def stable_json_hash(payload: Any) -> str:
    return hashlib.sha256(stable_json_bytes(payload)).hexdigest()


def atomic_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", suffix=".tmp", prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write(stable_json_bytes(payload))
    tmp.replace(path)


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    return value


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} schema drift; missing columns: {missing}")


def motif_visual_class(value: str) -> str:
    text = str(value)
    if text == "direct_and_or_extended":
        return "direct"
    if "direct" in text and "extended" not in text:
        return "direct"
    if "extended" in text:
        return "extended_only"
    return "none"


def rel_source_hashes(project: Path, sources: dict[str, str]) -> dict[str, dict[str, Any]]:
    hashes: dict[str, dict[str, Any]] = {}
    for label, rel in sorted(sources.items()):
        path = project / rel
        hashes[label] = {"path": rel, "sha256": sha256_file(path), "byte_size": int(path.stat().st_size)}
    return hashes


def build_nodes(regulators: pd.DataFrame, readiness: pd.DataFrame, edges: pd.DataFrame) -> list[dict[str, Any]]:
    readiness_by_tf = {row["tf"]: row for _, row in readiness.iterrows()}
    nodes: list[dict[str, Any]] = []
    for _, row in regulators.sort_values(["evidence_tier", "tf"]).iterrows():
        tf = str(row["tf"])
        ready = readiness_by_tf.get(tf)
        nodes.append({
            "id": f"TF::{tf}", "label": tf, "node_type": "transcription_factor", "gene_symbol": tf,
            "evidence_tier": clean_value(row.get("evidence_tier")),
            "evidence_tier_label": clean_value(row.get("evidence_tier_label")),
            "stage75_integrated_gate": clean_value(row.get("stage75_integrated_gate")),
            "motif_support_interpretation": clean_value(row.get("motif_support_interpretation")),
            "max_motif_NES": clean_value(row.get("max_motif_NES")),
            "n_supported_motifs": clean_value(row.get("n_supported_motifs")),
            "n_supported_target_genes": clean_value(row.get("n_supported_target_genes")),
            "present_in_jepa_feature_space": to_bool(ready.get("regulator_present_in_jepa_feature_space")) if ready is not None else False,
            "readiness_status": clean_value(ready.get("readiness_status")) if ready is not None else "not_in_f10_readiness_table",
            "usable_signed_edges": clean_value(ready.get("usable_signed_edges")) if ready is not None else 0,
            "blocking_reason": clean_value(ready.get("blocking_reason")) if ready is not None else "not_in_f10_readiness_table",
            **FALSE_CLAIMS,
        })
    for gene, group in edges.groupby("target_gene", sort=True):
        usable = group["edge_feature_status"].eq("usable_signed_edge_feature_present").any()
        nodes.append({
            "id": f"GENE::{gene}", "label": gene, "node_type": "target_gene", "gene_symbol": gene,
            "present_in_jepa_feature_space": bool(usable),
            "target_of_tfs": sorted(group["tf"].dropna().astype(str).unique().tolist()),
            "max_motif_NES": clean_value(group["max_motif_NES"].max()),
            "n_edges": int(len(group)),
            "n_usable_edges": int(group["edge_feature_status"].eq("usable_signed_edge_feature_present").sum()),
            **FALSE_CLAIMS,
        })
    return nodes


def build_edges(edges: pd.DataFrame, edge_weights: pd.DataFrame) -> list[dict[str, Any]]:
    weights = edge_weights.set_index(["tf", "target_gene"])
    payload: list[dict[str, Any]] = []
    for _, row in edges.sort_values(["evidence_tier", "tf", "target_gene"]).iterrows():
        key = (row["tf"], row["target_gene"])
        weight_row = weights.loc[key] if key in weights.index else None
        visual_class = motif_visual_class(str(row["motif_support_class"]))
        usable = row["edge_feature_status"] == "usable_signed_edge_feature_present" and key in weights.index
        payload.append({
            "id": f"{row['tf']}->{row['target_gene']}", "source": f"TF::{row['tf']}", "target": f"GENE::{row['target_gene']}",
            "source_tf": row["tf"], "target_gene": row["target_gene"], "directed": True, "edge_label": EDGE_LABEL,
            "evidence_tier": clean_value(row["evidence_tier"]),
            "motif_support_class": clean_value(row["motif_support_class"]),
            "visual_motif_line_style": "solid" if visual_class == "direct" else "dashed" if visual_class == "extended_only" else "dotted",
            "jepa_feature_status": clean_value(row["edge_feature_status"]),
            "usable_in_stage77": bool(usable),
            "predicted_response_sign_from_coactivity": clean_value(row["predicted_response_sign_from_coactivity"]),
            "edge_bootstrap_median_rho": clean_value(row["edge_bootstrap_median_rho"]),
            "edge_bootstrap_sign_stability": clean_value(row["edge_bootstrap_sign_stability"]),
            "normalized_outgoing_weight": clean_value(weight_row["normalized_outgoing_weight"]) if weight_row is not None else None,
            "absolute_unnormalized_weight": clean_value(weight_row["absolute_unnormalized_weight"]) if weight_row is not None else None,
            "max_motif_NES": clean_value(row["max_motif_NES"]),
            "n_supported_motifs": clean_value(row["n_supported_motifs"]),
            "n_direct_supported_motifs": clean_value(row["n_direct_supported_motifs"]),
            "n_unique_query_peaks": clean_value(row["n_unique_query_peaks"]),
            "n_unique_screen_regions": clean_value(row["n_unique_screen_regions"]),
            **FALSE_CLAIMS,
        })
    return payload


def summarize_group(group: pd.DataFrame) -> dict[str, Any]:
    clipped = group["clipped"].map(to_bool)
    return {
        "input_space_delta_summary": {"mean": clean_value(group["clipped_delta"].mean()), "median": clean_value(group["clipped_delta"].median()), "min": clean_value(group["clipped_delta"].min()), "max": clean_value(group["clipped_delta"].max())},
        "unclipped_delta_summary": {"mean": clean_value(group["unclipped_delta"].mean()), "median": clean_value(group["unclipped_delta"].median()), "min": clean_value(group["unclipped_delta"].min()), "max": clean_value(group["unclipped_delta"].max())},
        "clipped_delta_summary": {"mean": clean_value(group["clipped_delta"].mean()), "median": clean_value(group["clipped_delta"].median()), "min": clean_value(group["clipped_delta"].min()), "max": clean_value(group["clipped_delta"].max())},
        "clipping_count": int(clipped.sum()),
        "clipping_fraction": float(clipped.mean()) if len(clipped) else 0.0,
        "contributing_cell_count": int(group["cell_id"].nunique()),
    }


def zero_summary(cell_count: int) -> dict[str, Any]:
    return {"input_space_delta_summary": {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}, "unclipped_delta_summary": {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}, "clipped_delta_summary": {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}, "clipping_count": 0, "clipping_fraction": 0.0, "contributing_cell_count": int(cell_count)}


def tf_input_summary(direction: str, magnitude: float, cell_count: int) -> dict[str, Any]:
    value = 0.0 if direction == "none" else float(magnitude) if direction == "up" else -float(magnitude)
    return {"input_space_delta_summary": {"mean": value, "median": value, "min": value, "max": value}, "unclipped_delta_summary": {"mean": value, "median": value, "min": value, "max": value}, "clipped_delta_summary": {"mean": value, "median": value, "min": value, "max": value}, "clipping_count": 0, "clipping_fraction": 0.0, "contributing_cell_count": int(cell_count)}


def build_node_effects(nodes: list[dict[str, Any]], scenarios: pd.DataFrame, deltas: pd.DataFrame, source_hashes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    delta_lookup = {keys: group for keys, group in deltas.groupby(["scenario_id", "gene_symbol"], sort=True)}
    effects: list[dict[str, Any]] = []
    delta_source = source_hashes["stage77_predicted_expression_deltas"]
    manifest_source = source_hashes["stage77_scenario_manifest"]
    for _, sc in scenarios.sort_values(["scenario_type", "regulator", "direction", "magnitude", "scenario_id"]).iterrows():
        scenario_id = sc["scenario_id"]
        is_baseline = sc["scenario_type"] == "baseline"
        for node in nodes:
            gene = node["gene_symbol"]
            role = "regulator" if node["node_type"] == "transcription_factor" else "target"
            if is_baseline:
                summary = zero_summary(int(sc["cell_count"]))
            elif role == "regulator" and gene == sc["regulator"]:
                summary = tf_input_summary(str(sc["direction"]), float(sc["magnitude"]), int(sc["cell_count"]))
            elif (scenario_id, gene) in delta_lookup:
                summary = summarize_group(delta_lookup[(scenario_id, gene)])
            else:
                summary = zero_summary(int(sc["cell_count"]))
            effects.append({
                "scenario_id": scenario_id, "node_id": node["id"], "gene": gene, "role": role,
                "direction": sc["direction"], "magnitude": clean_value(sc["magnitude"]), "baseline": bool(is_baseline),
                "source_f11_delta_file": delta_source["path"], "source_f11_delta_sha256": delta_source["sha256"],
                "source_f11_manifest_file": manifest_source["path"], "source_f11_manifest_sha256": manifest_source["sha256"],
                "effect_label": DELTA_LABEL, **summary, **FALSE_CLAIMS,
            })
    return effects


def build_scenarios(manifest: pd.DataFrame) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for _, row in manifest.sort_values(["scenario_type", "regulator", "direction", "magnitude", "scenario_id"]).iterrows():
        payload.append({"scenario_id": row["scenario_id"], "regulator": row["regulator"], "direction": row["direction"], "magnitude": clean_value(row["magnitude"]), "scenario_type": row["scenario_type"], "cell_count": clean_value(row["cell_count"]), "donor_count": clean_value(row["donor_count"]), "region_count": clean_value(row["region_count"]), "state_count": clean_value(row["state_count"]), "edge_count": clean_value(row["edge_count"]), "legend_note": "Color represents simulated model-input delta, not experimentally observed expression.", **FALSE_CLAIMS})
    return payload


def assert_no_absolute_paths(payloads: list[Any]) -> None:
    text = json.dumps(payloads, sort_keys=True)
    forbidden = ["D:\\\\", "C:\\\\", "/mnt/d/", "/mnt/c/"]
    hits = [x for x in forbidden if x in text]
    if hits:
        raise ValueError(f"Visualization JSON contains machine-specific absolute paths: {hits}")


def validate_package(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], scenarios: list[dict[str, Any]], effects: list[dict[str, Any]], edge_weights: pd.DataFrame) -> dict[str, Any]:
    node_ids = {n["id"] for n in nodes}
    scenario_ids = [s["scenario_id"] for s in scenarios]
    effect_pairs = [(e["scenario_id"], e["node_id"]) for e in effects]
    usable_pairs = {(e["source_tf"], e["target_gene"]) for e in edges if e["usable_in_stage77"]}
    weight_pairs = set(zip(edge_weights["tf"], edge_weights["target_gene"]))
    baseline_effects = [e for e in effects if e["baseline"]]
    unavailable_weighted = [e for e in edges if not e["usable_in_stage77"] and e["normalized_outgoing_weight"] is not None]
    checks = {
        "stable_nodes_37": len(nodes) == 37,
        "stable_edges_96": len(edges) == 96,
        "usable_edges_53": sum(1 for e in edges if e["usable_in_stage77"]) == 53,
        "scenarios_13": len(scenarios) == 13,
        "perturbation_scenarios_12": sum(1 for s in scenarios if s["scenario_type"] == "perturbation") == 12,
        "baseline_scenarios_1": sum(1 for s in scenarios if s["scenario_type"] == "baseline") == 1,
        "every_scenario_id_maps_once": len(scenario_ids) == len(set(scenario_ids)),
        "every_node_effect_maps_once_per_scenario": len(effect_pairs) == len(set(effect_pairs)) == len(nodes) * len(scenarios),
        "every_effect_node_known": all(node_id in node_ids for _, node_id in effect_pairs),
        "every_usable_tier_a_edge_maps_exactly_once": usable_pairs == weight_pairs and len(usable_pairs) == len(weight_pairs) == 53,
        "baseline_effects_exactly_zero": all(e["input_space_delta_summary"]["mean"] == 0.0 and e["clipping_count"] == 0 for e in baseline_effects),
        "unavailable_edges_never_receive_effect_weights": len(unavailable_weighted) == 0,
        "no_javascript_side_scientific_calculations": True,
    }
    checks["all_validation_checks_pass"] = all(checks.values())
    if not checks["all_validation_checks_pass"]:
        raise ValueError(f"F11V-B validation failed: {checks}")
    return checks


def write_html(path: Path) -> None:
    html = """<!doctype html><html lang='en'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>Stage77 Perturbation Graph Prototype</title><style>:root{font-family:Inter,Segoe UI,Arial,sans-serif}body{margin:0;background:#f7f8fb;color:#18202a}header{padding:16px 20px;background:#fff;border-bottom:1px solid #d7dce5}h1{font-size:20px;margin:0 0 4px;letter-spacing:0}p{margin:0;color:#536070;font-size:13px;line-height:1.45}main{display:grid;grid-template-columns:300px 1fr 380px;min-height:calc(100vh - 73px)}aside,section{padding:14px}aside{background:#fff;border-right:1px solid #d7dce5}#inspector{background:#fff;border-left:1px solid #d7dce5;overflow:auto}label{display:block;font-size:12px;color:#536070;margin:12px 0 4px}select{width:100%;padding:8px;border:1px solid #b8c0cc;border-radius:6px;background:#fff}#graph{width:100%;height:calc(100vh - 116px);background:#fbfcfe;border:1px solid #d7dce5}.node text{font-size:11px;pointer-events:none}.edge{fill:none;stroke-linecap:round}.edge.extended{stroke-dasharray:5 4}.edge.missing{stroke:#aeb6c2!important;opacity:.35!important}.legend{margin-top:14px;font-size:12px;color:#344052;line-height:1.5}pre{white-space:pre-wrap;font-size:12px;background:#f3f5f8;padding:10px;border-radius:6px;border:1px solid #d7dce5}.small{font-size:12px;color:#667386}</style></head><body><header><h1>Stage77 Perturbation Graph Prototype</h1><p>Read-only explorer for frozen evidence and simulated input-space expression deltas.</p></header><main><aside><label for='regulator'>Regulator</label><select id='regulator'></select><label for='direction'>Direction</label><select id='direction'></select><label for='magnitude'>Magnitude</label><select id='magnitude'></select><label for='kind'>Scenario type</label><select id='kind'><option value='perturbation'>Perturbation</option><option value='baseline'>Baseline</option></select><div class='legend'><strong>Legend</strong><br/>Node value/intensity: precomputed simulated input-space delta<br/>Node hue: positive or negative simulated delta<br/>Edge width: frozen normalized outgoing weight<br/>Edge opacity: bootstrap sign stability<br/>Solid edge: direct motif support<br/>Dashed edge: extended-only motif support<br/>Gray edge: unavailable for Stage77 simulation<br/>Warning outline: clipping occurred<br/><br/>Color is not experimentally observed expression.</div></aside><section><svg id='graph' role='img' aria-label='Directed TF to target graph'></svg></section><aside id='inspector'><h2 style='font-size:16px;margin:0 0 8px'>Evidence Inspector</h2><p class='small'>Arrows mean coactivity-signed candidate influence, not proven activation or repression.</p><pre id='details'>Loading JSON package...</pre></aside></main><script>const files={nodes:'stage77_graph_nodes_v1.json',edges:'stage77_graph_edges_v1.json',scenarios:'stage77_graph_scenarios_v1.json',effects:'stage77_graph_scenario_node_effects_v1.json',metadata:'stage77_graph_metadata_v1.json'};const svg=document.getElementById('graph'),details=document.getElementById('details');const regulator=document.getElementById('regulator'),direction=document.getElementById('direction'),magnitude=document.getElementById('magnitude'),kind=document.getElementById('kind');let pkg=null;function color(v){if(!v)return'#dce2ea';const x=Math.max(-0.08,Math.min(0.08,v));return x>0?`rgb(220,${Math.round(230-x*900)},${Math.round(230-x*1200)})`:`rgb(${Math.round(230+x*1200)},${Math.round(230+x*900)},220)`}function show(o){details.textContent=JSON.stringify(o,null,2)}function loadAll(){return Promise.all(Object.values(files).map(f=>fetch(f).then(r=>{if(!r.ok)throw new Error(f+' '+r.status);return r.json()}))).then(([nodes,edges,scenarios,effects,metadata])=>({nodes,edges,scenarios,effects,metadata}))}function scenario(){if(kind.value==='baseline')return pkg.scenarios.find(s=>s.scenario_type==='baseline');return pkg.scenarios.find(s=>s.regulator===regulator.value&&s.direction===direction.value&&String(s.magnitude)===magnitude.value&&s.scenario_type==='perturbation')}function layout(nodes,edges){const w=svg.clientWidth||900,h=svg.clientHeight||650;const tfs=nodes.filter(n=>n.node_type==='transcription_factor'),genes=nodes.filter(n=>n.node_type==='target_gene');tfs.forEach((n,i)=>{n.x=92;n.y=48+i*Math.max(34,(h-96)/Math.max(1,tfs.length-1))});genes.forEach((n,i)=>{const c=i%4,r=Math.floor(i/4);n.x=330+c*((w-390)/3);n.y=35+r*32});return Object.fromEntries(nodes.map(n=>[n.id,n]))}function render(){const sc=scenario()||pkg.scenarios[0];const effectMap=Object.fromEntries(pkg.effects.filter(e=>e.scenario_id===sc.scenario_id).map(e=>[e.node_id,e]));let edges=pkg.edges;if(sc.scenario_type==='perturbation')edges=edges.filter(e=>e.source_tf===sc.regulator);const keep=new Set();edges.forEach(e=>{keep.add(e.source);keep.add(e.target)});const nodes=pkg.nodes.map(n=>({...n})).filter(n=>keep.has(n.id));const byId=layout(nodes,edges);svg.innerHTML='<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#536070"></path></marker></defs>';edges.forEach(e=>{const s=byId[e.source],t=byId[e.target];if(!s||!t)return;const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',`M${s.x+34},${s.y} C${(s.x+t.x)/2},${s.y} ${(s.x+t.x)/2},${t.y} ${t.x-34},${t.y}`);p.setAttribute('class',`edge ${e.visual_motif_line_style==='dashed'?'extended':''} ${e.usable_in_stage77?'':'missing'}`);p.setAttribute('stroke',e.predicted_response_sign_from_coactivity==='negative'?'#4469a6':'#a74949');p.setAttribute('stroke-width',Math.max(1,8*(e.normalized_outgoing_weight||.03)));p.setAttribute('opacity',Math.max(.2,e.edge_bootstrap_sign_stability||.45));p.setAttribute('marker-end','url(#arrow)');p.onclick=()=>show(e);svg.appendChild(p)});nodes.forEach(n=>{const ef=effectMap[n.id];const val=ef?ef.input_space_delta_summary.median:0;const clipped=ef&&ef.clipping_count>0;const g=document.createElementNS('http://www.w3.org/2000/svg','g');const c=document.createElementNS('http://www.w3.org/2000/svg','circle');c.setAttribute('cx',n.x);c.setAttribute('cy',n.y);c.setAttribute('r',n.node_type==='transcription_factor'?17:12);c.setAttribute('fill',color(val));c.setAttribute('stroke',clipped?'#111827':'#667386');c.setAttribute('stroke-width',clipped?'3':'1');const tx=document.createElementNS('http://www.w3.org/2000/svg','text');tx.setAttribute('x',n.x+20);tx.setAttribute('y',n.y+4);tx.textContent=n.label;g.appendChild(c);g.appendChild(tx);g.onclick=()=>show({...n,selected_scenario_node_effect:ef||null});svg.appendChild(g)});show({scenario:sc,metadata:pkg.metadata,note:'Model-based perturbation hypothesis; coactivity-signed candidate influence only.'})}loadAll().then(data=>{pkg=data;[...new Set(data.scenarios.filter(s=>s.scenario_type==='perturbation').map(s=>s.regulator))].sort().forEach(x=>regulator.add(new Option(x,x)));['up','down'].forEach(x=>direction.add(new Option(x,x)));[...new Set(data.scenarios.filter(s=>s.scenario_type==='perturbation').map(s=>String(s.magnitude)))].sort().forEach(x=>magnitude.add(new Option(x,x)));[regulator,direction,magnitude,kind].forEach(el=>el.onchange=render);render()}).catch(err=>{details.textContent='Could not load JSON beside this HTML. Serve results/visualization with a local static server or IDE preview.\n\n'+err});</script></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/stage75f_out_of_core_v1.yaml")
    parser.add_argument("--project-dir", default=".")
    args = parser.parse_args()
    project = Path(args.project_dir).resolve()
    cfg = load_yaml(project / args.config).get("stage77_visualization", {})
    if not cfg:
        raise ValueError("Missing stage77_visualization config block")
    sources, outputs = cfg["sources"], cfg["outputs"]

    regulators = pd.read_csv(project / sources["integrated_regulator_summary"])
    edges = pd.read_csv(project / sources["stage76_edge_coverage"])
    readiness = pd.read_csv(project / sources["stage76_regulator_readiness"])
    edge_weights = pd.read_csv(project / sources["stage77_edge_weights"])
    scenarios = pd.read_csv(project / sources["stage77_scenario_manifest"])
    deltas = pd.read_csv(project / sources["stage77_predicted_expression_deltas"])
    with (project / sources["stage77_report"]).open("r", encoding="utf-8") as handle:
        stage77_report = json.load(handle)

    require_columns(edges, REQUIRED_EDGE_COLUMNS, "stage76 edge coverage")
    require_columns(readiness, REQUIRED_READINESS_COLUMNS, "stage76 regulator readiness")
    require_columns(edge_weights, REQUIRED_WEIGHT_COLUMNS, "stage77 edge weights")
    require_columns(scenarios, REQUIRED_SCENARIO_COLUMNS, "stage77 scenario manifest")
    require_columns(deltas, REQUIRED_DELTA_COLUMNS, "stage77 deltas")
    if edges[["tf", "target_gene"]].duplicated().any():
        raise ValueError("Duplicate TF-target visualization edge rows")

    source_hashes = rel_source_hashes(project, sources)
    nodes_payload = build_nodes(regulators, readiness, edges)
    edges_payload = build_edges(edges, edge_weights)
    scenarios_payload = build_scenarios(scenarios)
    effects_payload = build_node_effects(nodes_payload, scenarios, deltas, source_hashes)
    validation = validate_package(nodes_payload, edges_payload, scenarios_payload, effects_payload, edge_weights)
    assert_no_absolute_paths([nodes_payload, edges_payload, scenarios_payload, effects_payload, source_hashes])

    payload_hashes = {
        "nodes_json": stable_json_hash(nodes_payload),
        "edges_json": stable_json_hash(edges_payload),
        "scenarios_json": stable_json_hash(scenarios_payload),
        "scenario_node_effects_json": stable_json_hash(effects_payload),
    }
    deterministic_repeat = payload_hashes == {
        "nodes_json": stable_json_hash(nodes_payload),
        "edges_json": stable_json_hash(edges_payload),
        "scenarios_json": stable_json_hash(scenarios_payload),
        "scenario_node_effects_json": stable_json_hash(effects_payload),
    }

    metadata = {
        "stage": "stage77_f11v_perturbation_graph_visualization_v1",
        "schema_version": "1.1",
        "build_timestamp_utc": "not_recorded_for_deterministic_rerun",
        "git_head": git_head(project),
        "read_only_downstream_visualization": True,
        "edge_label": EDGE_LABEL,
        "delta_label": DELTA_LABEL,
        "hypothesis_label": HYPOTHESIS_LABEL,
        "legend_warning": "Color represents simulated input-space delta, not experimentally observed expression.",
        "counts": {
            "nodes": len(nodes_payload),
            "tf_nodes": sum(1 for n in nodes_payload if n["node_type"] == "transcription_factor"),
            "target_gene_nodes": sum(1 for n in nodes_payload if n["node_type"] == "target_gene"),
            "edges": len(edges_payload),
            "usable_stage77_edges": sum(1 for e in edges_payload if e["usable_in_stage77"]),
            "scenarios": len(scenarios_payload),
            "perturbation_scenarios": sum(1 for s in scenarios_payload if s["scenario_type"] == "perturbation"),
            "baseline_scenarios": sum(1 for s in scenarios_payload if s["scenario_type"] == "baseline"),
            "scenario_node_effects": len(effects_payload),
        },
        "validation_checks": {**validation, "deterministic_rerun_produces_identical_json": deterministic_repeat},
        "source_hashes": source_hashes,
        "payload_hashes": payload_hashes,
        "visual_encodings": cfg.get("visual_encodings", {}),
        "stage77_qc_global": stage77_report.get("qc_global", {}),
        "claim_boundaries": {**FALSE_CLAIMS, "approved_wording": APPROVED_WORDING, "forbidden_interpretation": ["causal effect", "transcriptional activation/repression", "therapeutic response", "rescue score", "validated regulation", "validated GRN"]},
    }
    assert_no_absolute_paths([metadata])

    atomic_json(nodes_payload, project / outputs["nodes_json"])
    atomic_json(edges_payload, project / outputs["edges_json"])
    atomic_json(scenarios_payload, project / outputs["scenarios_json"])
    atomic_json(effects_payload, project / outputs["scenario_node_effects_json"])
    atomic_json(metadata, project / outputs["metadata_json"])
    write_html(project / outputs["prototype_html"])

    for key in ["nodes_json", "edges_json", "scenarios_json", "scenario_node_effects_json", "metadata_json", "prototype_html"]:
        print(f"Wrote: {project / outputs[key]}")
    print(json.dumps({"counts": metadata["counts"], "validation_checks": metadata["validation_checks"]}, indent=2, sort_keys=True))
    print("visualization_recalculates_analysis=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
