#!/usr/bin/env python3
"""Retrieve *public* seven E2G browser tracks for offline reproducibility.

Uses the same allowlisted and byte-bounded downloader as the predeclared
seven-track source survey. Verifies exact source SHA256 from the frozen
non-authorizing receipt. No private data and no requester-pays bucket access.
The public genomic rows are staged ONLY in ephemeral CI artifact storage,
never committed to Git.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from survey_e2g_public_7tracks_v1 import (
    PANEL, MAX_TOTAL, bounded_public_download, public_sources
)

EXPECTED = Path("results/regulatory/e2g_public_7track_provisional_result_receipt_v1_20261027.json")


def main() -> None:
    if len(sys.argv)!=2:
        raise SystemExit("Usage: export_public_7track_audit_bundle_v1.py OUTPUT_DIRECTORY")
    dest=Path(sys.argv[1])
    receipt=json.loads(EXPECTED.read_text(encoding="utf-8"))
    expected={x["source_id"]:x for x in receipt["source_results"]}
    if len(expected)!=7 or set(expected)!=set(PANEL):
        raise RuntimeError("Expected source identity panel drift")
    chosen=public_sources()
    # Fail-closed preflight of *all* seven metadata fields prior to any download.
    for sid in PANEL:
        meta=chosen[sid]
        expected_basename=expected[sid]["source_id"]
        from urllib.parse import urlsplit
        basename=urlsplit(meta["e2gPredictionsUrl"]).path.rsplit("/",1)[-1]
        known={
          "inflammatory_macrophage_ENCSR593WXK":"encode_e2g_predictions_inflammatory_macrophage_ENCSR593WXK_thresholded_predictions.bedpe.gz",
          "inflammatory_macrophage_ENCSR643ZGR":"encode_e2g_predictions_inflammatory_macrophage_ENCSR643ZGR_thresholded_predictions.bedpe.gz",
          "inflammatory_macrophage_ENCSR226JLK":"encode_e2g_predictions_inflammatory_macrophage_ENCSR226JLK_thresholded_predictions.bedpe.gz",
          "Macrophage":"Macrophage_encode_e2g_predictions_threshold0.173.bedpe",
          "Immune_monocyte_1":"Immune_monocyte_1_encode_e2g_predictions_threshold0.173.bedpe",
          "brain_ENCSR344FLH":"encode_e2g_predictions_brain_ENCSR344FLH_thresholded_predictions.bedpe.gz",
          "Stitziel_hCA_Myeloid":"encode_e2g_predictions_threshold0.177.bedpe",
        }
        if basename!=known[sid]:
            raise RuntimeError("Unexpected exact track basename for "+sid)
    dest.mkdir(parents=True, exist_ok=True)
    total=0
    manifest={"schema":"E2G_PUBLIC_7TRACK_EXTERNAL_BUNDLE_V1",
              "source":"https://e2g.stanford.edu/graphql",
              "method":"PUBLIC_HTTPS__NO_CLOUD_BILLING",
              "sources":[]}
    for sid in PANEL:
        from urllib.parse import urlsplit
        url=chosen[sid]["e2gPredictionsUrl"]
        body,digest=bounded_public_download(url,MAX_TOTAL-total)
        if digest!=expected[sid]["source_sha256"]:
            raise RuntimeError("Published track content changed: "+sid)
        total+=len(body)
        filename=urlsplit(url).path.rsplit("/",1)[-1]
        (dest/filename).write_bytes(body)
        manifest["sources"].append({
            "id":sid,"filename":filename,"sha256":digest,
            "byte_count":len(body),
            "model":chosen[sid]["modelType"],
            "cell_type":chosen[sid]["cellType"]
        })
    (dest/"_SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"status":"SEVEN_PUBLIC_SOURCES_SHA256_VERIFIED",
      "sources":len(manifest["sources"]),"downloaded_bytes":total,
      "no_training":True,"no_private_data":True,"cloud_billing":False},indent=2))


if __name__=="__main__":
    main()
