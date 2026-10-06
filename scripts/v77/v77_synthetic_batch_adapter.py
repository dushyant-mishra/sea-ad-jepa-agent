#!/usr/bin/env python3
"""Synthetic world -> model-facing batch, with oracle truth PHYSICALLY separated.

RUNTIME-AGNOSTIC BY DESIGN. This does not import, subclass or name any historical loader
class. It emits a neutral structure described in terms of the tensors and metadata a V5-style
consumer needs. When the runtime lane freezes the canonical consumer interface, the join is a
thin bridge, not a rewrite. There is no trainer here, no optimizer step, no EMA and no
checkpoint loop; those belong to the runtime lane and must have exactly one implementation.

THE SEPARATION IS STRUCTURAL, NOT DOCUMENTARY. Two distinct frozen types:

    SyntheticModelBatch    everything a model may lawfully see
    SyntheticOracleRecord  planted truth, usable ONLY after prediction, for scoring

They are separate objects with no reference from the batch to the oracle. A model-facing
function cannot receive z_reg_private by accident, because the batch has no field that could
carry it and no handle on the record that does. ORACLE_ONLY_FIELDS below is the enforced
list, and the test suite asserts the two namespaces never intersect. Every truth field must
be declared oracle-only or permitted; an undeclared field stops the conversion.

WHY THIS MATTERS HERE SPECIFICALLY. The B3 non-recoverable arms and z_reg_private are
provably absent from permitted RNA evidence. If they leaked into model-visible fields through
ordinary plumbing, the anti-cheat rehearsal would report a cheat that the harness itself
created. The separation is the instrument, so it has to be sound before any forward pass.

MEASUREMENT SEMANTICS. Three states must survive conversion and never be collapsed:

    measured, detected         measurement_mask True,  count > 0
    measured zero              measurement_mask True,  count == 0   evidence of absence
    structurally unmeasured    measurement_mask False               no evidence at all

The mask is read from the world, per element (support_mask_packed in each observer shard).
It is never reconstructed from registry coverage, because structural support also depends on
operator-level attrition, and a reconstruction can silently diverge from what the world used
(defects S128, S134, S146, S147). A world that does not carry per-element support is refused.
A detected count on an address outside support means the world violates measurement physics,
and that is refused too, never relabelled as measured.

Hidden targets are drawn within structural support, measured zeros included, with each cell's
draw seeded by its own global_cell_index. Eligibility therefore depends only on declared
support and identity, never on the realized value (S132) or on storage order (S133).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse

# Planted variables that may NEVER appear in a model-facing structure. Enforced by tests.
ORACLE_ONLY_FIELDS = frozenset({
    "z_global", "z_query", "z_reg_shared", "z_reg_private", "technical_latents",
    "z_donor", "z_marker", "z_partial", "z_gain", "z_bioqc", "z_tf",
    "z_atac_bio", "z_atac_tech", "rare_flags", "state_index", "substate",
    "c_state_a", "c_state_b", "pseudotime", "niche_score", "compartment",
    "pert_id", "pert_dose", "spatial_x", "spatial_y",
    "donor_index",      # identity of the donor: for scoring splits, never a model input
})

# Lawful physical descriptors a model or diagnostic may see.
PERMITTED_METADATA = frozenset({
    "operator_index", "source_index", "library_size", "n_measured",
    "global_cell_index",
})

# Truth-file keys used only to align cells with the observer; copied into neither structure.
ALIGNMENT_ONLY_FIELDS = frozenset({"cell_id"})

# Truth keys that must be present; the adapter will not default them.
REQUIRED_TRUTH_FIELDS = ("global_cell_index", "operator_index", "source_index")

PACKED_SUPPORT_KEY = "support_mask_packed"


class AdapterContractError(RuntimeError):
    """The world cannot be converted without guessing, so the adapter refuses instead."""


@dataclass(frozen=True)
class SyntheticModelBatch:
    """Model-visible only. Adding an oracle field here is a test failure, by construction."""
    gene_ids: np.ndarray            # [cells, genes] int64, canonical registry indices
    expression: np.ndarray          # [cells, genes] float32, CPM-log1p of observed counts
    measurement_mask: np.ndarray    # [cells, genes] bool, address structurally measurable
    hidden_target_mask: np.ndarray  # [cells, genes] bool, hidden from the student view
    operator_index: np.ndarray      # [cells] int16
    source_index: np.ndarray        # [cells] int8
    library_size: np.ndarray        # [cells] float32, total counts over ALL addresses
    n_measured: np.ndarray          # [cells] int32, measurable addresses in the universe,
                                    #   measured zeros included (V5 measured_count semantics)
    global_cell_index: np.ndarray   # [cells] int64, synthetic cell identity

    def digest(self) -> str:
        h = hashlib.sha256()
        for f in sorted(fields(self), key=lambda x: x.name):
            a = np.ascontiguousarray(getattr(self, f.name))
            h.update(f.name.encode()); h.update(str(a.dtype).encode())
            h.update(str(a.shape).encode()); h.update(a.tobytes())
        return h.hexdigest()

    def student_visible_expression(self) -> np.ndarray:
        """Expression the STUDENT may use: measured AND not hidden.

        Hidden targets are zeroed here rather than merely flagged, so a consumer that ignores
        the mask still cannot read them. A zero in this view is ambiguous on its own; the
        masks say which of the three states it is.
        """
        allow = self.measurement_mask & ~self.hidden_target_mask
        return np.where(allow, self.expression, 0.0).astype(np.float32)


@dataclass(frozen=True)
class SyntheticOracleRecord:
    """Planted truth. For scoring AFTER prediction. Never passed to a model-facing function."""
    global_cell_index: np.ndarray
    latents: dict[str, np.ndarray]      # every ORACLE_ONLY field present in the world
    b3_arm_membership: np.ndarray | None
    b6_ladder_level: np.ndarray | None
    substate: np.ndarray | None
    annotated_class: np.ndarray | None

    def digest(self) -> str:
        h = hashlib.sha256()
        h.update(np.ascontiguousarray(self.global_cell_index).tobytes())
        for k in sorted(self.latents):
            a = np.ascontiguousarray(self.latents[k])
            h.update(k.encode()); h.update(a.tobytes())
        return h.hexdigest()


def _cpm_log1p(counts: np.ndarray, library: np.ndarray) -> np.ndarray:
    lib = np.where(library > 0, library, 1.0)[:, None]
    return np.log1p(counts / lib * 1e4).astype(np.float32)


def sample_hidden_targets(measurement_mask: np.ndarray, global_cell_index: np.ndarray,
                          hidden_fraction: float, seed: int) -> np.ndarray:
    """Hidden-target mask drawn within STRUCTURAL support, measured zeros included.

    A cell's draw is seeded by (seed, its global_cell_index), so its mask does not depend on
    which other cells are converted alongside it or in what order.
    """
    mm = np.asarray(measurement_mask, dtype=bool)
    gci = np.asarray(global_cell_index, dtype=np.int64)
    if mm.ndim != 2 or mm.shape[0] != len(gci):
        raise AdapterContractError("measurement_mask rows and global_cell_index disagree")
    if not 0.0 <= float(hidden_fraction) < 1.0:
        raise AdapterContractError(f"hidden_fraction {hidden_fraction} outside [0, 1)")
    if len(gci) and gci.min() < 0:
        raise AdapterContractError("negative global_cell_index cannot seed a per-cell draw")
    hidden = np.zeros_like(mm)
    for i in range(mm.shape[0]):
        elig = np.flatnonzero(mm[i])
        k = int(round(float(hidden_fraction) * len(elig)))
        if k <= 0:
            continue
        rng = np.random.default_rng([int(seed), int(gci[i])])
        hidden[i, rng.choice(elig, size=k, replace=False)] = True
    return hidden


def _read_truth(root: Path) -> dict[str, np.ndarray]:
    files = sorted((root / "hidden_truth").glob("TRUTH_*.npz"))
    if not files:
        raise AdapterContractError(f"no truth shards under {root / 'hidden_truth'}")
    parts: dict[str, list[np.ndarray]] = {}
    for f in files:
        z = np.load(f, allow_pickle=False)
        for k in z.files:
            parts.setdefault(k, []).append(z[k])
    declared = ORACLE_ONLY_FIELDS | PERMITTED_METADATA | ALIGNMENT_ONLY_FIELDS
    undeclared = sorted(set(parts) - declared)
    if undeclared:
        raise AdapterContractError(
            f"undeclared truth fields {undeclared}: every planted field must be declared "
            "oracle-only or permitted before any conversion")
    missing = [k for k in REQUIRED_TRUTH_FIELDS if k not in parts]
    if missing:
        raise AdapterContractError(f"truth lacks required fields {missing}; refusing to default them")
    truth = {k: np.concatenate(v, 0) for k, v in parts.items()}
    n = len(truth["global_cell_index"])
    ragged = sorted(k for k, v in truth.items() if len(v) != n)
    if ragged:
        raise AdapterContractError(f"truth fields with a different cell count: {ragged}")
    return truth


def _validate_universe(universe: np.ndarray, n_addr: int) -> np.ndarray:
    u = np.asarray(universe)
    if u.ndim != 1 or len(u) == 0 or not np.issubdtype(u.dtype, np.integer):
        raise AdapterContractError("universe must be a non-empty 1-D integer index array")
    u = u.astype(np.int64)
    if u.min() < 0 or u.max() >= n_addr:
        raise AdapterContractError(f"universe indices outside [0, {n_addr})")
    if len(np.unique(u)) != len(u):
        raise AdapterContractError("universe contains duplicate addresses")
    return u


def build_from_world(root: Path, obs_dir: str, universe: np.ndarray,
                     hidden_fraction: float = 0.15, seed: int = 20261006,
                     max_cells: int | None = None
                     ) -> tuple[SyntheticModelBatch, SyntheticOracleRecord, dict[str, Any]]:
    """Read a generated synthetic world and emit (model batch, oracle record, provenance)."""
    root = Path(root)
    odir = root / "observable_raw" / obs_dir
    manifests = sorted(odir.glob("*MANIFEST*.json"))
    if len(manifests) != 1:
        raise AdapterContractError(
            f"expected exactly one observer manifest in {odir}, found {len(manifests)}")
    man = json.loads(manifests[0].read_text())
    n_addr = int(man["n_addresses"])
    universe = _validate_universe(universe, n_addr)
    truth = _read_truth(root)
    t_gci = np.asarray(truth["global_cell_index"], dtype=np.int64)

    cnt_parts, sup_parts, lib_parts, cell_parts = [], [], [], []
    off, n_shards_read = 0, 0
    for s in man["shards"]:
        if max_cells is not None and off >= max_cells:
            break
        z = np.load(odir / s["file"], allow_pickle=False)
        n = len(z["indptr"]) - 1
        X = sparse.csr_matrix((z["data"].astype(np.float64), z["indices"], z["indptr"]),
                              shape=(n, n_addr))
        gci = np.asarray(z["global_cell_index"], dtype=np.int64)
        if len(gci) != n:
            raise AdapterContractError(f"{s['file']}: {len(gci)} cell ids for {n} rows")
        if off + n > len(t_gci) or not np.array_equal(t_gci[off:off + n], gci):
            raise AdapterContractError(
                f"{s['file']}: observer cells are not aligned with truth cells at offset {off}; "
                "refusing to attach latents to the wrong cells")
        if (X.data < 0).any():
            raise AdapterContractError(f"{s['file']}: negative counts")
        if PACKED_SUPPORT_KEY not in z.files:
            raise AdapterContractError(
                f"{s['file']}: no per-element structural support ({PACKED_SUPPORT_KEY}). The "
                "adapter will not guess which zeros were measurable. Worlds observed before the "
                "S146/S147 repair carry swapped and double-counted support and must be rebuilt.")
        sup = np.unpackbits(np.asarray(z[PACKED_SUPPORT_KEY], dtype=np.uint8), axis=1,
                            count=n_addr).astype(bool)
        if sup.shape != (n, n_addr):
            raise AdapterContractError(f"{s['file']}: support shape {sup.shape} != {(n, n_addr)}")
        if "support_count" in z.files and not np.array_equal(
                sup.sum(1), np.asarray(z["support_count"], dtype=np.int64)):
            raise AdapterContractError(f"{s['file']}: support mask disagrees with support_count")
        rows = np.repeat(np.arange(n), np.diff(X.indptr))
        outside = (X.data > 0) & ~sup[rows, X.indices]
        if outside.any():
            raise AdapterContractError(
                f"{s['file']}: {int(outside.sum())} detected counts on structurally unsupported "
                "addresses; the world violates measurement physics")
        cnt_parts.append(np.asarray(X[:, universe].todense(), dtype=np.float32))
        sup_parts.append(sup[:, universe])
        lib_parts.append(np.asarray(X.sum(1)).ravel().astype(np.float32))
        cell_parts.append(gci)
        off += n
        n_shards_read += 1
    if not cell_parts:
        raise AdapterContractError("no observer cells read")

    counts = np.concatenate(cnt_parts)
    measurement_mask = np.concatenate(sup_parts)
    library = np.concatenate(lib_parts)
    cells = np.concatenate(cell_parts)
    if max_cells is not None:
        counts, measurement_mask = counts[:max_cells], measurement_mask[:max_cells]
        library, cells = library[:max_cells], cells[:max_cells]
    nc = len(cells)
    truth = {k: v[:nc] for k, v in truth.items()}

    detected = counts > 0
    hidden = sample_hidden_targets(measurement_mask, cells, hidden_fraction, seed)
    batch = SyntheticModelBatch(
        gene_ids=np.tile(universe, (nc, 1)),
        expression=_cpm_log1p(counts, library),
        measurement_mask=measurement_mask,
        hidden_target_mask=hidden,
        operator_index=truth["operator_index"].astype(np.int16),
        source_index=truth["source_index"].astype(np.int8),
        library_size=library,
        n_measured=measurement_mask.sum(1).astype(np.int32),
        global_cell_index=cells)

    oracle = SyntheticOracleRecord(
        global_cell_index=cells,
        latents={k: v for k, v in truth.items() if k in ORACLE_ONLY_FIELDS},
        b3_arm_membership=truth.get("rare_flags"),
        b6_ladder_level=truth.get("z_partial"),
        substate=truth.get("substate"),
        annotated_class=truth.get("state_index"))

    measured_zero = measurement_mask & ~detected
    prov = dict(
        schema="V77_SYNTHETIC_BATCH_ADAPTER_PROVENANCE_V2",
        claim_namespace="SYNTHETIC_PIPELINE_ANTICHEAT_REHEARSAL",
        world_root=str(root), observer_dir=obs_dir,
        observer_manifest_schema=man.get("schema"),
        observer_manifest_sha256=hashlib.sha256(manifests[0].read_bytes()).hexdigest(),
        structural_support_rule=man.get("structural_support_rule"),
        support_source="per-element support_mask_packed read from every observer shard",
        n_cells=int(nc), n_shards_read=int(n_shards_read),
        n_genes_in_universe=int(len(universe)),
        hidden_fraction=hidden_fraction, seed=seed,
        three_state_counts=dict(
            measured_detected=int(detected.sum()),
            measured_zero=int(measured_zero.sum()),
            structurally_unmeasured=int((~measurement_mask).sum())),
        hidden_targets=dict(
            total=int(hidden.sum()),
            on_measured_zero=int((hidden & measured_zero).sum()),
            on_detected=int((hidden & detected).sum()),
            on_unmeasured=int((hidden & ~measurement_mask).sum())),
        batch_digest=batch.digest(), oracle_digest=oracle.digest(),
        oracle_only_fields=sorted(ORACLE_ONLY_FIELDS),
        permitted_metadata=sorted(PERMITTED_METADATA),
        truth_fields_routed_to_oracle=sorted(oracle.latents),
        separation=("SyntheticModelBatch holds no reference to SyntheticOracleRecord; the "
                    "namespaces are asserted disjoint by test"),
        runtime_binding="NONE; this adapter names no runtime loader class",
        no_training_performed=True)
    return batch, oracle, prov


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert a synthetic world; write provenance only.")
    ap.add_argument("--world", required=True)
    ap.add_argument("--observer-dir", required=True)
    ap.add_argument("--universe", required=True, help="npz holding 'evaluation_universe'")
    ap.add_argument("--hidden-fraction", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--max-cells", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    here = Path(__file__).resolve().parent

    def git(*args):
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=here).stdout.strip()

    dirty = git("status", "--porcelain", "--untracked-files=no")
    if dirty or not git("ls-files", "--", Path(__file__).name):
        sys.exit("refusing: an integration receipt must describe committed code\n" + dirty)
    adapter_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    upath = Path(a.universe)
    universe = np.load(upath, allow_pickle=False)["evaluation_universe"]
    _, _, prov = build_from_world(Path(a.world), a.observer_dir, universe,
                                  a.hidden_fraction, a.seed, a.max_cells)
    prov["universe_file"] = dict(path=str(upath),
                                 sha256=hashlib.sha256(upath.read_bytes()).hexdigest())
    prov.update(source_commit=git("rev-parse", "HEAD"), adapter_sha256=adapter_sha256,
                provenance_status="CLEAN_COMMITTED_HEAD__ADAPTER_TRACKED",
                command=" ".join(["python", "scripts/v77/v77_synthetic_batch_adapter.py", *sys.argv[1:]]))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(prov, indent=2) + "\n")
    print(json.dumps(dict(three_state_counts=prov["three_state_counts"],
                          hidden_targets=prov["hidden_targets"],
                          batch_digest=prov["batch_digest"][:16]), indent=1))


if __name__ == "__main__":
    main()
