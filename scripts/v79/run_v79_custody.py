#!/usr/bin/env python3
"""V79 corrected-TRAIN custody receipt. Authenticates the substrate before any Bayesian fitting.

Fails closed (terminal STOP_...) unless: the local corrected cache is exactly the 84 files the S174 lane
recorded (35 rebuilt shard pairs from the build receipt, 7 NPH pairs from the freeze) and its 42 meta
files equal V78's frozen meta digest; the frozen registry has 41,238 address rows; every bridge stem
recomputes from its matrix id; every donor is foundation TRAIN for its own study; and the recomputed
gene universe equals the frozen corrected evaluation universe. The historical production-loader
manifest is recorded with V78's ruling that it identifies the pre-repair Stage81A3R cache, not this one.

Reads only allowlisted fields (v79_firewall). Writes no gene identity.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402

ROOT = HERE.parents[1]
PASS = "PASS_V79_CORRECTED_TRAIN_CUSTODY_AUTHENTICATED"
STOP = "STOP_V79_CUSTODY_MISMATCH__RECONCILE_BEFORE_ANALYSIS"
DEFAULTS = dict(
    cache="D:/Jepa project/data/cache/s174_rebuilt_real_train_v1",
    registry="D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_registry_candidate.csv",
    split="D:/Jepa project/results/v4/stage81a2_split_registry.csv",
    calibration_bundle="D:/Jepa project/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip",
    frozen_universe="D:/jepa_v77_synthetic_custody_20261005/s174_replay/frozen_evaluation_universe.npz",
)
BRIDGE = ROOT / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
META_DIGEST = ROOT / "results/v78/V78_S174_SHARD_META_DIGEST_V1.json"
RECOVERY = ROOT / "results/v78/V78_S174_CACHE_RECOVERY_CUSTODY_V1.json"
S174_BUILD = ROOT / "results/v77/S174_REBUILD_BUILD_RECEIPT_V1.json"
S174_FREEZE = ROOT / "results/v77/S174_REBUILD_FREEZE_V1.json"
CALIBRATION_BUNDLE_SHA = "07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444"
LOADER_MANIFEST_MEMBER = "contracts/production_loader_manifest.json"
TRANSFER_VERIFICATION = dict(branch="custody/s174-cache-transfer-verification-20261009",
                             commit="eb3f92045e95ee4e5a85a864d1ec5922fe8f3d16", pr=244,
                             terminal="PASS_S174_RAR_EXACTLY_MATCHES_G1B_AUTHORIZED_CORRECTED_CACHE")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()


def expected_cache() -> dict:
    build, freeze = json.loads(S174_BUILD.read_text()), json.loads(S174_FREEZE.read_text())
    exp = {}
    for s in build["h5_shards"]:
        exp[f"{s['stem']}.counts.npz"], exp[f"{s['stem']}.meta.npz"] = s["counts_sha256"], s["meta_sha256"]
    for s in freeze["nph_shards"]:
        exp[f"{s['stem']}.counts.npz"], exp[f"{s['stem']}.meta.npz"] = s["counts_sha256"], s["meta_sha256"]
    return exp


def build(a) -> dict:
    fails = []
    cache = FW.check_path(a.cache)
    exp = expected_cache()
    files = {p.name: p for p in cache.iterdir() if p.is_file()}
    rows = []
    for name in sorted(set(exp) | set(files)):
        s = sha_file(files[name]) if name in files else None
        rows.append(dict(file=name, bytes=files[name].stat().st_size if name in files else None, sha256=s,
                         s174_authority_sha256=exp.get(name), match=(s == exp.get(name) and s is not None)))
    if len(files) != 84 or not all(r["match"] for r in rows):
        fails.append("cache files are not exactly the 84 S174-authorized files")
    v78_meta = {r["file"]: r["sha256"] for r in json.loads(META_DIGEST.read_text())["rows"]}
    meta_ok = len(v78_meta) == 42 and all(files.get(f) is not None and sha_file(files[f]) == h for f, h in v78_meta.items())
    if not meta_ok:
        fails.append("meta files differ from V78's frozen meta digest")

    reg = Path(a.registry).read_bytes()
    reg_rows = reg.count(b"\n") - 1 + (0 if reg.endswith(b"\n") else 1)
    if reg_rows != DA.N_ADDRESSES:
        fails.append(f"registry has {reg_rows} rows, not {DA.N_ADDRESSES}")

    bundle_sha = sha_file(a.calibration_bundle)
    with zipfile.ZipFile(a.calibration_bundle) as z:
        name = next(n for n in z.namelist() if n.endswith(LOADER_MANIFEST_MEMBER))
        loader_sha = sha_bytes(z.read(name))
    recovery = json.loads(RECOVERY.read_text())
    if bundle_sha != CALIBRATION_BUNDLE_SHA or loader_sha != recovery["historical_loader_manifest"]["sha256"]:
        fails.append("calibration bundle or historical loader manifest identity differs")

    bridge = FW.load_bridge(BRIDGE)
    stems_ok = all(r["stem"] == sha_bytes(f"corrected|{r['matrix_id']}".encode())[:16] for r in bridge)
    ops_ok = sorted(r["operator_index"] for r in bridge) == list(range(42))
    if not (stems_ok and ops_ok and len(bridge) == 42):
        fails.append("bridge stems or operator indices do not recompute")

    d = FW.load_cell_design(cache, BRIDGE)
    sp = pd.read_csv(FW.check_path(a.split), usecols=list(FW.ALLOWED_SPLIT_COLUMNS), dtype=str)
    tr = sp[(sp.split_domain == "foundation") & (sp.split == "train")]
    train = {st: {v.split("::", 1)[-1] for v in g.canonical_person_id} for st, g in tr.groupby("study_id")}
    pairs = sorted(set(zip(d["source"].tolist(), d["donor_id"].tolist())))
    n_train = sum(don in train.get(src, set()) for src, don in pairs)
    if n_train != len(pairs):
        fails.append(f"only {n_train} of {len(pairs)} donors are foundation TRAIN")

    X = DA.load_counts(cache, BRIDGE)
    if X.shape != (len(d["donor_id"]), DA.N_ADDRESSES):
        fails.append(f"count matrix shape {X.shape} does not match the design")
    u = DA.universe(X)
    fu = np.load(FW.check_path(a.frozen_universe), allow_pickle=False)["evaluation_universe"]
    universe_equal = np.array_equal(np.sort(u), np.sort(fu))
    if not universe_equal:
        fails.append("recomputed universe differs from the frozen corrected evaluation universe")

    di = DA.design_indices(d)
    d2op = {}
    for don, op in zip(d["donor_id"].tolist(), d["operator"].tolist()):
        d2op.setdefault(don, set()).add(op)
    import torch  # noqa: E402  (environment record only)
    return dict(
        schema="V79_CORRECTED_TRAIN_CUSTODY_RECEIPT_V1",
        terminal=PASS if not fails else STOP, failures=fails, lane=FW.LANE_TERMINAL,
        cache=dict(root=str(cache), n_files=len(files), n_shards=len(bridge), files=rows,
                   all_match_s174_authority=all(r["match"] for r in rows), meta_match_v78_digest=meta_ok,
                   s174_authorities={p.name: sha_file(p) for p in (S174_BUILD, S174_FREEZE)},
                   transfer_archive_verification=TRANSFER_VERIFICATION),
        registry=dict(path=a.registry, sha256=sha_bytes(reg), address_rows=reg_rows,
                      read="row count only; no column is parsed"),
        loader_manifest=dict(bundle=a.calibration_bundle, bundle_sha256=bundle_sha, member=name,
                             sha256=loader_sha, v78_ruling=recovery["supersession"]["ruling"],
                             role="historical Stage81A3R loader identity; recorded, not used as the identity root"),
        bridge=dict(path=BRIDGE.relative_to(ROOT).as_posix(), sha256=sha_file(BRIDGE), rows=len(bridge),
                    stems_recompute=stems_ok, operator_indices_0_41=ops_ok),
        v78_records={p.relative_to(ROOT).as_posix(): sha_file(p) for p in (META_DIGEST, RECOVERY)},
        split=dict(path=a.split, sha256=sha_file(a.split), columns_read=list(FW.ALLOWED_SPLIT_COLUMNS),
                   rule="split_domain == foundation and split == train, per study_id (the S174 G5 join)",
                   donors=len(pairs), donors_foundation_train=n_train),
        cells=dict(n=int(len(d["donor_id"])), donors=di["n_donor"], operators=di["n_op"], sources=di["source_levels"],
                   cells_by_source=dict(Counter(d["source"].tolist())),
                   raw_class_counts=dict(Counter(d["raw_class"].tolist())),
                   broad_class_counts=dict(Counter(d["broad_class"].tolist())),
                   canonical_label_cells=int(d["canonical_label"].sum()), donor_class_cells=di["n_dk"],
                   donors_in_two_or_more_operators=sum(len(v) > 1 for v in d2op.values())),
        universe=dict(prevalence_floor=DA.PREVALENCE_FLOOR, size=int(len(u)), frozen_path=a.frozen_universe,
                      frozen_sha256=sha_file(a.frozen_universe), equal_to_frozen=universe_equal,
                      label_note=("the frozen file's builder labels it TRAIN_PREVALENCE05_19569; it holds the "
                                  "corrected 14,417-address universe (known nomenclature defect)")),
        fields_read=dict(meta=list(FW.ALLOWED_META_FIELDS), bridge=list(FW.ALLOWED_BRIDGE_FIELDS),
                         split=list(FW.ALLOWED_SPLIT_COLUMNS), counts="indices, indptr, data, shape"),
        class_map=FW.CLASS_MAP,
        code=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"),
                  files={p.name: sha_file(p) for p in sorted(HERE.glob("*.py"))}),
        environment=dict(python=sys.version.split()[0], platform=platform.platform(), numpy=np.__version__,
                         pandas=pd.__version__, torch=torch.__version__))


def main() -> None:
    ap = argparse.ArgumentParser()
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), default=v)
    ap.add_argument("--out", default=str(ROOT / "results/v79/V79_CORRECTED_TRAIN_CUSTODY_RECEIPT_V1.json"))
    a = ap.parse_args()
    rec = build(a)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=1) + "\n")
    print(rec["terminal"], rec["failures"])
    print({k: rec["cells"][k] for k in ("n", "donors", "operators", "broad_class_counts", "donor_class_cells")},
          "universe", rec["universe"]["size"], rec["universe"]["equal_to_frozen"])


if __name__ == "__main__":
    main()
