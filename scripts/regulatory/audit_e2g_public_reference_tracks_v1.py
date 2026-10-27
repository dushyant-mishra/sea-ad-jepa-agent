#!/usr/bin/env python3
"""Source-qualified, metadata-only inventory of public E2G reference tracks.

No enhancer rows, per-gene predictions, object downloads, Google Cloud calls,
or training. Unsafe/unknown hosts remain unvisited. This is not validation.
"""
from __future__ import annotations

import argparse
import collections
import json
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://e2g.stanford.edu/graphql"
QUERY = """query ReferenceTracks {
 getDataTracks {
   id cellTypeId cellType study studyId dataset datasetUrl paperUrl
   modelType e2gPredictionsUrl elementsUrl atacSignalUrl dnaseSignalUrl
 }
}"""
MAX_RESPONSE = 8_000_000
# Pattern ordering: specific labels first, so broad "brain" never hides myeloid.
TERMS = (
    ("explicit_microglia", ("microgl",)),
    ("macrophage_context", ("macroph",)),
    ("monocyte_context", ("monocyt",)),
    ("other_myeloid_context", ("myeloid", "dendritic cell")),
    ("brain_context", ("brain", "midbrain", "cerebell", "hippocamp")),
    ("astrocyte_context", ("astrocyt",)),
)


def category(celltype: str) -> str | None:
    val = celltype.lower()
    for name, terms in TERMS:
        if any(term in val for term in terms):
            return name
    return None


def safe_url_info(url: object) -> dict:
    if not isinstance(url, str) or not url.strip():
        return {"available": False, "host": None, "https": False}
    parsed = urllib.parse.urlsplit(url)
    return {
        "available": True, "host": (parsed.hostname or "").lower(),
        "https": parsed.scheme == "https",
        # Never store query strings: they can contain signed credentials.
        "path_suffix": parsed.path.rsplit("/", 1)[-1][:100],
    }


def summarize(tracks: list[dict]) -> dict:
    if not isinstance(tracks, list) or not all(isinstance(x, dict) for x in tracks):
        raise ValueError("Invalid getDataTracks response")
    chosen = []
    classes = collections.Counter()
    host_counts = collections.Counter()
    model_counts = collections.Counter()
    for track in tracks:
        label = track.get("cellType") or ""
        if not isinstance(label, str):
            raise ValueError("Bad cell type")
        model_counts[str(track.get("modelType") or "unknown")] += 1
        pred = safe_url_info(track.get("e2gPredictionsUrl"))
        if pred["available"]:
            host_counts[pred["host"] or "unknown"] += 1
        role = category(label)
        if role is None:
            continue
        classes[role] += 1
        # Data URLs are intentionally reduced to host and basename (no auth/query).
        chosen.append({
            "cell_type": label,
            "cell_type_id": str(track.get("cellTypeId") or ""),
            "study": str(track.get("study") or ""),
            "study_id": str(track.get("studyId") or ""),
            "dataset": str(track.get("dataset") or ""),
            "model": str(track.get("modelType") or ""),
            "e2g_prediction_url": pred,
            "dataset_url": safe_url_info(track.get("datasetUrl")),
            "element_url": safe_url_info(track.get("elementsUrl")),
            "context_role": role,
            "permitted_claim": "REGULATORY_REFERENCE_CONTEXT_ONLY",
        })
    chosen.sort(key=lambda x: (
        list(dict(TERMS)).index(x["context_role"]),
        x["cell_type"].lower(), x["study"].lower(), x["model"],
    ))
    return {
        "schema": "JEPA_PUBLIC_E2G_TRACK_CONTEXT_INVENTORY_V1",
        "status": "METADATA_ONLY__NO_PREDICTIONS_EVALUATED",
        "source_endpoint": ENDPOINT, "total_track_rows": len(tracks),
        "model_counts": dict(sorted(model_counts.items())),
        "prediction_url_hosts": dict(sorted(host_counts.items())),
        "categories": dict(sorted(classes.items())),
        "selected_rows": chosen,
        "source_context_authority": {
            "adult_human_microglia_proven": False,
            "species_proven": False,
            "development_exposure_reconciled": False,
            "regulatory_validation": False,
            "causal_validation": False,
            "target_selection": False, "real_training": False,
        },
    }


def read_endpoint(timeout: int) -> list[dict]:
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps({"query": QUERY}).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json",
                 "Accept": "application/json",
                 "User-Agent": "JEPA-E2G-Reference-Intake/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        if resp.status != 200:
            raise ValueError(f"Non-200 GraphQL response: {resp.status}")
        raw = resp.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("GraphQL metadata exceeded byte cap")
    obj = json.loads(raw)
    if obj.get("errors") or not isinstance(obj.get("data"), dict):
        raise ValueError("GraphQL returned errors or unexpected schema")
    return obj["data"]["getDataTracks"]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--timeout", type=int, default=15)
    args = p.parse_args()
    if not 1 <= args.timeout <= 30:
        raise ValueError("Timeout outside safe range")
    data = summarize(read_endpoint(args.timeout))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        k: v for k, v in data.items() if k not in ("selected_rows", "source_context_authority")
    }, indent=2))
    print("selected_rows_count=", len(data["selected_rows"]))


if __name__ == "__main__":
    main()
