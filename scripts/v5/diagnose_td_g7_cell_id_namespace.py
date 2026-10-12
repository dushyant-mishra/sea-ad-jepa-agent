#!/usr/bin/env python3
"""Read-only, metadata-only cell-ID namespace diagnostic for the G7 NOT_ESTIMABLE outcome (PR #298, 6119238901).

The single G7 successor attempt (receipt 47f9be6e) found 0 natural overlap between the 34 Sample-A HVS/SEA matrices
and their joined S174 shards. This diagnostic asks whether that is genuine disjointness or an identifier-namespace
mismatch. It is not a G7 rerun and creates no G7 or biological authority.

It reads only cell identifiers and index metadata:
  - the authenticated sample freeze, columns sample/source/matrix_id/cell_id;
  - the pinned Macha S174 freeze, matrix -> stem;
  - the G1b shard authority, read from git;
  - the S174 meta `cell_id` arrays, through G7's own SHA-checked loader.
It never opens S174 counts, H5AD values, G6 values or corrected-replay values.

Stages:
  syntax      Exact intersections only, computed three ways: within G7's matrix -> stem join, per matrix against every
              shard, and globally. Plus syntax characterization: counts, uniqueness, lengths, character-class shapes,
              delimiters, and a few raw examples per study.
  transforms  Apply a committed, prospectively specified list of deterministic transforms. Report, per transform,
              injectivity (collisions) on each side, reversibility as declared, and overlap by matrix/shard and
              globally. A transform with any collision on either side cannot establish overlap.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
G7_PATH = ROOT / "scripts" / "v5" / "audit_td_relational_g7_s174_overlap_v2.py"
SAMPLE_FREEZE_SHA = "79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6"
MACHA_FREEZE_SHA = "240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c"
SAMPLE_A = "A_NATURAL_MIXTURE"
N_HVS_SEA_MATRICES = 34
N_SHARDS = 35
EXAMPLES_PER_STUDY = 3


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _g7():
    spec = importlib.util.spec_from_file_location("td_g7_for_id_namespace_diagnostic", G7_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shape(s: str) -> str:
    """Character-class signature: letters -> A/a, digits -> 9, runs collapsed with their length."""
    classes = re.sub(r"[A-Z]", "A", re.sub(r"[a-z]", "a", re.sub(r"[0-9]", "9", s)))
    return re.sub(r"(.)\1*", lambda m: m.group(1) + (str(len(m.group(0))) if len(m.group(0)) > 1 else ""), classes)


def describe(ids: list[str]) -> dict:
    lengths = Counter(len(x) for x in ids)
    delims = Counter(ch for x in ids for ch in set(x) if not ch.isalnum())
    shapes = Counter(shape(x) for x in ids)
    return {"n": len(ids), "unique": len(set(ids)), "length_counts": dict(sorted(lengths.items())),
            "delimiter_char_counts": dict(sorted(delims.items())), "top_shapes": shapes.most_common(5)}


def load_namespaces(sample_freeze: Path, macha_freeze: Path, cache_root: Path) -> dict:
    if sha(sample_freeze) != SAMPLE_FREEZE_SHA or sha(macha_freeze) != MACHA_FREEZE_SHA:
        raise SystemExit("STOP: sample freeze or Macha freeze SHA mismatch")
    frame = pd.read_csv(sample_freeze, dtype=str, usecols=["sample", "source", "matrix_id", "cell_id"])
    a = frame[frame["sample"].eq(SAMPLE_A) & ~frame["source"].eq("NPH52")]
    sample_ids = {str(m): g.cell_id.astype(str).tolist() for m, g in a.groupby("matrix_id", sort=True)}
    study = {str(m): str(g.source.iloc[0]) for m, g in a.groupby("matrix_id", sort=True)}
    if len(sample_ids) != N_HVS_SEA_MATRICES:
        raise SystemExit(f"STOP: {len(sample_ids)} Sample-A HVS/SEA matrices != {N_HVS_SEA_MATRICES}")
    matrices = {str(m["matrix_id"]): m for m in json.loads(macha_freeze.read_text(encoding="utf-8"))["matrices"]}
    g7 = _g7()
    _, g1b_freeze, _, g1b_freeze_sha = g7.load_g1b_authority_from_pass_commit(G7_PATH)
    shards = g1b_freeze["rebuilt_cache"]["shards"]
    if len(shards) != N_SHARDS:
        raise SystemExit(f"STOP: {len(shards)} shards != {N_SHARDS}")
    s174 = {}
    for stem, authority in sorted(shards.items()):
        cells, _, meta_sha = g7.load_s174_cell_index(cache_root / f"{stem}.meta.npz", authority["meta"])
        s174[stem] = {"ids": cells.tolist(), "meta_sha256": meta_sha}
    join = {m: str(matrices[m]["stem"]) for m in sample_ids}
    return {"sample": sample_ids, "study": study, "s174": s174, "join": join, "g1b_freeze_sha256": g1b_freeze_sha}


def exact_overlaps(ns: dict) -> dict:
    s174_sets = {stem: set(v["ids"]) for stem, v in ns["s174"].items()}
    all_s174 = set().union(*s174_sets.values())
    per_matrix = {}
    for m, ids in ns["sample"].items():
        ids_set = set(ids)
        stem = ns["join"][m]
        per_matrix[m] = {"study": ns["study"][m], "joined_stem": stem, "n_sample_ids": len(ids_set),
                         "joined_stem_in_g1b": stem in s174_sets,
                         "overlap_with_joined_stem": len(ids_set & s174_sets.get(stem, set())),
                         "shards_with_any_overlap": sorted(s for s, ss in s174_sets.items() if ids_set & ss)}
    all_sample = set().union(*(set(v) for v in ns["sample"].values()))
    return {"per_matrix": per_matrix, "global_overlap_any_shard": len(all_sample & all_s174),
            "n_sample_ids_total": len(all_sample), "n_s174_ids_total": len(all_s174),
            "s174_ids_duplicated_across_shards": sum(len(v) for v in s174_sets.values()) - len(all_s174)}


def syntax(ns: dict) -> dict:
    by_study_sample: dict[str, list[str]] = defaultdict(list)
    for m, ids in ns["sample"].items():
        by_study_sample[ns["study"][m]].extend(ids)
    joined_stems = defaultdict(set)
    for m, stem in ns["join"].items():
        joined_stems[ns["study"][m]].add(stem)
    by_study_s174 = {st: [x for stem in sorted(stems) for x in ns["s174"].get(stem, {"ids": []})["ids"]]
                     for st, stems in joined_stems.items()}
    unjoined = sorted(set(ns["s174"]) - set(ns["join"].values()))
    return {
        "sample_a_by_study": {st: {**describe(ids), "examples": ids[:EXAMPLES_PER_STUDY]} for st, ids in sorted(by_study_sample.items())},
        "s174_joined_shards_by_study": {st: {**describe(ids), "examples": ids[:EXAMPLES_PER_STUDY], "stems": sorted(joined_stems[st])}
                                        for st, ids in sorted(by_study_s174.items())},
        "s174_unjoined_shards": {stem: {**describe(ns["s174"][stem]["ids"]), "examples": ns["s174"][stem]["ids"][:EXAMPLES_PER_STUDY]}
                                 for stem in unjoined},
    }


TRANSFORMS = {  # the only transforms the committed stage-3 spec may name
    "IDENTITY": lambda x: x,
    "STRIP_WHITESPACE": lambda x: x.strip(),
    "UPPERCASE": lambda x: x.upper(),
    "DROP_TRAILING_FIELD": lambda x: x.rsplit("-", 1)[0],
    "BARCODE_AND_TRAILING_FIELD": lambda x: f"{x.split('-')[0]}-{x.split('-')[-1]}",
    "BARCODE_ONLY": lambda x: x.split("-", 1)[0],
}
CAN_ESTABLISH = ("STRIP_WHITESPACE", "UPPERCASE")
BLOCKS_DISJOINTNESS = ("DROP_TRAILING_FIELD", "BARCODE_AND_TRAILING_FIELD")


def _image(groups: dict[str, list[str]], fn) -> tuple[dict, dict]:
    """Map every ID through fn; return output -> set of preimages, and per-group collision counts."""
    pre: dict[str, set] = defaultdict(set)
    within = {}
    for key, ids in groups.items():
        outs = [fn(x) for x in ids]
        within[key] = len(outs) - len(set(outs))
        for x, y in zip(ids, outs):
            pre[y].add(x)
    return pre, within


def evaluate_transform(name: str, ns: dict) -> dict:
    fn = TRANSFORMS[name]
    s174_groups = {stem: v["ids"] for stem, v in ns["s174"].items()}
    a_pre, a_within = _image(ns["sample"], fn)
    b_pre, b_within = _image(s174_groups, fn)
    a_inputs = sum(len(v) for v in ns["sample"].values())
    b_inputs = sum(len(v) for v in s174_groups.values())
    shared = set(a_pre) & set(b_pre)
    b_by_stem = {stem: {fn(x) for x in ids} for stem, ids in s174_groups.items()}
    per_matrix = {}
    for m, ids in ns["sample"].items():
        outs = {fn(x) for x in ids}
        per_matrix[m] = {"overlap_with_joined_stem": len(outs & b_by_stem.get(ns["join"][m], set())),
                         "overlap_any_shard": len(outs & set(b_pre))}
    one_to_one = all(len(a_pre[y]) == 1 and len(b_pre[y]) == 1 for y in shared)
    return {"transform": name,
            "sample_a": {"inputs": a_inputs, "distinct_outputs": len(a_pre), "global_collisions": a_inputs - len(a_pre),
                         "max_within_matrix_collisions": max(a_within.values())},
            "s174": {"inputs": b_inputs, "distinct_outputs": len(b_pre), "global_collisions": b_inputs - len(b_pre),
                     "max_within_shard_collisions": max(b_within.values())},
            "collision_free_both_sides": a_inputs == len(a_pre) and b_inputs == len(b_pre),
            "global_overlap": len(shared), "overlap_all_one_to_one": one_to_one,
            "matrices_with_overlap_joined_stem": sum(v["overlap_with_joined_stem"] > 0 for v in per_matrix.values()),
            "matrices_with_overlap_any_shard": sum(v["overlap_any_shard"] > 0 for v in per_matrix.values()),
            "per_matrix": per_matrix}


def classify(results: dict) -> str:
    for name in CAN_ESTABLISH:
        r = results[name]
        if r["collision_free_both_sides"] and r["global_overlap"] >= 1 and r["overlap_all_one_to_one"]:
            return "IDENTIFIER_NAMESPACE_MISMATCH"
    if any(results[name]["global_overlap"] >= 1 for name in BLOCKS_DISJOINTNESS):
        return "ID_NAMESPACE_DIAGNOSTIC_NOT_ESTIMABLE"
    return "GENUINELY_DISJOINT_NATURAL_CELL_SETS"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["syntax", "transforms"])
    ap.add_argument("--sample-freeze", required=True)
    ap.add_argument("--macha-freeze", required=True)
    ap.add_argument("--s174-cache-root", required=True)
    ap.add_argument("--spec", help="committed stage-3 transform spec (transforms stage)")
    a = ap.parse_args()
    ns = load_namespaces(Path(a.sample_freeze), Path(a.macha_freeze), Path(a.s174_cache_root))
    if a.stage == "transforms":
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
        names = [t["name"] for t in spec["transforms"]]
        if set(names) != set(TRANSFORMS) or spec.get("status") != "PROSPECTIVE__COMMITTED_BEFORE_ANY_TRANSFORMED_OVERLAP_IS_COMPUTED":
            raise SystemExit("STOP: the transform spec does not name exactly the registered transforms")
        results = {name: evaluate_transform(name, ns) for name in names}
        out = {"schema": "JEPA_TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_TRANSFORMS_V1", "spec_sha256": sha(Path(a.spec)),
               "classification": classify(results),
               "summary": {n: {k: v for k, v in r.items() if k != "per_matrix"} for n, r in results.items()},
               "per_matrix": {n: r["per_matrix"] for n, r in results.items()},
               "values_opened": {"s174_counts": False, "h5ad": False, "g6": False, "corrected_replay": False},
               "g7_authority_created": False, "biological_replay_authorized": False, "training_authorized": False}
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    out = {"schema": "JEPA_TD_G7_CELL_ID_NAMESPACE_DIAGNOSTIC_SYNTAX_V1", "stage": "syntax_and_exact_intersections",
           "inputs": {"sample_freeze_sha256": SAMPLE_FREEZE_SHA, "macha_freeze_sha256": MACHA_FREEZE_SHA,
                      "g1b_freeze_sha256": ns["g1b_freeze_sha256"],
                      "s174_meta_sha256": {s: v["meta_sha256"] for s, v in sorted(ns["s174"].items())}},
           "exact": exact_overlaps(ns), "syntax": syntax(ns),
           "values_opened": {"s174_counts": False, "h5ad": False, "g6": False, "corrected_replay": False},
           "g7_authority_created": False, "biological_replay_authorized": False, "training_authorized": False}
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
