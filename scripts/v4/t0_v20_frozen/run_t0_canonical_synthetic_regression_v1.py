from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from t0_primary_membership_v1 import load_membership
from t0_feature_authority_v1 import load_feature_authority
from t0_donor_role_authority_v2 import build_role_authority, load_role_authority
from t0_canonical_freeze_v1 import freeze_target_after_role, freeze_tail_after_discovery_authority
from t0_technical_registry_v2 import build_technical_registry, load_technical_registry
from t0_target_family_authority_v2 import build_primary_only_family, load_primary_only_family, ALLOWED_STATUS
from t0_discovery_authority_v1 import load_discovery_authority
from t0_target_serializer_v2 import load_target_v2
from t0_tail_authority_v1 import load_tail_authority
from t0_adjudicator_v1 import adjudicate_from_raw

MEMBERSHIP_SHA256 = "d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529"
FEATURE_SPLIT_SHA256 = "29116c16e9002329090a5054b6c4bdae1cbff28917cbee85f03b4633b0b29369"
RARE_AUDIT_PLACEHOLDER_SHA256 = "1" * 64




def _canonicalize(value):
    if isinstance(value, np.ndarray):
        a=np.asarray(value)
        if a.dtype.kind in 'f':
            b=np.asarray(a,dtype='<f8').tobytes(order='C')
        elif a.dtype.kind in 'iu':
            b=np.asarray(a,dtype='<i8').tobytes(order='C')
        elif a.dtype==np.bool_:
            b=np.asarray(a,dtype=np.uint8).tobytes(order='C')
        else:
            raise TypeError(f'unsupported ndarray dtype {a.dtype}')
        return {'array_shape':list(a.shape),'array_sha256':hashlib.sha256(b).hexdigest()}
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, dict):
        return {str(k):_canonicalize(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [_canonicalize(v) for v in value]
    if value is None or isinstance(value,(str,int,float,bool)):
        return value
    raise TypeError(f'unsupported canonical value {type(value).__name__}')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def u01(tag: str, value: str) -> float:
    b = hashlib.sha256(f"{tag}|{value}".encode()).digest()[:8]
    return int.from_bytes(b, "big") / 2**64


def build_fixture(root: Path, membership_csv: Path, feature_split_csv: Path) -> dict:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    if sha256(membership_csv) != MEMBERSHIP_SHA256:
        raise RuntimeError("membership authority hash mismatch")
    if sha256(feature_split_csv) != FEATURE_SPLIT_SHA256:
        raise RuntimeError("feature split authority hash mismatch")

    m = load_membership(membership_csv)
    f = load_feature_authority(feature_split_csv)
    ids = f.molecular_address_id.astype(str).tolist()
    g = len(ids)

    support = m.groupby("donor_id").size().rename("cells").reset_index()
    support.insert(0, "source", "SEA_AD")
    support.insert(2, "operator_index", 31)
    donors = sorted(support.donor_id.astype(str), key=lambda x: x.encode())

    z = {d: 2 * u01("Z", d) - 1 for d in donors}
    age = {d: 65 + 25 * u01("AGE", d) for d in donors}
    sex = {d: ("F" if u01("SEX", d) < 0.5 else "M") for d in donors}
    if len(set(sex.values())) != 2:
        raise AssertionError("synthetic sex fixture lost binary support")

    role_meta = pd.DataFrame(
        {
            "donor_id": donors,
            "AT8_available": True,
            "age": [age[d] for d in donors],
            "sex": [sex[d] for d in donors],
            "technical_complete": True,
        }
    )
    role = build_role_authority(
        root / "role",
        support,
        role_meta,
        {"membership": MEMBERSHIP_SHA256, "feature_split": FEATURE_SPLIT_SHA256},
    )
    rr = role["registry"]
    disc = sorted(rr.loc[rr.role.eq("DISCOVERY"), "donor_id"].astype(str), key=lambda x: x.encode())
    conf = sorted(rr.loc[rr.role.eq("CONFIRMATION"), "donor_id"].astype(str), key=lambda x: x.encode())

    score_pos = np.flatnonzero(f.feature_role.to_numpy() == "SCORING")
    hold_pos = np.flatnonzero(f.feature_role.to_numpy() == "COHERENCE_HOLDOUT")
    s0, s1, s2, s3 = map(int, score_pos[:4])
    h0, h1, h2, h3, h4 = map(int, hold_pos[:5])

    rows: list[int] = []
    cols: list[int] = []
    vals: list[int] = []
    lib = np.empty(len(m), dtype=np.float64)
    for i, r in enumerate(m.itertuples(index=False)):
        d = str(r.donor_id)
        key = int(r.stable_key)
        zz = z[d]
        eps = ((key >> 8) % 3) - 1
        c0 = max(1, int(round(9 + 4 * zz + eps)))
        c1 = max(1, int(round(9 - 3 * zz - eps)))
        high = u01("TAIL", str(key)) < 0.20
        entries = [(s0, c0), (s1, c1)]
        if high:
            mult = 5 + int(10 * u01("TAILMAG", str(key)))
            entries += [(s0, (mult - 1) * c0), (s2, 9), (h0, 8), (h1, 8)]
        else:
            entries += [(s3, 9), (h2, 8), (h3, 8)]
        if u01("QC", str(key)) < 0.5:
            entries.append((h4, 3))
        for c, v in entries:
            rows.append(i)
            cols.append(c)
            vals.append(v)
        lib[i] = 1000 + (key % 47)

    X = sparse.coo_matrix((vals, (rows, cols)), shape=(len(m), g), dtype=np.int64).tocsr()

    y = {
        d: 8 + 5 * z[d] + 0.002 * (age[d] - 77.5) ** 2 + 0.05 * (u01("YNOISE", d) - 0.5)
        for d in donors
    }
    shift = max(0.0, -min(y.values()) + 0.1)
    y = {d: v + shift for d, v in y.items()}

    def role_inputs(ds: list[str]) -> tuple[dict, np.ndarray, pd.DataFrame]:
        mask = m.donor_id.astype(str).isin(ds).to_numpy()
        q = m.loc[mask].reset_index(drop=True)
        dm = pd.DataFrame(
            {
                "donor_id": ds,
                "AT8": [y[d] for d in ds],
                "age": [age[d] for d in ds],
                "sex": [sex[d] for d in ds],
            }
        )
        return (
            {
                "scalar_raw_counts": X[mask],
                "scalar_feature_ids": ids,
                "matrix_id": q.matrix_id.tolist(),
                "local_row": q.local_row.tolist(),
                "cell_id": q.cell_id.tolist(),
                "donor_id": q.donor_id.astype(str).tolist(),
                "stable_key": q.stable_key.tolist(),
                "source_library": lib[mask],
                "donor_metadata": dm,
            },
            mask,
            q,
        )

    di, _, _ = role_inputs(disc)
    ci, _, _ = role_inputs(conf)

    frozen = freeze_target_after_role(
        target_dir=root / "target",
        discovery_authority_dir=root / "discovery_link",
        role_dir=root / "role",
        feature_split_csv=feature_split_csv,
        membership_csv=membership_csv,
        **di,
    )
    tail = freeze_tail_after_discovery_authority(
        tail_dir=root / "tail",
        discovery_authority_dir=root / "discovery_link",
        target_dir=root / "target",
        role_dir=root / "role",
        feature_split_csv=feature_split_csv,
        membership_csv=membership_csv,
        **di,
    )
    build_technical_registry(
        root / "tech",
        [],
        {"membership": MEMBERSHIP_SHA256},
        "synthetic fixture: no extra technical block beyond frozen Q_DEPTH/Q_DETECT",
    )
    build_primary_only_family(
        root / "family",
        ALLOWED_STATUS,
        {"rare_audit": RARE_AUDIT_PLACEHOLDER_SHA256},
        "historical rare5 exact scoring authority unrecovered",
    )

    cmeta = pd.DataFrame(
        {
            "donor_id": conf,
            "AT8": [y[d] for d in conf],
            "age": [age[d] for d in conf],
            "sex": [sex[d] for d in conf],
            "IMMUNE_FRACTION": [0.02 + 0.02 * u01("IMM", d) for d in conf],
        }
    )

    return {
        "root": root,
        "membership": m,
        "feature": f,
        "ids": ids,
        "role": load_role_authority(root / "role"),
        "discovery": disc,
        "confirmation": conf,
        "discovery_inputs": di,
        "confirmation_inputs": ci,
        "confirmation_metadata": cmeta,
        "frozen": frozen,
        "tail": tail,
    }


def run(root: Path, membership_csv: Path, feature_split_csv: Path) -> dict:
    t0 = time.perf_counter()
    fx = build_fixture(root, membership_csv, feature_split_csv)
    sys.stderr.write("PHASE fixture_complete\n"); sys.stderr.flush()
    t_fixture = time.perf_counter()
    d = fx["discovery_inputs"]
    c = fx["confirmation_inputs"]
    result = adjudicate_from_raw(
        target_dir=root / "target",
        tail_dir=root / "tail",
        role_dir=root / "role",
        discovery_authority_dir=root / "discovery_link",
        technical_registry_dir=root / "tech",
        family_registry_dir=root / "family",
        discovery_scalar_raw_counts=d["scalar_raw_counts"],
        scalar_feature_ids=fx["ids"],
        discovery_matrix_id=d["matrix_id"],
        discovery_local_row=d["local_row"],
        discovery_cell_id=d["cell_id"],
        discovery_donor_id=d["donor_id"],
        discovery_stable_key=d["stable_key"],
        discovery_source_library=d["source_library"],
        discovery_metadata=d["donor_metadata"],
        confirmation_scalar_raw_counts=c["scalar_raw_counts"],
        confirmation_matrix_id=c["matrix_id"],
        confirmation_local_row=c["local_row"],
        confirmation_cell_id=c["cell_id"],
        confirmation_donor_id=c["donor_id"],
        confirmation_stable_key=c["stable_key"],
        confirmation_source_library=c["source_library"],
        confirmation_metadata=fx["confirmation_metadata"],
        feature_split_csv=feature_split_csv,
        membership_csv=membership_csv,
    )
    t_adjud = time.perf_counter()
    sys.stderr.write("PHASE adjudication_complete\n"); sys.stderr.flush()

    target = load_target_v2(root / "target", feature_split_csv)
    tail = load_tail_authority(root / "tail", target_package_root_sha256=target["package_root_sha256"])
    discovery_link = load_discovery_authority(root / "discovery_link", root / "target", root / "role", feature_split_csv)
    role = load_role_authority(root / "role")
    tech = load_technical_registry(root / "tech")
    family = load_primary_only_family(root / "family")
    sys.stderr.write("PHASE reload_complete\n"); sys.stderr.flush()

    # Keep output canonical and path-independent. Timings are reported separately to stderr only.
    out = {
        "schema": "t0-canonical-synthetic-regression-v1",
        "authority_sha256": {
            "membership": sha256(membership_csv),
            "feature_split": sha256(feature_split_csv),
        },
        "package_roots": {
            "donor_role": role["package_root_sha256"],
            "target": target["package_root_sha256"],
            "discovery_link": discovery_link["package_root_sha256"],
            "tail": tail["package_root_sha256"],
            "technical": tech["package_root_sha256"],
            "family": family["package_root_sha256"],
        },
        "donors": {
            "discovery": fx["discovery"],
            "confirmation": fx["confirmation"],
        },
        "result": _canonicalize(result),
    }
    sys.stderr.write("PHASE result_canonicalized\n"); sys.stderr.flush()
    sys.stderr.write(json.dumps({"fixture_seconds": t_fixture - t0, "adjudication_seconds": t_adjud - t_fixture}, sort_keys=True) + "\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--membership", required=True)
    ap.add_argument("--feature-split", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out = run(Path(args.work_dir), Path(args.membership), Path(args.feature_split))
    text = json.dumps(out, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(hashlib.sha256(text.encode()).hexdigest(), flush=True)
    sys.stdout.flush(); sys.stderr.flush()
    # Some container runtimes retain native numerical-library cleanup state after the
    # exact coherence/QC path. All authoritative bytes are already fsync-visible here;
    # bypass interpreter finalizers so the regression executable has deterministic exit.
    os._exit(0)


if __name__ == "__main__":
    main()
