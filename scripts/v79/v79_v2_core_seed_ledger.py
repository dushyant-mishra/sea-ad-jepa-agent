#!/usr/bin/env python3
"""Controller-side seed ledger builder.

Transforms frozen world-index seed authority into opaque fit-id -> numeric seed
records for the fitter. World names/indices never leave this controller surface.
"""
from __future__ import annotations

import re
from typing import Mapping

import numpy as np

import v79_v2_core_fit_runner as R


class SeedLedgerRefused(RuntimeError):
    pass


def _refuse(msg: str):
    raise SeedLedgerRefused(f"REFUSED V2_CORE seed ledger: {msg}")


def _seed(root: int, world_index: int, gene_index: int, stream: int) -> int:
    ss = np.random.SeedSequence(entropy=int(root), spawn_key=(int(world_index), int(gene_index), int(stream)))
    return int(ss.generate_state(1, np.uint32)[0])


def expected_fit_entry(contract: Mapping, *, world_index: int, opaque_world_id: str,
                       manifest_sha: str, gene_index: int, part: str) -> dict:
    if part not in {"detection", "positive"}:
        _refuse("unknown part")
    streams = contract["seeds"]["gene_streams"]
    primary_stream = int(streams["fit_det_primary" if part == "detection" else "fit_pos_primary"])
    escalation_stream = int(streams["fit_det_escalation" if part == "detection" else "fit_pos_escalation"])
    root = int(contract["seeds"]["root"])
    primary = _seed(root, world_index, gene_index, primary_stream)
    escalation = _seed(root, world_index, gene_index, escalation_stream)
    if primary == escalation:
        _refuse("primary and escalation seeds unexpectedly collide")
    fid = R.fit_identity(opaque_world_id, manifest_sha, part, gene_index)
    return {"fit_id": fid, "primary_seed": primary, "escalation_seed": escalation}


def build_seed_ledger(contract: Mapping, root_manifest: Mapping, blinded_index: Mapping) -> list[dict]:
    if root_manifest.get("mode") != "QUALIFICATION_TRUTH_FREEZE":
        _refuse("root manifest is not qualification truth freeze")
    worlds = root_manifest.get("worlds")
    if not isinstance(worlds, list) or len(worlds) != int(root_manifest.get("world_count", -1)):
        _refuse("invalid root world list")
    idx_worlds = blinded_index.get("worlds")
    if not isinstance(idx_worlds, list) or len(idx_worlds) != int(blinded_index.get("world_count", -1)):
        _refuse("invalid blinded index")
    by_oid = {str(x.get("opaque_world_id")): x for x in idx_worlds}
    n_gene = int(contract["worlds"]["genes_per_world"])
    out = []
    for w in worlds:
        oid = str(w.get("opaque_world_id", ""))
        wi = w.get("world_index")
        if not re.fullmatch(r"[0-9a-f]{12}", oid) or not isinstance(wi, int) or oid not in by_oid:
            _refuse("invalid controller world identity")
        rec = by_oid[oid]
        msha = str(rec.get("manifest_sha256", ""))
        if msha != str(w.get("fit_manifest_sha256", "")):
            _refuse("root/index fit manifest binding mismatch")
        for g in range(n_gene):
            for part in ("detection", "positive"):
                out.append(expected_fit_entry(contract, world_index=wi, opaque_world_id=oid,
                                              manifest_sha=msha, gene_index=g, part=part))
    want = int(contract["resources"]["estimate"]["n_fits"])
    if len(out) != want or len({x["fit_id"] for x in out}) != want:
        _refuse("seed ledger cardinality/identity mismatch")
    out.sort(key=lambda x: x["fit_id"])
    return out
