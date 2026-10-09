#!/usr/bin/env python3
"""Freeze ONE evaluation universe: the real TRAIN prevalence-filtered gene set.

THE DEFECT THIS FIXES. Every Observer-V2 candidate was independently prevalence-filtered on
its OWN counts before topology was scored, giving vertex sets of 12,468 to 28,884 genes
against a canonical real universe of 19,569. Mean degree, transitivity, correlation fractions
and community structure were therefore compared across DIFFERENT graphs.

Why that is not merely untidy: an observer that makes thousands of canonical genes vanish
should be PENALISED for making them vanish. Under per-candidate filtering it is instead
rewarded with a smaller, easier graph on which topology is then scored.

THE FIX. One frozen vertex set, taken from the REAL TRAIN data at a 0.05 detection floor, the
same filtering that produced the frozen topology envelope. Every synthetic candidate is scored
on exactly those registry indices, whether or not the candidate itself detects them. A gene the
candidate never detects becomes a zero column and contributes no correlation, which is the
correct penalty.

The synthetic world is built over the canonical registry order, so a real registry index means
the same address in both. Candidate-specific filtered metrics may still be reported, but only
as secondary diagnostics.

NAMING. Metrics scored on this universe carry the suffix TRAIN_PREVALENCE05_19569. Metrics over
all 41,238 registry addresses carry FULL_REGISTRY_41238. Only the former may be quoted against
the frozen topology and abundance envelopes.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v77_real_calibration as RC

DETECTION_FLOOR = 0.05


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(RC.DEFAULT_CACHE))
    ap.add_argument("--out", required=True)
    ap.add_argument("--index-out", required=True)
    a = ap.parse_args()

    X, cls, don, src, digests = RC.load_real(Path(a.cache))
    n, G = X.shape
    gdet = np.asarray((X > 0).sum(0)).ravel() / n
    keep = np.where(gdet > DETECTION_FLOOR)[0].astype(np.int64)

    np.savez_compressed(a.index_out, evaluation_universe=keep,
                        detection_rate=gdet[keep].astype(np.float32),
                        n_addresses_total=np.int64(G))
    h = hashlib.sha256(Path(a.index_out).read_bytes()).hexdigest()

    rec = dict(
        schema="V77_FROZEN_EVALUATION_UNIVERSE_V1",
        name="TRAIN_PREVALENCE05_19569",
        definition=f"real FOUNDATION TRAIN addresses with detection rate > {DETECTION_FLOOR}",
        n_genes=int(len(keep)), n_addresses_total=int(G),
        detection_floor=DETECTION_FLOOR,
        index_file=dict(path=a.index_out, sha256=h),
        source=dict(cache=str(a.cache), n_shards=len(digests), shard_digests=digests,
                    pathology_blind=True, train_only=True, read_only=True),
        rule=("every synthetic candidate is scored on EXACTLY these registry indices. A gene a "
              "candidate never detects becomes a zero column and contributes nothing, which is "
              "the correct penalty for making canonical genes disappear."),
        naming=dict(
            scored_on_this_universe="<metric>__TRAIN_PREVALENCE05_19569",
            scored_on_all_addresses="<metric>__FULL_REGISTRY_41238",
            only_the_former_may_be_quoted_against_frozen_envelopes=True),
        supersedes=("per-candidate prevalence filtering, which produced vertex sets of 12,468 to "
                    "28,884 genes and made topology statistics non-comparable across candidates"))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(dict(name=rec["name"], n_genes=rec["n_genes"],
                          index_sha256=h[:16]), indent=2))


if __name__ == "__main__":
    main()
