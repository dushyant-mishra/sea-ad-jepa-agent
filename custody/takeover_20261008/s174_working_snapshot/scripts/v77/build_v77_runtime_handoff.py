#!/usr/bin/env python3
"""V77 -> canonical-runtime handoff package (Phase 6). ZERO_UPDATE only; no optimizer, EMA or
checkpoint code, and no mutation.

For each S157 arm world it records what the runtime will receive and the digests the runtime must
reproduce through the same entrypoint: the adapter-level digests of the full world, and the
interface-level identity digests (feature, operator, support, batch scientific identity) of the
declared rehearsal batch, with the ZERO_UPDATE plumbing outputs as the baseline proof.

It also executes the q-safety probe the boundary needs, rather than citing it: counts at hidden
target positions are changed in a copy of the world, and the model-facing and operator-context
digests must not move while the readout digest must. A deliberately leaky model view, which writes
hidden values into the student evidence, is the control the probe must refuse.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import v77_synthetic_batch_adapter as AD  # noqa: E402

OBS_DIR = "FULLSCALE_V2_CANONICAL_sharded"
HIDDEN_FRACTION, ADAPTER_SEED = 0.15, 20261006
HIDDEN_BUMP = 5


def mutate_hidden_counts(world: Path, conv, universe: np.ndarray, obs_dir: str = OBS_DIR) -> int:
    """Add HIDDEN_BUMP to every stored count at a hidden-target position, in place. Returns the
    number of entries changed. Only positions the adapter hides are touched."""
    row_of = {int(g): i for i, g in enumerate(conv.global_cell_index)}
    hidden = np.asarray(conv.model.hidden_target_mask, dtype=bool)
    changed = 0
    for shard in sorted(glob.glob(str(Path(world) / "observable_raw" / obs_dir / "RNA_SPARSE_*.npz"))):
        z = dict(np.load(shard, allow_pickle=False))
        data = z["data"].copy()
        for r, g in enumerate(z["global_cell_index"]):
            i = row_of.get(int(g))
            if i is None:
                continue
            addrs = universe[np.flatnonzero(hidden[i])]
            lo, hi = int(z["indptr"][r]), int(z["indptr"][r + 1])
            hit = np.isin(z["indices"][lo:hi], addrs)
            data[lo:hi][hit] += HIDDEN_BUMP
            changed += int(hit.sum())
        z["data"] = data
        np.savez_compressed(shard, **z)
    return changed


def leaky_model_digest(conv) -> str:
    """The QUERY_LEAK control: the same model view with hidden values written into the evidence."""
    m, rd = conv.model, conv.readout
    lib = np.maximum(rd.full_library_size.astype(np.float64), 1.0)[:, None]
    leak = np.log1p(rd.query_counts.astype(np.float64) / lib * 1e4).astype(np.float32)
    student = np.where(m.hidden_target_mask, leak, m.student_expression).astype(np.float32)
    return AD.SyntheticModelBatch(gene_ids=m.gene_ids, student_expression=student,
                                  measurement_mask=m.measurement_mask,
                                  hidden_target_mask=m.hidden_target_mask).digest()


def hidden_value_invariance(world: Path, universe: np.ndarray, obs_dir: str = OBS_DIR,
                            max_cells: int | None = None) -> dict:
    conv = AD.build_from_world(Path(world), obs_dir, universe, HIDDEN_FRACTION, ADAPTER_SEED, max_cells=max_cells)
    with tempfile.TemporaryDirectory() as td:
        mutant = Path(td) / "MUTANT"
        shutil.copytree(world, mutant)
        changed = mutate_hidden_counts(mutant, conv, universe, obs_dir)
        mconv = AD.build_from_world(mutant, obs_dir, universe, HIDDEN_FRACTION, ADAPTER_SEED, max_cells=max_cells)
    same = {n: getattr(conv, n).digest() == getattr(mconv, n).digest()
            for n in ("model", "operator_context", "split_context", "readout")}
    leak_moves = leaky_model_digest(conv) != leaky_model_digest(mconv)
    return dict(hidden_entries_changed=changed,
                model_digest_unchanged=same["model"], operator_context_digest_unchanged=same["operator_context"],
                split_digest_unchanged=same["split_context"], readout_digest_changed=not same["readout"],
                leaky_control_digest_changed=leak_moves,
                verdict=("PASS" if changed > 0 and same["model"] and same["operator_context"]
                         and same["split_context"] and not same["readout"] and leak_moves else "FAIL"),
                reading=("the probe passes the adapter and refuses the leaky control: changing only hidden "
                         "values moves the readout and the leaky view, never the model view or the context"))


def main() -> None:
    import v77_qualification_bridge as BR
    import v77_address_universe as AU
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds-dir", required=True)
    ap.add_argument("--arms", default="NULL,BIO,TWIN_EXACT,TWIN_OPERATOR")
    ap.add_argument("--universe", required=True)
    ap.add_argument("--interface-worktree", required=True)
    ap.add_argument("--rehearsal-cells", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    git = lambda *x: subprocess.run(["git", *x], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    mine = ("scripts/v77/build_v77_runtime_handoff.py", "scripts/v77/v77_qualification_bridge.py",
            "scripts/v77/v77_synthetic_batch_adapter.py", "scripts/v77/v77_address_universe.py")
    if git("status", "--porcelain", "--untracked-files=no") or not all(git("ls-files", "--", f) for f in mine):
        sys.exit("refusing: the handoff must describe committed code")
    Q, iface = BR.load_interface(Path(a.interface_worktree))
    universe = np.load(a.universe, allow_pickle=False)["evaluation_universe"]
    uni = AU.AddressUniverse(7302)
    head = git("rev-parse", "HEAD")
    arms = {}
    for arm in a.arms.split(","):
        world = Path(a.worlds_dir) / arm
        full = AD.build_from_world(world, OBS_DIR, universe, HIDDEN_FRACTION, ADAPTER_SEED)
        conv = AD.build_from_world(world, OBS_DIR, universe, HIDDEN_FRACTION, ADAPTER_SEED, max_cells=a.rehearsal_cells)
        tm = world / "hidden_truth" / "TRUTH_MANIFEST.json"
        realization = f"V77_SEED7302_{hashlib.sha256(tm.read_bytes()).hexdigest()[:16]}"
        batch = BR.build_qualification_batch(
            Q, conv, world=world, obs_dir=OBS_DIR, universe=universe, address_ids=uni.address_id,
            registry_check=True, experiment_run_id=f"v77-s157-handoff-{arm.lower()}-{head[:12]}",
            realization_id=realization, code_commit=head, environment_digest=BR.environment_digest())
        protocol, out, seen = BR.run_plumbing_qualification(Q, batch)
        arms[arm] = dict(
            full_world=dict(n_cells=int(len(full.global_cell_index)),
                            adapter_digests={n: getattr(full, n).digest()
                                             for n in ("model", "operator_context", "split_context", "readout")}),
            rehearsal_batch=dict(
                n_cells=len(batch.scientific_identity.observation_ids),
                n_features=len(batch.feature_identity_receipt.tensor_feature_axis_ids),
                adapter_model_digest=conv.model.digest(),
                feature_identity_digest=batch.feature_identity_receipt.digest(),
                operator_identity_digest=batch.operator_identity_receipt.digest(),
                measurement_support_digest=batch.measurement_support_receipt.digest(),
                batch_scientific_identity_digest=batch.scientific_identity.digest(),
                synthetic_realization_id=batch.synthetic_realization_id,
                challenge_partition=batch.challenge_partition,
                field_visibility={f.declaration.name: f.declaration.visibility.value for f in batch.fields}),
            zero_update_plumbing=dict(output_digest=out.output_digest,
                                      provenance_receipt_digest=out.provenance_receipt_digest,
                                      mutation_proof_status=out.mutation_proof_status.value,
                                      q_safety_execution_proof_status=out.q_safety_execution_proof_status.value,
                                      seen_by_representation_function=seen),
            hidden_value_invariance=hidden_value_invariance(world, universe, max_cells=a.rehearsal_cells))
        print(arm, arms[arm]["hidden_value_invariance"]["verdict"], flush=True)
    rec = dict(head=head, interface=iface, arms=arms,
               executor_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in mine},
               command=" ".join(["python", "scripts/v77/build_v77_runtime_handoff.py", *sys.argv[1:]]))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, indent=1) + "\n")


if __name__ == "__main__":
    main()
