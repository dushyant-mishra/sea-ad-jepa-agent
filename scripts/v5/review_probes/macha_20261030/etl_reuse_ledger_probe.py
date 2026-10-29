"""ETL verification reuse ledger (custody only; reads no expression values).

usage: python -I etl_reuse_ledger_probe.py <repo-root> <stage81a3r-root> <git-dir> > ledger.json

For every artifact named by an existing authority manifest it records the original
SHA-256, the authority that verified it, and whether today's bytes are identical.
Files up to REHASH_LIMIT bytes are re-hashed (cheap, demonstrable identity); larger
files are only stat'ed and rely on their existing receipt, as instructed. The
8,915 FULL104 count blocks are counted, never hashed. A manifest path that no
longer exists is resolved by content only through a declared rename, never by name.
"""
import hashlib
import io
import json
import os
import subprocess
import sys

import pandas as pd

ROOT, AUTH, GIT = sys.argv[1].rstrip("/") + "/", sys.argv[2].rstrip("/") + "/", sys.argv[3]
REHASH_LIMIT = 256 * 1024 * 1024
RENAMES = {"_staging_expression_level4": "expression_level4"}  # declared directory rename after materialization
rehashed_bytes = 0


def sha256(path):
    global rehashed_bytes
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    rehashed_bytes += os.path.getsize(path)
    return h.hexdigest()


def git_show(ref_path):
    return subprocess.run(["git", "--git-dir", GIT, "show", ref_path], capture_output=True, check=True).stdout


def locate(path, base):
    path = path.replace("\\", "/")
    candidates = [base + path, ROOT + path]
    for old, new in RENAMES.items():
        candidates += [c.replace(old, new) for c in candidates]
    return next((c for c in candidates if os.path.isfile(c)), None)


def check(group, authority, coverage, path, recorded_sha, recorded_bytes=None, base=None, verification="EXACT"):
    found = locate(path, base or ROOT)
    row = {"group": group, "path": path, "recorded_sha256": recorded_sha, "authority": authority,
           "coverage": coverage, "located_at": None if found is None else os.path.relpath(found, ROOT).replace("\\", "/")}
    if verification == "PATTERN":
        row["classification"] = "VERIFIED_AT_LIMITED_SCOPE"
    elif recorded_sha is None:
        row["classification"] = "NOT_PREVIOUSLY_VERIFIED"
    else:
        row["classification"] = "EXACT_SHA_ALREADY_VERIFIED"
    if found is None:
        row["current_bytes"] = "NOT_LOCATED_LOCALLY"
        return row
    size = os.path.getsize(found)
    row["current_size"] = size
    if size <= REHASH_LIMIT:
        current = sha256(found)
        row["current_sha256"] = current
        if recorded_sha is None:
            row["current_bytes"] = "HASHED_NOW_NO_PRIOR_PIN"
        elif current == recorded_sha:
            row["current_bytes"] = "IDENTICAL_REHASHED"
        else:
            row["current_bytes"] = "DIFFERS"
            row["classification"] = "DRIFTED"
    elif recorded_bytes is not None:
        row["current_bytes"] = "SIZE_MATCH_NOT_REHASHED" if int(recorded_bytes) == size else "SIZE_DIFFERS"
        if int(recorded_bytes) != size:
            row["classification"] = "DRIFTED"
    else:
        row["current_bytes"] = "PRESENT_NOT_REHASHED"
    return row


rows = []
F104 = "outputs/full104_v014_20260826/"

# 1. 2026-09-02 FULL104 reuse manifest.
reuse = pd.read_csv(ROOT + "outputs/full104_parallel_reuse_delta_20260902/FULL104_REUSED_ARTIFACT_MANIFEST.csv", dtype=str)
for r in reuse.itertuples(index=False):
    rows.append(check("full104_reuse_manifest_20260902", "FULL104_REUSE_AUTHORITY.json; independent validation",
                      f"{r.action}: {r.semantic_scope}", r.path, r.sha256,
                      verification="PATTERN" if "PATTERN" in r.action else "EXACT"))

# 2. FULL104 metadata adapter manifest.
adapter_dir = ROOT + F104 + "01_full104_metadata_adapter/"
adapter = pd.read_csv(adapter_dir + "FULL104_ADAPTER_SHA256_MANIFEST.csv", dtype=str)
for r in adapter.itertuples(index=False):
    rows.append(check("full104_metadata_adapter", "FULL104_ADAPTER_SHA256_MANIFEST.csv; fidelity + red-team review",
                      "reader_fit metadata lineage", r.path, r.sha256, r.bytes, base=adapter_dir))

# 3. FULL104 expression interface v8 package.
v8_dir = ROOT + F104 + "full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8/"
v8 = pd.read_csv(v8_dir + "FULL104_EXPRESSION_INTERFACE_V8_SHA256_MANIFEST.csv", dtype=str)
for r in v8.itertuples(index=False):
    rows.append(check("full104_expression_interface_v8", "V8 package manifest; 84-cell 42-operator replay",
                      "expression interface package", r.path, r.sha256, r.bytes, base=v8_dir))
package_root = open(ROOT + F104 + "full104_expression_interface_v8_verified/"
                    "FULL104_EXPRESSION_INTERFACE_V8.PACKAGE_ROOT_SHA256.txt").read().split()[0]
package_root_check = {"recorded": package_root,
                      "manifest_sha256_now": sha256(v8_dir + "FULL104_EXPRESSION_INTERFACE_V8_SHA256_MANIFEST.csv")}

# 4. FULL104 Level-4 materialization (blocks counted, never hashed).
l4 = ROOT + F104 + "03_phase2_state_derivation_v1/expression_level4/"
audit = json.load(open(l4 + "PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json"))
rows.append(check("full104_level4_materialization", "PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json",
                  "8,915-block manifest", F104 + "03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv",
                  audit["block_manifest_sha256"]))
rows.append(check("full104_level4_materialization", "PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json",
                  "asset authentication journal", F104 + "03_phase2_state_derivation_v1/expression_level4/ASSET_AUTHENTICATION.csv",
                  audit["asset_authentication_sha256"]))
for r in pd.read_csv(l4 + "PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv", dtype=str).itertuples(index=False):
    rows.append(check("full104_level4_materialization", "PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv",
                      "materialization package", r.path, r.sha256, r.bytes))
blocks = pd.read_csv(l4 + "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv", dtype=str)
present = sum(os.path.isfile(l4 + p) and os.path.isfile(l4 + m) for p, m in zip(blocks.counts_path, blocks.meta_path))
block_census = {"manifest_blocks": int(len(blocks)), "blocks_with_both_files_present": int(present),
                "audit_blocks": audit["blocks"], "audit_cells": audit["cells"], "hashed": False}

# 5. Calibration bundle (97/97 verified by #471 / #492): bundle members.
bundle_dir = ROOT + "exports/foundation_calibration_bundle_20260824/"
bundle = pd.read_csv(bundle_dir + "BUNDLE_SHA256_MANIFEST.csv", dtype=str)
path_col = next(c for c in bundle.columns if "path" in c.lower())
sha_col = next(c for c in bundle.columns if "sha" in c.lower())
byte_col = next((c for c in bundle.columns if "byte" in c.lower() or "size" in c.lower()), None)
for r in bundle.to_dict("records"):
    rows.append(check("calibration_bundle_20260824", "#471 97/97 member verification; #492 reacquired custody",
                      "calibration bundle member", r[path_col], r[sha_col], r[byte_col] if byte_col else None, base=bundle_dir))
bundle_manifest_sha = sha256(bundle_dir + "BUNDLE_SHA256_MANIFEST.csv")

# 6. #492 pinned inputs, and 7. the inputs Macha #509 used, looked up against every authority above.
r492 = json.loads(git_show("79d2f936:results/target_discovery/unified_qualification_v1/"
                           "JEPA_REACQUIRED_FOUNDATION_SOURCE_AUDIT_20261028.json"))
pins_492 = {k: v for k, v in r492["inputs"].items() if isinstance(v, str) and len(v) == 64}
known = {}
for r in rows:
    if r["recorded_sha256"]:
        known.setdefault(r["recorded_sha256"], []).append(r["group"])
for name, value in pins_492.items():
    known.setdefault(value, []).append(f"pr492:{name}")
for item in r492["mechanical_query_observability"]["artifacts"].values():
    known.setdefault(item["sha256"], []).append("pr492:mechanical_query_observability")
def walk_pins(value, label):
    if isinstance(value, dict):
        for item in value.values():
            walk_pins(item, label)
    elif isinstance(value, list):
        for item in value:
            walk_pins(item, label)
    elif isinstance(value, str) and HEX64.fullmatch(value):
        known.setdefault(value, []).append(label)


import re  # noqa: E402 - kept beside its only use
HEX64 = re.compile(r"[0-9a-f]{64}")
walk_pins(r492.get("minimal_alias_reacquisition", {}), "pr492:minimal_alias_reacquisition")
preservation = pd.read_csv(io.BytesIO(git_show("2c000ecc:docs/history/JEPA_COMPLETE_PRESERVATION_MANIFEST_20260902.csv")),
                           dtype=str, usecols=["source_local_path", "filesystem_sha256"])
for p, s in zip(preservation.source_local_path, preservation.filesystem_sha256):
    known.setdefault(s, []).append("preservation_manifest_20260902")
# Pins quoted inside the located authority receipts themselves (JSON/CSV/MD/TXT up to 16 MB).
for r in rows:
    loc = r["located_at"]
    if loc and loc.rsplit(".", 1)[-1] in ("json", "csv", "md", "txt") and os.path.getsize(ROOT + loc) <= 16 << 20:
        text = open(ROOT + loc, encoding="utf-8", errors="replace").read()
        for token in set(HEX64.findall(text)):
            known.setdefault(token, []).append(f"quoted_in:{r['group']}")

used_by_509 = {
    "results/v4/stage81a2r_authoritative_source_mapping_decisions_candidate.csv.gz": ROOT,
    "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz": ROOT,
    "results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv": ROOT,
    "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz": ROOT,
    "results/v4/stage81a2_canonical_asset_registry.csv": ROOT,
    "results/v4/stage81a2_matrix_semantics_contract.csv": ROOT,
    "results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz": AUTH,
    "results/v4/stage81a3r_scalar_mapping_unregistered_collisions.csv": AUTH,
}
inputs_509 = []
for path, base in used_by_509.items():
    current = sha256(base + path)
    inputs_509.append({"path": path, "root": "stage81a3r" if base == AUTH else "repo", "current_sha256": current,
                       "prior_authorities": sorted(set(known.get(current, []))),
                       "classification": "EXACT_SHA_ALREADY_VERIFIED" if current in known else "NOT_PREVIOUSLY_VERIFIED"})

summary = {}
for r in rows:
    key = (r["group"], r["classification"], r["current_bytes"])
    summary[" | ".join(key)] = summary.get(" | ".join(key), 0) + 1
print(json.dumps({
    "schema": "JEPA_MACHA_ETL_REUSE_LEDGER_V1",
    "rehash_limit_bytes": REHASH_LIMIT, "rehashed_bytes": rehashed_bytes,
    "summary": dict(sorted(summary.items())),
    "v8_package_root": package_root_check,
    "level4_block_census": block_census,
    "bundle_manifest_sha256_now": bundle_manifest_sha,
    "pr492_input_pins": pins_492,
    "inputs_used_by_pr509": inputs_509,
    "rows": rows,
}, indent=1, sort_keys=True))
