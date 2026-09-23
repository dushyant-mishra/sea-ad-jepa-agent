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
import os
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
# Frozen, independently published physical references for THIS derivative version.
DERIVATIVE_SHA256 = "4b15ee5238c6e48d931329d222a9488a7b4f122c58767b6615a0b480afc4800b"
ARRAY_MANIFEST_CANONICAL_SHA256 = "4f55158c59d2ee6cdb3ad9276e887126ae78b5b9305021c8c607b524c61293a5"
ARRAY_MANIFEST_FILE_SHA256 = "9517b95446013c7f803df0b63b662d24f2e1df81f0b4917a2af41dae1df2b1ee"
SPLIT_FILE_SHA256 = "56f045d7dc80fde7e30c97632c1d109286e4b8f9f033b77476521c2822980585"
ORIGINAL_SIX_FILE_SHA256 = "bbd2b95b882f52c313a3623bab55e5d7ff6562cdba27e48f9c84009075cf713d"
# The PR #67 diagnostic rebuilt this vector from all 8,915 authenticated metadata files.
AUTHENTICATED_METADATA_CELL_DONOR_SHA256 = "3d56cda1d1d4ec228351b1f29197c9bce00ac8d7f12687430490fe7c6192a607"
EXPECTED_CHANGED = {"source_names", "src_of_cell"}
EXPECTED_MEMBERS = 35
EXPECTED_FOLD_DONORS = (28, 26, 25, 25)


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


def int64_digest(value: np.ndarray) -> str:
    arr = np.asarray(value)
    if arr.dtype != np.int64:
        raise SystemExit("authenticated donor vector requires exact int64")
    return hashlib.sha256(np.ascontiguousarray(arr, dtype="<i8").tobytes()).hexdigest()


def verify_all_members(parent, derivative, array_manifest) -> None:
    """Independent read-back: do not trust the candidate manifest's own claims."""
    old_names, new_names = set(parent.files), set(derivative.files)
    rows = array_manifest.get("per_array")
    if (not isinstance(rows, list) or len(rows) != EXPECTED_MEMBERS
            or old_names != new_names or len(old_names) != EXPECTED_MEMBERS):
        raise SystemExit("physical NPZ member census mismatch")
    by_name = {row["name"]: row for row in rows}
    if len(by_name) != EXPECTED_MEMBERS or set(by_name) != old_names:
        raise SystemExit("manifest member set missing/duplicate/extra")
    changes = set()
    for name in sorted(old_names):
        a, b, rec = parent[name], derivative[name], by_name[name]
        if str(a.dtype) != rec["dtype"] or list(a.shape) != rec["shape"]:
            raise SystemExit(f"manifest dtype/shape mismatch: {name}")
        if b.dtype != a.dtype or b.shape != a.shape:
            raise SystemExit(f"derivative dtype/shape mismatch: {name}")
        old_hash, new_hash = value_sha256(a), value_sha256(b)
        if (rec["old_value_sha256"] != old_hash
                or rec["new_value_sha256"] != new_hash):
            raise SystemExit(f"independent per-member value digest mismatch: {name}")
        changed = old_hash != new_hash
        if rec["changed"] is not changed:
            raise SystemExit(f"manifest change flag mismatch: {name}")
        if changed:
            changes.add(name)
        if not rec.get("scientific_role") or rec.get("source_dependent") in (None, "unknown"):
            raise SystemExit(f"unclassified member: {name}")
        if rec.get("disposition") != (
                "INTENDED_CHANGE__REBUILT_FROM_LEVEL4" if name in EXPECTED_CHANGED
                else "UNAFFECTED_BY_BUG__PROVED"):
            raise SystemExit(f"member disposition mismatch: {name}")
    if changes != EXPECTED_CHANGED:
        raise SystemExit(f"independently observed changed members differ: {sorted(changes)}")
    if (array_manifest.get("members_total") != EXPECTED_MEMBERS
            or array_manifest.get("members_changed") != len(EXPECTED_CHANGED)
            or array_manifest.get("members_unchanged") != EXPECTED_MEMBERS - len(EXPECTED_CHANGED)):
        raise SystemExit("manifest member counts disagree with independently loaded arrays")


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
    if derivative_sha != DERIVATIVE_SHA256:
        raise SystemExit("derivative physical SHA differs from independently reviewed artifact")

    if sha256_file(args.array_manifest) != ARRAY_MANIFEST_FILE_SHA256:
        raise SystemExit("per-array manifest file SHA differs from reviewed bytes")
    array_manifest = json.loads(args.array_manifest.read_text(encoding="utf-8"))
    recomputed = canonical_digest({k: v for k, v in array_manifest.items()
                                   if k != "manifest_sha256"})
    if (recomputed != array_manifest.get("manifest_sha256")
            or recomputed != ARRAY_MANIFEST_CANONICAL_SHA256):
        raise SystemExit("per-array manifest self-digest mismatch")
    if array_manifest.get("derivative_sha256") != derivative_sha:
        raise SystemExit("per-array manifest binds a different derivative")
    if array_manifest.get("parent_original_sha256") != parent_sha:
        raise SystemExit("per-array manifest binds a different parent")
    changed = sorted(r["name"] for r in array_manifest["per_array"] if r["changed"])
    if changed != ["source_names", "src_of_cell"]:
        raise SystemExit(f"unexpected changed member set: {changed}")

    if sha256_file(args.split_receipt) != SPLIT_FILE_SHA256:
        raise SystemExit("frozen split physical file SHA mismatch")
    if sha256_file(args.original_six_donor_receipt) != ORIGINAL_SIX_FILE_SHA256:
        raise SystemExit("original six-donor physical file SHA mismatch")
    split = json.loads(args.split_receipt.read_text(encoding="utf-8"))
    if split.get("receipt_sha256") != SPLIT_CANONICAL_SHA256:
        raise SystemExit("split receipt has the wrong frozen canonical digest")

    d = np.load(args.derivative, allow_pickle=True)
    p = np.load(args.parent, allow_pickle=True)
    verify_all_members(p, d, array_manifest)
    core = np.asarray(d["core"], dtype=np.int64)
    duniq = [str(x) for x in d["duniq"]]
    donor_src = np.asarray(d["donor_src"], dtype=np.int64)
    src_of_cell = np.asarray(d["src_of_cell"], dtype=np.int64)
    names = [str(x) for x in d["source_names"]]
    nnz = np.asarray(d["donor_nnz"], dtype=np.int64)
    umi = np.asarray(d["donor_umi"], dtype=np.int64)

    p1 = np.load(args.pass1, allow_pickle=True)
    cell_donor = np.asarray(p1["cell_donor"])
    if cell_donor.dtype != np.int64 or cell_donor.shape != (EXPECTED_CELLS,):
        raise SystemExit("pass1 cell_donor must be exact FULL104 int64")
    if int64_digest(cell_donor) != AUTHENTICATED_METADATA_CELL_DONOR_SHA256:
        raise SystemExit("pass1 donor vector differs from PR67 full-metadata physical audit")
    if not np.array_equal(p1["core"], d["core"]) or not np.array_equal(p1["duniq"], d["duniq"]):
        raise SystemExit("pass1 address or donor registry differs from derivative")
    if np.any(cell_donor < 0) or np.any(cell_donor >= EXPECTED_DONORS):
        raise SystemExit("pass1 cell_donor outside frozen donor registry")

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
    per_donor = list(original["per_donor"])
    if (len(donors) != 6 or len(set(donors)) != 6 or len(per_donor) != 6
            or set(donors) != {rec["donor"] for rec in per_donor}
            or len({rec["donor"] for rec in per_donor}) != 6):
        raise SystemExit("original six-donor identities missing, duplicated or inconsistent")

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
    if not numbers_unchanged:
        raise SystemExit("numeric donor row/total changed: raw reaggregation required")
    per_source = {}
    for r in rows:
        per_source.setdefault(r["corrected_canonical_label"], []).append(r["donor"])

    if sorted(len([r for r in rows if r["corrected_canonical_label"] == s])
              for s in CANONICAL_SOURCE_NAMES) != [2, 2, 2]:
        raise SystemExit("corrected six-donor source census is not two per source")
    if "fold_by_donor" not in split:
        raise SystemExit("frozen split missing required fold_by_donor vector")
    fold = np.asarray(split["fold_by_donor"])
    if (fold.dtype.kind not in "iu" or fold.shape != (EXPECTED_DONORS,)
            or np.any(fold < 0) or np.any(fold >= 4)
            or sorted(np.bincount(fold.astype(np.int64), minlength=4).tolist()) != sorted(EXPECTED_FOLD_DONORS)):
        raise SystemExit("frozen four-fold donor assignment invalid")

    six = {
        "schema": "V5_FULL104_SIX_DONOR_SUCCESSOR_QUALIFICATION_V2",
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
        "schema": "V5_FULL104_N1_PHYSICAL_PREFLIGHT_SUCCESSOR_V2",
        "state": "NEW_PHYSICAL_N1_INPUTS_QUALIFIED_FOR_INDEPENDENT_REVIEW",
        "not_execution_authority": (
            "this terminal authorises independent review only. It does not permit "
            "selecting N1 targets, generating masks, computing burden or precision, "
            "or inspecting any N1 outcome."
        ),
        "pr62_binder_left_intact": True,
        "pr62_parent_rejection": "EXTERNAL_REGRESSION__NOT_REEXECUTED_BY_THIS_CLI",
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
        "fold_by_donor_sha256": value_sha256(fold),
        "donor_nnz_value_sha256": value_sha256(nnz),
        "donor_umi_value_sha256": value_sha256(umi),
        "source_invariant_violations": mismatch,
        "all_35_members_independently_reloaded_and_hashed_here": True,
        "pass1_donor_vector_bound_to_authenticated_PR67_metadata": True,
        "input_file_hashes_verified": {
            "parent": parent_sha, "derivative": derivative_sha,
            "array_manifest": ARRAY_MANIFEST_FILE_SHA256,
            "original_six_donor": ORIGINAL_SIX_FILE_SHA256,
            "split_receipt": SPLIT_FILE_SHA256,
        },
        "caller_supplied_sha_strings_trusted": False,
        "n1_targets_selected": False,
        "masks_generated": False,
        "burden_calculated": False,
        "precision_calculated": False,
        "expression_opened": False,
        "count_matrices_opened": False,
        "training_authorized": False,
    }
    pre["receipt_sha256"] = canonical_digest({k: v for k, v in pre.items()
                                              if k != "receipt_sha256"})

    # Publish the independent-qualification pair with durable exclusive stages.
    # The final N1 preflight is always committed last: a crash cannot produce a
    # qualified-looking preflight without the corresponding six-donor receipt.
    stages = []
    for out, payload in ((args.out_six_donor, six), (args.out_preflight, pre)):
        out.parent.mkdir(parents=True, exist_ok=True)
        stage = out.with_name("." + out.name + ".staged")
        if stage.exists() or out.exists():
            raise SystemExit("refusing to reuse existing receipt or stage: " + str(out))
        with stage.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        stages.append((stage, out))
    for stage, out in stages:
        if out.exists():
            raise SystemExit("receipt appeared during staged commit: " + str(out))
        os.replace(stage, out)
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
