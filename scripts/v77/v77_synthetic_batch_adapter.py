#!/usr/bin/env python3
"""Synthetic world -> model-facing structures, with every visibility class PHYSICALLY separated.

RUNTIME-AGNOSTIC BY DESIGN. This does not import, subclass or name any historical loader
class, and it contains no trainer, optimizer step, EMA or checkpoint loop; those belong to the
runtime lane and must have exactly one implementation. It emits neutral structures that map
one-to-one onto the visibility classes of the shared qualification interface (PR #223).

FIVE STRUCTURES, ONE PER VISIBILITY CLASS, so a consumer cannot read across a class by accident:

    SyntheticModelBatch        MODEL_VISIBLE            gene ids, student evidence, measurement
                                                         mask, hidden-target (query) positions
    SyntheticOperatorContext   LAWFUL_OPERATOR_CONTEXT  source, operator, q-safe depth, measurable count
    SyntheticSplitContext      SPLIT_ONLY               donor
    SyntheticReadoutRecord     READOUT_ONLY             counts at the hidden targets, full library
    SyntheticOracleRecord      ORACLE_ONLY              planted truth, for scoring after prediction

No hidden value can be represented on the model side. The student evidence is built with hidden
entries removed, and every denominator and depth summary on the model-facing side is computed
from visible counts only: an earlier version normalised by a library that included the hidden
counts, so the visible values' shortfall revealed how much expression was hidden (S167), and it
carried the full expression on the model batch behind a zeroing method (S168). Source, operator
and depth are operator context, not model inputs (S162), and they are read from the observer's
own shards and authenticated by name against its rosters, never taken from hidden truth (S161).

MEASUREMENT SEMANTICS. Three states survive conversion and are never collapsed:

    measured, detected         measurement_mask True,  count > 0
    measured zero              measurement_mask True,  count == 0   evidence of absence
    structurally unmeasured    measurement_mask False               no evidence at all

The mask is read per element from the producer (support_mask_packed); a world without it is
refused, and a detected count outside support is refused, never relabelled (S128, S134, S146,
S147). Hidden targets are drawn within structural support, measured zeros included, each cell
seeded by its own global_cell_index, so eligibility depends only on support and identity, never
on the realized value (S132) or on storage order (S133).
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
})

# Facts of the measurement design. Read from the PRODUCER; a truth copy, when present, must agree.
OBSERVATION_DESIGN_FIELDS = ("source_index", "operator_index", "donor_index")

# Truth-file keys used only to align cells with the observer; copied into no structure.
ALIGNMENT_ONLY_FIELDS = frozenset({"global_cell_index", "cell_id"})

PACKED_SUPPORT_KEY = "support_mask_packed"


class AdapterContractError(RuntimeError):
    """The world cannot be converted without guessing, so the adapter refuses instead."""


def _digest_arrays(obj) -> str:
    h = hashlib.sha256()
    for f in sorted(fields(obj), key=lambda x: x.name):
        a = np.ascontiguousarray(getattr(obj, f.name))
        h.update(f.name.encode()); h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode()); h.update(a.tobytes())
    return h.hexdigest()


@dataclass(frozen=True)
class SyntheticModelBatch:
    """MODEL_VISIBLE only. No hidden value and no operator context can be represented here."""
    gene_ids: np.ndarray            # [cells, genes] int64, canonical registry indices
    student_expression: np.ndarray  # [cells, genes] float32, log1p(count / visible library * 1e4)
                                    #   on visible evidence, 0 elsewhere; the masks say which state
    measurement_mask: np.ndarray    # [cells, genes] bool, address structurally measurable
    hidden_target_mask: np.ndarray  # [cells, genes] bool, query positions, values held elsewhere

    def digest(self) -> str:
        return _digest_arrays(self)

    @property
    def evidence_mask(self) -> np.ndarray:
        return self.measurement_mask & ~self.hidden_target_mask


@dataclass(frozen=True)
class SyntheticOperatorContext:
    """LAWFUL_OPERATOR_CONTEXT. Computed without any hidden value."""
    source_index: np.ndarray          # [cells] int16, index into the producer's source_roster
    operator_index: np.ndarray        # [cells] int16, index into the producer's operator_ids
    visible_library_size: np.ndarray  # [cells] float32, total counts EXCLUDING hidden targets
    n_measured: np.ndarray            # [cells] int32, measurable addresses in the universe

    def digest(self) -> str:
        return _digest_arrays(self)


@dataclass(frozen=True)
class SyntheticSplitContext:
    """SPLIT_ONLY. Grouping for splits and inference units, never a model input."""
    donor_index: np.ndarray           # [cells] int32, index into the producer's donor_ids

    def digest(self) -> str:
        return _digest_arrays(self)


@dataclass(frozen=True)
class SyntheticReadoutRecord:
    """READOUT_ONLY. The hidden values themselves, for scoring a prediction, never an input."""
    query_counts: np.ndarray          # [cells, genes] float32, counts at hidden targets, 0 elsewhere
    full_library_size: np.ndarray     # [cells] float32, total counts INCLUDING hidden targets

    def digest(self) -> str:
        return _digest_arrays(self)


@dataclass(frozen=True)
class SyntheticOracleRecord:
    """ORACLE_ONLY. Planted truth, for scoring AFTER prediction."""
    global_cell_index: np.ndarray
    latents: dict[str, np.ndarray]
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


@dataclass(frozen=True)
class SyntheticConversion:
    model: SyntheticModelBatch
    operator_context: SyntheticOperatorContext
    split_context: SyntheticSplitContext
    readout: SyntheticReadoutRecord
    oracle: SyntheticOracleRecord
    global_cell_index: np.ndarray     # PROVENANCE_ONLY observation identity
    provenance: dict[str, Any]


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
    declared = ORACLE_ONLY_FIELDS | set(OBSERVATION_DESIGN_FIELDS) | ALIGNMENT_ONLY_FIELDS
    undeclared = sorted(set(parts) - declared)
    if undeclared:
        raise AdapterContractError(
            f"undeclared truth fields {undeclared}: every planted field must be declared "
            "oracle-only or a measurement-design fact before any conversion")
    if "global_cell_index" not in parts:
        raise AdapterContractError("truth lacks global_cell_index; refusing to align by position")
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


def _validate_observation_identity(oi: Any, src: np.ndarray, op: np.ndarray, don: np.ndarray) -> None:
    """Every positional index must resolve by NAME, and every operator must belong to the cell's
    declared source: the rule of the shared interface, and the check that would have caught S146."""
    if not isinstance(oi, dict):
        raise AdapterContractError("observer manifest has no observation_identity block")
    roster, ops = oi.get("source_roster"), oi.get("operator_ids")
    omap, donors = oi.get("operator_source_map"), oi.get("donor_ids")
    if not roster or not ops or not omap or donors is None:
        raise AdapterContractError("observation_identity lacks a roster, operator ids, map or donor ids")
    if len(set(roster)) != len(roster) or len(set(ops)) != len(ops):
        raise AdapterContractError("observation_identity rosters contain duplicates")
    mapping = {str(o): str(s) for o, s in omap}
    if set(mapping) != set(map(str, ops)) or not set(mapping.values()) <= set(roster):
        raise AdapterContractError("operator_source_map does not cover the operator roster within the source roster")
    if src.min() < 0 or src.max() >= len(roster) or op.min() < 0 or op.max() >= len(ops):
        raise AdapterContractError("a source or operator index lies outside its roster")
    if len(donors) and (don.min() < 0 or don.max() >= len(donors)):
        raise AdapterContractError("a donor index lies outside the donor roster")
    op_source = np.array([mapping[str(o)] for o in ops], dtype=object)[op]
    cell_source = np.array(roster, dtype=object)[src]
    bad = int((op_source != cell_source).sum())
    if bad:
        raise AdapterContractError(f"{bad} cells have an operator from a different source than the one they declare")


def build_from_world(root: Path, obs_dir: str, universe: np.ndarray,
                     hidden_fraction: float = 0.15, seed: int = 20261006,
                     max_cells: int | None = None) -> SyntheticConversion:
    """Read a generated synthetic world and emit one structure per visibility class."""
    root = Path(root)
    odir = root / "observable_raw" / obs_dir
    manifests = sorted(odir.glob("*MANIFEST*.json"))
    if len(manifests) != 1:
        raise AdapterContractError(
            f"expected exactly one observer manifest in {odir}, found {len(manifests)}")
    man_bytes = manifests[0].read_bytes()
    man = json.loads(man_bytes)
    n_addr = int(man["n_addresses"])
    universe = _validate_universe(universe, n_addr)
    truth = _read_truth(root)
    t_gci = np.asarray(truth["global_cell_index"], dtype=np.int64)

    parts: dict[str, list[np.ndarray]] = {k: [] for k in
                                          ("cnt", "sup", "lib", "gci", *OBSERVATION_DESIGN_FIELDS)}
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
        missing = [k for k in OBSERVATION_DESIGN_FIELDS if k not in z.files]
        if missing:
            raise AdapterContractError(
                f"{s['file']}: no producer-side {missing}. Observation identity must come from the "
                "observer, not from hidden truth; worlds observed before S161 must be re-observed.")
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
        parts["cnt"].append(np.asarray(X[:, universe].todense(), dtype=np.float64))
        parts["sup"].append(sup[:, universe])
        parts["lib"].append(np.asarray(X.sum(1)).ravel())
        parts["gci"].append(gci)
        for k in OBSERVATION_DESIGN_FIELDS:
            parts[k].append(np.asarray(z[k], dtype=np.int64))
        off += n
        n_shards_read += 1
    if not parts["gci"]:
        raise AdapterContractError("no observer cells read")

    cat = {k: np.concatenate(v) for k, v in parts.items()}
    if max_cells is not None:
        cat = {k: v[:max_cells] for k, v in cat.items()}
    counts, measurement_mask, full_library, cells = cat["cnt"], cat["sup"], cat["lib"], cat["gci"]
    src, op, don = cat["source_index"], cat["operator_index"], cat["donor_index"]
    nc = len(cells)
    truth = {k: v[:nc] for k, v in truth.items()}

    _validate_observation_identity(man.get("observation_identity"), src, op, don)
    for k, produced in (("source_index", src), ("operator_index", op), ("donor_index", don)):
        if k in truth and not np.array_equal(np.asarray(truth[k], dtype=np.int64), produced):
            raise AdapterContractError(f"producer-side {k} disagrees with the truth copy; refusing")

    detected = counts > 0
    hidden = sample_hidden_targets(measurement_mask, cells, hidden_fraction, seed)
    query_counts = np.where(hidden, counts, 0.0)
    visible_library = full_library - query_counts.sum(1)       # exact: integer counts in float64
    evidence = measurement_mask & ~hidden
    denom = np.where(visible_library > 0, visible_library, 1.0)[:, None]
    student = np.where(evidence, np.log1p(counts / denom * 1e4), 0.0).astype(np.float32)

    model = SyntheticModelBatch(
        gene_ids=np.tile(universe, (nc, 1)),
        student_expression=student,
        measurement_mask=measurement_mask,
        hidden_target_mask=hidden)
    operator_context = SyntheticOperatorContext(
        source_index=src.astype(np.int16), operator_index=op.astype(np.int16),
        visible_library_size=visible_library.astype(np.float32),
        n_measured=measurement_mask.sum(1).astype(np.int32))
    split_context = SyntheticSplitContext(donor_index=don.astype(np.int32))
    readout = SyntheticReadoutRecord(query_counts=query_counts.astype(np.float32),
                                     full_library_size=full_library.astype(np.float32))
    oracle = SyntheticOracleRecord(
        global_cell_index=cells,
        latents={k: v for k, v in truth.items() if k in ORACLE_ONLY_FIELDS},
        b3_arm_membership=truth.get("rare_flags"),
        b6_ladder_level=truth.get("z_partial"),
        substate=truth.get("substate"),
        annotated_class=truth.get("state_index"))

    measured_zero = measurement_mask & ~detected
    prov = dict(
        schema="V77_SYNTHETIC_BATCH_ADAPTER_PROVENANCE_V3",
        claim_namespace="SYNTHETIC_PIPELINE_ANTICHEAT_REHEARSAL",
        world_root=str(root), observer_dir=obs_dir,
        observer_manifest_schema=man.get("schema"),
        observer_manifest_sha256=hashlib.sha256(man_bytes).hexdigest(),
        structural_support_rule=man.get("structural_support_rule"),
        observation_identity=man.get("observation_identity"),
        feature_identity=man.get("feature_identity"),
        support_source="per-element support_mask_packed read from every observer shard",
        identity_source="source, operator and donor read from every observer shard, checked by name",
        n_cells=int(nc), n_shards_read=int(n_shards_read), n_genes_in_universe=int(len(universe)),
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
        q_safety=("student evidence and every model-facing depth summary exclude hidden-target counts; "
                  "hidden values exist only in the readout record"),
        digests=dict(model=model.digest(), operator_context=operator_context.digest(),
                     split_context=split_context.digest(), readout=readout.digest(),
                     oracle=oracle.digest()),
        oracle_only_fields=sorted(ORACLE_ONLY_FIELDS),
        truth_fields_routed_to_oracle=sorted(oracle.latents),
        runtime_binding="NONE; this adapter names no runtime loader class",
        no_training_performed=True)
    return SyntheticConversion(model=model, operator_context=operator_context,
                               split_context=split_context, readout=readout, oracle=oracle,
                               global_cell_index=cells, provenance=prov)


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
    conv = build_from_world(Path(a.world), a.observer_dir, universe,
                            a.hidden_fraction, a.seed, a.max_cells)
    prov = dict(conv.provenance)
    prov["universe_file"] = dict(path=str(upath), sha256=hashlib.sha256(upath.read_bytes()).hexdigest())
    prov.update(source_commit=git("rev-parse", "HEAD"), adapter_sha256=adapter_sha256,
                provenance_status="CLEAN_COMMITTED_HEAD__ADAPTER_TRACKED",
                command=" ".join(["python", "scripts/v77/v77_synthetic_batch_adapter.py", *sys.argv[1:]]))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="\n") as fh:
        fh.write(json.dumps(prov, indent=2) + "\n")
    print(json.dumps(dict(three_state_counts=prov["three_state_counts"],
                          hidden_targets=prov["hidden_targets"], digests=prov["digests"]), indent=1))


if __name__ == "__main__":
    main()
