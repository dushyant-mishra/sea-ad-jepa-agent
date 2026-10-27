#!/usr/bin/env python3
"""Bounded, public-metadata-only E2G GraphQL connectivity probe.

Never requests genomic rows, predictions, private data, or GCS objects.
Do not treat transport failures as a negative biological finding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from collections import Counter

CHECK = "query Health { __typename }"
TRACKS = """query E2GPublicTracks {
  getDataTracks { cellTypeId cellType study dataset modelType }
}"""
SCHEMA = """query E2GQueryFieldNames {
  __schema { queryType { fields { name } } }
}"""
MAX_BODY = 6_000_000


def post(endpoint: str, query: str, timeout: int) -> dict:
    payload = json.dumps({"query": query}).encode("utf-8")
    request = urllib.request.Request(
        endpoint, data=payload, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "JEPA-External-E2G-Source-Audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        data = response.read(MAX_BODY + 1)
    if len(data) > MAX_BODY:
        raise RuntimeError("Response exceeded fixed 6MB bound")
    obj = json.loads(data)
    if not isinstance(obj, dict) or obj.get("errors"):
        raise RuntimeError("GraphQL error: " + str(obj.get("errors", "bad root"))[:450])
    if not isinstance(obj.get("data"), dict):
        raise RuntimeError("Missing GraphQL data payload")
    return obj["data"]


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--endpoint", default="https://e2g.stanford.edu/graphql")
    cli.add_argument("--timeout", type=int, default=15)
    args = cli.parse_args()
    if args.endpoint != "https://e2g.stanford.edu/graphql":
        print("Refusing unreviewed API endpoint", file=sys.stderr)
        return 2
    if not 2 <= args.timeout <= 30:
        print("Timeout out of bounds", file=sys.stderr)
        return 2
    try:
        health = post(args.endpoint, CHECK, args.timeout)
        if health.get("__typename") is None:
            raise RuntimeError("No health __typename")
        metadata = post(args.endpoint, TRACKS, args.timeout)
        tracks = metadata.get("getDataTracks")
        if not isinstance(tracks, list):
            raise RuntimeError("getDataTracks did not return a list")
        if any(not isinstance(t, dict) for t in tracks):
            raise RuntimeError("Unrecognized data tracks shape")
        seen = sorted(set(
            (str(t.get("cellType") or ""), str(t.get("study") or ""),
             str(t.get("modelType") or "")) for t in tracks
        ))
        relevant = [x for x in seen if any(term in x[0].lower()
                    for term in ("microgl", "macroph", "myeloid", "monocyt", "brain", "astrocyt"))]
        try:
            schema = post(args.endpoint, SCHEMA, args.timeout)
            fields = schema["__schema"]["queryType"]["fields"]
            e2g_fields = sorted(f["name"] for f in fields
                                if any(k in f["name"].lower()
                                       for k in ("enhancer", "e2g", "gene", "track", "celltype")))
            schema_state = "AVAILABLE"
        except (KeyError, TypeError, ValueError, RuntimeError, OSError) as schema_exc:
            e2g_fields = []
            schema_state = "UNAVAILABLE_" + type(schema_exc).__name__
        print(json.dumps({
            "api_probe_status": "LIVE_PUBLIC_GRAPHQL_METADATA_RETURNED",
            "endpoint": args.endpoint,
            "operations": ["Health", "E2GPublicTracks", "E2GQueryFieldNames"],
            "graphql_schema_status": schema_state,
            "graph_ql_e2g_related_query_fields": e2g_fields,
            "tracks_count": len(tracks),
            "distinct_context_triplets": len(seen),
            "model_family_counts": dict(sorted(Counter(
                str(t.get("modelType") or "unspecified") for t in tracks
            ).items())),
            "relevant_context_triplets_found": len(relevant),
            "microglia_labelled_tracks": sum(
                "microgl" in str(t.get("cellType") or "").lower() for t in tracks
            ),
            "microglia_labelled_contexts": [
                list(x) for x in seen if "microgl" in x[0].lower()
            ],
            "relevant_context_examples": relevant[:40],
            "biological_validation": None,
            "authority": "METADATA_ONLY__NO_TARGET_SELECTION_OR_TRAINING",
        }, indent=2))
        return 0
    except (OSError, TimeoutError, ValueError, RuntimeError, urllib.error.HTTPError) as exc:
        print(json.dumps({
            "api_probe_status": "LIVE_ACCESS_NOT_CONFIRMED",
            "endpoint": args.endpoint, "error_class": type(exc).__name__,
            "error": str(exc)[:350],
            "interpretation": "Transport or GraphQL failure; no claim about absence of E2G data",
            "authority": "NO_TARGET_SELECTION_OR_TRAINING",
        }, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
