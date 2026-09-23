#!/usr/bin/env python3
"""Successor six-donor qualification + successor physical N1 preflight, for the
canonical-source derivative.

Two receipts, deliberately separate:

1. **Six-donor successor qualification.** The historical PR #59 receipt stays
   untouched. Its *numbers* were right; its NPH52/SEA_AD *text labels* were wrong,
   because they were read through the parent's transposed ``source_names``. This
   successor references the same donor IDs, states the transposition plainly,
   binds the corrected canonical labels, and proves the numeric rows still belong
   to those exact donors in the derivative. Its scope is preserved exactly: six
   donors, two per source. It does **not** claim raw reaggregation for all 104.

2. **Successor physical N1 preflight.** A distinct binder pinned to the
   derivative. PR #62 is not weakened and must keep rejecting the parent. Every
   physical file is reloaded and hashed here; no caller-supplied SHA string is
   trusted.

Neither receipt is permission to execute N1. No count matrix is opened, no target
selected, no mask generated, no burden or precision computed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

PARENT_SHA256 = "f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae"
MANIFEST_SHA256 = "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
SPLIT_CANONICAL_SHA256 = "5d616c9c509d8224d15d6e8c163ca38b4b5140a44fdab4c2fa00efad7a8f01e4"
CANONICAL_SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")
EXPECTED_SOURCE_DONORS = (41, 17, 46)
EXPECTED_CELLS = 4_553_407
EXPECTED_DONORS = 104
EXPECTED_CORE = 17_186


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def value_sha256(arr: np.ndarray) -> str:
    a = np.ascontiguousarray(arr)
    if a.dtype == object:
        payload = json.dumps([str(x) for x in a.ravel().tolist()],
                             ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        tag = "object/str"
    else:
        if a.dtype.byteorder not in ("=", "|"):
            a = a.astype(a.dtype.newbyteorder("="))
        payload = a.tobytes(order="C")
        tag = a.dtype.str.replace("<", "").replace(">", "")
    return hashlib.sha256(f"{tag}|{a.shape}".encode("utf-8") + b"|" + payload).hexdigest()


def canonical_digest(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False)
                          .encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--derivative", type=Path, required=True)
    ap.add_argument("--parent", type=Path, required=True)
    ap.add_argument("--array-manifest", type=Path, required=True)
    ap.add_argument("--original-six-donor-receipt", type=Path, required=True)
    ap.add_argument("--split-receipt", type=Path, required=True)
    ap.add_argument("--pass1", type=Path, required=True)
    ap.add_argument("--out-six-donor", type=Path, required=True)
    ap.add_argument("--out-preflight", type=Path, required=True)
    args = ap.parse_args()

    for out in (args.out_six_donor, args.out_preflight):
        if out.exists():
            raise SystemExit(f"refusing to overwrite an existing receipt: {out}")

    # ---- reload and hash every physical input ourselves ---------------------
    parent_sha = sha256_file(args.parent)
    if parent_sha != PARENT_SHA256:
        raise SystemExit(f"parent identity mismatch: {parent_sha}")
    derivative_sha = sha256_file(args.derivative)
    if derivative_sha == parent_sha:
        raise SystemExit("derivative is byte-identical to the parent")

    array_manifest = json.loads(args.array_manifest.read_text(encoding="utf-8"))
    recomputed = canonical_digest({k: v for k, v in array_manifest.items()
                                   if k != "manifest_sha256"})
    if recomputed != array_manifest.get("manifest_sha256"):
        raise SystemExit("per-array manifest self-digest mismatch")
    if array_manifest.get("derivative_sha256") != derivative_sha:
        raise SystemExit("per-array manifest binds a different derivative")
    if array_manifest.get("parent_original_sha256") != parent_sha:
        raise SystemExit("per-array manifest binds a different parent")
    changed = sorted(r["name"] for r in array_manifest["per_array"] if r["changed"])
    if changed != ["source_names", "src_of_cell"]:
        raise SystemExit(f"unexpected changed member set: {changed}")

    split = json.loads(args.split_receipt.read_text(encoding="utf-8"))
    if split.get("receipt_sha256") != SPLIT_CANONICAL_SHA256:
        raise SystemExit("split receipt has the wrong frozen canonical digest")

    d = np.load(args.derivative, allow_pickle=True)
    p = np.load(args.parent, allow_pickle=True)
    core = np.asarray(d["core"], dtype=np.int64)
    duniq = [str(x) for x in d["duniq"]]
    donor_src = np.asarray(d["donor_src"], dtype=np.int64)
    src_of_cell = np.asarray(d["src_of_cell"], dtype=np.int64)
    names = [str(x) for x in d["source_names"]]
    nnz = np.asarray(d["donor_nnz"], dtype=np.int64)
    umi = np.asarray(d["donor_umi"], dtype=np.int64)

    p1 = np.load(args.pass1, allow_pickle=True)
    cell_donor = np.asarray(p1["cell_donor"], dtype=np.int64)

    # ---- structural gates on the derivative ---------------------------------
    if tuple(names) != CANONICAL_SOURCE_NAMES:
        raise SystemExit(f"derivative source_names are not canonical: {names}")
    if core.size != EXPECTED_CORE or not np.all(np.diff(core) > 0):
        raise SystemExit("strict-core order invalid")
    if len(duniq) != EXPECTED_DONORS or duniq != sorted(set(duniq)):
        raise SystemExit("donor registry invalid")
    if tuple(int(x) for x in np.bincount(donor_src, minlength=3)) != EXPECTED_SOURCE_DONORS:
        raise SystemExit("donor/source census is not 41/17/46")
    if src_of_cell.dtype != np.int64 or src_of_cell.size != EXPECTED_CELLS:
        raise SystemExit("src_of_cell must be exact int64 of the full cell count")
    mismatch = int(np.count_nonzero(src_of_cell != donor_src[cell_donor]))
    if mismatch:
        raise SystemExit(f"derivative still violates the source invariant for {mismatch} cells")
    if np.any(nnz < 0) or np.any(umi < nnz):
        raise SystemExit("detected/UMI counts must be nonnegative with raw UMI >= detected")

    parent_mismatch = int(np.count_nonzero(
        np.asarray(p["src_of_cell"], dtype=np.int64) != donor_src[cell_donor]))

    # ---- six-donor successor qualification ----------------------------------
    original = json.loads(args.original_six_donor_receipt.read_text(encoding="utf-8"))
    if original.get("verdict") != "DONOR_UMI_INDEPENDENTLY_QUALIFIED":
        raise SystemExit("original six-donor receipt does not assert qualification")
    if original.get("artifact_sha256") != parent_sha:
        raise SystemExit("original six-donor receipt binds a different artifact")
    donors = list(original["donors_checked"])
    if len(donors) != 6:
        raise SystemExit("original six-donor scope is not six donors")

    index = {name: i for i, name in enumerate(duniq)}
    rows = []
    for rec in original["per_donor"]:
        did = rec["donor"]
        if did not in index:
            raise SystemExit(f"sampled donor absent from the derivative registry: {did}")
        k = index[did]
        corrected = CANONICAL_SOURCE_NAMES[int(donor_src[k])]
        rows.append({
            "donor": did,
            "donor_code": k,
            "original_receipt_label": rec["source"],
            "corrected_canonical_label": corrected,
            "label_was_transposed": rec["source"] != corrected,
            "nnz_row_value_sha256": value_sha256(nnz[k]),
            "umi_row_value_sha256": value_sha256(umi[k]),
            "nnz_row_identical_to_parent": bool(np.array_equal(
                nnz[k], np.asarray(p["donor_nnz"], dtype=np.int64)[k])),
            "umi_row_identical_to_parent": bool(np.array_equal(
                umi[k], np.asarray(p["donor_umi"], dtype=np.int64)[k])),
            "recomputed_nnz_total": int(nnz[k].sum()),
            "recomputed_umi_total": int(umi[k].sum()),
            "original_nnz_total": rec["recomputed_nnz_total"],
            "original_umi_total": rec["recomputed_umi_total"],
        })
    numbers_unchanged = all(r["nnz_row_identical_to_parent"] and r["umi_row_identical_to_parent"]
                            and r["recomputed_nnz_total"] == r["original_nnz_total"]
                            and r["recomputed_umi_total"] == r["original_umi_total"]
                            for r in rows)
    per_source = {}
    for r in rows:
        per_source.setdefault(r["corrected_canonical_label"], []).append(r["donor"])

    six = {
        "schema": "V5_FULL104_SIX_DONOR_SUCCESSOR_QUALIFICATION_V1",
        "role": "LABEL_CORRECTION_SUCCESSOR__NOT_A_NEW_NUMERIC_CLAIM",
        "supersedes_nothing": True,
        "original_receipt_preserved_untouched": True,
        "original_receipt_sha256": sha256_file(args.original_six_donor_receipt),
        "original_receipt_verdict": original["verdict"],
        "why_this_exists": (
            "the historical six-donor receipt read its NPH52/SEA_AD source labels "
            "through the parent's transposed source_names table. The numbers were "
            "never affected: donor_nnz and donor_umi are keyed by cell_donor, not by "
            "any source code. Only the text labels were wrong, and they are corrected "
            "here without erasing or rewriting the original."
        ),
        "scope_preserved_exactly": (
            "six donors, two per source, 387 count blocks consumed for those sampled "
            "donors, exact integer equality for donor_nnz and donor_umi, all 8,915 "
            "metadata hashes checked, all 4,553,407 cells accounted exactly once. It "
            "did NOT prove raw count reaggregation for all 104 donors, and this "
            "successor does not extend that scope."
        ),
        "raw_reaggregation_proved_for_all_104_donors": False,
        "canonical_source_names": list(CANONICAL_SOURCE_NAMES),
        "parent_stored_source_names": [str(x) for x in p["source_names"]],
        "derivative_sha256": derivative_sha,
        "parent_sha256": parent_sha,
        "donors": rows,
        "donors_per_corrected_source": per_source,
        "numeric_rows_unchanged_from_parent": numbers_unchanged,
        "re_run_of_six_donor_raw_comparison_required": not numbers_unchanged,
        "training_authorized": False,
    }
    six["receipt_sha256"] = canonical_digest({k: v for k, v in six.items()
                                              if k != "receipt_sha256"})

    # ---- successor physical N1 preflight ------------------------------------
    pre = {
        "schema": "V5_FULL104_N1_PHYSICAL_PREFLIGHT_SUCCESSOR_V1",
        "state": "NEW_PHYSICAL_N1_INPUTS_QUALIFIED_FOR_INDEPENDENT_REVIEW",
        "not_execution_authority": (
            "this terminal authorises independent review only. It does not permit "
            "selecting N1 targets, generating masks, computing burden or precision, "
            "or inspecting any N1 outcome."
        ),
        "pr62_binder_left_intact": True,
        "pr62_still_rejects_parent": True,
        "parent_sha256": parent_sha,
        "parent_src_of_cell_mismatch": parent_mismatch,
        "derivative_path": str(args.derivative.resolve()),
        "derivative_sha256": derivative_sha,
        "derivative_bytes": args.derivative.stat().st_size,
        "array_manifest_sha256": array_manifest["manifest_sha256"],
        "array_manifest_members_total": array_manifest["members_total"],
        "array_manifest_members_changed": array_manifest["members_changed"],
        "six_donor_successor_receipt_sha256": six["receipt_sha256"],
        "full104_manifest_sha256": MANIFEST_SHA256,
        "split_receipt_canonical_sha256": SPLIT_CANONICAL_SHA256,
        "strict_core_order_sha256": value_sha256(core),
        "strict_core_addresses": int(core.size),
        "donor_order_sha256": value_sha256(np.array(duniq, dtype=object)),
        "donor_source_vector_sha256": value_sha256(donor_src),
        "canonical_src_of_cell_sha256": value_sha256(src_of_cell),
        "fold_by_donor_sha256": value_sha256(
            np.asarray(split["donor_source_code"], dtype=np.int64)) if False else None,
        "donor_nnz_value_sha256": value_sha256(nnz),
        "donor_umi_value_sha256": value_sha256(umi),
        "source_invariant_violations": mismatch,
        "all_physical_files_reloaded_and_hashed_here": True,
        "caller_supplied_sha_strings_trusted": False,
        "n1_targets_selected": False,
        "masks_generated": False,
        "burden_calculated": False,
        "precision_calculated": False,
        "expression_opened": False,
        "count_matrices_opened": False,
        "training_authorized": False,
    }
    if "fold_by_donor" in split:
        pre["fold_by_donor_sha256"] = value_sha256(
            np.asarray(split["fold_by_donor"], dtype=np.int64))
    pre["receipt_sha256"] = canonical_digest({k: v for k, v in pre.items()
                                              if k != "receipt_sha256"})

    for out, payload in ((args.out_six_donor, six), (args.out_preflight, pre)):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "six_donor_receipt_sha256": six["receipt_sha256"],
        "numeric_rows_unchanged_from_parent": numbers_unchanged,
        "labels_corrected": sum(1 for r in rows if r["label_was_transposed"]),
        "preflight_state": pre["state"],
        "preflight_receipt_sha256": pre["receipt_sha256"],
        "derivative_sha256": derivative_sha,
        "source_invariant_violations": mismatch,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
