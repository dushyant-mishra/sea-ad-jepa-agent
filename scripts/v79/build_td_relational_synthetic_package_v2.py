from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import numpy as np


PACKAGE_ID = "JEPA_TD_RELATIONAL_SYNTHETIC_V2_20261013"
PACKAGE_SCHEMA = "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2"
CONTROLLER_SCHEMA = "JEPA_TD_RELATIONAL_SUCCESSOR_CONTROLLER_MANIFEST_V2"
FIT_ROOT_SCHEMA = "JEPA_TD_RELATIONAL_SYNTHETIC_FIT_ROOT_V2"
FEATURE_COUNT = 512
CELLS_PER_DONOR = 35
CONTROL_COUNT = 5

CAPABILITIES = (
    "REL_BROAD_MESO_POSITIVE",
    "REL_FINE_RECURRENT_POSITIVE",
    "REL_RARE_LOCAL_ISLAND_POSITIVE",
    "REL_MULTI_ISLAND_POSITIVE",
    "REL_DONOR_RESTRICTED_POSITIVE",
    "REL_SOURCE_VISIBILITY_STRESS",
    "REL_TECHNICAL_TWIN_NEGATIVE",
    "REL_NULL_NEGATIVE",
    "REL_UNDERPOWERED_POSITIVE",
)
RARE_CONTROL_CAPABILITIES = frozenset({
    "REL_RARE_LOCAL_ISLAND_POSITIVE",
    "REL_MULTI_ISLAND_POSITIVE",
    "REL_DONOR_RESTRICTED_POSITIVE",
    "REL_TECHNICAL_TWIN_NEGATIVE",
})
CONTROL_ROLES = (
    "DONOR_MATCHED_COMMON",
    "DEPTH_DETECTED_SUM_MATCHED",
    "SOURCE_OPERATOR_MATCHED",
    "WRONG_CELL",
    "PSEUDO_RARE_TECHNICAL",
)
SEMANTIC_CLASS = {
    "REL_BROAD_MESO_POSITIVE": "POSITIVE_TRUTH",
    "REL_FINE_RECURRENT_POSITIVE": "POSITIVE_TRUTH",
    "REL_RARE_LOCAL_ISLAND_POSITIVE": "POSITIVE_TRUTH",
    "REL_MULTI_ISLAND_POSITIVE": "POSITIVE_TRUTH",
    "REL_DONOR_RESTRICTED_POSITIVE": "POSITIVE_TRUTH",
    "REL_SOURCE_VISIBILITY_STRESS": "STRESS_TRUTH",
    "REL_TECHNICAL_TWIN_NEGATIVE": "NEGATIVE_TRUTH",
    "REL_NULL_NEGATIVE": "NEGATIVE_TRUTH",
    "REL_UNDERPOWERED_POSITIVE": "UNDERIDENTIFIED_TRUTH",
}
FIT_VIEW_FIELDS = (
    "source", "panel_id",
    "z_values", "x_values", "y_values",
    "z_measured", "x_measured", "y_measured",
    "z_feature_ids", "x_feature_ids", "y_feature_ids",
    "donor_ids", "operator_ids", "global_rows",
    "source_library", "detected_genes",
    "focal_mask", "neighbor_pool_mask", "min_focal_anchors_per_donor",
    "control_ids", "control_focal_masks", "control_neighbor_pool_masks",
    "control_min_focal_anchors_per_donor",
)
BINDING_AUTHORITY = {
    "synthetic_world_generation_authorized": False,
    "synthetic_world_regeneration_authorized": False,
    "qualification_model_fitting_authorized": False,
    "target_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}
CONTROLLER_AUTHORITY = {
    "synthetic_world_generation_authorized": False,
    "synthetic_world_regeneration_authorized": False,
    "real_execution_authorized": False,
    "target_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any, *, preserve_order: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if preserve_order:
        raw = json.dumps(value, sort_keys=False, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    else:
        raw = canonical_bytes(value)
    path.write_bytes(raw)


def _npy_bytes(array: np.ndarray) -> bytes:
    handle = io.BytesIO()
    np.lib.format.write_array(handle, np.asarray(array), allow_pickle=False)
    return handle.getvalue()


def _write_deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    if set(arrays) != set(FIT_VIEW_FIELDS):
        raise ValueError("fit-view arrays do not match the frozen V2 NPZ schema")
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for key in sorted(arrays):
            array = np.asarray(arrays[key])
            if array.dtype.kind == "O":
                raise ValueError(f"object arrays are forbidden: {key}")
            info = zipfile.ZipInfo(f"{key}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o600 << 16
            archive.writestr(info, _npy_bytes(array))


def _opaque_token(namespace: str, index: int, *, width: int = 18) -> str:
    digest = hashlib.sha256(f"{PACKAGE_ID}|{namespace}|{index}|v2".encode("utf-8")).hexdigest()
    prefix = "q" if namespace == "challenge" else "c"
    return f"{prefix}-{digest[:width]}"


def _feature_ids(prefix: str) -> np.ndarray:
    return np.asarray([f"{prefix}{index:04d}" for index in range(FEATURE_COUNT)], dtype="U8")


def _base_population(n_donors: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    donors = np.asarray(
        [f"D{donor:02d}" for donor in range(n_donors) for _ in range(CELLS_PER_DONOR)],
        dtype="U8",
    )
    local_rows = np.tile(np.arange(CELLS_PER_DONOR, dtype=np.int64), n_donors)
    operators = np.asarray(["O0"] * len(donors), dtype="U4")
    global_rows = np.arange(len(donors), dtype=np.int64)
    return donors, operators, local_rows, global_rows


def _technical_covariates(donors: np.ndarray, local_rows: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = len(donors)
    library = rng.lognormal(mean=np.log(9500.0), sigma=0.18, size=n).astype(np.float64)
    detected = rng.integers(390, 501, size=n, endpoint=False, dtype=np.int64)
    # Break any accidental alignment between biological local order and the TD37A matching ranks.
    for donor in sorted(set(donors.astype(str).tolist())):
        idx = np.where(donors.astype(str) == donor)[0]
        library[idx] = library[idx][rng.permutation(len(idx))]
        detected[idx] = detected[idx][rng.permutation(len(idx))]
    return library, detected


def _line_latent(local_rows: np.ndarray, *, scale: float = 5.0) -> np.ndarray:
    u = local_rows.astype(np.float64) / (CELLS_PER_DONOR - 1)
    return np.column_stack((scale * (2.0 * u - 1.0), 1.25 * np.sin(2.0 * np.pi * u)))


def _encode_latent(latent: np.ndarray, *, noise_seed: int | None = None, noise_sd: float = 0.0) -> np.ndarray:
    latent = np.asarray(latent, dtype=np.float64)
    theta = 2.0 * np.pi * np.arange(FEATURE_COUNT, dtype=np.float64) / FEATURE_COUNT
    weights = np.column_stack((np.cos(theta), np.sin(theta)))
    bias = 0.22 * np.sin(3.0 * theta) + 0.11 * np.cos(7.0 * theta)
    values = latent @ weights.T + bias[None, :]
    if noise_sd:
        rng = np.random.default_rng(noise_seed)
        values = values + rng.normal(0.0, noise_sd, size=values.shape)
    return values.astype(np.float32)


def _support(n: int, *, seed: int, keep: float = 1.0) -> np.ndarray:
    if keep >= 1.0:
        return np.ones((n, FEATURE_COUNT), dtype=bool)
    rng = np.random.default_rng(seed)
    support = rng.random((n, FEATURE_COUNT)) < keep
    # The TD geometry requires >=256 informative pair coordinates; keep every row comfortably above that regime.
    minimum = 420 if keep >= 0.85 else 360
    for row in range(n):
        if int(support[row].sum()) < minimum:
            missing = np.where(~support[row])[0]
            support[row, missing[: minimum - int(support[row].sum())]] = True
    return support


def _permute_within_donor(latent: np.ndarray, donors: np.ndarray, *, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.empty_like(latent)
    donor_s = donors.astype(str)
    for donor in sorted(set(donor_s.tolist())):
        idx = np.where(donor_s == donor)[0]
        out[idx] = latent[idx][rng.permutation(len(idx))]
    return out


def _focal_controls(donors: np.ndarray, primary: np.ndarray) -> list[np.ndarray]:
    donor_s = donors.astype(str)
    controls = [np.zeros(len(donors), dtype=bool) for _ in range(CONTROL_COUNT)]
    for donor in sorted(set(donor_s.tolist())):
        idx = np.where(donor_s == donor)[0]
        common = idx[~primary[idx]]
        if len(common) < CONTROL_COUNT:
            common = idx
        for position, row in enumerate(common.tolist()):
            controls[position % CONTROL_COUNT][row] = True
        # Non-rare challenges have primary=all; ensure every nuisance profile has recurrent focal support.
        for control_index in range(CONTROL_COUNT):
            if not np.any(controls[control_index][idx]):
                controls[control_index][idx[control_index % len(idx)]] = True
    return controls


def _base_world(n_donors: int, seed: int) -> dict[str, Any]:
    donors, operators, local_rows, global_rows = _base_population(n_donors)
    library, detected = _technical_covariates(donors, local_rows, seed + 11)
    return {
        "donor_ids": donors,
        "operator_ids": operators,
        "local_rows": local_rows,
        "global_rows": global_rows,
        "source_library": library,
        "detected_genes": detected,
    }


def _broad_world(*, stress: bool = False) -> dict[str, Any]:
    base = _base_world(5, 41001)
    local = base["local_rows"]
    group = np.minimum(local // 7, 4).astype(np.float64)
    centered = group - 2.0
    within = (local % 7).astype(np.float64) / 6.0 - 0.5
    latent = np.column_stack((centered * 4.5, within * 1.5))
    z_latent = latent.copy()
    coarse = np.column_stack((centered * 4.5, np.zeros_like(centered)))
    z_values = _encode_latent(z_latent)
    x_values = _encode_latent(coarse)
    y_values = _encode_latent(coarse)
    n = len(local)
    z_measured = _support(n, seed=41021, keep=1.0)
    x_measured = _support(n, seed=41022, keep=0.99 if not stress else 0.90)
    y_measured = _support(n, seed=41023, keep=0.99 if not stress else 0.84)
    if stress:
        y_values = (y_values + np.random.default_rng(41024).normal(0.0, 0.035, y_values.shape)).astype(np.float32)
    primary = np.ones(n, dtype=bool)
    controls = _focal_controls(base["donor_ids"], primary)
    base.update({
        "source": "S1" if stress else "S0",
        "panel_id": "P0",
        "latent": latent,
        "z_values": z_values,
        "x_values": x_values,
        "y_values": y_values,
        "z_measured": z_measured,
        "x_measured": x_measured,
        "y_measured": y_measured,
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
        "control_focals": controls,
    })
    if stress:
        base["detected_genes"] = x_measured.sum(axis=1).astype(np.int64)
        base["source_library"] = base["source_library"] * 0.72
    return base


def _fine_world(n_donors: int = 5, *, seed: int = 42001) -> dict[str, Any]:
    base = _base_world(n_donors, seed)
    latent = _line_latent(base["local_rows"], scale=5.5)
    n = len(latent)
    primary = np.ones(n, dtype=bool)
    base.update({
        "source": "S0",
        "panel_id": "P0",
        "latent": latent,
        "z_values": _encode_latent(latent, noise_seed=seed + 1, noise_sd=0.002),
        "x_values": _encode_latent(latent, noise_seed=seed + 2, noise_sd=0.002),
        "y_values": _encode_latent(latent, noise_seed=seed + 3, noise_sd=0.002),
        "z_measured": _support(n, seed=seed + 4, keep=0.995),
        "x_measured": _support(n, seed=seed + 5, keep=0.995),
        "y_measured": _support(n, seed=seed + 6, keep=0.995),
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
        "control_focals": _focal_controls(base["donor_ids"], primary),
    })
    return base


def _rare_world(*, multi: bool = False, donor_restricted: bool = False, seed: int = 43001) -> dict[str, Any]:
    n_donors = 6 if donor_restricted else 5
    base = _base_world(n_donors, seed)
    donors = base["donor_ids"]
    local = base["local_rows"]
    n = len(donors)
    donor_s = donors.astype(str)
    primary = np.zeros(n, dtype=bool)
    latent = np.column_stack((12.0 + local.astype(np.float64) / 3.0, np.zeros(n, dtype=np.float64)))
    z_latent = latent.copy()
    x_background = _line_latent(local, scale=5.0)
    y_background = _permute_within_donor(x_background, donors, seed=seed + 101)
    x_latent = _permute_within_donor(x_background, donors, seed=seed + 102)
    y_latent = y_background.copy()
    active_donors = sorted(set(donor_s.tolist()))[:5] if donor_restricted else sorted(set(donor_s.tolist()))
    for donor in active_donors:
        idx = np.where(donor_s == donor)[0]
        groups = [idx[13:21]]
        centers = [0.0]
        if multi:
            groups = [idx[:6], idx[20:26]]
            centers = [-4.0, 4.0]
        for rows, center in zip(groups, centers):
            primary[rows] = True
            local_coordinate = np.linspace(-0.45, 0.45, len(rows), dtype=np.float64)
            island = np.column_stack((np.full(len(rows), center), local_coordinate * 3.0))
            latent[rows] = island
            z_latent[rows] = island
            x_latent[rows] = island
            y_latent[rows] = island
    control_focals = _focal_controls(donors, primary)
    z_measured = _support(n, seed=seed + 10, keep=0.99)
    x_measured = _support(n, seed=seed + 11, keep=0.99)
    y_measured = _support(n, seed=seed + 12, keep=0.99)
    # The fifth controller-only role is a frequency-matched technical pseudo-profile.
    pseudo_rows = control_focals[4]
    x_measured[pseudo_rows] &= _support(int(pseudo_rows.sum()), seed=seed + 13, keep=0.82)
    y_measured[pseudo_rows] &= _support(int(pseudo_rows.sum()), seed=seed + 14, keep=0.82)
    base.update({
        "source": "S0",
        "panel_id": "P0",
        "latent": latent,
        "z_values": _encode_latent(z_latent, noise_seed=seed + 20, noise_sd=0.002),
        "x_values": _encode_latent(x_latent, noise_seed=seed + 21, noise_sd=0.003),
        "y_values": _encode_latent(y_latent, noise_seed=seed + 22, noise_sd=0.003),
        "z_measured": z_measured,
        "x_measured": x_measured,
        "y_measured": y_measured,
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
        "control_focals": control_focals,
    })
    base["detected_genes"] = x_measured.sum(axis=1).astype(np.int64)
    return base


def _technical_twin_world(seed: int = 44001) -> dict[str, Any]:
    base = _base_world(5, seed)
    donors = base["donor_ids"]
    local = base["local_rows"]
    donor_s = donors.astype(str)
    n = len(donors)
    primary = np.zeros(n, dtype=bool)
    z_latent = _line_latent(local, scale=7.0)
    x_base = _line_latent(local, scale=5.0)
    x_latent = _permute_within_donor(x_base, donors, seed=seed + 101)
    y_latent = _permute_within_donor(x_base, donors, seed=seed + 102)
    for donor in sorted(set(donor_s.tolist())):
        idx = np.where(donor_s == donor)[0]
        rows = idx[13:21]
        primary[rows] = True
        z_latent[rows] = np.column_stack((np.zeros(len(rows)), np.linspace(-1.0, 1.0, len(rows))))
    control_focals = _focal_controls(donors, primary)
    z_measured = _support(n, seed=seed + 10, keep=0.99)
    x_measured = _support(n, seed=seed + 11, keep=0.99)
    y_measured = _support(n, seed=seed + 12, keep=0.99)
    # The primary pseudo-state is generated by observation degradation, not shared X/Y biology.
    x_measured[primary] &= _support(int(primary.sum()), seed=seed + 13, keep=0.80)
    y_measured[primary] &= _support(int(primary.sum()), seed=seed + 14, keep=0.80)
    base.update({
        "source": "S0",
        "panel_id": "P0",
        "latent": _line_latent(local, scale=5.0),
        "z_values": _encode_latent(z_latent),
        "x_values": _encode_latent(x_latent, noise_seed=seed + 20, noise_sd=0.004),
        "y_values": _encode_latent(y_latent, noise_seed=seed + 21, noise_sd=0.004),
        "z_measured": z_measured,
        "x_measured": x_measured,
        "y_measured": y_measured,
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
        "control_focals": control_focals,
    })
    base["detected_genes"] = x_measured.sum(axis=1).astype(np.int64)
    return base


def _null_world(seed: int = 45001) -> dict[str, Any]:
    base = _base_world(5, seed)
    donors = base["donor_ids"]
    local = base["local_rows"]
    z_latent = _line_latent(local, scale=5.0)
    x_latent = _permute_within_donor(z_latent, donors, seed=seed + 101)
    y_latent = _permute_within_donor(z_latent, donors, seed=seed + 102)
    n = len(donors)
    primary = np.ones(n, dtype=bool)
    base.update({
        "source": "S0",
        "panel_id": "P0",
        "latent": z_latent,
        "z_values": _encode_latent(z_latent),
        "x_values": _encode_latent(x_latent, noise_seed=seed + 20, noise_sd=0.004),
        "y_values": _encode_latent(y_latent, noise_seed=seed + 21, noise_sd=0.004),
        "z_measured": _support(n, seed=seed + 10, keep=0.99),
        "x_measured": _support(n, seed=seed + 11, keep=0.99),
        "y_measured": _support(n, seed=seed + 12, keep=0.99),
        "primary_focal": primary,
        "primary_pool": np.ones(n, dtype=bool),
        "control_focals": _focal_controls(donors, primary),
    })
    return base


def build_worlds_for_self_audit() -> dict[str, dict[str, Any]]:
    broad = _broad_world(stress=False)
    stress = _broad_world(stress=True)
    worlds = {
        "REL_BROAD_MESO_POSITIVE": broad,
        "REL_FINE_RECURRENT_POSITIVE": _fine_world(5, seed=42001),
        "REL_RARE_LOCAL_ISLAND_POSITIVE": _rare_world(seed=43001),
        "REL_MULTI_ISLAND_POSITIVE": _rare_world(multi=True, seed=43101),
        "REL_DONOR_RESTRICTED_POSITIVE": _rare_world(donor_restricted=True, seed=43201),
        "REL_SOURCE_VISIBILITY_STRESS": stress,
        "REL_TECHNICAL_TWIN_NEGATIVE": _technical_twin_world(seed=44001),
        "REL_NULL_NEGATIVE": _null_world(seed=45001),
        "REL_UNDERPOWERED_POSITIVE": _fine_world(4, seed=46001),
    }
    # The stress world is the same biological universe as the broad world; only observation changes.
    worlds["REL_SOURCE_VISIBILITY_STRESS"]["latent"] = worlds["REL_BROAD_MESO_POSITIVE"]["latent"].copy()
    worlds["REL_SOURCE_VISIBILITY_STRESS"]["primary_focal"] = worlds["REL_BROAD_MESO_POSITIVE"]["primary_focal"].copy()
    return worlds


def _fit_arrays(world: dict[str, Any], control_ids: list[str]) -> dict[str, np.ndarray]:
    n = len(world["donor_ids"])
    control_focals = np.stack(world["control_focals"], axis=0).astype(bool)
    control_pools = np.ones((CONTROL_COUNT, n), dtype=bool)
    arrays = {
        "source": np.asarray(world["source"], dtype="U8"),
        "panel_id": np.asarray(world["panel_id"], dtype="U8"),
        "z_values": np.asarray(world["z_values"], dtype=np.float32),
        "x_values": np.asarray(world["x_values"], dtype=np.float32),
        "y_values": np.asarray(world["y_values"], dtype=np.float32),
        "z_measured": np.asarray(world["z_measured"], dtype=bool),
        "x_measured": np.asarray(world["x_measured"], dtype=bool),
        "y_measured": np.asarray(world["y_measured"], dtype=bool),
        "z_feature_ids": _feature_ids("Z"),
        "x_feature_ids": _feature_ids("X"),
        "y_feature_ids": _feature_ids("Y"),
        "donor_ids": np.asarray(world["donor_ids"], dtype="U8"),
        "operator_ids": np.asarray(world["operator_ids"], dtype="U4"),
        "global_rows": np.asarray(world["global_rows"], dtype=np.int64),
        "source_library": np.asarray(world["source_library"], dtype=np.float64),
        "detected_genes": np.asarray(world["detected_genes"], dtype=np.int64),
        "focal_mask": np.asarray(world["primary_focal"], dtype=bool),
        "neighbor_pool_mask": np.asarray(world["primary_pool"], dtype=bool),
        "min_focal_anchors_per_donor": np.asarray(1, dtype=np.int64),
        "control_ids": np.asarray(control_ids, dtype="U24"),
        "control_focal_masks": control_focals,
        "control_neighbor_pool_masks": control_pools,
        "control_min_focal_anchors_per_donor": np.ones(CONTROL_COUNT, dtype=np.int64),
    }
    return arrays


def _challenge_mapping() -> dict[str, str]:
    opaque_ids = [_opaque_token("challenge", index) for index in range(len(CAPABILITIES))]
    # Deterministic permutation prevents the fit-view list position from mirroring capability order.
    permutation = np.random.default_rng(31920261013).permutation(len(opaque_ids)).tolist()
    return {capability: opaque_ids[permutation[index]] for index, capability in enumerate(CAPABILITIES)}


def _control_ids_for(challenge_id: str) -> list[str]:
    offset = int(hashlib.sha256(challenge_id.encode("utf-8")).hexdigest()[:8], 16)
    return [_opaque_token(f"control-{challenge_id}", offset + index, width=14) for index in range(CONTROL_COUNT)]


def _controller_claims(challenge_map: dict[str, str], controls_by_challenge: dict[str, list[str]]) -> dict[str, dict[str, Any]]:
    claims: dict[str, dict[str, Any]] = {}
    for capability in CAPABILITIES:
        challenge_id = challenge_map[capability]
        control_ids = controls_by_challenge[challenge_id]
        roles: dict[str, list[str]] = {}
        if capability in RARE_CONTROL_CAPABILITIES:
            for role, control_id in zip(CONTROL_ROLES, control_ids):
                roles[role] = [control_id]
        claims[capability] = {
            "challenge_id": challenge_id,
            "semantic_class": SEMANTIC_CLASS[capability],
            "control_roles": roles,
            "expected_status": "PASS" if capability == "REL_SOURCE_VISIBILITY_STRESS" else None,
        }
    return claims


def main(out_dir: str) -> Path:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    fit_dir = root / "fit_views"
    fit_dir.mkdir(parents=True, exist_ok=True)

    worlds = build_worlds_for_self_audit()
    challenge_map = _challenge_mapping()
    fit_records: list[dict[str, str]] = []
    controls_by_challenge: dict[str, list[str]] = {}

    for capability in CAPABILITIES:
        challenge_id = challenge_map[capability]
        control_ids = _control_ids_for(challenge_id)
        controls_by_challenge[challenge_id] = control_ids
        arrays = _fit_arrays(worlds[capability], control_ids)
        scratch = fit_dir / f".{challenge_id}.npz"
        _write_deterministic_npz(scratch, arrays)
        digest = file_sha256(scratch)
        final = fit_dir / f"{digest}.npz"
        scratch.replace(final)
        fit_records.append({"challenge_id": challenge_id, "sha256": digest})

    # The blinded package root intentionally excludes controller semantics, avoiding a hash cycle.
    fit_records = sorted(fit_records, key=lambda record: record["challenge_id"])
    fit_root = {
        "schema": FIT_ROOT_SCHEMA,
        "package_id": PACKAGE_ID,
        "fit_view_fields": list(FIT_VIEW_FIELDS),
        "fit_views": fit_records,
        "authority": dict(BINDING_AUTHORITY),
    }
    package_sha256 = canonical_sha256(fit_root)
    _write_json(root / "fit_package_root.json", fit_root)

    controller = {
        "schema": CONTROLLER_SCHEMA,
        "package_sha256": package_sha256,
        "claims": _controller_claims(challenge_map, controls_by_challenge),
        "authority": dict(CONTROLLER_AUTHORITY),
    }
    controller_sha256 = canonical_sha256(controller)
    # Preserve mandatory capability insertion order in the file; the TD controller hashes it canonically.
    _write_json(root / "controller_manifest.json", controller, preserve_order=True)

    binding = {
        "schema": PACKAGE_SCHEMA,
        "package_id": PACKAGE_ID,
        "package_sha256": package_sha256,
        "controller_truth_sha256": controller_sha256,
        "fit_view_fields": list(FIT_VIEW_FIELDS),
        "fit_views": fit_records,
        "authority": dict(BINDING_AUTHORITY),
    }
    _write_json(root / "TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V2.json", binding)
    return root


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: build_td_relational_synthetic_package_v2.py <output_dir>")
    main(sys.argv[1])
