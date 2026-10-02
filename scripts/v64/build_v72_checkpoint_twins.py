#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def corr_max(emb: np.ndarray, target: np.ndarray) -> float:
    vals = []
    for i in range(emb.shape[1]):
        x = emb[:, i]
        for j in range(target.shape[1]):
            y = target[:, j]
            if np.std(x) == 0 or np.std(y) == 0:
                vals.append(0.0)
            else:
                vals.append(float(abs(np.corrcoef(x, y)[0, 1])))
    return max(vals) if vals else 0.0


def build(root: Path, seed: int = 7212, n: int = 512) -> dict:
    rng = np.random.default_rng(seed)
    obs = root / "observable_checkpoints"
    truth = root / "hidden_checkpoint_truth"
    obs.mkdir(parents=True, exist_ok=True)
    truth.mkdir(parents=True, exist_ok=True)

    shared = rng.normal(size=(n, 4))
    private = rng.normal(size=(n, 2))
    source_ix = np.arange(n) % 3
    donor_ix = np.arange(n) % 12
    source_oh = np.eye(3)[source_ix]
    donor_oh = np.eye(12)[donor_ix]
    x = np.c_[shared + .08*rng.normal(size=shared.shape),
              rng.normal(size=(n, 4))]
    W = rng.normal(size=(x.shape[1], 4))

    healthy = x @ W + .05*rng.normal(size=(n, 4))
    collapsed = np.zeros((n, 4), dtype=float) + 1e-8*rng.normal(size=(n,4))
    source_shortcut = np.c_[source_oh, np.zeros((n,1))]
    donor_shortcut = donor_oh[:, :4]
    private_leak = np.c_[private, private]
    overconfident = healthy + np.c_[private, private]
    uncertainty_healthy = np.full((n,1), .4)
    uncertainty_overconfident = np.full((n,1), 1e-6)

    cases = {
        "HEALTHY": (healthy, uncertainty_healthy),
        "COLLAPSED": (collapsed, uncertainty_healthy),
        "SOURCE_SHORTCUT": (source_shortcut, uncertainty_healthy),
        "DONOR_SHORTCUT": (donor_shortcut, uncertainty_healthy),
        "PRIVATE_STATE_LEAK": (private_leak, uncertainty_healthy),
        "OVERCONFIDENT_UNRECOVERABLE": (overconfident, uncertainty_overconfident),
    }
    manifests = {}
    for name, (emb, unc) in cases.items():
        p = obs / f"{name}.npz"
        np.savez_compressed(p, embedding=emb.astype(np.float32),
                            uncertainty=unc.astype(np.float32),
                            sample_id=np.array([f"S{i:05d}" for i in range(n)]))
        manifests[name] = {
            "file": p.name,
            "sha256": sha256_file(p),
            "embedding_dim": int(emb.shape[1]),
            "status": "SYNTHETIC_CHECKPOINT_TWIN",
        }

    # Corrupt case: manifest binds the wrong digest and wrong axis.
    src = obs / "HEALTHY.npz"
    corrupt = obs / "CORRUPT_MANIFEST_AXIS.npz"
    z = np.load(src, allow_pickle=False)
    np.savez_compressed(corrupt, embedding=z["embedding"].T,
                        uncertainty=z["uncertainty"],
                        sample_id=z["sample_id"])
    manifests["CORRUPT_MANIFEST_AXIS"] = {
        "file": corrupt.name,
        "sha256": "0"*64,
        "embedding_dim": 4,
        "status": "INTENTIONALLY_CORRUPT",
    }

    (obs / "MANIFEST.json").write_text(json.dumps({
        "schema":"V72_SYNTHETIC_CHECKPOINT_TWINS_MANIFEST_V1",
        "cases":manifests,
        "truth_not_available_to_checkpoint_selection":True,
    }, indent=2)+"\n")
    np.savez_compressed(truth / "CHECKPOINT_TRUTH.npz",
                        shared=shared, private=private,
                        source_ix=source_ix, donor_ix=donor_ix)
    return {
        "status":"PASS__CHECKPOINT_TWINS_BUILT",
        "n":n,
        "cases":sorted(manifests),
    }


def audit(root: Path) -> dict:
    obs = root/"observable_checkpoints"
    truth = root/"hidden_checkpoint_truth"
    m = json.loads((obs/"MANIFEST.json").read_text())
    t = np.load(truth/"CHECKPOINT_TRUTH.npz", allow_pickle=False)
    shared, private = t["shared"], t["private"]
    source_ix, donor_ix = t["source_ix"], t["donor_ix"]

    results = {}
    for name, meta in m["cases"].items():
        p = obs/meta["file"]
        if not p.exists():
            results[name] = {"status":"FAIL__MISSING_FILE"}
            continue
        digest_ok = sha256_file(p) == meta["sha256"]
        z = np.load(p, allow_pickle=False)
        emb = z["embedding"]
        axis_ok = emb.ndim == 2 and emb.shape[0] == len(source_ix) and emb.shape[1] == meta["embedding_dim"]
        if not digest_ok or not axis_ok:
            results[name] = {
                "status":"FAIL__MANIFEST_OR_AXIS",
                "digest_ok":digest_ok,
                "axis_ok":axis_ok,
            }
            continue
        onehot_source = np.eye(3)[source_ix]
        onehot_donor = np.eye(12)[donor_ix]
        results[name] = {
            "status":"AUDITED",
            "variance":float(np.mean(np.var(emb, axis=0))),
            "shared_corr_max":corr_max(emb, shared),
            "private_corr_max":corr_max(emb, private),
            "source_corr_max":corr_max(emb, onehot_source),
            "donor_corr_max":corr_max(emb, onehot_donor),
            "mean_uncertainty":float(np.mean(z["uncertainty"])),
        }
    return results


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--audit", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.audit:
        print(json.dumps(audit(root), indent=2))
    else:
        print(json.dumps(build(root), indent=2))


if __name__ == "__main__":
    main()
