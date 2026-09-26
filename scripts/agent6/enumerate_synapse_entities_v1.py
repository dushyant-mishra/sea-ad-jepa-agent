#!/usr/bin/env python3
"""Agent 6 external dataset registry: Synapse / AD Knowledge Portal enumerator.

Reads the Synapse repository service's own entity metadata and child listings
(public endpoints, no credentials, no file downloads) so that library counts and
file inventories for controlled-access studies come from the primary record
rather than from a paper's prose or a portal summary page.

Listing an entity's children is NOT the same as being able to download it.
Controlled-access studies expose their file *names* publicly while the file
*bytes* require a Data Use Certificate. That distinction is recorded per entity
as ``listing_is_public_download_is_not``.

Usage:
    python enumerate_synapse_entities_v1.py --entities syn66271521 syn66271522 \\
        --out-dir <dir>
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import time
import urllib.request

REPO = "https://repo-prod.prod.sagebase.org/repo/v1"
UA = "jepa-agent6-registry/1.0"
NOT_STATED = "NOT_STATED_IN_DEPOSIT"


def _request(url, data=None):
    headers = {"User-Agent": UA}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as fh:
        return json.loads(fh.read().decode("utf-8"))


def entity(syn_id):
    return _request("{0}/entity/{1}".format(REPO, syn_id))


def children(parent_id, max_pages=200):
    out = []
    token = None
    for _ in range(max_pages):
        payload = {
            "parentId": parent_id,
            "includeTypes": ["folder", "file"],
            "sortBy": "NAME",
            "sortDirection": "ASC",
        }
        if token:
            payload["nextPageToken"] = token
        res = _request("{0}/entity/children".format(REPO), payload)
        out.extend(res.get("page", []))
        token = res.get("nextPageToken")
        if not token:
            break
        time.sleep(0.2)
    return out


def sample_stems(names):
    """Group file names by the token before the first '.' -- the library/sample stem.

    This is a transcription of the deposit's own file naming, not an inference
    about biology. A stem is a LIBRARY identifier unless the deposit states
    otherwise; it must never be read as a donor count.
    """
    stems = collections.Counter()
    exts = collections.Counter()
    for name in names:
        stems[name.split(".")[0]] += 1
        m = re.search(r"\.([a-z0-9]+(?:\.gz)?)$", name, re.IGNORECASE)
        exts[m.group(1).lower() if m else NOT_STATED] += 1
    return stems, exts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entities", nargs="+", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--recurse", action="store_true")
    args = parser.parse_args()

    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    results = {}
    for syn_id in args.entities:
        rec = {"syn_id": syn_id}
        try:
            meta = entity(syn_id)
            rec["name"] = meta.get("name")
            rec["concrete_type"] = meta.get("concreteType", "").split(".")[-1]
            rec["parent_id"] = meta.get("parentId")
            rec["created_on"] = meta.get("createdOn")
            rec["modified_on"] = meta.get("modifiedOn")

            kids = children(syn_id)
            files = [k for k in kids if k["type"].endswith("FileEntity")]
            folders = [k for k in kids if k["type"].endswith("Folder")]
            rec["n_child_files"] = len(files)
            rec["n_child_folders"] = len(folders)
            rec["child_folder_names"] = [f["name"] for f in folders][:100]

            names = [f["name"] for f in files]
            stems, exts = sample_stems(names)
            rec["n_unique_file_stems"] = len(stems)
            rec["file_stem_note"] = (
                "unique leading tokens of deposited file names; these are LIBRARY / "
                "sample identifiers. Donor count is " + NOT_STATED + " from file "
                "names alone and must not be inferred from this number."
            )
            rec["extension_counts"] = dict(exts)
            rec["example_file_names"] = names[:12]
            rec["listing_is_public_download_is_not"] = True
            rec["file_bytes"] = (
                NOT_STATED + " - the public children listing does not return file "
                "sizes; sizes require an authenticated entity bundle request"
            )

            if args.recurse and folders:
                sub = {}
                for folder in folders[:40]:
                    fk = children(folder["id"])
                    fkf = [k for k in fk if k["type"].endswith("FileEntity")]
                    s2, _ = sample_stems([k["name"] for k in fkf])
                    sub[folder["name"]] = {
                        "syn_id": folder["id"],
                        "n_files": len(fkf),
                        "n_unique_file_stems": len(s2),
                        "example": [k["name"] for k in fkf][:6],
                    }
                    time.sleep(0.2)
                rec["subfolders"] = sub
            print(
                "OK {0} {1}: {2} files / {3} folders".format(
                    syn_id, rec["name"], len(files), len(folders)
                ),
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            rec["error"] = str(exc)
            print("FAIL {0}: {1}".format(syn_id, exc), flush=True)
        rec["retrieved_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rec["endpoint"] = "{0}/entity/{1} and {0}/entity/children".format(REPO, syn_id)
        results[syn_id] = rec
        time.sleep(0.3)

    dest = out / "synapse_primary_records.json"
    dest.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print("wrote {0}".format(dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
