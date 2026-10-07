#!/usr/bin/env python3
"""Build the S157 paired-challenge worlds from committed code, by the pre-registered rules.

Claim namespace: V77_SYNTHETIC_WORLD_QUALIFICATION. Pre-registration:
results/v77/V77_S157_PAIRED_CHALLENGE_PREREGISTRATION_V1.json (committed in f36ad6ad, before any
challenge world existed). Four worlds share the seed-7302 truth (DEVELOPMENT_CALIBRATION):

    NULL           no challenge component
    BIO            a latent tied to the largest biological state raises module M
    TWIN_EXACT     the same latent read as capture; identical observables by construction
    TWIN_OPERATOR  a capture nuisance on module M tied to a matched set of operators

Every design constant is derived here by the rule fixed in the pre-registration, from the truth
and the NULL world's planted modules, never from any outcome. The challenge spec is written only
into each world's hidden-truth folder.

Before anything is scored, this builder verifies: the truth is byte-identical across the four
worlds; the observable output of TWIN_EXACT is byte-identical to BIO's (RED_1 at the producer);
and NULL reproduces the earlier repaired world fs_smoke_s161 byte for byte.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

EXECUTOR_FILES = ("scripts/v77/build_v77_s157_challenge.py", "scripts/v77/build_v77_extended_truth.py",
                  "scripts/v77/build_v77_fullscale_rna_observer_v2.py", "scripts/v77/v77_address_universe.py",
                  "scripts/v64/v73_full104_qc_calibration.py", "scripts/v64/v73_full104_population_geometry.py")
PREREG = ROOT / "results" / "v77" / "V77_S157_PAIRED_CHALLENGE_PREREGISTRATION_V1.json"
OBS_DIR = "FULLSCALE_V2_CANONICAL_sharded"
MODULE_SIZE = 200


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout.strip()


def _run(cmd):
    r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"step failed: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    return " ".join(["python", *cmd])


def _tree_digests(d: Path) -> dict:
    return {str(p.relative_to(d)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.rglob("*")) if p.is_file()}


def _truth(world: Path) -> dict:
    z = {}
    for f in sorted((world / "hidden_truth").glob("TRUTH_*.npz")):
        d = np.load(f, allow_pickle=False)
        for k in ("state_index", "operator_index", "global_cell_index"):
            z.setdefault(k, []).append(d[k])
    return {k: np.concatenate(v) for k, v in z.items()}


def build_truth(world: Path, seed: int, cells: int) -> str:
    if world.exists():
        sys.exit(f"refusing to reuse {world}: every challenge world is built fresh")
    return _run(["scripts/v77/build_v77_extended_truth.py", "--root", str(world), "--cells", str(cells),
                 "--shard-size", "500", "--seed", str(seed), "--world", "FULL"])


def observe(world: Path, seed: int) -> str:
    return _run(["scripts/v77/build_v77_fullscale_rna_observer_v2.py", "--root", str(world),
                 "--seed", str(seed), "--background", "v1"])


def design(null_world: Path, universe: np.ndarray, seed: int, prereg: dict) -> dict:
    import v77_address_universe as AU
    rules = prereg["design_rules_fixed_now"]
    z = _truth(null_world)
    st, op = z["state_index"].astype(np.int64), z["operator_index"].astype(np.int64)
    k_star = int(np.argmax(np.bincount(st)))
    man = json.loads((null_world / "observable_raw" / OBS_DIR / "FULLSCALE_V2_MANIFEST.json").read_text())
    used = set()
    for s in man["module_address_sets"].values():
        used |= {int(a) for a in s}
    uni = AU.AddressUniverse(seed)
    covered_by_all = uni.source_support.all(axis=0)
    cands = [int(a) for a in universe if covered_by_all[int(a)] and int(a) not in used]
    cands.sort(key=lambda a: hashlib.sha256(f"S157:{uni.address_id[a]}".encode()).hexdigest())
    module = sorted(cands[:MODULE_SIZE])
    if len(module) != MODULE_SIZE:
        sys.exit(f"only {len(module)} eligible module addresses; the pre-registered size is {MODULE_SIZE}")
    target = int((st == k_star).sum())
    ops = np.unique(op)
    frac = {int(o): float(((op == o) & (st == k_star)).sum()) / float((op == o).sum()) for o in ops}
    order = sorted(frac, key=lambda o: (-frac[o], o))
    chosen, total = [], 0
    for o in order:
        if total >= target:
            break
        chosen.append(o)
        total += int((op == o).sum())
    in_set = np.isin(op, chosen)
    return dict(k_star=k_star, state_cells=target,
                module_addresses=module, module_address_ids=[str(uni.address_id[a]) for a in module],
                operator_set=sorted(chosen), operator_set_cells=int(in_set.sum()),
                operator_set_overlap_with_state=int((in_set & (st == k_star)).sum()),
                delta=float(rules["delta"]), beta=float(rules["beta"]),
                candidates_available=len(cands), existing_module_addresses=len(used))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--reference-null", required=True, help="the earlier repaired world NULL must reproduce")
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--cells", type=int, default=2000)
    a = ap.parse_args()
    for rel in EXECUTOR_FILES:
        if subprocess.run(["git", "ls-files", "--error-unmatch", rel], capture_output=True, cwd=ROOT).returncode:
            sys.exit(f"refusing: {rel} is not tracked")
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode:
            sys.exit(f"refusing: {rel} differs from HEAD")
    if _git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("refusing: tracked files are modified")
    head = _git("rev-parse", "HEAD")
    digests = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in EXECUTOR_FILES}
    prereg = json.loads(PREREG.read_text())
    universe = np.load(a.universe, allow_pickle=False)["evaluation_universe"]

    out = Path(a.out_dir)
    worlds = {k: out / k for k in ("NULL", "BIO", "TWIN_EXACT", "TWIN_OPERATOR")}
    commands = {"NULL": [build_truth(worlds["NULL"], a.seed, a.cells), observe(worlds["NULL"], a.seed)]}
    spec_common = design(worlds["NULL"], universe, a.seed, prereg)
    for kind in ("BIO", "TWIN_EXACT", "TWIN_OPERATOR"):
        cmds = [build_truth(worlds[kind], a.seed, a.cells)]
        spec = dict(kind=kind, k_star=spec_common["k_star"], module_addresses=spec_common["module_addresses"],
                    operator_set=spec_common["operator_set"], delta=spec_common["delta"], beta=spec_common["beta"],
                    preregistration=str(PREREG.relative_to(ROOT)).replace("\\", "/"))
        with open(worlds[kind] / "hidden_truth" / "CHALLENGE_SPEC.json", "w", newline="\n") as fh:
            fh.write(json.dumps(spec, indent=2) + "\n")
        cmds.append(observe(worlds[kind], a.seed))
        commands[kind] = cmds
        print(f"built {kind}", flush=True)

    truth = {k: {n: h for n, h in _tree_digests(w / "hidden_truth").items() if n.startswith("TRUTH_") and n.endswith(".npz")}
             for k, w in worlds.items()}
    obs = {k: _tree_digests(w / "observable_raw" / OBS_DIR) for k, w in worlds.items()}
    ref = _tree_digests(Path(a.reference_null) / "observable_raw" / OBS_DIR)
    checks = dict(
        truth_identical_across_worlds=all(truth[k] == truth["NULL"] for k in worlds),
        exact_twin_observables_byte_identical_to_bio=(obs["TWIN_EXACT"] == obs["BIO"]),
        null_reproduces_reference=(obs["NULL"] == ref),
        bio_differs_from_null=(obs["BIO"] != obs["NULL"]),
        operator_twin_differs_from_bio=(obs["TWIN_OPERATOR"] != obs["BIO"]),
        no_challenge_word_in_any_observable_manifest=not any(
            b"CHALLENGE" in (w / "observable_raw" / OBS_DIR / "FULLSCALE_V2_MANIFEST.json").read_bytes()
            for w in worlds.values()))
    rec = dict(
        schema="V77_S157_CHALLENGE_WORLDS_BUILD_V1",
        claim_class="V77_SYNTHETIC_WORLD_QUALIFICATION",
        preregistration=dict(path=str(PREREG.relative_to(ROOT)).replace("\\", "/"),
                             sha256=hashlib.sha256(PREREG.read_bytes()).hexdigest()),
        realization=dict(truth_seed=a.seed, cells=a.cells, status="DEVELOPMENT_CALIBRATION"),
        design=spec_common, worlds={k: str(w) for k, w in worlds.items()}, commands=commands,
        observable_file_sha256=obs, checks=checks,
        all_checks_pass=all(checks.values()),
        source_commit=head, provenance_status="CLEAN_COMMITTED_HEAD__EXECUTORS_TRACKED_AND_UNMODIFIED",
        executor_sha256=digests, no_training_performed=True)
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    with open(a.receipt, "w", newline="\n") as fh:
        fh.write(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(dict(design={k: v for k, v in spec_common.items() if "address" not in k}, checks=checks), indent=1))
    if not rec["all_checks_pass"]:
        sys.exit("a pre-scoring check failed; see the receipt")


if __name__ == "__main__":
    main()
