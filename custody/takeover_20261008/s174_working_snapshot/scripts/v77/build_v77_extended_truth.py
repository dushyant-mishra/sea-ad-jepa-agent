#!/usr/bin/env python3
"""V77 extended master truth: World A's truth plus isolable biological regimes.

This is a NEW generator. World A's generators are frozen by
`results/v77/V77_WORLD_A_BEHAVIOURAL_LOCK_V1.json` and are imported read-only here;
nothing in scripts/v64 or scripts/v75 is modified or re-parameterised.

The World A base (z_global, z_query, z_reg_shared, z_reg_private, technical_latents)
is reproduced by calling World A's own `latent_block` with World A's own streams, so an
extended world with no components enabled has a base identical to World A.

Every extension component draws from its own disjoint stream block at 2000+ and carries an
independent switch, so any single regime can be instantiated alone. Isolation is a property
of the component, not of the world.

Truth firewall: this writes only under `hidden_truth/`. Loadings, gene modules and the
observation operator live in the observer, never here.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v64"))
import build_v73_sharded_master_truth as T       # World A truth primitives (frozen)
import v73_full104_population_geometry as G      # World A population geometry (frozen)

# ---------------------------------------------------------------- stream registry
# World A occupies 10-13, 20-21, 30-32, 40-41, 50-52. Extensions start at 2000.
S_STATE      = 2000
S_DONOR      = 2100
S_RARE       = 2200
S_PTIME      = 2300
S_MARKER     = 2400
S_PARTIAL    = 2500
S_CSTATE     = 2600
S_GAIN       = 2700
S_BIOQC      = 2800
S_TF         = 2900
S_ATACPRIV   = 3000
S_SPATIAL    = 3200
S_PERT       = 3300

N_STATES       = 6
N_DONOR_DIMS   = 3
RARE_PREVALENCE = (0.05, 0.01, 0.002, 0.0005)
RARE_RECOVERABLE = (True, True, False, False)   # designed class, enforced by the observer
N_MARKER_DIMS  = 2
N_PARTIAL      = 5
N_TF           = 4

COMPONENTS = {
  # id : (world, truth arrays it adds, one-line description)
  "B1": ("B", ["state_index"],            "cell-state mixture, K=6"),
  "B2": ("B", ["z_donor"],                "donor-level biology, drawn per donor"),
  "B3": ("B", ["rare_flags"],             "four rare states, two recoverable by design"),
  "B4": ("B", ["pseudotime"],             "transient state on a pseudotime band"),
  "B5": ("B", ["z_marker"],               "sparse marker programs"),
  "B6": ("B", ["z_partial"],              "graded partially-recoverable continuum"),
  "C1": ("C", ["c_state_a", "c_state_b"], "nonlinear interaction, A x B activates a third module"),
  "C2": ("C", ["z_gain"],                 "query-local multiplicative gain on one module"),
  "C3": ("C", ["z_bioqc"],                "biology x operator: state drives measurement quality"),
  "D1": ("D", ["z_tf"],                   "directed regulator activities"),
  "D2": ("D", ["z_atac_bio", "z_atac_tech"], "distinguishable ATAC-private bio vs technical"),
  "D3": ("D", [],                         "SCENIC+-like TF->enhancer->gene graph with known negatives"),
  "E1": ("E", ["spatial_x", "spatial_y", "compartment", "niche_score"],
                                          "spatial position, compartment and a smooth niche field"),
  "E2": ("E", ["pert_id", "pert_dose"],   "dosed perturbations: TF targets with cascade, direct target, and a null arm"),
}
WORLD_PRESETS = {
  "A_REPLICA": [],
  "B": ["B1", "B2", "B3", "B4", "B5", "B6"],
  "C": ["C1", "C2", "C3"],
  "D": ["D1", "D2", "D3"],
  "E": ["E1", "E2", "D1", "D3"],   # perturbation cascade needs the regulatory graph to flow through
  "FULL": ["B1", "B2", "B3", "B4", "B5", "B6", "C1", "C2", "C3",
           "D1", "D2", "D3", "E1", "E2"],
}

# E2 perturbation catalog. Arm 0 is control. Arm 4 is a NULL perturbation: it is assigned
# and dosed exactly like a real arm but has no effect, which is the false-positive control.
PERTURBATIONS = [
  dict(pert_id=0, name="control",        kind="none",        target_tf=-1, effect=0.0),
  dict(pert_id=1, name="TF0_activate",   kind="tf_cascade",  target_tf=0,  effect=+1.6),
  dict(pert_id=2, name="TF2_repress",    kind="tf_cascade",  target_tf=2,  effect=-1.6),
  dict(pert_id=3, name="direct_module",  kind="direct_genes", target_tf=-1, effect=+1.1),
  dict(pert_id=4, name="NULL_arm",       kind="null",        target_tf=-1, effect=0.0),
]
PERT_ASSIGN_FRACTION = 0.50      # half of cells receive some arm, half stay control
DOSE_RANGE = (0.25, 1.50)


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _components(ids_u, donor, seed, enabled):
    """Each component is a pure function of (seed, identity, its own stream)."""
    out = {}
    if "B1" in enabled:
        u = T.u01(seed + S_STATE, ids_u, S_STATE)
        out["state_index"] = np.minimum((u * N_STATES).astype(np.int8), N_STATES - 1)
    if "B2" in enabled:
        # keyed by DONOR, never by operator, so donor biology is separable from batch
        d = np.asarray(donor, dtype=np.uint64)
        out["z_donor"] = np.stack(
            [T.normal(seed + S_DONOR, d, S_DONOR + j) for j in range(N_DONOR_DIMS)],
            axis=1).astype(np.float32)
    if "B3" in enabled:
        flags = np.zeros((len(ids_u), len(RARE_PREVALENCE)), dtype=np.uint8)
        for j, p in enumerate(RARE_PREVALENCE):
            flags[:, j] = (T.u01(seed + S_RARE, ids_u, S_RARE + j) < p).astype(np.uint8)
        out["rare_flags"] = flags
    if "B4" in enabled:
        out["pseudotime"] = T.u01(seed + S_PTIME, ids_u, S_PTIME).astype(np.float32)
    if "B5" in enabled:
        out["z_marker"] = T.latent_block(seed + S_MARKER, ids_u, S_MARKER, N_MARKER_DIMS)
    if "B6" in enabled:
        out["z_partial"] = T.latent_block(seed + S_PARTIAL, ids_u, S_PARTIAL, N_PARTIAL)
    if "C1" in enabled:
        out["c_state_a"] = (T.u01(seed + S_CSTATE, ids_u, S_CSTATE) < 0.50).astype(np.uint8)
        out["c_state_b"] = (T.u01(seed + S_CSTATE, ids_u, S_CSTATE + 1) < 0.50).astype(np.uint8)
    if "C2" in enabled:
        out["z_gain"] = T.normal(seed + S_GAIN, ids_u, S_GAIN).astype(np.float32)
    if "C3" in enabled:
        out["z_bioqc"] = T.normal(seed + S_BIOQC, ids_u, S_BIOQC).astype(np.float32)
    if "D1" in enabled:
        out["z_tf"] = T.latent_block(seed + S_TF, ids_u, S_TF, N_TF)
    if "D2" in enabled:
        out["z_atac_bio"] = T.normal(seed + S_ATACPRIV, ids_u, S_ATACPRIV).astype(np.float32)
        out["z_atac_tech"] = T.normal(seed + S_ATACPRIV, ids_u, S_ATACPRIV + 1).astype(np.float32)
    if "E1" in enabled:
        # Position is per cell; the niche field is a smooth function of position with
        # donor-specific hashed coefficients, so it is spatially autocorrelated AND
        # shard-invariant. No neighbour lookup is needed, so niche never depends on how the
        # cells happen to be partitioned into shards.
        x = T.u01(seed + S_SPATIAL, ids_u, S_SPATIAL).astype(np.float32)
        y = T.u01(seed + S_SPATIAL, ids_u, S_SPATIAL + 1).astype(np.float32)
        out["spatial_x"], out["spatial_y"] = x, y
        d = np.asarray(donor, dtype=np.uint64)
        niche = np.zeros(len(ids_u), dtype=np.float64)
        for m in range(3):                      # three Fourier modes per donor
            kx = 1.0 + 3.0 * T.u01(seed + S_SPATIAL + 10, d, S_SPATIAL + 10 + m)
            ky = 1.0 + 3.0 * T.u01(seed + S_SPATIAL + 20, d, S_SPATIAL + 20 + m)
            ph = 2 * np.pi * T.u01(seed + S_SPATIAL + 30, d, S_SPATIAL + 30 + m)
            amp = 1.0 / (m + 1.0)
            niche += amp * np.sin(2 * np.pi * (kx * x + ky * y) + ph)
        niche = (niche - niche.mean()) / (niche.std() + 1e-9)
        out["niche_score"] = niche.astype(np.float32)
        # compartments are contiguous in space: they are a threshold of the same smooth field
        out["compartment"] = np.digitize(niche, [-0.6, 0.0, 0.6]).astype(np.int8)
    if "E2" in enabled:
        u_assign = T.u01(seed + S_PERT, ids_u, S_PERT)
        n_arms = len(PERTURBATIONS) - 1                      # arms 1..4
        arm = np.where(u_assign < PERT_ASSIGN_FRACTION,
                       1 + (T.u01(seed + S_PERT, ids_u, S_PERT + 1) * n_arms).astype(np.int64),
                       0)
        arm = np.clip(arm, 0, n_arms)
        lo, hi = DOSE_RANGE
        dose = (lo + (hi - lo) * T.u01(seed + S_PERT, ids_u, S_PERT + 2)).astype(np.float32)
        dose = np.where(arm == 0, 0.0, dose).astype(np.float32)
        out["pert_id"] = arm.astype(np.int8)
        out["pert_dose"] = dose
    return out


def build(root: Path, n_cells: int, shard_size: int, seed: int, enabled: list[str]) -> dict:
    if n_cells <= 0:
        raise ValueError("n_cells must be positive")
    unknown = [c for c in enabled if c not in COMPONENTS]
    if unknown:
        raise ValueError("unknown components: " + ",".join(unknown))
    truth = root / "hidden_truth"
    truth.mkdir(parents=True, exist_ok=True)
    authority, trip, quotas = G.quotas_for_n(n_cells)
    pop = G.summary_from_quotas(authority, trip, quotas)
    shards = []
    realised_sources = np.zeros(3, dtype=np.int64)
    for start in range(0, n_cells, shard_size):
        stop = min(start + shard_size, n_cells)
        ids = np.arange(start, stop, dtype=np.uint64)
        donor, operator, source_ix, _, _, _ = G.assignments_for_ids(
            ids.astype(np.int64), n_cells, seed)
        realised_sources += np.bincount(source_ix, minlength=3)
        payload = dict(
            global_cell_index=ids.astype(np.int64),
            cell_id=np.array([f"MASTER_{int(i):09d}" for i in ids]),
            donor_index=donor, source_index=source_ix, operator_index=operator,
            # --- World A base, reproduced with World A's own streams ---
            z_global=T.latent_block(seed, ids, 10, 4),
            z_query=T.latent_block(seed, ids, 20, 2),
            z_reg_shared=T.latent_block(seed, ids, 30, 3),
            z_reg_private=T.latent_block(seed, ids, 40, 2),
            technical_latents=T.latent_block(seed, ids, 50, 3),
        )
        payload.update(_components(ids, donor, seed, enabled))
        path = truth / f"TRUTH_{start:09d}_{stop:09d}.npz"
        np.savez(path, **payload)
        shards.append(dict(start=start, stop=stop, cells=stop - start,
                           file=path.name, sha256=sha256_file(path)))
    # The regulatory graph is ground truth, so it is serialised beside the shards whenever any
    # component that uses it is enabled. Observers import the same builder, never a copy.
    graph_file = None
    if {"D1", "D3", "E2"} & set(enabled):
        import v77_regulatory_graph as RG
        graph = RG.build_graph(seed)
        gp = truth / "REGULATORY_GRAPH_TRUTH.json"
        gp.write_text(json.dumps(graph, indent=2) + "\n")
        graph_file = dict(file=gp.name, sha256=sha256_file(gp),
                          n_known_positive_region_gene_pairs=len(graph["known_positive_region_gene_pairs"]),
                          n_decoy_regions=len(graph["decoy_regions"]),
                          n_never_targeted_panel_genes=len(graph["never_targeted_panel_genes"]))

    manifest = dict(
        schema="V77_EXTENDED_MASTER_TRUTH_MANIFEST_V1",
        seed=seed, n_cells=n_cells, shard_size_requested=shard_size,
        shard_size_is_non_scientific=True,
        n_donors=authority["n_donors"], n_operators=authority["n_operators"],
        source_names=list(T.SOURCE_NAMES),
        source_counts=dict(zip(T.SOURCE_NAMES, realised_sources.tolist())),
        world_a_base_streams_preserved=True,
        world_a_base_blocks=dict(z_global=4, z_query=2, z_reg_shared=3,
                                 z_reg_private=2, technical_latents=3),
        enabled_components=list(enabled),
        component_catalog={k: dict(world=v[0], arrays=v[1], description=v[2])
                           for k, v in COMPONENTS.items()},
        extension_stream_base=2000,
        rare_prevalence=list(RARE_PREVALENCE),
        rare_designed_recoverable=list(RARE_RECOVERABLE),
        n_states=N_STATES, n_partial_rungs=N_PARTIAL, n_tf=N_TF,
        regulatory_graph_truth=graph_file,
        perturbation_catalog=(PERTURBATIONS if "E2" in enabled else None),
        perturbation_assignment_fraction=(PERT_ASSIGN_FRACTION if "E2" in enabled else None),
        perturbation_dose_range=(list(DOSE_RANGE) if "E2" in enabled else None),
        perturbation_null_arm_exists=("E2" in enabled),
        donor_ids=authority["donor_ids"], operator_ids=authority["operator_ids"],
        operator_sources=authority["operator_sources"],
        randomization="stateless SplitMix64 keyed by (seed, identity, stream); "
                      "extension streams are disjoint from World A's",
        population_summary=pop, shards=shards,
        truth_firewall="hidden_truth only; observable manifests must never reference this path")
    (truth / "TRUTH_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--cells", type=int, required=True)
    ap.add_argument("--shard-size", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=7302)
    ap.add_argument("--world", choices=sorted(WORLD_PRESETS), default=None,
                    help="preset component set")
    ap.add_argument("--components", default=None,
                    help="explicit comma-separated component ids, for single-regime isolation")
    a = ap.parse_args()
    if (a.world is None) == (a.components is None):
        raise SystemExit("give exactly one of --world or --components")
    enabled = WORLD_PRESETS[a.world] if a.world else [c.strip() for c in a.components.split(",") if c.strip()]
    m = build(Path(a.root), a.cells, a.shard_size, a.seed, enabled)
    print(json.dumps(dict(status="PASS", cells=m["n_cells"], shards=len(m["shards"]),
                          enabled_components=m["enabled_components"],
                          source_counts=m["source_counts"]), indent=2))


if __name__ == "__main__":
    main()
