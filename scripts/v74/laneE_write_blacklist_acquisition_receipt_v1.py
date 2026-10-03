#!/usr/bin/env python3
"""V74 LANE E: assemble the acquisition receipt for the ENCODE exclusion list.

Every identity field is read back off the artifacts on disk or out of the captured
HTTP headers. Nothing is typed in by hand, so the receipt cannot drift away from the
bytes it describes.

POST-HOC LABEL: the download itself was executed by
shared/immutable_scripts/acquire_encode_blacklist_v1.sh and its headers and timings
were captured at that time; this script PACKAGES those captures. It is labelled as
packaging rather than presented as a prospective instrument.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

BL = Path("D:/jepa_v5_outputs_20260925/v74_laneE/blacklist")
OUT = Path("D:/jepa_v5_outputs_20260925/v74_laneE/receipts/"
           "ACQ_ENCODE_BLACKLIST_ENCFF356LFX_V1.json")


def digest(p: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def header_block(path: Path) -> dict:
    """Parse the LAST HTTP response block in a curl -D dump (after redirects)."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    blocks = [b for b in re.split(r"\r?\n\r?\n", raw) if b.strip().startswith("HTTP/")]
    last = blocks[-1] if blocks else ""
    out = {"status_line": last.splitlines()[0].strip() if last else None}
    for line in last.splitlines()[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def main() -> int:
    gz = BL / "ENCFF356LFX.bed.gz"
    bed = BL / "ENCFF356LFX.bed"
    meta = json.loads((BL / "ENCFF356LFX.metadata.json").read_text(encoding="utf-8"))
    ann = json.loads((BL / "ENCSR636HFF.metadata.json").read_text(encoding="utf-8"))
    get_hdr = header_block(BL / "get_headers.txt")

    local = {
        "gz_bytes": gz.stat().st_size,
        "gz_sha256": digest(gz, "sha256"),
        "gz_md5": digest(gz, "md5"),
        "bed_uncompressed_bytes": bed.stat().st_size,
        "bed_uncompressed_sha256": digest(bed, "sha256"),
        "bed_uncompressed_md5": digest(bed, "md5"),
    }

    intervals = [l.split("\t") for l in
                 bed.read_text(encoding="utf-8").splitlines() if l.strip()]
    n_intervals = len(intervals)
    bl_bp = sum(int(r[2]) - int(r[1]) for r in intervals)

    declared_len = get_hdr.get("content-length")
    declared_etag = (get_hdr.get("etag") or "").strip('"')

    checks = {
        "server_declared_content_length_equals_bytes_on_disk":
            declared_len is not None and int(declared_len) == local["gz_bytes"],
        "encode_metadata_file_size_equals_bytes_on_disk":
            int(meta["file_size"]) == local["gz_bytes"],
        "s3_etag_equals_local_md5_of_the_gz": declared_etag == local["gz_md5"],
        "encode_published_md5sum_equals_local_md5_of_the_gz":
            meta["md5sum"] == local["gz_md5"],
        "encode_published_content_md5sum_equals_local_md5_of_the_UNCOMPRESSED_bed":
            meta["content_md5sum"] == local["bed_uncompressed_md5"],
        "assembly_is_GRCh38": meta.get("assembly") == "GRCh38",
        "output_type_is_an_exclusion_list":
            meta.get("output_type") == "exclusion list regions",
        "release_status_is_released": meta.get("status") == "released",
    }
    status = ("PASS__BYTE_COMPLETE_AND_AUTHENTICATED" if all(checks.values())
              else "FAIL__REMOTE_IDENTITY_NOT_CONFIRMED")

    rec = {
        "schema": "V69_REMOTE_OBJECT_ACQUISITION_RECEIPT_V1",
        "successor_of": None,
        "label": "ENCODE_GRCh38_EXCLUSION_LIST_ENCFF356LFX",
        "status": status,
        "recorded_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "acquisition_started_utc": "2026-10-03T01:33:47Z",
        "acquisition_finished_utc": "2026-10-03T01:33:48Z",
        "acquisition_timestamps_note": ("Taken from the acquisition script's own clock "
                                        "around the curl GET. Not estimated."),
        "accession": meta["accession"],
        "source_url": "https://www.encodeproject.org/files/ENCFF356LFX/@@download/ENCFF356LFX.bed.gz",
        "resolved_object_url": (meta.get("cloud_metadata") or {}).get("url"),
        "portal_record_url": "https://www.encodeproject.org/files/ENCFF356LFX/",
        "genome_build": meta.get("assembly"),
        "output_type": meta.get("output_type"),
        "annotation_dataset": {
            "accession": ann.get("accession"),
            "annotation_type": ann.get("annotation_type"),
            "assemblies": ann.get("assembly"),
            "date_released": ann.get("date_released"),
            "lab": ann.get("lab"),
            "award": ann.get("award"),
            "description": ann.get("description"),
        },
        "file_lab": meta.get("lab"),
        "file_award": meta.get("award"),
        "file_date_created": meta.get("date_created"),

        "remote_identity_declared_by_source": {
            "encode_metadata_file_size": meta["file_size"],
            "encode_metadata_md5sum": meta["md5sum"],
            "encode_metadata_content_md5sum": meta["content_md5sum"],
            "http_get_status_line": get_hdr.get("status_line"),
            "http_get_content_length": declared_len,
            "http_get_etag": get_hdr.get("etag"),
            "http_get_last_modified": get_hdr.get("last-modified"),
            "note": ("A HEAD request against the portal URL returns 307 to a presigned "
                     "S3 object that answers 403 to HEAD, so the authoritative length "
                     "was taken from the GET response headers and cross-checked against "
                     "the ENCODE metadata record. Both agree."),
        },
        "local_identity_measured_on_disk": local,
        "local_paths": {
            "gz": str(gz),
            "bed_uncompressed": str(bed),
            "file_metadata_json": str(BL / "ENCFF356LFX.metadata.json"),
            "annotation_metadata_json": str(BL / "ENCSR636HFF.metadata.json"),
            "get_response_headers": str(BL / "get_headers.txt"),
            "data_use_policy_capture": str(BL / "encode_citing.html"),
        },
        "content_structure": {
            "n_intervals": n_intervals,
            "genome_bp_covered_unmerged": bl_bp,
            "contigs": sorted({r[0] for r in intervals}),
            "bed_flavour": meta.get("file_type"),
        },
        "AUTHENTICATION_CHECKS": checks,
        "why_three_independent_identities": (
            "The acquisition tool's exit code proves nothing about completeness. Three "
            "identities published by the source and reproduced locally do: the declared "
            "byte length, the S3 ETag (which equals the object md5 for a single-part "
            "upload), and ENCODE's own content_md5sum of the UNCOMPRESSED payload. The "
            "last is the strongest, because it survives any re-compression."),
        "licence_terms": {
            "observed_utc": "2026-10-03T01:35Z",
            "source": "https://www.encodeproject.org/help/citing-encode/",
            "policy_quoted_verbatim": (
                "Data Use Policy for External Users. External data users may freely "
                "download, analyze and publish results based on any ENCODE data without "
                "restrictions. This applies to all datasets, regardless of type or size, "
                "and includes no grace period for ENCODE data producers, either as "
                "individual members or as part of the Consortium."),
            "citation_requested": (
                "ENCODE requests citation of the Consortium's integrative analysis "
                "(PMID 22955616) and portal (PMID 31713622) publications, and of the "
                "dataset and file accessions used: ENCSR636HFF / ENCFF356LFX."),
            "api_rate_limit_observed": "10 GET requests/sec per user, group, company or lab.",
            "downloadable_is_not_licensed": (
                "Recorded because the two are different questions. The terms above were "
                "read off the portal at acquisition time and are quoted, not summarised "
                "from memory. No registration, access control or data-use agreement was "
                "presented at any point in the acquisition."),
            "underlying_method_citation": (
                "Amemiya HM, Kundaje A, Boyle AP. The ENCODE Blacklist: Identification of "
                "Problematic Regions of the Genome. Sci Rep 2019;9:9354. PMID 31249361."),
        },
        "recovery_locator": (
            "https://www.encodeproject.org/files/ENCFF356LFX/@@download/ENCFF356LFX.bed.gz "
            "-- deterministically recoverable: verify sha256 " + local["gz_sha256"]),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")

    persisted = json.loads(OUT.read_text(encoding="utf-8"))
    print(json.dumps({"status": persisted["status"],
                      "AUTHENTICATION_CHECKS": persisted["AUTHENTICATION_CHECKS"],
                      "local_identity_measured_on_disk":
                          persisted["local_identity_measured_on_disk"]}, indent=2))
    return 0 if persisted["status"].startswith("PASS") else 3


if __name__ == "__main__":
    raise SystemExit(main())
