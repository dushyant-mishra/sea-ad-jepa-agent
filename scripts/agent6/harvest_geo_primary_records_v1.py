#!/usr/bin/env python3
"""Agent 6 external dataset registry: GEO primary-record harvester.

Fetches the machine-readable GEO SOFT records for a frozen accession list and
transcribes ONLY what the deposit itself states. Nothing is estimated. Any field
the deposit does not state is emitted as the literal string
``NOT_STATED_IN_DEPOSIT``.

Endpoints are NCBI's own machine-readable records, not a mirror, a review, or a
summary site:

    series brief : acc.cgi?acc=<GSE>&targ=self&form=text&view=brief
    sample brief : acc.cgi?acc=<GSE>&targ=gsm&form=text&view=brief
    suppl sizes  : ftp.ncbi.nlm.nih.gov/geo/series/<GSEnnn>/<GSE>/suppl/filelist.txt

Usage:
    python harvest_geo_primary_records_v1.py \\
        --accessions GSE174367 GSE214979 --out-dir <dir>
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.request

NOT_STATED = "NOT_STATED_IN_DEPOSIT"
UA = "jepa-agent6-registry/1.0"
ACC_CGI = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"


def fetch(url, retries=3, pause=1.0):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as fh:
                return fh.read()
        except Exception as exc:  # noqa: BLE001 - public-record reconnaissance
            last = exc
            time.sleep(pause * (attempt + 1))
    raise RuntimeError("fetch failed for {0}: {1}".format(url, last))


def series_brief_url(acc):
    return "{0}?acc={1}&targ=self&form=text&view=brief".format(ACC_CGI, acc)


def sample_brief_url(acc):
    return "{0}?acc={1}&targ=gsm&form=text&view=brief".format(ACC_CGI, acc)


def suppl_dir_url(acc):
    stem = acc[:-3] + "nnn" if len(acc) > 6 else acc
    return "https://ftp.ncbi.nlm.nih.gov/geo/series/{0}/{1}/suppl/".format(stem, acc)


def filelist_url(acc):
    return suppl_dir_url(acc) + "filelist.txt"


_DIR_ROW = re.compile(
    r'<a href="(?P<name>[^"/][^"]*)">[^<]*</a>\s*'
    r"(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(?P<size>[0-9.]+[KMG]?)",
    re.IGNORECASE,
)
_UNITS = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}


def parse_suppl_dir(html):
    """Parse the NCBI FTP-over-HTTP directory index for supplementary file sizes.

    NCBI renders sizes in human units (e.g. ``1.3G``). Those are the deposit's own
    rendering and are recorded as such: ``bytes_approx_from_dir_index`` is a
    UNIT-ROUNDED size, explicitly not an exact byte count. filelist.txt, when the
    series has one, carries exact bytes and is preferred.
    """
    rows = []
    for m in _DIR_ROW.finditer(html):
        name = m.group("name")
        if name.startswith("?") or name.startswith("/"):
            continue
        raw = m.group("size")
        if raw[-1] in _UNITS:
            approx = int(float(raw[:-1]) * _UNITS[raw[-1]])
        else:
            try:
                approx = int(float(raw))
            except ValueError:
                continue
        rows.append(
            {"name": name, "bytes_approx_from_dir_index": approx, "size_as_rendered": raw}
        )
    return rows


def soft_fields(text, prefix):
    out = collections.defaultdict(list)
    for line in text.splitlines():
        if not line.startswith("!") or " = " not in line:
            continue
        key, val = line[1:].split(" = ", 1)
        if key.startswith(prefix):
            out[key].append(val.strip())
    return dict(out)


def first(fields, key):
    vals = fields.get(key)
    return vals[0] if vals else NOT_STATED


def parse_samples(text):
    """Parse the per-sample SOFT brief block. Every count here is a transcription."""
    blocks = text.split("^SAMPLE = ")[1:]
    recs = []
    for block in blocks:
        acc = block.split("\n", 1)[0].strip()
        fields = soft_fields(block, "Sample_")
        chars = fields.get("Sample_characteristics_ch1", [])
        char_map = {}
        for entry in chars:
            if ":" in entry:
                key, val = entry.split(":", 1)
                char_map[key.strip().lower()] = val.strip()
        recs.append(
            {
                "gsm": acc,
                "title": first(fields, "Sample_title"),
                "library_strategy": first(fields, "Sample_library_strategy"),
                "library_source": first(fields, "Sample_library_source"),
                "platform_id": first(fields, "Sample_platform_id"),
                "organism": first(fields, "Sample_organism_ch1"),
                "source_name": first(fields, "Sample_source_name_ch1"),
                "characteristics": chars,
                "char_map": char_map,
            }
        )
    return recs


DONOR_KEYS = (
    "donor", "donor id", "donor_id", "donorid", "subject", "subject id",
    "patient", "patient id", "individual", "individual id", "case",
    "brain id", "specimen", "projid", "rosmap id", "sample id", "sampleid",
)
DX_KEYS = (
    "diagnosis", "disease", "disease state", "condition", "group",
    "phenotype", "clinical diagnosis", "braak", "neuropathology",
    "disease status",
)


def summarize(acc, series_txt, sample_txt, filelist_txt, suppl_dir_html=None):
    sf = soft_fields(series_txt, "Series_")
    recs = parse_samples(sample_txt)

    strat = collections.Counter(r["library_strategy"] for r in recs)
    plat = collections.Counter(r["platform_id"] for r in recs)
    org = collections.Counter(r["organism"] for r in recs)

    charkeys = collections.Counter()
    for rec in recs:
        for key in rec["char_map"]:
            charkeys[key] += 1

    donor_key = next((k for k in DONOR_KEYS if k in charkeys), None)
    if donor_key is not None:
        donors = set()
        for rec in recs:
            val = rec["char_map"].get(donor_key)
            if val:
                donors.add(val)
        donor_n = len(donors)
        donor_basis = "unique values of characteristics field '{0}'".format(donor_key)
    else:
        donor_n = NOT_STATED
        donor_basis = (
            "no donor/subject/individual characteristics field present in the deposit; "
            "donor count is NOT derivable from GEO alone and must not be estimated"
        )

    dx_key = next((k for k in DX_KEYS if k in charkeys), None)
    if dx_key is not None:
        dx_counts = dict(
            collections.Counter(r["char_map"].get(dx_key, NOT_STATED) for r in recs)
        )
    else:
        dx_counts = NOT_STATED

    shapes = collections.Counter(re.sub(r"\d+", "#", r["title"]) for r in recs)

    suppl_rows = NOT_STATED
    suppl_bytes = NOT_STATED
    suppl_basis = "no supplementary listing retrievable from the GEO FTP tree"
    if filelist_txt:
        rows = []
        total = 0
        for line in filelist_txt.splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) >= 3:
                name = parts[0].strip()
                try:
                    size_i = int(parts[1].strip())
                except ValueError:
                    continue
                rows.append({"name": name, "bytes": size_i})
                total += size_i
        if rows:
            suppl_rows = rows
            suppl_bytes = total
            suppl_basis = "exact bytes from the series' own filelist.txt"
    if suppl_rows is NOT_STATED and suppl_dir_html:
        rows = parse_suppl_dir(suppl_dir_html)
        if rows:
            suppl_rows = rows
            suppl_bytes = sum(r["bytes_approx_from_dir_index"] for r in rows)
            suppl_basis = (
                "UNIT-ROUNDED sizes parsed from the NCBI FTP directory index; "
                "series has no filelist.txt, so exact byte counts are "
                + NOT_STATED
            )

    return {
        "accession": acc,
        "primary_record_endpoints": {
            "series": series_brief_url(acc),
            "samples": sample_brief_url(acc),
            "filelist": filelist_url(acc),
        },
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "series": {
            "title": first(sf, "Series_title"),
            "status": first(sf, "Series_status"),
            "submission_date": first(sf, "Series_submission_date"),
            "last_update_date": first(sf, "Series_last_update_date"),
            "pubmed_id": sf.get("Series_pubmed_id", [NOT_STATED]),
            "overall_design": first(sf, "Series_overall_design"),
            "summary": first(sf, "Series_summary"),
            "types": sf.get("Series_type", [NOT_STATED]),
            "contributors": sf.get("Series_contributor", [NOT_STATED]),
            "contact_institute": first(sf, "Series_contact_institute"),
            "relations": sf.get("Series_relation", [NOT_STATED]),
            "n_sample_ids_in_series_record": len(sf.get("Series_sample_id", [])),
        },
        "samples": {
            "n_samples_listed": len(recs),
            "library_strategy_counts": dict(strat),
            "platform_counts": dict(plat),
            "organism_counts": dict(org),
            "characteristics_keys": dict(charkeys),
            "donor_field": donor_key if donor_key is not None else NOT_STATED,
            "n_unique_donor_values": donor_n,
            "donor_count_basis": donor_basis,
            "diagnosis_field": dx_key if dx_key is not None else NOT_STATED,
            "diagnosis_counts": dx_counts,
            "title_shapes": dict(shapes),
        },
        "supplementary": {
            "rows": suppl_rows,
            "total_bytes": suppl_bytes,
            "size_basis": suppl_basis,
        },
        "sha256_of_retrieved": {
            "series_brief": hashlib.sha256(
                series_txt.encode("utf-8", "replace")
            ).hexdigest(),
            "sample_brief": hashlib.sha256(
                sample_txt.encode("utf-8", "replace")
            ).hexdigest(),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accessions", nargs="+", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--pause", type=float, default=0.8)
    args = parser.parse_args()

    out = pathlib.Path(args.out_dir)
    (out / "raw").mkdir(parents=True, exist_ok=True)

    results = {}
    for acc in args.accessions:
        try:
            series_txt = fetch(series_brief_url(acc)).decode("utf-8", "replace")
            time.sleep(args.pause)
            sample_txt = fetch(sample_brief_url(acc)).decode("utf-8", "replace")
            time.sleep(args.pause)
            try:
                filelist_txt = fetch(filelist_url(acc)).decode("utf-8", "replace")
                if "<html" in filelist_txt[:400].lower():
                    filelist_txt = None  # NCBI 404 page, not a filelist
            except Exception:  # noqa: BLE001 - absence of a filelist is itself a fact
                filelist_txt = None
            try:
                suppl_dir_html = fetch(suppl_dir_url(acc)).decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                suppl_dir_html = None
            (out / "raw" / (acc + "_series_brief.txt")).write_text(
                series_txt, encoding="utf-8"
            )
            (out / "raw" / (acc + "_sample_brief.txt")).write_text(
                sample_txt, encoding="utf-8"
            )
            if filelist_txt:
                (out / "raw" / (acc + "_filelist.txt")).write_text(
                    filelist_txt, encoding="utf-8"
                )
            if suppl_dir_html:
                (out / "raw" / (acc + "_suppl_dir_index.html")).write_text(
                    suppl_dir_html, encoding="utf-8"
                )
            results[acc] = summarize(
                acc, series_txt, sample_txt, filelist_txt, suppl_dir_html
            )
            print(
                "OK {0}: {1} GSMs".format(
                    acc, results[acc]["samples"]["n_samples_listed"]
                ),
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            results[acc] = {"accession": acc, "error": str(exc)}
            print("FAIL {0}: {1}".format(acc, exc), file=sys.stderr, flush=True)
        time.sleep(args.pause)

    dest = out / "geo_primary_records.json"
    dest.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print("wrote {0}".format(dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
