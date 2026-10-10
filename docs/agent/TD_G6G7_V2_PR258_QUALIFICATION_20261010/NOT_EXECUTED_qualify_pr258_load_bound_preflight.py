#!/usr/bin/env python3
"""PR #258 qualification: run the exact PR #259 receipts through load_bound_preflight() and nothing else.

Usage: python qualify_pr258_load_bound_preflight.py <repo_root> <out_dir_outside_repo>

1. Extracts the two receipt blobs from PR #259 head 80e6b445 with `git cat-file blob` (raw bytes; no CRLF/LF
   normalization) and checks their SHA-256 against the owner-supplied values.
2. Imports scripts/v5/td_relational_value_read_v2_common.py from the repo root and calls only
   load_bound_preflight(...) on those bytes with those SHA values; records what it returns.
3. Supplementary negative control (labelled): an LF-normalized copy of the driver receipt must be refused with
   the SHA-binding error, showing the gate binds the physical bytes. The real files are never modified.
No runtime value-read authorization object is created or read; no H5AD file, expression array or count array
is opened; G6/G7 are not imported or run.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PR259_HEAD = "80e6b4454dd2bc7b8dfcfb060a6e27d3c559f947"
NS = "results/target_discovery/td_relational_corrected_replay_20261010/preflight_v4_sampleA_custody_split/"
FILES = {
    "driver": (NS + "PREFLIGHT_RESULT.json", "62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae"),
    "mapping": (NS + "TD_RELATIONAL_MAPPING_PREFLIGHT.json",
                "6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0"),
}


def git(repo: Path, *args, binary=False):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode().strip()


def main() -> int:
    repo, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if out == repo or repo in out.parents:
        raise SystemExit("output directory must be outside the repository")
    out.mkdir(parents=True, exist_ok=True)
    rec = dict(schema="TD_G6G7_V2_PR258_LOAD_BOUND_PREFLIGHT_QUALIFICATION_V1",
               repo_head=git(repo, "rev-parse", "HEAD"), repo_status_short=git(repo, "status", "--short"),
               pr259_head=PR259_HEAD, receipts={})
    paths = {}
    for key, (path, expected) in FILES.items():
        blob = git(repo, "rev-parse", f"{PR259_HEAD}:{path}")
        data = git(repo, "cat-file", "blob", blob, binary=True)
        dest = out / Path(path).name
        dest.write_bytes(data)
        on_disk = hashlib.sha256(dest.read_bytes()).hexdigest()
        rec["receipts"][key] = dict(path=path, git_blob=blob, bytes=len(data), sha256=on_disk, expected_sha256=expected,
                                    sha256_matches=on_disk == expected, crlf_pairs=data.count(b"\r\n"))
        paths[key] = dest
    if not all(v["sha256_matches"] for v in rec["receipts"].values()):
        rec["result"] = "STOP_RECEIPT_SHA_MISMATCH"
        print(json.dumps(rec, indent=1))
        return 1

    sys.path.insert(0, str(repo / "scripts" / "v5"))
    import td_relational_value_read_v2_common as C
    rec["common_module"] = dict(path="scripts/v5/td_relational_value_read_v2_common.py",
                                git_blob_at_head=git(repo, "rev-parse", "HEAD:scripts/v5/td_relational_value_read_v2_common.py"),
                                sha256=hashlib.sha256((repo / "scripts/v5/td_relational_value_read_v2_common.py").read_bytes()).hexdigest())
    preflight, mapping = C.load_bound_preflight(
        paths["driver"], paths["mapping"],
        expected_preflight_sha=FILES["driver"][1], expected_mapping_sha=FILES["mapping"][1])
    rec["load_bound_preflight"] = dict(
        returned=True,
        driver_schema=preflight.get("schema"), driver_status=preflight.get("status"),
        mapping_schema=mapping.get("schema"), mapping_status=mapping.get("status"),
        expected=dict(driver_schema=C.PREFLIGHT_SCHEMA, driver_status=C.DRIVER_PASS,
                      mapping_schema=C.MAPPING_SCHEMA, mapping_status=C.MAPPING_PASS),
        required_checks_in_mapping={k: mapping["checks"].get(k) for k in C.REQUIRED_MAPPING_CHECKS},
        required_checks_embedded_in_driver={k: preflight["mapping_checks"].get(k) for k in C.REQUIRED_MAPPING_CHECKS},
        sample_A_contract=mapping.get("sample_A_contract"),
        substrate_custody_contract=mapping.get("substrate_custody_contract"),
        driver_inputs_equal_expected={k: preflight["inputs"].get(k) == v for k, v in C.EXPECTED_INPUT_HASHES.items()},
        driver_real_value_replay_authorized=preflight.get("real_value_replay_authorized"),
        driver_training_authorized=preflight.get("training_authorized"),
        mapping_real_value_replay_authorized_by_this_receipt=mapping.get("real_value_replay_authorized_by_this_receipt"),
        mapping_training_authorized=mapping.get("training_authorized"))
    lb = rec["load_bound_preflight"]
    lb["all_expected"] = (lb["driver_schema"] == C.PREFLIGHT_SCHEMA and lb["driver_status"] == C.DRIVER_PASS
                          and lb["mapping_schema"] == C.MAPPING_SCHEMA and lb["mapping_status"] == C.MAPPING_PASS
                          and all(v is True for v in lb["required_checks_in_mapping"].values())
                          and all(v is True for v in lb["required_checks_embedded_in_driver"].values())
                          and all(lb["driver_inputs_equal_expected"].values()))

    # supplementary negative control: an LF-normalized copy must fail the SHA binding (real files untouched)
    neg_dir = out / "negative_control_lf_normalized"
    neg_dir.mkdir(exist_ok=True)
    neg = neg_dir / "PREFLIGHT_RESULT.json"
    neg.write_bytes(paths["driver"].read_bytes().replace(b"\r\n", b"\n"))
    try:
        C.load_bound_preflight(neg, paths["mapping"], expected_preflight_sha=FILES["driver"][1],
                               expected_mapping_sha=FILES["mapping"][1])
        rec["negative_control"] = dict(refused=False)
    except RuntimeError as e:
        rec["negative_control"] = dict(refused=True, error=str(e),
                                       lf_copy_sha256=hashlib.sha256(neg.read_bytes()).hexdigest())
    rec["real_receipts_unchanged_after_test"] = {
        k: hashlib.sha256(p.read_bytes()).hexdigest() == FILES[k][1] for k, p in paths.items()}
    rec["value_authorization_object_created"] = False
    rec["authorization_files_present_in_out_dir"] = sorted(
        p.name for p in out.rglob("*.json") if C.VALUE_AUTH_SCHEMA in p.read_text(encoding="utf-8", errors="ignore"))
    rec["h5ad_or_count_arrays_opened"] = False
    rec["g6_g7_run"] = False
    rec["result"] = ("PASS_PR258_BINDS_EXACT_PR259_V3_EVIDENCE"
                     if lb["all_expected"] and rec["negative_control"]["refused"]
                     and all(rec["real_receipts_unchanged_after_test"].values()) else "FAIL")
    print(json.dumps(rec, indent=1))
    return 0 if rec["result"].startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
